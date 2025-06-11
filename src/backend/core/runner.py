"""Command line entry point for the backend."""

import argparse
import asyncio

from ..stt import VoskStream
from ..agent.simple import EchoAgent
from ..tts.simple import ConsoleTTS
from .backend import ChatBackend


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the chat backend")
    parser.add_argument("model", help="Path to Vosk model")
    parser.add_argument("--turns", type=int, default=-1, help="Number of turns to process")
    args = parser.parse_args()

    stt = VoskStream(args.model)
    agent = EchoAgent()
    tts = ConsoleTTS()

    backend = ChatBackend(stt, agent, tts)
    asyncio.run(backend.run(turns=args.turns))


if __name__ == "__main__":
    main()
