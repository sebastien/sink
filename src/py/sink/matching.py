from typing import NamedTuple, Iterable, Optional
import re
import fnmatch
from pathlib import Path
from .utils import shell, dotfile


class RawFilters(NamedTuple):
    rejects: Optional[list[str]] = None
    accepts: Optional[list[str]] = None


class Filters(NamedTuple):
    rejects: Optional[re.Pattern[str]] = None
    accepts: Optional[re.Pattern[str]] = None


def makePattern(
    items: Optional[list[str]],
    setlist: Optional[list[str]],
    sets: dict[str, RawFilters],
    accepts=True,
):
    """A helper function for filters"""
    if items or setlist:
        res = items if items else []
        for s in setlist or []:
            res += sets[s].accepts if accepts else sets[s].rejects
        return patterns(res)
    else:
        return None


def filters(
    *,
    rejects: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    rejectSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
) -> Filters:
    sets: dict[str, RawFilters] = {
        _: filterset(_) for _ in set((rejectSet or []) + (acceptSet or []))
    }
    accepted = makePattern(accepts, acceptSet, sets, accepts=True)
    rejected = makePattern(rejects, rejectSet, sets, accepts=False)
    if rejected or accepted:
        return Filters(accepted, rejected)
    else:
        f = gitignored()
        return Filters(patterns(f.accepts), patterns(f.rejects))


RE_EXACT = re.compile(r"^(/|./)(?P<path>.*)$")


def patterns(
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
    expr_exact, expr_partial = (
        "|".join(fnmatch.translate(_).lstrip("(?s:").rstrip(")\\Z") for _ in p)
        for p in (exact, partial)
    )
    expr_exact = f"^({expr_exact})$" if exact else ""
    expr_partial = f"^(.*/)?({expr_partial})[/$]" if partial else ""

    if expr_exact and expr_partial:
        return re.compile(f"{expr_exact}|{expr_partial}")
    else:
        return re.compile(expr_exact or expr_partial)


def matches(
    value: str,
    accepts: Optional[re.Pattern[str]] = None,
    rejects: Optional[re.Pattern[str]] = None,
) -> bool:
    """Tells if the given value passes the `accepts` and `rejects` filters."""
    if rejects and rejects.match(value):
        return False
    elif accepts and not accepts.match(value):
        return False
    else:
        return True


def filterset(collection: str) -> RawFilters:
    """Returns"""
    match collection:
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


def gitignored(path: Optional[Path] = None) -> RawFilters:
    """Returns the list of patterns that are part of the `gitignore` file."""
    path = dotfile(".gitignore") if not path else path
    accepts: list[str] = []
    rejects: list[str] = []
    if path and path.exists():
        with open(path, "rt") as f:
            for pattern in f.readlines():
                pattern = pattern.strip().rstrip("\n").strip()
                if pattern.startswith("#") or not pattern:
                    continue
                if pattern.startswith("!"):
                    accepts.append(pattern[1:])
                else:
                    rejects.append(pattern)
    return RawFilters(accepts=accepts, rejects=rejects)
