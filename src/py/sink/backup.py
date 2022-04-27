#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Project           :   Sink
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre           <sebastien.pierre@gmail.com>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   2022-04-27
# Last mod.         :   2022-04-27
# -----------------------------------------------------------------------------

from . import snap


class Engine:
    """Implements operations used by the Sink main command-line interface."""

    def __init__(self, logger, config=None):
        self.logger = logger
        if config:
            self.setup(config)

    def setup(self, config):
        """Sets up the engine using the given configuration object."""
        pass

    def run(self, arguments: list[str]):
        print(arguments)


# EOF
