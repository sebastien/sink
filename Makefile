# Sink makefile
# ----------------
#
# Revision 1.6.0 (26-Jul-2007)
#
# Distributed under BSD License
# See <www.type-z.org/copyleft.html>
# (c) Sébastien Pierre - http://www.type-z.org, http://www.ivy.fr 2003 - 2007
#
#  This Makefile is intendended for developers only. It allows to automate
#  common tasks such as checking the code, getting statistics, listing the TODO,
#  FIXME, etc, generating the documentation, packaging a source tarball and so
#  on.
#
#  On of the main advantage is that this Makefile can "prepare" the development
#  environment quickly by creating a symblink from the main package to the
#  proper location in Python site-packages, so that testing can be done without
#  having to run 'setup.py install' each time.
#  
#  For that reason, end-users will use the setup.py, while developers will
#  typically want to use this makefile, by first running "make prepare".


# Project variables___________________________________________________________
#
# Project name. Do not put spaces.
PROJECT         = Sink
PROJECT_VERSION = $(shell grep -r  __version__ Sources | head -n1 | cut -d'"' -f2)
PROJECT_STATUS  = RELEASE

DOCUMENTATION   = Documentation
SOURCES         = Sources
TESTS           = Tests
SCRIPTS         = Scripts
RESOURCES       = Resources
DISTRIBUTION    = Distribution
API             = $(DOCUMENTATION)/sink-api.html
DOCS            = $(API) MANUAL.txt MANUAL.html
DISTROCONTENT   = $(DOCS) $(SOURCES) $(TESTS) $(SCRIPTS) $(RESOURCES) \
                  Makefile setup.py

# Project files_______________________________________________________________

PACKAGE         = sink
MAIN            = main.py
MODULES         = sink.main sink.tracking sink.linking sink.snaphot

TEST_MAIN       = $(TESTS)/$(PROJECT)Test.py
SOURCE_FILES    = $(shell find $(SOURCES) -name "*.py")
TEST_FILES      = $(shell find $(TESTS) -name "*.py")
CHECK_BLACKLIST = 

# Tools_______________________________________________________________________

PYTHON          = $(shell which python)
PYTHONHOME      = $(shell $(PYTHON) -c \
 "import sys;print filter(lambda x:x[-13:]=='site-packages',sys.path)[0]")
SDOC            = $(shell which sdoc)
PYCHECKER       = $(shell which pychecker)
CTAGS           = $(shell which ctags)
KIWI            = $(shell which kiwi)

# Useful variables____________________________________________________________

CURRENT_ARCHIVE = $(PROJECT)-$(PROJECT_VERSION).tar.gz
# This is the project name as lower case, used in the install rule
project_lower   = $(shell echo $(PROJECT) | tr "A-Z" "a-z")
# The installation prefix, used in the install rule
prefix          = /usr/local

# Rules_______________________________________________________________________

.PHONY: help info preparing-pre clean check dist doc tags todo

help:
	@echo "$(PROJECT) development make rules:"
	@echo
	@echo "Developers:"
	@echo "    prepare - prepares the project, may require editing this file"
	@echo "    check   - executes pychecker"
	@echo "    clean   - cleans up build files"
	@echo "    doc     - generates the documentation"
	@echo "    tags    - generates ctags"
	@echo "    todo    - view TODO, FIXMES, etc"
	@echo "    dist    - generates distribution"
	@echo
	@echo "Users:"
	@echo "    test    - executes the test suite"
	@echo "    info    - displays project information"
	@echo

all: prepare clean check test doc dist
	@echo "Making everything for $(PROJECT)"

info:
	@echo "$(PROJECT)-$(PROJECT_VERSION) ($(PROJECT_STATUS))"
	@echo Source file lines:
	@wc -l $(SOURCE_FILES)

todo:
	@grep  -R --only-matching "TODO.*$$"  $(SOURCE_FILES)
	@grep  -R --only-matching "FIXME.*$$" $(SOURCE_FILES)

prepare:
	@echo "WARNING : You may required root priviledges to execute this rule."
	@echo "Preparing python for $(PROJECT)"
	sudo ln -snf $(PWD)/$(SOURCES)/$(PACKAGE) \
		  $(PYTHONHOME)/$(PACKAGE)
	@echo "Preparing done."

clean:
	@echo "Cleaning $(PROJECT)."
	@find . -name "*.pyc" -or -name "*.sw?" -or -name ".DS_Store" -or -name "*.bak" -or -name "*~" -exec rm '{}' ';'
	@rm -rf $(DOCUMENTATION)/API build dist

check:
	@echo "Checking $(PROJECT) sources :"
ifeq ($(shell basename spam/$(PYCHECKER)),pychecker)
	@$(PYCHECKER) -b $(CHECK_BLACKLIST) $(SOURCE_FILES)
	@echo "Checking $(PROJECT) tests :"
	@$(PYCHECKER) -b $(CHECK_BLACKLIST) $(TEST_FILES)
else
	@echo "You need Pychecker to check $(PROJECT)."
	@echo "See <http://pychecker.sf.net>"
endif
	@echo "done."

test: $(SOURCE_FILES) $(TEST_FILES)
	@echo "Testing $(PROJECT)."
	@$(PYTHON) $(TEST_MAIN)

dist:
	@echo "Creating archive $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION).tar.gz"
	@mkdir -p $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)
	@cp -r $(DISTROCONTENT) $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)
	@make -C $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION) clean
	@make -C $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION) doc
	@tar cfz $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION).tar.gz \
	-C $(DISTRIBUTION) $(PROJECT)-$(PROJECT_VERSION)
	@rm -rf $(DISTRIBUTION)/$(PROJECT)-$(PROJECT_VERSION)

doc: $(DOCS)
	@echo "Generating $(PROJECT) documentation"

$(API): $(SOURCE_FILES)
ifeq ($(shell basename spam/$(SDOC)),sdoc)
	@$(SDOC) -cp$(SOURCES) $(MODULES) $(API)
else
	@echo "Sdoc is required to generate $(PROJECT) documentation."
	@echo "Please see <http://www.ivy.fr/sdoc>"
endif

tags:
	@echo "Generating $(PROJECT) tags"
ifeq ($(shell basename spam/$(CTAGS)),ctags)
	@$(CTAGS) -R
else
	@echo "Ctags is required to generate $(PROJECT) tags."
	@echo "Please see <http://ctags.sf.net>"
endif

%.html: %.txt
ifeq ($(shell basename spam/$(KIWI)),kiwi)
	$(KIWI) -m -ilatin-1 $< $@
else
	@echo "Kiwi is required to the $< file."
	@echo "Please see <http://www.ivy.fr/kiwi>"
endif

#EOF
