import tkinter as tk
from tkinter import ttk, messagebox
from SPARQLWrapper import SPARQLWrapper, JSON
import threading
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import re
from io import BytesIO
from PIL import Image, ImageTk
import gzip

class FootballGraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VINI - Consultas")
        
        # Cargar icono una sola vez
        self.icon_path = Path(__file__).resolve().parent / "resources" / "eii.ico"
        self.root.iconbitmap(str(self.icon_path))
        
        self.root.geometry("900x600")
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self._confirm_close)
        
        # Definir consultas disponibles
        self.queries = {
            "champions": {
                "name": "Ganadores de la UEFA Champions League",
                "columns": ("Año", "Equipo", "Overall", "Formación"),
                "vars": ("year", "teamName", "overall", "formation")
            },
            "eficacia": {
                "name": "Eficacia de Goles vs Expected Goals",
                "columns": ("Equipo", "Año", "Goles Promedio", "xG Promedio", "Diferencia", "Eficacia"),
                "vars": ("teamName", "year", "avgGoals", "avgxGoals", "diferencia", "eficacia")
            },
            "team_urls": {
                "name": "URLs de equipos (Sofifa)",
                "columns": ("Equipo", "Temporada", "URL"),
                "vars": ("teamName", "year", "url")
            }
        }
        
        # Puerto del servidor Fuseki
        self.fuseki_port = None
        self.sparql_endpoint = None

        self._fuseki_process = None
        self._loading_step = 0
        self._loading_steps_total = 4
        self._boot_cancelled = False

        self._show_loading_screen()
        boot_thread = threading.Thread(target=self._boot_app, daemon=True)
        boot_thread.start()

    def _show_loading_screen(self):
        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("VINI - Cargando...")
        self.loading_window.protocol("WM_DELETE_WINDOW", self._on_loading_window_close)
        self.loading_window.iconbitmap(str(self.icon_path))
        
        self.loading_window.geometry("420x180")
        self.loading_window.resizable(False, False)
        self.loading_window.grab_set()

        frame = ttk.Frame(self.loading_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text="Iniciando la aplicacion", font=("Arial", 14, "bold"))
        title.pack(pady=(10, 8))

        self.loading_status = ttk.Label(frame, text="Preparando servidor...", foreground="blue")
        self.loading_status.pack(pady=(0, 15))

        self.loading_progress = ttk.Progressbar(frame, mode="determinate", maximum=self._loading_steps_total)
        self.loading_progress.pack(fill=tk.X)

    def _boot_app(self):
        try:
            self._update_loading_status("Iniciando Fuseki...")
            if self._boot_cancelled:
                return
            
            # Usar puerto 3030 por defecto
            self.fuseki_port = 3030
            self.sparql_endpoint = f"http://localhost:{self.fuseki_port}/vini/sparql"
            
            if self._boot_cancelled:
                return
            if not self._is_fuseki_running():
                self._update_loading_status("Arrancando Fuseki en puerto 3030...")
                self._start_fuseki(self.fuseki_port)
            else:
                self._update_loading_status("Fuseki ya esta activo...")
            self._advance_loading_step()

            if self._boot_cancelled:
                return
            self._update_loading_status("Esperando a Fuseki...")
            if not self._wait_for_fuseki_ready():
                raise RuntimeError("Fuseki no responde en el tiempo esperado")
            self._advance_loading_step()

            if self._boot_cancelled:
                return
            self._update_loading_status("Verificando dataset vini...")
            self._ensure_dataset("vini")
            self._advance_loading_step()

            if self._boot_cancelled:
                return
            self._update_loading_status("Cargando grafos...")
            self._run_carga_grafos()
            self._advance_loading_step()

            if self._boot_cancelled:
                return
            self.root.after(0, self._finish_boot)
        except Exception as exc:
            self.root.after(0, self._boot_failed, str(exc))

    def _finish_boot(self):
        self.loading_window.destroy()
        self.root.deiconify()
        self.root.lift()
        self._setup_ui()

    def _boot_failed(self, message):
        self.loading_window.destroy()
        messagebox.showerror("Error", f"No se pudo iniciar la aplicacion:\n{message}")
        self._stop_fuseki()
        self.root.destroy()

    def _update_loading_status(self, message):
        self.root.after(0, lambda: self.loading_status.config(text=message))

    def _advance_loading_step(self):
        self._loading_step += 1
        self.root.after(0, lambda: self.loading_progress.config(value=self._loading_step))

    def _confirm_close(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres cerrar la aplicacion?"):
            self._stop_fuseki()
            self.root.destroy()

    def _on_loading_window_close(self):
        """Manejador para cuando se cierra la ventana de carga"""
        self._boot_cancelled = True
        self._stop_fuseki()
        self.root.destroy()


    def _start_fuseki(self, port=3030):
        """Inicia el servidor Fuseki en el puerto especificado"""
        fuseki_dir = Path(__file__).resolve().parents[1] / "Apache Jena Fuseki" / "apache-jena-fuseki-6.0.0"
        fuseki_bat = fuseki_dir / "fuseki-server.bat"

        if not fuseki_bat.exists():
            raise FileNotFoundError(f"No se encontro {fuseki_bat}")

        # Ejecutar el .bat en una nueva consola
        self._fuseki_process = subprocess.Popen(
            [str(fuseki_bat)],
            cwd=str(fuseki_dir),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

    def _wait_for_fuseki_ready(self, timeout_seconds=60):
        """Espera a que Fuseki esté listo en el puerto configurado"""
        deadline = time.time() + timeout_seconds
        ping_url = f"http://localhost:{self.fuseki_port}/$/ping"
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(ping_url, timeout=2) as response:
                    if response.status == 200:
                        return True
            except urllib.error.URLError:
                time.sleep(1)
        return False

    def _is_fuseki_running(self):
        """Verifica si Fuseki está ejecutándose en el puerto configurado"""
        if self.fuseki_port is None:
            return False
        try:
            ping_url = f"http://localhost:{self.fuseki_port}/$/ping"
            with urllib.request.urlopen(ping_url, timeout=2) as response:
                return response.status == 200
        except urllib.error.URLError:
            return False
    
    def _stop_fuseki(self):
        """Detiene el proceso Fuseki si está ejecutándose"""
        # Primero intentar terminar el proceso guardado
        if self._fuseki_process is not None:
            try:
                self._fuseki_process.terminate()
                try:
                    self._fuseki_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._fuseki_process.kill()
            except Exception as e:
                print(f"Error al terminar proceso: {e}")
            self._fuseki_process = None
        
        # Luego, matar cualquier proceso que esté usando el puerto 3030
        try:
            # Usar netstat para encontrar el PID usando el puerto 3030
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if ':3030' in line and 'LISTENING' in line:
                    # Extraer el PID (último campo)
                    parts = line.split()
                    if len(parts) > 0:
                        pid = parts[-1]
                        if pid.isdigit():
                            try:
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", pid],
                                    capture_output=True,
                                    timeout=5
                                )
                                print(f"Proceso {pid} matado")
                            except Exception as e:
                                print(f"Error matando PID {pid}: {e}")
        except Exception as e:
            print(f"Error al limpiar puerto 3030: {e}")

    def _ensure_dataset(self, dataset_name):
        datasets_url = f"http://localhost:{self.fuseki_port}/$/datasets"
        try:
            with urllib.request.urlopen(datasets_url, timeout=5) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"No se pudo consultar datasets: {exc}")

        if f'"{dataset_name}"' in payload:
            self._delete_dataset(dataset_name)

        data = urllib.parse.urlencode({
            "dbName": dataset_name,
            "dbType": "mem",
        }).encode("utf-8")

        request = urllib.request.Request(datasets_url, data=data, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status not in (200, 201):
                    raise RuntimeError(f"No se pudo crear el dataset {dataset_name}")
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                return
            raise

    def _delete_dataset(self, dataset_name):
        delete_url = f"http://localhost:{self.fuseki_port}/$/datasets/{dataset_name}"
        request = urllib.request.Request(delete_url, method="DELETE")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status not in (200, 204):
                    raise RuntimeError(f"No se pudo borrar el dataset {dataset_name}")
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409):
                return
            raise


    def _run_carga_grafos(self):
        carga_path = Path(__file__).resolve().parents[1] / "Grafo" / "cargaGrafos.py"
        if not carga_path.exists():
            raise FileNotFoundError(f"No se encontro {carga_path}")

        result = subprocess.run(
            [sys.executable, str(carga_path)],
            cwd=str(carga_path.parent),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Error ejecutando cargaGrafos.py")

    def _setup_ui(self):
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear pestañas
        self.tab_players = ttk.Frame(self.notebook)
        self.tab_teams = ttk.Frame(self.notebook)
        self.tab_games = ttk.Frame(self.notebook)
        self.tab_competitions = ttk.Frame(self.notebook)
        self.tab_special = ttk.Frame(self.notebook)
        self.tab_custom_queries = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_players, text="Jugadores")
        self.notebook.add(self.tab_teams, text="Equipos")
        self.notebook.add(self.tab_games, text="Partidos")
        self.notebook.add(self.tab_competitions, text="Competiciones")
        self.notebook.add(self.tab_special, text="Especial")
        self.notebook.add(self.tab_custom_queries, text="Consultas personalizadas")

        # Configurar pestañas
        self.setup_players_tab()
        self.setup_teams_tab()
        self.setup_games_tab()
        self.setup_competitions_tab()
        self.setup_special_tab()
        self.setup_custom_queries_tab()
        
        
    
    def setup_query_tab(self, tab, title, buttons_config):
        """Configura una pestaña con botones de consulta"""
        frame = ttk.Frame(tab, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(frame, text=title, font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Frame para botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        for btn_config in buttons_config:
            btn = ttk.Button(btn_frame, text=btn_config['name'], 
                           command=btn_config['command'])
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Frame para la tabla
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(table_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview (tabla)
        tree = ttk.Treeview(table_frame,
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Label para estado
        status_label = ttk.Label(frame, text="Selecciona una consulta para ejecutar", 
                                foreground="blue")
        status_label.pack(pady=10)
        
        return tree, status_label
    
    def setup_players_tab(self):
        """Configura la pestaña de Jugadores"""
        buttons_config = [
            {'name': 'Botón 1', 'command': self.placeholder_query},
            {'name': 'Botón 2', 'command': self.placeholder_query},
            {'name': 'Botón 3', 'command': self.placeholder_query}
        ]
        self.players_tree, self.players_status = self.setup_query_tab(
            self.tab_players, "Consultas de Jugadores", buttons_config
        )
    
    def setup_teams_tab(self):
        """Configura la pestaña de Equipos"""
        buttons_config = [
            {'name': self.queries["champions"]["name"], 'command': lambda: self.execute_query("champions", self.teams_tree, self.teams_status)},
            {'name': self.queries["eficacia"]["name"], 'command': lambda: self.execute_query("eficacia", self.teams_tree, self.teams_status)},
            {'name': 'Botón 3', 'command': self.placeholder_query}
        ]
        self.teams_tree, self.teams_status = self.setup_query_tab(
            self.tab_teams, "Consultas de Equipos", buttons_config
        )
    
    def setup_games_tab(self):
        """Configura la pestaña de Partidos"""
        buttons_config = [
            {'name': 'Botón 1', 'command': self.placeholder_query},
            {'name': 'Botón 2', 'command': self.placeholder_query},
            {'name': 'Botón 3', 'command': self.placeholder_query}
        ]
        self.games_tree, self.games_status = self.setup_query_tab(
            self.tab_games, "Consultas de Partidos", buttons_config
        )
    
    def setup_competitions_tab(self):
        """Configura la pestaña de Competiciones"""
        buttons_config = [
            {'name': 'Botón 1', 'command': self.placeholder_query},
            {'name': 'Botón 2', 'command': self.placeholder_query},
            {'name': 'Botón 3', 'command': self.placeholder_query}
        ]
        self.competitions_tree, self.competitions_status = self.setup_query_tab(
            self.tab_competitions, "Consultas de Competiciones", buttons_config
        )

    def setup_special_tab(self):
        """Configura la pestaña Especial"""
        frame = ttk.Frame(self.tab_special, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(frame, text="Consultas Especiales", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # Frame para selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(pady=10, fill=tk.X)
        
        label = ttk.Label(selector_frame, text="Selecciona un equipo:")
        label.pack(side=tk.LEFT, padx=5)
        
        self.team_combobox = ttk.Combobox(selector_frame, state="readonly", width=40)
        self.team_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        btn_load = ttk.Button(selector_frame, text="Cargar Equipos",
                             command=self._load_teams_combobox)
        btn_load.pack(side=tk.LEFT, padx=5)
        
        btn_show = ttk.Button(selector_frame, text="Ver Equipaciones",
                             command=self._show_kit_from_combo)
        btn_show.pack(side=tk.LEFT, padx=5)
        
        # Label para estado
        self.special_status = ttk.Label(frame, text="Haz clic en 'Cargar Equipos' para comenzar",
                                foreground="blue")
        self.special_status.pack(pady=10)
        
        # Label para loading
        self.special_loading = ttk.Label(frame, text="", foreground="gray")
        self.special_loading.pack(pady=5)
    
    def setup_custom_queries_tab(self):
        """Configura la pestaña de consultas personalizadas"""
        frame = ttk.Frame(self.tab_custom_queries, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = ttk.Label(frame, text="Crear Consulta SPARQL", 
                         font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Label para la consulta
        label = ttk.Label(frame, text="Escribe tu consulta SPARQL:")
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # Frame para el área de texto y scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar vertical para el texto
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Area de texto
        self.query_text = tk.Text(text_frame, height=10, wrap=tk.WORD, 
                                 yscrollcommand=scrollbar.set)
        self.query_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.query_text.yview)
        
        # Botón para ejecutar
        self.btn_custom_execute = ttk.Button(frame, text="Ejecutar Consulta", 
                                            command=self.execute_custom_query)
        self.btn_custom_execute.pack(pady=10)
        
        # Frame para la tabla de resultados
        result_label = ttk.Label(frame, text="Resultados:")
        result_label.pack(anchor=tk.W, pady=(10, 5))
        
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars para la tabla
        scrollbar_y = ttk.Scrollbar(table_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview para resultados
        self.custom_tree = ttk.Treeview(table_frame,
                                       yscrollcommand=scrollbar_y.set,
                                       xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.config(command=self.custom_tree.yview)
        scrollbar_x.config(command=self.custom_tree.xview)
        
        self.custom_tree.pack(fill=tk.BOTH, expand=True)
        
        # Label para estado
        self.custom_status_label = ttk.Label(frame, text="Escribe tu consulta y haz clic en ejecutar", 
                                            foreground="blue")
        self.custom_status_label.pack(pady=10)
    
    def placeholder_query(self):
        """Placeholder para consultas no implementadas"""
        messagebox.showinfo("Información", "Esta consulta aún no ha sido implementada")
    
    def execute_custom_query(self):
        """Ejecuta la consulta SPARQL personalizada"""
        query = self.query_text.get("1.0", tk.END).strip()
        
        if not query:
            messagebox.showwarning("Advertencia", "Por favor, escribe una consulta SPARQL")
            return
        
        self.btn_custom_execute.config(state=tk.DISABLED)
        self.custom_status_label.config(text="Ejecutando consulta...", foreground="blue")
        self.root.update()
        
        # Ejecutar en thread separado para no bloquear la UI
        thread = threading.Thread(target=self._fetch_custom_results, args=(query,))
        thread.start()
    
    def execute_query(self, query_key, tree, status_label):
        """Ejecuta una consulta parametrizada"""
        status_label.config(text="Ejecutando consulta...", foreground="blue")
        self.root.update()
        
        thread = threading.Thread(
            target=self._fetch_query_results,
            args=(query_key, tree, status_label)
        )
        thread.start()
    
    def _fetch_query_results(self, query_key, tree, status_label):
        """Obtiene los resultados de una consulta parametrizada"""
        # Diccionario de consultas SPARQL
        sparql_queries = {
            "champions": """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX vini: <http://vini-eii.org/>

SELECT ?year ?teamName ?overall ?formation
WHERE {
  ?winner a vini:CompetitionWinner ;
          vini:competition <http://vini-eii.org/competition/6> ;
          vini:winningTeam ?team ;
          vini:season ?season .
  
  ?team vini:hasSeason ?teamSeason .
  ?teamSeason vini:inSeason ?season ;
              vini:name ?teamName ;
              vini:overall ?overall ;
              vini:formation ?formation .
  
  BIND(SUBSTR(STR(?season), STRLEN(STR(?season)) - 3) AS ?year)
}
ORDER BY ?year ?teamName""",
            "eficacia": """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX vini: <http://vini-eii.org/>

SELECT
  ?teamName
  ?year
  (ROUND(AVG(xsd:decimal(?goals)) * 100) / 100 AS ?avgGoals)
  (ROUND(AVG(xsd:decimal(?xGoals)) * 100) / 100 AS ?avgxGoals)
  (ROUND((AVG(xsd:decimal(?goals)) - AVG(xsd:decimal(?xGoals))) * 100) / 100 AS ?diferencia)
  (IF(
      AVG(xsd:decimal(?goals)) > AVG(xsd:decimal(?xGoals)),
      "Efectivo",
      "Inefectivo"
  ) AS ?eficacia)
WHERE {
  ?stats a vini:GameStats ;
         vini:goals ?goals ;
         vini:xGoals ?xGoals ;
         vini:team ?teamSeason .

  ?teamSeason vini:name ?teamName ;
              vini:year ?year .
}
GROUP BY ?teamName ?year
ORDER BY DESC(?diferencia)
LIMIT 30""",
                        "team_urls": """PREFIX vini: <http://vini-eii.org/>

SELECT ?teamName ?year ?url
WHERE {
    ?teamSeason vini:name ?teamName ;
                            vini:year ?year ;
                            vini:url ?url .
}
ORDER BY ?teamName ?year"""
        }
        
        try:
            query_info = self.queries[query_key]
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(sparql_queries[query_key])
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Limpiar tabla
            for item in tree.get_children():
                tree.delete(item)
            
            # Configurar columnas
            if tree['columns'] != query_info["columns"]:
                tree['columns'] = query_info["columns"]
                tree.column('#0', width=0, stretch=tk.NO)
                
                for col in query_info["columns"]:
                    tree.column(col, anchor=tk.W, width=150)
                    tree.heading(col, text=col, anchor=tk.W)
            
            # Agregar resultados
            if results['results']['bindings']:
                for binding in results['results']['bindings']:
                    row = []
                    for var in query_info["vars"]:
                        value = binding.get(var, {}).get('value', 'N/A')
                        row.append(value)
                    tree.insert('', 'end', values=tuple(row))
                
                status_label.config(
                    text=f"Se cargaron {len(results['results']['bindings'])} resultados",
                    foreground="green"
                )
            else:
                status_label.config(text="No se encontraron resultados", foreground="orange")
        
        except Exception as e:
            status_label.config(text=f"Error: {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Error al ejecutar la consulta:\n{str(e)}")
    
    def _fetch_custom_results(self, query):
        """Obtiene los resultados de una consulta personalizada (en thread)"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Limpiar tabla (eliminar todos los items/filas)
            for item in self.custom_tree.get_children():
                self.custom_tree.delete(item)
            
            # Obtener variables de la consulta
            if results['results']['bindings']:
                bindings = results['results']['bindings']
                variables = list(bindings[0].keys())
                
                # Configurar columnas
                self.custom_tree['columns'] = tuple(variables)
                self.custom_tree.column('#0', width=0, stretch=tk.NO)
                
                for var in variables:
                    self.custom_tree.column(var, anchor=tk.W, width=150)
                    self.custom_tree.heading(var, text=var, anchor=tk.W)
                
                # Agregar datos
                for binding in bindings:
                    row = []
                    for var in variables:
                        value = binding.get(var, {}).get('value', 'N/A')
                        row.append(value)
                    self.custom_tree.insert('', 'end', values=tuple(row))
                
                self.custom_status_label.config(
                    text=f" Se cargaron {len(bindings)} resultados",
                    foreground="green"
                )
            else:
                self.custom_status_label.config(text="No se encontraron resultados", 
                                               foreground="orange")
        
        except Exception as e:
            self.custom_status_label.config(
                text=f"Error: {str(e)}",
                foreground="red"
            )
            messagebox.showerror("Error", f"Error al ejecutar la consulta:\n{str(e)}")
        
        finally:
            self.btn_custom_execute.config(state=tk.NORMAL)
    
    def _load_teams_combobox(self):
        """Carga la lista de equipos en el combobox"""
        self.special_status.config(text="Cargando equipos...", foreground="blue")
        self.special_loading.config(text="Obteniendo datos de la base de datos...")
        self.root.update()
        
        thread = threading.Thread(target=self._fetch_teams_for_combobox)
        thread.start()
    
    def _fetch_teams_for_combobox(self):
        """Obtiene todos los equipos y años disponibles"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            query = """PREFIX vini: <http://vini-eii.org/>

SELECT ?teamName ?year ?url
WHERE {
    ?teamSeason vini:name ?teamName ;
                vini:year ?year ;
                vini:url ?url .
}
ORDER BY ?teamName ?year"""
            
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            if results['results']['bindings']:
                teams_data = []
                team_items = []
                
                for binding in results['results']['bindings']:
                    team_name = binding.get('teamName', {}).get('value', 'N/A')
                    year = binding.get('year', {}).get('value', 'N/A')
                    url = binding.get('url', {}).get('value', 'N/A')
                    
                    display_text = f"{team_name} - {year}"
                    team_items.append(display_text)
                    teams_data.append({
                        'team_name': team_name,
                        'year': year,
                        'url': url,
                        'display': display_text
                    })
                
                self.teams_data = teams_data
                self.root.after(0, lambda: self._update_combobox_items(team_items))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Aviso",
                    "No se encontraron equipos en la base de datos"
                ))
                self.root.after(0, lambda: self.special_status.config(
                    text="No hay equipos disponibles",
                    foreground="orange"
                ))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Error cargando equipos:\n{str(e)}"
            ))
            self.root.after(0, lambda: self.special_status.config(
                text=f"Error: {str(e)}",
                foreground="red"
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.config(text=""))
    
    def _update_combobox_items(self, items):
        """Actualiza los items del combobox"""
        self.team_combobox['values'] = items
        self.special_status.config(
            text=f"Se cargaron {len(items)} equipos. Selecciona uno para ver equipaciones.",
            foreground="green"
        )
    
    def _on_team_selected(self, event):
        """Evento cuando se selecciona un equipo del combobox (ahora sin acción automática)"""
        pass
    
    def _show_kit_from_combo(self):
        """Muestra equipaciones del equipo seleccionado en el combobox"""
        selected_index = self.team_combobox.current()
        if selected_index < 0 or not hasattr(self, 'teams_data'):
            messagebox.showwarning("Advertencia", "Por favor selecciona un equipo del desplegable")
            return
        
        team_info = self.teams_data[selected_index]
        self.special_status.config(text="Descargando equipaciones...", foreground="blue")
        self.special_loading.config(text="Obteniendo imagen...")
        self.root.update()
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._fetch_and_show_kit,
            args=(team_info['url'], team_info['team_name'])
        )
        thread.start()
    
    def _fetch_and_show_kit(self, url, team_name):
        """Descarga la página y extrae la imagen de equipaciones"""
        try:
            # Headers mejorados para evitar 403
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://sofifa.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            # Descargar página HTML
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html_data = response.read()
            
            # Descomprimir si está comprimido con gzip
            if html_data[:2] == b'\x1f\x8b':  # Firma de gzip
                html_data = gzip.decompress(html_data)
            
            html = html_data.decode('utf-8')
            
            # Buscar URLs de imágenes de equipaciones
            kit_patterns = [
                r'class="[^"]*kit[^"]*"[^>]*(?:src|data-src)="([^"]+\.(?:png|jpg|jpeg|gif|webp))"',
                r'<img[^>]*kit[^>]*(?:src|data-src)="([^"]+\.(?:png|jpg|jpeg|gif|webp))"',
                r'<img[^>]*(?:src|data-src)="([^"]*kit[^"]*\.(?:png|jpg|jpeg|gif|webp))"',
                r'class="[^"]*uniform[^"]*"[^>]*(?:src|data-src)="([^"]+\.(?:png|jpg|jpeg|gif|webp))"',
                r'player-kit[^>]*src="([^"]+\.(?:png|jpg|jpeg|gif|webp))"',
                r'sofifa\.com/img/kits/[^\s"]+\.(?:png|jpg|jpeg|gif|webp)',
                r'https://sofifa\.com[^\s"]*(?:kit|uniform)[^\s"]*\.(?:png|jpg|jpeg|gif|webp)'
            ]
            
            img_urls = []
            for pattern in kit_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        img_urls.extend([m for m in matches if isinstance(m, str) and m])
                    else:
                        img_urls.extend([m for m in matches if m])
            
            # Filtrar URLs para evitar escudos (badges) y logos
            filtered_urls = []
            for url_candidate in img_urls:
                url_lower = url_candidate.lower()
                # Evitar escudos, logos y otras imágenes que no sean equipaciones
                if not any(x in url_lower for x in ['badge', 'logo', 'crest', 'emblem', 'shield', 'coat', 'flag', 'icon', 'avatar', '_a', '_l', 'default']):
                    if url_candidate not in filtered_urls:  # Evitar duplicados
                        filtered_urls.append(url_candidate)
            
            # Si no encontramos con filtro, usar todas
            img_urls = filtered_urls if filtered_urls else img_urls
            
            if not img_urls:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Información",
                    f"No se encontraron equipaciones para {team_name}.\n\nPrueba visitando directamente:\n{url}"
                ))
                self.root.after(0, lambda: self.special_status.config(
                    text="No se encontraron equipaciones",
                    foreground="orange"
                ))
                return
            
            # Procesar primera imagen encontrada
            img_url = img_urls[0]
            
            # Asegurar que la URL sea absoluta
            if img_url.startswith('/'):
                base_url = 'https://sofifa.com'
                img_url = base_url + img_url
            elif not img_url.startswith('http'):
                img_url = 'https://sofifa.com/' + img_url
            
            # Descargar imagen con headers
            img_req = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(img_req, timeout=10) as img_response:
                img_data = img_response.read()
            
            # Descomprimir imagen si está comprimida con gzip
            if img_data[:2] == b'\x1f\x8b':
                img_data = gzip.decompress(img_data)
            
            # Procesar imagen con PIL
            img = Image.open(BytesIO(img_data))
            
            # Mostrar en nueva ventana
            self.root.after(0, lambda: self._display_kit_window(img, team_name))
            self.root.after(0, lambda: self.special_status.config(
                text=f"Equipaciones de {team_name} mostradas",
                foreground="green"
            ))
            self.root.after(0, lambda: self.special_loading.config(text=""))
        
        except urllib.error.HTTPError as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error HTTP",
                f"Error {e.code} al descargar equipaciones:\n{e.reason}\n\nSofifa puede requerir verificación."
            ))
            self.root.after(0, lambda: self.special_status.config(
                text=f"Error HTTP {e.code}",
                foreground="red"
            ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Error descargando equipaciones:\n{str(e)}"
            ))
            self.root.after(0, lambda: self.special_status.config(
                text=f"Error: {str(e)}",
                foreground="red"
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.config(text=""))
    
    def _display_kit_window(self, img, team_name):
        """Muestra la imagen en una nueva ventana"""
        kit_window = tk.Toplevel(self.root)
        kit_window.title(f"Equipaciones - {team_name}")
        kit_window.iconbitmap(str(self.icon_path))
        
        # Redimensionar imagen si es muy grande
        max_width = 800
        max_height = 600
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convertir a PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # Mostrar imagen
        label = tk.Label(kit_window, image=photo)
        label.image = photo  # Mantener referencia
        label.pack(padx=10, pady=10)
        
        kit_window.geometry(f"{img.width + 20}x{img.height + 20}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FootballGraphApp(root)
    root.mainloop()
