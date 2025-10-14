from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service
from faster_whisper import WhisperModel
from piper import PiperVoice
import io
import tempfile
import os
import wave
import re
import json
import asyncio
from datetime import datetime

router = APIRouter()

# Initialize models (lazy loading recommended for production)
whisper_model = None
piper_voice = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return whisper_model

def get_piper_voice():
    global piper_voice
    if piper_voice is None:
        piper_voice = PiperVoice.load("models/piper/en_US-lessac-medium.onnx")
    return piper_voice

@router.websocket("/ws/interview/{session_id}")
async def voice_interview_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice interviews
    Handles: Audio streaming, Speech-to-Text, LLM interaction, Text-to-Speech
    """
    await websocket.accept()

    # Initialize services
    bedrock_service = BedrockService()
    s3_service = S3Service()
    whisper = get_whisper_model()
    voice = get_piper_voice()

    # State management
    streaming_active = False
    streaming_audio_chunks = []
    accumulated_transcript = ""
    processing = False

    async def transcribe_audio(audio_data: bytes) -> str:
        """Convert audio to text using faster-whisper"""
        import time
        start_time = time.time()

        suffix = '.webm' if audio_data[:4] != b'RIFF' else '.wav'

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_path = temp_audio.name

        try:
            segments, _ = whisper.transcribe(
                temp_path,
                beam_size=1,  # Reduced from 5 for speed
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            text = " ".join([segment.text for segment in segments]).strip()
            elapsed = time.time() - start_time
            print(f"[WHISPER] Transcription took {elapsed:.2f}s")
            return text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def text_to_speech(text: str) -> bytes:
        """Convert text to speech using Piper TTS"""
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(voice.config.sample_rate)

                for audio_chunk in voice.synthesize(text):
                    wav_file.writeframes(audio_chunk.audio_int16_bytes)

            return wav_buffer.getvalue()
        except Exception as e:
            print(f"TTS error: {e}")
            return b""

    async def process_voice_turn(audio_data: bytes):
        """Process complete voice turn: STT -> Bedrock -> TTS"""
        nonlocal processing, accumulated_transcript

        if processing:
            return

        processing = True

        try:
            # Step 1: Speech-to-Text
            transcript = await transcribe_audio(audio_data)

            if not transcript:
                processing = False
                return

            # Send final transcript to frontend IMMEDIATELY with priority
            await websocket.send_json({
                "type": "transcript",
                "text": transcript,
                "role": "user",
                "is_final": True
            })
            await asyncio.sleep(0)  # Force context switch, let message send
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Transcript sent: {transcript}")

            # Save to S3 in background (don't wait)
            asyncio.create_task(asyncio.to_thread(
                s3_service.update_session_transcript,
                session_id,
                {
                    "role": "user",
                    "content": transcript,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))

            # Step 2: Get response from Bedrock Agent (streaming) - starts IMMEDIATELY
            print(f"[{datetime.now()}] Calling Bedrock Agent...")
            full_response = ""
            text_buffer = ""
            sentence_endings = re.compile(r'[.!?]\s*')

            try:
                event_stream = bedrock_service.invoke_agent(session_id, transcript)
                print(f"[{datetime.now()}] Bedrock Agent invoked")

                for event in event_stream:
                    if 'chunk' in event:
                        chunk_data = event['chunk']
                        if 'bytes' in chunk_data:
                            chunk_text = chunk_data['bytes'].decode('utf-8')
                            full_response += chunk_text
                            text_buffer += chunk_text

                            # Send text chunk to frontend
                            await websocket.send_json({
                                "type": "llm_chunk",
                                "text": chunk_text
                            })

                            # Generate TTS for complete sentences
                            sentences = sentence_endings.split(text_buffer)

                            for sentence in sentences[:-1]:
                                sentence = sentence.strip()
                                if sentence:
                                    audio_bytes = await text_to_speech(sentence)
                                    if len(audio_bytes) > 44:  # More than WAV header
                                        await websocket.send_bytes(audio_bytes)

                            # Keep incomplete fragment
                            text_buffer = sentences[-1] if sentences else ""

                # Process remaining text
                if text_buffer.strip():
                    audio_bytes = await text_to_speech(text_buffer)
                    if len(audio_bytes) > 44:
                        await websocket.send_bytes(audio_bytes)

            except Exception as e:
                print(f"Bedrock Agent error: {e}")
                # Fallback error message
                await websocket.send_json({
                    "type": "error",
                    "message": f"AI processing error: {str(e)}"
                })
                full_response = "I apologize, but I encountered an error processing your response."

            # Signal completion
            await websocket.send_json({
                "type": "assistant_complete",
                "text": full_response,
                "role": "assistant"
            })

            # Save assistant response to transcript
            s3_service.update_session_transcript(session_id, {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })

            accumulated_transcript = ""

        except Exception as e:
            print(f"Voice processing error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        finally:
            processing = False

    # Main WebSocket loop
    try:
        while True:
            message = await websocket.receive()

            if message['type'] == 'websocket.disconnect':
                break

            # Handle control signals
            if 'text' in message:
                try:
                    data = json.loads(message['text'])
                    if isinstance(data, dict):
                        if data.get('type') == 'speech_start':
                            print(f"[{session_id}] Speech started")
                            streaming_active = True
                            streaming_audio_chunks = []
                            accumulated_transcript = ""
                        elif data.get('type') == 'speech_end':
                            print(f"[{session_id}] Speech ended, processing...")
                            streaming_active = False
                            if streaming_audio_chunks:
                                combined_audio = b''.join(streaming_audio_chunks)
                                streaming_audio_chunks = []
                                await process_voice_turn(combined_audio)
                except Exception as e:
                    print(f"Error parsing control message: {e}")

            # Handle audio data
            if 'bytes' in message:
                data = message['bytes']

                # Skip small chunks (noise)
                if len(data) < 1000:
                    continue

                if streaming_active:
                    streaming_audio_chunks.append(data)
                else:
                    # Fallback: process complete audio
                    await process_voice_turn(data)

    except WebSocketDisconnect:
        print(f"[{session_id}] Client disconnected")
    except Exception as e:
        print(f"[{session_id}] WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
