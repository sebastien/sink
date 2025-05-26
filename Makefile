
# --
# ## Make & Shell Configuration

SHELL:= bash
.SHELLFLAGS:= -eu -o pipefail -c
MAKEFLAGS+= --warn-undefined-variables
MAKEFLAGS+= --no-builtin-rules

# --
# ## Python Configuration

PYTHON=python3
PYTHON_MODULES=$(patsubst src/py/%,%,$(wildcard src/py/*))
PYTHON_MODULES_PIP=flake8 bandit mypy
PYTHONPATH:=$(abspath run/lib/python)$(if $(PYTHONPATH),:$(PYTHONPATH))
export PYTHONPATH

# --
# ## Sources Configuration

SOURCES_BIN:=$(wildcard bin/*)
SOURCES_PY_PATH=src/py
SOURCES_PY:=$(wildcard $(SOURCES_PY_PATH)/*.py $(SOURCES_PY_PATH)/*/*.py $(SOURCES_PY_PATH)/*/*/*.py $(SOURCES_PY_PATH)/*/*/*/*.py)
MODULES_PY:=$(filter-out %/__main__,$(filter-out %/__init__,$(SOURCES_PY:$(SOURCES_PY_PATH)/%.py=%)))

LOCAL_PY_PATH=$(firstword $(shell $(PYTHON) -c "import sys,pathlib;sys.stdout.write(' '.join([_ for _ in sys.path if _.startswith(str(pathlib.Path.home()))] ))"))
LOCAL_BIN_PATH=$(HOME)/.local/bin

PREP_ALL=$(PYTHON_MODULES_PIP:%=build/py-install-%.task)

# --
# ## Commands

BANDIT=$(PYTHON) -m bandit
FLAKE8=$(PYTHON) -m flake8
MYPY=$(PYTHON) -m mypy
MYPYC=mypyc

cmd-check=if ! $$(which $1 &> /dev/null ); then echo "ERR Could not find command $1"; exit 1; fi; $1

.PHONY: prep
prep: $(PREP_ALL)
	@

.PHONY: run
run:
	@

.PHONY: ci
ci: check test
	@

.PHONY: audit
audit: check-bandit
	@echo "=== $@"

# NOTE: The compilation seems to create many small modules instead of a big single one
.PHONY: compile
compile:
	@echo "=== $@"
	echo "Compiling $(MODULES_PY): $(SOURCES_PY)"
	# NOTE: Output is going to be like 'extra/__init__.cpython-310-x86_64-linux-gnu.so'

	mkdir -p "build"
	$(foreach M,$(MODULES_PY),mkdir -p build/$M;)
	env -C build MYPYPATH=$(realpath .)/src/py mypyc -p extra

.PHONY: check
check: check-bandit check-flakes check-strict
	echo "=== $@"

.PHONY: check-compiled
check-compiled:
	@
	echo "=== $@"
	COMPILED=$$(PYTHONPATH=build python -c "import extra;print(extra)")
	echo "Extra compiled at: $$COMPILED"

.PHONY: check-bandit
check-bandit: $(PREP_ALL)
	@echo "=== $@"
	$(BANDIT) -r -s B101 $(wildcard src/py/*)

.PHONY: check-flakes
check-flakes: $(PREP_ALL)
	@echo "=== $@"
	$(FLAKE8) --ignore=E1,E203,E302,E401,E501,E704,E741,E266,F821,W  $(SOURCES_PY)

.PHONY: check-mypyc
check-mypyc: $(PREP_ALL)
	@$(call cmd-check,mypyc)  $(SOURCES_PY)

.PHONY: check-strict
check-strict: $(PREP_ALL)
	@
	count_ok=0
	count_err=0
	files_err=
	for item in $(SOURCES_PY); do
		if $(MYPY) --strict $$item; then
			count_ok=$$(($$count_ok+1))
		else
			count_err=$$(($$count_err+1))
			files_err+=" $$item"
		fi
	done
	summary="OK $$count_ok ERR $$count_err TOTAL $$(($$count_err + $$count_ok))"
	if [ "$$count_err" != "0" ]; then
		for item in $$files_err; do
			echo "ERR $$item"
		done
		echo "EOS FAIL $$summary"
		exit 1
	else
		echo "EOS OK $$summary"
	fi

.PHONY: lint
lint: check-flakes
	@

.PHONY: format
format:
	@black $(SOURCES_PY)

.PHONY: install
install:
	@for file in $(SOURCES_BIN); do
		echo "Installing $(LOCAL_BIN_PATH)/$$(basename $$file)"
		ln -sfr $$file "$(LOCAL_BIN_PATH)/$$(basename $$file)"
		mkdir -p "$(LOCAL_BIN_PATH)"
	done
	if [ ! -e "$(LOCAL_PY_PATH)" ]; then
		mkdir -p "$(LOCAL_PY_PATH)"
	fi
	if [ -d "$(LOCAL_PY_PATH)" ]; then
		for module in $(PYTHON_MODULES); do
			echo "Installing $(LOCAL_PY_PATH)/$$module"
			ln -sfr src/py/$$module "$(LOCAL_PY_PATH)"/$$module
		done
	else
		echo "No local Python module path found:  $(LOCAL_PY_PATH)"
	fi


.PHONY: try-install
try-uninstall:
	@for file in $(SOURCES_BIN); do
		unlink $(LOCAL_BIN_PATH)/$$(basename $$file)
	done
	if [ -s "$(LOCAL_PY_PATH)" ]; then
		for module in $(PYTHON_MODULES); do
			unlink "$(LOCAL_PY_PATH)"/$$module
		done
	fi

build/py-install-%.task:
	@
	mkdir -p run/lib/python
	if $(PYTHON) -mpip install --target=run/lib/python --upgrade '$*'; then
		mkdir -p "$(dir $@)"
		touch "$@"
	fi

print-%:
	$(info $*=$($*))

.ONESHELL:
# EOF
