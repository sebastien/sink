from .cli import command, write, run, CLI
from .utils import gitignored, difftool
from .snap import snapshot
from .diff import diff as _diff
from .model import Snapshot
from typing import Optional, NamedTuple
from pathlib import Path


# --
# ## Main CLI commands
#
# Defines the primary commands available through the Sink CLI.

O_STANDARD = ["-o|--output", "-f|--format"]
O_FILTERS = ["-i|--ignores+", "-a|--accepts"]


class Filters(NamedTuple):
    rejects: Optional[list[str]] = None
    accepts: Optional[list[str]] = None


class DiffRange(NamedTuple):
    rows: Optional[list[int]] = None
    sources: Optional[list[int]] = None


def filters(
    *,
    rejects: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
) -> Filters:
    if rejects or accepts:
        return Filters(rejects, accepts)
    else:
        return Filters(gitignored(), accepts)


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


@command("PATH", *(O_STANDARD + O_FILTERS))
def snap(
    cli: CLI,
    *,
    path: str,
    output: Optional[str] = None,
    format: Optional[str] = None,
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
):
    """Takes a snapshot of the given file location."""
    s = snapshot(
        path, accepts=accepts, rejects=gitignored() if ignores is None else ignores
    )
    with write(output) as f:
        for path in s.nodes:
            f.write(f"{path}\n")


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
):
    """Compares the different snapshots of file locations."""
    f = filters(rejects=ignores, accepts=accepts)
    snaps: list[Snapshot] = [
        snapshot(_, accepts=f.accepts, rejects=f.rejects) for _ in path
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

    # We defined convenience funcions
    def has_source(i: int) -> bool:
        return not diff_ranges.sources or i in diff_ranges.sources

    def has_row(i: int) -> bool:
        return not diff_ranges.rows or i in diff_ranges.rows

    # --
    # List formatting
    for i, p_nodes in enumerate(compared.items()):
        p, nodes = p_nodes
        if not diff_ranges.rows or i in diff_ranges.rows:
            print(
                f"{i:3d}",
                p.ljust(node_path_length),
                " ".join(
                    _.value if has_source(j) else "   " for j, _ in enumerate(nodes)
                ),
            )
            if with_diff:
                paths = [
                    Path(sources[j]) / p
                    for j, _ in enumerate(nodes)
                    if j == 0 or has_source(j)
                ]
                difftool(*paths)


# EOF
