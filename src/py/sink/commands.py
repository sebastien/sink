from .cli import command, write, CLI
from .utils import difftool
from .snap import snapshot
from .term import TermFont, termcolor
from .diff import diff as _diff
from .model import Snapshot, Status
from .matching import (
    filters,
    rawfilters,
)
from typing import Optional, NamedTuple
from pathlib import Path
import json


# --
# ## Main CLI commands
#
# Defines the primary commands available through the Sink CLI.

O_STANDARD = ["-o|--output?", "-f|--format?"]
O_FILTERS = [
    "-i|--ignores*",
    "-I|--ignore-set*",
    "-k|--keeps*",
    "-K|--keep-set*",
    "-a|--accepts*",
    "-A|--accept-set*",
    "-s|--filter-set*",
]


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


# TODO: Add -s for the filterset
# TODO: Seems that snap
@command("PATH?", *(O_STANDARD + O_FILTERS))
def snap(
    cli: CLI,
    *,
    # TODO: the cli module does not take care of defaults
    path: str = ".",
    format: str = " {status} {path}",
    output: Optional[str] = None,
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    keeps: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
    keepSet: Optional[list[str]] = None,
    filterSet: Optional[list[str]] = None,
):
    """Takes a snapshot of the given file location."""

    active_filters = filters(
        rejects=ignores,
        accepts=accepts,
        keeps=keeps,
        rejectSet=ignoreSet,
        acceptSet=acceptSet,
        keepSet=keepSet,
        filterSet=filterSet,
    )
    s = snapshot(
        path,
        accepts=active_filters.accepts,
        rejects=active_filters.rejects,
        keeps=active_filters.keeps,
    )
    if output.endswith(".json"):
        format = "json"
    with write(output) as f:
        if format == "json":
            json.dump(s.toPrimitive(), f)
        else:
            for path in s.nodes:
                f.write(f"{path}\n")


@command("PATH?", *(O_STANDARD + O_FILTERS))
def _filters(
    cli: CLI,
    *,
    path: str = ".",
    set: Optional[str] = None,
    output: Optional[str] = None,
    format: Optional[str] = "{status} {path}",
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    keeps: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
    keepSet: Optional[list[str]] = None,
    filterSet: Optional[list[str]] = None,
):
    """Lists the filters active for a given set of parameters."""
    filters = rawfilters(
        rejects=ignores,
        accepts=accepts,
        keeps=keeps,
        rejectSet=ignoreSet,
        acceptSet=acceptSet,
        keepSet=keepSet,
        filterSet=filterSet,
    )
    i: int = 0
    template: str = format if format else "{status} {path}"
    if not template.endswith("\n"):
        template += "\n"
    with write(output) as f:
        for path in filters.rejects or ():
            f.write(template.format(number=i, status="-", path=path))
            i += 1

        for path in filters.keeps or ():
            f.write(template.format(number=i, status="~", path=path))
            i += 1

        for path in filters.accepts or ():
            f.write(template.format(number=i, status="+", path=path))
            i += 1
    if i == 0:
        f.write("No active filter\n")


@command("PATH+", *(O_STANDARD + O_FILTERS))
def _list(
    cli: CLI,
    *,
    path: list[str],
    output: Optional[str] = None,
    format: Optional[str] = "{status} {path}",
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
    keeps: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
    keepSet: Optional[list[str]] = None,
    filterSet: Optional[list[str]] = None,
):
    """Prints out the paths in the given snapshot."""
    snap: Snapshot | None = None
    f = filters(
        rejects=ignores,
        accepts=accepts,
        keeps=keeps,
        rejectSet=ignoreSet,
        acceptSet=acceptSet,
        keepSet=keepSet,
        filterSet=filterSet,
    )
    for s in (
        snapshot(
            _,
            accepts=f.accepts,
            rejects=f.rejects,
            keeps=f.keeps,
        )
        for _ in path
    ):
        if snap:
            snap = snap.extend(s.nodes.values())
        else:
            snap = s
    with write(output) as f:
        if not snap:
            pass
        elif format == "json":
            json.dump(snap.toPrimitive(), f)
        else:
            for path in snap.nodes:
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
    keeps: Optional[list[str]] = None,
    ignoreSet: Optional[list[str]] = None,
    acceptSet: Optional[list[str]] = None,
    keepSet: Optional[list[str]] = None,
    filterSet: Optional[list[str]] = None,
):
    """Compares the different snapshots of file locations."""
    f = filters(
        rejects=ignores,
        accepts=accepts,
        keeps=keeps,
        rejectSet=ignoreSet,
        acceptSet=acceptSet,
        keepSet=keepSet,
        filterSet=filterSet,
    )
    snaps: list[Snapshot] = [
        snapshot(
            _,
            accepts=f.accepts,
            rejects=f.rejects,
            keeps=f.keeps,
        )
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
    if not node_paths:
        cli.out("No matching paths")
    else:
        node_path_length = max((len(_) for _ in node_paths))
        COLOR_FORMAT = {
            # NOTE: I've changed the presentation here, '.' becomes '+' and
            # '<' becomes '.'. We may
            " ! ": f"{termcolor(237, 73, 18)}{TermFont.Bold} ! {TermFont.Reset}",
            " - ": f"{termcolor(237, 73, 18)} - {TermFont.Reset}",
            " > ": f"{termcolor(156, 224, 220)}{TermFont.Bold} > {TermFont.Reset}",
            " + ": f"{termcolor(156, 224, 20)}{TermFont.Bold} + {TermFont.Reset}",
            " . ": f"{termcolor(156, 224, 20)}{TermFont.Bold} + {TermFont.Reset}",
            " < ": f"{termcolor(160, 160, 160)} . {TermFont.Reset}",
        }

        # --
        # Header formatting
        for i, p in enumerate(sources):
            cli.out("    ")
            cli.out(
                " ".join((" " * (node_path_length), " ┆ " * i, f"[{SOURCES[i]}] ← {p}"))
            )
            cli.out("\n")
        # TODO: Restore that
        # cli.out(" " * node_path_length, " ".join(f" ⇣ " for _ in range(len(sources))))

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
            f"{i:03d}",
            p.ljust(node_path_length),
            " ".join(
                COLOR_FORMAT.get(v := _.value, v) if has_source(j) else "   "
                for j, _ in enumerate(nodes)
            ),
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
