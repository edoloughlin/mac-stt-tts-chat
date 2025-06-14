import React, { useState, useRef, useEffect } from 'react';
import './app.css';

type Message = {
  speaker: 'user' | 'agent';
  text: string;
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [listening, setListening] = useState(false);
  const [bytesSent, setBytesSent] = useState(0);
  const [bytesReceived, setBytesReceived] = useState(0);
  const [silenceThreshold, setSilenceThreshold] = useState(0.002);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animRef = useRef<number | null>(null);

  useEffect(() => {
    if (workletNodeRef.current) {
      workletNodeRef.current.port.postMessage({ silenceThreshold });
    }
  }, [silenceThreshold]);

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
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyserRef.current = analyser;
        const node = new AudioWorkletNode(ctx, 'pcm-processor');
        workletNodeRef.current = node;
        node.port.postMessage({ silenceThreshold });
        node.port.onmessage = (ev: MessageEvent) => {
          const data = ev.data as ArrayBuffer;
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(data);
            setBytesSent((b) => b + data.byteLength);
          }
        };
        const gain = ctx.createGain();
        gain.gain.value = 0;
        source.connect(analyser);
        analyser.connect(node).connect(gain).connect(ctx.destination);

        const draw = () => {
          if (!analyserRef.current || !canvasRef.current) return;
          const analyser = analyserRef.current;
          const canvas = canvasRef.current;
          const canvasCtx = canvas.getContext('2d');
          if (!canvasCtx) return;
          const bufferLength = analyser.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);
          analyser.getByteFrequencyData(dataArray);
          canvasCtx.fillStyle = 'black';
          canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
          const barWidth = canvas.width / bufferLength;
          for (let i = 0; i < bufferLength; i++) {
            const value = dataArray[i];
            const percent = value / 255;
            const height = canvas.height * percent;
            const offset = canvas.height - height;
            canvasCtx.fillStyle = '#0f0';
            canvasCtx.fillRect(i * barWidth, offset, barWidth, height);
          }
          animRef.current = requestAnimationFrame(draw);
        };
        draw();
        ws.onmessage = async (ev: MessageEvent) => {
          if (typeof ev.data !== 'string') {
            const buf =
              ev.data instanceof Blob ? await ev.data.arrayBuffer() : ev.data;
            setBytesReceived((b) => b + buf.byteLength);
            if (audioCtxRef.current) {
              const audioBuf = await audioCtxRef.current.decodeAudioData(buf);
              const source = audioCtxRef.current.createBufferSource();
              source.buffer = audioBuf;
              source.connect(audioCtxRef.current.destination);
              source.start();
            }
            return;
          }
          try {
            const t = JSON.parse(ev.data);
            if (t.final) {
              if (t.agent) {
                setMessages((m) => [...m, { speaker: 'agent', text: t.text }]);
              } else {
                setMessages((m) => [...m, { speaker: 'user', text: t.text }]);
              }
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
      if (animRef.current) {
        cancelAnimationFrame(animRef.current);
        animRef.current = null;
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
          <div key={i} className={`message ${m.speaker}`}>{m.text}</div>
        ))}
      </div>
      {listening && (
        <div className="byte-counts">
          Sent {bytesSent} bytes / Received {bytesReceived} bytes
        </div>
      )}
      <div className="controls">
        <label>
          Silence Threshold: {silenceThreshold.toFixed(3)}
          <input
            type="range"
            min="0"
            max="0.01"
            step="0.001"
            value={silenceThreshold}
            onChange={(e) =>
              setSilenceThreshold(parseFloat(e.target.value))
            }
          />
        </label>
      </div>
      <canvas ref={canvasRef} className="spectrogram" width={400} height={100} />
      <button className="mic-button" onClick={toggleMic}>
        {listening ? '🛑 Stop Listening' : '🎤 Start Listening'}
      </button>
    </div>
  );
}
