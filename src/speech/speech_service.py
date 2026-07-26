import threading
import queue

class SpeechService:
    def __init__(self, engine):
        self.engine = engine
        self.commands = queue.Queue()

        self.thread = threading.Thread(
            target=self.worker,
            daemon=True
        )

        self.thread.start()

    def worker(self):
        while True:
            command, data = self.commands.get()
            if command == "speak":
                self.engine.speak(data)
            elif command == "stop":
                self.engine.stop()

    def speak_text(self, text):
        while not self.commands.empty():
            try:
                self.commands.get_nowait()
            except queue.Empty:
                break

        self.commands.put(("speak", text))

    def stop(self):
        self.commands.put(("stop", None))