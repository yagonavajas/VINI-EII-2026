"""
SoFIFA Scraper - Scrapes teams and players from sofifa.com using Selenium and BeautifulSoup.
Bypasses Cloudflare by using a real Chrome browser instance.
"""

import time
import logging
import re
import sys
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logger = logging.getLogger(__name__)

BASE_URL = "https://sofifa.com"
POLITE_DELAY = 1.5

PLAYERS_BASE_URL = (
    "https://sofifa.com/players?type=all"
    "&lg[0]=13&lg[1]=31&lg[2]=53&lg[3]=19&lg[4]=16"
    "&showCol[]=pi&showCol[]=ae&showCol[]=by&showCol[]=hi&showCol[]=wi"
    "&showCol[]=pf&showCol[]=oa&showCol[]=pt&showCol[]=bo&showCol[]=bp"
    "&showCol[]=gu&showCol[]=jt&showCol[]=le&showCol[]=vl&showCol[]=wg"
    "&showCol[]=rc&showCol[]=ta&showCol[]=ts&showCol[]=to&showCol[]=tg"
    "&showCol[]=tt&showCol[]=bs&showCol[]=wk&showCol[]=sk&showCol[]=aw"
    "&showCol[]=dw&showCol[]=ir&showCol[]=bt&showCol[]=hc&showCol[]=phy"
    "&showCol[]=cj"
)

TEAMS_BASE_URL = (
    "https://sofifa.com/teams?type=all"
    "&lg[0]=13&lg[1]=31&lg[2]=53&lg[3]=19&lg[4]=16"
    "&showCol[]=ti&showCol[]=fm&showCol[]=oa&showCol[]=at&showCol[]=md"
    "&showCol[]=df&showCol[]=tb&showCol[]=cw&showCol[]=bs&showCol[]=bd"
    "&showCol[]=bp&showCol[]=bps&showCol[]=cc&showCol[]=cp&showCol[]=cs"
    "&showCol[]=cps&showCol[]=da&showCol[]=dm&showCol[]=dw&showCol[]=dd"
    "&showCol[]=dp&showCol[]=ip&showCol[]=ps&showCol[]=sa&showCol[]=ta"
)

PLAYER_COLUMN_NAMES = [
    "age", "overall_rating", "potential", "team_contract", "player_id", 
    "birth_year", "height", "weight", "preferred_foot",
    "best_overall", "best_position", "growth",
    "joined", "loan_date_end", "value", "wage", "release_clause",
    "total_attacking", "total_skill", "total_movement", "total_goalkeeping",
    "total_stats", "base_stats", "weak_foot", "skill_moves",
    "attacking_work_rate", "defensive_work_rate", "international_reputation",
    "body_type", "real_face", "physical_positioning", "club_kit_number"
]

TEAM_COLUMN_NAMES = [
    "team_id", "formation", "overall", "attack", "midfield", "defence",
    "transfer_budget", "club_worth", "speed", "dribbling", "passing",
    "positioning", "crossing", "passing_2", "shooting", "positioning_2",
    "aggression", "pressure", "team_width", "defender_line",
    "domestic_prestige", "international_prestige", "players",
    "starting_xi_avg_age", "whole_team_avg_age"
]


