import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from Aplicacion.Fuentes.kaggleDownloader import KaggleDownloader
from Aplicacion.Fuentes.SoFifascraper import SoFIFAScraper
from Aplicacion.Fuentes.wikiDataQuerys import WikidataCompetitionScraper

def test_download_dataset():
    downloader = KaggleDownloader(base_output_dir="./Pruebas/kaggle_test/")
    result = downloader.download_dataset("technika148/football-database")
    assert result is True
    # Verifica que el archivo CSV se haya generado correctamente
    files = os.listdir(downloader.base_output_dir)
    assert "football-database" in files

def test_download_multiple_datasets():
    downloader = KaggleDownloader(base_output_dir="./Pruebas/kaggle_test/")
    datasets = [
        "technika148/football-database",
        {"name": "davidcariboo/player-scores", "folder": "player-scores"}
    ]
    results = downloader.download_multiple_datasets(datasets)
    assert all(results.values())

def test_get_summary():
    downloader = KaggleDownloader(base_output_dir="./Pruebas/kaggle_test/")
    summary = downloader.get_summary()
    assert "base_dir" in summary
    assert len(summary["datasets"]) > 0

# def test_scrape_sofifa():
#     scraper = SoFIFAScraper(version="10", headless=False)
#     teams, players = scraper.scrape_all()

#     if teams:
#         scraper.save_to_csv("test_teams.csv")

#         assert os.path.exists("test_teams.csv")

#         os.remove("test_teams.csv")
#     if players:
#         scraper.save_to_csv(players_file="test_players.csv")

#         assert os.path.exists("test_players.csv")

#         os.remove("test_players.csv")
    
#     assert len(teams) > 0
#     assert len(players) > 0

def test_fetch_multiple_competitions():
    scraper = WikidataCompetitionScraper(output_dir="./Pruebas/wikidata_test/")
    competitions = {
        'Q18756': 'UEFA Champions League',
        'Q18760': 'UEFA Europa League'
    }
    results, filepath = scraper.fetch_multiple_competitions(competitions)
    assert len(results) > 0
    assert os.path.exists(filepath)

    os.remove(filepath)


