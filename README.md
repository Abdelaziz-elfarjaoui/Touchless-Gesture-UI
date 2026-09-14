# Touchless Gesture Control System

Professional modular version of the touchless Arduino + OpenCV/MediaPipe project.

## Structure
- `main.py` — current application entry point/baseline UI
- `config.py` — all configuration and timing parameters
- `hardware/arduino.py` — serial communication and state parsing
- `vision/hand_tracker.py` — MediaPipe hand tracking and smoothing
- `control/motor.py` — motor speed and safety-stop logic
- `control/leds.py` — LED state management
- `logger.py` — timestamped event logging
- `logs/system.log` — generated event history
- `models/hand_landmarker.task` — MediaPipe model file

## Run
Put `hand_landmarker.task` in `models/`, install requirements, close Arduino Serial Monitor, then:

`python main.py`

The original working UI is retained in `main.py`; the modules are the new professional service layer for the next integration step.
