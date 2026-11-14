# hackfetch

A fastfetch-inspired terminal dashboard for your [Hackatime](https://hackatime.hackclub.com) stats.

It fetches your status-bar total for today and your last 7 days of coding stats, then renders them with [Rich](https://github.com/Textualize/rich).

## Installation 
From pip
```bash
pip install hackfetch
```

Or from release page (linux only)
```bash
chmod +x hackfetch
./hackfetch
```

## Usage

Make a file at ~/.wakatime.cfg
```conf
[settings]
api_url = https://hackatime.hackclub.com/api/hackatime/v1
api_key=API_KEY
heartbeat_rate_limit_seconds = 30
hostname = HOSTNAME
```

OR

```bash
uv sync

export HACKATIME_API_KEY="your-api-key"
uv run hackfetch
```

Or pass the key directly:

```bash
uv run hackfetch --api-key "your-api-key"
```

The installed commands are `hackfetch` and `hkf`.

### Options

```text
-k, --api-key   Hackatime API key (or set HACKATIME_API_KEY)
-u, --user      User ID, or "current" for the key owner (default: current)
    --timeout   Request timeout in seconds (default: 20)
    --config    Config file path (default: ~/.config/hackfetch/config.toml)
    --dev       Use fake data from data.json instead of calling the API
```

### Dev mode

Test the layout without an API key:

```bash
uv run hackfetch --dev
```

This renders the fake payload in `data.json` (a `today` object and a `week`
object) and skips all network requests.

## Configuration

The first run creates `~/.config/hackfetch/config.toml` (or
`$XDG_CONFIG_HOME/hackfetch/config.toml`) automatically. A default looks like:

```toml
[logo] # config for logo
show = true
style = "block" # block bloody or custom
color = "#ff786b"
file = "logo.txt" # read only when style is custom

[display]
show_values = true # for showing values and keys , disable for only logo
bar_style = "ascii" # block , shade , line , dots , square , ascii
fields = [
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
  # "user_id",
  # "ranking_time",
  # "today_range",
  # "today_timezone",
  # "today_window",
  # "today_categories",
  # "today_languages",
  "today_projects",
  "today_editors",
  # "today_machines",
  # "today_os",
  # "today_dependencies",
  # "week_range",
  # "week_period",
  "best_day",
  # "days",
  # "workdays",
  # "holidays",
  # "total_with_other",
  # "daily_avg_with_other",
  # "timezone",
  # "status",
  # "up_to_date",
  # "percent_calculated",
  # "writes_only",
  # "timeout",
  # "coding_visible",
  # "other_visible",
  # "created_at",
  # "modified_at",
  # "category",
  # "dependency",
  # "branch",
  # "entity",
  "top_editors",
  # "top_machines",
  # "top_os",
  # "top_categories",
  # "top_dependencies",
  # "top_branches",
  # "top_entities",
]

[colors]
header = "#ff786b" # for header eg: Today , Top Launguage
bar = "#ffa575" # for bar
key = "#a1a1aa" # for key eg: total , daily avg
value = "#ffffff" # for value  eg: 18h 15m , 2h 20m
muted = "#52525b"
```

- **Logo color** must be a single hex value such as `#ff786b` or `#f7b`.
- **Logo styles**
  - `block` — default block lettering
  - `bloody` — block lettering with drips
  - `custom` — reads `~/.config/hackfetch/logo.txt` (or the configured `logo.file`)
- **Show/hide**
  - `display.show_values = false` hides the whole stats panel
  - remove any entry from `display.fields` to hide that field
  - `logo.show = false` hides the logo

Use a different config file with:

```bash
uv run hackfetch --dev --config ./my-config.toml
```

## API

The client uses `https://hackatime.hackclub.com/api/hackatime/v1` and these endpoints:

- `GET /users/{id}/statusbar/today`
- `GET /users/{id}/stats/last_7_days`

The key is sent both as a Bearer token and as the `api_key` query parameter.
