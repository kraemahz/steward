import logging

from dataclasses import asdict, dataclass
from queue import Queue
from typing import Any, List

import cbor2
from prism import Client, Wavelet

_log = logging.getLogger(__name__)


@dataclass
class PrismConfig:
    addr: str
    events: List[str]


def push_job_result(client: Client, result: Any, source: str):
    result = asdict(result)
    cbor_bytes = cbor2.dumps(result)
    client.emit(source, cbor_bytes)


def connect_to_event_listener(config: PrismConfig, queue: Queue):
    def event_handler(wavelet: Wavelet):
        for photon in wavelet.photons:
            data = photon.payload
            queue.put(data)

    client = Client(f"ws://{config.addr}", event_handler)
    for event_sink in config.events:
        client.subscribe(event_sink)

    return client
