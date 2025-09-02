# Sink Backup

We introduce a `sink backup -t script SRC_PATH [PATH_OR_SNAPSHOT]` command that outputs
commands that describe the changes to be made for `PATH_OR_SNAPSHOT` to become
like `SRC_PATH`. When `PATH_OR_SNAPSHOT` is empty, this is a list of all the commands
to create `SRC_PATH`

Here's an example:

```
# Backup of SRC_PATH from PATH_OR_SNAPSHOT on YYYY-MM-DDTHH:MM:SS
RM PATH
DATA PATH
META PATH mode=MODE uid=UID gid=GID ctime=TIME mtime=TIME
LN PATH ORIGIN
```

The commands are:

- `RM PATH` to remove the file or directory at `PATH`
- `DATA PATH` to update the data at `PATH`
- `META PATH mode=MODE uid=UID gid=GID ctime=TIME mtime=TIME` to update any of the given meta attributes at the given `PATH`
- `LN PATH ORIGIN` to make `PATH` point to `ORIGIN`

The options are:

- `-r|--root=ROOT_PATH` `PATH` in commands will be relative to `ROOT_PATH`, which is `SRC_PATH` by default.

- `-t|--type=TYPE` where `TYPE` is the type of backup, here it is `script` by default.

## Implementation

In `src/py/sink/backup.py`:
- Define `OpRm`, `OpData`, `OpMeta`, `OpLn` name tuples representing each operation with `Op=OpRm|OpData|OpMeta|OpLn`
- Following `src/sink/diff.py`, implement `iops(current:Snapshot, other:Optional[Snapshot]=None):Iterator[Op]` that
  streams operations to unify `other` with `current`
- Implement `iscript(current:Snapshot, other:Optional[Snapshot]=None):Iterator[str]` that converts each op into the
  format above.

In `src/py/sink/commands.py`, implement the `backup` command, which when the type is script runs the `iscript` function. If the type is different, throw an error.
