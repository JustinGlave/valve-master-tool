"""inventory.py — Parts List / Inventory data layer.

Loads and saves the ATS parts catalog from a JSON file living on the
Phoenix SharePoint site (synced locally via OneDrive Business). Schema:

    {
        "version":    1,
        "updated_at": "2026-05-08T14:30:00",
        "updated_by": "<windows-username>",
        "parts": [
            {
                "ats_id":      "PHX-1402",
                "manuf_part":  "PRT-800-210-192",
                "description": "PHX - Analog Scaling Module",
                "low_limit":   null
            },
            ...
        ]
    }

The dialog code stays UI-only and routes all reads/writes through the
``load_inventory`` / ``save_inventory`` functions here.
"""
from __future__ import annotations

import datetime
import getpass
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field

# SharePoint folder synced via OneDrive Business.
# Path resolves to <USERPROFILE>\ATS\Phoenix - Documents\Valve Master Tool\inventory.json
# which is identical for every ATS Inc. user with the SharePoint site synced.
_INVENTORY_REL_PATH = os.path.join(
    "ATS", "Phoenix - Documents", "Valve Master Tool", "inventory.json"
)


def inventory_json_path() -> str:
    """Absolute path to the SharePoint-synced inventory.json for this user."""
    return os.path.join(os.path.expanduser("~"), _INVENTORY_REL_PATH)


# SHA-256 of the admin password ("Alerton1986@"). Hash so the literal isn't
# trivially recoverable from a `strings` dump of the EXE — the password is
# still embedded, this is just speed-bump security as agreed for the
# first revision. Replace with proper auth later.
_ADMIN_PW_HASH = "2818b591fcbb93a54c5d3556771a449fd44d5cf77d064b0afcb19763457c975c"


def is_admin_password(password: str) -> bool:
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest() == _ADMIN_PW_HASH


@dataclass
class Part:
    ats_id: str = ""
    manuf_part: str = ""
    description: str = ""
    low_limit: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Part":
        low = data.get("low_limit")
        if isinstance(low, str) and low.strip():
            try:
                low = int(low)
            except ValueError:
                low = None
        elif isinstance(low, float):
            low = int(low)
        elif not isinstance(low, int):
            low = None
        return cls(
            ats_id=str(data.get("ats_id", "")).strip(),
            manuf_part=str(data.get("manuf_part", "")).strip(),
            description=str(data.get("description", "")).strip(),
            low_limit=low,
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Inventory:
    parts: list[Part] = field(default_factory=list)
    version: int = 1
    updated_at: str = ""
    updated_by: str = ""

    @classmethod
    def empty(cls) -> "Inventory":
        return cls()


def cache_path() -> str:
    """Local fallback path used when the SharePoint copy is unavailable.

    Lives in ``%APPDATA%\\ATS Inc\\PhoenixMasterTool\\inventory_cache.json`` so
    each user's machine keeps the last-known-good copy of the inventory.
    """
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "ATS Inc", "PhoenixMasterTool", "inventory_cache.json")


def _save_cache(payload: dict) -> None:
    """Best-effort cache write. Never raises — caching is a fallback only."""
    path = cache_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass


def _build_inventory(data: dict) -> Inventory:
    parts_raw = data.get("parts", []) if isinstance(data, dict) else []
    parts = [Part.from_dict(p) for p in parts_raw if isinstance(p, dict)]
    return Inventory(
        parts=parts,
        version=int(data.get("version", 1)) if isinstance(data, dict) else 1,
        updated_at=str(data.get("updated_at", "")) if isinstance(data, dict) else "",
        updated_by=str(data.get("updated_by", "")) if isinstance(data, dict) else "",
    )


def load_inventory() -> tuple[Inventory, str | None, str]:
    """Read the inventory JSON, falling back to the local cache when needed.

    Returns ``(inventory, banner_message, status)``.

    ``status`` is one of:
        - ``"ok"``      — fresh read from the SharePoint sync. ``banner_message`` is None.
        - ``"warning"`` — SharePoint copy unavailable; loaded from local cache.
                          Banner explains and includes the cache's last-synced timestamp.
        - ``"error"``   — neither SharePoint nor cache could be read; ``inventory`` is empty.
    """
    primary = inventory_json_path()
    primary_data: dict | None = None
    primary_err: str | None = None

    if os.path.exists(primary):
        try:
            with open(primary, "r", encoding="utf-8") as fh:
                primary_data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            primary_err = str(exc)
    else:
        primary_err = "inventory.json was not found on the SharePoint sync"

    # Fresh load — refresh the cache and return clean.
    if primary_data is not None:
        _save_cache(primary_data)
        return _build_inventory(primary_data), None, "ok"

    # Primary failed — try the cache.
    cpath = cache_path()
    if os.path.exists(cpath):
        try:
            with open(cpath, "r", encoding="utf-8") as fh:
                cached_data = json.load(fh)
            cached_at = datetime.datetime.fromtimestamp(
                os.path.getmtime(cpath)
            ).strftime("%Y-%m-%d %H:%M")
            banner = (
                f"Working from local cache last synced {cached_at}. "
                f"The Phoenix SharePoint copy is unavailable ({primary_err}). "
                "Edits cannot be saved while offline."
            )
            return _build_inventory(cached_data), banner, "warning"
        except (OSError, json.JSONDecodeError) as exc:
            # Cache is also dead — fall through to the no-data path.
            primary_err = f"{primary_err} (cache also unreadable: {exc})"

    return Inventory.empty(), (
        "Could not load inventory.json from SharePoint or local cache.\n\n"
        f"Source: {primary}\n"
        f"Cache:  {cpath}\n"
        f"Error:  {primary_err}"
    ), "error"


def save_inventory(parts: list[Part]) -> tuple[bool, str]:
    """Atomically write the inventory back to SharePoint.

    Returns (ok, message). Writes to a temp file in the same directory and
    then renames over the target so a partial write can't corrupt the JSON
    during a network hiccup.
    """
    path = inventory_json_path()
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        return False, (
            "SharePoint folder not found:\n" + folder + "\n\n"
            "Make sure the Phoenix SharePoint site is synced via OneDrive."
        )

    payload = {
        "version": 1,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "updated_by": getpass.getuser(),
        "parts": [p.to_dict() for p in parts],
    }

    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False, f"Could not save inventory.json: {exc}"

    return True, f"Saved {len(parts)} parts to inventory.json."
