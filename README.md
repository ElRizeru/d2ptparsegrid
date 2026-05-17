# 🛡️ Dota 2 Pro Tracker & OpenDota Guides

[![Update Hero Grids](https://github.com/ElRizeru/d2ptparsegrid/actions/workflows/update_grids.yml/badge.svg)](https://github.com/ElRizeru/d2ptparsegrid/actions/workflows/update_grids.yml)
[![Build and Release](https://github.com/ElRizeru/d2ptparsegrid/actions/workflows/build_exe.yml/badge.svg)](https://github.com/ElRizeru/d2ptparsegrid/actions/workflows/build_exe.yml)

<p align="center">
  <em>An automated, self-healing pipeline that brings Dota 2 meta directly into your client. Every single day.</em>
</p>

---

## 🌟 What This Project Does

This tool automatically synchronizes your Dota 2 client with the latest professional meta by providing **Hero Grids** (from Dota2ProTracker) and **Dynamic Item/Skill Guides** (from OpenDota). Everything is generated automatically, requiring zero manual maintenance.

<div align="center">
  <table>
    <tr>
      <td align="center"><b>🕹️ Pro Meta Grids</b></td>
      <td align="center"><b>⚔️ Dynamic Item & Skill Guides</b></td>
    </tr>
    <tr>
      <td>Automatically parses Dota2ProTracker to organize your hero selection screen by <i>Most Played</i>, <i>High Winrate</i>, or <i>D2PT Rating</i>.</td>
      <td>Fully automated guide generator that pulls popularity data and ability progression from the OpenDota API. Resilient to game patches.</td>
    </tr>
    <tr>
      <td align="center"><b>🤖 Smart Setup & Backups</b></td>
      <td align="center"><b>☁️ Steam Cloud Sync</b></td>
    </tr>
    <tr>
      <td>Locates your Steam/Dota 2 paths instantly. Safely creates <code>.bak</code> backups of your existing configurations. Updates all profiles on your PC.</td>
      <td>Patches internal Steam cache files to permanently inject your new guides into the Steam Cloud.</td>
    </tr>
  </table>
</div>

---

## 📸 In-Game Preview

<details open>
<summary><b>Hero Grids (Roles & Current Meta)</b></summary>
<br>
<p align="center"><img src="1.png" width="100%" alt="Main Hero Grid"></p>
</details>

<details open>
<summary><b>Counters & Synergies (D2PT Matchups)</b></summary>
<br>
<p align="center"><img src="assets/2.png" width="100%" alt="Counters and Synergies"></p>
</details>

<details open>
<summary><b>In-Game Item Builds</b></summary>
<br>
<p align="center"><img src="assets/3.png" width="500" alt="Item Builds"></p>
</details>

---

## 🚀 Installation Options

### 1. Windows Executable (Recommended)
The absolute easiest way for most users. No setup required.
1. Go to the [Releases](https://github.com/ElRizeru/d2ptparsegrid/releases/latest) page.
2. Download `D2PT-Grid-Updater.exe`.
3. Run it and follow the on-screen instructions.

### 2. PowerShell One-Liner (Zero Install)
Run the updater directly from the internet without downloading any files.
1. Open **PowerShell** on your PC.
2. Copy and paste the following command:
   ```powershell
   powershell -ExecutionPolicy ByPass -Command "irm https://raw.githubusercontent.com/ElRizeru/d2ptparsegrid/main/install.ps1 | iex"
   ```

### 3. Manual Python Execution
For Linux/macOS users, or if you prefer running from source.
1. Download `main.py`.
2. Run: `python main.py`

---

## ⚠️ Important Note: Why Does Steam Restart?

When you choose to install the **Item Guides**, the script will **forcefully close and restart Steam**. This is a necessary and completely safe technical requirement. Here is exactly why this happens:

1. **The Steam Cloud Problem**: Steam heavily aggressively synchronizes Dota 2 hero guides with the Steam Cloud. If you simply paste new guide files into the local folder while Steam is running, Steam will consider them "unofficial" and overwrite them with the older versions from the cloud the next time you launch the game.
2. **The Cache Patch**: To solve this, the script completely exits Steam to unlock the files. It then injects the new item builds and specifically modifies the internal `remotecache.vdf` file. 
3. **The Sync Trick**: By patching the cache file with new timestamps and file signatures, the script "tricks" Steam into thinking that *you* just created these guides manually.
4. **The Restart**: When Steam restarts, it sees the patched cache, trusts the new files, and automatically uploads the new meta guides up to the Steam Cloud, permanently saving them to your account.

---

## 🛠️ Developer Setup

If you want to run the automated pipeline on your own GitHub account:

1. **Fork** this repository.
2. Enable **Read and Write permissions** in `Settings` -> `Actions` -> `General`.
3. The `Update Hero Grids` workflow will automatically run daily at 00:00 UTC.
4. To build your own EXE, manually trigger the `Build and Release` workflow.

---

## 🙏 Acknowledgments
- **[Dota 2 Pro Tracker](https://dota2protracker.com/)** for providing the incredible meta data.
- **[OpenDotaGuides](https://github.com/Egezenn/OpenDotaGuides)** - Special thanks to @Egezenn for the original item builds structure concept, which has now been completely decoupled from static files, heavily optimized, and fully integrated directly into this repository.
- **[Playwright](https://playwright.dev/)** for the scraping engine.

---

## 📄 License
This project is open-source and available under the MIT License.
