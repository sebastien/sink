```
 _______  ___   __    _  ___   _
|       ||   | |  |  | ||   | | |
|  _____||   | |   |_| ||   |_| |
| |_____ |   | |       ||      _|
|_____  ||   | |  _    ||     |_
 _____| ||   | | | |   ||    _  |
|_______||___| |_|  |__||___| |_|

``````

Sink is a the swiss army knife for directory comparison and synchronization.
With sink, you can:

- Compare multiple (2+) directories
- Take filesystem state snapshots
- Compare snapshots and states

Here are few uses cases where `sink` comes in handy:

- Compare multiple versions of a source tree (replacing `diff -r`)
- Manually merge directories outside of a revision control system
- Synchronize files belonging to different directories
- Track changes made to specific directory
- Implement incremental backup and restor
- Detect changes made to configuration fiels
- DIY version control system

# Quickstart

`sink` simply requires Python (2.7, 3+) to run. To install it, simply do:

```
python -m pip install --user sink
```

and then you're in business. Take a snapshot of your filesystem

```bash
$ sink snap ~ ~/home-$(date '+%Y%m%d').json
```

do some changes, and then compare it

```bash
$ sink diff ~/home-$(date '+%Y%m%d').json ~
```

Using `sink` is overall pretty straightforward:

- `sink diff ORIGIN COMPARE…` to compare two or more directories. Note that
   ORIGIN or COMPARE can be a snapshot JSON file (see below).
- `sink snap DIR` to take a snapshot (output as JSON) of the DIR state
- `sink snap FILE.json` lists the contents of the snapshot i

# Use Case: Comparing directories

Imagine you have 3 different versions of a specific source tree. In this
example, we'll simply checkout three different revisions of the `sink`
development tree:

```bash
$ git clone git://github.com/sebastien/sink.git sink-r1
$ git clone git://github.com/sebastien/sink.git sink-r2
$ git clone git://github.com/sebastien/sink.git sink-r3
```

and we compare the three directories:

```bash
$ sink diff sink-r1 sink-r2 sink-r3
No differences
```

as the three directories are the same, we'll put them to different revisions:

```bash
cd sink-r1 ; git checkout -b older a17609eaabbf8feb3b480d46cb972df0599755fe ; cd ..
cd sink-r2 ; git checkout -b old   9e0e6a476f41f0de685d2c92e142b206b46810e4 ; cd ..
```

and we can now compare the directories:

```bash
sink diff sink-r1 sink-r2 sink-r3
00  ! [+][+] .hgtags
01 [=][-][-] DESIGN
02 [=][<][<] Makefile
03 [=][-][-] NOTES
04 -!--!-[+] README
05 [=][-][-] ROADMAP
06 [=][>][<] TODO
07 -!-[+][+] setup.py
08 -!-[+]-!- Documentation/DESIGN.txt
09 -!-[+]-!- Documentation/MANUAL.txt
10 [=][=][-] Resources/epydoc.css
11 -!-[+][+] Scripts/sink
12 [=][-][-] Sources/sink/Sink.py
13 [=][-][-] Sources/sink/Tracking.py
14 -!-[+][+] Sources/sink/linking.py
15 -!-[+][+] Sources/sink/main.py
16 -!--!-[+] Sources/sink/snapshot.py
17 -!-[+][+] Sources/sink/tracking.py
```

`sink` has found differences and indicates them in the form of a table, where the
legend can be found in the `sink --help diff` command:

```
[=] no changes         [+] file added           [>] changed/newer
                       [-] file removed         [<] changed/older
                       -!- file missing
