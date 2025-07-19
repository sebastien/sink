from typing import Any, Optional
from .model import Node, NodeMeta, NodeType, Snapshot
from .utils import asJSON
import json


class Operations:
	def meta_restore(self, data: Any) -> Optional[NodeMeta]:
		return NodeMeta(**data) if isinstance(data, dict) else None

	def node_restore(self, data: Any) -> Optional[Node]:
		if not isinstance(data, dict):
			return None
		else:
			return Node(
				path=data["path"],
				type=data.get("type", NodeType.NULL),
				meta=self.meta_restore(data.get("meta")),
				sig=data.get("sig"),
			)

	def snapshot_load(self, path: str) -> Optional[Snapshot]:
		with open(path, "rt") as f:
			data = json.load(f)
			if not isinstance(data, dict):
				return None
			else:
				return Snapshot((_ for _ in (self.node_restore(_) for _ in data) if _))

	def snapshot_save(self, path: str, snapshot: Snapshot) -> Snapshot:
		with open(path, "wt") as f:
			asJSON(snapshot.nodes, f)
		return snapshot


# EOF
