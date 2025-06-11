import asyncio
import pathlib
import sys
from unittest import mock

# Allow importing the src package
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.stt import VoskStream, Transcript


def test_vosk_stream_yields_partial_and_final():
    # Mock vosk classes
    with mock.patch("src.stt.streaming.vosk") as m_vosk:
        m_vosk.Model.return_value = mock.Mock()
        rec_instance = mock.Mock()
        m_vosk.KaldiRecognizer.return_value = rec_instance

        # Configure recognizer behavior
        rec_instance.AcceptWaveform.side_effect = [False, True]
        rec_instance.PartialResult.return_value = "{\"partial\": \"hel\"}"
        rec_instance.Result.return_value = "{\"text\": \"hello\"}"

        stream = VoskStream("model")

        async def run_test():
            stream.feed_audio(b"data1")
            stream.feed_audio(b"data2")

            gen = stream.stream()
            partial = await anext(gen)
            final = await anext(gen)

            assert partial == Transcript(text="hel", is_final=False)
            assert final == Transcript(text="hello", is_final=True)

        asyncio.run(run_test())




