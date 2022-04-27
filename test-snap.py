from sink2.snap import Snapshot, snapshot


a = snapshot(".").save("a.json")
b = Snapshot.Load("a.json")
