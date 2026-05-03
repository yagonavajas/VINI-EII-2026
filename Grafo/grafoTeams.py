import csv
import pandas as pd
from urllib.parse import quote
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF, OWL

VINI = Namespace("http://vini-eii.org/")

# Cargar el CSV de equipos unificados una sola vez
EQUIPOS_UNIFICADOS_PATH = "./Aplicacion/Grafo/Archivos/Unificaciones/equipos_unificados_v3.csv"
COUNTRIES_UNIFICADOS_PATH = "./Aplicacion/Grafo/Archivos/Unificaciones/paises_unificados.csv"
COMPETITIONS_UNIFICADOS_PATH = "./Aplicacion/Grafo/Archivos/Unificaciones/competiciones_unificadas.csv"
_equipos_cache = None
_countries_cache = None
_competitions_cache = None


def addTeamsSofifa(graph):
    with open("./Aplicacion/Grafo/Archivos/teams_16_20_sofifa.csv", newline='', encoding='utf-8') as teams_file:
        reader = csv.DictReader(teams_file)

        for row in reader:
            id_team = obtener_id_equipo(idSofifa=row["id"])
            id_country = obtener_id_country(nameSofifa=row["country"])
            id_competition = obtener_id_competition(nameSofifa=row["league"])

            year = row["year"]

            team_season_id = f"{id_team}_{year}"
            uri = URIRef("http://vini-eii.org/teamSeason/" + team_season_id)
            
            team_uri = URIRef("http://vini-eii.org/team/" + id_team)
            
            country_uri = URIRef("http://vini-eii.org/country/" + id_country)
            league_uri = URIRef("http://vini-eii.org/league/" + id_competition)
            
            season_uri = URIRef("http://vini-eii.org/season/" + year)


            graph.add((uri, RDF.type, VINI.TeamSeason))

            graph.add((team_uri, VINI.hasSeason, uri))
            graph.add((uri, VINI.inSeason, season_uri))

            graph.add((uri, VINI.hasCountry, country_uri))
            graph.add((uri, VINI.playsInLeague, league_uri))

            # datos del equipo EN una temporada
            graph.add((uri, VINI.name, Literal(row["name"])))
            #g.add((uri, VINI.country, Literal(row["country"])))
            #g.add((uri, VINI.league, Literal(row["league"])))
            graph.add((uri, VINI.formation, Literal(row["formation"])))

            graph.add((uri, VINI.overall, Literal(row["overall"])))
            graph.add((uri, VINI.attack, Literal(row["attack"])))
            graph.add((uri, VINI.midfield, Literal(row["midfield"])))
            graph.add((uri, VINI.defence, Literal(row["defence"])))

            graph.add((uri, VINI.transfer_budget, Literal(row["transfer_budget"])))
            graph.add((uri, VINI.club_worth, Literal(row["club_worth"])))

            graph.add((uri, VINI.speed, Literal(row["speed"])))
            graph.add((uri, VINI.dribbling, Literal(row["dribbling"])))
            graph.add((uri, VINI.passing, Literal(row["passing"])))
            graph.add((uri, VINI.positioning, Literal(row["positioning"])))
            graph.add((uri, VINI.crossing, Literal(row["crossing"])))
            graph.add((uri, VINI.shooting, Literal(row["shooting"])))
            graph.add((uri, VINI.aggression, Literal(row["aggression"])))
            graph.add((uri, VINI.pressure, Literal(row["pressure"])))

            graph.add((uri, VINI.team_width, Literal(row["team_width"])))
            graph.add((uri, VINI.defender_line, Literal(row["defender_line"])))
           
            graph.add((uri, VINI.domestic_prestige, Literal(row["domestic_prestige"])))
            graph.add((uri, VINI.international_prestige, Literal(row["international_prestige"])))

            graph.add((uri, VINI.players, Literal(row["players"])))
            graph.add((uri, VINI.starting_xi_avg_age, Literal(row["starting_xi_avg_age"])))
            graph.add((uri, VINI.whole_team_avg_age, Literal(row["whole_team_avg_age"])))

            graph.add((uri, VINI.year, Literal(year)))

