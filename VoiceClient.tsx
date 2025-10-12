'use client';

import { useState, useRef, useEffect } from 'react';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

export default function VoiceClient() {
  const [isActive, setIsActive] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [error, setError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws');

    wsRef.current.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        const audioBuffer = await event.data.arrayBuffer();
        audioQueueRef.current.push(audioBuffer);

        if (!isPlayingRef.current) {
          playNextAudioChunk();
        }
      } else {
        const data = JSON.parse(event.data);

        if (data.type === 'transcript_partial' && data.role === 'user') {
          // Progressive transcript update - show but don't finalize
          setCurrentTranscript(data.text);
          setIsProcessing(true);
        } else if (data.type === 'transcript' && data.role === 'user') {
          // Final transcript
          setMessages(prev => [...prev, { role: 'user', content: data.text }]);
          setCurrentTranscript('');
          setCurrentResponse('');
          setError('');
          setIsProcessing(true);
        } else if (data.type === 'llm_chunk') {
          setCurrentResponse(prev => prev + data.text);
          setIsProcessing(true);
        } else if (data.type === 'assistant_complete') {
          setMessages(prev => [...prev, { role: 'assistant', content: data.text }]);
          setCurrentResponse('');
          setIsProcessing(false);
        } else if (data.type === 'error') {
          setError(data.message);
          setIsProcessing(false);
        }
      }
    };

    wsRef.current.onerror = () => {
      setError('Connection error');
    };

    return () => wsRef.current?.close();
  }, []);

  const toggleConversation = async () => {
    if (!isActive) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true
          }
        });
        streamRef.current = stream;

        // Setup audio analyser for silence detection
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        source.connect(analyser);
        analyserRef.current = analyser;

        const mimeType = MediaRecorder.isTypeSupported('audio/wav') ? 'audio/wav' : 'audio/webm';
        const mediaRecorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond: 16000 });
        mediaRecorderRef.current = mediaRecorder;

        let audioChunks: Blob[] = [];
        let isSpeaking = false;
        let streamingInterval: NodeJS.Timeout | null = null;
        let progressiveTranscriptTimer: NodeJS.Timeout | null = null;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);

            // Stream chunk immediately to backend while still recording
            if (wsRef.current?.readyState === WebSocket.OPEN && isSpeaking) {
              const chunk = new Blob([event.data], { type: mimeType });
              console.log('📡 Streaming chunk, size:', chunk.size);
              wsRef.current.send(chunk);
            }
          }
        };

        mediaRecorder.onstop = () => {
          // Send final end-of-speech signal
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'speech_end' }));
            console.log('✅ Speech ended signal sent');
          }
          audioChunks = [];
          setIsRecording(false);
          if (streamingInterval) {
            clearInterval(streamingInterval);
          }
        };

        // Check audio level periodically
        const checkSilence = () => {
          if (!analyserRef.current) return;

          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;

          const SPEECH_THRESHOLD = 10;
          const SILENCE_DURATION = 1000; // Reduced to 1 second for interviews

          if (average > SPEECH_THRESHOLD) {
            // Speech detected
            if (!isSpeaking) {
              console.log('🎤 Speech started - streaming mode enabled');
              isSpeaking = true;
              setIsRecording(true);

              // Send start signal
              if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'speech_start' }));
              }

              // Start recording and request data every 500ms for streaming
              mediaRecorder.start(500);

              // Request progressive transcription every 2 seconds while speaking
              progressiveTranscriptTimer = setInterval(() => {
                if (wsRef.current?.readyState === WebSocket.OPEN && isSpeaking) {
                  wsRef.current.send(JSON.stringify({ type: 'process_progressive' }));
                }
              }, 2000);
            }

            // Reset silence timeout
            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
            }
            silenceTimeoutRef.current = setTimeout(() => {
              if (mediaRecorder.state === 'recording') {
                console.log('🔇 Silence detected, stopping recording');
                mediaRecorder.stop();
                isSpeaking = false;

                // Stop progressive transcription
                if (progressiveTranscriptTimer) {
                  clearInterval(progressiveTranscriptTimer);
                  progressiveTranscriptTimer = null;
                }
              }
            }, SILENCE_DURATION);
          }
        };

        const intervalId = setInterval(checkSilence, 100);
        (mediaRecorder as any).intervalId = intervalId;

        setIsActive(true);
        setError('');
        console.log('✅ Voice assistant started (streaming mode)');
      } catch (err) {
        setError('Microphone access denied: ' + (err as Error).message);
      }
    } else {
      // Stop conversation
      if (mediaRecorderRef.current) {
        clearInterval((mediaRecorderRef.current as any).intervalId);
        if (mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
        }
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      streamRef.current?.getTracks().forEach(track => track.stop());
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      setIsActive(false);
      setIsRecording(false);
      console.log('⏹ Voice assistant stopped');
    }
  };

  const playNextAudioChunk = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      return;
    }

    isPlayingRef.current = true;
    const audioBuffer = audioQueueRef.current.shift()!;

    try {
      if (!audioContextRef.current || audioContextRef.current.state === 'closed') {
        audioContextRef.current = new AudioContext();
      }

      const context = audioContextRef.current;

      if (context.state === 'suspended') {
        await context.resume();
      }

      const buffer = await context.decodeAudioData(audioBuffer);
      const source = context.createBufferSource();
      source.buffer = buffer;
      source.connect(context.destination);

      source.onended = () => {
        playNextAudioChunk();
      };

      source.start();
    } catch (err) {
      setError('Failed to play audio: ' + (err as Error).message);
      playNextAudioChunk();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse, currentTranscript]);

  return (
    <div className="flex h-screen">
      {/* Chat Panel */}
      <div className="w-1/2 flex flex-col border-r border-gray-300">
        <div className="p-4 bg-gray-100 border-b border-gray-300">
          <h2 className="text-xl font-bold text-gray-800">Conversation</h2>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-100 ml-8 text-gray-900'
                  : 'bg-gray-100 mr-8 text-gray-900'
              }`}
            >
              <p className="font-semibold text-sm mb-1">
                {msg.role === 'user' ? 'You' : 'Assistant'}
              </p>
              <p>{msg.content}</p>
            </div>
          ))}

          {currentTranscript && (
            <div className="p-3 rounded-lg bg-blue-50 ml-8 text-gray-900 border-2 border-blue-300 border-dashed">
              <p className="font-semibold text-sm mb-1 text-blue-600">You (transcribing...)</p>
              <p className="italic opacity-80">{currentTranscript}</p>
            </div>
          )}

          {currentResponse && (
            <div className="p-3 rounded-lg bg-gray-100 mr-8 text-gray-900">
              <p className="font-semibold text-sm mb-1">Assistant</p>
              <p>{currentResponse}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Voice Control Panel */}
      <div className="w-1/2 flex flex-col items-center justify-center p-8 bg-gray-50">
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Voice Mode</h1>

        <button
          onClick={toggleConversation}
          className={`w-40 h-40 rounded-full text-white font-semibold transition-all shadow-lg ${
            isActive
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-blue-500 hover:bg-blue-600'
          } ${isRecording ? 'animate-pulse ring-4 ring-green-400' : ''}`}
        >
          <div className="text-5xl mb-2">
            {isRecording ? '🎙️' : isActive ? '⏹' : '🎤'}
          </div>
        </button>

        {isActive && (
          <div className="mt-6 text-center space-y-2">
            <p className="text-lg font-medium text-gray-700">
              {isRecording ? '🟢 Listening...' : '⚪ Waiting for speech...'}
            </p>
            {isProcessing && (
              <p className="text-sm text-blue-600 animate-pulse">
                ⚡ Processing response...
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="mt-8 w-full max-w-md p-4 bg-red-100 border border-red-400 rounded">
            <p className="font-semibold text-red-700">Error:</p>
            <p className="text-red-600">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}