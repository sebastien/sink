from typing import Optional, Iterable, Iterator
from dataclasses import dataclass
from enum import Enum

# --
# This is a re-implementation of Sink (V1) backend, with a few different
# takes. First is to use type annotation as much as possible, second is
# to use


class Status(Enum):
	"""Defines the status of an entry"""

	# TODO: Remove the spaces
	ADDED = " + "
	REMOVED = " - "
	NEWER = " > "
	OLDER = " < "
	SAME = " = "
	CHANGED = " ~ "
	ABSENT = " ! "
	ORIGIN = " . "


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
	def FromPrimitive(value) -> "NodeMeta":
		return NodeMeta(**value)

	def toPrimitive(self) -> dict:
		return dict(
			mode=self.mode,
			uid=self.uid,
			gid=self.gid,
			size=self.size,
			ctime=self.ctime,
			mtime=self.mtime,
		)


@dataclass
class Node:
	"""Represents the snapshot of a node in a given tree."""

	path: str
	type: int
	meta: Optional[NodeMeta] = None
	sig: Optional[str] = None

	@staticmethod
	def FromPrimitive(value) -> "Node":
		return Node(
			path=value["path"],
			type=value["type"],
			meta=(
				NodeMeta.FromPrimitive(value.get("NodeMeta"))
				if "NodeMeta" in value
				else None
			),
			sig=value.get("sig"),
		)

	def isNewer(self, other: Optional["Node"]) -> bool:
		return other.isOlder(self) if other else True

	def isOlder(self, other: Optional["Node"]) -> bool:
		if self.meta is None:
			return True
		elif other is None or other.meta is None:
			return False
		else:
			return (
				self.meta.mtime < other.meta.mtime
				if self.meta and other.meta
				else False
			)

	def toPrimitive(self) -> dict:
		return {
			"path": self.path,
			"type": self.type,
			"meta": self.meta.toPrimitive() if self.meta else None,
			"sig": self.sig,
		}

	def hasChanged(self, other: Optional["Node"]) -> bool:
		return self.sig != other.sig and self.meta != other.meta if other else False


class Snapshot:
	"""Represents a collection of node states."""

	@staticmethod
	def FromPrimitive(value) -> "Snapshot":
		return Snapshot(
			nodes=(
				{k: Node.FromPrimitive(v) for k, v in value.get("nodes").items()}
				if value.get("nodes")
				else None
			),
		)

	def __init__(self, nodes: Optional[Iterable[Node] | dict[str, Node]] = None):
		self.nodes: dict[str, Node] = nodes if nodes and isinstance(nodes, dict) else {}
		if nodes and not isinstance(nodes, dict):
			self.extend(nodes)

	def extend(self, nodes: Iterable[Node]):
		for node in nodes:
			if (path := node.path) in self.nodes:
				raise RuntimeError(f"Node already registered: {path}")
			self.nodes[path] = node
		return self

	def __iter__(self) -> Iterator[Node]:
		yield from self.nodes.values()

	def toPrimitive(self) -> dict:
		return {"nodes": {k: v.toPrimitive() for k, v in self.nodes.items()}}


class NodePredicates:
	"""Convenience functions to compare nodes"""

	@classmethod
	def IsSame(cls, a: Node, b: Node) -> bool:
		return a.sig == b.sig and a.meta == b.meta

	@classmethod
	def IsOlder(cls, a: Node, b: Node) -> bool:
		if a.meta is None:
			return True
		elif b.meta is None:
			return False
		else:
			return a.meta.mtime < b.meta.mtime if a.meta and b.meta else False


# EOF