def addCompetitionsWikidata(graph):
    with open("./Aplicacion/Grafo/Archivos/competiciones_wikidata.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            id_team = obtener_id_equipo(idWikidata=row["team"])
            id_country = obtener_id_country(idWikidata=row["country"])
            id_competition = obtener_id_competition(idWikidata=row["competition"])

            year = row["año"]

            # Crear entidad CompetitionWinner que representa el evento de ganar una competición
            competition_winner_id = f"{id_competition}_{id_team}_{year}"
            winner_uri = URIRef("http://vini-eii.org/competitionWinner/" + competition_winner_id)
            
            # URIs para las entidades relacionadas
            team_uri = URIRef("http://vini-eii.org/team/" + id_team)
            country_uri = URIRef("http://vini-eii.org/country/" + id_country)
            competition_uri = URIRef("http://vini-eii.org/competition/" + id_competition)
            season_uri = URIRef("http://vini-eii.org/season/" + year)

            # Definir tipo y relaciones principales
            graph.add((winner_uri, RDF.type, VINI.CompetitionWinner))
            
            # Relaciones con las entidades principales
            graph.add((winner_uri, VINI.competition, competition_uri))
            graph.add((winner_uri, VINI.winningTeam, team_uri))
            graph.add((winner_uri, VINI.country, country_uri))
            graph.add((winner_uri, VINI.season, season_uri))
            
            # Propiedades del evento
            # graph.add((winner_uri, VINI.year, Literal(year)))
            # graph.add((winner_uri, VINI.competitionName, Literal(row["competitionLabel"])))
            # graph.add((winner_uri, VINI.teamName, Literal(row["teamLabel"])))
            # graph.add((winner_uri, VINI.countryName, Literal(row["countryLabel"])))
            
            # Relación inversa: el equipo ganó esta competición
            graph.add((team_uri, VINI.wonCompetition, winner_uri))
            
            # Relación inversa: la competición fue ganada por este equipo
            graph.add((competition_uri, VINI.wonBy, winner_uri))

def addTeamStatsFBDB(graph):
    # with open("./Aplicacion/Grafo/Archivos/teamstats_16_20_fbdb.csv", newline='', encoding='utf-8') as file:
    #     reader = csv.DictReader(file)

    #     for row in reader:
    #         id_team = obtener_id_equipo(idfbdb=row["teamID"])
    #         id_country = obtener_id_country(nameSofifa=row["country"])
    #         id_competition = obtener_id_competition(nameSofifa=row["league"])

    #         year = row["season"]

    #         team_season_id = f"{id_team}_{year}"
    #         uri = URIRef("http://vini-eii.org/teamSeason/" + team_season_id)
            
    #         team_uri = URIRef("http://vini-eii.org/team/" + id_team)
            
    #         country_uri = URIRef("http://vini-eii.org/country/" + id_country)
    #         league_uri = URIRef("http://vini-eii.org/league/" + id_competition)
            
    #         season_uri = URIRef("http://vini-eii.org/season/" + year)


    #         graph.add((uri, RDF.type, VINI.TeamSeason))

    #         graph.add((team_uri, VINI.hasSeason, uri))

    #         graph.add((uri, VINI.year, Literal(year)))

    pass

def addGamesFBDB(graph): 
    with open("./Aplicacion/Grafo/Archivos/games_16_20_fbdb.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            id_game = row["gameID"]

            id_team_home = obtener_id_equipo(idfbdb=row["homeTeamID"])
            id_team_away = obtener_id_equipo(idfbdb=row["awayTeamID"])
            
            id_competition = obtener_id_competition(idFbdb=row["leagueID"])
            
            if id_team_home is None or id_team_away is None or id_competition is None:
                print(f"Advertencia: No se pudo encontrar ID para el juego {id_game}. HomeTeamID: {row['homeTeamID']} -> {id_team_home}, AwayTeamID: {row['awayTeamID']} -> {id_team_away}, LeagueID: {row['leagueID']} -> {id_competition}")
                continue

            year = row["season"]

            team_home_season_id = f"{id_team_home}_{year}"
            team_away_season_id = f"{id_team_away}_{year}"

            game_uri = URIRef("http://vini-eii.org/game/" + id_game)
            
            team_home_uri = URIRef("http://vini-eii.org/team/" + team_home_season_id)
            team_away_uri = URIRef("http://vini-eii.org/team/" + team_away_season_id)
            
            league_uri = URIRef("http://vini-eii.org/league/" + id_competition)
            
            season_uri = URIRef("http://vini-eii.org/season/" + year)


            graph.add((game_uri, RDF.type, VINI.Game))

            graph.add((team_home_uri, VINI.playGame, game_uri))
            graph.add((team_away_uri, VINI.playGame, game_uri))

            graph.add((league_uri, VINI.hasGame, game_uri))

            graph.add((game_uri, VINI.season, season_uri))


            graph.add((game_uri, VINI.date, Literal(row["date"])))
            graph.add((game_uri, VINI.year, Literal(year)))

            # Performance del equipo local
            home_performance_uri = URIRef("http://vini-eii.org/gamePerformance/" + id_game + "_home")
            graph.add((home_performance_uri, RDF.type, VINI.GamePerformance))
            graph.add((home_performance_uri, VINI.game, game_uri))
            graph.add((home_performance_uri, VINI.team, team_home_uri))
            graph.add((team_home_uri, VINI.hasPerformance, home_performance_uri))
            
            graph.add((home_performance_uri, VINI.goals, Literal(row["homeGoals"])))
            graph.add((home_performance_uri, VINI.probability, Literal(row["homeProbability"])))
            graph.add((home_performance_uri, VINI.goalsHalfTime, Literal(row["homeGoalsHalfTime"])))

            # Performance del equipo visitante
            away_performance_uri = URIRef("http://vini-eii.org/gamePerformance/" + id_game + "_away")
            graph.add((away_performance_uri, RDF.type, VINI.GamePerformance))
            graph.add((away_performance_uri, VINI.game, game_uri))
            graph.add((away_performance_uri, VINI.team, team_away_uri))
            graph.add((team_away_uri, VINI.hasPerformance, away_performance_uri))
            

            graph.add((away_performance_uri, VINI.goals, Literal(row["awayGoals"])))
            graph.add((away_performance_uri, VINI.probability, Literal(row["awayProbability"])))
            graph.add((away_performance_uri, VINI.goalsHalfTime, Literal(row["awayGoalsHalfTime"])))

            # Probabilidad de empate (propiedad del partido)
            graph.add((game_uri, VINI.drawProbability, Literal(row["drawProbability"])))

            # Apuestas - Nodo independiente para cada casa de apuestas
            betting_houses = {
                "B365": ("B365H", "B365D", "B365A"),
                "BW": ("BWH", "BWD", "BWA"),
                "IW": ("IWH", "IWD", "IWA"),
                "PS": ("PSH", "PSD", "PSA"),
                "WH": ("WHH", "WHD", "WHA"),
                "VC": ("VCH", "VCD", "VCA"),
                "PSC": ("PSCH", "PSCD", "PSCA")
            }
            
            for house_name, (home_key, draw_key, away_key) in betting_houses.items():
                if any(row.get(key) for key in [home_key, draw_key, away_key]):
                    bet_uri = URIRef("http://vini-eii.org/gameBet/" + id_game + "_" + house_name)
                    graph.add((bet_uri, RDF.type, VINI.GameBet))
                    graph.add((bet_uri, VINI.game, game_uri))
                    graph.add((bet_uri, VINI.bettingHouse, Literal(house_name)))
                    graph.add((game_uri, VINI.hasBet, bet_uri))
                    
                    graph.add((bet_uri, VINI.homeOdds, Literal(row[home_key])))
                    graph.add((bet_uri, VINI.drawOdds, Literal(row[draw_key])))
                    graph.add((bet_uri, VINI.awayOdds, Literal(row[away_key])))

            count += 1

            if count % 1000 == 0:
                print(f"Procesadas {count} filas")

def obtener_id_equipo(idSofifa=None, idfbdb=None, idWikidata=None):
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
            
def obtener_id_country(idWikidata=None, nameSofifa=None, nameWikidata=None):
    global _countries_cache
    if _countries_cache is None:
        df = pd.read_csv(COUNTRIES_UNIFICADOS_PATH, encoding='utf-8')
        _countries_cache = df
    df = _countries_cache
    
    # Buscar por idWikidata
    if idWikidata and str(idWikidata).strip():
        resultado = df[df['idWikidata'] == str(idWikidata)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    # Luego buscar por nameSofifa (nombre en inglés)
    if nameSofifa and str(nameSofifa).strip():
        resultado = df[df['nameSofifa'] == str(nameSofifa)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    # Finalmente buscar por nameWikidata (nombre en español)
    if nameWikidata and str(nameWikidata).strip():
        resultado = df[df['nameWikidata'] == str(nameWikidata)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    return None


def obtener_id_competition(idWikidata=None, idSofifa=None, idFbdb=None, nameSofifa=None, nameWikidata=None):
    global _competitions_cache
    if _competitions_cache is None:
        df = pd.read_csv(COMPETITIONS_UNIFICADOS_PATH, encoding='utf-8')
        _competitions_cache = df
    df = _competitions_cache
    
    # Buscar por idWikidata
    if idWikidata and str(idWikidata).strip():
        resultado = df[df['idWikidata'] == str(idWikidata)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    # Buscar por idSofifa
    if idSofifa and str(idSofifa).strip():
        try:
            resultado = df[df['idSofifa'] == int(idSofifa)]
            if not resultado.empty:
                return str(int(resultado['idFinal'].values[0]))
        except (ValueError, TypeError):
            pass
    
    # Buscar por idFbdb
    if idFbdb and str(idFbdb).strip():
        try:
            resultado = df[df['idFbdb'] == int(idFbdb)]
            if not resultado.empty:
                return str(int(resultado['idFinal'].values[0]))
        except (ValueError, TypeError):
            pass
    
    # Buscar por nameSofifa
    if nameSofifa and str(nameSofifa).strip():
        resultado = df[df['nameSofifa'] == str(nameSofifa)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    # Finalmente buscar por nameWikidata
    if nameWikidata and str(nameWikidata).strip():
        resultado = df[df['nameWikidata'] == str(nameWikidata)]
        if not resultado.empty:
            return str(int(resultado['idFinal'].values[0]))
    
    return None                  
            
def saveGraph(g, filename):
    ttl = g.serialize(format="turtle")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(ttl)

def main():
    # teamsSofifa = Graph()
    # teamsSofifa.bind("vini", VINI)
    # addTeamsSofifa(teamsSofifa)
    # saveGraph(teamsSofifa, "./Aplicacion/Grafo/Grafos/teams_graph.ttl")

    # competitionsWikidata = Graph()
    # competitionsWikidata.bind("vini", VINI)
    # addCompetitionsWikidata(competitionsWikidata)
    # saveGraph(competitionsWikidata, "./Aplicacion/Grafo/Grafos/competitions_graph.ttl")

    # teamStatsFBDB = Graph()
    # teamStatsFBDB.bind("vini", VINI)
    # addTeamStatsFBDB(teamStatsFBDB)
    # saveGraph(teamStatsFBDB, "./Aplicacion/Grafo/Grafos/team_stats_graph.ttl")

    gamesFBDB = Graph()
    gamesFBDB.bind("vini", VINI)
    addGamesFBDB(gamesFBDB)
    saveGraph(gamesFBDB, "./Aplicacion/Grafo/Grafos/games_graph.ttl")



if __name__ == "__main__":
    main()
