from .cli import command, write, run, CLI
from .utils import difftool, shell
from .snap import snapshot
from .diff import diff as _diff
from .model import Snapshot, Status
from .matching import RawFilters, filters, matches, gitignored, filterset
from typing import Optional, NamedTuple, cast
from pathlib import Path


# --
# ## Main CLI commands
#
# Defines the primary commands available through the Sink CLI.

O_STANDARD = ["-o|--output", "-f|--format"]
O_FILTERS = ["-i|--ignores", "-I|--ignore-set", "-a|--accepts", "-A|--accept-set"]


class DiffRange(NamedTuple):
    rows: Optional[list[int]] = None
    sources: Optional[list[int]] = None


def parseDiffRanges(ranges: Optional[list[str]]) -> DiffRange:
    """Parses multiple diff range definitions"""
    if not ranges:
        return DiffRange()
    else:
        rows: set[int] = set()
        sources: set[int] = set()
        for _ in ranges:
            r = parseDiffRange(_)
            rows = rows.union(r.rows if r.rows else ())
            sources = sources.union(r.sources if r.sources else ())
        return DiffRange(
            None if not rows else list(rows), None if not sources else list(sources)
        )


def parseDiffRange(text: str) -> DiffRange:
    """Parses a range expression, which is like `RANGE,…@TARGET,…`"""
    # We take N,N,N and I-J for ranges
    # and then @A,B,… where A,B,… are the sources for the diff.
    if not text or text in ("*", "_", "-"):
        return DiffRange()
    elif "@" in text:
        select_rows, select_sources = text.split("@", 1)
    else:
        select_rows, select_sources = text, None
    # We extract the rows
    rows: list[int] = []
    for item in select_rows.split(","):
        if "-" in item:
            a, b = (int(_) for _ in item.split("-", 1))
            rows += [_ for _ in range(a, b + 1)]
        else:
            rows.append(int(item))
    # And the sources
    sources = (
        None
        if not select_sources
        else [SOURCES.index(_.strip().upper()) for _ in select_sources.split(",")]
    )
    return DiffRange(rows, sources)


MODES = ["untracked"]

# TODO: Add -s for the filterset
# TODO: Seems that snap
@command("PATH?", *(O_STANDARD + O_FILTERS))
def snap(
    cli: CLI,
    *,
    # TODO: the cli module does not take care of defaults
    path: str = ".",
    output: Optional[str] = None,
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
):
    """Takes a snapshot of the given file location."""

    f = filters(
        rejects=ignores, accepts=accepts, rejectSet=ignoreSet, acceptSet=acceptSet
    )
    s = snapshot(
        path,
        accepts=f.accepts,
        rejects=f.rejects,
    )
    with write(output) as f:
        for path in s.nodes:
            f.write(f"{path}\n")


@command("PATH?", "-s|--set?", "-I|--ignore-set", "-A|--accept-set", "-f|--format")
def _list(
    cli: CLI,
    *,
    path: str = ".",
    set: Optional[str] = None,
    format: Optional[str] = "{status} {path}",
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
):
    sets: list[Rawfilter] = []
    if set:
        sets.append(filterset(set))
    for ignoreSet in ignoreSet or []:
        sets.append(RawFilters(accepts=None, rejects=filterset(ignoreSet).rejects))
    for acceptSet in acceptSet or []:
        sets.append(RawFilters(accepts=filterset(acceptSet).accepts, rejects=None))

    i: int = 0
    template: str = format if format else "{status} {path}"
    for f in sets:
        for path in f.accepts or ():
            print(template.format(number=i, status="+", path=path))
            i += 1
        for path in f.rejects or ():
            print(template.format(number=i, status="-", path=path))
            i += 1


SOURCES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@command("PATH+", "-d|--diff*", "-t|--tool?", *(O_STANDARD + O_FILTERS))
def diff(
    cli: CLI,
    *,
    path: list[str],
    format: Optional[str] = None,
    output: Optional[str] = None,
    diff: Optional[list[str]] = None,
    tool: Optional[str] = None,
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
):
    """Compares the different snapshots of file locations."""
    f = filters(
        rejects=ignores, accepts=accepts, rejectSet=ignoreSet, acceptSet=acceptSet
    )
    snaps: list[Snapshot] = [
        snapshot(_, accepts=patterns(f.accepts), rejects=patterns(f.rejects))
        for _ in path
    ]
    # This format the output like
    #                              [A] ← src/py
    #                               ┆  [B] ← ../xxxxxxx--main/src/py
    #                               ⇣   ⇣
    # 000 __main__.py                   <   >
    # 001 xxxxxxxxx/__init__.py         <   >
    # 002 xxxxxxxxx/service.py          <   >
    # 003 xxxxxxxxx/tests/__init__.py   <   >
    compared = _diff(*snaps)
    with_diff: bool = diff is not None
    diff_ranges = parseDiffRanges(diff)
    sources = path
    node_paths = [_ for _ in compared]
    node_path_length = max((len(_) for _ in node_paths))
    # --
    # Header formatting
    for i, p in enumerate(sources):
        cli.out(
            " ".join((" " * (node_path_length), " ┆ " * i, f"[{SOURCES[i]}] ← {p}"))
        )
    print(" " * node_path_length, " ".join(f" ⇣ " for _ in range(len(sources))))

    # We defined convenience functions
    def has_source(i: int) -> bool:
        """Tells if the given number is in the given diff ranges"""
        return not diff_ranges.sources or i in diff_ranges.sources

    def has_row(i: int) -> bool:
        return not diff_ranges.rows or i in diff_ranges.rows

    def has_changes(status: list[Status]) -> bool:
        for _ in status:
            if _ not in (Status.ORIGIN, Status.SAME):
                return True
        return False

    # --
    # List formatting
    edit_rounds: int = 0
    # We iterate on the nodes, skipping the ones that have no changes.
    for i, p_nodes in enumerate(
        (p, nodes) for p, nodes in compared.items() if has_changes(nodes)
    ):
        # We skip any row that is not in the -d sources, if provided.
        if not has_row(i):
            continue
        # We print the row, filtering out the sources
        p, nodes = p_nodes
        print(
            f"{i:3d}",
            p.ljust(node_path_length),
            " ".join(_.value if has_source(j) else "   " for j, _ in enumerate(nodes)),
        )
        # --
        # We have the -d option, so we're going to interactively review
        # the diffs.
        if with_diff:
            paths = [
                Path(sources[j]) / p
                for j, _ in enumerate(nodes)
                if j == 0 or has_source(i)
            ]
            if edit_rounds > 0:
                if (
                    # FIXME: Better prompt formatting
                    answer := (
                        cli.ask("- ↳ [E]dit ┄ [s]kip ┄ [q]uit → ").strip().lower()
                    )
                    or " "
                ) == "q":
                    break
                elif answer[0] == "s":
                    continue
                else:
                    pass
            difftool(*paths)
            edit_rounds += 1


# EOF
