"""
Defines the supply-chain firewall's command-line interface and performs argument parsing.
"""

from argparse import Namespace
from enum import Enum
import logging
import sys
from typing import Callable, Optional

import scfw
from scfw.ecosystem import ECOSYSTEM
from scfw.parser import ArgumentError, ArgumentParser

_LOG_LEVELS = list(
    map(
        logging.getLevelName,
        [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
    )
)
_DEFAULT_LOG_LEVEL = logging.getLevelName(logging.WARNING)


def _add_configure_cli(parser: ArgumentParser) -> None:
    """
    Defines the command-line interface for the firewall's `configure` subcommand.

    Args:
        parser: The `ArgumentParser` to which the `configure` command line will be added.
    """
    return


def _add_run_cli(parser: ArgumentParser) -> None:
    """
    Defines the command-line interface for the firewall's `run` subcommand.

    Args:
        parser: The `ArgumentParser` to which the `run` command line will be added.
    """
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify any installation targets but do not run the package manager command"
    )

    parser.add_argument(
        "--executable",
        type=str,
        default=None,
        metavar="PATH",
        help="Python or npm executable to use for running commands (default: environmentally determined)"
    )


class Subcommand(Enum):
    """
    The set of subcommands that comprise the supply-chain firewall's command line.
    """
    Configure = "configure"
    Run = "run"

    def _parser_spec(self) -> dict:
        """
        Return the `ArgumentParser` configuration for the given subcommand's parser.

        Returns:
            A `dict` of `kwargs` to pass to the `argparse.SubParsersAction.add_parser()`
            method for configuring the subparser corresponding to the subcommand.
        """
        match self:
            case Subcommand.Configure:
                return {
                    "exit_on_error": False,
                    "description": "Configure the environment for using the supply-chain firewall."
                }
            case Subcommand.Run:
                return {
                    "usage": "%(prog)s [options] COMMAND",
                    "exit_on_error": False,
                    "description": "Run a package manager command through the supply-chain firewall."
                }

    def _cli_spec(self) -> Callable[[ArgumentParser], None]:
        """
        Return a function for adding the given subcommand's command-line options
        to a given `ArgumentParser`.

        Returns:
            A `Callable[[ArgumentParser], None]` that adds the command-line options
            for the subcommand to the `ArgumentParser` it is given, in the intended
            case via a sequence of calls to `ArgumentParser.add_argument()`.
        """
        match self:
            case Subcommand.Configure:
                return _add_configure_cli
            case Subcommand.Run:
                return _add_run_cli


def _cli() -> ArgumentParser:
    """
    Defines the command-line interface for the supply-chain firewall.

    Returns:
        A parser for the supply-chain firewall's command line.

        This parser only handles the firewall's own optional arguments and subcommands.
        It does not parse the package manager commands being run through the firewall.
    """
    parser = ArgumentParser(
        prog="scfw",
        exit_on_error=False,
        description="A tool for preventing the installation of malicious PyPI and npm packages."
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=scfw.__version__
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=_LOG_LEVELS,
        default=_DEFAULT_LOG_LEVEL,
        metavar="LEVEL",
        help="Desired logging level (default: %(default)s, options: %(choices)s)"
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    for subcommand in Subcommand:
        subparser = subparsers.add_parser(subcommand.value, **subcommand._parser_spec())
        subcommand._cli_spec()(subparser)

    return parser


def _parse_command_line(argv: list[str]) -> tuple[Optional[Namespace], str]:
    """
    Parse the supply-chain firewall's command line from a given argument vector.

    Args:
        argv: The argument vector to be parsed.

    Returns:
        A `tuple` of a `Namespace` object containing the results of parsing the given
        argument vector and a `str` help message for the caller's use in early exits.
        In the case of a parsing failure, `None` is returned instead of a `Namespace`.

        On success, and only for the `run` subcommand, the returned `Namespace` contains
        the package manager command present in the given argument vector as a `list[str]`
        under the `command` attribute.
    """
    hinge = len(argv)
    for ecosystem in ECOSYSTEM:
        try:
            hinge = min(hinge, argv.index(ecosystem.value))
        except ValueError:
            pass

    parser = _cli()
    help_msg = parser.format_help()

    try:
        args = parser.parse_args(argv[1:hinge])

        # Only allow a package manager `command` argument when
        # the user selected the `run` subcommand
        match Subcommand(args.subcommand), argv[hinge:]:
            case Subcommand.Run, []:
                raise ArgumentError
            case Subcommand.Run, _:
                args_dict = vars(args)
                args_dict["command"] = argv[hinge:]
            case _, []:
                pass
            case _:
                raise ArgumentError

        return args, help_msg

    except ArgumentError:
        return None, help_msg


def parse_command_line() -> tuple[Optional[Namespace], str]:
    """
    Parse the supply-chain firewall's command line.

    Returns:
        A `tuple` of a `Namespace` object containing the results of parsing the
        firewall's command line and a `str` help message for the caller's use in
        early exits. In the case of a parsing failure, `None` is returned instead
        of a `Namespace`.

        On success, the returned `Namespace` contains the package manager command
        provided to the firewall as a (possibly empty) `list[str]` under the `command`
        attribute.
    """
    return _parse_command_line(sys.argv)
