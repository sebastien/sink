from .cli import command, write, run
from .utils import gitignored
from .snap import snapshot
from typing import Optional


O_STANDARD = ["-o|--output", "-f|--format"]
O_FILTERS = ["-i|--ignores+", "-a|--accepts"]


@command("PATH", *(O_STANDARD + O_FILTERS))
def snap(
    context,
    path: str,
    output: Optional[str] = None,
    format: Optional[str] = None,
    ignores: Optional[list[str]] = None,
    accepts: Optional[list[str]] = None,
):
    s = snapshot(
        path, accepts=accepts, rejects=gitignored() if ignores is None else ignores
    )
    with write(output) as f:
        for path in s.nodes:
            f.write(f"{path}\n")


@command("PATH+", "-d|--diff*", "--difftool", *(O_STANDARD))
def diff(
    context,
    path: list[str],
    diff: Optional[list[str]] = None,
    difftool: Optional[str] = None,
):
    print("DIFF", path, diff, difftool)


# EOF
