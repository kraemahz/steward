import json
import logging

from dataclasses import asdict, dataclass
from queue import Queue
from typing import Any, Dict

from prism import Client, Wavelet

_log = logging.getLogger(__name__)


@dataclass
class PrismConfig:
    addr: str
    event_pairs: Dict[str, str]


def push_job_result(client: Client, result: Any, source: str):
    result = asdict(result)
    json_text = json.dumps(result)
    json_bytes = json_text.encode('utf-8')
    client.emit(source, json_bytes)


def connect_to_event_listener(config: PrismConfig, queue: Queue):
    def event_handler(wavelet: Wavelet):
        response_beam = config.event_pairs[wavelet.beam]
        for photon in wavelet.photons:
            data = photon.payload
            queue.put((data, response_beam))

    client = Client(f"ws://{config.addr}", event_handler)
    for event_sink, event_source in config.event_pairs.items():
        client.add_beam(event_source)
        client.subscribe(event_sink)

    return client
