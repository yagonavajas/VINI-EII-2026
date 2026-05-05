import tkinter as tk
from tkinter import ttk, messagebox
from SPARQLWrapper import SPARQLWrapper, JSON
import threading

class FootballGraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Football Graph - Consultas")
        self.root.geometry("900x600")
        
        # SPARQL endpoint - Cambiar según tu configuración de Fuseki
        self.sparql_endpoint = "http://localhost:3030/vini/sparql"
        
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.tab_players = ttk.Frame(self.notebook)
        self.tab_teams = ttk.Frame(self.notebook)
        self.tab_games = ttk.Frame(self.notebook)
        self.tab_competitions = ttk.Frame(self.notebook)
        self.tab_custom_queries = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_players, text="Jugadores")
        self.notebook.add(self.tab_teams, text="Equipos")
        self.notebook.add(self.tab_games, text="Partidos")
        self.notebook.add(self.tab_competitions, text="Competiciones")
        self.notebook.add(self.tab_custom_queries, text="Consultas personalizadas")
        
        # Configurar pestañas
        self.setup_players_tab()
        self.setup_teams_tab()
        self.setup_games_tab()
        self.setup_competitions_tab()
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
            {'name': 'Ganadores de la UEFA Champions League', 'command': self.execute_champions_query},
            {'name': 'Botón 2', 'command': self.placeholder_query},
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
    
    def execute_champions_query(self):
        """Ejecuta la consulta de ganadores de la UEFA Champions League"""
        self.teams_status.config(text="Ejecutando consulta...", foreground="blue")
        self.root.update()
        
        # Ejecutar en thread separado para no bloquear la UI
        thread = threading.Thread(target=self._fetch_champions_results)
        thread.start()
    
    def _fetch_champions_results(self):
        """Obtiene los resultados de ganadores de Champions (en thread)"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            
            query = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
ORDER BY ?year ?teamName
            """
            
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Limpiar tabla
            for item in self.teams_tree.get_children():
                self.teams_tree.delete(item)
            
            # Configurar columnas si es necesario
            if self.teams_tree['columns'] != ('Año', 'Equipo', 'Overall', 'Formación'):
                self.teams_tree['columns'] = ('Año', 'Equipo', 'Overall', 'Formación')
                self.teams_tree.column('#0', width=0, stretch=tk.NO)
                self.teams_tree.column('Año', anchor=tk.CENTER, width=80)
                self.teams_tree.column('Equipo', anchor=tk.W, width=250)
                self.teams_tree.column('Overall', anchor=tk.CENTER, width=80)
                self.teams_tree.column('Formación', anchor=tk.CENTER, width=150)
                
                self.teams_tree.heading('#0', text='', anchor=tk.W)
                self.teams_tree.heading('Año', text='Año', anchor=tk.CENTER)
                self.teams_tree.heading('Equipo', text='Equipo', anchor=tk.W)
                self.teams_tree.heading('Overall', text='Overall', anchor=tk.CENTER)
                self.teams_tree.heading('Formación', text='Formación', anchor=tk.CENTER)
            
            # Agregar resultados
            if results['results']['bindings']:
                for idx, binding in enumerate(results['results']['bindings']):
                    year = binding.get('year', {}).get('value', 'N/A')
                    team_name = binding.get('teamName', {}).get('value', 'N/A')
                    overall = binding.get('overall', {}).get('value', 'N/A')
                    formation = binding.get('formation', {}).get('value', 'N/A')
                    
                    self.teams_tree.insert('', 'end', values=(year, team_name, overall, formation))
                
                self.teams_status.config(
                    text=f" Se cargaron {len(results['results']['bindings'])} resultados",
                    foreground="green"
                )
            else:
                self.teams_status.config(text="No se encontraron resultados", foreground="orange")
        
        except Exception as e:
            self.teams_status.config(
                text=f"✗ Error: {str(e)}",
                foreground="red"
            )
            messagebox.showerror("Error", f"Error al ejecutar la consulta:\n{str(e)}")
    
    def _fetch_custom_results(self, query):
        """Obtiene los resultados de una consulta personalizada (en thread)"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Limpiar tabla
            for item in self.custom_tree.get_children():
                self.custom_tree.delete(item)
            
            # Eliminar columnas previas
            for col in self.custom_tree['columns']:
                self.custom_tree.delete(col)
            self.custom_tree['columns'] = ()
            
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
                text=f"✗ Error: {str(e)}",
                foreground="red"
            )
            messagebox.showerror("Error", f"Error al ejecutar la consulta:\n{str(e)}")
        
        finally:
            self.btn_custom_execute.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = FootballGraphApp(root)
    root.mainloop()
