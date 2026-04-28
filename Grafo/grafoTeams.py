import csv
import pandas as pd
from urllib.parse import quote
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF, OWL

VINI = Namespace("http://vini-eii.org/")

# Cargar el CSV de equipos unificados una sola vez
EQUIPOS_UNIFICADOS_PATH = "./Aplicacion/Grafo/Archivos/equipos_unificados_v2.csv"
_equipos_cache = None


def addTeams(g):
    with open("./Aplicacion/Grafo/Archivos/teams_16_20_sofifa.csv", newline='', encoding='utf-8') as teams_file:
        reader = csv.DictReader(teams_file)

        for row in reader:
            id_final = obtener_id_final(idSofifa=row["id"])

            year = row["year"]

            team_season_id = f"{id_final}_{year}"
            uri = URIRef("http://vini-eii.org/teamSeason/" + team_season_id)
            
            team_uri = URIRef("http://vini-eii.org/team/" + id_final)
            
            country_uri = URIRef("http://vini-eii.org/country/" + row["country"].replace(" ", "_"))
            league_uri = URIRef("http://vini-eii.org/league/" + row["league"].replace(" ", "_"))
            
            season_uri = URIRef("http://vini-eii.org/season/" + year)


            g.add((uri, RDF.type, VINI.TeamSeason))

            g.add((team_uri, VINI.hasSeason, uri))
            g.add((uri, VINI.inSeason, season_uri))

            g.add((uri, VINI.hasCountry, country_uri))
            g.add((uri, VINI.playsInLeague, league_uri))

            # datos del equipo EN una temporada
            g.add((uri, VINI.name, Literal(row["name"])))
            g.add((uri, VINI.country, Literal(row["country"])))
            g.add((uri, VINI.league, Literal(row["league"])))
            g.add((uri, VINI.formation, Literal(row["formation"])))

            g.add((uri, VINI.overall, Literal(row["overall"])))
            g.add((uri, VINI.attack, Literal(row["attack"])))
            g.add((uri, VINI.midfield, Literal(row["midfield"])))
            g.add((uri, VINI.defence, Literal(row["defence"])))

            g.add((uri, VINI.transfer_budget, Literal(row["transfer_budget"])))
            g.add((uri, VINI.club_worth, Literal(row["club_worth"])))

            g.add((uri, VINI.speed, Literal(row["speed"])))
            g.add((uri, VINI.dribbling, Literal(row["dribbling"])))
            g.add((uri, VINI.passing, Literal(row["passing"])))
            g.add((uri, VINI.positioning, Literal(row["positioning"])))
            g.add((uri, VINI.crossing, Literal(row["crossing"])))
            g.add((uri, VINI.shooting, Literal(row["shooting"])))
            g.add((uri, VINI.aggression, Literal(row["aggression"])))
            g.add((uri, VINI.pressure, Literal(row["pressure"])))

            g.add((uri, VINI.team_width, Literal(row["team_width"])))
            g.add((uri, VINI.defender_line, Literal(row["defender_line"])))
           
            g.add((uri, VINI.domestic_prestige, Literal(row["domestic_prestige"])))
            g.add((uri, VINI.international_prestige, Literal(row["international_prestige"])))

            g.add((uri, VINI.players, Literal(row["players"])))
            g.add((uri, VINI.starting_xi_avg_age, Literal(row["starting_xi_avg_age"])))
            g.add((uri, VINI.whole_team_avg_age, Literal(row["whole_team_avg_age"])))

            g.add((uri, VINI.year, Literal(year)))

def obtener_id_final(idSofifa=None, idfbdb=None, idWikidata=None):
    global _equipos_cache
    if _equipos_cache is None:
        df = pd.read_csv(EQUIPOS_UNIFICADOS_PATH, encoding='utf-8')
        _equipos_cache = df
    df = _equipos_cache
    
    # Buscar por idWikidata
    if idWikidata and str(idWikidata).strip():
        resultado = df[df['idWikidata'] == str(idWikidata)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    # Luego buscar por idSofifa
    if idSofifa and str(idSofifa).strip():
        try:
            resultado = df[df['idSofifa'] == int(idSofifa)]
            if not resultado.empty:
                return str(int(resultado['idFinal'].values[0]))
        except (ValueError, TypeError):
            pass
    
    # Finalmente buscar por idfbdb
    if idfbdb and str(idfbdb).strip():
        try:
            resultado = df[df['idfbdb'] == int(idfbdb)]
            if not resultado.empty:
                return str(int(resultado['idFinal'].values[0]))
        except (ValueError, TypeError):
            pass
    
    return None                  
            
def saveGraph(g, filename):
    ttl = g.serialize(format="turtle")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(ttl)

def main():
    # Crear el grafo
    g = Graph()
    g.bind("vini", VINI)

    addTeams(g)


    saveGraph(g, "./Aplicacion/Grafo/Grafos/teams_graph.ttl")

if __name__ == "__main__":
    main()
