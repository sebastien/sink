#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Sink                   <http://sofware.type-z.org/sink>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   03-Dec-2004
# Last mod.         :   24-Jul-2006
# -----------------------------------------------------------------------------

import os, sys, shutil, getopt, string, ConfigParser
from os.path import basename, dirname, exists

# We try to import the sink module. If we have trouble, we simply insert the
# path into the Python path
try:
	from sink import tracking
except:
	sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
	from sink import tracking

__version__ = "0.9.8"

#------------------------------------------------------------------------------
#
#  Logger
#
#------------------------------------------------------------------------------

class Logger:
	"""A logger instance allows to properly output information to the user
	through the terminal."""

	def error( self, message ):
		sys.stderr.write("ERROR   : %s\n" % (message))

	def warning( self, message ):
		sys.stderr.write("WARNING : %s\n" % (message))

	def message( self, message ):
		sys.stdout.write( "%s\n" % (message))

	def tip( self, tip ):
		sys.stdout.write( "TIP:\t%s\n" % (tip))

#------------------------------------------------------------------------------
#
#  Main
#
#------------------------------------------------------------------------------

USAGE = """\
Sink - v.%s

  Sink is the swiss army-knife for many common development synchronisation
  needs.

  Usage:    sink [OPERATION?] [ARGUMENTS]

  OPERATION    the operation you want to use ('changes' by default, see below)
  ARGUMENTS    the arguments to the operations (use --help to know more)

  Operations:

    changes (DEF)  Lists the changes between two or more directories
    link           Manage synchrnoisation links between files
    help           Gives detailed help about a specific operation

  Type 'sink help changes' or 'sink changes --help' to get detailed information
  about the 'changes' operation.

""" % (__version__)

DEFAULTS = {
	"sink.mode"       : tracking.CONTENT_MODE,
	"sink.diff"       : "diff -u",
	"sink.whitespace" : True,
	"filters.accepts" : [],
	"filters.rejects" : []
}

OPERATIONS = {
	"list":tracking.Engine,
	"":tracking.Engine
}

def run( arguments, runningPath=".", logger=None ):
	"""Runs Sink using the given list of arguments, given either as a
	string or as a list."""

	# Ensures that the running path is actually a path (it may be simply the
	# full path to the executable )
	runningPath = os.path.abspath(runningPath)

	# If arguments are given as a string, split them
	if type(arguments) in (type(""), type(u"")):
		arguments = arguments.split(" ")

	# And the logger
	if logger==None:
		logger = Logger()

	# TODO: Add a better command/engine integration, where engines have a change
	# to set defaults, and parse config

	# Reads the configuration
	config = DEFAULTS.copy()
	config_path = os.path.expanduser("~/.sinkrc")
	if os.path.isfile(config_path):
		parser = ConfigParser.ConfigParser()
		parser.read(config_path)
		for section in parser.sections():
			for option in parser.options(section):
				key = section.lower() + "." + option.lower()
				val = parser.get(section, option).strip()
				if key == "sink.mode":
					if val in ("content", "contents"):
						config[key] = CONTENT_MODE
					elif val in ("time", "date"):
						config[key] = TIME_MODE
					else:
						print "Expected 'content' or 'time': ", val
				elif key == "sink.whitespace":
					if val == "ignore":
						config[key] = False
					else:
						config[key] = True
				elif key == "filters.accepts":
					config["filters.accepts"].extend(map(string.strip, val.split(",")))
				elif key in ("filters.rejects", "filters.reject", "filters.ignore", "filters.ignores"):
					config["filters.rejects"].extend(map(string.strip, val.split(",")))
				else:
					print "Invalid configuration option:", key

	# If there is no arguments
	args = arguments
	if not args or args[0] in ('-h', '--help'):
		print USAGE
		return
	elif args[0] == '--version':
		print __version__
		return
	elif args[0] in OPERATIONS.keys():
		engine = OPERATIONS[args[0]](logger, config)
		return engine.run(args[1:])
	else:
		engine = OPERATIONS[""](logger, config)
		return engine.run(args)

if __name__ == "__main__" :
	#import profile
	if len( sys.argv ) > 1:
		#profile.run("run(sys.argv[1:])")
		run(sys.argv[1:])
	else:
		run([])

# EOF - vim: sw=4 ts=4 tw=80 noet
