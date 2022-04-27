from sink2.snap import snapshot
from sink2.utils import json


print(json(snapshot(".").nodes))
