import React, { useState, useRef } from 'react';
import './app.css';

export default function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [listening, setListening] = useState(false);
  const [bytesSent, setBytesSent] = useState(0);
  const [bytesReceived, setBytesReceived] = useState(0);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const toggleMic = async () => {
    if (!listening) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const ws = new WebSocket('ws://localhost:8000');
        wsRef.current = ws;
        setBytesSent(0);
        setBytesReceived(0);

        const ctx = new AudioContext();
        audioCtxRef.current = ctx;
        await ctx.audioWorklet.addModule(new URL('./pcmWorklet.ts', import.meta.url));
        const source = ctx.createMediaStreamSource(stream);
        sourceRef.current = source;
        const node = new AudioWorkletNode(ctx, 'pcm-processor');
        workletNodeRef.current = node;
        node.port.onmessage = (ev: MessageEvent) => {
          const data = ev.data as ArrayBuffer;
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(data);
            setBytesSent((b) => b + data.byteLength);
          }
        };
        const gain = ctx.createGain();
        gain.gain.value = 0;
        source.connect(node).connect(gain).connect(ctx.destination);
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
        console.log('Microphone capture started');
        setListening(true);
      } catch (err) {
        console.error('Failed to access microphone', err);
      }
    } else {
      if (workletNodeRef.current) {
        workletNodeRef.current.disconnect();
        workletNodeRef.current.port.onmessage = null;
        workletNodeRef.current = null;
      }
      if (sourceRef.current) {
        sourceRef.current.mediaStream.getTracks().forEach((t) => t.stop());
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }
      if (audioCtxRef.current) {
        await audioCtxRef.current.close();
        audioCtxRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      console.log('Microphone capture stopped');
      setListening(false);
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
