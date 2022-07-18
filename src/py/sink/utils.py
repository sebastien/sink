import dataclasses
from json import dumps, dump, JSONEncoder
from typing import Any, Optional, TextIO
from pathlib import Path
import os
import fnmatch
import subprocess


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
    """Tells if the given value passes the `accepts` and `rejects` filters."""
    for pat in accepts or []:
        if fnmatch.fnmatch(value, pat):
            return True
    for pat in rejects or []:
        if fnmatch.fnmatch(value, pat):
            return False
    return matches(value.rsplit("/")[-1], accepts, rejects) if "/" in value else True


def dotfile(name: str, base: Optional[Path] = None) -> Optional[Path]:
    """Looks for the file `name` in the current directory or its ancestors"""
    user_home: Optional[str] = os.getenv("HOME")
    path = Path(base or ".").absolute()
    while path != path.parent:
        if (loc := path / name).exists():
            return loc
        if path != user_home:
            path = path.parent
        else:
            break
    return None


def gitignored(path: Optional[Path] = None) -> list[str]:
    """Returns the list of patterns that are part of the `gitignore` file."""
    path = dotfile(".gitignore") if not path else path
    res: list[str] = []
    if path and path.exists():
        with open(path, "rt") as f:
            for pattern in f.readlines():
                pattern = pattern.strip().rstrip("\n")
                if pattern.startswith("#"):
                    continue
                res.append(pattern)
    return res


def difftool(origin: Path, *other: list[Path]):
    # NOTE: We assume 2 way diff for now
    tool: str = (
        os.getenv("SINK_DIFF") or os.getenv("DIFFTOOL") or os.getenv("EDITOR") or "diff"
    )
    prefix = [_ for _ in (_.strip() for _ in tool.split()) if _]
    for _ in other:
        subprocess.run(prefix + [origin, _])


# EOF
