from typing import Callable, Optional, NamedTuple, Generic, TypeVar, Iterator, Any, cast
from contextlib import contextmanager
from io import TextIOWrapper
import argparse
import inspect
import re
import sys

T = TypeVar("T")
# --
# # CLI EDSL
#
# We define a simple `cli` decorator that parses argument declarations into
# an `argparse`-compatible argument definition.

RE_SPACES = re.compile(r"\s+")
RE_COMMAND = re.compile(
	r"((-(?P<short>[a-zA-Z0-9]))?(\|?--(?P<long>[a-z0-9\-]+))|(?P<arg>[A-Z]+))(?P<card>[\?\*\+]?)"
)
RE_ARG = re.compile(r"\s*(?P<arg>[a-z0-9]+|[A-Z]+):(?P<text>.*)$")

# --
# Commands are aggregated into the `COMMANDS` dictionary, which can
# then be fed to `argparse`.
TArgument = tuple[list[str], dict[str, Any]]
COMMANDS: dict[str, "Command"] = {}


def camelCase(text: str) -> str:
	"""Converts the given string to `camelCase`"""
	return "".join(
		_.lower() if i == 0 else _.capitalize() for i, _ in enumerate(text.split("-"))
	)


@contextmanager
def write(path: Optional[str] = None, append: bool = False) -> Iterator[TextIOWrapper]:
	"""Returns a writable file-like text object"""
	output: Optional[str] = None if path in (None, "-") else path
	try:
		if output:
			with open(output, "at" if append else "wt") as f:
				yield f
		else:
			yield cast(TextIOWrapper, sys.stdout)
	except Exception as e:
		raise e
	finally:
		pass


