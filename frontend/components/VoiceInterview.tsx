'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
};

type VoiceInterviewProps = {
  sessionId: string;
  interviewType: string;
  candidateName: string;
};

export default function VoiceInterview({ sessionId, interviewType, candidateName }: VoiceInterviewProps) {
  const router = useRouter();
  const [isActive, setIsActive] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [error, setError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [timeElapsed, setTimeElapsed] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    wsRef.current = new WebSocket(`${wsUrl}/ws/interview/${sessionId}`);

    wsRef.current.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        const audioBuffer = await event.data.arrayBuffer();
        audioQueueRef.current.push(audioBuffer);

        if (!isPlayingRef.current) {
          playNextAudioChunk();
        }
      } else {
        const data = JSON.parse(event.data);

        if (data.type === 'transcript' && data.role === 'user') {
          setMessages(prev => [...prev, { role: 'user', content: data.text, timestamp: new Date() }]);
          setCurrentTranscript('');
          setCurrentResponse('');
          setError('');
          setIsProcessing(true);
        } else if (data.type === 'llm_chunk') {
          setCurrentResponse(prev => prev + data.text);
          setIsProcessing(true);
        } else if (data.type === 'assistant_complete') {
          setMessages(prev => [...prev, { role: 'assistant', content: data.text, timestamp: new Date() }]);
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

    return () => {
      wsRef.current?.close();
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [sessionId]);

  useEffect(() => {
    if (isActive) {
      timerRef.current = setInterval(() => {
        setTimeElapsed(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isActive]);

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
        let progressiveTranscriptTimer: NodeJS.Timeout | null = null;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);

            if (wsRef.current?.readyState === WebSocket.OPEN && isSpeaking) {
              const chunk = new Blob([event.data], { type: mimeType });
              wsRef.current.send(chunk);
            }
          }
        };

        mediaRecorder.onstop = () => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'speech_end' }));
          }
          audioChunks = [];
          setIsRecording(false);
        };

        const checkSilence = () => {
          if (!analyserRef.current) return;

          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;

          const SPEECH_THRESHOLD = 10;
          const SILENCE_DURATION = 1000;

          if (average > SPEECH_THRESHOLD) {
            if (!isSpeaking) {
              isSpeaking = true;
              setIsRecording(true);

              if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'speech_start' }));
              }

              mediaRecorder.start(500);
            }

            if (silenceTimeoutRef.current) {
              clearTimeout(silenceTimeoutRef.current);
            }
            silenceTimeoutRef.current = setTimeout(() => {
              if (mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                isSpeaking = false;

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
      } catch (err) {
        setError('Microphone access denied: ' + (err as Error).message);
      }
    } else {
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

  const handleEndInterview = async () => {
    if (confirm('Are you sure you want to end this interview?')) {
      try {
        await fetch(`/api/interviews/${sessionId}/end`, {
          method: 'POST',
        });
        router.push('/');
      } catch (err) {
        console.error('Failed to end interview:', err);
        router.push('/');
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentResponse, currentTranscript]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Interview Session</h1>
            <p className="text-sm text-gray-600">
              {candidateName} • {interviewType}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-lg font-mono text-gray-700">
              {formatTime(timeElapsed)}
            </div>
            <button
              onClick={handleEndInterview}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              End Session
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Transcript Panel (Left) */}
        <div className="w-1/2 flex flex-col border-r border-gray-300 bg-white">
          <div className="p-4 bg-gray-100 border-b border-gray-300">
            <h2 className="text-lg font-semibold text-gray-800">Conversation Transcript</h2>
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
                <div className="flex justify-between items-center mb-1">
                  <p className="font-semibold text-sm">
                    {msg.role === 'user' ? 'You' : 'Interviewer'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
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
                <p className="font-semibold text-sm mb-1">Interviewer</p>
                <p>{currentResponse}</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Voice Control Panel (Right) */}
        <div className="w-1/2 flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-50">
          <h1 className="text-3xl font-bold mb-8 text-gray-900">Voice Interview Mode</h1>

          <button
            onClick={toggleConversation}
            className={`w-48 h-48 rounded-full text-white font-semibold transition-all shadow-lg ${
              isActive
                ? 'bg-red-500 hover:bg-red-600'
                : 'bg-blue-500 hover:bg-blue-600'
            } ${isRecording ? 'animate-pulse ring-4 ring-green-400' : ''}`}
          >
            <div className="text-6xl mb-2">
              {isRecording ? '🎙️' : isActive ? '⏹' : '🎤'}
            </div>
            <div className="text-sm">
              {isRecording ? 'Speaking' : isActive ? 'Stop' : 'Start'}
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

          {!isActive && (
            <p className="mt-6 text-gray-600 text-center max-w-md">
              Click the microphone to start your voice interview. Speak naturally and the AI interviewer will respond.
            </p>
          )}

          {error && (
            <div className="mt-8 w-full max-w-md p-4 bg-red-100 border border-red-400 rounded">
              <p className="font-semibold text-red-700">Error:</p>
              <p className="text-red-600">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
