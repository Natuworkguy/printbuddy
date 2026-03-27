# PrintBuddy

**PrintBuddy** is a lightweight desktop serial console for 3D printers.

Connect quickly, send G-code commands, and monitor live device responses in a clean Tkinter UI.

## Features

- Serial connection UI with configurable port input
- Send commands from an interactive console input
- Real-time response log window
- Copy log contents to clipboard

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python run.py
```

## Notes

- The app uses `pyserial` for serial communication.
- A bundled resource helper is included for packaged builds.
