import os
import hashlib
from pathlib import Path
from typing import Optional, Iterable, NamedTuple, TextIO, Dict, Set, Union

# --
# # Snap
#
# Snap is a simple Python module that takes a snapshot of one directory and allows to compare
# the result later one. It is a simplified reimplementation of the key functionality
# provided in [Sink](https://github.com/sebastien/sink).

Stat = NamedTuple(
    "Stat",
    [
        ("mode", int),
        ("uid", int),
        ("gid", int),
        ("size", int),
        ("ctime", float),
        ("mtime", float),
    ],
)

PathElement = NamedTuple(
    "PathElement", [("path", str), ("meta", Optional[Stat]), ("sig", Optional[str])]
)


def file_meta(path: str) -> Stat:
    r = os.stat(path)
    return Stat(
        mode=r.st_mode,
        uid=r.st_uid,
        gid=r.st_gid,
        size=r.st_size,
        ctime=r.st_ctime,
        mtime=r.st_mtime,
    )


def file_sig(path: str) -> Optional[str]:
    h = hashlib.new("sha512_256")
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def walk(path: str) -> Iterable[PathElement]:
    for dirpath, _, filenames in os.walk(path, followlinks=False):
        for _ in filenames:
            path = f"{dirpath}/{_}"
            if os.path.exists(path) and os.path.isfile(path):
                meta = file_meta(path)
                sig = file_sig(path)
                yield PathElement(path, meta, sig)
            else:
                yield PathElement(path, None, None)


def index(elements: Iterable[PathElement]) -> Dict[str, PathElement]:
    return dict((_.path, _) for _ in elements)


def same(a: PathElement, b: PathElement) -> bool:
    return a.sig == b.sig and a.meta == b.meta


def older(a: PathElement, b: PathElement) -> bool:
    if a.meta == None:
        return True
    elif b.meta == None:
        return False
    else:
        return a.meta.mtime < b.meta.time


def read(stream: Union[str, Path, TextIO]) -> Iterable[PathElement]:
    if isinstance(stream, str) or isinstance(stream, Path):
        with open(stream) as f:
            yield from read(f)
    else:
        for i, line in enumerate(stream.readlines()):
            res = parse(line)
            if not res:
                raise RuntimeError(f"Malformed line {i}: {repr(line)}")
            else:
                yield res


def write(elements: Iterable[PathElement], stream: TextIO):
    for _ in elements:
        stream.write(fmt(_))


def parse(line: str) -> PathElement:
    fields = line.split("\t")
    if len(fields) != 3:
        return None
    else:
        path, meta, sig
        return PathElement(
            path,
            Stat(*((int if i < 4 else float)(_) for i, _ in enumerate(meta.split(","))))
            if meta
            else None,
            sig if sig else None,
        )


def fmt(element: PathElement) -> str:
    path, meta, sig = element
    return f"{path}\t{','.join(str(_) for _ in meta) if meta else ''}\t{sig if sig else ''}"


def paths(indexes: Iterable[Dict[str, PathElement]]) -> Set[str]:
    res = set()
    for _ in indexes:
        res = res.union(k for k in _)
    return res


def compare(paths: Iterable[str]) -> Iterable[Tuple[str, List[str]]]:
    sources = [index(read(_)) for _ in paths]
    all_paths = paths(sources)
    for p in all_paths:
        entry = []
        src = None
        o = None
        for i, s in enumerate(sources):
            if i == 0:
                src = s
                o = src[p] if p in src else None
                entry.append("=" if p in s else "!")
            else:
                d = src[p]
                if p not in s:
                    entry.append("!")
                elif not o:
                    entry.append("+")
                elif same(o, d):
                    entry.append("=")
                else:
                    entry.append(">" if older(o, d) else "<")
        yield (p, entry)


# SEP = "\t"
# for path, entries in compare(SOURCES):
#     print(f"{SEP.join(entries)}{SEP}{path}")


# EOF
