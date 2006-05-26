#!/usr/bin/env python
# Encoding: iso-8859-1
# vim: ts=4 noet
# -----------------------------------------------------------------------------
# Project           :   Sink                   <http://sofware.type-z.org/sink>
# Module            :   Change tracking
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   03-Dec-2004
# Last mod.         :   16-Jan-2006
# History           :
#                       22-Feb-2006 Added sorted output
#                       13-Feb-2006 Enhanced report
#                       16-Jan-2006 Added easy import snippet
#                       19-Dec-2004 Checkin improvements (SPE)
#                       03-Dec-2004 First implementation (SPE)
#
# Bugs              :
#                       -
# To do             :
#                       -
#
# Notes             :
#                       -


import os, sys, shutil, getopt
from os.path import basename, dirname, exists

# We try to import the sink module. If we have trouble, we simply insert the
# path into the Python path
try:
	from sink import Tracking
except:
	sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
	from sink import Tracking

__version__ = "0.9.1"

CONTENT_MODE = True
TIME_MODE    = False


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

def listChanges( changes, source, destination, logger ):
	"""Outputs a list of changes, with files only in source, fiels only in
	destination and modified files."""
	added   = changes.getOnlyInOldState()
	removed = changes.getOnlyInNewState()
	changed = changes.getModified()
	added.sort(lambda a,b:cmp(a.location(), b.location()))
	removed.sort(lambda a,b:cmp(a.location(), b.location()))
	changed.sort(lambda a,b:cmp(a.location(), b.location()))
	logger.message( "[S][ ]  " + source)
	logger.message( "[ ][D]  " + destination)
	logger.message( "------")
	for node in added:
		logger.message( "[ ][*]\t" + node.location() )
	for node in removed:
		logger.message( "[*][ ]\t" + node.location() )
	for node in changed:
		if node.isDirectory(): continue
		old_node = changes.previousState.nodeWithLocation(node.location())
		new_node = changes.newState.nodeWithLocation(node.location())
		if old_node.getAttribute("Modification") < new_node.getAttribute("Modification"):
			logger.message( "[*][+]\t" + node.location() )
		else:
			logger.message( "[+][*]\t" + node.location() )
	if added:   logger.message( "\t%s were added" % (len(added)))
	if removed: logger.message( "\t%s were added" % (len(removed)))
	if changed: logger.message( "\t%s were changed" % (len(changed)))


def copyFile( source, destination ):
	"""Copies the file from the source location to the destination location.
	The containing directories must exist."""
	assert( basename(source) == basename(destination) )
	shutil.copyfile(source, destination)
	shutil.copymode(source, destination)
	shutil.copystat(source, destination)

def makeDirs( source, destination ):
	"""Creates the destination directory, as well as its parent directories,
	and preserves the mode and stats of the source directory."""
	assert( basename(source) == basename(destination) )
	# We create parent directories if necessary
	if not exists(dirname(destination)):
		makeDirs( dirname(source), dirname(destination) )
	if not exists(destination): os.makedirs(destination)
	shutil.copymode(source, destination)
	shutil.copystat(source, destination)

def checkin( changes, source, destination, logger ):
	"""Updates the files in the destination"""
	# Creates the directories
	for node in filter(lambda n:n.isDirectory(), changes.getOnlyInOldState()):
		logger.message( "Creating\t" + node.location() )
		makeDirs(source + "/" + node.location(),
			destination + "/" + node.location())
	# Creates the files
	for node in filter(lambda n:not n.isDirectory(), changes.getOnlyInOldState()):
		logger.message( "Copying \t" + node.location() )
		copyFile(source + "/" + node.location(),
			destination + "/" + node.location())
	# Updates the files
	for node in changes.getModified():
		if not node.isDirectory():
			logger.message( "Updating\t" + node.location() )
			copyFile(source + "/" + node.location(),
			destination + "/" + node.location())
		else:
			logger.message( "Updating\t" + node.location() )
			makeDirs(source + "/" + node.location(),
			destination + "/" + node.location())

#------------------------------------------------------------------------------
#
#  Main
#
#------------------------------------------------------------------------------


USAGE = """\
Sink - v.%s

  Sink list changes between a source directory and a destination directory and
  optionaly updates the destination directory to be identical to the source
  directory.

  Usage:    sink [MODE] [OPERATION] SOURCE DESTINATION

  Modes:
    -t, --time (default)   Uses timestamp to detect changes
    -c, --content          Uses content analysis to detect changes
        --ignore-spaces    Ignores the spaces when analyzing the content

  Operations:
    -l, --list (default)   List changes made to the source directory
    -o, --checkout         Updates the destination
    -i, --checkin          Updates the source

    Note that by default, checkin and checkout operation never remove files, they
    only add or update files.

""" % (__version__)

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

	operation     = listChanges
	mode          = TIME_MODE
	ignore_spaces = False

	# We extract the arguments
	try:
		optlist, args = getopt.getopt( arguments, "cthVvli",\
		["version", "help", "verbose", "list", "checkin", "checkout",
		"time", "content", "ignore-spaces", "ignorespaces"])
	except:
		args=[]
		optlist = []

	# We parse the options
	for opt, arg in optlist:
		if opt in ('-h', '--help'):
			print USAGE ; sys.exit()
		elif opt in ('-v', '--version'):
			print __version__
			sys.exit()
		elif opt in ('-l', '--list'):
			operation = listChanges
		elif opt in ('-i', '--checkin'):
			operation = checkin
		elif opt in ('-c', '--content'):
			mode   = CONTENT_MODE
		elif opt in ('--ignorespaces', '--ignore-spaces'):
			ignore_spaces = True
		elif opt in ('-t', '--time'):
			mode = TIME_MODE

	# We ensure that there are enough arguments
	if len(args) != 2:
		logger.error("Bad arguments\n" + USAGE)
		sys.exit()

	source_path, dest_path = args
	if not os.path.exists(source_path):
		logger.error("Source path does not exist.") ; sys.exit()
	if not os.path.exists(dest_path):
		logger.error("Dest path does not exist.") ; sys.exit()

	# Detects changes between source and destination
	tracker		 = Tracking.Tracker()
	source_state = Tracking.State(source_path)
	dest_state   = Tracking.State(dest_path)

	# Scans the source and destination, and updates
	logger.message("Scanning source: " + source_path)
	source_state.populate( lambda x: mode )
	logger.message("Scanning destination: " + dest_path)
	dest_state.populate(lambda x: mode )
	logger.message("Comparing...")
	changes      = tracker.detectChanges(dest_state, source_state)
	
	# We apply the operation
	if changes.anyChanges():
		operation( changes, source_path, dest_path, logger)
	else:
		logger.message("Nothing changed.")

if __name__ == "__main__" :
	#import profile
	if len( sys.argv ) > 1:
		#profile.run("run(sys.argv[1:])")
		run(sys.argv[1:])
	else:
		run([])

# EOF-Unix/ASCII------------------------------------@RisingSun//Python//1.0//EN
