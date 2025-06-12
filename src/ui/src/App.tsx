import React, { useState, useRef } from 'react';
import './app.css';

export default function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [listening, setListening] = useState(false);
  const [bytesSent, setBytesSent] = useState(0);
  const [bytesReceived, setBytesReceived] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const toggleMic = async () => {
    if (!listening) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const ws = new WebSocket('ws://localhost:8000');
        wsRef.current = ws;
        setBytesSent(0);
        setBytesReceived(0);

        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];
        mediaRecorder.ondataavailable = async (e: BlobEvent) => {
          if (e.data.size > 0) {
            console.log('Captured chunk', e.data.size, 'bytes');
            audioChunksRef.current.push(e.data);
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(await e.data.arrayBuffer());
              setBytesSent((b) => b + e.data.size);
            }
          }
        };
        ws.onmessage = async (ev: MessageEvent) => {
          if (typeof ev.data !== 'string') {
            let size = 0;
            if (ev.data instanceof Blob) {
              size = ev.data.size;
            } else if (ev.data instanceof ArrayBuffer) {
              size = ev.data.byteLength;
            }
            if (size > 0) {
              setBytesReceived((b) => b + size);
            }
            return;
          }
          try {
            const t = JSON.parse(ev.data);
            if (t.final) {
              setMessages((m) => [...m, t.text]);
            }
          } catch (err) {
            console.error('Failed to parse message', err);
          }
        };
        // Pass a timeslice so dataavailable fires periodically
        mediaRecorder.start(250);
        console.log('Microphone capture started');
        setListening(true);
      } catch (err) {
        console.error('Failed to access microphone', err);
      }
    } else {
      const recorder = mediaRecorderRef.current;
      if (recorder) {
        recorder.stop();
        recorder.stream.getTracks().forEach((t) => t.stop());
        mediaRecorderRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      console.log('Microphone capture stopped');
      setListening(false);

      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      console.log('Recorded audio length (ms):', blob.size);
    }
  };

  return (
    <div className="app-container">
      <h1>mac-stt-tts-chat</h1>
      <div className="conversation">
        {messages.map((m, i) => (
          <div key={i} className="message">{m}</div>
        ))}
      </div>
      {listening && (
        <div className="byte-counts">
          Sent {bytesSent} bytes / Received {bytesReceived} bytes
        </div>
      )}
      <button className="mic-button" onClick={toggleMic}>
        {listening ? '🛑 Stop Listening' : '🎤 Start Listening'}
      </button>
    </div>
  );
}
