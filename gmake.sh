#!/bin/bash
# Wrapper script to ensure GNU Make is used

set -euo pipefail

# Check if gmake is available
if command -v gmake >/dev/null 2>&1; then
    echo "Using gmake..."
    exec gmake "$@"
elif command -v make >/dev/null 2>&1; then
    # Check if the default make is GNU Make
    if make --version 2>/dev/null | head -1 | grep -q "GNU Make"; then
        echo "Using GNU Make (via 'make' command)..."
        exec make "$@"
    else
        echo "Error: GNU Make is required but not found."
        echo "Please install GNU Make:"
        echo "  macOS: brew install make"
        echo "  Ubuntu/Debian: apt-get install make"
        echo "  CentOS/RHEL: yum install make"
        exit 1
    fi
else
    echo "Error: No make command found."
    echo "Please install GNU Make:"
    echo "  macOS: brew install make"
    echo "  Ubuntu/Debian: apt-get install make"
    echo "  CentOS/RHEL: yum install make"
    exit 1
fi