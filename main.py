"""
Entry point – runs the SoFIFA scraper for FIFA 10 (2010).

Usage:
    python main.py

Outputs:
    teams_2010.csv    – all clubs / national teams
    players_2010.csv  – all players with full attribute data
"""

import sys
import os
from scraper import SoFIFAScraper


def main() -> None:
    # Output directory: same folder as this script
    output_dir = os.path.dirname(os.path.abspath(__file__))

    teams_file   = os.path.join(output_dir, "teams_2010.csv")
    players_file = os.path.join(output_dir, "players_2010.csv")

    scraper = SoFIFAScraper(version="10")

    teams, players = scraper.scrape_all()

    if not teams and not players:
        print(
            "\n[!] Nothing was scraped.\n"
            "    Possible reasons:\n"
            "    • FIFA 10 roster data is not available in the SoFIFA API.\n"
            "    • The API returned 403 (access restricted) or 404 (not found).\n"
            "    • Check your internet connection and try again.\n"
        )
        sys.exit(1)

    scraper.save_to_csv(teams_file=teams_file, players_file=players_file)
    scraper.print_summary()

    print(f"\nDone!  Files written to:\n  {teams_file}\n  {players_file}")


if __name__ == "__main__":
    main()

