import pandas as pd
import os

# Rutas de los archivos
ruta_sofifa = r"c:\Users\yagon\Desktop\Clase\Quinto año\TFG\Aplicacion\Grafo\UnificacionEntidades\Paises\players_16_20.csv"
ruta_wikidata = r"c:\Users\yagon\Desktop\Clase\Quinto año\TFG\Aplicacion\Grafo\UnificacionEntidades\Paises\competiciones_wikidata.csv"
ruta_salida = r"c:\Users\yagon\Desktop\Clase\Quinto año\TFG\Aplicacion\Grafo\UnificacionEntidades\Paises\paises_unificados.csv"

# Mapeo de países en español a inglés (de Wikidata a Sofifa/English)
mapeo_paises = {
    "Italia": "Italy",
    "Alemania": "Germany",
    "Francia": "France",
    "Reino Unido": "England",
    "España": "Spain",
    "Azerbaiyán": "Azerbaijan",
    "Ucrania": "Ukraine",
    "Portugal": "Portugal",
    "Noruega": "Norway",
    "Macedonia del Norte": "North Macedonia",
    "Estonia": "Estonia",
    "Turquía": "Turkey",
    "Austria": "Austria",
    "Marruecos": "Morocco",
    "República Popular China": "China",
    "Arabia Saudí": "Saudi Arabia",
    "Hungría": "Hungary",
}

# Leer archivos
df_sofifa = pd.read_csv(ruta_sofifa)
df_wikidata = pd.read_csv(ruta_wikidata)

# Extraer países únicos de Sofifa (en inglés)
paises_sofifa = set(df_sofifa['nationality'].unique())

# Extraer países únicos de Wikidata con sus IDs de Wikidata (country) y etiquetas (countryLabel)
paises_wikidata_dict = {}
for _, row in df_wikidata.iterrows():
    country_qid = row['country']
    country_label = row['countryLabel']
    if country_qid not in paises_wikidata_dict:
        paises_wikidata_dict[country_qid] = country_label

print("Países en Wikidata:", sorted(paises_wikidata_dict.values()))

# Crear lista unificada de países
paises_unificados = []
id_final = 1

# Primero, agregar los países que están en Wikidata
for country_qid in sorted(paises_wikidata_dict.keys()):
    country_label = paises_wikidata_dict[country_qid]
    country_sofifa = mapeo_paises.get(country_label, country_label)
    
    paises_unificados.append({
        'idWikidata': country_qid,
        'nameWikidata': country_label,
        'idSofifa': '',
        'nameSofifa': country_sofifa,
        'idFinal': id_final
    })
    id_final += 1

# Agregar países de Sofifa que no estén en Wikidata
paises_sofifa_en_wikidata = set([mapeo_paises.get(paises_wikidata_dict[qid], paises_wikidata_dict[qid]) for qid in paises_wikidata_dict.keys()])
paises_sofifa_restantes = paises_sofifa - paises_sofifa_en_wikidata

for country_sofifa in sorted(paises_sofifa_restantes):
    paises_unificados.append({
        'idWikidata': '',
        'nameWikidata': '',
        'idSofifa': '',
        'nameSofifa': country_sofifa,
        'idFinal': id_final
    })
    id_final += 1

# Crear DataFrame y guardar
df_unificados = pd.DataFrame(paises_unificados)
df_unificados.to_csv(ruta_salida, index=False)

print(f"\n Archivo unificado guardado en: {ruta_salida}")
print(f"Total de países unificados: {len(df_unificados)}")
print("\n" + df_unificados.to_string())
