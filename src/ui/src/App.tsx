import React, { useState } from 'react';
import './app.css';

export default function App() {
  const [messages, setMessages] = useState<string[]>([]);

  return (
    <div className="app-container">
      <h1>mac-stt-tts-chat</h1>
      <div className="conversation">
        {messages.map((m, i) => (
          <div key={i} className="message">{m}</div>
        ))}
      </div>
      <button className="mic-button" disabled>
        🎤 Start Speaking
      </button>
    </div>
  );
}
