"""Rich rendering for the hackfetch dashboard."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.align import Align
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from .config import BAR_STYLES, DEFAULT_BAR_STYLE, Config, load_config

VIOLET = "#a78bfa"
BLUE = "#60a5fa"
CYAN = "#22d3ee"
GREEN = "#4ade80"
PINK = "#ff5fec"

MIN_SIDE_BY_SIDE_WIDTH = 78

_LOGO_TOP = [
    "██╗  ██╗ █████╗  ██████╗██╗  ██╗",
    "██║  ██║██╔══██╗██╔════╝██║ ██╔╝",
    "███████║███████║██║     █████╔╝ ",
    "██╔══██║██╔══██║██║     ██╔═██╗ ",
    "██║  ██║██║  ██║╚██████╗██║  ██╗",
    "╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝",
]

_LOGO_BOTTOM = [
    "██████╗██████╗████████╗ ██████╗██╗  ██╗",
    "██╔═══╝██╔═══╝╚══██╔══╝██╔════╝██║  ██║",
    "████╗  ████╗     ██║   ██║     ███████║",
    "██╔═╝  ██╔═╝     ██║   ██║     ██╔══██║",
    "██║    ██████╗   ██║   ╚██████╗██║  ██║",
    "╚═╝    ╚═════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝",
]

_LOGO_BLOCK = _LOGO_TOP + _LOGO_BOTTOM
_LOGO_BLOODY = (
    _LOGO_TOP
    + ["  ╲       ╲        ╲       ╲"]
    + _LOGO_BOTTOM
    + ["   ╲        ╲       ╲      ╲"]
)


def render_dashboard(
    console: Console,
    today: dict[str, Any],
    week: dict[str, Any],
    user: str = "current",
    source: str = "hackatime api",
    config: Config | None = None,
) -> None:
    """Print the dashboard: logo on the left, stats on the right.

    Falls back to a stacked layout on narrow terminals. Loads the default
    config when none is given. Sections hidden by the config are skipped,
    and a footer shows the data source and update time.
    """
    if config is None:
        config = load_config()

    username = str(week.get("username") or user)

    left = None
    if config.logo.show:
        user_lines = [
            Text.assemble(
                ("  user: ", config.logo.color),
                (username, f"bold {config.colors.value}"),
            )
        ]
        user_id = _text(week.get("user_id"))
        if config.field_enabled("user_id") and user_id:
            user_lines.append(
                Text.assemble(
                    ("  id:   ", config.logo.color),
                    (user_id, f"bold {config.colors.value}"),
                )
            )
        left = Group(_logo(config), Text(), *user_lines)

    right = _stats_panel(today, week, config) if config.show_values else None

    console.print()

    if left is not None and right is not None:
        if console.width < MIN_SIDE_BY_SIDE_WIDTH:
            console.print(left)
            console.print()
            console.print(right)
        else:
            layout = Table.grid(padding=(0, 4))
            layout.add_column(vertical="top")
            layout.add_column(vertical="top")
            layout.add_row(left, right)
            console.print(layout)
    elif left is not None:
        console.print(left)
    elif right is not None:
        console.print(right)

    console.print()
    footer = Text.assemble(
        (source, config.colors.muted),
        ("  ·  ", config.colors.muted),
        (f"updated {datetime.now():%H:%M}", config.colors.muted),
    )
    console.print(Align.right(footer))


def _stats_panel(
    today: dict[str, Any], week: dict[str, Any], config: Config
) -> Group | None:
    """Build the right-hand stats column, or None if nothing is enabled."""
    sections: list[Group] = []

    if config.field_enabled("today"):
        today_block = _today_block(today, config)
        if today_block is not None:
            sections.append(Group(_section("today", config), today_block))

    sections.extend(_ranking_sections(today, _TODAY_RANKINGS, config))

    if config.field_enabled("week"):
        week_block = _week_block(week, config)
        if week_block.row_count:
            sections.append(Group(_section("last 7 days", config), week_block))

    sections.extend(_ranking_sections(week, _WEEK_RANKINGS, config))

    if not sections:
        return None

    parts: list[Any] = []
    for index, section in enumerate(sections):
        if index:
            parts.append(Text())
        parts.append(section)
    return Group(*parts)


def _ranking_sections(
    data: dict[str, Any],
    specs: tuple[tuple[str, str, str, int], ...],
    config: Config,
) -> list[Group]:
    """Build one ranked section per enabled spec that has data."""
    sections: list[Group] = []
    for field, title, key, limit in specs:
        items = data.get(key)
        if not config.field_enabled(field) or not isinstance(items, list):
            continue
        block = _ranking_block(items, config, limit)
        if block.row_count:
            sections.append(Group(_section(title, config), block))
    return sections


def _logo(config: Config) -> Text:
    """Return the logo as colored text for the configured style."""
    if config.logo.style == "custom":
        lines = config.logo.file.read_text(encoding="utf-8").rstrip("\n").splitlines()
    elif config.logo.style == "bloody":
        lines = _LOGO_BLOODY
    else:
        lines = _LOGO_BLOCK

    text = Text()
    for index, line in enumerate(lines):
        text.append(line, style=f"bold {config.logo.color}")
        if index < len(lines) - 1:
            text.append("\n")
    return text


def _section(title: str, config: Config) -> Text:
    """Return an uppercase section heading in the header color."""
    text = Text()
    text.append("[ ", style=f"bold {config.colors.header}")
    text.append(title.upper(), style=f"bold {config.colors.header}")
    text.append(" ]", style=f"bold {config.colors.header}")
    return text


def _grid(config: Config) -> Table:
    """Return an empty two-column key/value grid."""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style=config.colors.key, no_wrap=True)
    grid.add_column(no_wrap=True)
    return grid


def _add_rows(
    grid: Table,
    config: Config,
    rows: list[tuple[str, str, str | None]] | tuple[tuple[str, str, str | None], ...],
) -> None:
    """Add (field, label, text) rows when the field is on and the text exists."""
    for field, label, text in rows:
        if not config.field_enabled(field) or text is None:
            continue
        grid.add_row(label, Text(text, style=f"bold {config.colors.value}"))


def _today_block(today: dict[str, Any], config: Config) -> Group | None:
    """Build today's total, goal bar and range details, or None if all hidden."""
    grand_total = today.get("grand_total") or {}
    seconds = grand_total.get("total_seconds") or 0
    goal = today.get("goal") or {}

    parts: list[Any] = []

    if config.field_enabled("today_total"):
        parts.append(Text(_duration(seconds), style=f"bold {config.colors.header}"))

    target = _number(goal.get("target_seconds"))
    if config.field_enabled("goal") and target > 0:
        tracked = _number(goal.get("tracked_seconds")) or _number(seconds)
        percent = goal.get("completion_percent")
        percent = _number(percent) if percent is not None else tracked / target * 100
        complete = bool(goal.get("complete")) or percent >= 100

        line = Text(no_wrap=True)
        line.append_text(
            _bar(
                percent,
                18,
                GREEN if complete else config.colors.bar,
                config,
            )
        )
        line.append(
            f"  {percent:.0f}%",
            style=f"bold {GREEN if complete else config.colors.header}",
        )
        line.append(f" of {_goal_duration(target)} goal", style=config.colors.key)
        if complete:
            line.append("  ✓", style=f"bold {GREEN}")
        parts.append(line)

    details = _today_details(today, config)
    if details.row_count:
        parts.append(details)

    if not parts:
        return None
    return Group(*parts)


