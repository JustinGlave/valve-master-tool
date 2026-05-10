# PhoenixMasterTool — Git & Release Workflow

## One-Time Git Setup

```
git init
git add .
git commit -m "Initial release v1.0.0"
git branch -M main
git remote add origin https://github.com/JustinGlave/phoenix-master-tool.git
git push -u origin main
```

---

## Every Release (repeat this)

### 1. Bump the version
Edit `version.py`:
```python
__version__ = "1.0.1"   # increment as needed
```

### 2. Build and zip
```
build.bat
```
Output:
- `dist\PhoenixMasterTool\PhoenixMasterTool.exe` — full app folder (distribute to new users)
- `PhoenixMasterTool.zip` — exe only (~5 MB, upload this to GitHub Release for auto-updates)

### 3. Commit and push
```
git add .
git commit -m "v1.0.1 - brief description of changes"
git push
```

### 4. Create GitHub Release
1. Go to https://github.com/JustinGlave/phoenix-master-tool/releases
2. Click **Draft a new release**
3. Tag: `v1.0.1` (always lowercase `v`)
4. Title: `v1.0.1 - brief description`
5. Write release notes in the body (shown in Help → Version History)
6. Upload `PhoenixMasterTool.zip`
7. Click **Publish release**

Users see the update banner on their next app launch.

---

## Important Notes

- Always use lowercase `v` in version tags: `v1.0.1` not `V1.0.1`
- Delete `dist\` and `build\` before every rebuild (build.bat does this automatically)
- Upload **only the zip** (exe only) — not the full dist folder
- App must be installed in a **local folder** — NOT OneDrive/Dropbox (file locking breaks updates)
- The update ships only the new exe (~5 MB), not the full PySide6 folder (~255 MB)

---

## Code Signing (optional but strongly recommended)

Without a code-signing certificate, Windows SmartScreen shows a "Windows protected
your PC" warning the first time a user runs the installer or the auto-updated exe.
This kills user trust and routinely causes IT to block the app.

### What you need

| Cert type | Cost (approx)     | SmartScreen behavior                                      |
|-----------|-------------------|-----------------------------------------------------------|
| OV        | $200-400 / year   | Warning shows until enough downloads build "reputation"   |
| **EV**    | $400-800 / year   | Warning suppressed immediately, no reputation period      |

For an internal-but-distributed tool like this, **EV is the right call** if the
budget allows — it spares first-time users the warning entirely. Vendors:
DigiCert, Sectigo, SSL.com.

You'll also need `signtool.exe`, which ships with the
[Windows 10/11 SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/).

### One-time setup

1. Buy and provision an EV (or OV) code-signing certificate.
2. Export it as a `.pfx` file (with private key) — most providers ship it as
   a token (USB/HSM) or a downloadable PFX.
3. Note the cert path and password somewhere only you can see them.

### Per-build setup

Set environment variables before running `build.bat`:

```
set VMT_SIGNING_CERT=C:\Path\To\phoenixmaster.pfx
set VMT_SIGNING_PASSWORD=your-pfx-password
REM Optional override; defaults work for the Win 10/11 SDK installed location.
set SIGNTOOL=C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe
```

When these are set, `build.bat` signs both the inner `PhoenixMasterTool.exe` and
the `PhoenixMasterToolSetup.exe` installer with a SHA-256 timestamp from
DigiCert's free timestamp server.

If `VMT_SIGNING_CERT` is unset, signing is skipped silently (the build still
produces working artifacts — they just trigger SmartScreen).

### Verifying

After build:

```
"%SIGNTOOL%" verify /pa /v dist\PhoenixMasterToolSetup.exe
"%SIGNTOOL%" verify /pa /v dist\PhoenixMasterTool\PhoenixMasterTool.exe
```

Both should report `Successfully verified`.

### EV cert + HSM / token

EV certs typically come on a hardware token. The signtool command in
`build.bat` assumes a `.pfx` on disk. If your cert is on a token, you'll need
to either:

- Use the vendor's signing helper (e.g. SafeNet's `signtool` wrapper with the
  appropriate provider), or
- Switch `build.bat` to `signtool sign /sha1 <cert-thumbprint>` and let
  Windows pick up the cert from the user store.

The script as written is the common-case `.pfx` path. Adjust if needed.
