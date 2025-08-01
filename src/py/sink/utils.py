import dataclasses
from json import dumps, dump, JSONEncoder
from typing import Any, Optional, TextIO
from pathlib import Path
import os
import subprocess  # nosec: B404


class EnhancedJSONEncoder(JSONEncoder):
	def default(self, o: Any) -> Any:
		if dataclasses.is_dataclass(o) and not isinstance(o, type):
			return dataclasses.asdict(o)
		return super().default(o)


def asJSON(value: Any, stream: Optional[TextIO] = None) -> Optional[str]:
	if stream:
		dump(value, stream, cls=EnhancedJSONEncoder)
		return None
	else:
		return dumps(value, cls=EnhancedJSONEncoder)


def dotfile(name: str, base: Optional[Path] = None) -> Optional[Path]:
	"""Looks for the file `name` in the current directory or its ancestors"""
	user_home: Optional[str] = os.getenv("HOME")
	path = Path(base or ".").absolute()
	while path != path.parent:
		if (loc := path / name).exists():
			return loc
		if str(path) != user_home:
			path = path.parent
		else:
			break
	return None


def difftool(origin: Path, *other: Path) -> None:
	# NOTE: We assume 2 way diff for now
	tool: str = os.getenv("SINK_DIFF") or os.getenv("DIFFTOOL") or "diff -u"
	prefix = [_.strip() for _ in tool.split() if _.strip()]
	for _ in other:
		# We resolve the paths so that we get the actual files
		cmd: list[str] = prefix + [
			str(origin.resolve().absolute()),
			str(_.resolve().absolute()),
		]
		subprocess.run(cmd, capture_output=False)  # nosec: B603


class CommandError(Exception):
	def __init__(self, command: list[str], status: int, err: bytes):
		super().__init__()
		self.command = command
		self.status = status
		self.err = err

	def __str__(self) -> str:
		return f"CommandError: '{' '.join(self.command)}', failed with status {self.status}: {self.err!r}"


# FIXME: Does not do streaming
def shell(
	command: list[str], cwd: Optional[str] = None, input: Optional[bytes] = None
) -> bytes:
	"""Runs a shell command, and returns the stdout as a byte output"""
	# FROM: https://stackoverflow.com/questions/163542/how-do-i-pass-a-string-into-subprocess-popen-using-the-stdin-argument#165662
	res = subprocess.run(  # nosec: B603
		command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=input
	)
	if res.returncode == 0:
		return res.stdout
	else:
		raise CommandError(command, res.returncode, res.stderr)


# EOF
