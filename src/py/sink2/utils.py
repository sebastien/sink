import dataclasses
from json import dumps, dump, JSONEncoder
from typing import Any, Optional, TextIO
from pathlib import Path
import os
import fnmatch


class EnhancedJSONEncoder(JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def asJSON(value: Any, stream: Optional[TextIO] = None) -> Optional[str]:
    if stream:
        dump(value, stream, cls=EnhancedJSONEncoder)
        return None
    else:
        return dumps(value, cls=EnhancedJSONEncoder)


def matches(
    value: str, accepts: Optional[list[str]] = None, rejects: Optional[list[str]] = None
) -> bool:
    for pat in accepts or []:
        if fnmatch.fnmatch(value, pat):
            return True
    for pat in rejects or []:
        if fnmatch.fnmatch(value, pat):
            return False
    return matches(value.rsplit("/")[-1], accepts, rejects) if "/" in value else True


def gitignored(path: Path = Path(os.path.expanduser("~/.gitignore"))) -> list[str]:
    res: list[str] = []
    if path.exists():
        with open(path, "rt") as f:
            for pattern in f.readlines():
                pattern = pattern.strip().rstrip("\n")
                if pattern.startswith("#"):
                    continue
                res.append(pattern)
    return res


# EOF
