from .model import Node, Snapshot, NodeType
from typing import Optional, Iterator, NamedTuple, Union
import os

# --
# ## Backup operations

Op = Union["OpRm", "OpData", "OpMeta", "OpLn"]

class OpRm(NamedTuple):
    """Remove operation"""
    path: str

class OpData(NamedTuple):
    """Data update operation"""
    path: str

class OpMeta(NamedTuple):
    """Metadata update operation"""
    path: str
    mode: Optional[int] = None
    uid: Optional[int] = None
    gid: Optional[int] = None
    ctime: Optional[float] = None
    mtime: Optional[float] = None

class OpLn(NamedTuple):
    """Symlink operation"""
    path: str
    origin: str

def iops(current: Snapshot, other: Optional[Snapshot] = None) -> Iterator[Op]:
    """Streams operations to unify `other` with `current`"""
    # Get all paths from both snapshots
    all_paths = set(current.nodes.keys())
    if other:
        all_paths.update(other.nodes.keys())

    for path in sorted(all_paths):
        current_node = current.nodes.get(path)
        other_node = other.nodes.get(path) if other else None

        if current_node and not other_node:
            # Path exists in current but not in other - create it
            if current_node.type == NodeType.FILE:
                yield OpData(path)
            elif current_node.type == NodeType.LINK:
                # For symlinks, we need to read the actual target from filesystem
                # Since Node doesn't store the target, we'll need to read it
                try:
                    target = os.readlink(path)
                    yield OpLn(path, target)
                except OSError:
                    # If we can't read the link, skip it
                    pass
            # Also yield metadata if present
            if current_node.meta:
                yield OpMeta(
                    path,
                    mode=current_node.meta.mode,
                    uid=current_node.meta.uid,
                    gid=current_node.meta.gid,
                    ctime=current_node.meta.ctime,
                    mtime=current_node.meta.mtime
                )

        elif other_node and not current_node:
            # Path exists in other but not in current - remove it
            yield OpRm(path)

        elif current_node and other_node:
            # Path exists in both - check for differences
            if current_node.hasContentChanged(other_node):
                if current_node.type == NodeType.FILE:
                    yield OpData(path)
                elif current_node.type == NodeType.LINK:
                    try:
                        target = os.readlink(path)
                        yield OpLn(path, target)
                    except OSError:
                        pass

            if current_node.hasMetaChanged(other_node):
                if current_node.meta and other_node.meta:
                    # Only yield changed attributes
                    mode = current_node.meta.mode if current_node.meta.mode != other_node.meta.mode else None
                    uid = current_node.meta.uid if current_node.meta.uid != other_node.meta.uid else None
                    gid = current_node.meta.gid if current_node.meta.gid != other_node.meta.gid else None
                    ctime = current_node.meta.ctime if current_node.meta.ctime != other_node.meta.ctime else None
                    mtime = current_node.meta.mtime if current_node.meta.mtime != other_node.meta.mtime else None

                    if any([mode, uid, gid, ctime, mtime]):
                        yield OpMeta(path, mode, uid, gid, ctime, mtime)

def iscript(current: Snapshot, other: Optional[Snapshot] = None, root: str = "") -> Iterator[str]:
    """Converts operations into script command strings"""
    # Header comment
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    src_name = "SRC_PATH" if other else "PATH_OR_SNAPSHOT"
    other_name = "PATH_OR_SNAPSHOT" if other else "empty"
    yield f"# Backup of {src_name} from {other_name} on {timestamp}"

    for op in iops(current, other):
        path = os.path.join(root, op.path) if root else op.path

        if isinstance(op, OpRm):
            yield f"RM {path}"
        elif isinstance(op, OpData):
            yield f"DATA {path}"
        elif isinstance(op, OpMeta):
            parts = []
            if op.mode is not None:
                parts.append(f"mode={op.mode}")
            if op.uid is not None:
                parts.append(f"uid={op.uid}")
            if op.gid is not None:
                parts.append(f"gid={op.gid}")
            if op.ctime is not None:
                parts.append(f"ctime={op.ctime}")
            if op.mtime is not None:
                parts.append(f"mtime={op.mtime}")
            if parts:
                yield f"META {path} {' '.join(parts)}"
        elif isinstance(op, OpLn):
            yield f"LN {path} {op.origin}"

# EOF