def copydoc(
	functor: Callable[..., Any],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
		f.__doc__ = functor.__doc__
		return f

	return decorator


def option(
	*args: Any, **kwargs: Any
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	"""Returns a functor that can be applied to an argparse
	`parser.add_argument` method."""
	return lambda f: f(*args, **kwargs)


# --
# The `cli` decorate is the heart of this module, and as such is a relatively
# meaty piece of code. The overall idea is to use the decorator in a way
# that is expressive, and produces data that can be used to parameter
# an `argparse` subparser.


class Command(NamedTuple):
	functor: Callable[[Any], Any]
	doc: Optional[str]
	args: dict[str, TArgument]
	options: list[Callable[..., Any]]
	aliases: list[str]


def command(
	*args: str,
	options: Optional[list[Callable[..., Any]]] = None,
	alias: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	"""Decorator used to register a function as a CLI command. Arguments
	are like `("-o","-f|--format", "FILE+")` and the decorated function
	should have a documentation that contains lines like
	`o: Output file` or `format: Output format` or `FILE: Input file(s)`."""
	cli_args: dict[str, TArgument] = {}
	# We iterate on the arguments
	for i, p in enumerate(args):
		# The following extracts the `argparse.add_argument` information and
		# stores it in `p_args` and `p_kwargs`.
		p_args: list[str] = []
		p_kwargs: dict[str, Any] = {}
		if not (m := RE_COMMAND.match(p)):
			raise ValueError(
				f"Incorrect argument format: {p} for argument {i} in {args}"
			)
		else:
			short = m.group("short")
			long = m.group("long")
			card = m.group("card")
			# Do we have an option, like -f or --format?
			if short or long:
				name = long or short
				if short:
					p_args.append(f"-{short}")
				if long:
					p_args.append(f"--{long}")
				# NOTE: Using append is actually better than
				# using nargs there.
				if card in "+*":
					p_kwargs["action"] = "append"

				p_kwargs["dest"] = name
				cli_args[name] = (p_args, p_kwargs)
			# Or do we have an argument, like FILE?
			else:
				arg = m.group("arg")
				p_args.append(arg.lower())
				p_kwargs["metavar"] = arg
				if card:
					p_kwargs["nargs"] = card
				# We add the value to the `cli_args`
				cli_args[arg] = (p_args, p_kwargs)

	# We convert the arg names
	pythonArgNames = {camelCase(_): _ for _ in cli_args}

	# That's the decorator's wrapper
	def wrapper(
		f: Callable[..., Any], alias: Optional[str] = alias
	) -> Callable[..., Any]:
		# We now extract the arguments help from the command line
		# help, and update the `cli_args` accordingly.
		doc: list[str] = []
		arg_doc: dict[str, str] = {}
		# We merge in the default values, this is a bit annoying to do, but
		# we need to map python arg names to CLI arg names, which don't use
		# the same convention.
		arg_spec = inspect.getfullargspec(f)
		if arg_spec.defaults:
			for i, k in enumerate(arg_spec.args):
				kk = pythonArgNames[k]
				cli_args[kk][1].setdefault("default", arg_spec.defaults[i])
		for k, v in (arg_spec.kwonlydefaults or {}).items():
			if k not in pythonArgNames:
				continue
			kk = pythonArgNames[k]
			cli_args[kk][1].setdefault("default", v)
		for line in (f.__doc__ or "").split("\n"):
			if not (m := RE_ARG.match(line)):
				doc.append(line)
			else:
				arg_doc[m.group("arg")] = m.group("text")
		# Merges the extracted `arg_doc` into the `cli_args` `help` field.
		for k, v in cli_args.items():
			_, kw = v
			if k in arg_doc:
				kw["help"] = arg_doc[k].strip()
				del arg_doc[k]
		if arg_doc:
			raise ValueError(
				f"Cannot match documentation arguments: {', '.join(_ for _ in arg_doc)} with {', '.join(_ for _ in cli_args)}"
			)

		# We register the commands now
		c_doc = RE_SPACES.sub(" ", " ".join(doc).strip())
		cmd = Command(
			functor=f,
			doc=c_doc,
			args=cli_args,
			options=options or [],
			aliases=[_.strip() for _ in (alias or "").split("|") if _.strip()],
		)
		COMMANDS[f.__name__.lstrip("_")] = cmd
		return f

	return wrapper


class CLI(Generic[T]):
	def __init__(self, context: T):
		self.context: T = context

	def ask(self, prompt: str) -> str:
		return input(prompt)

	def out(self, text: str) -> None:
		sys.stdout.write(text)


# --
# This is the entry point to process the command line function registered
# in the `COMMANDS` mapping.
def run(
	args: list[str] = sys.argv[1:],
	name: Optional[str] = None,
	description: Optional[str] = None,
	context: Optional[Any] = None,
) -> int:
	"""Runs the given command, as passed on the command line"""
	# FROM: https://stackoverflow.com/questions/10448200/how-to-parse-multiple-nested-sub-commands-using-python-argparse
	if not args:
		args = ["--help"]
	parser = argparse.ArgumentParser(prog=name, description=description)
	subparsers = parser.add_subparsers(help="Available subcommands", dest="subcommand")
	# We register the subcommands
	for name, cmd in COMMANDS.items():
		# We create a subparser
		# TODO: Support aliases
		func, doc, argsdef, options, aliases = cmd
		subparser = subparsers.add_parser(name, help=doc)
		for o in options:
			o(subparser.add_argument)
		# And then register the arguments as part of the subparser
		for a in argsdef.values():
			subparser.add_argument(*a[0], **a[1])

	# We parse the arguments
	parsed = None
	rest = args
	while rest:
		p, rest = parser.parse_known_args(rest)
		if p.subcommand:
			parsed = p
		if not p.subcommand:
			break
	# We could not parse everything
	if rest:
		raise ValueError("Cannot parse the command", parsed, rest)
	# Or we've parsed something and we have the matching subcommand
	elif parsed and (cmd_name := parsed.subcommand):
		fun, _, cmd_args, options, _ = COMMANDS[cmd_name]
		# FIXME: The conversation to lower here is likely to break at some point
		# TODO: Should pass parsed there
		fun_kwargs = {camelCase(k): getattr(parsed, k.lower()) for k in cmd_args}
		try:
			result = fun(CLI(context), **fun_kwargs)
		except TypeError as e:
			sys.stderr.write(
				f"CLI arguments mismatch:\n"
				f" - command-line options are: {', '.join(f'#{i}={_}' for i, _ in enumerate(cmd_args))}\n"
				f" - argument values are: {fun_kwargs}\n"
			)
			raise e
		return result or 0
	else:
		# FIXME: Not sure what is going in there
		raise RuntimeError("Unexpected arguments")


# EOF
