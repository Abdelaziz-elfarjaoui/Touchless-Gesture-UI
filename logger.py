from collections import deque
from datetime import datetime
from pathlib import Path

class EventLogger:
    def __init__(self, path='logs/system.log', max_events=10):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events = deque(maxlen=max_events)
    def log(self, message):
        entry = f'{datetime.now():%Y-%m-%d %H:%M:%S}  {message}'
        self.events.appendleft(entry)
        try:
            with self.path.open('a', encoding='utf-8') as f: f.write(entry+'\n')
        except OSError: pass
        return entry
