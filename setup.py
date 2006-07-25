#!/usr/bin/python
# Encoding: ISO-8859-1
# vim: tw=80 ts=4 sw=4 fenc=latin-1 noet
# -----------------------------------------------------------------------------
# Project           :   Sink                   <http://sofware.type-z.org/sink>
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   20-Mar-2005
# Last mod.         :   25-Jul-2006
# -----------------------------------------------------------------------------

import sys ; sys.path.insert(0, "Sources")
from tahchee import main
from distutils.core import setup

SUMMARY     = "Multiple directory change detection and synchronization"
DESCRIPTION = """\
Sink allows easy and fast comparison of multiple repositories, compared to one
"origin" directory. Sink then allows to easily bind actions to the various
detected changes, such as uploading files or running a diff utility. Sink is an
ideal companion to a revision control system, or when you have multiple modified
copies of a single directory.
"""
# ------------------------------------------------------------------------------
#
# SETUP DECLARATION
#
# ------------------------------------------------------------------------------

setup(
    name        = "Sink",
    version     = main.__version__,
    author      = "Sebastien Pierre", author_email = "sebastien@type-z.org",
    description = SUMMARY, long_description = DESCRIPTION,
    license     = "Revised BSD License",
    keywords    = "change detection, synchronization",
    url         = "http://www.ivy.fr/sink",
    download_url= "http://www.ivy.fr/sink/sink-%s.tar.gz" % (main.__version__) ,
    package_dir = { "": "Sources" },
    packages    = ["sink"],
    scripts     = ["Scripts/sink"],
    classifiers = [
      "Development Status :: 4 - Beta",
      "Environment :: Web Environment",
      "Intended Audience :: Developers",
      "Intended Audience :: Information Technology",
      "License :: OSI Approved :: BSD License",
      "Natural Language :: English",
      "Topic :: System :: Archiving :: Backup",
      "Topic :: System :: Archiving :: Mirroring",
      "Topic :: System :: Filesystems",
      "Topic :: Utilities",
      "Operating System :: POSIX",
      "Operating System :: Microsoft :: Windows",
      "Programming Language :: Python",
    ]
)

# EOF