def _today_details(today: dict[str, Any], config: Config) -> Table:
    """Build the grid of today's range, timezone and window."""
    window = today.get("range")
    window = window if isinstance(window, dict) else {}
    start = _stamp(window.get("start"))
    end = _stamp(window.get("end"))

    grid = _grid(config)
    _add_rows(
        grid,
        config,
        (
            (
                "today_range",
                "range",
                _text(window.get("text")) or _day(window.get("date")),
            ),
            ("today_timezone", "timezone", _text(window.get("timezone"))),
            ("today_window", "window", f"{start} → {end}" if start and end else None),
        ),
    )
    return grid


def _week_block(week: dict[str, Any], config: Config) -> Table:
    """Build the seven-day summary grid of enabled fields."""
    grid = _grid(config)

    if config.field_enabled("week_total"):
        grid.add_row(
            "total",
            Text(
                _duration(week.get("total_seconds")),
                style=f"bold {config.colors.header}",
            ),
        )
    if config.field_enabled("daily_average"):
        grid.add_row(
            "daily avg",
            Text(
                _duration(week.get("daily_average")),
                style=f"bold {config.colors.header}",
            ),
        )

    _add_rows(
        grid,
        config,
        [("week_period", "period", _period(week.get("start"), week.get("end")))],
    )
    _add_rows(
        grid,
        config,
        [(field, label, fmt(week.get(key))) for field, label, key, fmt in _WEEK_ROWS],
    )

    for field, label, key, show_percent in _TOP_ITEMS:
        if not config.field_enabled(field):
            continue
        item = _top_item(week.get(key))
        if item is None:
            continue
        value = Text(
            str(item.get("name") or "unknown"), style=f"bold {config.colors.value}"
        )
        if show_percent and item.get("percent") is not None:
            value.append(
                f"  {_number(item['percent']):.0f}%",
                style=f"bold {config.colors.header}",
            )
        grid.add_row(label, value)

    return grid


