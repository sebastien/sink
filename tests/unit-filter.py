from sink.matching import pattern, gitignored

FILES = """\
src
src/node_modules
src/node_modules/.vite/deps/chunk-ZTU3NHQE.js.map
src/node_modules/.vite/deps/preact.js
src/node_modules/.vite/deps/preact_debug.js
src/node_modules/.vite/deps/preact_hooks.js
node_modules
node_modules/vscode-languageserver/lib/common/semantic.ts
node_modules/vscode-languageserver/lib/common/server.js\
""".split("\n")

# Basic sanity: single glob pattern for "node_modules" compiles and
# matches the top-level directory and its contents.
rx = pattern(["node_modules"])
assert rx is not None
rejected = [p for p in FILES if rx.match(p)]
expected = [
	"node_modules",
	"node_modules/vscode-languageserver/lib/common/semantic.ts",
	"node_modules/vscode-languageserver/lib/common/server.js",
]
assert rejected == expected, rejected

# Exact path syntax with leading "/" should behave the same here.
rx_root = pattern(["/node_modules"])
assert rx_root is not None
rejected_root = [p for p in FILES if rx_root.match(p)]
assert rejected_root == expected, rejected_root

# Regression: combined gitignored() reject patterns should compile
# without raising, even when HOME .gitignore contains complex rules.
rf = gitignored()
rx_all = pattern(rf.rejects)
assert rx_all is not None

# A few representative paths for HOME-level ignores that should be
# matched by the combined reject regex.
for p in [".mypy_cache", "x/.mypy_cache", "node_modules"]:
	assert rx_all.match(p), f"Pattern from gitignored() should match {p!r}"

# EOF
