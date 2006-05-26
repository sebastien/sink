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
# Last mod.         :   26-May-2006
# History           :
#                       26-May-2006 Added configuration and filtering options
#                       24-Apr-2006 Supports SHA1 and TIME modes, supports
#                       output filtering.
#                       19-Apr-2006 More understandable output, added multiple
#                       directories comparison, enhanced usage information,
#                       added -d option.
#                       10-Mar-2006 Small bug fix
#                       22-Feb-2006 Added sorted output
#                       13-Feb-2006 Enhanced report
#                       16-Jan-2006 Added easy import snippet
#                       19-Dec-2004 Checkin improvements (SPE)
#                       03-Dec-2004 First implementation (SPE)
# -----------------------------------------------------------------------------

import os, sys, shutil, getopt, string, ConfigParser
from os.path import basename, dirname, exists

# We try to import the sink module. If we have trouble, we simply insert the
# path into the Python path
try:
	from sink import Tracking
except:
	sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
	from sink import Tracking

__version__ = "0.9.6"

CONTENT_MODE = True
TIME_MODE    = False
ADDED        = "[+]"
REMOVED      = "[-]"
NEWER        = "[M]"
OLDER        = "[m]"
SAME         = "[.]"
ABSENT       = "   "

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
#  Operations
#
#------------------------------------------------------------------------------

def listChanges( changes, origin, compared, logger, diffs=[],
diffcommand="diff", show=None
):
	"""Outputs a list of changes, with files only in source, fiels only in
	destination and modified files."""
	assert show
	all_locations = []
	all_locations_keys = {}
	# We get the locations by changes
	for change in changes:
		locations = {}
		removed   = change.getOnlyInOldState()
		added     = change.getOnlyInNewState()
		changed   = change.getModified()
		unchanged = change.getUnmodified()
		added.sort(lambda a,b:cmp(a.location(), b.location()))
		removed.sort(lambda a,b:cmp(a.location(), b.location()))
		changed.sort(lambda a,b:cmp(a.location(), b.location()))
		for node in added:
			if not show.get(ADDED): break
			if node.isDirectory(): continue
			all_locations_keys[node.location()] = True
			locations[node.location()] = ADDED
		for node in removed:
			if not show.get(REMOVED): break
			if node.isDirectory(): continue
			all_locations_keys[node.location()] = True
			locations[node.location()] = REMOVED
		for node in changed:
			if not show.get(NEWER) or not show.get(OLDER): break
			if node.isDirectory(): continue
			all_locations_keys[node.location()] = True
			old_node = change.previousState.nodeWithLocation(node.location())
			new_node = change.newState.nodeWithLocation(node.location())
			if old_node.getAttribute("Modification") < new_node.getAttribute("Modification"):
				if not show.get(NEWER): continue
				locations[node.location()] = NEWER
			else:
				if not show.get(OLDER): continue
				locations[node.location()] = OLDER
		for node in unchanged:
			if not show.get(SAME): break
			if node.isDirectory(): continue
			all_locations_keys[node.location()] = True
			locations[node.location()] = SAME
		all_locations.append(locations)
	# Now we print the result
	all_locations_keys = all_locations_keys.keys()
	all_locations_keys.sort(lambda a,b:cmp((a.count("/"),a),(b.count("/"), b)))
	format  = "%0" + str(len(str(len(all_locations_keys))) ) + "d %s %s"
	counter = 0
	for loc in all_locations_keys:
		if origin.nodeWithLocation(loc) == None: state = ABSENT
		else: state = SAME
		for locations in all_locations:
			node = locations.get(loc)
			if node == None: state += "[ ]"
			else: state += node
		logger.message(format % (counter, state, loc))
		if counter in diffs:
			src = origin.nodeWithLocation(loc)
			dst = compared[0].nodeWithLocation(loc)
			if not src:
				logger.message("Cannot diff\nFile only in dest:   " + dst.getAbsoluteLocation())
			elif not dst:
				logger.message("Cannot diff\nFile only in source: " + src.getAbsoluteLocation())
			else:
				src = src.getAbsoluteLocation()
				dst = dst.getAbsoluteLocation()
				logger.message("Diff: '%s' --> '%s'" % (src,dst))
				command = '%s %s %s' % ( diffcommand,src,dst)
				os.system(command)
		counter += 1
	# if added:     logger.message( "\t%5s were added    [+]" % (len(added)))
	# if removed:   logger.message( "\t%5s were removed  [-]" % (len(removed)))
	# if changed:   logger.message( "\t%5s were modified [M]" % (len(changed)))
	# if unchanged: logger.message( "\t%5s are the same  [.]" % (len(unchanged)))
	if not all_locations_keys: logger.message("No changes found.")


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

  Sink lists changes between an origin directory and a list of compared
  directories. 

  Usage:    sink [OPTIONS] [OPERATION] ORIGIN COMPARED...

  ORIGIN    is the directory to which we want to compare the others
  COMPARED  is a list of directories that will be compared to ORIGIN

  Operations:
    -l, --list (default)   List changes made to the source directory
        --diff             Specifies the diff command to be used with -d
        -dNUM              Shows the diff for the item NUM in the list

    -o, --checkout         Updates the destination
    -i, --checkin          Updates the source

  Options:
    -c, --content (dflt)   Uses content analysis to detect changes
    -t, --time             Uses timestamp to detect changes
    --ignore-spaces        Ignores the spaces when analyzing the content
    --ignore GLOBS         Ignores the files that match the glob
    --only   GLOBS         Only accepts the file that match glob

    GLOBS understand '*' and '?', will refer to the basename and can be
    separated by commas. If a directory matches the glob, it will not be
    traversed (ex: --ignore '*.pyc,*.bak,.[a-z]*')

    You can also specify what you want to be listed in the diff:

    [-+]s                  Hides/Shows SAME files
    [-+]a                  Hides/Shows ADDED files
    [-+]r                  Hides/Shows REMOVED files
    [-+]m                  Hides/Shows MODIFIED files
    [-+]n                  Hides/Shows NEWER files
    [-+]o                  Hides/Shows OLDER files



  Note that by default, checkin and checkout operation never remove files, they
  only add or update files.

