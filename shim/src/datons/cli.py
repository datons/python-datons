"""Datons CLI — manage authentication and configuration.

Usage:
    datons auth set <KEY>     Save API key to ~/.config/datons/config.toml
    datons auth show          Show the saved key (masked)
    datons auth remove        Remove the saved key
"""

from __future__ import annotations

import argparse
import sys

from datons.config import read_api_key, remove_api_key, write_api_key


def _auth_set(args: argparse.Namespace) -> None:
    write_api_key(args.key)
    masked = args.key[:8] + "..." + args.key[-4:] if len(args.key) > 12 else args.key[:4] + "..."
    print(f"API key saved: {masked}")


def _auth_show(_args: argparse.Namespace) -> None:
    key = read_api_key()
    if not key:
        print("No API key configured.")
        print("Set one with: datons auth set <KEY>")
        sys.exit(1)
    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else key[:4] + "..."
    print(f"API key: {masked}")


def _auth_remove(_args: argparse.Namespace) -> None:
    if remove_api_key():
        print("API key removed.")
    else:
        print("No API key to remove.")


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="datons",
        description="Datons CLI — Python client for Datons data APIs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # datons auth
    auth_parser = subparsers.add_parser("auth", help="Manage API key authentication")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")

    # datons auth set <KEY>
    set_parser = auth_sub.add_parser("set", help="Save API key")
    set_parser.add_argument("key", help="Your Datons API key")
    set_parser.set_defaults(func=_auth_set)

    # datons auth show
    show_parser = auth_sub.add_parser("show", help="Show saved API key (masked)")
    show_parser.set_defaults(func=_auth_show)

    # datons auth remove
    remove_parser = auth_sub.add_parser("remove", help="Remove saved API key")
    remove_parser.set_defaults(func=_auth_remove)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "auth" and not args.auth_command:
        auth_parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
