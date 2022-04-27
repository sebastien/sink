from typing import Iterator
import os
import stat
import hashlib
from .model import Node, NodeType, NodeMeta, Snapshot, Optional
from .utils import matches


class FileSystem:
    """An abstraction of key operations involved in snapshotting filesystems"""

    @classmethod
    def walk(
        cls,
        path: str,
        followLinks=False,
        accepts: Optional[list[str]] = None,
        rejects: Optional[list[str]] = None,
    ) -> Iterator[Node]:
        """Walks the given path and produces nodes augmented with metadata"""
        abs_path = os.path.abspath(path)
        offset = len(abs_path) + 1
        ignored: dict[str, bool] = {}
        print("IGNORED", ignored)
        for dirpath, dirnames, filenames in os.walk(abs_path, followlinks=followLinks):
            is_ignored = dirpath in ignored
            if is_ignored:
                for _ in dirnames:
                    if not matches(_, accepts, rejects):
                        ignored[f"{dirpath}/{_}"] = True
            else:
                for _ in filenames:
                    path = f"{dirpath}/{_}"
                    print("XXX ", path, (accepts, rejects))
                    if not matches(path, accepts, rejects):
                        continue
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
                        yield Node(
                            path[offset:],
                            node_type,
                            meta,
                            cls.signature(path) if node_type == NodeType.FILE else None,
                        )
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


def snapshot(
    path: str, accepts: Optional[list[str]] = None, rejects: Optional[list[str]] = None
) -> Snapshot:
    return Snapshot(FileSystem.walk(path, accepts, rejects))


# EOF
