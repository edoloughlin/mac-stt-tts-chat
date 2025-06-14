# UI

This directory contains the React-based web user interface built with Vite.

## Development

Install dependencies and run the development server:

```bash
npm install
npm run dev
```

Open `http://localhost:5173` in your browser to view the app.

The UI streams microphone audio to the backend via a WebSocket connection and displays the conversation history. Start the Python WebSocket server before launching the UI.

A spectrogram visualizes the incoming audio while listening. Use the slider below the conversation history to adjust the silence detection threshold if the default is too aggressive.
