import dataclasses
from json import dumps, dump, JSONEncoder
from typing import Any, Optional, TextIO


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def json(value: Any, stream: Optional[TextIO] = None) -> Optional[str]:
    if stream:
        dump(value, stream, cls=EnhancedJSONEncoder)
        return None
    else:
        return dumps(value, cls=EnhancedJSONEncoder)


# EOF
