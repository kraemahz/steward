import logging

from dataclasses import dataclass
from threading import Thread
from typing import List
from queue import Queue, Empty

import cbor2
from prism import Client
from faster_whisper import WhisperModel
from .event import push_job_result

_log = logging.getLogger(__name__)


@dataclass
class SpeechToTextRequest:
    conversation_id: str
    payload: List[int]
    count: int
    beam: str
    finalize: bool


@dataclass
class SpeechToTextResponse:
    conversation_id: str
    count: int
    payload: str
    finalized: bool


class VoiceThread(Thread):
    QUEUE_POLL_RATE = 1.0

    def __init__(self, client: Client, queue: Queue):
        super().__init__()
        self.client = client
        self.queue = queue
        self.model = WhisperModel('medium',
                                  device='cuda',
                                  compute_type='float16')

    def run(self):
        while True:
            try:
                data = self.queue.get(timeout=self.QUEUE_POLL_RATE)
            except Empty:
                continue
            if data is None:
                break

            try:
                request = SpeechToTextRequest(**cbor2.loads(data))
            except TypeError:
                _log.error("Could not decode to request")
                continue
            transcribed = self.model.transcribe(request.payload)
            response = SpeechToTextResponse(
                request.conversation_id,
                request.count,
                transcribed,
                request.finalized
            )
            push_job_result(self.client, response, request.beam)
