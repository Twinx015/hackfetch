from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_NAME = "hackfetch"
DEFAULT_LOGO_COLOR = "#ff786b"
DEFAULT_LOGO_FILE = "logo.txt"

LOGO_STYLES = ("block", "bloody", "custom")

DEFAULT_FIELDS = (
    "today",
    "today_total",
    "goal",
    "week",
    "week_total",
    "daily_average",
    "language",
    "project",
    "editor",
    "machine",
    "os",
    "top_languages",
    "top_projects",
)

FIELDS = DEFAULT_FIELDS + (
    "user_id",
    "ranking_time",
    "today_range",
    "today_timezone",
    "today_window",
    "today_categories",
    "today_languages",
    "today_projects",
    "today_editors",
    "today_machines",
    "today_os",
    "today_dependencies",
    "week_range",
    "week_period",
    "best_day",
    "days",
    "workdays",
    "holidays",
    "total_with_other",
    "daily_avg_with_other",
    "timezone",
    "status",
    "up_to_date",
    "percent_calculated",
    "writes_only",
    "timeout",
    "coding_visible",
    "other_visible",
    "created_at",
    "modified_at",
    "category",
    "dependency",
    "branch",
    "entity",
    "top_editors",
    "top_machines",
    "top_os",
    "top_categories",
    "top_dependencies",
    "top_branches",
    "top_entities",
)

DEFAULT_BAR_STYLE = "block"
BAR_STYLES = {
    "block": ("█", "░"),
    "shade": ("▓", "░"),
    "line": ("━", "─"),
    "dots": ("●", "○"),
    "square": ("■", "□"),
    "ascii": ("#", "-"),
}

DEFAULT_COLORS = {
    "header": "#ff786b",
    "bar": "#ffa575",
    "key": "#a1a1aa",
    "value": "#ffffff",
    "muted": "#52525b",
}

COLOR_ALIASES = {
    "header": ("primary",),
    "bar": ("secondary",),
    "key": ("feild_key", "field_key"),
    "value": ("feild_value", "field_value"),
    "muted": (),
}

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

_FIELDS_TOML = "\n".join(
    f'  "{name}",' if name in DEFAULT_FIELDS else f'  # "{name}",' for name in FIELDS
)

DEFAULT_CONFIG = f"""\
[logo] # config for logo
show = true
style = "block" # block bloody or custom
color = "{DEFAULT_LOGO_COLOR}"
file = "{DEFAULT_LOGO_FILE}" # read only when style is custom

[display]
show_values = true # for showing values and keys , disable for only logo
bar_style = "{DEFAULT_BAR_STYLE}" # block , shade , line , dots , square , ascii
fields = [ # Uncomment a field to show it.
{_FIELDS_TOML}
]

[colors]
header = "{DEFAULT_COLORS["header"]}" # for header eg: Today , Top Launguage
bar = "{DEFAULT_COLORS["bar"]}" # for bar
key = "{DEFAULT_COLORS["key"]}" # for key eg: total , daily avg
value = "{DEFAULT_COLORS["value"]}" # for value  eg: 18h 15m , 2h 20m
muted = "{DEFAULT_COLORS["muted"]}"
"""


class ConfigError(ValueError):
    """Raised when the configuration file is missing, unreadable or invalid."""


@dataclass(frozen=True, slots=True)
class LogoConfig:
    """Logo settings: visibility, style name, color and custom logo path."""

    show: bool
    style: str
    color: str
    file: Path


@dataclass(frozen=True, slots=True)
class ColorsConfig:
    """Resolved hex colors used by the dashboard renderer.

    ``primary`` and ``secondary`` remain as read-only aliases of ``header``
    and ``bar`` for older callers.
    """

    header: str
    bar: str
    key: str
    value: str
    muted: str

    @property
    def primary(self) -> str:
        """Alias for ``header``."""
        return self.header

    @property
    def secondary(self) -> str:
        """Alias for ``bar``."""
        return self.bar


@dataclass(frozen=True, slots=True)
class Config:
    """Fully validated hackfetch configuration."""

    path: Path
    logo: LogoConfig
    colors: ColorsConfig
    show_values: bool
    fields: frozenset[str]
    bar_style: str = DEFAULT_BAR_STYLE

    def field_enabled(self, name: str) -> bool:
        """Return True if the named display field is enabled."""
        return name in self.fields


