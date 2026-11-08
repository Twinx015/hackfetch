# hackfetch

A fastfetch-inspired terminal dashboard for your [Hackatime](https://hackatime.hackclub.com) stats.

It fetches your status-bar total for today and your last 7 days of coding stats, then renders them with [Rich](https://github.com/Textualize/rich).

## Usage

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
[logo]
show = true
style = "block"       # block | bloody | custom
color = "#ff786b"     # single hex color only
file = "logo.txt"     # used by style = "custom"

[display]
show_values = true    # false shows only the logo
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
]
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
