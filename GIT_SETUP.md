# ValveMasterTool — Git & Release Workflow

## One-Time Git Setup

```
git init
git add .
git commit -m "Initial release v1.0.0"
git branch -M main
git remote add origin https://github.com/JustinGlave/valve-master-tool.git
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
- `dist\ValveMasterTool\ValveMasterTool.exe` — full app folder (distribute to new users)
- `ValveMasterTool.zip` — exe only (~5 MB, upload this to GitHub Release for auto-updates)

### 3. Commit and push
```
git add .
git commit -m "v1.0.1 - brief description of changes"
git push
```

### 4. Create GitHub Release
1. Go to https://github.com/JustinGlave/valve-master-tool/releases
2. Click **Draft a new release**
3. Tag: `v1.0.1` (always lowercase `v`)
4. Title: `v1.0.1 - brief description`
5. Write release notes in the body (shown in Help → Version History)
6. Upload `ValveMasterTool.zip`
7. Click **Publish release**

Users see the update banner on their next app launch.

---

## Important Notes

- Always use lowercase `v` in version tags: `v1.0.1` not `V1.0.1`
- Delete `dist\` and `build\` before every rebuild (build.bat does this automatically)
- Upload **only the zip** (exe only) — not the full dist folder
- App must be installed in a **local folder** — NOT OneDrive/Dropbox (file locking breaks updates)
- The update ships only the new exe (~5 MB), not the full PySide6 folder (~255 MB)
