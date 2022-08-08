from typing import Iterator
import os
import stat
import hashlib
from .model import Node, NodeType, NodeMeta, Snapshot, Optional
from .utils import matches
from .logging import metric


class FileSystem:
    """An abstraction of key operations involved in snapshotting filesystems"""

    @classmethod
    def walk(
        cls,
        path: str,
        accepts: Optional[list[str]] = None,
        rejects: Optional[list[str]] = None,
        followLinks: bool = False,
    ) -> Iterator[str]:
        """Does a breadth-first walk of the filesystem, yielding non-directory
        paths that match the `accepts` and `rejects` filters."""
        queue: list[str] = [path]
        while queue:
            base_path = queue.pop()
            # TODO: It may be better to use os.walk there...
            for rel_path in os.listdir(base_path):
                if matches(rel_path, accepts, rejects):
                    abs_path = f"{base_path}/{rel_path}"
                    if not followLinks and os.path.islink(abs_path):
                        continue
                    if os.path.isdir(abs_path):
                        queue.append(abs_path)
                    else:
                        # TODO: Should we follow symlinks?
                        yield abs_path

    @classmethod
    def nodes(
        cls,
        path: str,
        *,
        accepts: Optional[list[str]] = None,
        rejects: Optional[list[str]] = None,
    ) -> Iterator[Node]:
        """Walks the given path and produces nodes augmented with metadata"""
        offset = len(path) + 1
        snap_paths = metric("snap.paths")
        for path in cls.walk(path, accepts, rejects, followLinks=False):
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
                snap_paths.inc()
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
        """Returns the meta information"""
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
    path: str,
    *,
    accepts: Optional[list[str]] = None,
    rejects: Optional[list[str]] = None,
) -> Snapshot:
    """Creates a snapshot for the given `path`, given the `accepts` and `rejects`
    filters."""
    return Snapshot(FileSystem.nodes(path, accepts=accepts, rejects=rejects))


# EOF
