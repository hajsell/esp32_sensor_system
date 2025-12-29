import queue, threading

class OpenAIAgent:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.q = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

    def enqueue_event(self, data: dict):
        self.q.put(data)

    def _worker(self):
        while True:
            data = self.q.get()
            try:
                # tu wywołanie OpenAI (klient + prompt)
                # wynik możesz emitować do socketio albo logować
                pass
            finally:
                self.q.task_done()
