# Backend Installer and Runner Plan

This document outlines a proposed script to set up and run the project backend. The goal is a single command that prepares the environment, installs missing dependencies and launches all services with a convenient console interface.

## 1. Virtual Environment Management

- Target **Python 3.12**.
- When invoked, the script should check for an existing `venv` directory. If not found, it will create a virtual environment using `python3.12 -m venv venv`.
- The script will then activate the environment before running any further commands.

## 2. Dependency Installation

- After activation, it will inspect installed Python packages and compare them with `requirements.txt` and `requirements-dev.txt` (if present).
- For STT and TTS models (e.g. Vosk model files or Orpheus voice checkpoints), the script detects if the required files are present in the expected directories.
- If anything is missing, the user is asked for permission to download from the Internet. Declining the prompt aborts the run.
- The script uses `pip install -r requirements.txt` and downloads model archives only when the user agrees.

## 3. Console Layout

A tmux-like layout is recommended. The layout consists of three panes:

1. **Top Left (2/3 width)** – continuously tails `transcript.log`. Applies colours to make the timestamp distinct. Incoming text (denoted by '< ') and outgoing text (denoted by '> ') are coloured differently.
2. **Top right (1/3 width)** – shows the backend configuration. Properties and values are coloured differently.
3. **Bottom Left (2/3 width)** – shows log output from the WebSocket streaming backend.
4. **Bottom Right (1/3 width)** – displays output from `npm run dev` for the React frontend.

The bottom line of the terminal shows a small prompt accepting single-letter commands:

- `Q` – quit all running processes and exit.
- `R` – restart the backend services (relaunch the WebSocket server and refresh the log panes).

The current timestamp is displayed right justified on the bottom line.

## 4. Implementation Options

Below are possible approaches to implement the console interface.

### a. tmux

- **Pros:** well‑tested, multiplexed terminal support; easy splitting and pane management; native key bindings for scripting.
- **Cons:** external dependency; not installed on all systems by default.

### b. Python curses

- **Pros:** no external dependencies beyond the standard library; full control over the layout.
- **Cons:** more manual work to manage subprocesses and window resizing; limited scrollback compared to tmux.

### c. Rich library (`rich.console`, `rich.live`)

- **Pros:** modern Python interface with colors and layout helpers; cross‑platform.
- **Cons:** not designed for complex pane layouts; implementing a persistent prompt with multiple subprocess outputs is non‑trivial.

The *Rich* library will be used, as neither tmux nor screen are installed by default on MacOS.

## 5. Startup Workflow

1. Ensure the virtual environment exists and is active.
2. Validate that Python dependencies and required models are installed, prompting before any downloads.
3. Create an empty `transcript.log` if it does not already exist.
4. Launch a Rich application with the layout described above:
   - Pane 1: displays a colourised equivalent of `tail -n 100 -F transcript.log`
   - Pane 2: displays a view of the current config, with colours distinguishing property names from values
   - Pane 3: run the WebSocket streamer backend (e.g. `python -m src.backend.server > backkend.log`) and display a colourised equivalent of `tail -F backend.log`
   - Pane 4: display the output of `npm run dev`
5. Display the command prompt on the bottom line for `Q` and `R` actions and show the current timestamp.

This plan provides an installer and runner that simplifies setup and offers a convenient console dashboard for development.
