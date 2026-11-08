from __future__ import annotations

import argparse
import configparser
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .api import HackatimeClient, HackatimeError
from .config import ConfigError, data_file_path, ensure_dev_file, load_config
from .data import DATA
from .render import PINK, render_dashboard

__version__ = "0.1.0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hackfetch",
        description="Show your Hackatime stats in a fastfetch-style dashboard.",
    )
    parser.add_argument(
        "-k",
        "--api-key",
        help="Hackatime API key (defaults to the HACKATIME_API_KEY environment variable).",
    )
    parser.add_argument(
        "-u",
        "--user",
        default="current",
        help='Hackatime user ID, or "current" for the key owner (default: current).',
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds (default: 20).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Config file path (default: ~/.config/hackfetch/config.toml).",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Skip the API and render fake data from data.json.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    return parser


def _load_dev_data(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Dev data file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse {path}: {exc}") from exc

    if not isinstance(payload, dict) or "today" not in payload or "week" not in payload:
        raise ValueError(f'{path} must contain "today" and "week" objects.')

    today = payload["today"]
    week = payload["week"]
    if not isinstance(today, dict) or not isinstance(week, dict):
        raise ValueError(f'{path}: "today" and "week" must both be objects.')

    return today, week


def read_wakatime_key(path: Path | None = None) -> str | None:
    """Return api_key from ~/.wakatime.cfg [settings], or None if unavailable."""
    cfg_path = (
        path or Path(os.environ.get("WAKATIME_HOME") or Path.home()) / ".wakatime.cfg"
    )
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(cfg_path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return None
    key = parser.get("settings", "api_key", fallback="").strip()
    return key or None


def resolve_api_key(cli_key: str | None) -> str | None:
    """Pick the key from the CLI flag, then env vars, then ~/.wakatime.cfg."""
    return (
        cli_key
        or os.environ.get("HACKATIME_API_KEY")
        or os.environ.get("WAKATIME_API_KEY")
        or read_wakatime_key()
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    console = Console()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        console.print(
            Panel(
                Text(str(exc), style="bold red"),
                title="[red]hackfetch config error[/red]",
                border_style="red",
            )
        )
        return 1

    source = "hackatime api"

    if args.dev:
        ensure_dev_file(DATA=DATA)
        data_path = data_file_path()
        try:
            today, week = _load_dev_data(data_path)
        except (OSError, ValueError) as exc:
            console.print(
                Panel(
                    Text(str(exc), style="bold red"),
                    title="[red]dev data error[/red]",
                    border_style="red",
                )
            )
            return 1
        source = "dev data (data.json)"
    else:
        api_key = resolve_api_key(args.api_key)
        if not api_key:
            console.print(
                Panel(
                    Text.assemble(
                        ("No Hackatime API key found.\n\n", "bold red"),
                        ("Set ", "dim"),
                        ("HACKATIME_API_KEY", f"bold {PINK}"),
                        (", or pass ", "dim"),
                        ("--api-key", f"bold {PINK}"),
                        (" for real data, or use ", "dim"),
                        ("--dev", f"bold {PINK}"),
                        (" for fake data.", "dim"),
                    ),
                    title="[red]hackfetch[/red]",
                    border_style="red",
                )
            )
            return 2

        client = HackatimeClient(api_key, user=args.user, timeout=args.timeout)

        try:
            with console.status(
                "[bold #c084fc]contacting hackatime...", spinner="dots"
            ):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    today_future = pool.submit(client.statusbar_today)
                    week_future = pool.submit(client.stats_last_7_days)
                    today = today_future.result()
                    week = week_future.result()
        except HackatimeError as exc:
            console.print(
                Panel(
                    Text(str(exc), style="bold red"),
                    title="[red]hackatime request failed[/red]",
                    border_style="red",
                )
            )
            return 1

    render_dashboard(console, today, week, user=args.user, source=source, config=config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