```

we can have a list of all the files that were added in `sink-r2` and `sink-r3`
by showing only the added files:

```shell
$ sink diff +a sink-r1 sink-r2 sink-r3
00 -!-[+][+] .hgtags
01 -!--!-[+] README
02 -!-[+][+] setup.py
03 -!-[+]-!- Documentation/DESIGN.txt
04 -!-[+]-!- Documentation/MANUAL.txt
05 -!-[+][+] Scripts/sink
06 -!-[+][+] Sources/sink/linking.py
07 -!-[+][+] Sources/sink/main.py
08 -!--!-[+] Sources/sink/snapshot.py
09 -!-[+][+] Sources/sink/tracking.py
```

and the output is `cut` friendly:

```shell
$ sink diff +a sink-r1 sink-r2 sink-r3 | cut -d' ' -f3-
.hgtags
README
setup.py
Documentation/DESIGN.txt
Documentation/MANUAL.txt
Scripts/sink
Sources/sink/linking.py
Sources/sink/main.py
Sources/sink/snapshot.py
Sources/sink/tracking.py
```

you can also compare individual changes between all the versions. Let's
see the changes made to the `src/sink/tracking.py` file between `sink-r2`
and `sink-r3`:

```shell
$ sink diff sink-r2 sink-r3
0 -!-[+] README
1 [=][<] TODO
2 [=][-] Documentation/DESIGN.txt
3 [=][-] Documentation/MANUAL.txt
4 [=][-] Resources/epydoc.css
5 [=][<] Sources/sink/linking.py
6 [=][<] Sources/sink/main.py
7 -!-[+] Sources/sink/snapshot.py
8 [=][<] Sources/sink/tracking.py
```

the number of the file in the table is 5, so we pass it to sink `-d` option:

```
$ sink diff -d5 sink-r2 sink-r3
>> gvimdiff sink-r2/Sources/sink/linking.py sink-r3/Sources/sink/linking.py
```

this starts up `gvimdiff`, showing the differences between the files. This is a
great way to do a merge outside of a revision control system.

## Use Case: Directory synchronization

So taking our previous example, let's imaging we'd like to synchronize `sink-r1`
so that it is exactly the same as `sink-r3`.

We start by showing the added or modified files:

```shell
$ sink +a +m sink-r1 sink-r3
00 -!-[+] .hgtags
01 [=][<] Makefile
02 -!-[+] README
03 [=][<] TODO
04 -!-[+] setup.py
05 -!-[+] Scripts/sink
06 -!-[+] Sources/sink/linking.py
07 -!-[+] Sources/sink/main.py
08 -!-[+] Sources/sink/snapshot.py
09 -!-[+] Sources/sink/tracking.py
```

we then pipe the result to `cut` and `xargs`, first to create the directories
that may not exist, and then to copy the files

```shell
$ sink +a +m sink-r1 sink-r3 | cut -d' ' -f3- | xargs dirname | sort | uniq| xargs mkdir -p
$ sink +a +m sink-r1 sink-r3 | cut -d' ' -f3- | xargs -I FILE cp sink-r3/FILE sink-r1/FILE
```

and we make sure the directories are the same:

```
$ sink sink-r1 sink-r3
0 [=][-] DESIGN
1 [=][-] NOTES
2 [=][-] ROADMAP
3 [=][-] Resources/epydoc.css
4 [=][-] Sources/sink/Sink.py
5 [=][-] Sources/sink/Tracking.py
```

we see that we have files to remove from 'sink-r1', so let's do it:

```shell
$ sink +r sink-r1 sink-r3 | cut -d' ' -f3 | xargs -I FILE rm sink-r1/FILE
$ sink sink-r1 sink-r3
No changes found.
```

and we've done the synchronization right. This may look a little bit verbose,
but it's Unix's design philosophy -- have simple tools that do thing, and then
integrate with other tools to do higher-level operations.

## Use Case: Tracking changes made to a directory

Let's say you've just downloaded 'fltk', a cross-platform C++ widget library and
you'd like to install it in /usr/local -- but you want to keep a receipt of the
installed files.

First, get fltk, and compile it

```shell
$ wget 'http://ftp.easysw.com/pub/fltk/1.1.9/fltk-1.1.9-source.tar.bz2'
$ tar fvxj fltk-1.1.9-source.tar.bz2
$ cd fltk-1.1.9 ; ./configure --prefix=/usr/local ; make
```

now we take a snapshot of '/usr/local'

```shell
$ sink snap /usr/local > usr-local.snap
```

you can now install fltk and see the changes:

```
$ sudo make install
$ sink usr-local.snap /usr/local
000 -!-[+] bin/fltk-config
001 -!-[+] lib/libfltk.a
002 -!-[+] lib/libfltk_forms.a
003 -!-[+] lib/libfltk_gl.a
004 -!-[+] lib/libfltk_images.a
005 -!-[+] include/FL/Enumerations.H
006 -!-[+] include/FL/Fl.H
007 -!-[+] include/FL/Fl_Adjuster.H
008 -!-[+] include/FL/Fl_BMP_Image.H
009 -!-[+] include/FL/Fl_Bitmap.H
...
434 -!-[+] share/doc/fltk/examples/pixmaps/whiteking_3.xbm
435 -!-[+] share/doc/fltk/examples/pixmaps/whiteking_4.xbm
436 -!-[+] share/doc/fltk/examples/pixmaps/yellow.xpm
437 -!-[+] share/doc/fltk/examples/pixmaps/yellow_bomb.xpm
```

now you could create a receipt for the installation:

```shell
$ sink +a +m usr-local.snap /usr/local | cut -d' ' -f3- | xargs -IFILE echo /usr/local/FILE > fltk.receipt
```

or create a tarball with the installed files:

```shell
$ tar cvfj fltk-1.1.9-i386.tar.bz2 `sink +a +m usr-local.snap /usr/local | cut -d' ' -f3- | xargs -IFILE echo /usr/local/FILE`
```

## Use Case: Backuping your data

Let's imagine you just got a new slice on Linode, and you'd like to start doing
its configuration. You'd start by creating a snapshot of `etc`:

```shell
$ sudo sink -s /etc > etc-`date  +'%Y%m%d'`.snap
```

you'd then do your modifications and list the changes you made:

```
$ sudo sink etc-20090929.snaphsot /etc
000 [=][>] apt/sources.list
001 [=][>] passwd
002 [=][>] group
...
```

and make a tarball out of your changes:

```
$ tar cvfj node-configured.tar.bz2 `sink +a +m etc-20090929.snap /etc | cut -d' ' -f3- | xargs -IFILE echo etc/FILE`
```

you'll then be able to simply apply the same configuration to a new node by
doing this:

```
$ cd / ; sudo tar fvxj ~/node-configured.tar.bz2
```
