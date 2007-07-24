#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Sink
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   23-Jul-2006
# Last mod.         :   24-Jul-2006
# -----------------------------------------------------------------------------

import os, sys, sha, stat, getopt

#------------------------------------------------------------------------------
#
#  Exceptions
#
#------------------------------------------------------------------------------

class LinksCollectionError(Exception):
	"""Raised when an error happens in the configuration process."""

class RuntimeError(Exception):
	"""Raised when an error happens in the engine."""

CFG_BAD_ROOT = "Directory or symlink expected for collection root"
CFG_NOT_A_CHILD = "Link destination must be a subpath of %s"
ENG_NOT_FOUND = "Path does not exist: %s"
ENG_SOURCE_NOT_FOUND = "Link source not found: %s"
ENG_LINK_IS_NEWER = "Link is newer, update has to be forced: %s"

#------------------------------------------------------------------------------
#
#  Basic operations
#
#------------------------------------------------------------------------------

def expand_path( path ):
	"""Completely expands the given path (vars, user and make it absolute)."""
	return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

def path_is_child( path, parent ):
	"""Returns 'True' if the given 'path' is a child of the given 'parent'
	path."""
	e_path   = expand_path(path)
	e_parent = expand_path(parent)
	return e_path.startswith(e_parent)

def make_relative( path, relative_to ):
	path, relative_to = map(expand_path, (path, relative_to))
	if path.startswith(relative_to):
		path = path[len(relative_to):]
		if path[0] == "/": path = path[1:]
		return path
	else:
		return path

#------------------------------------------------------------------------------
#
#  LinksCollection Class
#
#------------------------------------------------------------------------------

def has_hg( path ):
	"""Returns the path of the (possible) Mercurial repository contained at the
	given location, or returns None if it was not found."""
	if not path: return None
	path = os.path.abspath(path)
	parent = os.path.dirname(path)
	hg_path = os.path.join(path, ".hg")
	if os.path.exists(hg_path):
		return hg_path
	elif parent != path:
		return has_hg(parent)
	else:
		return None

class LinksCollection:

	@staticmethod
	def lookup( path="." ):
		"""Looks for a file '.versions-links' or '.hg/version-links' in the
		current path or in a parent path."""
		if not path: return None
		path = os.path.abspath(path)
		parent = os.path.dirname(path)
		fs_vlinks = os.path.join(path, ".sink-links")
		hg_vlinks = os.path.join(path, ".hg/sink-links")
		if os.path.exists(fs_vlinks):
			return LinksCollection(fs_vlinks, fullPath=True)
		elif os.path.exists(hg_vlinks):
			return LinksCollection(hg_vlinks, fullPath=True)
		elif parent != path:
			return LinksCollection.lookup(parent)
		else:
			return None

	def __init__( self, root, fullPath=False ):
		"""Creates a new link collection object, using the given root."""
		self.links = {}
		root  = expand_path(root)
		if not os.path.exists(root):
			raise LinksCollectionError(CFG_BAD_ROOT)
		if not fullPath:
			if root.endswith(".hg"):
				root = os.path.join(root, "sink-links")
			else:
				root = os.path.join(root, ".sink-links")
		self.root = root

	def getLinks( self ):
		"""Returns a list of '(source, dest)' where source and dest are absolute
		_expanded paths_ representing the link source and destination."""
		res = []
		for d, s in self.links.items():
			res.append(map(expand_path,(s,os.path.join(self.root,d))))
		return res

	def getSource( self, destination ):
		"""Returns the source for the given destination, in its _unexpanded_
		form."""
		n_destination = self._normalizeDestination(destination)
		return self.links.get(n_destination)

	def _normalizeDestination( self, destination ):
		"""Normalizes the destination path, making it relative to the
		collection root, and discarding the leading '/'"""
		e_destination = expand_path(destination)
		assert e_destination.startswith(self.root)
		n_destination = e_destination[len(self.root):]
		assert n_destination[0] == "/"
		n_destination = n_destination[1:]
		return n_destination

	def registerLink( self, source, destination ):
		"""Registers a link from the given source path to the given destination.
		*Source* is stored as-is (meaning that variables *won't be expanded*), and
		*destination will be expanded* and be expressed relatively to the
		collection root.
		
		This implies that destination must be contained in the collection
		root directory."""
		# TODO: Should we check the source ?
		e_destination = expand_path(destination)
		if not path_is_child(e_destination, self.root):
			raise LinksCollectionError(CFG_NOT_A_CHILD % (self.root))
		n_destination = self._normalizeDestination(e_destination)
		self.links[n_destination] = source
		return e_destination, source

	def save( self ):
		f = file(self.root, 'w')
		f.write(str(self))
		f.close()

	def exists( self ):
		"""Tells if the collection exists on the filesystem."""
		return os.path.exists(self.root)

	def __str__( self ):
		"""Serializes the collection to a string"""
		res = []
		res.append("# Sink Link Database")
		res.append("root:\t%s" % (self.root))
		res.append("links:\t%s" % (len(self.links)))
		for d,s in self.links.items():
			res.append("link:\t%s\t%s" % (d,s))
		res.append("# EOF")
		return "\n".join(res)

