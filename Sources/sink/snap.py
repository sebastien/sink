#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Sink
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   29-Sep-2009
# Last mod.         :   30-Sep-2009
# -----------------------------------------------------------------------------

import os, simplejson
from sink import tracking

#------------------------------------------------------------------------------
#
#  File system node
#
#------------------------------------------------------------------------------

#TODO: Describe -d option
USAGE = """\
sink [-s|snap] [OPTIONS] DIRECTORY|FILE

Takes a snapshot of the given DIRECTORY and outputs it to the stdout. The
output format is JSON. If FILE is given instead, then displays the content
of the snapshot.

Options:

  -c, --content (dflt)   Uses content analysis to detect changes
  -t, --time             Uses timestamp to detect changes
  --ignore-spaces        Ignores the spaces when analyzing the content
  --ignore   GLOBS       Ignores the files that match the glob
  --only     GLOBS       Only accepts the file that match glob
  
Examples:

  Taking a snapshot of the state of /etc

  $ sink -s /etc > etc-`date +'%Y%m%d`.json

  Listing the content of a snapshot

  $ sink -s etc-20090930.json

  Comparing two snapshots

  $ sink -c etc-20090930.json etc-20091001.json

""" 

class Engine:
	"""Implements operations used by the Sink main command-line interface."""

	def __init__( self, logger, config=None ):
		self.logger        = logger
		if config: self.setup(config)

	def setup( self, config ):
		"""Sets up the engine using the given configuration object."""

	def run( self, arguments ):
		"""Runs the command using the given list of arguments (a list of
		strings)."""
		logger   = self.logger
		accepts  = []
		rejects  = []
		if not arguments:
			print self.usage()
			return -1
		#arguments = arguments[0], arguments[1:]
		args = arguments
		# We ensure that there are enough arguments
		if len(args) != 1:
			print args
			logger.error("Bad number of arguments\n" + USAGE)
			return -1
		root_path = args[0]
		# Ensures that the directory exists
		if os.path.isdir(root_path):
			# We take a state snapshot of the given directory
			root_state = tracking.State(root_path, accepts=accepts, rejects=rejects)
			root_state.populate( lambda x: True )
			print simplejson.dumps(root_state.exportToDict())
		else:
			f = file(root_path, 'r')
			d = simplejson.loads(f.read())
			print tracking.State.FromDict(d)
		return 0

	def usage( self ):
		return USAGE

# EOF - vim: sw=4 ts=4 tw=80 noet
