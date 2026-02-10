import logging
import requests
from plugins.base_plugin.base_plugin import BasePlugin
from utils.app_utils import resolve_path

logger = logging.getLogger(__name__)


class KlipperProgress(BasePlugin):
    """InkyPi plugin that displays Klipper/Moonraker 3D print progress on an e-ink display."""

    def generate_image(self, settings, device_config):
        moonraker_url = settings.get("moonraker_url", "").strip().rstrip("/")
        if not moonraker_url:
            raise RuntimeError(
                "Moonraker URL is not configured. "
                "Please enter your Moonraker address (e.g. http://192.168.1.100:7125)."
            )

        # ------------------------------------------------------------------ #
        #  Fetch printer state from Moonraker                                 #
        # ------------------------------------------------------------------ #
        objects = "print_stats&virtual_sdcard&extruder&heater_bed&display_status&toolhead"
        query_url = f"{moonraker_url}/printer/objects/query?{objects}"

        try:
            resp = requests.get(query_url, timeout=5)
            resp.raise_for_status()
            data = resp.json()["result"]["status"]
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot reach Moonraker at {moonraker_url}. "
                "Check the URL and that Moonraker is running."
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Timed out connecting to Moonraker at {moonraker_url}."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch printer data: {e}")

        # ------------------------------------------------------------------ #
        #  Parse the response                                                 #
        # ------------------------------------------------------------------ #
        print_stats   = data.get("print_stats", {})
        virtual_sdcard = data.get("virtual_sdcard", {})
        extruder      = data.get("extruder", {})
        heater_bed    = data.get("heater_bed", {})
        display_status = data.get("display_status", {})

        state        = print_stats.get("state", "standby")          # printing / complete / standby / paused / error
        filename     = print_stats.get("filename", "") or ""
        print_time   = print_stats.get("print_duration", 0)         # seconds elapsed
        total_time   = print_stats.get("total_duration", 0)
        layer_info   = display_status.get("message", "")

        # Progress: prefer virtual_sdcard (file-based), fall back to display_status
        progress_raw     = virtual_sdcard.get("progress", display_status.get("progress", 0))
        progress_pct     = round(progress_raw * 100, 1)

        # Temperatures
        nozzle_actual  = round(extruder.get("temperature", 0), 1)
        nozzle_target  = round(extruder.get("target", 0), 1)
        bed_actual     = round(heater_bed.get("temperature", 0), 1)
        bed_target     = round(heater_bed.get("target", 0), 1)

        # Elapsed / estimated remaining
        elapsed_str    = _fmt_seconds(print_time)
        remaining_str  = "—"
        eta_str        = "—"
        if progress_raw > 0.01 and print_time > 0:
            estimated_total = print_time / progress_raw
            remaining_secs  = max(0, estimated_total - print_time)
            remaining_str   = _fmt_seconds(remaining_secs)

        # Short display name for the file
        display_name = filename.split("/")[-1] if filename else "—"
        if len(display_name) > 28:
            display_name = display_name[:25] + "…"

        # State label & colour hint (CSS class)
        state_label, state_class = _state_info(state)

        # ------------------------------------------------------------------ #
        #  Render HTML → image                                                #
        # ------------------------------------------------------------------ #
        template_data = {
            "state":          state,
            "state_label":    state_label,
            "state_class":    state_class,
            "filename":       display_name,
            "progress_pct":   progress_pct,
            "nozzle_actual":  nozzle_actual,
            "nozzle_target":  nozzle_target,
            "bed_actual":     bed_actual,
            "bed_target":     bed_target,
            "elapsed":        elapsed_str,
            "remaining":      remaining_str,
            "layer_info":     layer_info,
        }

        image = self.render_image(
            settings,
            device_config,
            "klipper_progress.html",
            template_data,
        )
        return image

    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        return template_params


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _fmt_seconds(secs):
    """Convert seconds to a human-readable h:mm:ss string."""
    secs = int(secs)
    h    = secs // 3600
    m    = (secs % 3600) // 60
    s    = secs % 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


def _state_info(state):
    """Return a human-readable label and CSS class for the printer state."""
    mapping = {
        "printing":  ("Printing",   "state-printing"),
        "paused":    ("Paused",     "state-paused"),
        "complete":  ("Complete ✓", "state-complete"),
        "error":     ("Error",      "state-error"),
        "standby":   ("Standby",    "state-standby"),
        "cancelled": ("Cancelled",  "state-error"),
    }
    return mapping.get(state, (state.capitalize(), "state-standby"))
