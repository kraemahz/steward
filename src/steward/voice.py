import logging

from dataclasses import dataclass
from threading import Thread
from typing import List
from queue import Queue

import cbor2
import numpy as np
from prism import Client
from whisper import load_model
from .event import push_job_result

_log = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    device: str
    model: str


@dataclass
class SpeechToTextRequest:
    conversation_id: str
    payload: List[float]
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

    def __init__(self, client: Client, queue: Queue, config: WhisperConfig):
        super().__init__()
        self.client = client
        self.queue = queue
        self.config = config
        self.model = load_model(config.model)

    def run(self):
        while True:
            data = self.queue.get()
            if data is None:
                break

            try:
                request = SpeechToTextRequest(**cbor2.loads(data))
            except TypeError:
                _log.error("Could not decode to request")
                continue

            payload = np.array(request.payload, dtype=np.float32)
            transcribed = self.model.transcribe(payload)
            text = transcribed['text']
            response = SpeechToTextResponse(
                request.conversation_id,
                request.count,
                text,
                request.finalize
            )
            push_job_result(self.client, response, request.beam)
