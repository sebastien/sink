from enum import Enum
from time import monotonic as now
from typing import Optional, Union, Any
from dataclasses import dataclass
import json


class Level(Enum):
    LOG = 0


class Metric:
    THROTTLING = 1.0

    def __init__(self, name: str, value: int = 0):
        self.name: str = name
        self.value = value
        self.update = now()
        self.last = value

    def inc(self):
        self.value += 1
        t = now()
        if t - self.update < self.THROTTLING:
            pass
        else:
            show(self)


@dataclass
class Event:
    name: str
    value: Optional[dict] = None


@dataclass
class Log:
    message: str
    level: Level
    data: Optional[dict] = None


class Counter(Metric):
    pass


def fmtJSON(data):
    json.dumps(data)


def fmtPairs(data: dict):
    return ", ".join(f"{k}={fmtJSON(v)}" for k, v in data.items()) if data else ""


def show(data: Union[Log, Metric, Event]):
    if isinstance(data, Event):
        print(f" → {data.name}: {fmtJSON(data.value)}")
    elif isinstance(data, Metric):
        print(f" . {data.name}={data.value}")
    elif isinstance(data, Log):
        print(f" ! {data.message}: {fmtPairs(metric.data)}")
    else:
        pass


METRICS: dict[str, Metric] = {}


def metric(name: str) -> Metric:
    if name not in METRICS:
        METRICS[name] = Metric(name)
    return METRICS[name]


def event(name: str, data: Optional[dict[str, Any]]):
    show(Event(name, data))


def log(message: str, level: Level = Level.LOG, data: Optional[dict[str, Any]] = None):
    show(Log(message, level, data))


# EOF
