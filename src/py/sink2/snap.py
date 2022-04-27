from typing import Optional, Iterator, Iterable, Any, cast
from dataclasses import dataclass
import os
import stat
import hashlib
import json
from .utils import asJSON


# --
# This is a re-implementation of Sink (V1) backend, with a few different
# takes. First is to use type annotation as much as possible, second is
# to use


class NodeDifference:
    """Flags to capture the difference between when comparing nodes"""

    path = 0b0001
    type = 0b0010
    meta = 0b0100
    signature = 0b1000


class NodeType:
    """A simplified categorisation of node types"""

    NULL: int = 0
    FILE: int = 1
    LINK: int = 2
    DIRECTORY: int = 3
    SPECIAL: int = 10
    UNKNOWN: int = 100


@dataclass
class NodeMeta:
    """Captures the node metadata that is part of the snapshot"""

    mode: int
    uid: int
    gid: int
    size: int
    ctime: float
    mtime: float

    @staticmethod
    def FromDict(data: dict[str, Any]) -> "NodeMeta":
        assert isinstance(data, dict), f"Expected dict, got: {data}"
        return NodeMeta(**data)


@dataclass
class Node:
    path: str
    type: int
    meta: Optional[NodeMeta] = None
    sig: Optional[str] = None

    @staticmethod
    def FromDict(data: dict[str, Any]) -> "Node":
        assert isinstance(data, dict), f"Expected dict, got: {data}"
        return Node(
            path=data["path"],
            type=data.get("type", NodeType.NULL),
            meta=NodeMeta.FromDict(cast(dict, data.get("meta")))
            if "meta" in data
            else None,
            sig=data.get(
                "sibl",
            ),
        )


class Operations:
    @classmethod
    def Index(cls, nodes: Iterator[Node]) -> dict[str, Node]:
        return {_.path: _ for _ in nodes}

    @classmethod
    def IsSame(cls, a: Node, b: Node) -> bool:
        return a.sig == b.sig and a.meta == b.meta

    @classmethod
    def IsOlder(cls, a: Node, b: Node) -> bool:
        if a.meta == None:
            return True
        elif b.meta == None:
            return False
        else:
            return a.meta.mtime < b.meta.mtime


class FileSystem:
    """An abstraction of key operations involved in snapshotting filesystems"""

    @classmethod
    def walk(cls, path: str, followLinks=False) -> Iterator[Node]:
        """Walks the given path and produces nodes augmented with metadata"""
        for dirpath, _, filenames in os.walk(path, followlinks=followLinks):
            for _ in filenames:
                path = f"{dirpath}/{_}"
                if os.path.exists(path):
                    meta = cls.meta(path)
                    node_type = (
                        NodeType.FILE
                        if stat.S_ISREG(meta.mode)
                        else NodeType.DIRECTORY
                        if stat.S_ISREG(meta.mode)
                        else NodeType.LINK
                        if stat.S_ISLNK(meta.mode)
                        else NodeType.SPECIAL
                    )
                    yield Node(path, node_type, meta, cls.signature(path))
                else:
                    yield Node(path, NodeType.NULL, None, None)

    @classmethod
    def meta(cls, path: str) -> NodeMeta:
        """Returns the meta"""
        r = os.stat(path)
        return NodeMeta(
            mode=r.st_mode,
            uid=r.st_uid,
            gid=r.st_gid,
            size=r.st_size,
            ctime=r.st_ctime,
            mtime=r.st_mtime,
        )

    @classmethod
    def signature(cls, path: str) -> str:
        """Returns the signature of the file contents, as a string"""
        h = hashlib.new("sha512_256")
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()


class Snapshot:
    @staticmethod
    def Load(path: str) -> "Snapshot":
        with open(path, "rt") as f:
            return Snapshot(Node.FromDict(_) for _ in json.load(f).values())

    def __init__(self, nodes: Optional[Iterable[Node]] = None):
        self.nodes: dict[str, Node] = {}
        if nodes:
            self.extend(nodes)

    def save(self, path: str):
        with open(path, "wt") as f:
            asJSON(self.nodes, f)
        return self

    def extend(self, nodes: Iterable[Node]):
        for node in nodes:
            if (path := node.path) in self.nodes:
                raise RuntimeError(f"Node already registered: {path}")
            self.nodes[path] = node
        return self


def snapshot(*path: str) -> Snapshot:
    res = Snapshot()
    for p in path:
        res.extend(FileSystem.walk(p))
    return res


# EOF
