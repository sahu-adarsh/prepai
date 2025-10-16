from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.bedrock_service import BedrockService
from app.services.s3_service import S3Service
from faster_whisper import WhisperModel
from TTS.api import TTS
import numpy as np
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
tts_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return whisper_model

def get_tts_model():
    global tts_model
    if tts_model is None:
        print("Loading Coqui TTS model (VITS)...")
        tts_model = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False)
        print("Coqui TTS model loaded successfully")
    return tts_model

@router.websocket("/ws/interview/{session_id}")
async def voice_interview_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice interviews
    Handles: Audio streaming, Speech-to-Text, LLM interaction, Text-to-Speech
    """
    try:
        # Initialize models BEFORE accepting connection
        whisper = get_whisper_model()
        tts = get_tts_model()

        await websocket.accept()

        # Initialize services
        bedrock_service = BedrockService()
        s3_service = S3Service()
    except Exception as e:
        print(f"Model initialization error: {e}")
        await websocket.close(code=1011, reason=f"Model init failed: {str(e)}")
        return

    # State management
    streaming_active = False
    streaming_audio_chunks = []
    accumulated_transcript = ""
    processing = False
    interview_started = False

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
        """Convert text to speech using Coqui TTS"""
        try:
            # Generate audio using Coqui TTS
            wav_data = tts.tts(text=text, speaker="p232") # Authoritative male

            # Convert to numpy array
            if isinstance(wav_data, np.ndarray):
                wav_array = wav_data
            elif isinstance(wav_data, list) and wav_data and isinstance(wav_data[0], (int, float)):
                # List of raw samples (int/float)
                wav_array = np.array(wav_data, dtype=np.float32)
            else:
                # Fallback: try direct conversion
                wav_array = np.array(wav_data)

            # Ensure it's a 1D array
            if wav_array.ndim == 0:
                raise ValueError("TTS returned scalar value instead of audio array")

            wav_array = wav_array.flatten()  # Ensure 1D

            # Convert numpy array to WAV bytes
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)  # Coqui default sample rate

                # Convert float32 to int16
                audio_int16 = (wav_array * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())

            return wav_buffer.getvalue()
        except Exception as e:
            print(f"TTS error: {e}")
            import traceback
            traceback.print_exc()
            return b""

    async def send_interviewer_introduction():
        """Send interviewer's initial introduction"""
        nonlocal processing

        if processing:
            return

        processing = True

        try:
            # Get session data to personalize greeting
            session_data = s3_service.get_session(session_id)
            candidate_name = session_data.get("candidate_name", "candidate") if session_data else "candidate"
            interview_type = session_data.get("interview_type", "Technical Interview") if session_data else "Technical Interview"

            # Create greeting prompt for the interviewer
            greeting_prompt = f"Start the interview by introducing yourself (Alex Rivera) as the interviewer and welcoming {candidate_name} to the {interview_type}. Keep it brief and professional."

            print(f"[{datetime.now()}] Sending interviewer introduction...")
            full_response = ""
            text_buffer = ""
            sentence_endings = re.compile(r'[.!?]\s*')

            try:
                event_stream = bedrock_service.invoke_agent(session_id, greeting_prompt)
                print(f"[{datetime.now()}] Bedrock Agent invoked for introduction")

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
                print(f"Bedrock Agent error during introduction: {e}")
                # Fallback greeting
                full_response = f"Hello {candidate_name}, welcome to your {interview_type}. I'll be conducting this interview today. Let's begin."
                audio_bytes = await text_to_speech(full_response)
                if len(audio_bytes) > 44:
                    await websocket.send_bytes(audio_bytes)

            # Signal completion
            await websocket.send_json({
                "type": "assistant_complete",
                "text": full_response,
                "role": "assistant"
            })

            # Save introduction to transcript
            s3_service.update_session_transcript(session_id, {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            print(f"Error sending introduction: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        finally:
            processing = False

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
                        if data.get('type') == 'interview_ready' and not interview_started:
                            print(f"[{session_id}] Client ready, sending introduction...")
                            interview_started = True
                            await send_interviewer_introduction()
                        elif data.get('type') == 'speech_start':
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