def config_directory() -> Path:
    """Return the hackfetch config directory, honouring XDG_CONFIG_HOME."""
    base = os.environ.get("XDG_CONFIG_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".config"
    return root / APP_NAME


def default_config_path() -> Path:
    """Return the default path of config.toml."""
    return config_directory() / "config.toml"


def ensure_config(path: Path | str | None = None) -> Path:
    """Return the config path, creating it with defaults if it is missing."""
    config_path = Path(path).expanduser() if path else default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return config_path


def data_file_path() -> Path:
    """Return the path of data.json inside the hackfetch config directory."""
    return config_directory() / "data.json"


def ensure_dev_file(DATA):
    path = data_file_path()
    if path.exists():
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(json.loads(DATA), handle, indent=2)
    return False


def load_config(path: Path | str | None = None) -> Config:
    """Load, validate and return the configuration.

    Creates the file with defaults when absent. Missing keys fall back to
    defaults; empty color strings use the default color. Raises
    ``ConfigError`` with a readable message on any problem.
    """
    try:
        config_path = ensure_config(path)
    except OSError as exc:
        raise ConfigError(
            f"Could not create or access config directory: {exc}"
        ) from exc

    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Could not parse {config_path}: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read {config_path}: {exc}") from exc

    logo_data = _table(data.get("logo"), "logo", config_path)
    display_data = _table(data.get("display"), "display", config_path)
    colors_data = _table(data.get("colors"), "colors", config_path)

    return Config(
        path=config_path,
        logo=_logo_config(logo_data, config_path),
        colors=_colors_config(colors_data, config_path),
        show_values=_boolean(
            display_data.get("show_values", True), "display.show_values", config_path
        ),
        fields=_fields(display_data.get("fields", list(DEFAULT_FIELDS)), config_path),
        bar_style=_bar_style(
            display_data.get("bar_style", DEFAULT_BAR_STYLE), config_path
        ),
    )


def _logo_config(data: dict[str, Any], config_path: Path) -> LogoConfig:
    """Validate the [logo] table and build a LogoConfig."""
    show = _boolean(data.get("show", True), "logo.show", config_path)

    style = data.get("style", "block")
    if not isinstance(style, str):
        raise ConfigError(f"{config_path}: logo.style must be a string.")
    style = style.strip().lower()
    if style not in LOGO_STYLES:
        allowed = ", ".join(LOGO_STYLES)
        raise ConfigError(f"{config_path}: logo.style must be one of: {allowed}.")

    color = _hex_color(
        data.get("color", DEFAULT_LOGO_COLOR),
        "logo.color",
        config_path,
        DEFAULT_LOGO_COLOR,
    )

    file_value = data.get("file", DEFAULT_LOGO_FILE)
    if not isinstance(file_value, str) or not file_value.strip():
        raise ConfigError(f"{config_path}: logo.file must be a non-empty string.")
    logo_file = Path(file_value.strip()).expanduser()
    if not logo_file.is_absolute():
        logo_file = config_path.parent / logo_file

    if show and style == "custom":
        _check_custom_logo(logo_file, config_path)

    return LogoConfig(show=show, style=style, color=color, file=logo_file)


def _check_custom_logo(logo_file: Path, config_path: Path) -> None:
    """Ensure the custom logo file exists, is readable and is not empty."""
    if not logo_file.is_file():
        raise ConfigError(
            f"Custom logo not found: {logo_file}\n"
            f"Create it, or change logo.style in {config_path}."
        )
    try:
        content = logo_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"Could not read custom logo {logo_file}: {exc}") from exc
    if not content.strip():
        raise ConfigError(f"Custom logo is empty: {logo_file}")


def _colors_config(data: dict[str, Any], config_path: Path) -> ColorsConfig:
    """Resolve every color, accepting legacy and misspelled key names."""
    return ColorsConfig(
        **{name: _color(data, name, config_path) for name in DEFAULT_COLORS}
    )


def _color(data: dict[str, Any], name: str, config_path: Path) -> str:
    """Read one color by name or alias, falling back to its default."""
    for key in (name, *COLOR_ALIASES[name]):
        if key in data:
            return _hex_color(
                data[key], f"colors.{key}", config_path, DEFAULT_COLORS[name]
            )
    return DEFAULT_COLORS[name]


def _bar_style(value: Any, config_path: Path) -> str:
    """Validate display.bar_style against the known bar styles."""
    if not isinstance(value, str) or value.strip().lower() not in BAR_STYLES:
        allowed = ", ".join(BAR_STYLES)
        raise ConfigError(
            f"{config_path}: display.bar_style must be one of: {allowed}."
        )
    return value.strip().lower()


def _fields(value: Any, config_path: Path) -> frozenset[str]:
    """Validate display.fields and return it as a frozenset."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{config_path}: display.fields must be a list of strings.")
    unknown = sorted(set(value) - set(FIELDS))
    if unknown:
        raise ConfigError(
            f"{config_path}: unknown display field(s): {', '.join(unknown)}."
        )
    return frozenset(value)


def _table(value: Any, name: str, path: Path) -> dict[str, Any]:
    """Return a TOML table, treating a missing one as empty."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{path}: [{name}] must be a TOML table.")
    return value


def _boolean(value: Any, name: str, path: Path) -> bool:
    """Return value if it is a real boolean, otherwise raise ConfigError."""
    if not isinstance(value, bool):
        raise ConfigError(f"{path}: {name} must be true or false.")
    return value


def _hex_color(value: Any, name: str, path: Path, default: str) -> str:
    """Validate a hex color; an empty string selects the default."""
    if not isinstance(value, str):
        raise ConfigError(f"{path}: {name} must be a hex string.")
    value = value.strip()
    if not value:
        return default
    if not _HEX_COLOR.fullmatch(value):
        raise ConfigError(f'{path}: {name} must be a hex color like "#ff786b".')
    return value
