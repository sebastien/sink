#!/usr/bin/python
# -----------------------------------------------------------------------------
# Project           :   Sink
# -----------------------------------------------------------------------------
# Author            :   Sebastien Pierre                 <sebastien@type-z.org>
# License           :   Revised BSD License
# -----------------------------------------------------------------------------
# Creation date     :   2005-04-20
# Last mod.         :   2021-07-25
# -----------------------------------------------------------------------------

from distutils.core import setup

SUMMARY = "Multiple directory change detection and synchronization"
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
    name="sink",
    version="1.1.0",
    author="Sebastien Pierre", author_email="sebastien@type-z.org",
    description=SUMMARY, long_description=DESCRIPTION,
    license="Revised BSD License",
    keywords="change detection, synchronization",
    url="http://github.com/sebastien/sink",
    download_url="http://github.com/sebastien/sink/tarball/master",
    package_dir={"": "src"},
    packages=["sink"],
    scripts=["bin/sink"],
    classifiers=[
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

# EOF - vim: tw=80 ts=4 sw=4 fenc=latin-1 noet
