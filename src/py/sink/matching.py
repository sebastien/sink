from typing import NamedTuple, Iterable, Optional
import re
import os
import sys
import fnmatch
from enum import Enum
from pathlib import Path
from .utils import shell, dotfile


# --
# We define filters which have three levels: rejects, keeps, and accepts.
# Rejected filters will reject any matching file, except if it matches a
# keep. Reject/keeps act as an "excludes" filter. The accepts filter is
# only used when you need a restricted set of files, ie "includes.".


class RawFilters(NamedTuple):
	rejects: Optional[list[str]] = None
	accepts: Optional[list[str]] = None
	keeps: Optional[list[str]] = None


class Filters(NamedTuple):
	rejects: Optional[re.Pattern[str]] = None
	accepts: Optional[re.Pattern[str]] = None
	keeps: Optional[re.Pattern[str]] = None


class FilterCategory(Enum):
	Rejects = 0
	Accepts = 1
	Keeps = 2


def makeFilterList(
	items: Optional[list[str]],
	setlist: Optional[list[str]],
	sets: dict[str, RawFilters],
	category: FilterCategory,
) -> Optional[list[str]]:
	"""A helper function for filters"""
	if items or setlist:
		res: list[str] = items if items else []
		for s in setlist or []:
			if not sets:
				raise RuntimeError(
					f"Given sets is empty, cannot retrieve set '{s}': {sets}"
				)
			elif s not in sets:
				raise ValueError(
					f"Unknown set '{s}', pick one of: {', '.join(_ for _ in sets)}"
				)
			res += sets[s][category.value] or []
		return res
	else:
		return None


def makePattern(
	items: Optional[list[str]],
	setlist: Optional[list[str]],
	sets: dict[str, RawFilters],
	category: FilterCategory,
) -> Optional[re.Pattern[str]]:
	"""A helper function for filters"""
	return pattern(makeFilterList(items, setlist, sets, category))


def combine(a: Optional[list[str]], b: Optional[list[str]]) -> Optional[list[str]]:
	return None if a is None and b is None else (a or []) + (b or [])


def rawfilters(
	*,
	rejects: Optional[list[str]] = None,
	accepts: Optional[list[str]] = None,
	keeps: Optional[list[str]] = None,
	rejectSet: Optional[list[str]] = None,
	acceptSet: Optional[list[str]] = None,
	keepSet: Optional[list[str]] = None,
	filterSet: Optional[list[str]] = None,
) -> RawFilters:
	sets: dict[str, RawFilters] = {
		_: filterset(_)
		for _ in set(
			(rejectSet or []) + (acceptSet or []) + (keepSet or []) + (filterSet or [])
		)
	}
	accepted = makeFilterList(
		accepts, combine(acceptSet, filterSet), sets, FilterCategory.Accepts
	)
	rejected = makeFilterList(
		rejects, combine(rejectSet, filterSet), sets, FilterCategory.Rejects
	)
	kept = makeFilterList(
		keeps, combine(keepSet, filterSet), sets, FilterCategory.Keeps
	)
	if rejected is None and accepted is None and kept is None:
		f = gitignored()
		return RawFilters(accepts=None, rejects=f.rejects, keeps=f.keeps)
	else:
		return RawFilters(accepts=accepted, rejects=rejected, keeps=kept)


def filters(
	*,
	rejects: Optional[list[str]] = None,
	accepts: Optional[list[str]] = None,
	keeps: Optional[list[str]] = None,
	rejectSet: Optional[list[str]] = None,
	acceptSet: Optional[list[str]] = None,
	keepSet: Optional[list[str]] = None,
	filterSet: Optional[list[str]] = None,
) -> Filters:
	sets: dict[str, RawFilters] = {
		_: filterset(_)
		for _ in set(
			(rejectSet or []) + (acceptSet or []) + (keepSet or []) + (filterSet or [])
		)
	}
	accepted = makePattern(
		accepts, combine(acceptSet, filterSet), sets, FilterCategory.Accepts
	)
	rejected = makePattern(
		rejects, combine(rejectSet, filterSet), sets, FilterCategory.Rejects
	)
	kept = makePattern(keeps, combine(keepSet, filterSet), sets, FilterCategory.Keeps)
	if rejected or accepted or kept:
		return Filters(accepts=accepted, rejects=rejected, keeps=kept)
	else:
		f = gitignored()
		return Filters(accepts=None, rejects=pattern(f.rejects), keeps=pattern(f.keeps))


