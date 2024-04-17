import logging
import os
import subprocess
import tempfile

from dataclasses import dataclass
from threading import Thread
from queue import Queue

import cbor2
from prism import Client
from whisper import load_model, load_audio
from .event import push_job_result

_log = logging.getLogger(__name__)


@dataclass
class WhisperConfig:
    device: str
    model: str


@dataclass
class SpeechToTextRequest:
    conversation_id: str
    payload: bytes
    count: int
    beam: str
    finalize: bool


@dataclass
class SpeechToTextResponse:
    conversation_id: str
    count: int
    payload: str
    finalized: bool


def run_ffmpeg(input_file):
    output_file = tempfile.mktemp() + ".wav"
    subprocess.call(
        ["ffmpeg", "-i", input_file, "-ar", "16000", output_file],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    data = load_audio(output_file)
    os.unlink(output_file)
    return data


class VoiceThread(Thread):
    def __init__(self, client: Client, queue: Queue, config: WhisperConfig):
        super().__init__()
        self.client = client
        self.queue = queue
        self.config = config
        self.model = load_model(config.model)

    def run(self):
        _log.info("Steward has started")
        while True:
            data = self.queue.get()
            if data is None:
                break

            try:
                request = SpeechToTextRequest(**cbor2.loads(data))
            except TypeError:
                _log.error("Could not decode to request")
                continue
            _log.info("Received request")

            with tempfile.NamedTemporaryFile() as f:
                f.write(bytes(request.payload))
                f.flush()
                payload = run_ffmpeg(f.name)

            transcribed = self.model.transcribe(payload)
            text = transcribed["text"]
            _log.info("Sending back: %s", text)
            response = SpeechToTextResponse(
                request.conversation_id, request.count, text, request.finalize
            )
            push_job_result(self.client, response, request.beam)
