from .model import Node, Snapshot, Optional
from enum import Enum


# --
# ## Directory diffing command


class Status(Enum):
    """Defines the status of an entr"""

    ADDED = "[+]"
    REMOVED = " - "
    NEWER = " > "
    OLDER = " < "
    SAME = " = "
    CHANGED = " ~ "
    ABSENT = "-!-"
    ORIGIN = " . "


def compareNodes(a: Optional[Node], b: Optional[Node]) -> int:
    pass


def compareSignature(a: Optional[Node], b: Optional[Node]) -> int:
    pass


def compareMeta(a: Optional[Node], b: Optional[Node]) -> int:
    pass


def status(origin: Optional[Node], *others: Optional[Node]) -> list[Status]:
    """Maps the status of a node, with respect to the other nodes"""
    res = []
    added_count = 0
    removed_count = 0
    newer_count = 0
    older_count = 0
    changed_count = 0
    for other in others:
        if not origin:
            res.append(Status.ADDED)
            added_count += 1
        elif not other:
            res.append(Status.REMOVED)
            removed_count += 1
        elif other.isNewer(origin):
            res.append(Status.NEWER)
            changed_count += 1
            newer_count += 1
        elif other.isOlder(origin):
            res.append(Status.OLDER)
            older_count += 1
            changed_count += 1
        elif other.hasChanged(origin):
            res.append(Status.CHANGED)
            changed_count += 1
        else:
            res.append(Status.SAME)
    # We compare the origin with the rest
    if not origin:
        # No origin means it's absent
        res.insert(0, Status.ABSENT)
    elif newer_count == 0 and older_count:
        # If there's only older others, then it's newer
        res.insert(0, Status.NEWER)
    elif older_count == 0 and newer_count:
        # If there's only newer others, then it's older
        res.insert(0, Status.OLDER)
    elif older_count or newer_count:
        # If there's new and or old, then there's a change
        res.insert(0, Status.CHANGED)
    else:
        # Otherwise it's the origin, as-is
        res.insert(0, Status.ORIGIN)
    return res


def diff(*snapshots: Snapshot) -> dict[str, list[Status]]:
    """Compares the list of snapshots, returning a list of status per snapshot"""
    states: dict[str, list[Optional[Node]]] = {}
    n: int = len(snapshots)
    for i, s in enumerate(snapshots):
        for node in s.nodes.values():
            if node.path not in states:
                states[node.path] = [None] * n
            states[node.path][i] = node
    return {path: status(*sources) for path, sources in states.items()}


# EOF