RE_EXACT = re.compile(r"^(/|./)(?P<path>.*)$")


def globre(text: str) -> str:
	"""Converts a glob to regexp.

	We strip the wrapper that `fnmatch.translate` adds, which typically
	adds a `(?s:...)` prefix and a `)\\Z` or `)\\z` suffix around the
	translated pattern. We accept either suffix to remain compatible with
	different Python versions.
	"""
	t: str = fnmatch.translate(text)
	p: str = "(?s:"
	if t.startswith(p):
		t = t[len(p) :]
	for s in (")\\Z", ")\\z"):
		if t.endswith(s):
			t = t[: -len(s)]
			break
	return t


def pattern(
	patterns: Optional[Iterable[str]],
) -> Optional[re.Pattern[str]]:
	"""We compile expressions to regexes as we're going to run a ton of them. This
	is for exact matches. Patterns starting with `./` or `/` are considered full
	paths (exact)"""
	if patterns is None:
		return None
	exact: list[str] = []
	partial: list[str] = []
	for p in patterns:
		if m := RE_EXACT.match(p):
			exact.append(m.group("path"))
		else:
			partial.append(p)
	expr_exact, expr_partial = [
		"|".join(globre(_) for _ in p) for p in (exact, partial)
	]
	re_raw: str = (
		f"^({expr_exact}|{expr_partial})(/.*)?$"
		if (expr_exact and expr_partial)
		else f"^({expr_exact or expr_partial})(/.*)?$"
	)
	try:
		return re.compile(re_raw)
	except Exception as e:
		sys.stderr.write(f"ERR Bad regexp pattern {re_raw}\n")
		raise e from e


def matches(
	value: str,
	*,
	accepts: Optional[re.Pattern[str]] = None,
	rejects: Optional[re.Pattern[str]] = None,
	keeps: Optional[re.Pattern[str]] = None,
) -> bool:
	"""Tells if the given value passes the `accepts` and `rejects` filters."""
	if rejects and rejects.match(value):
		if not (keeps and keeps.match(value)):
			return False
	if accepts and not accepts.match(value):
		return False
	else:
		return True


def filterset(collection: str) -> RawFilters:
	"""Returns"""
	match collection:
		case "none":
			return RawFilters()
		case "git":
			return RawFilters(
				accepts=[
					_
					for _ in str(
						shell(["git", "ls-tree", "-r", "HEAD", "--name-only"]), "utf8"
					).split("\n")
					if _.strip()
				]
			)
		case "gitignore":
			return gitignored()
		case _:
			raise ValueError(
				f"Unsupported category '{collection}', pick one of: git, gitignore"
			)


DEFAULT_KEEPS: list[str] = []
DEFAULT_REJECTS = [".git", ".svg", "*.swp", ".cache", "*.pyc"]


def gitignored(path: Optional[Path] = None) -> RawFilters:
	"""Returns the list of patterns that are part of the `gitignore` file."""
	keeps: list[str] = [] + DEFAULT_KEEPS
	rejects: list[str] = [] + DEFAULT_REJECTS
	for p in [
		Path(_)
		for _ in (
			[f"{os.environ['HOME']}/.gitignore", dotfile(".gitignore")]
			if not path
			else [path]
		)
		if _ is not None
	]:
		if p and p.exists():
			with open(p, "rt") as f:
				for pattern in f.readlines():
					pattern = pattern.strip().rstrip("\n").strip()
					if pattern.startswith("#") or not pattern:
						continue
					if pattern.startswith("!"):
						keeps.append(pattern[1:])
					else:
						rejects.append(pattern)
	return RawFilters(keeps=keeps, rejects=rejects)


# EOF
