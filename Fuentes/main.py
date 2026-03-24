"""
Entry point – runs the SoFIFA scraper for FIFA 10 (2010) and FIFA 11 (2011).

Usage:
    python main.py

Outputs:
    teams_2010.csv    – all clubs / national teams
    players_2010.csv  – all players with full attribute data
    teams_2011.csv    – all clubs / national teams
    players_2011.csv  – all players with full attribute data
"""

import sys
import os
from SoFifascraper import SoFIFAScraper


def scrape_fifa_version(version: str, year: str) -> None:
    """Scrape a specific FIFA version and save to CSV files."""
    # Output directory: csv_sofifa folder in the same location as this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "csv_sofifa")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    teams_file   = os.path.join(output_dir, f"teams_{year}.csv")
    players_file = os.path.join(output_dir, f"players_{year}.csv")

    scraper = SoFIFAScraper(version=version)

    teams, players = scraper.scrape_all()

    if not teams and not players:
        print(
            f"\n[!] Nothing was scraped for FIFA {version} ({year}).\n"
            "    Possible reasons:\n"
            "    • FIFA roster data is not available in the SoFIFA API.\n"
            "    • The API returned 403 (access restricted) or 404 (not found).\n"
            "    • Check your internet connection and try again.\n"
        )
        return False

    scraper.save_to_csv(teams_file=teams_file, players_file=players_file)
    scraper.print_summary()

    print(f"\nDone!  Files written to:\n  {teams_file}\n  {players_file}")
    return True


def main() -> None:
    # Scrape FIFA 12 (2012)
    print("\n" + "=" * 60)
    print("Scraping FIFA 12 (2012)...")
    print("=" * 60)
    success_12 = scrape_fifa_version(version="12", year="2012")

    # Scrape FIFA 11 (2011)
    # print("\n" + "=" * 60)
    # print("Scraping FIFA 11 (2011)...")
    # print("=" * 60)
    # success_11 = scrape_fifa_version(version="11", year="2011")

    # if not success_10 and not success_11:
    #     sys.exit(1)


if __name__ == "__main__":
    main()

