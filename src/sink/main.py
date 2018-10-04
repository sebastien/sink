#!/usr/bin/env python
# -----------------------------------------------------------------------------
# Project           :   Sink                 <http://github.com/sebastien/sink>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre           <sebastien.pierre@gmail.com>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   03-Dec-2004
# Last mod.         :   29-Sep-2009
# -----------------------------------------------------------------------------

import os, sys, shutil, getopt, string, ConfigParser
from os.path import basename, dirname, exists

# We try to import the sink module. If we have trouble, we simply insert the
# path into the Python path
try:
	from sink import diff, link, snap
except:
	sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
	from sink import diff, link, snap

__version__ = "1.0.1"

#------------------------------------------------------------------------------
#
#  Logger
#
#------------------------------------------------------------------------------

class Logger:
	"""A logger instance allows to properly output information to the user
	through the terminal."""

	@staticmethod
	def default():
		"""Returs the default logger instance."""
		if not hasattr(Logger, "DEFAULT"):
			Logger.DEFAULT = Logger()
		return Logger.DEFAULT

	def __init__( self ):
		self._out = sys.stdout
		self._err = sys.stderr

	def error( self, *message ):
		self._write(self._err,  "[ERROR]", *message)
		return -1

	def warning( self, *message ):
		self._write(self._out, "[!]", *message)
		return 0

	def message( self, *message ):
		self._write(self._out, *message)
		return 0

	def info( self, *message ):
		self._write(self._out,  *message)
		return 0

	def _write( self, stream, *a ):
		stream.write(" ".join(map(str,a)) + "\n")
		stream.flush()

#------------------------------------------------------------------------------
#
#  Main
#
#------------------------------------------------------------------------------

USAGE = """\
sink (%s)

Sink is the swiss army-knife for many common directory comparison and 
synchronization.

Usage:    sink [MODE] [OPTIONS]

Modes:

  (diff/-d/--diff)  Lists the changes between two or more directories [default]
  (link/-l/--link)  Manages a links between files
  (snap/-s/--snap)  Takes a snapshot of a directory
  (help/-h/--help)  Shows help (--help diff, --help link, --help snap)

Options:

  See `sink --help diff`, `sink --help link`, etc. for more information
  about each mode options.

Examples:

  $ sink diff DIR1 DIR2 DIR3       Compares the contents of DIR1, DIR2 and DIR3

                                   in the listing given by 'sink DIR1 DIR2'
  $ sink diff --only '*.py' D1 D2  Compares the '*.py' files in D1 and D2

""" % (__version__)

DEFAULTS = {
	"sink.mode"       : diff.CONTENT_MODE,
	"sink.diff"       : "diff -u",
	"sink.whitespace" : True,
	"filters.accepts" : [],
	"filters.rejects" : []
}

OPERATIONS = {
	"-d":diff.Engine,
	"-l":link.Engine,
	"-s":snap.Engine,
	"--diff":diff.Engine,
	"--link":link.Engine,
	"--snap":snap.Engine,
	"diff":diff.Engine,
	"link":link.Engine,
	"snap":snap.Engine,
	"":diff.Engine
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
		logger = Logger.default()

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
				elif key == "sink.diff":
					config[key] = val.strip()
				else:
					print "Invalid configuration option:", key

	# If there is no arguments
	args = arguments
	if not args or args[0] in ('-h', '--help'):
		if len(args) == 2:
			if   args[1] == "diff":
				print diff.USAGE
			elif args[1] == "link":
				print link.USAGE
			elif args[1] == "snap":
				print snap.USAGE
			else:
				print USAGE
			return
		else:
			print USAGE
			return
	elif args[0] == '--version':
		print __version__
		return
	elif args[0] in OPERATIONS.keys():
		engine = OPERATIONS[args[0]](logger, config)
		return engine.run(args[1:])
		#try:
		#	return engine.run(args[1:])
		#except Exception, e:
		#	return logger.error(str(e))
	else:
		engine = OPERATIONS[""](logger, config)
		return engine.run(args)
		#try:
		#	return engine.run(args)
		#except Exception, e:
		#	return logger.error(str(e))

if __name__ == "__main__" :
	#import profile
	if len( sys.argv ) > 1:
		#profile.run("run(sys.argv[1:])")
		run(sys.argv[1:])
	else:
		run([])

# EOF - vim: sw=4 ts=4 tw=80 noet
