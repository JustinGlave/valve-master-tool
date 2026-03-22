# updater.py
# GitHub Releases auto-updater for ValveMasterTool
# Checks for a newer version on startup (background thread).
# Downloads and installs via a batch script — proven working approach.

import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
import json

try:
    from version import __version__
except ImportError:
    __version__ = "0.0.0"

GITHUB_OWNER = "JustinGlave"
GITHUB_REPO  = "valve-master-tool"
EXE_NAME     = "ValveMasterTool.exe"

API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
ALL_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{GITHUB_REPO}-updater",
}


def _parse_version(tag: str) -> tuple[int, ...]:
    """Strip leading 'v'/'V' and return a tuple of ints for comparison."""
    cleaned = tag.lstrip("vV")
    parts = re.split(r"[.\-]", cleaned)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result)


def _fetch_json(url: str) -> dict | list | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def check_for_update() -> tuple[bool, str, str]:
    """
    Returns (update_available, latest_version_str, download_url).
    download_url is the zip asset URL, or "" if not available.
    """
    data = _fetch_json(API_URL)
    if not data or not isinstance(data, dict):
        return False, "", ""

    latest_tag = data.get("tag_name", "")
    if not latest_tag:
        return False, "", ""

    current = _parse_version(__version__)
    latest  = _parse_version(latest_tag)

    if latest <= current:
        return False, latest_tag.lstrip("vV"), ""

    # Find a zip asset containing the exe
    assets = data.get("assets", [])
    zip_url = ""
    for asset in assets:
        name = asset.get("name", "")
        if name.lower().endswith(".zip"):
            zip_url = asset.get("browser_download_url", "")
            break

    return True, latest_tag.lstrip("vV"), zip_url


def fetch_all_release_notes() -> list[dict]:
    """
    Returns a list of dicts: [{tag, name, body, published_at}, ...]
    Used by the Help → Version History dialog.
    """
    data = _fetch_json(ALL_RELEASES_URL)
    if not data or not isinstance(data, list):
        return []
    results = []
    for release in data:
        results.append({
            "tag":          release.get("tag_name", ""),
            "name":         release.get("name", ""),
            "body":         release.get("body", ""),
            "published_at": release.get("published_at", "")[:10],  # YYYY-MM-DD
        })
    return results


def download_and_install(zip_url: str, on_progress=None) -> None:
    """
    Downloads the zip, extracts just ValveMasterTool.exe next to the running
    exe, then relaunches the app via a batch script.

    on_progress(bytes_done, total_bytes) is called during download if provided.
    """
    # Determine where the running exe lives
    if getattr(sys, "frozen", False):
        exe_path = os.path.abspath(sys.executable)
    else:
        exe_path = os.path.abspath(__file__)

    exe_dir = os.path.dirname(exe_path)

    # Download zip to a temp file
    tmp_zip = os.path.join(tempfile.gettempdir(), "ValveMasterTool_update.zip")

    try:
        req = urllib.request.Request(zip_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            done  = 0
            chunk = 8192
            with open(tmp_zip, "wb") as f:
                while True:
                    data = resp.read(chunk)
                    if not data:
                        break
                    f.write(data)
                    done += len(data)
                    if on_progress and total:
                        on_progress(done, total)
    except Exception as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc

    # Build a batch script that:
    #   1. Waits for this process to exit
    #   2. Extracts ONLY the exe from the zip (PowerShell)
    #   3. Restarts the app
    #   4. Deletes itself
    batch_path = os.path.join(tempfile.gettempdir(), "vmt_update.bat")
    new_exe    = os.path.join(exe_dir, EXE_NAME)
    pid        = os.getpid()

    batch_content = f"""@echo off
:waitloop
tasklist /FI "PID eq {pid}" 2>NUL | find /I "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >NUL
    goto waitloop
)

powershell -ExecutionPolicy Bypass -Command ^
"Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
$zip = [System.IO.Compression.ZipFile]::OpenRead('{tmp_zip}'); ^
$entry = $zip.Entries | Where-Object {{ $_.Name -eq '{EXE_NAME}' }} | Select-Object -First 1; ^
if ($entry) {{ [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, '{new_exe}', $true) }}; ^
$zip.Dispose()"

start "" "{new_exe}"
del "{tmp_zip}" >NUL 2>&1
del "%~f0"
"""

    with open(batch_path, "w") as f:
        f.write(batch_content)

    subprocess.Popen(
        ["cmd.exe", "/c", batch_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )

    # Exit this process so the batch script can replace the exe
    sys.exit(0)
