"""Consultas SPARQL a Wikidata para obtener datos de competiciones deportivas en CSV"""

import requests
import csv
from typing import Dict, List
import os
import sys
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


class WikidataCompetitionScraper:
    """Descarga datos de competiciones de Wikidata mediante queries SPARQL"""
    
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    
    def __init__(self, output_dir: str = "wikidataCompetitions"):
        fuentes_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(fuentes_dir, output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def build_query(self, competitions_qids: list) -> str:
        """Construye query SPARQL con múltiples competiciones"""
        values_section = "\n    ".join([f"wd:{qid}" for qid in competitions_qids])
        
        return f"""
                SELECT ?year ?competition ?competitionLabel ?countryLabel ?teamLabel WHERE {{
          VALUES ?competition {{
            {values_section}
          }}
          
          OPTIONAL {{ ?competition wdt:P17 ?country. }}
          
          ?season wdt:P3450 ?competition;
                  wdt:P1346 ?team;
                  wdt:P580 ?startTime.
          
          BIND(YEAR(?startTime) AS ?year)
          FILTER(?year >= 2012 && ?year <= 2022)
          
          SERVICE wikibase:label {{
                        bd:serviceParam wikibase:language "[AUTO_LANGUAGE],es,en".
          }}
        }}
        ORDER BY ?competitionLabel ?year
        """
    
    def execute_query(self, query: str) -> List[Dict]:
        """Ejecuta consulta SPARQL contra Wikidata"""
        try:
            params = {
                "query": query,
                "format": "json"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            print(f"  Ejecutando consulta...")
            response = requests.get(self.WIKIDATA_ENDPOINT, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            results = response.json().get("results", {}).get("bindings", [])
            print(f"  [OK] Se obtuvieron {len(results)} resultados")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] {e}")
            return []
    
    def format_results(self, results: List[Dict], competitions: Dict[str, str]) -> List[Dict]:
        """Formatea resultados de Wikidata a formato CSV"""
        formatted = []
        for result in results:
            competition_value = result.get('competition', {}).get('value', '')
            qid_match = re.search(r'(Q\d+)$', competition_value)
            qid = qid_match.group(1) if qid_match else ''

            competition_label = result.get('competitionLabel', {}).get('value', 'N/A')
            
            # Si Wikidata devuelve QID en lugar de etiqueta, usar nombre del diccionario
            if re.fullmatch(r'Q\d+', competition_label) and qid in competitions:
                competition_label = competitions[qid]

            formatted.append({
                'año': result.get('year', {}).get('value', 'N/A'),
                'pais': result.get('countryLabel', {}).get('value', 'N/A'),
                'competicion': competition_label,
                'equipo': result.get('teamLabel', {}).get('value', 'N/A')
            })
        return formatted
    
    def save_to_csv(self, results: List[Dict], filename: str) -> str:
        """Guarda resultados en CSV"""
        filepath = os.path.join(self.output_dir, filename)
        
        if not results:
            print(f"  [WARNING] No hay resultados para guardar en {filename}")
            return filepath
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['año', 'pais', 'competicion', 'equipo']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"  [OK] Guardado en: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            return filepath
    
    def fetch_competition(self, competition_qid: str, competition_name: str,
                         year_min: int = 2012, year_max: int = 2022):
        """Obtiene y guarda datos de una competición individual"""
        print(f"\n[DOWNLOAD] Descargando: {competition_name}")
        
        query = self.build_query([competition_qid])
        raw_results = self.execute_query(query)
        formatted_results = self.format_results(raw_results, {competition_qid: competition_name})
        
        csv_filename = f"{competition_name.lower().replace(' ', '_')}.csv"
        filepath = self.save_to_csv(formatted_results, csv_filename)
        
        return formatted_results, filepath
    
    def fetch_multiple_competitions(self, competitions: Dict[str, str],
                                   year_min: int = 2012, year_max: int = 2022):
        """Obtiene datos de múltiples competiciones y los guarda en un único CSV"""
        competition_qids = list(competitions.keys())
        
        print(f"\n{'='*60}")
        print(f">> Descargando {len(competitions)} competiciones...")
        print(f">> Competiciones: {', '.join(competitions.values())}")
        print(f"{'='*60}")
        
        query = self.build_query(competition_qids)
        print(f"\n[DOWNLOAD] Ejecutando consulta combinada...")
        raw_results = self.execute_query(query)
        formatted_results = self.format_results(raw_results, competitions)
        
        filepath = self._save_all_to_csv(formatted_results)
        
        print(f"\n{'='*60}")
        print(f"[OK] Descarga completada")
        print(f"{'='*60}")
        
        return formatted_results, filepath
    
    def _save_all_to_csv(self, results: List[Dict]) -> str:
        """Guarda todos los resultados en archivo CSV único"""
        filepath = os.path.join(self.output_dir, "competiciones.csv")
        
        if not results:
            print(f"  [WARNING] No hay resultados para guardar")
            return filepath
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['año', 'pais', 'competicion', 'equipo']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            print(f"\n  [OK] Guardado en: {filepath}")
            print(f"  [INFO] Total de registros: {len(results)}")
            return filepath
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            return filepath



# ============================================================================
# CONFIGURACIÓN DE COMPETICIONES
# ============================================================================

COMPETITIONS = {
    'Q18756': 'UEFA Champions League',
    'Q18760': 'UEFA Europa League',
    'Q484028': 'Super Copa de Europa',

    # Inglaterra
    'Q9448': 'Premier League',
    'Q11151': 'FA Cup',
    'Q11152': 'EFL Cup',
    'Q189188': 'FA Community Shield',
    
    # España
    'Q324867': 'La Liga',
    'Q163683': 'Copa del Rey',
    'Q485997': 'Supercopa de España',
    
    # Italia
    'Q15804': 'Serie A',
    'Q16400': 'Coppa Italia',
    'Q19618': 'Supercoppa Italiana',
    
    # Francia
    'Q13394': 'Ligue 1',
    'Q19376': 'Coupe de France',
    'Q653544': 'Trophée des Champions',
    
    # Alemania
    'Q82595': 'Bundesliga',
    'Q150880': 'DFB-Pokal',
    'Q156973': 'DFL-Supercup'
}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    scraper = WikidataCompetitionScraper(output_dir="wikidataCompetitions")
    all_results, filepath = scraper.fetch_multiple_competitions(competitions=COMPETITIONS)
    
    print("\n[SUMMARY]")
    print(f"  - Total de registros: {len(all_results)}")
    print(f"  >> Archivo: {filepath}")