class SoFIFAScraper:
    """Scrapes FIFA team and player data from sofifa.com using Selenium + BeautifulSoup."""

    def __init__(self, version: str = "10", headless: bool = False) -> None:
        self.version = version
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.teams: List[Dict] = []
        self.players: List[Dict] = []

    def _start_browser(self) -> None:
        """Launch Chrome browser with anti-detection options."""
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
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        opts.add_argument("--window-size=1280,900")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.execute_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        logger.info("Browser started (headless=%s)", self.headless)

    def _stop_browser(self) -> None:
        """Close browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Browser closed.")

    def _select_fifa_version(self) -> bool:
        """Select FIFA version from dropdown."""
        if not self.driver:
            return False

        try:
            logger.info("Selecting FIFA version %s...", self.version)
            time.sleep(1)

            selectors = [
                "//select[contains(@name, 'version') or contains(@id, 'version')]",
                "//select[@name='version']",
                "//select[@id='version']",
            ]

            for selector in selectors:
                try:
                    dropdown = self.driver.find_element(By.XPATH, selector)
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)
                    time.sleep(0.5)

                    for option in dropdown.find_elements(By.TAG_NAME, "option"):
                        option_text = option.text.strip()
                        if self.version in option_text:
                            option.click()
                            logger.info("Selected FIFA version: %s", option_text)
                            time.sleep(1)
                            return True
                except Exception:
                    continue

            logger.warning("Could not find FIFA version dropdown")
            return False

        except Exception as e:
            logger.error("Error selecting FIFA version: %s", e)
            return False

    def _load(self, url: str, wait_selector: str = "table") -> Optional[BeautifulSoup]:
        """Load page and return parsed HTML."""
        if not self.driver:
            return None

        for attempt in range(1, 3):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                )
                time.sleep(POLITE_DELAY)
                return BeautifulSoup(self.driver.page_source, "lxml")
            except Exception as exc:
                logger.warning("Load failed (attempt %d/2): %s", attempt, exc)
                time.sleep(3)

        return None

    @staticmethod
    def _clean(text: str) -> str:
        """Clean and normalize text."""
        return " ".join(text.split()) if text else ""

    def _parse_teams_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract teams from HTML table."""
        teams = []
        table = soup.find("table")
        if not table:
            return teams

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            name_cell = cells[1]
            link_tag = name_cell.find("a", href=re.compile(r"/team/\d+"))
            team_name = self._clean(link_tag.text) if link_tag else self._clean(name_cell.text)
            team_href = link_tag["href"] if link_tag else ""
            team_id_m = re.search(r"/team/(\d+)", team_href)
            team_id = int(team_id_m.group(1)) if team_id_m else None

            flag_img = name_cell.find("img")
            country = self._clean(flag_img.get("title", "")) if flag_img and flag_img.get("title") else ""

            league_link = name_cell.find("a", class_="sub")
            league = self._clean(league_link.text) if league_link else ""

            def _cell(idx: int) -> str:
                return self._clean(cells[idx].text) if idx < len(cells) else ""

            team_data = {
                "id": team_id,
                "name": team_name,
                "country": country,
                "league": league,
                "url": BASE_URL + team_href if team_href else "",
            }

            for col_idx, col_name in enumerate(TEAM_COLUMN_NAMES):
                team_data[col_name] = _cell(col_idx + 2)

            teams.append(team_data)

        return teams

    def _parse_players_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract players from HTML table."""
        players = []
        table = soup.find("table")
        if not table:
            return players

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            info_cell = cells[1]
            link_tag = info_cell.find("a", href=re.compile(r"/player/\d+"))
            player_name = self._clean(link_tag.text) if link_tag else self._clean(info_cell.text)
            player_href = link_tag["href"] if link_tag else ""
            pid_m = re.search(r"/player/(\d+)", player_href)
            player_id = int(pid_m.group(1)) if pid_m else None

            pos_spans = info_cell.find_all("span", class_=re.compile(r"pos|badge", re.I))
            positions = " ".join(self._clean(s.text) for s in pos_spans)

            flag = info_cell.find("img")
            nationality = flag.get("title", "") if flag else ""

            def _cell(idx: int) -> str:
                return self._clean(cells[idx].text) if idx < len(cells) else ""

            player_data = {
                "id": player_id,
                "name": player_name,
                "nationality": nationality,
                "positions": positions,
                "url": BASE_URL + player_href if player_href else "",
            }

            for col_idx, col_name in enumerate(PLAYER_COLUMN_NAMES):
                cell_idx = col_idx + 2

                player_data[col_name] = _cell(cell_idx)

            players.append(player_data)

        return players

    def _get_next_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Find next page link."""
        for a in soup.find_all("a", href=True):
            if re.search(r"\bNext\b", a.get_text()):
                href = a["href"]
                return href if href.startswith("http") else BASE_URL + href
        return None

    def scrape_teams(self) -> List[Dict]:
        """Scrape all teams by following pagination."""
        all_teams: List[Dict] = []
        seen_ids: set = set()
        url: Optional[str] = TEAMS_BASE_URL

        if self.driver:
            logger.info("Loading teams page...")
            self.driver.get(url)
            time.sleep(2)
            self._select_fifa_version()
            time.sleep(2)

        while url:
            logger.info("Teams: %s", url)
            soup = self._load(url)
            if not soup:
                break

            batch = self._parse_teams_page(soup)
            if not batch:
                logger.info("Empty page - done")
                break

            first_id = batch[0].get("id")
            if first_id is not None and first_id in seen_ids:
                logger.info("Duplicate page - done")
                break

            added = 0
            for t in batch:
                tid = t.get("id")
                if tid not in seen_ids:
                    seen_ids.add(tid)
                    all_teams.append(t)
                    added += 1

            logger.info("-> %d teams collected (+%d new)", len(all_teams), added)
            url = self._get_next_url(soup)

        return all_teams

    def scrape_players(self) -> List[Dict]:
        """Scrape all players by following pagination."""
        all_players: List[Dict] = []
        seen_ids: set = set()
        url: Optional[str] = PLAYERS_BASE_URL

        if self.driver:
            logger.info("Loading players page...")
            self.driver.get(url)
            time.sleep(2)
            self._select_fifa_version()
            time.sleep(2)

        while url:
            logger.info("Players: %s", url)
            soup = self._load(url)
            if not soup:
                break

            batch = self._parse_players_page(soup)
            if not batch:
                logger.info("Empty page - done")
                break

            first_id = batch[0].get("id")
            if first_id is not None and first_id in seen_ids:
                logger.info("Duplicate page - done")
                break

            added = 0
            for p in batch:
                pid = p.get("id")
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    all_players.append(p)
                    added += 1

            logger.info("-> %d players collected (+%d new)", len(all_players), added)
            url = self._get_next_url(soup)

        return all_players

    def scrape_all(self) -> Tuple[List[Dict], List[Dict]]:
        """Run full scraping pipeline."""
        logger.info("=" * 60)
        logger.info("SoFIFA Scraper - FIFA %s", self.version)
        logger.info("=" * 60)

        self._start_browser()
        try:
            logger.info("--- Scraping teams ---")
            self.teams = self.scrape_teams()
            logger.info("Total teams: %d", len(self.teams))

            logger.info("--- Scraping players ---")
            self.players = self.scrape_players()
            logger.info("Total players: %d", len(self.players))

        finally:
            self._stop_browser()

        return self.teams, self.players

    def save_to_csv(self, teams_file: str = "teams.csv", players_file: str = "players.csv") -> None:
        """Save teams and players to CSV files."""
        if self.teams:
            pd.DataFrame(self.teams).to_csv(teams_file, index=False, encoding="utf-8-sig")
            logger.info("Teams saved → %s (%d rows)", teams_file, len(self.teams))
        else:
            logger.warning("No teams to save.")

        if self.players:
            pd.DataFrame(self.players).to_csv(players_file, index=False, encoding="utf-8-sig")
            logger.info("Players saved → %s (%d rows)", players_file, len(self.players))
        else:
            logger.warning("No players to save.")

    def print_summary(self) -> None:
        """Print summary of scraped data."""
        sep = "-" * 60
        print(f"\n{sep}")
        print(f"  FIFA {self.version} - Scraping Summary")
        print(sep)
        print(f"  Teams:   {len(self.teams):>5}")
        print(f"  Players: {len(self.players):>5}")

        if self.teams:
            print("\n  First 10 teams:")
            for t in self.teams[:10]:
                print(f"    • {t['name']:30s} ({t.get('league', '')})")

        if self.players:
            print("\n  Top 10 players by rating:")
            def _to_int(val: str) -> int:
                try:
                    return int(re.sub(r"[^\d]", "", str(val)))
                except (ValueError, TypeError):
                    return 0

            top = sorted(self.players, key=lambda x: _to_int(x.get("overall_rating", "")), reverse=True)[:10]
            for p in top:
                print(f"    {p.get('overall_rating', ''):>3}  {p.get('name', ''):30s}  {p.get('positions', '')}")

        print(sep)
