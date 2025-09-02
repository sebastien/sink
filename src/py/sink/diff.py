from .model import Node, Snapshot, Status
from typing import Optional

# --
# ## Directory diffing command


def compareNodes(a: Optional[Node], b: Optional[Node]) -> int:
	return 0


def compareSignature(a: Optional[Node], b: Optional[Node]) -> int:
	return 0


def compareMeta(a: Optional[Node], b: Optional[Node]) -> int:
	return 0


def status(origin: Optional[Node], *others: Optional[Node]) -> list[Status]:
	"""Maps the status of a node, with respect to the other nodes"""
	res = []
	added_count = 0
	removed_count = 0
	newer_count = 0
	older_count = 0
	changed_count = 0
	# NOTE: Leaving this for debug
	# row = [origin] + [_ for _ in others]
	# path = [_ for _ in row if _][0]
	# path = path.path if path else None
	# print("".join(["-" if _ is None else "X" for _ in row]), path)
	for other in others:
		if other is None:
			if not origin:
				res.append(Status.ABSENT)
			else:
				res.append(Status.REMOVED)
				removed_count += 1
		elif not origin:
			res.append(Status.ADDED)
			added_count += 1
		# TODO: We should distinguish between type, content and meta changes
		elif other.hasChanged(origin):
			if other.isNewer(origin):
				res.append(Status.NEWER)
				changed_count += 1
				newer_count += 1
			elif other.isOlder(origin):
				res.append(Status.OLDER)
				older_count += 1
				changed_count += 1
			else:
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


# TODO: Should do sha vs time
def diff(*snapshots: Snapshot) -> dict[str, list[Status]]:
	"""Compares the list of snapshots, returning a list of status per snapshot"""
	states: dict[str, list[Optional[Node]]] = {}
	n: int = len(snapshots)
	# This fills in states as a sparse matrix of nodes (rows) by
	# snapshots.
	for i, s in enumerate(snapshots):
		# For each node of the snapshot
		for node in s.nodes.values():
			# We create a row if it's not there
			if node.path not in states:
				states[node.path] = [None] * n
			# And we assign the node
			states[node.path][i] = node
	# FIXME: The sort here may be an issue performance-wise
	return {path: status(*sources) for path, sources in sorted(states.items())}


# EOF