def _ranking_block(items: list[dict[str, Any]], config: Config, limit: int) -> Table:
    """Build a name, time, percent and bar table of the top entries by time."""
    show_time = config.field_enabled("ranking_time")

    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, min_width=10, max_width=32, overflow="ellipsis")
    if show_time:
        grid.add_column(justify="right", no_wrap=True, min_width=6)
    grid.add_column(justify="right", no_wrap=True, min_width=5)
    grid.add_column(no_wrap=True)

    entries = [item for item in items if isinstance(item, dict)]
    total = sum(_seconds(item) for item in entries)

    for item in sorted(entries, key=_seconds, reverse=True)[:limit]:
        percent = _percent_of(item, total)
        cells: list[Any] = [
            Text(
                str(item.get("name") or "unknown"), style=f"bold {config.colors.value}"
            )
        ]
        if show_time:
            cells.append(Text(_duration(_seconds(item)), style=config.colors.key))
        cells.append(Text(f"{percent:.0f}%", style=config.colors.key))
        cells.append(_bar(percent, 14, config.colors.bar, config))
        grid.add_row(*cells)
    return grid


def _percent_of(item: dict[str, Any], total: float) -> float:
    """Return an entry's percent, computing it from seconds when missing."""
    if item.get("percent") is not None:
        return _number(item.get("percent"))
    if total > 0:
        return _seconds(item) / total * 100
    return 0.0


def _top_item(items: Any) -> dict[str, Any] | None:
    """Return the entry with the most seconds, or None if there is none."""
    if not isinstance(items, list):
        return None
    candidates = [item for item in items if isinstance(item, dict)]
    return max(candidates, key=_seconds, default=None)


def _seconds(item: dict[str, Any]) -> float:
    """Return an entry's total_seconds as a float, treating bad values as 0."""
    return _number(item.get("total_seconds"))


def _number(value: Any) -> float:
    """Convert value to float, returning 0.0 when it is missing or invalid."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _bar(percent: float, width: int, color: str, config: Config) -> Text:
    """Return a progress bar in the configured style, clamped to 0-100%."""
    full, empty = BAR_STYLES.get(config.bar_style, BAR_STYLES[DEFAULT_BAR_STYLE])
    percent = max(0.0, min(100.0, _number(percent)))
    filled = round(width * percent / 100)
    bar = Text()
    bar.append(full * filled, style=color)
    bar.append(empty * (width - filled), style=config.colors.muted)
    return bar


def _duration(seconds: Any) -> str:
    """Format seconds as '2h 5m', '5m' or '30s'."""
    total = max(int(_number(seconds)), 0)
    hours, remainder = divmod(total, 3600)
    minutes = remainder // 60

    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{total}s"


def _goal_duration(seconds: Any) -> str:
    """Format a goal length, using whole hours like '2h' when exact."""
    total = int(_number(seconds))
    if total > 0 and total % 3600 == 0:
        return f"{total // 3600}h"
    return _duration(total)


def _text(value: Any) -> str | None:
    """Return value as stripped text, or None for missing, empty or nested data."""
    if value is None or isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    return text or None


def _flag(value: Any) -> str | None:
    """Format a real boolean as 'yes' or 'no', or None for anything else."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    return None


