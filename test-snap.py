from sink2.snap import snapshot
from sink2.diff import diff
from sink2.utils import gitignored
import sys


# a = snapshot(".").save("a.json")
# b = Snapshot.Load("a.json")
# for node in snapshot(sys.argv[1]):
#     print(node)
gitignore = gitignored()
a = snapshot("../../Current/nzx-ticker-api", rejects=gitignore)
b = snapshot("../../Current/nzx-ticker-api--SP-playground-DEAD", rejects=gitignore)
counter = 0
for path, status in diff(a, b).items():
    print(f"{counter:04d} {''.join(status)} {path}")
    counter += 1