#------------------------------------------------------------------------------
#
#  Engine Class
#
#------------------------------------------------------------------------------

USAGE = """\
  sink link allows to create synchronisation links between files. It is
  especially useful when files are shared between different projects.

  Available operations are:

     link init           Initializes a link database for a specific folder
     link add            Creates a link between two file
     link remove         Removes a link between two files
     link status         Gives the status of linked files
     link update         Updates the linked files

  sink link init [PATH]

    Initialises the link database for the current folder, or the folder at the
    given PATH. If PATH is omitted, it will use the current folder, or will look
    for a Mercurial (.hg) repository in the parent directories, and will use it
    to store the links database.

    There are no options for this command.

  sink link add [OPTIONS] SOURCE DESTINATION

    Creates a link from the the SOURCE to the DESTINATION. The DESTINATION must
    be contained in a directory where the 'link init' command was run.

    Options:

      -w, --writable    Link will be made writable (so that you can update it)

  sink link status [PATH|LINK]...

     Returns the status of the given links. If no link is given, the status of
     all links will be returned. When no argument is given, the current
     directory (or one of its parent) must contain a link database, otherwise
     you should give a PATH containing a link databae.

  sink link update [OPTIONS] [PATH|LINK]...


     Options:

       -f, --force       Forces the update, ignoring local modifications
       -m, --merge       Uses the $MERGETOOL to merge the link source and dest

"""