""" % (__version__)

DEFAULTS = {
	"sink.mode"       : CONTENT_MODE,
	"sink.diff"       : "diff -u",
	"sink.whitespace" : True,
	"filters.accepts" : [],
	"filters.rejects" : []
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

	# Sets the variables
	operation     = listChanges
	mode          = config["sink.mode"]
	diff_command  = config["sink.diff"]
	diffs         = []
	accepts       = config["filters.accepts"]
	rejects       = config["filters.rejects"]
	ignore_spaces = config["sink.whitespace"]
	show          = {}

	# We extract the arguments
	try:
		optlist, args = getopt.getopt( arguments, "cthVvld:iarsmno",\
		["version", "help", "verbose", "list", "checkin", "checkout",
		"modified",
		"time", "content", "ignore-spaces", "ignorespaces", "diff=", "ignore=",
		"ignores=", "accept=", "accepts=", "only="])
	except:
		args    = []
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
		elif opt in ('-t', '--time'):
			mode = TIME_MODE
		elif opt in ('--ignorespaces', '--ignore-spaces'):
			ignore_spaces = True
		elif opt in ('--ignore', '--ignores'):
			rejects.extend(arg.split(","))
		elif opt in ('--only', '--accept','--accepts'):
			accepts.extend(arg.split("."))
		elif opt == '-d':
			diffs.append(int(arg))
		elif opt == '--diff':
			diff_command = arg
		elif opt in ('-a'):
			show[ADDED]   = False
		elif opt in ('-r'):
			show[REMOVED] = False
		elif opt in ('-s'):
			show[SAME]    = False
		elif opt in ('-m'):
			show[NEWER]   = False
			show[OLDER]   = False
		elif opt in ('-n'):
			show[NEWER]   = False
		elif opt in ('-o'):
			show[OLDER]   = False

	# We adjust the show
	nargs = []
	for arg in args:
		if   arg == "+a":
			show[ADDED] = True
		elif arg == "+r":
			show[REMOVED] = True
		elif arg == "+s":
			show[SAME] = True
		elif arg == "+m":
			show[MODIFIED] = True
		elif arg == "+o":
			show[OLDER] = True
		elif arg == "+n":
			show[OLDER] = True
		else:
			nargs.append(arg)
	args = nargs

	# We set the default values for the show, only if there was no + option
	if show == {} or filter(lambda x:not x, show.values()):
		for key,value in { ADDED:True, REMOVED:True, NEWER:True, OLDER:True,
		SAME:False }.items():
			show.setdefault(key, value)

	# We ensure that there are enough arguments
	if len(args) < 2:
		logger.error("Bad number of arguments\n" + USAGE)
		sys.exit()

	origin_path    = args[0]
	compared_paths = args[1:]
	# Wensures that the origin and compared directories exist
	if not os.path.isdir(origin_path):
		logger.error("Origin directory does not exist.") ; sys.exit()
	for path in compared_paths:
		if not os.path.isdir(path):
			logger.error("Compared directory does not exist.") ; sys.exit()

	# Detects changes between source and destination
	tracker         = Tracking.Tracker()
	origin_state    = Tracking.State(origin_path, accepts=accepts, rejects=rejects)
	compared_states = []
	for path in compared_paths:
		compared_states.append(Tracking.State(path, accepts=accepts, rejects=rejects))

	# Scans the source and destination, and updates
	#logger.message("Scanning origin: " + origin_path)
	origin_state.populate( lambda x: mode )
	for state in compared_states:
		#logger.message("Scanning compared: " + state.location())
		state.populate(lambda x: mode )
	changes     = []
	any_changes = False
	for state in compared_states:
		#logger.message("Comparing '%s' to origin" % (state.location()))
		if mode == CONTENT_MODE:
			changes.append(tracker.detectChanges(state, origin_state,
			method=Tracking.Tracker.SHA1))
		else:
			changes.append(tracker.detectChanges(state, origin_state,
			method=Tracking.Tracker.TIME))
		any_changes = changes[-1].anyChanges() or any_changes
	
	# We apply the operation
	if any_changes:
		if operation == listChanges and diffs:
			operation( changes, origin_state, compared_states, logger, diffs,
			diffcommand=diff_command, show=show)
		else:
			operation( changes, origin_state, compared_states, logger, show=show)
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
