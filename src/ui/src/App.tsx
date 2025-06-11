import React, { useState, useRef } from 'react';
import './app.css';

export default function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [listening, setListening] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const toggleMic = async () => {
    if (!listening) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];
        mediaRecorder.ondataavailable = (e: BlobEvent) => {
          if (e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };
        mediaRecorder.start();
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
      setListening(false);

      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      console.log('Recorded audio length (ms):', blob.size); // placeholder for future streaming
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
      <button className="mic-button" onClick={toggleMic}>
        {listening ? '🛑 Stop Listening' : '🎤 Start Listening'}
      </button>
    </div>
  );
}
