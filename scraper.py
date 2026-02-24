"""
SoFIFA Scraper - FIFA 10 (2010)
Scrapes teams and players from sofifa.com using Selenium (real Chrome browser)
to bypass Cloudflare protection, then parses the HTML tables with BeautifulSoup.

Requirements:
    pip install selenium webdriver-manager beautifulsoup4 pandas lxml

Notes:
    • SoFIFA uses Cloudflare; only a real browser can pass its JS challenge.
    • The scraper opens Chrome (visible or headless), navigates page by page,
      and collects all data for the FIFA 10 / 2010 roster.
    • Rate limit: adds polite delays between requests (~2 s).
"""

import time
import logging
import re
from typing import List, Dict, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
# Force stdout to UTF-8 so non-ASCII characters in log messages never crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────
BASE_URL = "https://sofifa.com"

# SoFIFA roster IDs for FIFA 10.
# The "version" query param accepted by sofifa.com is the roster string, e.g. "100001".
# We probe sequentially until no data is found.
FIFA_VERSION  = "10"
ROSTER_RANGE  = range(0, 2)      # test up to roster 100030
POLITE_DELAY  = 1.5                 # seconds between page loads

# Player attribute column order on the sofifa.com /players page
# (the default view with Age, Overall, Potential, Value, Wage, Total Stats)
PLAYER_COLUMNS = [
    "name", "positions", "age", "overall", "potential",
    "club", "contract", "value", "wage", "total_stats",
]

# Team column order on the sofifa.com /teams page
TEAM_COLUMNS = [
    "name", "country_league", "overall", "attack", "midfield",
    "defence", "budget", "worth", "players", "avg_age",
]


