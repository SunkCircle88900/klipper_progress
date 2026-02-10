# InkyPi-KlipperProgress

An [InkyPi](https://github.com/fatihak/InkyPi) plugin that displays live 3D print progress from a [Klipper](https://www.klipper3d.org/) printer running [Moonraker](https://github.com/Arksine/moonraker) on your e-ink display.

## What it shows

| Field | Source |
|---|---|
| Print state (Printing / Paused / Complete / Standby / Error) | `print_stats.state` |
| Current filename | `print_stats.filename` |
| Progress bar + percentage | `virtual_sdcard.progress` |
| Nozzle temperature (actual / target) | `extruder.temperature` / `extruder.target` |
| Bed temperature (actual / target) | `heater_bed.temperature` / `heater_bed.target` |
| Elapsed time | `print_stats.print_duration` |
| Estimated remaining time | Derived from progress + elapsed |
| Layer / message info | `display_status.message` (e.g. from SET_DISPLAY_TEXT) |

## Prerequisites

- InkyPi installed and running
- A Klipper printer with **Moonraker** accessible on your local network
- InkyPi must be able to reach the Moonraker HTTP API (default port **7125**)

## Installation

### Option A — Manual install

```bash
# SSH into your InkyPi Raspberry Pi
cd ~/InkyPi/src/plugins
git clone https://github.com/YOUR_USERNAME/InkyPi-KlipperProgress klipper_progress
sudo systemctl restart inkypi.service
```

### Option B — Copy files

Copy the `klipper_progress/` directory into `src/plugins/` on your InkyPi device:

```
src/plugins/
└── klipper_progress/
    ├── klipper_progress.py
    ├── klipper_progress.html
    ├── settings.html
    └── plugin.json
```

Then restart the InkyPi service:

```bash
sudo systemctl restart inkypi.service
```

## Configuration

1. Open the InkyPi web UI in your browser.
2. Select **Klipper Print Progress** from the plugin list.
3. Enter your **Moonraker URL** (e.g. `http://192.168.1.100:7125`).
4. Save — the display will update on the next refresh cycle.

> **Tip:** Set the InkyPi refresh interval to something short (e.g. 1–5 minutes) while a print is in progress so the display stays current.

## Klipper SET_DISPLAY_TEXT support

If you add `SET_DISPLAY_TEXT MSG="Layer {layer_num}/{total_layer_count}"` to your slicer's layer-change G-code, that message will appear in the footer of the display via `display_status.message`.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot reach Moonraker" | Check the IP/port. Try `curl http://<ip>:7125/printer/info` from the Pi. |
| Temperatures show 0 | The printer may be in standby with heaters off — this is normal. |
| Progress stuck at 0% | Ensure a print is actually running and `virtual_sdcard` is active. |

## License

MIT
