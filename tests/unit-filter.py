from sink.matching import filters, pattern, matches, gitignored, dotfile

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
""".split(
    "\n"
)

l = [_ for _ in FILES if matches(_, rejects=pattern(["node_modules"]))]
assert len(l) == 1, f"Expected 1, got: {l}"

print(pattern(["/node_modules"]))
l = [_ for _ in FILES if matches(_, rejects=pattern(["/node_modules"]))]
assert len(l) == 6, f"Expected 6, got: {l}"

# EOF
