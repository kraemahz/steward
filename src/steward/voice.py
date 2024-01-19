from threading import Thread
from queue import Queue, Empty

import numpy
from faster_whisper import WhisperModel


class VoiceThread(Thread):
    QUEUE_POLL_RATE = 1.0

    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        self.model = WhisperModel('medium',
                                  device='cuda',
                                  compute_type='float16')

    def run(self):
        while True:
            try:
                entry = self.queue.get(timeout=self.QUEUE_POLL_RATE)
            except Empty:
                continue

            if entry is None:
                break

            (data, response_beam) = entry

            data = numpy.array(data, dtype='uint16')
            self.model.transcribe(data)
