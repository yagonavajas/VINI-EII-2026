import os
import requests
from pathlib import Path

GRAFOS_DIR = os.path.join(os.path.dirname(__file__), "Grafos")
URL = "http://localhost:3030/vini/data"
HEADERS = {"Content-Type": "text/turtle"}

for archivo in sorted(Path(GRAFOS_DIR).glob("*.ttl")):
    with open(archivo, "rb") as f:
        response = requests.post(URL, data=f, headers=HEADERS)
    print(f"{archivo.name}: {response.status_code}")
