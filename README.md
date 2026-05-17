# Dota 2 Pro Tracker Hero Grids Auto-Parser

Automated parser for hero grids from [Dota 2 Pro Tracker](https://dota2protracker.com/meta-hero-grids) and an installation script for end-users.

## Structure
- `parser.py`: Scraper script for GitHub Actions.
- `main.py`: User-side script to install grids and item builds.
- `hero_grids/`: Directory containing parsed grids (updated daily).
  - `most_played/`
  - `high_winrate/`
  - `d2pt_rating/`

## Usage (For Players)

1. Download the repository or just the `main.py` file.
2. Ensure Python is installed.
3. Run the updater:
   ```bash
   python main.py
   ```
4. Select the desired hero grid category from the menu.
5. The script automatically locates Dota 2, creates a backup of your existing grid, installs the new one, and updates item builds from OpenDotaGuides.

## Setup (For Developers)

1. Fork this repository.
2. Go to **Settings** -> **Actions** -> **General** -> **Workflow permissions** and enable **Read and write permissions**.
3. Manually trigger the workflow: **Actions** -> **Update Hero Grids** -> **Run workflow**.
4. (Optional) Update `DEFAULT_REPO` in `main.py` to point to your fork.

## Local Parsing
```bash
pip install -r requirements.txt
playwright install chromium
python parser.py
```
