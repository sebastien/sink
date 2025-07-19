import sys
import sink.commands as commands
from sink.cli import run

__all__ = ["commands"]  # NOTE: to keep module
run(sys.argv[1:])
# EOF
