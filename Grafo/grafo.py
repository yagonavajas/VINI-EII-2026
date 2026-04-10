import csv
import pandas as pd
from urllib.parse import quote
from pathlib import Path
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF

EX = Namespace("http://example.org/football/")

def addTeams(g):
    with open("./Aplicacion/Fuentes/csv_sofifa/teams_16_20.csv", newline='', encoding='utf-8') as teams_file:
        reader = csv.DictReader(teams_file)
        
        for row in reader:
            uri = URIRef("http://example.org/team/" + row["id"])

            g.add((uri, RDF.type, EX.FootballTeam))

            g.add((uri, EX.name, Literal(row["name"])))
            g.add((uri, EX.country, Literal(row["country"])))
            g.add((uri, EX.league, Literal(row["league"])))
            g.add((uri, EX.formation, Literal(row["formation"])))

            g.add((uri, EX.overall, Literal(row["overall"])))
            g.add((uri, EX.attack, Literal(row["attack"])))
            g.add((uri, EX.midfield, Literal(row["midfield"])))
            g.add((uri, EX.defence, Literal(row["defence"])))

            g.add((uri, EX.transfer_budget, Literal(row["transfer_budget"])))
            g.add((uri, EX.club_worth, Literal(row["club_worth"])))

            g.add((uri, EX.speed, Literal(row["speed"])))
            g.add((uri, EX.dribbling, Literal(row["dribbling"])))
            g.add((uri, EX.passing, Literal(row["passing"])))
            g.add((uri, EX.shooting, Literal(row["shooting"])))

            g.add((uri, EX.year, Literal(row["year"])))
                        
            
def saveGraph(g, filename):
    ttl = g.serialize(format="turtle")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(ttl)

def main():
    # Crear el grafo
    g = Graph()
    g.bind("ex", EX)

    addTeams(g)

    saveGraph(g, "./Aplicacion/Grafo/Grafos/teams_graph.ttl")

if __name__ == "__main__":
    main()
