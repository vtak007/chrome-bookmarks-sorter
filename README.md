# Chrome Bookmarks Sorter

A safe, repeatable tool to sort your Chrome bookmarks.  
Sorts **folders first (A→Z)**, then **bookmarks (A→Z by title)**.  
Sorting is **case-insensitive**, **Unicode-aware**, and **digit-aware** (e.g. `2 < 10`).  

Optional feature: treat titles that **start with digits** (`15 Tips…`, `2024 Report`) as coming **before alphabetic titles**.

Built with **Python 3.9+ (Tkinter GUI)**. A Windows EXE is available via PyInstaller (see **Build** below).

---

## Features

- ✅ Folders before URLs in every folder  
- ✅ Titles sorted case-insensitively with natural digit ordering  
- ✅ Optional “numbers-first” toggle  
- ✅ Dry-run + HTML preview (safe, no file written)  
- ✅ In-place sort with timestamped `.bak` backup  
- ✅ Idempotent (running again produces no further changes if already sorted)  

---

## Safe Use Notes

⚠️ **Close Chrome before sorting in-place.**  
Chrome actively rewrites the `Bookmarks` file while running. If the browser is open, your changes may be overwritten.

⚠️ **Chrome Sync may revert your sort order.**  
See the next section for a step-by-step workflow to handle Sync.

---

## How to Run Safely with Chrome Sync

Chrome’s Sync service may undo your sorted order by pushing down an older unsorted copy from the cloud.  
To make sure your sort sticks, follow these steps:

1. **Pause Sync**  
   - In Chrome, click your profile picture → select **Pause Sync**.

2. **Close Chrome**  
   - Make sure Chrome is not running so it won’t overwrite the `Bookmarks` file while you edit it.

3. **Run the Sorter**  
   - Use **In-place (with backup)** or **Write to file**.  
   - Recommended: run a **Dry-run + HTML report** first to preview.

4. **Verify Locally**  
   - Reopen Chrome and confirm your bookmarks/folders are sorted.

5. **Re-enable Sync**  
   - Resume Sync.  
   - If Chrome reverts your changes:  
     - Go to `chrome://settings/syncSetup`  
     - Choose **Reset Sync**  
     - Then re-enable Sync — your freshly sorted bookmarks will now become the new master copy.

---

## Usage

### 1. Run from Source
```bash
python src/chrome_bookmarks_sorter_gui.pyw
```

### 2. Windows EXE (no Python needed)
- Download `ChromeBookmarksSorterGUI.exe` (from GitHub Actions artifact or build locally).
- Double-click to run.

### 3. GUI Workflow
1. Select your Chrome `Bookmarks` file.  
   - Find it via `chrome://version` → **Profile Path** → file named `Bookmarks`.
2. Choose one:
   - **In-place (with backup)** — safest default.
   - **Write to file** — save a new sorted JSON without touching the original.
3. Options:
   - **Dry-run**: don’t write JSON, just preview.
   - **HTML Report**: export a `preview.html` with a visual tree.
   - **Numbers-first titles**: bubble digit-leading names before alphabetic ones.
4. Click **Run Sort**.
5. Review log in the Output pane and optionally open the report.

---

## Build Locally (Windows)

### PowerShell
```powershell
PowerShell -ExecutionPolicy Bypass -File .\builder\Build-BookmarksSorterGUI.ps1
# EXE created at: .\src\dist\ChromeBookmarksSorterGUI.exe
```

### Batch (CMD)
```powershell
.\builder\make_exe_portable.bat
```

---

## Example Workflows

- **In-place with backup:**
  ```powershell
  ChromeBookmarksSorterGUI.exe
  ```
  (Choose `Bookmarks` → In-place → Backup enabled.)

- **Dry-run with HTML preview:**
  ```powershell
  ChromeBookmarksSorterGUI.exe
  ```
  (Check **Dry-run** + specify an HTML report path.)

---

## Repo Layout

```
chrome-bookmarks-sorter/
├─ src/
│  └─ chrome_bookmarks_sorter_gui.pyw
├─ builder/
│  ├─ Build-BookmarksSorterGUI.ps1
│  └─ make_exe_portable.bat
├─ .github/workflows/
│  └─ build-windows-exe.yml
├─ extension/                  # optional: future Chrome extension port
├─ assets/                     # screenshots, icons
├─ CHANGELOG.md
├─ requirements.txt            # build-time only
├─ .gitignore
├─ LICENSE
└─ README.md
```

---

## GitHub Actions

- Private repo → Actions still work.
- Each push builds a private **Windows EXE artifact**.
- Artifacts are visible only to repo members while private.

---

## License

MIT License (see `LICENSE`).