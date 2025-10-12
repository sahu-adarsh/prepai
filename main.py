from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from piper import PiperVoice
import ollama
import io
import tempfile
import os
import wave
import re
import json

app = FastAPI()

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize models
# "mps" (Metal Performance Shaders) for Mac, "cuda" for NVIDIA GPUs, "cpu" for CPU
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Maintain conversation history
    conversation_history = [
        {'role': 'system', 'content': 'You are a helpful AI assistant. Keep responses very concise and natural for voice conversation. Respond as if in a real-time conversation.'}
    ]

    processing = False
    streaming_audio_chunks = []  # Buffer for streaming chunks
    streaming_active = False
    accumulated_transcript = ""  # Progressive transcript accumulation
    last_processed_length = 0  # Track what we've already processed

    async def process_audio_streaming(audio_data, is_final=False):
        """Process audio with progressive transcription"""
        nonlocal accumulated_transcript, last_processed_length

        # Determine file extension based on data
        suffix = '.webm'
        if audio_data[:4] == b'RIFF':
            suffix = '.wav'

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_path = temp_audio.name

        try:
            # Progressive transcription - transcribe accumulated audio
            segments, _ = whisper_model.transcribe(
                temp_path,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            current_text = " ".join([segment.text for segment in segments]).strip()

            if current_text:
                # Send progressive transcript update
                await websocket.send_json({
                    "type": "transcript_partial" if not is_final else "transcript",
                    "text": current_text,
                    "role": "user",
                    "is_final": is_final
                })

                # Update accumulated transcript
                accumulated_transcript = current_text

        except Exception as e:
            print(f"Transcription error: {e}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def process_audio(audio_data, is_final=True):
        nonlocal processing, accumulated_transcript, last_processed_length

        if processing and not is_final:
            # Allow progressive updates but block final processing
            return

        if is_final:
            processing = True

        # Determine file extension based on data
        suffix = '.webm'
        if audio_data[:4] == b'RIFF':
            suffix = '.wav'

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_path = temp_audio.name

        try:
            # Step 1: STT - Convert speech to text with VAD filter
            segments, _ = whisper_model.transcribe(
                temp_path,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            text = " ".join([segment.text for segment in segments]).strip()

            if not is_final:
                # Progressive transcript
                if text and text != accumulated_transcript:
                    accumulated_transcript = text
                    await websocket.send_json({
                        "type": "transcript_partial",
                        "text": text,
                        "role": "user",
                        "is_final": False
                    })
        except Exception as e:
            print(f"Transcription error: {e}")
            text = ""
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        if not is_final:
            return

        # Final processing
        text = accumulated_transcript or text
        accumulated_transcript = ""  # Reset for next utterance
        last_processed_length = 0

        if not text:
            processing = False
            return

        await websocket.send_json({"type": "transcript", "text": text, "role": "user", "is_final": True})

        # Add user message to history
        conversation_history.append({'role': 'user', 'content': text})

        # Step 2 & 3: Incremental LLM + TTS - Start processing as soon as we have text
        await process_llm_response()

    async def process_llm_response():
        """Process LLM response with incremental streaming"""
        nonlocal processing, conversation_history

        try:
            # Initialize Piper voice
            voice = PiperVoice.load("models/piper/en_US-lessac-medium.onnx")

            text_buffer = ""
            full_response = ""
            sentence_endings = re.compile(r'[.!?]\s*')

            # Incremental LLM streaming - start generating response immediately
            stream = ollama.chat(
                model='mistral',
                messages=conversation_history,
                stream=True,
            )

            for chunk in stream:
                content = chunk['message']['content']
                text_buffer += content
                full_response += content

                # Send text chunk to frontend immediately
                await websocket.send_json({"type": "llm_chunk", "text": content})

                # Check if we have a complete sentence for TTS
                sentences = sentence_endings.split(text_buffer)

                # Process complete sentences (all but the last fragment)
                for sentence in sentences[:-1]:
                    sentence = sentence.strip()
                    if sentence:
                        # Generate audio for this sentence and stream it
                        audio_data = io.BytesIO()
                        with wave.open(audio_data, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(voice.config.sample_rate)

                            for audio_chunk in voice.synthesize(sentence):
                                wav_file.writeframes(audio_chunk.audio_int16_bytes)

                        # Send audio chunk to frontend
                        audio_bytes = audio_data.getvalue()
                        if len(audio_bytes) > 44:  # More than WAV header
                            await websocket.send_bytes(audio_bytes)

                # Keep the last incomplete fragment in buffer
                text_buffer = sentences[-1] if sentences else ""

            # Process any remaining text in buffer
            if text_buffer.strip():
                audio_data = io.BytesIO()
                with wave.open(audio_data, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(voice.config.sample_rate)

                    for audio_chunk in voice.synthesize(text_buffer):
                        wav_file.writeframes(audio_chunk.audio_int16_bytes)

                audio_bytes = audio_data.getvalue()
                if len(audio_bytes) > 44:
                    await websocket.send_bytes(audio_bytes)

            # Signal end of response and send full transcript
            await websocket.send_json({
                "type": "assistant_complete",
                "text": full_response,
                "role": "assistant"
            })

            # Add assistant response to history
            conversation_history.append({'role': 'assistant', 'content': full_response})

        except Exception as tts_error:
            print(f"LLM/TTS Error: {tts_error}")
            await websocket.send_json({"type": "error", "message": f"LLM/TTS failed: {str(tts_error)}"})

        processing = False

    try:
        while True:
            # Receive message from client
            message = await websocket.receive()

            # Check for disconnect
            if message['type'] == 'websocket.disconnect':
                break

            # Handle text messages (control signals)
            if 'text' in message:
                try:
                    data = json.loads(message['text'])
                    if isinstance(data, dict):
                        if data.get('type') == 'speech_start':
                            print("📡 Streaming mode started")
                            streaming_active = True
                            streaming_audio_chunks = []
                            accumulated_transcript = ""
                            last_processed_length = 0
                        elif data.get('type') == 'speech_end':
                            print("✅ Streaming mode ended, processing accumulated audio")
                            streaming_active = False
                            if streaming_audio_chunks:
                                # Concatenate all chunks
                                combined_audio = b''.join(streaming_audio_chunks)
                                streaming_audio_chunks = []
                                await process_audio(combined_audio, is_final=True)
                        elif data.get('type') == 'process_progressive':
                            # Process accumulated audio progressively without finalizing
                            if streaming_audio_chunks:
                                combined_audio = b''.join(streaming_audio_chunks)
                                await process_audio(combined_audio, is_final=False)
                except Exception as e:
                    print(f"Error parsing control message: {e}")
                    pass

            # Check if it's audio data
            if 'bytes' in message:
                data = message['bytes']

                # Skip very small chunks (likely noise)
                if len(data) < 1000:
                    continue

                if streaming_active:
                    # Buffer chunks while streaming
                    print(f"📦 Buffering chunk: {len(data)} bytes")
                    streaming_audio_chunks.append(data)
                else:
                    # Process complete audio segment (fallback mode)
                    await process_audio(data, is_final=True)

    except Exception as e:
        if "disconnect" not in str(e).lower():
            print(f"WebSocket Error: {e}")
            import traceback
            traceback.print_exc()
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.get("/health")
async def health():
    return {"status": "ok"}