# ─── Scraper class ────────────────────────────────────────────────────────────
class SoFIFAScraper:
    """
    Scrapes all teams and players for FIFA 10 (2010) from sofifa.com.

    Uses a real Chrome browser via Selenium to bypass Cloudflare, then
    parses the HTML with BeautifulSoup.

    Strategy
    --------
    1. Find a valid FIFA 10 roster ID by probing /teams?roster=100001 … etc.
    2. Scrape every page of /teams?roster={id}  → collect team links + info.
    3. Scrape every page of /players?roster={id} → collect player info.
    4. Optionally visit each player page for detailed stats.
    5. Save results to CSV.
    """

    def __init__(self, version: str = FIFA_VERSION, headless: bool = False) -> None:
        self.version = version
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.teams:   List[Dict] = []
        self.players: List[Dict] = []
        self._roster_id: Optional[str] = None

    # Browser with anti-detection options, and page loading with retries and polite delays
    def _start_browser(self) -> None:
        """Launch Chrome with anti-detection options."""
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        opts.add_argument("--window-size=1280,900")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        # Make navigator.webdriver undetectable
        self.driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        logger.info("Browser started (headless=%s)", self.headless)

    def _stop_browser(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser closed.")

    # Page loading helper with retries and polite delay
    def _load(self, url: str, wait_selector: str = "table") -> Optional[BeautifulSoup]:
        """
        Navigate to *url*, wait for the CSS *wait_selector* to appear,
        return a BeautifulSoup of the page source.
        Returns None if loading fails after retries.
        """
        if not self.driver:
            return None

        for attempt in range(1, 4):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
                time.sleep(POLITE_DELAY)
                return BeautifulSoup(self.driver.page_source, "lxml")
            except Exception as exc:
                logger.warning("Load failed (%s) – attempt %d/3  url=%s", exc, attempt, url)
                time.sleep(3)

        return None

    # ── Roster discovery ──────────────────────────────────────────────────────
    def find_roster_id(self) -> Optional[str]:
        """
        Probe roster IDs 100001 … 100030 to find one that has data.
        Returns the first valid roster ID, or None if none found.
        """
        logger.info("Looking for a valid FIFA %s roster ID …", self.version)
        for i in ROSTER_RANGE:
            rid = f"{self.version}{i:04d}"
            url = f"{BASE_URL}/teams?roster={rid}&hl=en-US"
            soup = self._load(url)
            if soup is None:
                continue

            table = soup.find("table")
            if table:
                rows = table.find_all("tr")
                data_rows = [r for r in rows if r.find("td")]
                if data_rows:
                    logger.info("  ✓  Roster %s  – %d teams on first page", rid, len(data_rows))
                    self._roster_id = rid
                    return rid

            logger.debug("  ✗  Roster %s – no table data", rid)

        logger.error("No valid FIFA %s roster found.", self.version)
        return None

    # ── Parse helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def _clean(text: str) -> str:
        return " ".join(text.split()) if text else ""

    # Parse the teams table on a /teams page, extract team info + links.
    def _parse_teams_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team rows from one /teams page."""
        teams = []
        table = soup.find("table")
        if not table:
            return teams

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            # Column 0: image/icon (skip) — same layout as the players table
            # Column 1: team name + country + league
            name_cell = cells[1]
            link_tag  = name_cell.find("a", href=re.compile(r"/team/\d+"))
            team_name = self._clean(link_tag.text) if link_tag else self._clean(name_cell.text)
            team_href = link_tag["href"] if link_tag else ""
            team_id_m = re.search(r"/team/(\d+)", team_href)
            team_id   = int(team_id_m.group(1)) if team_id_m else None

            # Country + league live in <span> tags inside the name cell
            sub_spans = name_cell.find_all("span")
            country = self._clean(sub_spans[0].text) if len(sub_spans) > 0 else ""
            league  = self._clean(sub_spans[1].text) if len(sub_spans) > 1 else ""

            def _cell(idx: int) -> str:
                return self._clean(cells[idx].text) if idx < len(cells) else ""

            # Columns 2-9: overall, attack, midfield, defence, budget, worth, players, avg_age
            teams.append({
                "id":           team_id,
                "name":         team_name,
                "country":      country,
                "league":       league,
                "overall":      _cell(2),
                "attack":       _cell(3),
                "midfield":     _cell(4),
                "defence":      _cell(5),
                "budget":       _cell(6),
                "worth":        _cell(7),
                "players":      _cell(8),
                "avg_age":      _cell(9),
                "roster":       self._roster_id,
                "fifa_version": self.version,
                "url":          BASE_URL + team_href if team_href else "",
            })
        return teams

    # Parse the players table on a /players page, extract player info + links.
    def _parse_players_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract player rows from one /players page."""
        players = []
        table = soup.find("table")
        if not table:
            return players

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            # Column 0: player image (skip)
            # Column 1: name + positions + nationality
            info_cell = cells[1]
            link_tag  = info_cell.find("a", href=re.compile(r"/player/\d+"))
            player_name = self._clean(link_tag.text) if link_tag else self._clean(info_cell.text)
            player_href = link_tag["href"] if link_tag else ""
            pid_m = re.search(r"/player/(\d+)", player_href)
            player_id = int(pid_m.group(1)) if pid_m else None

            # Positions are often in <span> tags inside the cell
            pos_spans = info_cell.find_all("span", class_=re.compile(r"pos|badge", re.I))
            positions = " ".join(self._clean(s.text) for s in pos_spans)

            # Nationality flag alt text
            flag = info_cell.find("img")
            nationality = flag.get("title", "") if flag else ""

            def _cell(idx: int) -> str:
                return self._clean(cells[idx].text) if idx < len(cells) else ""

            players.append({
                "id":          player_id,
                "name":        player_name,
                "nationality": nationality,
                "positions":   positions,
                "age":         _cell(2),
                "overall":     _cell(3),
                "potential":   _cell(4),
                "club":        _cell(5),
                "value":       _cell(6),
                "wage":        _cell(7),
                "total_stats": _cell(8) if len(cells) > 8 else "",
                "roster":      self._roster_id,
                "fifa_version": self.version,
                "url":         BASE_URL + player_href if player_href else "",
            })
        return players

    # Pagination helper
    def _get_next_url(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Find the 'Next' pagination link in the rendered HTML.
        Returns its absolute URL, or None if this is the last page.
        """
        for a in soup.find_all("a", href=True):
            if re.search(r"\bNext\b", a.get_text()):
                href = a["href"]
                return href if href.startswith("http") else BASE_URL + href
        return None

    # Scrape all teams
    def scrape_teams(self, roster_id: str) -> List[Dict]:
        """Paginate through /teams using offset (capped at 500) and collect all team records."""
        all_teams: List[Dict] = []
        seen_ids: set = set()
        MAX_OFFSET = 500

        for offset in range(0, MAX_OFFSET + 1, 60):
            url = f"{BASE_URL}/teams?type=club&roster={roster_id}&hl=en-US&offset={offset}"
            logger.info("Teams offset=%d  url=%s", offset, url)
            soup = self._load(url)
            if not soup:
                break

            batch = self._parse_teams_page(soup)
            if not batch:
                logger.info("  (empty page at offset=%d - done)", offset)
                break

            # Loop guard: stop if the first ID is already collected (page wrapped)
            first_id = batch[0].get("id")
            if first_id is not None and first_id in seen_ids:
                logger.info("  (duplicate page at offset=%d - done)", offset)
                break

            added = 0
            for t in batch:
                tid = t.get("id")
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    all_teams.append(t)
                    added += 1

            logger.info("  -> %d teams collected (+%d new)", len(all_teams), added)

        return all_teams

    # Scrape all players
    def scrape_players(self, roster_id: str) -> List[Dict]:
        """Follow 'Next' links to collect every player page."""
        all_players: List[Dict] = []
        seen_ids: set = set()
        url: Optional[str] = f"{BASE_URL}/players?roster={roster_id}&hl=en-US"

        while url:
            logger.info("Players: %s", url)
            soup = self._load(url)
            if not soup:
                break

            batch = self._parse_players_page(soup)
            if not batch:
                logger.info("  (empty page - done)")
                break

            # Loop guard: stop if the first ID is already collected
            first_id = batch[0].get("id")
            if first_id is not None and first_id in seen_ids:
                logger.info("  (duplicate page detected - done)")
                break

            added = 0
            for p in batch:
                pid = p.get("id")
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_players.append(p)
                    added += 1

            logger.info("  -> %d players collected (+%d new)", len(all_players), added)
            url = self._get_next_url(soup)

        return all_players

    # Main scraping pipeline: find roster ID, scrape teams + players, return results.
    def scrape_all(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Full pipeline:
          1. Start browser.
          2. Find a valid FIFA 10 roster ID.
          3. Scrape teams + players across all pages.
          4. Close browser.
        Returns (teams, players).
        """
        logger.info("=" * 60)
        logger.info("SoFIFA scraper  –  FIFA %s  (2010)", self.version)
        logger.info("=" * 60)

        self._start_browser()
        try:
            roster_id = self.find_roster_id()
            if not roster_id:
                logger.error("Cannot proceed without a valid roster ID.")
                return [], []

            logger.info("--- Scraping teams ---")
            self.teams = self.scrape_teams(roster_id)
            logger.info("Total teams: %d", len(self.teams))

            logger.info("--- Scraping players ---")
            #self.players = self.scrape_players(roster_id)
            logger.info("Total players: %d", len(self.players))

        finally:
            self._stop_browser()

        return self.teams, self.players

    # Persist results to CSV files
    def save_to_csv(
        self,
        teams_file:   str = "teams_2010.csv",
        players_file: str = "players_2010.csv",
    ) -> None:
        """Write teams and players to CSV files."""
        if self.teams:
            pd.DataFrame(self.teams).to_csv(teams_file, index=False, encoding="utf-8-sig")
            logger.info("Teams saved → %s  (%d rows)", teams_file, len(self.teams))
        else:
            logger.warning("No teams to save.")

        if self.players:
            pd.DataFrame(self.players).to_csv(players_file, index=False, encoding="utf-8-sig")
            logger.info("Players saved → %s  (%d rows)", players_file, len(self.players))
        else:
            logger.warning("No players to save.")

    # Print a human-readable summary of what was scraped.
    def print_summary(self) -> None:
        """Print a human-readable summary of what was scraped."""
        sep = "-" * 60
        print(f"\n{sep}")
        print(f"  FIFA {self.version} (2010) – Scraping summary")
        print(sep)
        print(f"  Total teams:   {len(self.teams):>5}")
        print(f"  Total players: {len(self.players):>5}")

        if self.teams:
            print("\n  First 10 teams:")
            for t in self.teams[:10]:
                print(f"    • {t['name']:30s}  ({t.get('country','')})")

        if self.players:
            print("\n  Top-10 players by overall rating:")
            def _to_int(val: str) -> int:
                try:
                    return int(re.sub(r"[^\d]", "", str(val)))
                except (ValueError, TypeError):
                    return 0

            top = sorted(self.players, key=lambda x: _to_int(x.get("overall", "")), reverse=True)[:10]
            for p in top:
                print(
                    f"    {str(p.get('overall','')):>3}  "
                    f"{p.get('name',''):30s}  "
                    f"{p.get('positions',''):8s}  "
                    f"{p.get('club','')}"
                )
        print(sep)

