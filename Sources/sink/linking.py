#!/usr/bin/env python
# Encoding: iso-8859-1
# -----------------------------------------------------------------------------
# Project           :   Sink
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   BSD License (revised)
# -----------------------------------------------------------------------------
# Creation date     :   23-Jul-2007
# Last mod.         :   01-Aug-2007
# -----------------------------------------------------------------------------

# TODO: Make it standalone (so it can be intergrated into Mercurial Contrib)

import os, sys, sha, stat, getopt, shutil

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
#  Basic path operations
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

def make_relative( path, relative_to="." ):
	"""Expresses the given 'path' relatively to the 'relative_to' path."""
	path, relative_to = map(expand_path, (path, relative_to))
	if path.startswith(relative_to):
		path = path[len(relative_to):]
		if path and path[0] == "/": path = path[1:]
		return path
	else:
		return path

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

#------------------------------------------------------------------------------
#
#  LinksCollection Class
#
#------------------------------------------------------------------------------

DB_FILE    = ".sink-links"
DB_FILE_HG = os.path.join(".hg", "sink-links")

class LinksCollection:

	@staticmethod
	def lookup( path="." ):
		"""Looks for a file '.versions-links' or '.hg/version-links' in the
		current path or in a parent path."""
		if not path: return None
		path = os.path.abspath(path)
		parent = os.path.dirname(path)
		fs_vlinks = os.path.join(path, DB_FILE)
		hg_vlinks = os.path.join(path, DB_FILE_HG)
		if os.path.exists(fs_vlinks):
			return LinksCollection(path, DB_FILE)
		elif os.path.exists(hg_vlinks):
			return LinksCollection(path, DB_FILE_HG)
		elif parent != path:
			return LinksCollection.lookup(parent)
		else:
			return None

	def __init__( self, root, dbfile=DB_FILE ):
		"""Creates a new link collection object, using the given root."""
		self.links = {}
		root  = expand_path(root)
		if not os.path.exists(root):
			raise LinksCollectionError(CFG_BAD_ROOT)
		self.root   = root
		self.dbfile = dbfile
		if self.exists():
			self.load()

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

	def removeLink( self, link, delete=False ):
		"""Removes the link from this link collection. The file is only delete
		if the delete option is True."""
		assert self.getSource(link)
		e_link = expand_path(link)
		n_link = self._normalizeDestination(e_link)
		if delete and os.path.exists(e_link):
			os.unlink(e_link)
		del self.links[n_link]

	def save( self ):
		"""Saves the link collection to the 'dbpath()' file."""
		f = file(self.dbpath(), 'w')
		f.write(str(self))
		f.close()

	def load( self ):
		"""Loads the given collection."""
		f = file(self.dbpath(), 'r')
		c = f.readlines()
		f.close()
		links_count = 0
		for line in c: 
			line = line[:-1]
			line = line.strip()
			if not line: continue
			if line.startswith("#"): continue
			elements = line.split("\t")
			command, args = elements[0], elements[1:]
			command = command.strip()[:-1]
			if   command == "dbfile":
				# TODO: Check that the dbfile has the same value
				pass
			elif command == "root":
				# TODO: Check that root has the same value
				pass
			elif command == "links":
				links_count = int(args[0])
			elif command == "link":
				self.links[args[0]] = args[1]
		assert len(self.links.items()) == links_count

	def dbpath( self ):
		"""Returns the absolute patht ot the DB file."""
		return expand_path(os.path.join(self.root, self.dbfile))

	def exists( self ):
		"""Tells if the collection exists on the filesystem."""
		return os.path.exists(self.dbpath())

	def __str__( self ):
		"""Serializes the collection to a string"""
		res = []
		res.append("# Sink Link Database")
		res.append("root:\t%s" % (self.root))
		res.append("dbfile:\t%s" % (self.dbfile))
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

     Updates the given links in the current or given PATH, or updates only the
     given list of LINKs (they must belong to the same link DB, accessible from
     the current path).

     If the link is newer than the source and has modifications, then the update
     will not happen unless it is --force'd.

     You can also merge back the changes by using '--merge'. This will start
     your favorite $MERGETOOL.

     Options:

       -f, --force       Forces the update, ignoring local modifications
       -m, --merge       Uses the $MERGETOOL to merge the link source and dest

  sink link remove LINK [LINK..]

      Removes one or more link from the link database. The links destinations
      won't be removed from the filesystem unlesse you specify '--delete'.

      Options:

        -d, --delete      Deletes the link destination (your local file)