def _count(value: Any) -> str | None:
    """Format a number without a trailing '.0', or None if it is not numeric."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return str(int(number)) if number.is_integer() else f"{number:.1f}"


def _percent_text(value: Any) -> str | None:
    """Format a number as a percentage, or None if it is not numeric."""
    number = _count(value)
    return f"{number}%" if number is not None else None


def _clock(value: Any) -> str | None:
    """Format seconds as a duration, or None when the value is missing."""
    if value is None or isinstance(value, bool):
        return None
    return _duration(value)


def _parse_time(value: Any) -> datetime | None:
    """Parse an ISO date or datetime string, or return None."""
    text = _text(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _stamp(value: Any) -> str | None:
    """Format an ISO timestamp as 'Nov 08 14:30', falling back to raw text."""
    parsed = _parse_time(value)
    return f"{parsed:%b %d %H:%M}" if parsed else _text(value)


def _day(value: Any) -> str | None:
    """Format an ISO date as 'Sun Nov 08', falling back to raw text."""
    parsed = _parse_time(value)
    return f"{parsed:%a %b %d}" if parsed else _text(value)


def _period(start: Any, end: Any) -> str | None:
    """Format two ISO dates as 'Sun Nov 01 → Sat Nov 07'."""
    first, last = _day(start), _day(end)
    return f"{first} → {last}" if first and last else None


def _best_day(value: Any) -> str | None:
    """Format the best_day object as its date and tracked time."""
    if not isinstance(value, dict):
        return None
    spent = _text(value.get("text"))
    if spent is None and value.get("total_seconds") is not None:
        spent = _duration(value.get("total_seconds"))
    parts = [part for part in (_day(value.get("date")), spent) if part]
    return "  ".join(parts) or None


_WEEK_ROWS: tuple[tuple[str, str, str, Callable[[Any], str | None]], ...] = (
    ("week_range", "range", "human_readable_range", _text),
    ("best_day", "best day", "best_day", _best_day),
    ("days", "days", "days_including_holidays", _count),
    ("workdays", "workdays", "days_minus_holidays", _count),
    ("holidays", "holidays", "holidays", _count),
    (
        "total_with_other",
        "total + other",
        "total_seconds_including_other_language",
        _clock,
    ),
    (
        "daily_avg_with_other",
        "avg + other",
        "daily_average_including_other_language",
        _clock,
    ),
    ("timezone", "timezone", "timezone", _text),
    ("status", "status", "status", _text),
    ("up_to_date", "up to date", "is_up_to_date", _flag),
    ("percent_calculated", "calculated", "percent_calculated", _percent_text),
    ("writes_only", "writes only", "writes_only", _flag),
    ("timeout", "timeout", "timeout", _count),
    ("coding_visible", "coding public", "is_coding_activity_visible", _flag),
    ("other_visible", "other public", "is_other_usage_visible", _flag),
    ("created_at", "created", "created_at", _stamp),
    ("modified_at", "modified", "modified_at", _stamp),
)

_TOP_ITEMS = (
    ("language", "language", "languages", True),
    ("project", "project", "projects", True),
    ("editor", "editor", "editors", False),
    ("machine", "machine", "machines", False),
    ("os", "os", "operating_systems", False),
    ("category", "category", "categories", True),
    ("dependency", "dependency", "dependencies", False),
    ("branch", "branch", "branches", False),
    ("entity", "file", "entities", False),
)

_TODAY_RANKINGS = (
    ("today_categories", "today categories", "categories", 4),
    ("today_languages", "today languages", "languages", 4),
    ("today_projects", "today projects", "projects", 3),
    ("today_editors", "today editors", "editors", 3),
    ("today_machines", "today machines", "machines", 3),
    ("today_os", "today operating systems", "operating_systems", 3),
    ("today_dependencies", "today dependencies", "dependencies", 5),
)

_WEEK_RANKINGS = (
    ("top_languages", "top languages", "languages", 4),
    ("top_projects", "top projects", "projects", 3),
    ("top_editors", "top editors", "editors", 3),
    ("top_machines", "top machines", "machines", 3),
    ("top_os", "top operating systems", "operating_systems", 3),
    ("top_categories", "top categories", "categories", 4),
    ("top_dependencies", "top dependencies", "dependencies", 5),
    ("top_branches", "top branches", "branches", 3),
    ("top_entities", "top files", "entities", 3),
)