class Engine:
	"""Implements operations that can be done on a link collection. Operations
	include giving status, resolving a link, and updating a link."""

	ST_SAME      = "="
	ST_DIFFERENT = "!"
	ST_EMPTY     = "-"
	ST_NOT_THERE = "?"
	ST_NEWER     = ">"
	ST_OLDER     = "<"

	def __init__( self, logger, config=None ):
		self.logger        = logger
		self.linksReadOnly = True
		if config: self.setup(config)

	def setup( self, config ):
		"""Sets up the engine using the given configuration object."""
		# TODO: Setup difftool/mergetool

	def run( self, arguments ):
		"""Runs the command using the given list of arguments (a list of
		strings)."""
		logger = self.logger
		if not arguments:
			return self.logger.message(USAGE)
		command = arguments[0]
		rest    = arguments[1:]
		# -- INIT command
		if command == "init":
			path = "."
			if len(rest) > 1:
				return self.logger.error("Too many arguments")
			elif len(rest) == 1:
				path = rest[0]
			self.init(path)
			return 1
		# -- ADD command
		elif command == "add":
			try:
				optlist, args = getopt.getopt( rest, "w", ["writable"])
			except:
				args    = []
				optlist = []
			self.linksReadOnly = True
			for opt, arg in optlist:
				if opt in ('-w', '--writable'):
					self.linksReadOnly = False
			if len(args) != 2:
				return self.logger.error("Adding a link requires a SOURCE and DESTINATION")
			collection = LinksCollection.lookup(".") or LinksCollection()
			self.add(collection, args[0], args[1])

	def init( self, path="." ):
		"""Initializes a link collection (link db) at the given location."""
		path = expand_path(path)
		hg_path = has_hg(path)
		if not os.path.exists(path) and (hg_path and not os.path.exists(hg_path)):
			return self.logger.error("Given path does not exist: %s" % (path))
		if hg_path:
			path = hg_path
		collection = LinksCollection(path)
		if os.path.exists(collection.root):
			return self.logger.error("Link database already exists: ", collection.root)
		collection.save()
		self.logger.info("Link database created: ", make_relative(collection.root, "."))
		return collection

	def add( self, collection, source, destination ):
		"""Adds a link from the source to the destination"""
		self.logger.message("Adding a link from %s to %s" % (source, destination))
		if not collection.exists():
			return self.logger.error("Collection was not initialized: %s" % (collection.root))
		destination = collection.registerLink(source, destination)
		# TODO: Remove the WRITABLE mode from the destinatino
		if not os.path.exists(destination):
			self.logger.info("File does not exist, creating it")
			f = file(destination, "w")
			f.write("")
			f.close()
		collection.write()

	def status( self ):
		links    = []
		link_max = 0
		src_max  = 0
		for s, l in self.collection.getLinks():
			l = make_relative(l, ".")
			link_max = max(len(l), link_max) 
			src_max  = max(len(s), src_max)
			links.append([s, l])
		template = "%-" + str(link_max) + "s  %s  %" + str(src_max) + "s  [%s]"
		for s, l in links:
			content, date = self.linkStatus(l)
			self.logger.message(template % (l,date,s,content))

	def update( self=None ):
		for s, l in self.collection.getLinks():
			content, date = self.linkStatus(l)
			if content == self.ST_NOT_THERE or content == self.ST_EMPTY \
			or content == self.ST_DIFFERENT and date != self.ST_NEWER:
				self.logger.message("Updating ", make_relative(l,"."))
				self.updateLink(l)
			elif content == self.ST_DIFFERENT:
				self.logger.warn("Skipping update", make_relative(l,"."), "(file has local modifications)")

	def linkStatus( self, link ):
		"""Returns a couple '(CONTENT_STATUS, FILE_STATUS)' where
		'CONTENT_STATUS' is any of 'ST_SAME, ST_DIFFERENT', 'ST_EMPTY',
		'ST_NOT_THERE' and 'FILE_STATUS' is any of 'ST_SAME, ST_NEWER,
		ST_OLDER'."""
		source = self.collection.getSource(link)
		if not source: raise RuntimeError(ENG_SOURCE_NOT_FOUND % (source))
		source, s_content = self._read(source)
		if not os.path.exists(link):
			return (self.ST_NOT_THERE, self.ST_NEWER)
		dest,   d_content = self._read(link)
		s_sig = self._sha(s_content)
		d_sig = self._sha(d_content)
		s_tme = self._mtime(source)
		d_tme = self._mtime(dest)
		res_0 = self.ST_DIFFERENT
		if s_sig == d_sig: res_0 = self.ST_SAME
		if not d_content: res_0 = self.ST_EMPTY
		res_1 = self.ST_SAME
		if s_tme < d_tme: res_1 = self.ST_NEWER
		if s_tme > d_tme: res_1 = self.ST_OLDER
		return (res_0, res_1)

	def updateLink( self, link, force=False ):
		"""Updates the given link to the content of the link source"""
		c, d = self.linkStatus(link)
		if not force and (not (c in (self.ST_EMPTY, self.ST_NOT_THERE)) and d != self.ST_SAME):
			raise RuntimeError(ENG_LINK_IS_NEWER % (link))
		e_link = expand_path(link)
		assert os.path.exists(e_link)
		f = file(e_link, 'w')
		_, content = self.resolveLink(e_link)
		f.write(content)
		f.close()

	def resolveLink( self, link ):
		"""Returns ta coupel ('path', 'content') corresponding to the resolution
		of the given link.
		
		The return value is the same as the '_read' method."""
		source = self.collection.getSource(link)
		return self._read(source)

	def _read( self, path, getContent=True ):
		"""Resolves the given path and returns a couple '(path, content)' when
		'getContent=True', or '(path, callback)' where callback will return the
		content of the file when invoked."""
		path = expand_path(path)
		if not os.path.exists(path):
			raise RuntimeError(ENG_NOT_FOUND % (path))
		if getContent:
			return (path, self._readLocal(path))
		else:
			return (path, lambda: self._readLocal(path))

	def _readLocal( self, path ):
		"""Reads a file from the local file system."""
		f = file(path, 'r')
		c = f.read()
		f.close()
		return c

	def _sha( self, content ):
		return sha.new(content).hexdigest()

	def _mtime( self, path ):
		"""Returns the modification time of the file at the give path."""
		return os.stat(path)[stat.ST_MTIME]

	def _size( self, path ):
		"""Returns the size of the file at the give path."""
		return os.stat(path)[stat.ST_SIZE]

# EOF - vim: ts=4 sw=4 noet
