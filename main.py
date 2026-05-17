import os
import shutil
import urllib.request
import platform
import logging
import re
import json
import tempfile
from datetime import datetime
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

import hashlib
import time
import subprocess

ITEMBUILDS_ZIP_URL = "https://raw.githubusercontent.com/ElRizeru/d2ptparsegrid/main/itembuilds.zip"
HERO_GRID_RAW_URL_TEMPLATE = "https://raw.githubusercontent.com/{repo}/main/hero_grids/{category}/hero_grid_config.json"
CONFIG_FILE = "config.json"

CATEGORIES = {
    "1": ("most_played", "Most Played"),
    "2": ("high_winrate", "Most Picked Heroes (>50% Winrate)"),
    "3": ("d2pt_rating", "D2PT Rating")
}

ASCII_ART = r"""
 ____  ____  ____ _____    ____ ____  ___ ____  
|  _ \|___ \|  _ \_   _|  / ___|  _ \|_ _|  _ \ 
| | | | __) | |_) || |   | |  _| |_) || || | | |
| |_| |/ __/|  __/ | |   | |_| |  _ < | || |_| |
|____/|_____|_|    |_|    \____|_| \_\___|____/ 
"""

def get_steam_path() -> str:
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            return os.path.normpath(path)
        except Exception:
            return r"C:\Program Files (x86)\Steam"
    else:
        paths = [
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.steam/root"),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return paths[0]

def get_dota_paths(steam_base: str) -> List[str]:
    dota_paths = []
    standard = os.path.join(steam_base, "steamapps", "common", "dota 2 beta")
    if os.path.exists(standard):
        dota_paths.append(standard)
    vdf_path = os.path.join(steam_base, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, "r", encoding="utf-8") as f:
                content = f.read()
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for p in paths:
                    p = p.replace("\\\\", "\\")
                    dota_path = os.path.join(p, "steamapps", "common", "dota 2 beta")
                    if os.path.exists(dota_path) and dota_path not in dota_paths:
                        dota_paths.append(dota_path)
        except Exception as e:
            logger.error(f"Failed to parse libraryfolders.vdf: {e}")
    return dota_paths

def clean_old_guides(guide_path: str, remotecache_path: str, new_build_files: set):
    if not os.path.exists(guide_path):
        return
        
    old_files = []
    for f in os.listdir(guide_path):
        if not f.endswith(".build"):
            continue
        if f in new_build_files:
            continue
            
        filepath = os.path.join(guide_path, f)
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                if '"Title"\t\t"ODG ' in content or '"Title"\t"ODG ' in content:
                    old_files.append(f)
        except Exception:
            pass
            
    if not old_files:
        return
        
    logger.info(f"Cleaning {len(old_files)} old guides from {guide_path}")
    for f in old_files:
        try:
            os.remove(os.path.join(guide_path, f))
        except Exception as e:
            logger.warning(f"Failed to remove {f}: {e}")
            
    if os.path.exists(remotecache_path):
        try:
            with open(remotecache_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            for old_file in old_files:
                vdf_key = f'guides/{old_file}'
                pattern = r'\t*"' + re.escape(vdf_key) + r'"\s*\{[^}]+\}\n'
                content = re.sub(pattern, '', content)
                
            with open(remotecache_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to clean remotecache.vdf: {e}")

def update_itembuilds():
    steam_base = get_steam_path()
    userdata_path = os.path.join(steam_base, "userdata")
    if not os.path.exists(userdata_path):
        logger.error(f"Steam userdata not found at {userdata_path}")
        return

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_zip = os.path.join(tmpdir, "guides_temp.zip")
            extract_path = os.path.join(tmpdir, "extract_temp")
            logger.info(f"Downloading itembuilds...")
            urllib.request.urlretrieve(ITEMBUILDS_ZIP_URL, temp_zip)
            shutil.unpack_archive(temp_zip, extract_path, "zip")
            
            new_build_files = set(os.listdir(extract_path))
            
            steam_running = False
            if platform.system() == "Linux":
                try:
                    if "steam" in subprocess.check_output(["ps", "-A"], text=True).lower():
                        steam_running = True
                        logger.info("Shutting down Steam to update guides...")
                        subprocess.run(["steam", "-shutdown"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(5)
                except: pass
            elif platform.system() == "Windows":
                try:
                    if "steam.exe" in subprocess.check_output(["tasklist"], text=True).lower():
                        steam_running = True
                        logger.info("Shutting down Steam to update guides...")
                        steam_path = os.path.join(steam_base, "steam.exe")
                        subprocess.run([steam_path, "-shutdown"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(5)
                except: pass

            for steam_id in os.listdir(userdata_path):
                if not steam_id.isdigit():
                    continue
                guide_dir = os.path.join(userdata_path, steam_id, "570", "remote", "guides")
                remotecache_path = os.path.join(userdata_path, steam_id, "570", "remotecache.vdf")
                
                os.makedirs(guide_dir, exist_ok=True)
                clean_old_guides(guide_dir, remotecache_path, new_build_files)
                
                for file in new_build_files:
                    src = os.path.join(extract_path, file)
                    dst = os.path.join(guide_dir, file)
                    shutil.copy2(src, dst)
                    
                    if os.path.exists(remotecache_path):
                        with open(dst, "rb") as f:
                            data = f.read()
                            size = len(data)
                            sha = hashlib.sha1(data).hexdigest()
                        
                        try:
                            with open(remotecache_path, "r", encoding="utf-8") as f:
                                lines = f.readlines()
                            
                            vdf_key = f'guides/{file}'
                            found = any(vdf_key in line for line in lines)
                            
                            if not found:
                                for j in range(len(lines)-1, -1, -1):
                                    if lines[j].strip() == '}':
                                        t = int(time.time())
                                        new_entry = f'\t"{vdf_key}"\n\t{{\n\t\t"root"\t\t"0"\n\t\t"size"\t\t"{size}"\n\t\t"localtime"\t\t"{t}"\n\t\t"time"\t\t"{t}"\n\t\t"remotetime"\t\t"{t}"\n\t\t"sha"\t\t"{sha}"\n\t\t"syncstate"\t\t"1"\n\t\t"persiststate"\t\t"0"\n\t\t"platformstosync2"\t\t"-1"\n\t}}\n'
                                        lines.insert(j, new_entry)
                                        break
                                
                                with open(remotecache_path, "w", encoding="utf-8") as f:
                                    f.writelines(lines)
                        except Exception as e:
                            logger.error(f"Failed to update remotecache.vdf: {e}")

            if steam_running:
                logger.info("Restarting Steam...")
                if platform.system() == "Linux":
                    subprocess.Popen(["steam"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                elif platform.system() == "Windows":
                    steam_path = os.path.join(steam_base, "steam.exe")
                    subprocess.Popen([steam_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        logger.info("Itembuilds updated successfully.")
    except Exception as e:
        logger.error(f"Itembuilds update failed: {e}")

def backup_file(file_path: str):
    if os.path.exists(file_path):
        backup_path = file_path + ".bak"
        shutil.copy2(file_path, backup_path)

def update_hero_grids(category_key: str):
    steam_base = get_steam_path()
    userdata_path = os.path.join(steam_base, "userdata")
    if not os.path.exists(userdata_path):
        logger.error(f"Steam userdata not found at {userdata_path}")
        return
    category_folder, category_name = CATEGORIES.get(category_key, CATEGORIES["2"])
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_grid = os.path.join(base_dir, "hero_grids", category_folder, "hero_grid_config.json")
    remote_url = HERO_GRID_RAW_URL_TEMPLATE.format(repo=DEFAULT_REPO, category=category_folder)
    logger.info(f"Updating grids with category: {category_name}")
    updated_count = 0
    for steam_id in os.listdir(userdata_path):
        if not steam_id.isdigit():
            continue
        grid_dir = os.path.join(userdata_path, steam_id, "570", "remote", "cfg")
        if not os.path.exists(grid_dir):
            continue
        target_file = os.path.join(grid_dir, "hero_grid_config.json")
        try:
            backup_file(target_file)
            if os.path.exists(local_grid):
                shutil.copy2(local_grid, target_file)
                source = "local"
            else:
                urllib.request.urlretrieve(remote_url, target_file)
                source = "remote (GitHub)"
            mtime = os.path.getmtime(target_file)
            dt_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{source}] Updated grid for {steam_id}. File date: {dt_str}")
            updated_count += 1
        except Exception as e:
            logger.error(f"Failed update for {steam_id}: {e}")
    if updated_count == 0:
        logger.warning("No Steam profiles found to update.")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def main():
    print(ASCII_ART)
    print("-" * 50)
    config = load_config()
    category_choice = config.get("category")
    install_guides = config.get("install_guides")
    if category_choice and install_guides is not None:
        print(f"Loaded saved settings:")
        print(f"Category: {CATEGORIES[category_choice][1]}")
        print(f"Install Item Guides: {'Yes' if install_guides else 'No'}")
        use_saved = input("\nUse these settings? (y/n, default y): ").lower().strip() or "y"
        if use_saved != "y":
            category_choice = None
            install_guides = None
    if not category_choice:
        print("\nSelect Hero Grid Category:")
        for k, v in CATEGORIES.items():
            print(f"{k}. {v[1]}")
        category_choice = input("\nChoice (default 2): ").strip() or "2"
        if category_choice not in CATEGORIES:
            category_choice = "2"
    if install_guides is None:
        guides_choice = input("\nInstall Item Guides (OpenDotaGuides)? (y/n, default y): ").lower().strip() or "y"
        install_guides = guides_choice == "y"
    if config.get("category") != category_choice or config.get("install_guides") != install_guides:
        save_choice = input("\nSave these settings for future use? (y/n, default n): ").lower().strip() or "n"
        if save_choice == "y":
            save_config({"category": category_choice, "install_guides": install_guides})
    print("\nStarting update...")
    update_hero_grids(category_choice)
    if install_guides:
        update_itembuilds()
    print("\nUpdate complete. Press Enter to exit.")
    input()

if __name__ == "__main__":
    main()
