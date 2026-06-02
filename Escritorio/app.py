import customtkinter as ctk
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
import re
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageTk
import gzip
from bs4 import BeautifulSoup
from queries import *
from menu_help import *
from ui import *

class FootballGraphApp:
    def __init__(self, root):
        # Configurar tema de CustomTkinter
        setup_app_theme()
        
        self.root = root
        self.root.title("VINI - Consultas de Fútbol")
        self.root.configure(fg_color=Colors.BG_PRIMARY)
        
        # Cargar icono una sola vez
        self.icon_path = Path(__file__).resolve().parent / "resources" / "eii.ico"
        try:
            self.root.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono: {e}")
            print(f"Ruta intentada: {self.icon_path}")
        
        self.root.geometry("1200x700")
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self._confirm_close)
        
        # Cargar consultas disponibles desde queries.py
        self.queries = QUERIES_INFO
        
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
        self.loading_window = ctk.CTkToplevel(self.root)
        self.loading_window.title("VINI - Cargando...")
        self.loading_window.protocol("WM_DELETE_WINDOW", self._on_loading_window_close)
        
        try:
            self.loading_window.iconbitmap(str(self.icon_path))
            print(f"Icono de carga establecido correctamente: {self.icon_path}")
        except tk.TclError as e:
            print(f"Error cargando icono en loading_window: {e}")
        
        self.loading_window.geometry("420x180")
        self.loading_window.resizable(False, False)
        self.loading_window.grab_set()
        self.loading_window.configure(fg_color=Colors.BG_PRIMARY)

        frame = ctk.CTkFrame(self.loading_window, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(frame, text="Iniciando la aplicación", 
                            font=("Segoe UI", FontSizes.TITLE, "bold"), text_color=Colors.ACCENT_GREEN)
        title.pack(pady=(10, 8))

        self.loading_status = ctk.CTkLabel(frame, text="Preparando servidor...", 
                                          text_color=Colors.TEXT_SECONDARY)
        self.loading_status.pack(pady=(0, 15))

        self.loading_progress = ctk.CTkProgressBar(
            frame, 
            mode="determinate", 
            fg_color=Colors.BG_TERTIARY,
            progress_color=Colors.ACCENT_GREEN,
            height=8
        )
        self.loading_progress.set(0)
        self.loading_progress.pack(fill="x")

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
        # Volver a establecer el icono después de deiconify (Windows a veces lo pierde)
        try:
            self.root.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error re-estableciendo icono: {e}")
        self.root.lift()
        self._setup_ui()

    def _boot_failed(self, message):
        self.loading_window.destroy()
        messagebox.showerror("VINI - Error", f"No se pudo iniciar la aplicacion:\n{message}")
        self._stop_fuseki()
        self.root.destroy()

    def _update_loading_status(self, message):
        self.root.after(0, lambda: self.loading_status.configure(text=message))

    def _advance_loading_step(self):
        self._loading_step += 1
        progress_value = self._loading_step / self._loading_steps_total
        self.root.after(0, lambda: self.loading_progress.set(progress_value))

    def _confirm_close(self):
        if messagebox.askyesno("VINI - Confirmar", "¿Seguro que quieres cerrar la aplicacion?"):
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
        
        # Verificar si el dataset ya existe
        if self._dataset_exists(dataset_name):
            # Borrarlo
            self._delete_dataset(dataset_name)
            # Esperar a que se complete la eliminación
            time.sleep(1)
        
        # Crear el dataset
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
                # Si sigue en conflicto, esperar y reintentar
                time.sleep(2)
                retry_request = urllib.request.Request(datasets_url, data=data, method="POST")
                try:
                    with urllib.request.urlopen(retry_request, timeout=10) as retry_response:
                        if retry_response.status not in (200, 201):
                            raise RuntimeError(f"No se pudo crear el dataset {dataset_name} en reintento")
                except urllib.error.HTTPError as retry_exc:
                    if retry_exc.code != 409:
                        raise
            else:
                raise

    def _dataset_exists(self, dataset_name):
        """Verifica si un dataset ya existe en Fuseki"""
        datasets_url = f"http://localhost:{self.fuseki_port}/$/datasets"
        try:
            with urllib.request.urlopen(datasets_url, timeout=5) as response:
                payload = response.read().decode("utf-8")
                # Buscar en el JSON de datasets
                return f'"{dataset_name}"' in payload or f"/{dataset_name}" in payload
        except urllib.error.URLError:
            return False

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
        # Crear barra de menú
        self._create_menu_bar()
        
        # Vincular atajos de teclado
        self.root.bind('<Control-q>', lambda e: self._confirm_close())
        
        # Header moderno
        # header = ModernHeader(self.root, title="VINI", subtitle="Consultas de Fútbol")
        # header.pack(fill="x")
        
        # Frame principal
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Crear tabs modernas
        self.notebook = ModernTabview(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Crear pestañas
        self.tab_players = self.notebook.add("Jugadores")
        self.tab_teams = self.notebook.add("Equipos")
        self.tab_games = self.notebook.add("Partidos")
        self.tab_competitions = self.notebook.add("Competiciones")
        self.tab_special = self.notebook.add("Especial")
        self.tab_custom_queries = self.notebook.add("Consultas personalizadas")

        # Configurar pestañas
        self.setup_players_tab()
        self.setup_teams_tab()
        self.setup_games_tab()
        self.setup_competitions_tab()
        self.setup_special_tab()
        self.setup_custom_queries_tab()
        
        # Status bar removido por request del usuario
    
    def _create_menu_bar(self):
        """Crea la barra de menú superior de la aplicación"""
        menubar = tk.Menu(
            self.root,
            bg=Colors.BG_SECONDARY,
            fg=Colors.TEXT_PRIMARY,
            activebackground=Colors.ACCENT_GREEN,
            activeforeground=Colors.PRIMARY_DARK
        )
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Salir (Ctrl+Q)", command=self._confirm_close)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Ayuda General", command=self._show_general_help)
        help_menu.add_command(label="Ayuda de Pestañas", command=self._show_tabs_help)
        help_menu.add_separator()
        help_menu.add_command(label="Acerca de", command=self._show_about)
    
    def _show_general_help(self):
        """Muestra la ventana de ayuda general"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Ayuda - VINI")
        help_window.geometry("700x600")
        try:
            help_window.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono en help_window: {e}")
        
        # Frame con scrollbar
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, 
                             font=("Courier", FontSizes.TEXT_SMALL))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Insertar texto de ayuda
        text_widget.insert(tk.END, get_help_text())
        text_widget.config(state=tk.DISABLED)  # Solo lectura
        
        # Botón cerrar
        btn_frame = ttk.Frame(help_window)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cerrar", command=help_window.destroy).pack()
    
    def _show_tabs_help(self):
        """Muestra la ventana de ayuda de pestañas"""
        tabs_window = tk.Toplevel(self.root)
        tabs_window.title("Ayuda - Pestañas")
        tabs_window.geometry("800x700")
        try:
            tabs_window.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono en tabs_window: {e}")
        
        # Frame con scrollbar
        text_frame = ttk.Frame(tabs_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                             font=("Courier", FontSizes.TEXT_SMALL))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Insertar texto de ayuda
        text_widget.insert(tk.END, get_tabs_help_text())
        text_widget.config(state=tk.DISABLED)  # Solo lectura
        
        # Botón cerrar
        btn_frame = ttk.Frame(tabs_window)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Cerrar", command=tabs_window.destroy).pack()
    
    def _show_about(self):
        """Muestra el diálogo de acerca de"""
        messagebox.showinfo(
            "VINI - Acerca de",
            "VINI - Consultas de Fútbol\nv1.0\n\n"
            "Aplicación de escritorio para consultar datos de fútbol "
            "en un triple store RDF usando SPARQL.\n\n"
            "Usa el menú Ayuda para obtener más información."
        )
    
    def setup_query_tab(self, tab, title, buttons_config, columns=None):
        """Configura una pestaña con botones de consulta usando componentes modernos"""
        if columns is None:
            columns = ["Resultado"]
        
        # Frame principal con scroll
        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Título
        title_label = ModernLabel(scroll_frame, text=title, variant="accent", font=("Segoe UI", FontSizes.TITLE_LARGE, "bold"))
        title_label.pack(anchor="w", pady=(0, 15))
        
        # Frame para botones
        btn_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=0)
        
        for btn_config in buttons_config:
            btn = ModernButton(btn_frame, text=btn_config['name'], variant="primary",
                             command=btn_config['command'])
            btn.pack(side="left", padx=5, pady=5)
        
        # Tabla moderna
        table = ModernTable(scroll_frame, columns=columns)
        table.pack(fill="both", expand=True, pady=10)
        
        # Label para estado
        status_label = ModernLabel(scroll_frame, text="Selecciona una consulta para ejecutar", 
                                  variant="secondary")
        status_label.pack(anchor="w", pady=10)
        
        return table, status_label
    
    def setup_players_tab(self):
        """Configura la pestaña de Jugadores"""
        columns = self.queries["precio_goles"]["columns"]
        buttons_config = [
            {'name': self.queries["precio_goles"]["name"], 'command': lambda: self.execute_query("precio_goles", self.players_tree, self.players_status)},
            {'name': self.queries["masGoles"]["name"], 'command': lambda: self.execute_query("masGoles", self.players_tree, self.players_status)},
            {'name': 'Consulta 3', 'command': self.placeholder_query}
        ]
        self.players_tree, self.players_status = self.setup_query_tab(
            self.tab_players, "Consultas de Jugadores", buttons_config, columns=columns
        )
    
    
    def setup_teams_tab(self):
        """Configura la pestaña de Equipos"""
        columns = self.queries["champions"]["columns"]
        buttons_config = [
            {'name': self.queries["champions"]["name"], 'command': lambda: self.execute_query("champions", self.teams_tree, self.teams_status)},
            {'name': self.queries["eficacia"]["name"], 'command': lambda: self.execute_query("eficacia", self.teams_tree, self.teams_status)},
            {'name': self.queries["formaciones"]["name"], 'command': lambda: self.execute_query("formaciones", self.teams_tree, self.teams_status)},
        ]
        self.teams_tree, self.teams_status = self.setup_query_tab(
            self.tab_teams, "Consultas de Equipos", buttons_config, columns=columns
        )
    
    def setup_games_tab(self):
        """Configura la pestaña de Partidos"""
        columns = ["Partido", "Resultado", "Fecha", "Estadio", "Espectadores"]
        buttons_config = [
            {'name': self.queries["casaVsFuera"]["name"], 'command': lambda: self.execute_query("casaVsFuera", self.games_tree, self.games_status)},
            {'name': self.queries["rojas"]["name"], 'command': lambda: self.execute_query("rojas", self.games_tree, self.games_status)},
            {'name': self.queries["diferencias"]["name"], 'command': lambda: self.execute_query("diferencias", self.games_tree, self.games_status)},
        ]
        self.games_tree, self.games_status = self.setup_query_tab(
            self.tab_games, "Consultas de Partidos", buttons_config, columns=columns
        )
    
    def setup_competitions_tab(self):
        """Configura la pestaña de Competiciones"""
        columns = self.queries["pctgApuestas"]["columns"]
        buttons_config = [
            {'name': 'Consulta 1', 'command': self.placeholder_query},
            {'name': self.queries["pctgApuestas"]["name"], 'command': lambda: self.execute_query("pctgApuestas", self.competitions_tree, self.competitions_status)},
            {'name': self.queries["cambiosGanadores"]["name"], 'command': lambda: self.execute_query("cambiosGanadores", self.competitions_tree, self.competitions_status)}
        ]
        self.competitions_tree, self.competitions_status = self.setup_query_tab(
            self.tab_competitions, "Consultas de Competiciones", buttons_config, columns=columns
        )

    def setup_special_tab(self):
        """Configura la pestaña Especial con búsqueda y funciones avanzadas"""
        scroll_frame = ctk.CTkScrollableFrame(self.tab_special, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title_label = ModernLabel(scroll_frame, text="Consultas Especiales", variant="accent", font=("Segoe UI", FontSizes.TITLE_LARGE, "bold"))
        title_label.pack(anchor="w", pady=(0, 20))
        
        # === SECCIÓN DE EQUIPOS ===
        teams_section = ctk.CTkFrame(scroll_frame, fg_color=Colors.BG_SECONDARY, corner_radius=8)
        teams_section.pack(fill="x", pady=10, padx=5)
        
        teams_title = ModernLabel(teams_section, text="Búsqueda de Equipos", variant="accent", font=("Segoe UI", FontSizes.TITLE_SMALL, "bold"))
        teams_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        selector_frame_teams = ctk.CTkFrame(teams_section, fg_color="transparent")
        selector_frame_teams.pack(pady=10, padx=15, fill="x")
        
        self.team_combobox = ModernCombobox(selector_frame_teams)
        self.team_combobox.set("Escribe el equipo...")
        self.team_combobox.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.team_combobox.bind('<KeyRelease>', self._on_team_search)
        
        button_frame_teams = ctk.CTkFrame(teams_section, fg_color="transparent")
        button_frame_teams.pack(pady=10, padx=15, fill="x")
        
        ModernButton(button_frame_teams, text="Ver Equipaciones", variant="primary",
                    command=self._show_kit_from_combo).pack(side="left", padx=5)
        ModernButton(button_frame_teams, text="Mostrar Plantilla", variant="primary",
                    command=self._show_squad_from_combo).pack(side="left", padx=5)
        
        # === SECCIÓN DE JUGADORES ===
        players_section = ctk.CTkFrame(scroll_frame, fg_color=Colors.BG_SECONDARY, corner_radius=8)
        players_section.pack(fill="x", pady=10, padx=5)
        
        players_title = ModernLabel(players_section, text="Búsqueda de Jugadores", variant="accent", font=("Segoe UI", FontSizes.TITLE_SMALL, "bold"))
        players_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        selector_frame_players = ctk.CTkFrame(players_section, fg_color="transparent")
        selector_frame_players.pack(pady=10, padx=15, fill="x")
        
        self.player_combobox = ModernCombobox(selector_frame_players)
        self.player_combobox.set("Escribe el jugador...")
        self.player_combobox.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.player_combobox.bind('<KeyRelease>', self._on_player_search)
        
        button_frame_players = ctk.CTkFrame(players_section, fg_color="transparent")
        button_frame_players.pack(pady=10, padx=15, fill="x")
        
        ModernButton(button_frame_players, text="Ver Foto", variant="primary",
                    command=self._show_player_photo_from_combo).pack(side="left", padx=5)
        ModernButton(button_frame_players, text="Ver Estadísticas", variant="primary",
                    command=self._show_player_stats_from_combo).pack(side="left", padx=5)
        
        # Estado
        self.special_status = ModernLabel(scroll_frame, text="Cargando datos...", variant="secondary")
        self.special_status.pack(anchor="w", pady=(20, 5))
        
        self.special_loading = ModernLabel(scroll_frame, text="", variant="secondary")
        self.special_loading.pack(anchor="w", pady=(0, 15))
        
        # Frame para la tabla de plantilla
        self.squad_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.squad_frame.pack(fill="both", expand=True, pady=10)

        self._load_teams_combobox()
        self._load_players_combobox()
    
    def setup_custom_queries_tab(self):
        """Configura la pestaña de consultas personalizadas"""
        scroll_frame = ctk.CTkScrollableFrame(self.tab_custom_queries, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        title = ModernLabel(scroll_frame, text="Crear Consulta SPARQL", variant="accent", font=("Segoe UI", FontSizes.TITLE_LARGE, "bold"))
        title.pack(anchor="w", pady=(0, 15))
        
        # Label para la consulta
        label = ModernLabel(scroll_frame, text="Escribe tu consulta SPARQL:", variant="secondary")
        label.pack(anchor="w", pady=(0, 10))
        
        # Frame para el área de texto CON SCROLLBAR
        text_frame = ctk.CTkFrame(scroll_frame, fg_color=Colors.BG_SECONDARY, corner_radius=8, border_width=1, border_color=Colors.BORDER_COLOR)
        text_frame.pack(fill="both", expand=False, pady=10, ipady=50)
        
        # Scrollbar para el área de texto
        text_scrollbar = ttk.Scrollbar(text_frame)
        text_scrollbar.pack(side="right", fill="y")
        
        # Area de texto con scrollbar
        self.query_text = tk.Text(
            text_frame,
            height=10,
            wrap="word",
            bg=Colors.BG_TERTIARY,
            fg=Colors.TEXT_PRIMARY,
            insertbackground=Colors.ACCENT_GREEN,
            font=("Courier", FontSizes.TEXT_SMALL),
            relief="flat",
            border=0,
            yscrollcommand=text_scrollbar.set
        )
        text_scrollbar.config(command=self.query_text.yview)
        self.query_text.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Botón para ejecutar
        self.btn_custom_execute = ModernButton(scroll_frame, text="Ejecutar Consulta", variant="primary",
                                              command=self.execute_custom_query)
        self.btn_custom_execute.pack(pady=15)
        
        # Label para resultados
        result_label = ModernLabel(scroll_frame, text="Resultados:", variant="accent", font=("Segoe UI", FontSizes.TITLE_SMALL, "bold"))
        result_label.pack(anchor="w", pady=(10, 5))
        
        # Frame para tabla con paginación
        table_container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, pady=10)
        
        # Frame para tabla sin paginación (sin scrollbars)
        table_frame = ctk.CTkFrame(table_container, fg_color=Colors.BG_SECONDARY, corner_radius=8, border_width=1, border_color=Colors.BORDER_COLOR)
        table_frame.pack(fill="both", expand=True)
        
        # Treeview sin scrollbars
        self.custom_tree = ttk.Treeview(
            table_frame,
            columns=["Resultado"],
            height=10,
            show="headings"
        )
        
        # Configurar columna inicial
        self.custom_tree.column("Resultado", width=300, anchor="center", stretch=True)
        self.custom_tree.heading("Resultado", text="Resultado")
        
        self.custom_tree.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Vincular evento de redimensionamiento para ajustar columnas
        table_frame.bind("<Configure>", lambda e: self._adjust_custom_tree_columns(e))
        
        # Frame para paginación
        pagination_frame = ctk.CTkFrame(table_container, fg_color="transparent")
        pagination_frame.pack(fill="x", pady=(10, 0))
        
        # Label de información
        self.custom_info_label = ctk.CTkLabel(
            pagination_frame,
            text="",
            font=("Segoe UI", FontSizes.TEXT_SMALL),
            text_color=Colors.TEXT_SECONDARY
        )
        self.custom_info_label.pack(side="left", padx=5)
        
        # Botones de paginación
        btn_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        self.custom_btn_prev = ModernButton(btn_frame, text="← Anterior", variant="secondary",
                                           width=100, height=28)
        self.custom_btn_prev.pack(side="left", padx=5)
        
        self.custom_btn_next = ModernButton(btn_frame, text="Siguiente →", variant="secondary",
                                           width=100, height=28)
        self.custom_btn_next.pack(side="left", padx=5)
    
    def placeholder_query(self):
        """Placeholder para consultas no implementadas"""
        ModernNotification(self.root, message="Esta consulta aún no ha sido implementada", notification_type="info", icon_path=self.icon_path)
    
    def _adjust_custom_tree_columns(self, event):
        """Ajusta el ancho de las columnas de la tabla personalizada cuando se redimensiona"""
        if event.width <= 1:
            return
        
        # Obtener columnas válidas
        try:
            columns = self.custom_tree.cget('columns')
            if not columns or '#all' in str(columns):
                return
            
            # Filtrar solo columnas válidas (evitar pseudo-columnas como '#all')
            valid_columns = [col for col in columns if col and not col.startswith('#')]
            if not valid_columns:
                return
            
            # Calcular ancho disponible
            available_width = event.width
            
            # Distribuir el ancho equitativamente
            column_width = max(50, available_width // len(valid_columns))
            
            # Aplicar ancho a cada columna
            for col in valid_columns:
                self.custom_tree.column(col, width=column_width, anchor="center", stretch=True)
        except Exception:
            pass
    
    def _adjust_custom_tree_columns_deferred(self):
        """Ajusta dinámicamente el ancho de las columnas después de cargar datos"""
        try:
            # Obtener las columnas válidas
            columns = self.custom_tree.cget('columns')
            if not columns or '#all' in str(columns):
                return
            
            # Filtrar solo columnas válidas
            valid_columns = [col for col in columns if col and not col.startswith('#')]
            if not valid_columns:
                return
            
            # Obtener el ancho disponible del widget
            width = self.custom_tree.winfo_width()
            if width <= 1:
                return
            
            # Distribuir el ancho equitativamente
            column_width = max(50, width // len(valid_columns))
            
            # Aplicar ancho a cada columna
            for col in valid_columns:
                self.custom_tree.column(col, width=column_width, anchor="center", stretch=True)
        except Exception:
            pass
    
    
    def execute_custom_query(self):
        """Ejecuta la consulta SPARQL personalizada"""
        query = self.query_text.get("1.0", tk.END).strip()
        
        if not query:
            ModernNotification(self.root, message="Por favor, escribe una consulta SPARQL", notification_type="warning", icon_path=self.icon_path)
            return
        
        self.btn_custom_execute.configure(state="disabled")
        self.root.update()
        
        # Ejecutar en thread separado para no bloquear la UI
        thread = threading.Thread(target=self._fetch_custom_results, args=(query,))
        thread.start()
    
    def execute_query(self, query_key, table, status_label):
        """Ejecuta una consulta parametrizada"""
        # Obtener columnas de la consulta
        query_columns = self.queries[query_key]["columns"]
        
        # Limpiar todos los items del treeview primero
        for item in table.tree.get_children():
            table.tree.delete(item)
        
        # Desregistrar columnas antiguas estableciendo displaycolumns vacío
        table.tree.configure(displaycolumns=())
        
        # Ahora configurar las nuevas columnas
        table.columns = list(query_columns)
        table.visible_columns = list(query_columns)
        table.tree.configure(columns=tuple(query_columns))
        
        # Configurar headers de las nuevas columnas
        for col in query_columns:
            table.tree.column(col, width=120, anchor="center", stretch=True)
            table.tree.heading(col, text=col)
        
        # Establecer las nuevas columnas como visibles
        table.tree.configure(displaycolumns=tuple(query_columns))
        
        # Limpiar la tabla
        table.clear()
        
        status_label.configure(text="Ejecutando consulta...", text_color=Colors.TEXT_SECONDARY)
        self.root.update()
        
        thread = threading.Thread(
            target=self._fetch_query_results,
            args=(query_key, table, status_label)
        )
        thread.start()
    
    def _fetch_query_results(self, query_key, table, status_label):
        """Obtiene los resultados de una consulta parametrizada"""
        try:
            query_info = self.queries[query_key]
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(SPARQL_QUERIES[query_key])
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Preparar datos para ModernTable
            data = []
            
            if results['results']['bindings']:
                for binding in results['results']['bindings']:
                    row = []
                    for var in query_info["vars"]:
                        value = binding.get(var, {}).get('value', 'N/A')
                        row.append(value)
                    data.append(row)
                
                # Actualizar tabla
                def update_ui():
                    table.set_data(data)
                    status_label.configure(
                        text=f"Se cargaron {len(data)} resultados",
                        text_color=Colors.ACCENT_GREEN
                    )
                
                self.root.after(0, update_ui)
            else:
                def update_ui():
                    table.clear()
                    status_label.configure(text="No se encontraron resultados", text_color=Colors.ACCENT_GREEN)
                
                self.root.after(0, update_ui)
        
        except Exception as e:
            def update_ui():
                status_label.configure(text=f"Error: {str(e)}", text_color=Colors.ACCENT_RED)
                ModernNotification(self.root, message=f"Error: {str(e)}", notification_type="error", icon_path=self.icon_path)
            
            self.root.after(0, update_ui)
    
    def _fetch_custom_results(self, query):
        """Obtiene los resultados de una consulta personalizada (en thread)"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()
            
            # Obtener variables de la consulta
            if results['results']['bindings']:
                bindings = results['results']['bindings']
                variables = list(bindings[0].keys())
                
                # Preparar datos
                data = []
                for binding in bindings:
                    row = []
                    for var in variables:
                        value = binding.get(var, {}).get('value', 'N/A')
                        row.append(value)
                    data.append(row)
                
                # Actualizar tabla con paginación
                def update_ui():
                    # Limpiar tabla anterior
                    for item in self.custom_tree.get_children():
                        self.custom_tree.delete(item)
                    
                    # Configurar columnas dinámicamente
                    self.custom_tree.configure(columns=tuple(variables))
                    for col in variables:
                        self.custom_tree.column(col, width=150, anchor="center", stretch=True)
                        self.custom_tree.heading(col, text=col)
                    
                    # Inicializar estado de paginación
                    if not hasattr(self, 'custom_pagination'):
                        self.custom_pagination = {}
                    self.custom_pagination['current'] = {
                        'current_page': 0,
                        'rows_per_page': 10,
                        'data': data,
                        'variables': variables
                    }
                    
                    # Mostrar primera página
                    self._refresh_custom_display()
                    
                    # Conectar botones
                    self.custom_btn_prev.configure(command=self._custom_prev_page)
                    self.custom_btn_next.configure(command=self._custom_next_page)
                    
                    self.btn_custom_execute.configure(state="normal")
                    
                    # Ajustar columnas automáticamente
                    self.root.after(10, self._adjust_custom_tree_columns_deferred)
                
                self.root.after(0, update_ui)
            else:
                def update_ui():
                    for item in self.custom_tree.get_children():
                        self.custom_tree.delete(item)
                    self.custom_info_label.configure(text="No hay resultados", text_color=Colors.TEXT_SECONDARY)
                    self.custom_btn_prev.configure(state="disabled")
                    self.custom_btn_next.configure(state="disabled")
                    self.btn_custom_execute.configure(state="normal")
                
                self.root.after(0, update_ui)
        
        except Exception as e:
            error_msg = str(e)
            def update_ui():
                for item in self.custom_tree.get_children():
                    self.custom_tree.delete(item)
                self.custom_info_label.configure(text=f"Error: {error_msg}", text_color=Colors.ACCENT_RED)
                self.custom_btn_prev.configure(state="disabled")
                self.custom_btn_next.configure(state="disabled")
                self.btn_custom_execute.configure(state="normal")
                ModernNotification(self.root, message=f"Error: {error_msg}", notification_type="error", icon_path=self.icon_path)
            
            self.root.after(0, update_ui)
    
    def _refresh_custom_display(self):
        """Actualiza la visualización de la tabla de consultas personalizadas"""
        if not hasattr(self, 'custom_pagination') or 'current' not in self.custom_pagination:
            return
        
        state = self.custom_pagination['current']
        data = state['data']
        
        # Limpiar tabla
        for item in self.custom_tree.get_children():
            self.custom_tree.delete(item)
        
        # Calcular página actual
        start = state['current_page'] * state['rows_per_page']
        end = start + state['rows_per_page']
        
        # Agregar datos de la página actual
        for row in data[start:end]:
            self.custom_tree.insert('', 'end', values=row)
        
        # Actualizar información y botones
        total_pages = (len(data) + state['rows_per_page'] - 1) // state['rows_per_page']
        page_display = f"Página {state['current_page'] + 1} de {max(1, total_pages)} ({len(data)} resultados)"
        self.custom_info_label.configure(text=page_display)
        
        self.custom_btn_prev.configure(state="normal" if state['current_page'] > 0 else "disabled")
        self.custom_btn_next.configure(state="normal" if state['current_page'] < total_pages - 1 else "disabled")
    
    def _custom_prev_page(self):
        """Navega a la página anterior en consultas personalizadas"""
        if not hasattr(self, 'custom_pagination') or 'current' not in self.custom_pagination:
            return
        
        state = self.custom_pagination['current']
        if state['current_page'] > 0:
            state['current_page'] -= 1
            self._refresh_custom_display()
    
    def _custom_next_page(self):
        """Navega a la página siguiente en consultas personalizadas"""
        if not hasattr(self, 'custom_pagination') or 'current' not in self.custom_pagination:
            return
        
        state = self.custom_pagination['current']
        data = state['data']
        total_pages = (len(data) + state['rows_per_page'] - 1) // state['rows_per_page']
        
        if state['current_page'] < total_pages - 1:
            state['current_page'] += 1
            self._refresh_custom_display()
    
    def _load_teams_combobox(self):
        """Carga la lista de equipos en el combobox"""
        self.special_status.configure(text="Cargando equipos...", text_color=Colors.TEXT_SECONDARY)
        self.special_loading.configure(text="Obteniendo datos de la base de datos...")
        self.root.update()
        
        thread = threading.Thread(target=self._fetch_teams_for_combobox)
        thread.start()
    
    def _fetch_teams_for_combobox(self):
        """Obtiene todos los equipos y años disponibles"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(FETCH_TEAMS_QUERY)
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
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message="No se encontraron equipos en la base de datos",
                    notification_type="warning",
                    icon_path=self.icon_path
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="No hay equipos disponibles",
                    text_color=Colors.ACCENT_GREEN
                ))
        
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error cargando equipos:\n{str(e)}",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.configure(text=""))
    
    def _update_combobox_items(self, items):
        """Actualiza los items del combobox"""
        self.all_teams = items  # Guardar lista completa para búsqueda
        self.team_combobox.configure(values=items)
        self.team_combobox.set("Escribe el equipo...")
        self.special_status.configure(
            text=f"Se cargaron {len(items)} equipos. Escribe para buscar o selecciona uno para ver equipaciones.",
            text_color=Colors.ACCENT_GREEN
        )
    
    def _load_players_combobox(self):
        """Carga la lista de jugadores en el combobox"""
        thread = threading.Thread(target=self._fetch_players_for_combobox)
        thread.start()
    
    def _fetch_players_for_combobox(self):
        """Obtiene todos los jugadores disponibles por año"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(FETCH_PLAYERS_QUERY)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            if results['results']['bindings']:
                players_data = []
                player_items = []
                
                for binding in results['results']['bindings']:
                    player_name = binding.get('playerName', {}).get('value', 'N/A')
                    year = binding.get('year', {}).get('value', 'N/A')
                    url = binding.get('url', {}).get('value', 'N/A')
                    
                    display_text = f"{player_name} - {year}"
                    player_items.append(display_text)
                    players_data.append({
                        'name': player_name,
                        'year': year,
                        'url': url,
                        'display': display_text
                    })
                
                self.players_data = players_data
                self.root.after(0, lambda: self._update_player_combobox_items(player_items))
            else:
                self.root.after(0, lambda: self.special_status.configure(
                    text="No se encontraron jugadores en la base de datos",
                    text_color=Colors.ACCENT_GREEN
                ))
        
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error cargando jugadores:\n{str(e)}",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
    
    def _update_player_combobox_items(self, items):
        """Actualiza los items del combobox de jugadores"""
        self.all_players = items  # Guardar lista completa para búsqueda
        self.player_combobox.configure(values=items)
        self.player_combobox.set("Escribe el jugador...")
        self.special_status.configure(
            text=f"Se cargaron {len(items)} jugadores por temporada. Escribe para buscar o selecciona uno para ver su foto.",
            text_color=Colors.ACCENT_GREEN
        )
    
    def _on_player_search(self, event):
        """Filtra jugadores mientras se escribe en el combobox"""
        # Ignorar eventos de navegación (flechas, rueda, page, etc)
        if event.keysym in ('Down', 'Up', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End', 'MouseWheel'):
            return
        
        search_text = self.player_combobox.get().lower()
        placeholder = "escribe el jugador..."
        
        if not hasattr(self, 'all_players'):
            return
        
        # Si es el placeholder, mostrar todos
        if search_text == placeholder:
            self.player_combobox.configure(values=self.all_players)
            return
        
        # Si está vacío o es placeholder, limpiar placeholder y mostrar todos
        if not search_text or search_text == placeholder:
            self.player_combobox.set("")
            self.player_combobox.configure(values=self.all_players)
            return
        
        # Filtrar jugadores que coincidan con el texto
        filtered_players = [player for player in self.all_players 
                          if search_text in player.lower()]
        
        # Actualizar combobox con jugadores filtrados
        self.player_combobox.configure(values=filtered_players)

    def _on_team_search(self, event):
        """Filtra equipos mientras se escribe en el combobox"""
        # Ignorar eventos de navegación (flechas, rueda, page, etc)
        if event.keysym in ('Down', 'Up', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End', 'MouseWheel'):
            return
        
        search_text = self.team_combobox.get().lower()
        placeholder = "escribe el equipo..."
        
        if not hasattr(self, 'all_teams'):
            return
        
        # Si es el placeholder, mostrar todos
        if search_text == placeholder:
            self.team_combobox.configure(values=self.all_teams)
            return
        
        # Si está vacío o es placeholder, limpiar placeholder y mostrar todos
        if not search_text or search_text == placeholder:
            self.team_combobox.set("")
            self.team_combobox.configure(values=self.all_teams)
            return
        
        # Filtrar equipos que coincidan con el texto
        filtered_teams = [team for team in self.all_teams 
                        if search_text in team.lower()]
        
        # Actualizar combobox con equipos filtrados
        self.team_combobox.configure(values=filtered_teams)
    
    def _on_team_selected(self, event):
        """Evento cuando se selecciona un equipo del combobox (ahora sin acción automática)"""
        pass
    
    def _show_kit_from_combo(self):
        """Muestra equipaciones del equipo seleccionado en el combobox"""
        selected_text = self.team_combobox.get()
        placeholder = "Escribe el equipo..."
        
        if not selected_text or selected_text == placeholder or not hasattr(self, 'teams_data'):
            ModernNotification(self.root, message="Por favor selecciona un equipo del desplegable", notification_type="warning", icon_path=self.icon_path)
            return
        
        # Buscar el equipo en teams_data por el texto seleccionado
        team_info = None
        for team in self.teams_data:
            if team['display'] == selected_text:
                team_info = team
                break
        
        if team_info is None:
            ModernNotification(self.root, message="Equipo no encontrado. Selecciona uno del desplegable.", notification_type="warning", icon_path=self.icon_path)
            return
        
        self.special_status.configure(text="Descargando equipaciones...", text_color=Colors.TEXT_SECONDARY)
        self.special_loading.configure(text="Obteniendo imagen...")
        self.root.update()
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._fetch_and_show_kit,
            args=(team_info['url'], team_info['team_name'])
        )
        thread.start()
    
    def _show_squad_from_combo(self):
        """Muestra la plantilla del equipo seleccionado en el combobox"""
        selected_text = self.team_combobox.get()
        placeholder = "Escribe el equipo..."
        
        if not selected_text or selected_text == placeholder or not hasattr(self, 'teams_data'):
            ModernNotification(self.root, message="Por favor selecciona un equipo del desplegable", notification_type="warning", icon_path=self.icon_path)
            return
        
        # Buscar el equipo en teams_data por el texto seleccionado
        team_info = None
        for team in self.teams_data:
            if team['display'] == selected_text:
                team_info = team
                break
        
        if team_info is None:
            ModernNotification(self.root, message="Equipo no encontrado. Selecciona uno del desplegable.", notification_type="warning", icon_path=self.icon_path)
            return
        
        self.special_status.configure(text="Cargando plantilla...", text_color=Colors.TEXT_SECONDARY)
        self.special_loading.configure(text="Obteniendo datos...")
        self.root.update()
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._fetch_squad_for_team,
            args=(team_info['team_name'], team_info['year'])
        )
        thread.start()
    
    def _show_player_stats_from_combo(self):
        """Muestra las estadísticas del jugador seleccionado en el combobox"""
        selected_text = self.player_combobox.get()
        placeholder = "Escribe el jugador..."
        
        if not selected_text or selected_text == placeholder or not hasattr(self, 'players_data'):
            ModernNotification(self.root, message="Por favor selecciona un jugador del desplegable", notification_type="warning", icon_path=self.icon_path)
            return
        
        # Buscar el jugador en players_data por el texto seleccionado
        player_info = None
        for player in self.players_data:
            if player['display'] == selected_text:
                player_info = player
                break
        
        if player_info is None:
            ModernNotification(self.root, message="Jugador no encontrado. Selecciona uno del desplegable.", notification_type="warning", icon_path=self.icon_path)
            return
        
        self.special_status.configure(text="Cargando estadísticas...", text_color=Colors.TEXT_SECONDARY)
        self.special_loading.configure(text="Obteniendo datos del jugador...")
        self.root.update()
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._fetch_stats_for_player,
            args=(player_info['url'], player_info['name'])
        )
        thread.start()

    def _fetch_stats_for_player(self, url, player_name):
        """Obtiene las estadísticas del jugador desde el grafo SPARQL"""
        try:
            self.special_status.configure(text="Obteniendo estadísticas desde el grafo...", text_color=Colors.TEXT_SECONDARY)
            self.root.update()
            
            # Obtener estadísticas desde SPARQL
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(get_player_stats_query(player_name))
            sparql.setReturnFormat(JSON)
            
            results = sparql.query().convert()

            
            if results['results']['bindings']:
                # Procesar resultados SPARQL
                stats = self._extract_player_stats_from_sparql(results['results']['bindings'], player_name)
                
                # Mostrar en la UI
                self.root.after(0, lambda: self._display_player_stats(stats, player_name))
                self.root.after(0, lambda: self.special_status.configure(
                    text=f"Estadísticas de {player_name} cargadas",
                    text_color=Colors.ACCENT_GREEN
                ))
            else:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"No se encontraron estadísticas para {player_name}",
                    notification_type="warning",
                    icon_path=self.icon_path
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="Sin estadísticas disponibles",
                    text_color=Colors.ACCENT_ORANGE
                ))
        
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error obteniendo estadísticas:\n{str(e)}",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.configure(text=""))
    
    def _extract_player_stats_from_sparql(self, bindings, player_name):
        """Extrae las estadísticas del jugador desde los resultados de SPARQL"""
        stats = {
            'name': player_name,
            'overall': 'N/A',
            'potential': 'N/A',
            'age': 'N/A',
            'position': 'N/A',
            'year': 'N/A',
            'value': 'N/A',
            'wage': 'N/A',
            'attributes': {}
        }
        
        try:
            # Procesar el primer resultado (temporada más reciente)
            if bindings:
                binding = bindings[0]
                
                # Extraer datos principales
                stats['year'] = binding.get('year', {}).get('value', 'N/A')
                stats['overall'] = binding.get('overall_rating', {}).get('value', 'N/A')
                stats['potential'] = binding.get('potential', {}).get('value', 'N/A')
                stats['age'] = binding.get('age', {}).get('value', 'N/A')
                stats['position'] = binding.get('position', {}).get('value', 'N/A')
                stats['value'] = binding.get('value', {}).get('value', 'N/A')
                stats['wage'] = binding.get('wage', {}).get('value', 'N/A')
                
                # Extraer atributos detallados
                attribute_keys = [
                    'total_attacking', 'total_skill', 'total_movement', 'total_goalkeeping',
                    'total_stats', 'weak_foot', 'skill_moves', 'international_reputation',
                    'attacking_work_rate', 'defensive_work_rate', 'body_type', 'real_face',
                    'height', 'weight', 'best_overall', 'best_position', 'growth',
                    'joined', 'loan_date_end', 'release_clause', 'club_kit_number',
                    'physical_positioning', 'base_stats'
                ]

                for attr_key in attribute_keys:
                    value = binding.get(attr_key, {}).get('value', None)
                    if value:
                        # Convertir snake_case a Title Case
                        attr_name = attr_key.replace('_', ' ').title()
                        stats['attributes'][attr_name] = value
        
        except Exception as e:
            print(f"Error procesando estadísticas SPARQL: {e}")
        
        return stats

    def _display_player_stats(self, stats, player_name):
        """Muestra las estadísticas del jugador en una tabla similar a la plantilla en el squad_frame"""
        # Limpiar frame anterior
        for widget in self.squad_frame.winfo_children():
            widget.destroy()
        
        # Preparar datos para la tabla
        all_stats = []
        
        # Agregar estadísticas principales
        main_stats_list = [
            ('Overall', stats.get('overall', 'N/A')),
            ('Potential', stats.get('potential', 'N/A')),
            ('Temporada', stats.get('year', 'N/A')),
            ('Edad', stats.get('age', 'N/A')),
            ('Posición', stats.get('position', 'N/A')),
            ('Valor', stats.get('value', 'N/A')),
            ('Salario', stats.get('wage', 'N/A')),
        ]
        all_stats.extend(main_stats_list)
        
        # Agregar atributos detallados
        if stats.get('attributes'):
            for attr_name, attr_value in stats['attributes'].items():
                all_stats.append((attr_name, str(attr_value)))
        
        # Inicializar estado de paginación
        pagination_key = f"stats_{player_name}"
        if not hasattr(self, 'stats_pagination'):
            self.stats_pagination = {}
        self.stats_pagination[pagination_key] = {
            'current_page': 0,
            'rows_per_page': 10,
            'data': all_stats
        }
        
        # Título
        # title_frame = ctk.CTkFrame(self.squad_frame, fg_color="transparent")
        # title_frame.pack(fill="x", pady=(0, 10))  
        
        # Frame para la tabla
        table_frame = ctk.CTkFrame(self.squad_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)
        
        # Crear tabla
        columns = ("Estadística", "Valor")
        stats_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            height=10,
            show="headings"
        )
        
        # Configurar columnas
        stats_tree.column('#0', width=0, stretch=tk.NO)
        stats_tree.column("Estadística", width=400, anchor="center", stretch=True)
        stats_tree.column("Valor", width=150, anchor="center", stretch=True)
        
        stats_tree.heading("Estadística", text="Estadística")
        stats_tree.heading("Valor", text="Valor")
        
        stats_tree.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Vincular evento de redimensionamiento
        table_frame.bind("<Configure>", lambda e: self._adjust_stats_tree_columns(e, stats_tree))
        
        # Frame para paginación
        pagination_frame = ctk.CTkFrame(self.squad_frame, fg_color="transparent")
        pagination_frame.pack(fill="x", pady=(10, 0))
        
        # Label de información
        info_label = ctk.CTkLabel(
            pagination_frame,
            text="",
            font=("Segoe UI", FontSizes.TEXT_SMALL),
            text_color=Colors.TEXT_SECONDARY
        )
        info_label.pack(side="left", padx=5)
        
        # Botones de paginación
        btn_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        btn_prev = ModernButton(btn_frame, text="← Anterior", variant="secondary",
                               width=100, height=28)
        btn_prev.pack(side="left", padx=5)
        
        btn_next = ModernButton(btn_frame, text="Siguiente →", variant="secondary",
                               width=100, height=28)
        btn_next.pack(side="left", padx=5)
        
        # Función para actualizar la tabla
        def refresh_stats_display():
            state = self.stats_pagination[pagination_key]
            data = state['data']
            
            # Limpiar tabla
            for item in stats_tree.get_children():
                stats_tree.delete(item)
            
            # Calcular página actual
            start = state['current_page'] * state['rows_per_page']
            end = start + state['rows_per_page']
            
            # Agregar datos de la página actual
            for stat_name, stat_value in data[start:end]:
                stats_tree.insert("", "end", values=(stat_name, stat_value))
            
            # Actualizar información y botones
            total_pages = (len(data) + state['rows_per_page'] - 1) // state['rows_per_page']
            page_display = f"Página {state['current_page'] + 1} de {max(1, total_pages)} ({len(data)} estadísticas)"
            info_label.configure(text=page_display)
            
            btn_prev.configure(state="normal" if state['current_page'] > 0 else "disabled")
            btn_next.configure(state="normal" if state['current_page'] < total_pages - 1 else "disabled")
        
        # Funciones para navegación
        def prev_page():
            state = self.stats_pagination[pagination_key]
            if state['current_page'] > 0:
                state['current_page'] -= 1
                refresh_stats_display()
        
        def next_page():
            state = self.stats_pagination[pagination_key]
            data = state['data']
            total_pages = (len(data) + state['rows_per_page'] - 1) // state['rows_per_page']
            
            if state['current_page'] < total_pages - 1:
                state['current_page'] += 1
                refresh_stats_display()
        
        # Vincular botones
        btn_prev.configure(command=prev_page)
        btn_next.configure(command=next_page)
        
        # Mostrar primera página
        refresh_stats_display()
    
    def _adjust_stats_tree_columns(self, event, stats_tree):
        """Ajusta dinámicamente el ancho de las columnas de la tabla de estadísticas"""
        if event.width <= 1:
            return
        
        try:
            # Calcular ancho disponible
            available_width = event.width - 10  # Restar margen
            
            # Distribuir: 60% para estadística, 40% para valor
            col_stat_width = int(available_width * 0.6)
            col_value_width = int(available_width * 0.4)
            
            # Aplicar anchos
            stats_tree.column("Estadística", width=col_stat_width)
            stats_tree.column("Valor", width=col_value_width)
        except Exception:
            pass


    def _show_player_photo_from_combo(self):
        """Muestra la foto del jugador seleccionado en el combobox"""
        selected_text = self.player_combobox.get()
        placeholder = "Escribe el jugador..."
        
        if not selected_text or selected_text == placeholder or not hasattr(self, 'players_data'):
            ModernNotification(self.root, message="Por favor selecciona un jugador del desplegable", notification_type="warning", icon_path=self.icon_path)
            return
        
        # Buscar el jugador en players_data por el display seleccionado
        player_info = None
        for player in self.players_data:
            if player['display'] == selected_text:
                player_info = player
                break
        
        if player_info is None:
            ModernNotification(self.root, message="Jugador no encontrado. Selecciona uno del desplegable.", notification_type="warning", icon_path=self.icon_path)
            return
        
        self.special_status.configure(text="Descargando foto del jugador...", text_color=Colors.TEXT_SECONDARY)
        self.special_loading.configure(text="Obteniendo imagen...")
        self.root.update()
        
        # Ejecutar en thread separado
        thread = threading.Thread(
            target=self._fetch_and_show_player_photo,
            args=(player_info['url'], player_info['name'])
        )
        thread.start()
    
    def _fetch_and_show_player_photo(self, url, player_name):
        """Descarga la foto del jugador desde su URL en Sofifa"""
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
            
            # Parsear HTML con BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar foto del jugador - buscar todas las imágenes de tipo "player"
            photo_url = None
            
            # Buscar todas las imágenes en la página
            all_imgs = soup.find_all('img')
            
            for img in all_imgs:
                # Buscar imágenes con data-type="player" (son las fotos del jugador)
                data_type = img.get('data-type')
                
                if data_type == 'player':
                    # Preferir srcset/data-srcset para obtener la resolución más grande
                    srcset = img.get('srcset') or img.get('data-srcset')
                    
                    if srcset:
                        # Formato: "url1 1x, url2 2x, url3 3x"
                        # Extraer la última URL (generalmente 3x, la más grande)
                        urls_parts = srcset.split(',')
                        largest_entry = urls_parts[-1].strip()  # "url 3x"
                        photo_url = largest_entry.split()[0]  # Extraer solo la URL
                        break
                    else:
                        # Si no hay srcset, usar data-src o src
                        photo_url = img.get('data-src') or img.get('src')
                        if photo_url:
                            # Intentar cambiar el tamaño a la resolución más alta (360)
                            photo_url = photo_url.replace('_120', '_360').replace('_240', '_360')
                            break
            
            if not photo_url:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"No se encontró foto para {player_name}.",
                    notification_type="warning",
                    icon_path=self.icon_path
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="No se encontró foto del jugador",
                    text_color=Colors.ACCENT_GREEN
                ))
                return
            
            # Descargar la imagen
            try:
                # Asegurar que la URL sea absoluta
                if photo_url.startswith('/'):
                    base_url = 'https://sofifa.com'
                    photo_url = base_url + photo_url
                elif not photo_url.startswith('http'):
                    photo_url = 'https://sofifa.com/' + photo_url
                
                # Descargar imagen con headers
                img_req = urllib.request.Request(photo_url, headers=headers)
                with urllib.request.urlopen(img_req, timeout=10) as img_response:
                    img_data = img_response.read()
                
                # Descomprimir imagen si está comprimida con gzip
                if img_data[:2] == b'\x1f\x8b':
                    img_data = gzip.decompress(img_data)
                
                # Procesar imagen con PIL
                img = Image.open(BytesIO(img_data))
                
                # Mostrar en nueva ventana
                self.root.after(0, lambda: self._display_player_photo(img, player_name))
                self.root.after(0, lambda: self.special_status.configure(
                    text=f"Foto de {player_name} cargada correctamente",
                    text_color=Colors.ACCENT_GREEN
                ))
            
            except Exception as photo_error:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"Error descargando la foto de {player_name}:\n{str(photo_error)}",
                    notification_type="error"
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="Error descargando foto",
                    text_color=Colors.ACCENT_RED
                ))
            
            self.root.after(0, lambda: self.special_loading.configure(text=""))
        
        except urllib.error.HTTPError as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error {e.code} al descargar foto:\n{e.reason}\n\nSofifa puede requerir verificación.",
                notification_type="error"
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error HTTP {e.code}",
                text_color=Colors.ACCENT_RED
            ))
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error descargando foto:\n{str(e)}",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.configure(text=""))
    
    def _display_player_photo(self, img, player_name):
        """Muestra la foto del jugador en una nueva ventana"""
        photo_window = tk.Toplevel(self.root)
        photo_window.title(f"Foto - {player_name}")
        try:
            photo_window.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono en photo_window: {e}")
        
        # Redimensionar imagen si es muy grande
        max_width = 600
        max_height = 500
        img_copy = img.copy()
        img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convertir a PhotoImage
        photo = ImageTk.PhotoImage(img_copy)
        
        # Frame para imagen
        img_frame = ttk.Frame(photo_window)
        img_frame.pack(padx=10, pady=10)
        
        # Mostrar imagen
        label = tk.Label(img_frame, image=photo)
        label.image = photo  # Mantener referencia
        label.pack()
        
        # Frame para nombre del jugador
        info_frame = ttk.Frame(photo_window)
        info_frame.pack(padx=10, pady=10)
        
        info_label = ttk.Label(info_frame, text=player_name, font=("Arial", FontSizes.TITLE_SMALL, "bold"))
        info_label.pack()
        
        photo_window.geometry(f"{img_copy.width + 20}x{img_copy.height + 60}")

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
            
            # Parsear HTML con BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar imágenes de equipaciones de forma robusta
            img_urls = []
            
            # Método 1: Buscar en contenedores con clase "kit" o "uniform"
            kit_containers = soup.find_all(['div', 'section'], class_=lambda x: x and any(
                k in (x.lower() if isinstance(x, str) else ' '.join(x)) 
                for k in ['kit', 'uniform', 'jersey', 'shirt', 'equipment']
            ))
            
            for container in kit_containers:
                imgs = container.find_all('img')
                for img in imgs:
                    src = img.get('src') or img.get('data-src')
                    if src and src not in img_urls:
                        img_urls.append(src)
            
            # Método 2: Si no encontró, buscar en aside (parte lateral de la página)
            if not img_urls:
                asides = soup.find_all('aside')
                for aside in asides:
                    imgs = aside.find_all('img')
                    for img in imgs:
                        src = img.get('src') or img.get('data-src')
                        alt = img.get('alt', '').lower()
                        
                        # Filtrar imágenes que parezcan uniformes/equipaciones
                        if src and src not in img_urls:
                            # Aceptar si tiene "kit" en URL/alt o tamaño razonable
                            width = img.get('width')
                            height = img.get('height')
                            is_reasonable_size = (width and 30 < int(width) < 500) or (height and 30 < int(height) < 500)
                            is_kit_related = 'kit' in (src.lower() + alt)
                            
                            if is_kit_related or is_reasonable_size:
                                img_urls.append(src)
            
            # Método 3: Si aún no encontró, buscar todas las imágenes en el main content
            # y filtrar las que parezcan ser uniformes
            if not img_urls:
                main_content = soup.find('main')
                if not main_content:
                    main_content = soup.find('article')
                
                if main_content:
                    all_imgs = main_content.find_all('img')
                    for img in all_imgs:
                        src = img.get('src') or img.get('data-src')
                        alt = img.get('alt', '').lower()
                        parent_class = ' '.join(img.parent.get('class', []))
                        
                        if src and src not in img_urls:
                            # Ser más permisivo en esta búsqueda final
                            width = img.get('width')
                            height = img.get('height')
                            
                            # Evitar logos y pequeños gráficos
                            is_large = (width and int(width) > 40) or (height and int(height) > 40)
                            not_small_logo = not ('logo' in alt or 'icon' in alt)
                            
                            if is_large and not_small_logo:
                                img_urls.append(src)
            
            if not img_urls:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"No se encontraron equipaciones para {team_name}.\n\nPrueba visitando directamente:\n{url}",
                    notification_type="warning",
                    icon_path=self.icon_path
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="No se encontraron equipaciones",
                    text_color=Colors.ACCENT_GREEN
                ))
                return
            
            # Descargar todas las imágenes encontradas
            images_data = []
            for img_url in img_urls:
                try:
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
                    images_data.append(img)
                except Exception as kit_error:
                    print(f"Error descargando imagen {img_url}: {kit_error}")
                    continue
            
            if images_data:
                # Mostrar en nueva ventana con galería
                self.root.after(0, lambda: self._display_kit_gallery(images_data, team_name))
                self.root.after(0, lambda: self.special_status.configure(
                    text=f"Se encontraron {len(images_data)} equipaciones de {team_name}",
                    text_color=Colors.ACCENT_GREEN
                ))
            else:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"No se pudieron descargar las equipaciones para {team_name}.",
                    notification_type="warning"
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="Error descargando equipaciones",
                    text_color=Colors.ACCENT_GREEN
                ))
            
            self.root.after(0, lambda: self.special_loading.configure(text=""))
        
        except urllib.error.HTTPError as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error {e.code} al descargar equipaciones:\n{e.reason}\n\nSofifa puede requerir verificación.",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error HTTP {e.code}",
                text_color=Colors.ACCENT_RED
            ))
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error descargando equipaciones:\n{str(e)}",
                notification_type="error",
                icon_path=self.icon_path
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.configure(text=""))
    
    def _fetch_squad_for_team(self, team_name, year):
        """Obtiene la plantilla de un equipo para una temporada específica"""
        try:
            sparql = SPARQLWrapper(self.sparql_endpoint)
            sparql.setQuery(get_squad_query(team_name, year))
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            if results['results']['bindings']:
                players_data = []
                for binding in results['results']['bindings']:
                    player = {
                        'name': binding.get('name', {}).get('value', 'N/A'),
                        'position': binding.get('position', {}).get('value', 'N/A'),
                        'overall': binding.get('overall', {}).get('value', 'N/A'),
                        'age': binding.get('age', {}).get('value', 'N/A'),
                        'potential': binding.get('potential', {}).get('value', 'N/A'),
                        'value': binding.get('value', {}).get('value', 'N/A'),
                        'wage': binding.get('wage', {}).get('value', 'N/A'),
                        'kit_number': binding.get('club_kit_number', {}).get('value', 'N/A'),
                    }
                    players_data.append(player)
                
                self.root.after(0, lambda: self._display_squad_table(players_data, team_name, year))
                self.root.after(0, lambda: self.special_status.configure(
                    text=f"Plantilla de {team_name} ({year}): {len(players_data)} jugadores",
                    text_color=Colors.ACCENT_GREEN
                ))
            else:
                self.root.after(0, lambda: ModernNotification(
                    self.root,
                    message=f"No se encontraron jugadores para {team_name} en {year}.",
                    notification_type="warning"
                ))
                self.root.after(0, lambda: self.special_status.configure(
                    text="No hay datos de plantilla",
                    text_color=Colors.ACCENT_GREEN
                ))
        
        except Exception as e:
            self.root.after(0, lambda: ModernNotification(
                self.root,
                message=f"Error cargando plantilla:\n{str(e)}",
                notification_type="error"
            ))
            self.root.after(0, lambda: self.special_status.configure(
                text=f"Error: {str(e)}",
                text_color=Colors.ACCENT_RED
            ))
        
        finally:
            self.root.after(0, lambda: self.special_loading.configure(text=""))

    
    def _display_squad_table(self, players_data, team_name, year):
        """Muestra la plantilla en una tabla con paginación"""
        # Limpiar frame anterior
        for widget in self.squad_frame.winfo_children():
            widget.destroy()
        
        # Inicializar estado de paginación
        pagination_key = f"{team_name}_{year}"
        if not hasattr(self, 'squad_pagination'):
            self.squad_pagination = {}
        self.squad_pagination[pagination_key] = {
            'current_page': 0,
            'rows_per_page': 10,
            'data': players_data
        }
        
        # Frame para la tabla
        table_frame = ctk.CTkFrame(self.squad_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)
        
        # Crear tabla SIN scrollbars (usa el scroll del contenedor principal)
        columns = ("Nombre", "Posición", "Overall", "Edad", "Potencial", "Valor", "Salario", "Dorsal")
        squad_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            height=10,
            show="headings"
        )
        
        # Configurar columnas con contenido CENTRADO
        squad_tree.column('#0', width=0, stretch=tk.NO)
        for i, col in enumerate(columns):
            squad_tree.column(col, anchor="center", width=120, stretch=True)
            squad_tree.heading(col, text=col, anchor="center")
        
        squad_tree.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Vincular evento de redimensionamiento para ajustar columnas dinámicamente
        table_frame.bind("<Configure>", lambda e: self._adjust_squad_tree_columns(e, squad_tree))
        
        # Frame para paginación
        pagination_frame = ctk.CTkFrame(self.squad_frame, fg_color="transparent")
        pagination_frame.pack(fill="x", pady=(10, 0))
        
        # Label de información
        info_label = ctk.CTkLabel(
            pagination_frame,
            text="",
            font=("Segoe UI", FontSizes.TEXT_SMALL),
            text_color=Colors.TEXT_SECONDARY
        )
        info_label.pack(side="left", padx=5)
        
        # Botones de paginación
        btn_frame = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        btn_prev = ModernButton(btn_frame, text="← Anterior", variant="secondary",
                               width=100, height=28)
        btn_prev.pack(side="left", padx=5)
        
        btn_next = ModernButton(btn_frame, text="Siguiente →", variant="secondary",
                               width=100, height=28)
        btn_next.pack(side="left", padx=5)
        
        # Función para actualizar la tabla
        def refresh_squad_display():
            # Limpiar tabla
            for item in squad_tree.get_children():
                squad_tree.delete(item)
            
            # Obtener página actual
            state = self.squad_pagination[pagination_key]
            start = state['current_page'] * state['rows_per_page']
            end = start + state['rows_per_page']
            
            # Agregar datos de la página actual
            for player in players_data[start:end]:
                values = (
                    player['name'],
                    player['position'],
                    player['overall'],
                    player['age'],
                    player['potential'],
                    player['value'],
                    player['wage'],
                    player['kit_number']
                )
                squad_tree.insert('', 'end', values=values)
            
            # Actualizar información y botones
            total_pages = (len(players_data) + state['rows_per_page'] - 1) // state['rows_per_page']
            page_display = f"Página {state['current_page'] + 1} de {max(1, total_pages)} ({len(players_data)} jugadores)"
            info_label.configure(text=page_display)
            
            btn_prev.configure(state="normal" if state['current_page'] > 0 else "disabled")
            btn_next.configure(state="normal" if state['current_page'] < total_pages - 1 else "disabled")
        
        # Funciones para navegación
        def prev_page():
            state = self.squad_pagination[pagination_key]
            if state['current_page'] > 0:
                state['current_page'] -= 1
                refresh_squad_display()
        
        def next_page():
            state = self.squad_pagination[pagination_key]
            total_pages = (len(players_data) + state['rows_per_page'] - 1) // state['rows_per_page']
            if state['current_page'] < total_pages - 1:
                state['current_page'] += 1
                refresh_squad_display()
        
        # Vincular botones
        btn_prev.configure(command=prev_page)
        btn_next.configure(command=next_page)
        
        # Mostrar primera página
        refresh_squad_display()
    
    def _adjust_squad_tree_columns(self, event, squad_tree):
        """Ajusta dinámicamente el ancho de las columnas de la tabla de plantilla"""
        if event.width <= 1:
            return
        
        try:
            # Obtener columnas válidas
            columns = squad_tree.cget('columns')
            if not columns or '#all' in str(columns):
                return
            
            # Filtrar solo columnas válidas
            valid_columns = [col for col in columns if col and not col.startswith('#')]
            if not valid_columns:
                return
            
            # Distribuir el ancho equitativamente
            column_width = max(50, event.width // len(valid_columns))
            
            # Aplicar ancho a cada columna
            for col in valid_columns:
                squad_tree.column(col, width=column_width, anchor="center", stretch=True)
        except Exception:
            pass
    
    def _display_kit_gallery(self, images, team_name):
        """Muestra una galería de equipaciones con navegación"""
        gallery_window = tk.Toplevel(self.root)
        gallery_window.title(f"Equipaciones - {team_name}")
        try:
            gallery_window.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono en gallery_window: {e}")
        
        # Variables para navegación
        current_index = [0]
        photo_ref = [None]
        
        # Frame para controles (botones) en la parte superior
        control_frame = ttk.Frame(gallery_window)
        control_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.TOP)
        
        # Botón anterior
        def show_previous():
            if current_index[0] > 0:
                current_index[0] -= 1
                update_image()
        
        # Botón siguiente
        def show_next():
            if current_index[0] < len(images) - 1:
                current_index[0] += 1
                update_image()
        
        btn_prev = ttk.Button(control_frame, text="< Anterior", command=show_previous)
        btn_prev.pack(side=tk.LEFT, padx=5, pady=5)
        
        btn_next = ttk.Button(control_frame, text="Siguiente >", command=show_next)
        btn_next.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Label para el contador
        counter_label = ttk.Label(control_frame, text="")
        counter_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Frame para la imagen en el centro
        img_frame = ttk.Frame(gallery_window, relief=tk.SUNKEN, borderwidth=1)
        img_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2, side=tk.TOP)
        
        # Crear label para la imagen
        img_label = tk.Label(img_frame, bg="white")
        img_label.pack(fill=tk.BOTH, expand=True)
        
        # Redimensionar imagen
        def resize_image(img):
            max_width = 400
            max_height = 400
            img_copy = img.copy()
            img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            return img_copy
        
        # Actualizar imagen
        def update_image():
            img = images[current_index[0]]
            resized_img = resize_image(img)
            photo = ImageTk.PhotoImage(resized_img)
            photo_ref[0] = photo
            img_label.config(image=photo)
            counter_label.config(text=f"Equipación {current_index[0] + 1} de {len(images)}")
            # Ajustar tamaño de la ventana al tamaño de la imagen
            gallery_window.geometry(f"{max(resized_img.width, 350) + 10}x{resized_img.height + 70}")
        
        # Mostrar primera imagen
        update_image()
    
    def _display_kit_window(self, img, team_name):
        """Muestra la imagen en una nueva ventana"""
        kit_window = tk.Toplevel(self.root)
        kit_window.title(f"Equipaciones - {team_name}")
        try:
            kit_window.iconbitmap(str(self.icon_path))
        except tk.TclError as e:
            print(f"Error cargando icono en kit_window: {e}")
        
        # Redimensionar imagen si es muy grande
        max_width = 400
        max_height = 400
        img_copy = img.copy()
        img_copy.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convertir a PhotoImage
        photo = ImageTk.PhotoImage(img_copy)
        
        # Mostrar imagen
        label = tk.Label(kit_window, image=photo, bg="white")
        label.image = photo  # Mantener referencia
        label.pack(padx=2, pady=2)
        
        kit_window.geometry(f"{img_copy.width + 5}x{img_copy.height + 5}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = FootballGraphApp(root)
    root.mainloop()
