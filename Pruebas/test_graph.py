import sys
import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF
from unittest.mock import patch, mock_open

# Configuración de rutas del proyecto
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Ajusta "Grafo.grafo" según el nombre de tu directorio y script
from Grafo.grafo import VINI, addTeamsSofifa, addCompetitionsWikidata, addTeamStatsFBDB, addGamesFBDB, addPlayersSofifa, addPlayersAppearancesFBDB, addShotsFBDB

# ==============================================================================
# MOCKS GLOBALES PARA LAS FUNCIONES DE UNIFICACIÓN
# ==============================================================================
# Reutilizaremos estos decoradores para evitar que los tests intenten cargar 
# los dataframes reales de unificaciones de IDs.

@pytest.fixture(autouse=True)
def mock_unificaciones():
    with patch("Grafo.grafo.obtener_id_equipo", return_value="EQ123"), \
         patch("Grafo.grafo.obtener_id_country", return_value="CO456"), \
         patch("Grafo.grafo.obtener_id_competition", return_value="COMP789"), \
         patch("Grafo.grafo.obtener_id_player", return_value="PL999"):
        yield

# ==============================================================================
# TESTS DE MÉTODOS DE CREACIÓN DE GRAFOS
# ==============================================================================

def test_add_teams_sofifa():
    """Prueba la inserción de triples de equipos desde Sofifa"""
    csv_content = (
        "id,country,league,year,name,url,formation,overall,attack,midfield,defence,"
        "transfer_budget,club_worth,speed,dribbling,passing,positioning,crossing,shooting,"
        "aggression,pressure,team_width,defender_line,domestic_prestige,international_prestige,"
        "players,starting_xi_avg_age,whole_team_avg_age\n"
        "1,Spain,LaLiga,2020,Real Madrid,http://rm.com,4-3-3,85,86,84,85,"
        "100M,1B,60,70,65,free,60,75,50,60,50,50,10,10,25,26.5,25.2\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        addTeamsSofifa(g)
        
    team_season_uri = URIRef("http://vini-eii.org/teamSeason/EQ123_2020")
    team_uri = URIRef("http://vini-eii.org/team/EQ123")
    
    assert (team_season_uri, RDF.type, VINI.TeamSeason) in g
    assert (team_uri, VINI.hasSeason, team_season_uri) in g
    assert (team_season_uri, VINI.name, Literal("Real Madrid")) in g
    assert (team_season_uri, VINI.formation, Literal("4-3-3")) in g
    assert (team_season_uri, VINI.overall, Literal("85")) in g


def test_add_competitions_wikidata():
    """Prueba la inserción de campeones de competiciones desde Wikidata"""
    csv_content = (
        "team,country,competition,año,competitionLabel,teamLabel,countryLabel\n"
        "Q12,Q34,Q56,2019,UEFA Champions League,Liverpool,England\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        addCompetitionsWikidata(g)
        
    winner_uri = URIRef("http://vini-eii.org/competitionWinner/COMP789_EQ123_2019")
    competition_uri = URIRef("http://vini-eii.org/competition/COMP789")
    
    assert (winner_uri, RDF.type, VINI.CompetitionWinner) in g
    assert (winner_uri, VINI.competition, competition_uri) in g
    assert (competition_uri, VINI.competitionName, Literal("UEFA Champions League")) in g


def test_add_team_stats_fbdb():
    """Prueba las estadísticas de partidos por equipo de FBDB"""
    csv_content = (
        "gameID,teamID,season,date,location,goals,xGoals,shots,shotsOnTarget,"
        "deep,ppda,fouls,corners,yellowCards,redCards,result\n"
        "99,5,2018,2018-05-12,h,3,2.5,15,7,5,10.2,8,4,1,0,W\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        addTeamStatsFBDB(g)
        
    game_uri = URIRef("http://vini-eii.org/game/99")
    stats_uri = URIRef("http://vini-eii.org/gameStats/99_home")
    
    assert (game_uri, RDF.type, VINI.Game) in g
    assert (stats_uri, RDF.type, VINI.GameStats) in g
    assert (stats_uri, VINI.goals, Literal("3")) in g
    assert (stats_uri, VINI.result, Literal("W")) in g


def test_add_games_fbdb():
    """Prueba el procesamiento de partidos completos y apuestas de FBDB"""
    csv_content = (
        "gameID,homeTeamID,awayTeamID,leagueID,season,date,homeGoals,homeProbability,"
        "homeGoalsHalfTime,awayGoals,awayProbability,awayGoalsHalfTime,drawProbability,"
        "B365H,B365D,B365A\n"
        "150,10,20,2,2017,2017-10-01,2,0.6,1,1,0.2,0,0.2,1.5,4.0,6.5\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        addGamesFBDB(g)
        
    game_uri = URIRef("http://vini-eii.org/game/150")
    home_perf_uri = URIRef("http://vini-eii.org/gamePerformance/150_home")
    bet_uri = URIRef("http://vini-eii.org/gameBet/150_B365")
    
    assert (game_uri, RDF.type, VINI.Game) in g
    assert (home_perf_uri, VINI.goals, Literal("2")) in g
    assert (game_uri, VINI.drawProbability, Literal("0.2")) in g
    assert (bet_uri, RDF.type, VINI.GameBet) in g
    assert (bet_uri, VINI.homeOdds, Literal("1.5")) in g


def test_add_players_sofifa():
    """Prueba la creación de nodos de jugadores y sus temporadas de Sofifa"""
    csv_content = (
        "id,name,team_contract,nationality,year,birth_year,preferred_foot,url,positions,"
        "age,overall_rating,potential,height,weight,best_overall,best_position,growth,"
        "joined,loan_date_end,value,wage,release_clause,total_attacking,total_skill,"
        "total_movement,total_goalkeeping,total_stats,base_stats,weak_foot,skill_moves,"
        "attacking_work_rate,defensive_work_rate,international_reputation,physical_positioning,"
        "club_kit_number,body_type,real_face\n"
        "20801,Cristiano Ronaldo,Juventus,Portugal,2019,1985,Right,http://cr7.com,ST,"
        "34,93,93,187,83,93,ST,0,2018-07-10,,60M,400K,100M,400,410,430,50,2200,460,4,5,"
        "High,Low,5,93,7,Athletic,Yes\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        addPlayersSofifa(g)
        
    player_uri = URIRef("http://vini-eii.org/player/PL999")
    player_season_uri = URIRef("http://vini-eii.org/playerSeason/PL999_2019")
    
    assert (player_uri, RDF.type, VINI.Player) in g
    assert (player_season_uri, RDF.type, VINI.PlayerSeason) in g
    assert (player_uri, VINI.name, Literal("Cristiano Ronaldo")) in g
    assert (player_season_uri, VINI.overall_rating, Literal("93")) in g
    assert (player_season_uri, VINI.wage, Literal("400K")) in g


def test_add_players_appearances_fbdb():
    """Prueba la inserción por rangos de las apariciones de jugadores en partidos"""
    csv_content = (
        "gameID,playerID,goals,ownGoals,shots,xGoals,xGoalsChain,xGoalsBuildup,"
        "assists,keyPasses,xAssists,position,positionOrder,yellowCard,redCard,time\n"
        "500,10,1,0,3,0.8,1.2,0.4,0,2,0.3,Sub,12,1,0,25\n"
    )
    
    g = Graph()
    with patch("builtins.open", mock_open(read_data=csv_content)):
        # Pasamos rango de líneas 0 a 10 para asegurar que procese la fila del mock
        addPlayersAppearancesFBDB(g, start_line=0, end_line=10)
        
    appearance_uri = URIRef("http://vini-eii.org/playerAppearance/PL999_500")
    
    assert (appearance_uri, RDF.type, VINI.PlayerAppearance) in g
    assert (appearance_uri, VINI.goals, Literal("1")) in g
    assert (appearance_uri, VINI.time, Literal("25")) in g
    assert (appearance_uri, VINI.position, Literal("Sub")) in g


def test_add_shots_fbdb():
    """Prueba la inserción de tiros por rangos incluyendo tirador y asistente"""
    csv_content = (
        "gameID,shooterID,assisterID,minute,situation,lastAction,shotType,shotResult,xGoal,positionX,positionY\n"
        "600,20,30,42,OpenPlay,Pass,LeftFoot,Goal,0.45,0.88,0.52\n"
    )
    
    g = Graph()
    # Mockear internamente el comportamiento para el ID del asistente secundario
    with patch("builtins.open", mock_open(read_data=csv_content)), \
         patch("Grafo.grafo.obtener_id_player", side_effect=["PL_SHOOTER", "PL_ASSISTER"]):
         
        addShotsFBDB(g, start_line=0, end_line=10)
        
    # Recuerda que el ID del shot usa tu contador dinámico de bucle: f"{id_game}_{count}"
    shot_uri = URIRef("http://vini-eii.org/shot/600_0")
    shooter_uri = URIRef("http://vini-eii.org/player/PL_SHOOTER")
    assister_uri = URIRef("http://vini-eii.org/player/PL_ASSISTER")
    
    assert (shot_uri, RDF.type, VINI.Shot) in g
    assert (shot_uri, VINI.shooter, shooter_uri) in g
    assert (shot_uri, VINI.assister, assister_uri) in g
    assert (shot_uri, VINI.shotResult, Literal("Goal")) in g
    assert (shot_uri, VINI.xGoal, Literal("0.45")) in g