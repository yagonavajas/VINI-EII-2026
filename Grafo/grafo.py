import csv
import re
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
    with open("./Aplicacion/Grafo/Archivos/teamstats_16_20_fbdb.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            id_game = row["gameID"]

            id_team = obtener_id_equipo(idfbdb=row["teamID"])

            year = row["season"]

            team_season_id = f"{id_team}_{year}"

            game_uri = URIRef("http://vini-eii.org/game/" + id_game)
            
            team_uri = URIRef("http://vini-eii.org/teamSeason/" + team_season_id)
            
            season_uri = URIRef("http://vini-eii.org/season/" + year)


            graph.add((game_uri, RDF.type, VINI.Game))

            graph.add((team_uri, VINI.playGame, game_uri))

            graph.add((game_uri, VINI.season, season_uri))

            graph.add((game_uri, VINI.date, Literal(row["date"])))
            graph.add((game_uri, VINI.year, Literal(year)))


            # Performance del equipo local
            if row["location"] == "h":
                team_stats_uri = URIRef("http://vini-eii.org/gameStats/" + id_game + "_home")
            else:
                team_stats_uri = URIRef("http://vini-eii.org/gameStats/" + id_game + "_away")
            
            graph.add((team_stats_uri, RDF.type, VINI.GameStats))
            graph.add((team_stats_uri, VINI.game, game_uri))
            graph.add((team_stats_uri, VINI.team, team_uri))
            graph.add((team_uri, VINI.hasStats, team_stats_uri))
            
            graph.add((team_stats_uri, VINI.goals, Literal(row["goals"])))
            graph.add((team_stats_uri, VINI.xGoals, Literal(row["xGoals"])))
            graph.add((team_stats_uri, VINI.shots, Literal(row["shots"])))
            graph.add((team_stats_uri, VINI.shotsOnTarget, Literal(row["shotsOnTarget"])))
            graph.add((team_stats_uri, VINI.deep, Literal(row["deep"])))
            graph.add((team_stats_uri, VINI.ppda, Literal(row["ppda"])))
            graph.add((team_stats_uri, VINI.fouls, Literal(row["fouls"])))
            graph.add((team_stats_uri, VINI.corners, Literal(row["corners"])))
            graph.add((team_stats_uri, VINI.yellowCards, Literal(row["yellowCards"])))
            graph.add((team_stats_uri, VINI.redCards, Literal(row["redCards"])))
            graph.add((team_stats_uri, VINI.result, Literal(row["result"])))

            count += 1

            if count % 1000 == 0:
                print(f"Procesadas {count} filas")

def addGamesFBDB(graph): 
    with open("./Aplicacion/Grafo/Archivos/games_16_20_fbdb.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            id_game = row["gameID"]

            id_team_home = obtener_id_equipo(idfbdb=row["homeTeamID"])
            id_team_away = obtener_id_equipo(idfbdb=row["awayTeamID"])
            
            id_competition = obtener_id_competition(idFbdb=row["leagueID"])

            year = row["season"]

            team_home_season_id = f"{id_team_home}_{year}"
            team_away_season_id = f"{id_team_away}_{year}"

            game_uri = URIRef("http://vini-eii.org/game/" + id_game)
            
            team_home_uri = URIRef("http://vini-eii.org/teamSeason/" + team_home_season_id)
            team_away_uri = URIRef("http://vini-eii.org/teamSeason/" + team_away_season_id)
            
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

def addPlayersSofifa(graph):
    with open("./Aplicacion/Grafo/Archivos/players_16_20_sofifa.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader:
            #id falta unificar (idFinal)
            id_player = row["id"] # obtener_id_player(idSofifa=row["id"])
            id_team = obtener_id_equipo(nombreSofifa=row["team_contract"])
            id_country = obtener_id_country(nameSofifa=row["nationality"])

            year = row["year"]

            player_season_id = f"{id_player}_{year}"
            player_season_uri = URIRef("http://vini-eii.org/playerSeason/" + player_season_id)

            player_uri = URIRef("http://vini-eii.org/player/" + id_player)

            season_uri = URIRef("http://vini-eii.org/season/" + year)

            graph.add((player_uri, RDF.type, VINI.Player))
            graph.add((player_season_uri, RDF.type, VINI.PlayerSeason))

            graph.add((player_uri, VINI.hasSeason, player_season_uri))
            graph.add((player_season_uri, VINI.inSeason, season_uri))

            country_uri = URIRef("http://vini-eii.org/country/" + id_country)
            graph.add((player_uri, VINI.born, country_uri))

            team_name = _extract_team_name(row.get("team_contract", ""))
            id_team = obtener_id_equipo(nombreSofifa=team_name)

            team_season_id = f"{id_team}_{year}"
            team_season_uri = URIRef("http://vini-eii.org/teamSeason/" + team_season_id)
            graph.add((player_season_uri, VINI.playsFor, team_season_uri))
            graph.add((team_season_uri, VINI.hasPlayer, player_season_uri))

            graph.add((player_uri, VINI.name, Literal(row["name"])))
            graph.add((player_uri, VINI.player_id, Literal(row["player_id"])))
            graph.add((player_uri, VINI.birth_year, Literal(row["birth_year"])))
            graph.add((player_uri, VINI.preferred_foot, Literal(row["preferred_foot"])))

            # Estadisticas de jugador en una temporada
            graph.add((player_season_uri, VINI.positions, Literal(row["positions"])))
            graph.add((player_season_uri, VINI.age, Literal(row["age"])))
            graph.add((player_season_uri, VINI.overall_rating, Literal(row["overall_rating"])))
            graph.add((player_season_uri, VINI.potential, Literal(row["potential"])))
            graph.add((player_season_uri, VINI.team_contract, Literal(row["team_contract"])))
            graph.add((player_season_uri, VINI.height, Literal(row["height"])))
            graph.add((player_season_uri, VINI.weight, Literal(row["weight"])))            
            graph.add((player_season_uri, VINI.best_overall, Literal(row["best_overall"])))
            graph.add((player_season_uri, VINI.best_position, Literal(row["best_position"])))
            graph.add((player_season_uri, VINI.growth, Literal(row["growth"])))
            graph.add((player_season_uri, VINI.joined, Literal(row["joined"])))
            graph.add((player_season_uri, VINI.loan_date_end, Literal(row["loan_date_end"])))
            graph.add((player_season_uri, VINI.value, Literal(row["value"])))
            graph.add((player_season_uri, VINI.wage, Literal(row["wage"])))
            graph.add((player_season_uri, VINI.release_clause, Literal(row["release_clause"])))
            graph.add((player_season_uri, VINI.total_attacking, Literal(row["total_attacking"])))
            graph.add((player_season_uri, VINI.total_skill, Literal(row["total_skill"])))
            graph.add((player_season_uri, VINI.total_movement, Literal(row["total_movement"])))
            graph.add((player_season_uri, VINI.total_goalkeeping, Literal(row["total_goalkeeping"])))
            graph.add((player_season_uri, VINI.total_stats, Literal(row["total_stats"])))
            graph.add((player_season_uri, VINI.base_stats, Literal(row["base_stats"])))
            graph.add((player_season_uri, VINI.weak_foot, Literal(row["weak_foot"])))
            graph.add((player_season_uri, VINI.skill_moves, Literal(row["skill_moves"])))
            graph.add((player_season_uri, VINI.attacking_work_rate, Literal(row["attacking_work_rate"])))
            graph.add((player_season_uri, VINI.defensive_work_rate, Literal(row["defensive_work_rate"])))
            graph.add((player_season_uri, VINI.international_reputation, Literal(row["international_reputation"])))
            graph.add((player_season_uri, VINI.physical_positioning, Literal(row["physical_positioning"])))
            graph.add((player_season_uri, VINI.club_kit_number, Literal(row["club_kit_number"])))
            graph.add((player_season_uri, VINI.body_type, Literal(row["body_type"])))
            graph.add((player_season_uri, VINI.real_face, Literal(row["real_face"])))            
            graph.add((player_season_uri, VINI.year, Literal(year)))

            count += 1

            if count % 1000 == 0:
                print(f"Procesadas {count} filas")

def addPlayersAppearancesFBDB(graph):
    with open("./Aplicacion/Grafo/Archivos/appearances_16_20_fbdb.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        count = 0

        for row in reader: 
            id_game = row["gameID"]
            id_player = row["playerID"]

            # Crear identificador único para la aparición (jugador + partido)
            appearance_id = f"{id_player}_{id_game}"
            
            # URIs principales
            appearance_uri = URIRef("http://vini-eii.org/playerAppearance/" + appearance_id)
            game_uri = URIRef("http://vini-eii.org/game/" + id_game)
            player_uri = URIRef("http://vini-eii.org/player/" + id_player)

            graph.add((appearance_uri, RDF.type, VINI.PlayerAppearance))

            graph.add((appearance_uri, VINI.player, player_uri))
            graph.add((appearance_uri, VINI.game, game_uri))
            
            graph.add((player_uri, VINI.appearsIn, appearance_uri))
            graph.add((game_uri, VINI.hasPlayerAppearance, appearance_uri))

            graph.add((appearance_uri, VINI.goals, Literal(row["goals"])))
            graph.add((appearance_uri, VINI.ownGoals, Literal(row["ownGoals"])))
            graph.add((appearance_uri, VINI.shots, Literal(row["shots"])))
            graph.add((appearance_uri, VINI.xGoals, Literal(row["xGoals"])))
            graph.add((appearance_uri, VINI.xGoalsChain, Literal(row["xGoalsChain"])))
            graph.add((appearance_uri, VINI.xGoalsBuildup, Literal(row["xGoalsBuildup"])))
            graph.add((appearance_uri, VINI.assists, Literal(row["assists"])))
            graph.add((appearance_uri, VINI.keyPasses, Literal(row["keyPasses"])))
            graph.add((appearance_uri, VINI.xAssists, Literal(row["xAssists"])))
            graph.add((appearance_uri, VINI.position, Literal(row["position"])))
            graph.add((appearance_uri, VINI.positionOrder, Literal(row["positionOrder"])))
            graph.add((appearance_uri, VINI.yellowCard, Literal(row["yellowCard"])))
            graph.add((appearance_uri, VINI.redCard, Literal(row["redCard"])))
            graph.add((appearance_uri, VINI.time, Literal(row["time"])))

            count += 1

            if count % 1000 == 0:
                print(f"Procesadas {count} filas")

def addShotsFBDB(graph):
    
    pass

def _extract_team_name(team_contract):
    if not team_contract:
        return ""

    name = team_contract
    if "~" in name:
        name = name.split("~", 1)[0].strip()

    name = name.replace("On loan", "").strip()
    name = re.sub(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b.*$", "", name).strip()
    name = re.sub(r"\b\d{4}\b.*$", "", name).strip()

    return name
            

def obtener_id_equipo(idSofifa=None, idfbdb=None, idWikidata=None, nombreSofifa=None):
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

    # Luego buscar por nombreSofifa
    if nombreSofifa and str(nombreSofifa).strip():
        try:
            resultado = df[df['nombreSofifa'] == str(nombreSofifa)]
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
    # saveGraph(teamStatsFBDB, "./Aplicacion/Grafo/Grafos/teamstats_graph.ttl")

    # gamesFBDB = Graph()
    # gamesFBDB.bind("vini", VINI)
    # addGamesFBDB(gamesFBDB)
    # saveGraph(gamesFBDB, "./Aplicacion/Grafo/Grafos/games_graph.ttl")

    # playersSofifa = Graph()
    # playersSofifa.bind("vini", VINI)
    # addPlayersSofifa(playersSofifa)
    # saveGraph(playersSofifa, "./Aplicacion/Grafo/Grafos/players_graph.ttl")

    appearancesFBDB = Graph()
    appearancesFBDB.bind("vini", VINI)
    addPlayersAppearancesFBDB(appearancesFBDB)
    saveGraph(appearancesFBDB, "./Aplicacion/Grafo/Grafos/appearances_graph.ttl")





if __name__ == "__main__":
    main()