"""

class Engine:
	"""Implements operations that can be done on a link collection. Operations
	include giving status, resolving a link, and updating a link."""

	ST_SAME      = "="
	ST_DIFFERENT = "!"
	ST_EMPTY     = "!"
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
			except Exception, e:
				return self.logger.error(e)
			self.linksReadOnly = True
			for opt, arg in optlist:
				if opt in ('-w', '--writable'):
					self.linksReadOnly = False
					raise Exception("--writable not implemented yet")
			if len(args) != 2:
				return self.logger.error("Adding a link requires a SOURCE and DESTINATION")
			collection = LinksCollection.lookup(".") or LinksCollection(".")
			self.add(collection, args[0], args[1])
		# -- STATUS command
		elif command == "status":
			collection = LinksCollection.lookup(".") or LinksCollection(".")
			self.status(collection)
		# -- REMOVE command
		elif command == "update":
			try:
				optlist, args = getopt.getopt( rest, "fm", ["force", "merge"])
			except Exception, e:
				return self.logger.error(e)
			self.forceUpdate = False
			for opt, arg in optlist:
				if opt in ('-f', '--force'):
					self.forceUpdate = True
				if opt in ('-m', '--merge'):
					raise Exception("--merge option not implemented yet")
			collection = LinksCollection.lookup(".") or LinksCollection(".")
			self.update(collection, *args)
		# -- REMOVE command
		elif command == "remove":
			try:
				optlist, args = getopt.getopt( rest, "d", ["delete"])
			except Exception, e:
				return self.logger.error(e)
			delete = False
			for opt, arg in optlist:
				if opt in ('-d', '--delete'):
					delete = True
			if not args:
				return self.logger.error("At least one link is expected")
			collection = LinksCollection.lookup(".") or LinksCollection(".")
			self.remove(collection, args, delete)
		else:
			return self.logger.error("Uknown command: %s" % (command))

	def init( self, path="." ):
		"""Initializes a link collection (link db) at the given location."""
		path = expand_path(path)
		hg_path = has_hg(path)
		if not os.path.exists(path) and (hg_path and not os.path.exists(hg_path)):
			return self.logger.error("Given path does not exist: %s" % (path))
		if hg_path:
			collection = LinksCollection(os.path.dirname(hg_path), DB_FILE_HG)
		else:
			collection = LinksCollection(path, DB_FILE)
		if collection.exists():
			return self.logger.error("Link database already exists: ", make_relative(collection.dbpath(), "."))
		collection.save()
		self.logger.info("Link database created: ", make_relative(collection.dbpath(), "."))
		return collection

	def add( self, collection, source, destination ):
		"""Adds a link from the source to the destination"""
		self.logger.message("Adding a link from %s to %s" % (source, destination))
		if not collection.exists():
			return self.logger.error("Link database was not initialized: %s" % (collection.root))
		exists = collection.getSource(destination)
		destination, source = collection.registerLink(source, destination)
		# TODO: Remove the WRITABLE mode from the destinatino
		if not os.path.exists(destination):
			self.logger.info("File does not exist, creating it")
			dirname = os.path.dirname(destination)
			if not os.path.exists(dirname):
				self.logger.info("Parent directory does not exist, creating it: %s" %( make_relative(dirname, ".")))
				os.makedirs(dirname)
			f = file(destination, "w")
			f.write("")
			f.close()
		if exists == source:
			self.logger.info("Link source is the same as the existing one: %s" % (make_relative(exists, ".")))
		elif exists:
			self.logger.warning("Previous link source was replaced: %s" % (make_relative(exists, ".")))
		collection.save()

	def status( self, collection ):
		links    = []
		link_max = 0
		src_max  = 0
		for s, l in collection.getLinks():
			l = make_relative(l, ".")
			link_max = max(len(l), link_max) 
			src_max  = max(len(s), src_max)
			links.append([s, l])
		links.sort()
		template = "%-" + str(link_max) + "s  %s  %" + str(src_max) + "s  [%s]"
		for s, l in links:
			content, date = self.linkStatus(collection, l)
			self.logger.message(template % (l,date,s,content))

	def update( self, collection, *links ):
		"""Updates the given links, or all if no link is specified."""
		col_links = collection.getLinks()
		dst_links = map(lambda x:x[1], col_links)
		if not col_links:
			return self.logger.warning("No link registered in the collection")
		links = map(expand_path, links)
		# We make sure that the link are registered
		for link in links:
			if not link in dst_links:
				return self.logger.error("Link is not registered: %s" % (
					make_relative(link, ".")
				))
		# Then we update the links
		for s, l in col_links:
			content, date = self.linkStatus(collection, l)
			# We ignore the links that are not in the 'links' list, if this list
			# is not empty
			if links and not (l in links):
				continue
			if content == self.ST_NOT_THERE or content == self.ST_EMPTY \
			or content == self.ST_DIFFERENT and date != self.ST_NEWER:
				self.logger.message("Updating ", make_relative(l,"."))
				self.updateLink(collection, l)
			elif content == self.ST_DIFFERENT:
				self.logger.warning("Skipping update", make_relative(l,"."), "(file has local modifications)")
			else:
				self.logger.message("Link is up to date: ", make_relative(l,"."))

	def remove( self, collection, links, delete=False ):
		"""Remove the given list of links from the collection."""
		for link in links:
			if not collection.getSource(link):
				return self.logger.error("Link does not exist: %s" % (make_relative(link)))
		for link in links:
			self.logger.message("Removing link: %s" % (make_relative(link)))
			collection.removeLink(link, delete)
		collection.save()

	def linkStatus( self, collection, link ):
		"""Returns a couple '(CONTENT_STATUS, FILE_STATUS)' where
		'CONTENT_STATUS' is any of 'ST_SAME, ST_DIFFERENT', 'ST_EMPTY',
		'ST_NOT_THERE' and 'FILE_STATUS' is any of 'ST_SAME, ST_NEWER,
		ST_OLDER'."""
		source = collection.getSource(link)
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

	def updateLink( self, collection, link, force=False ):
		"""Updates the given link to the content of the link source"""
		c, d = self.linkStatus(collection, link)
		if not force and (not (c in (self.ST_EMPTY, self.ST_NOT_THERE)) and d != self.ST_SAME):
			raise RuntimeError(ENG_LINK_IS_NEWER % (link))
		e_link = expand_path(link)
		path, content = self.resolveLink(collection, e_link)
		shutil.copyfile(path,e_link)
		shutil.copystat(path,e_link)

	def resolveLink( self, collection, link ):
		"""Returns ta couple ('path', 'content') corresponding to the resolution
		of the given link.
		
		The return value is the same as the '_read' method."""
		source = collection.getSource(link)
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
