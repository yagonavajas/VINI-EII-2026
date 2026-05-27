"""
Módulo UI - Componentes reutilizables con CustomTkinter
Estilo inspirado en SoFIFA con diseño moderno y profesional
"""

import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from typing import Callable, List, Dict, Any, Optional, Tuple
from PIL import Image, ImageTk
from pathlib import Path

# ============================================================================
# PALETA DE COLORES - Inspirada en SoFIFA
# ============================================================================

class Colors:
    """Paleta de colores del sistema"""
    # Colores primarios
    PRIMARY_DARK = "#1e1e2e"  # Azul muy oscuro (fondo)
    PRIMARY = "#16213e"  # Azul oscuro (componentes)
    PRIMARY_LIGHT = "#0f3460"  # Azul claro
    
    # Colores de acentos
    ACCENT_GOLD = "#a6e3a1"  # Verde vibrante (acentos, botones importantes)
    ACCENT_RED = "#f38ba8"  # Rojo (alertas, errores)
    ACCENT_GREEN = "#a6e3a1"  # Verde (éxito)
    
    # Colores neutrales
    TEXT_PRIMARY = "#cdd6f4"  # Texto principal
    TEXT_SECONDARY = "#bac2de"  # Texto secundario
    TEXT_MUTED = "#a6adc8"  # Texto deshabilitado
    
    # Fondos
    BG_PRIMARY = "#1e1e2e"  # Fondo principal
    BG_SECONDARY = "#181825"  # Fondo secundario
    BG_TERTIARY = "#11111b"  # Fondo terciario
    
    # Bordes
    BORDER_COLOR = "#9399b2"  # Color de bordes
    BORDER_LIGHT = "#7f849c"  # Borde claro


class FontSizes:
    """Tamaños de fuente del sistema"""
    # Títulos
    TITLE_EXTRA_LARGE = 30  # Títulos muy grandes (headers principales)
    TITLE_LARGE = 20  # Títulos grandes (títulos de secciones)
    TITLE = 18  # Títulos medianos (títulos de cards)
    TITLE_SMALL = 16  # Títulos pequeños (subtítulos)
    
    # Texto regular
    TEXT_NORMAL = 15  # Texto normal (contenido principal)
    TEXT_SMALL = 14  # Texto pequeño (etiquetas, información secundaria)


# ============================================================================
# COMPONENTES CUSTOMIZADOS
# ============================================================================

class ModernCard(ctk.CTkFrame):
    """Tarjeta moderna para mostrar consultas o información"""
    
    def __init__(self, master, title: str = "", description: str = "", 
                 command: Callable = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(
            fg_color=Colors.BG_SECONDARY,
            corner_radius=10,
            border_width=1,
            border_color=Colors.BORDER_COLOR
        )
        
        # Frame interno con padding
        inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        inner_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        if title:
            title_label = ctk.CTkLabel(
                inner_frame,
                text=title,
                font=("Segoe UI", FontSizes.TITLE, "bold"),
                text_color=Colors.TEXT_PRIMARY
            )
            title_label.pack(anchor="w", pady=(0, 8))
        
        # Descripción
        if description:
            desc_label = ctk.CTkLabel(
                inner_frame,
                text=description,
                font=("Segoe UI", FontSizes.TEXT_NORMAL),
                text_color=Colors.TEXT_SECONDARY,
                wraplength=250
            )
            desc_label.pack(anchor="w", pady=(0, 12))
        
        # Botón si hay comando
        if command:
            btn = ctk.CTkButton(
                inner_frame,
                text="Ejecutar",
                command=command,
                fg_color=Colors.ACCENT_GOLD,
                text_color=Colors.PRIMARY_DARK,
                hover_color="#ffc700",
                font=("Segoe UI", FontSizes.TEXT_NORMAL, "bold"),
                height=32,
                corner_radius=6
            )
            btn.pack(fill="x", pady=(8, 0))


class ModernButton(ctk.CTkButton):
    """Botón moderno con estilo SoFIFA"""
    
    def __init__(self, master, text: str = "", variant: str = "primary", **kwargs):
        """
        variant: "primary" (oro), "secondary" (azul), "danger" (rojo), "success" (verde)
        """
        
        color_map = {
            "primary": (Colors.ACCENT_GOLD, "#ffc700", Colors.PRIMARY_DARK),
            "secondary": (Colors.PRIMARY_LIGHT, Colors.PRIMARY, Colors.TEXT_PRIMARY),
            "danger": (Colors.ACCENT_RED, "#d23456", Colors.TEXT_PRIMARY),
            "success": (Colors.ACCENT_GREEN, "#2bb85d", Colors.TEXT_PRIMARY)
        }
        
        fg_color, hover_color, text_color = color_map.get(variant, color_map["primary"])
        
        # Permitir que font, height y corner_radius sean sobrescritos en kwargs
        font = kwargs.pop("font", ("Segoe UI", FontSizes.TEXT_NORMAL, "bold"))
        height = kwargs.pop("height", 32)
        corner_radius = kwargs.pop("corner_radius", 6)
        
        super().__init__(
            master,
            text=text,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            font=font,
            height=height,
            corner_radius=corner_radius,
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Campo de entrada moderno"""
    
    def __init__(self, master, placeholder: str = "", **kwargs):
        # Permitir que font sea sobrescrito en kwargs
        font = kwargs.pop("font", ("Segoe UI", FontSizes.TEXT_NORMAL))
        
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color=Colors.BG_TERTIARY,
            border_color=Colors.BORDER_COLOR,
            border_width=1,
            text_color=Colors.TEXT_PRIMARY,
            placeholder_text_color=Colors.TEXT_MUTED,
            font=font,
            **kwargs
        )


class ModernCombobox(ctk.CTkComboBox):
    """Combobox moderno con navegación mejorada"""
    
    def __init__(self, master, values: List[str] = None, **kwargs):
        # Permitir que font sea sobrescrito en kwargs
        font = kwargs.pop("font", ("Segoe UI", FontSizes.TEXT_NORMAL))
        
        super().__init__(
            master,
            values=values or [],
            fg_color=Colors.BG_TERTIARY,
            border_color=Colors.BORDER_COLOR,
            border_width=1,
            text_color=Colors.TEXT_PRIMARY,
            button_color=Colors.ACCENT_GOLD,
            button_hover_color="#ffc700",
            dropdown_fg_color=Colors.BG_SECONDARY,
            dropdown_text_color=Colors.TEXT_PRIMARY,
            font=font,
            **kwargs
        )
        
        self._current_index = -1
        self._all_values = values or []
        
        # Vincular eventos de navegación mejorada
        self.bind('<MouseWheel>', self._on_mousewheel, add=True)  # Windows
        self.bind('<Button-4>', self._on_mousewheel, add=True)    # Linux scroll up
        self.bind('<Button-5>', self._on_mousewheel, add=True)    # Linux scroll down
        self.bind('<Up>', self._on_arrow_up, add=True)            # Flecha arriba
        self.bind('<Down>', self._on_arrow_down, add=True)        # Flecha abajo
        self.bind('<Prior>', self._on_page_up, add=True)          # Page Up
        self.bind('<Next>', self._on_page_down, add=True)         # Page Down
    
    def _on_arrow_up(self, event):
        """Navega hacia arriba"""
        self._navigate(-1)
        return 'break'
    
    def _on_arrow_down(self, event):
        """Navega hacia abajo"""
        self._navigate(1)
        return 'break'
    
    def _on_mousewheel(self, event):
        """Maneja scroll con rueda del ratón para navegar opciones"""
        try:
            current_values = self.cget('values')
            if not current_values:
                return 'break'
            
            # Determinar dirección del scroll
            if hasattr(event, 'num'):
                if event.num == 5:
                    direction = 1  # Scroll hacia abajo
                elif event.num == 4:
                    direction = -1  # Scroll hacia arriba
                else:
                    return 'break'
            elif hasattr(event, 'delta'):
                direction = 1 if event.delta < 0 else -1
            else:
                return 'break'
            
            self._navigate(direction)
            return 'break'
        except:
            return 'break'
    
    def _on_page_up(self, event):
        """Navega hacia arriba por páginas (3 opciones)"""
        self._navigate(-3)
        return 'break'
    
    def _on_page_down(self, event):
        """Navega hacia abajo por páginas (3 opciones)"""
        self._navigate(3)
        return 'break'
    
    def _navigate(self, direction: int):
        """Navega en la dirección especificada"""
        try:
            current_values = list(self.cget('values'))
            if not current_values:
                return
            
            current_text = self.get()
            
            # Encontrar el índice actual
            try:
                current_index = current_values.index(current_text)
            except ValueError:
                current_index = -1
            
            # Calcular nuevo índice
            new_index = current_index + direction
            
            # Asegurar que está dentro de los límites
            new_index = max(0, min(new_index, len(current_values) - 1))
            
            # Establecer el nuevo valor
            if 0 <= new_index < len(current_values):
                new_value = current_values[new_index]
                self.set(new_value)
        except:
            pass


class ModernTable(ctk.CTkFrame):
    """Tabla mejorada con paginación"""
    
    def __init__(self, master, columns: List[str] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.columns = columns or []
        self.visible_columns = self.columns  # Columnas visibles (dinámicas)
        self.data = []
        self.current_page = 0
        self.rows_per_page = 10
        
        # Frame de tabla
        self.table_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER_COLOR
        )
        self.table_frame.pack(fill="both", expand=True)
        
        # Frame para Treeview
        self.tree_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Crear Treeview sin scrollbars
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Treeview",
            background=Colors.BG_SECONDARY,
            foreground=Colors.TEXT_PRIMARY,
            fieldbackground=Colors.BG_SECONDARY,
            borderwidth=0,
            rowheight=32,
            font=("Segoe UI", FontSizes.TEXT_SMALL)
        )
        style.configure(
            "Treeview.Heading",
            background=Colors.PRIMARY_LIGHT,
            foreground=Colors.TEXT_PRIMARY,
            borderwidth=0,
            font=("Segoe UI", FontSizes.TEXT_SMALL, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", Colors.ACCENT_GOLD)],
            foreground=[("selected", Colors.TEXT_PRIMARY)]
        )
        
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            height=10,
            show="headings"
        )
        
        # Configurar columnas (centradas con ancho dinámico)
        for col in self.columns:
            self.tree.column(col, width=100, anchor="center", stretch=True)
            self.tree.heading(col, text=col)
        
        self.tree.pack(fill="both", expand=True)
        
        # Vincular evento de redimensionamiento para ajustar columnas
        self.tree_frame.bind("<Configure>", self._on_frame_resize)
        
        # Frame de paginación
        self.pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.pagination_frame.pack(fill="x", pady=(10, 0))
        
        self.info_label = ctk.CTkLabel(
            self.pagination_frame,
            text="",
            font=("Segoe UI", FontSizes.TEXT_SMALL),
            text_color=Colors.TEXT_SECONDARY
        )
        self.info_label.pack(side="left", padx=5)
        
        # Botones de paginación
        btn_frame = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5)
        
        self.btn_prev = ModernButton(btn_frame, text="← Anterior", variant="secondary", 
                                     command=self._prev_page, width=100, height=28)
        self.btn_prev.pack(side="left", padx=5)
        
        self.btn_next = ModernButton(btn_frame, text="Siguiente →", variant="secondary",
                                     command=self._next_page, width=100, height=28)
        self.btn_next.pack(side="left", padx=5)
    
    def _on_frame_resize(self, event):
        """Ajusta el ancho de las columnas cuando el frame se redimensiona"""
        if not self.visible_columns or event.width <= 1:
            return
        
        # Calcular ancho disponible
        available_width = event.width
        
        # Distribuir el ancho equitativamente entre columnas visibles
        column_width = max(50, available_width // len(self.visible_columns))
        
        # Aplicar ancho a cada columna visible
        for col in self.visible_columns:
            self.tree.column(col, width=column_width, anchor="center", stretch=True)
    
    def _on_frame_resize_deferred(self):
        """Ajusta el ancho de las columnas de forma diferida después de actualizar datos"""
        if not self.visible_columns:
            return
        
        # Obtener ancho actual del frame
        width = self.tree_frame.winfo_width()
        if width <= 1:
            return
        
        # Distribuir el ancho equitativamente entre columnas visibles
        column_width = max(50, width // len(self.visible_columns))
        
        # Aplicar ancho a cada columna visible
        for col in self.visible_columns:
            self.tree.column(col, width=column_width, anchor="center", stretch=True)
    
    def set_data(self, data: List[List[Any]]):
        """Establece los datos de la tabla"""
        self.data = data
        self.current_page = 0
        
        # Detectar qué columnas tienen datos reales (no "N/A")
        if data:
            columns_with_data = []
            for i, col in enumerate(self.columns):
                # Verificar si esta columna tiene algún dato que no sea N/A
                has_data = False
                for row in data:
                    if i < len(row):
                        value = row[i]
                        # Considerar que hay dato si no es "N/A" y no está vacío
                        if value != "N/A" and (not isinstance(value, str) or value.strip()):
                            has_data = True
                            break
                if has_data:
                    columns_with_data.append(col)
            
            # Si no hay columnas con datos, mostrar todas
            if not columns_with_data:
                columns_with_data = self.columns
            
            # Actualizar columnas visibles
            self.visible_columns = columns_with_data
            self.tree.configure(displaycolumns=columns_with_data)
        else:
            self.visible_columns = self.columns
            self.tree.configure(displaycolumns=self.columns)
        
        self._refresh_display()
        
        # Forzar ajuste de columnas después de actualizar datos
        self.tree_frame.after(10, lambda: self._on_frame_resize_deferred())
    
    def add_row(self, row_data: List[Any]):
        """Agrega una fila a la tabla"""
        self.data.append(row_data)
        self._refresh_display()
    
    def clear(self):
        """Limpia la tabla"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.data = []
        self.visible_columns = self.columns
        self.tree.configure(displaycolumns=self.columns)
        self._refresh_display()
    
    def _refresh_display(self):
        """Actualiza la visualización de la tabla"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        start = self.current_page * self.rows_per_page
        end = start + self.rows_per_page
        
        for row in self.data[start:end]:
            self.tree.insert("", "end", values=row)
        
        total_pages = (len(self.data) + self.rows_per_page - 1) // self.rows_per_page
        page_display = f"Página {self.current_page + 1} de {max(1, total_pages)} ({len(self.data)} resultados)"
        self.info_label.configure(text=page_display)
        
        self.btn_prev.configure(state="normal" if self.current_page > 0 else "disabled")
        self.btn_next.configure(
            state="normal" if self.current_page < total_pages - 1 else "disabled"
        )
    
    def _prev_page(self):
        """Va a la página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_display()
    
    def _next_page(self):
        """Va a la siguiente página"""
        total_pages = (len(self.data) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._refresh_display()


class ModernSearchBar(ctk.CTkFrame):
    """Barra de búsqueda moderna con filtros"""
    
    def __init__(self, master, on_search: Callable = None, on_filter: Callable = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color=Colors.BG_SECONDARY, corner_radius=8)
        main_frame.pack(fill="x", pady=5)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=10)
        
        # Campo de búsqueda
        self.search_entry = ModernEntry(content_frame, placeholder="🔍 Buscar...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        if on_search:
            self.search_entry.bind("<Return>", lambda e: on_search(self.search_entry.get()))
        
        # Botón de búsqueda
        self.search_btn = ModernButton(content_frame, text="Buscar", variant="primary",
                                       command=lambda: on_search(self.search_entry.get()) if on_search else None)
        self.search_btn.pack(side="left", padx=(0, 10))
        
        # Botón de filtro
        self.filter_btn = ModernButton(content_frame, text="⚙ Filtros", variant="secondary",
                                       command=on_filter if on_filter else None)
        self.filter_btn.pack(side="left")
    
    def get_search_text(self) -> str:
        """Obtiene el texto de búsqueda"""
        return self.search_entry.get()
    
    def clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_entry.delete(0, tk.END)


class ModernScrollableFrame(ctk.CTkScrollableFrame):
    """Frame con scroll personalizado - scroll solo visible cuando sea necesario"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_PRIMARY,
            scrollbar_button_color=Colors.ACCENT_GOLD,
            scrollbar_button_hover_color="#ffc700",
            **kwargs
        )


class ModernTabview(ctk.CTkTabview):
    """Tabs moderno"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_SECONDARY,
            segmented_button_fg_color=Colors.BG_TERTIARY,
            segmented_button_selected_color=Colors.ACCENT_GOLD,
            segmented_button_selected_hover_color="#ffc700",
            text_color=Colors.TEXT_PRIMARY,
            text_color_disabled=Colors.TEXT_MUTED,
            **kwargs
        )


class ModernLabel(ctk.CTkLabel):
    """Label moderno"""
    
    def __init__(self, master, text: str = "", variant: str = "primary", **kwargs):
        """
        variant: "primary" (blanco), "secondary" (gris), "accent" (dorado), "error" (rojo)
        """
        
        color_map = {
            "primary": Colors.TEXT_PRIMARY,
            "secondary": Colors.TEXT_SECONDARY,
            "accent": Colors.ACCENT_GOLD,
            "error": Colors.ACCENT_RED,
            "success": Colors.ACCENT_GREEN
        }
        
        text_color = color_map.get(variant, Colors.TEXT_PRIMARY)
        
        # Permitir que font sea sobrescrito en kwargs
        font = kwargs.pop("font", ("Segoe UI", FontSizes.TEXT_NORMAL))
        
        super().__init__(
            master,
            text=text,
            text_color=text_color,
            font=font,
            **kwargs
        )


class ModernDialog(ctk.CTkToplevel):
    """Diálogo modal moderno"""
    
    def __init__(self, master, title: str = "Diálogo", width: int = 400, height: int = 300):
        super().__init__(master)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=Colors.BG_PRIMARY)
        
        # Centrar ventana
        self.transient(master)
        self.grab_set()
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.result = None
    
    def get_result(self):
        """Obtiene el resultado del diálogo"""
        return self.result


class ModernStatusBar(ctk.CTkFrame):
    """Barra de estado en la parte inferior"""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_SECONDARY,
            border_width=1,
            border_color=Colors.BORDER_COLOR,
            height=40,
            **kwargs
        )
        
        # Label de estado
        self.status_label = ctk.CTkLabel(
            self,
            text="Listo",
            font=("Segoe UI", FontSizes.TEXT_SMALL),
            text_color=Colors.TEXT_SECONDARY
        )
        self.status_label.pack(side="left", padx=10, pady=8)
        
        # Indicador de progreso (opcional)
        self.progress_var = tk.DoubleVar()
        self.progress = ctk.CTkProgressBar(
            self,
            variable=self.progress_var,
            fg_color=Colors.BG_TERTIARY,
            progress_color=Colors.ACCENT_GOLD,
            width=200,
            height=6
        )
        self.progress.pack(side="right", padx=10, pady=8)
    
    def set_status(self, text: str, status_type: str = "info"):
        """Actualiza el estado"""
        color_map = {
            "info": Colors.TEXT_SECONDARY,
            "success": Colors.ACCENT_GREEN,
            "error": Colors.ACCENT_RED,
            "warning": Colors.ACCENT_GOLD
        }
        
        text_color = color_map.get(status_type, Colors.TEXT_SECONDARY)
        self.status_label.configure(text=text, text_color=text_color)
    
    def set_progress(self, value: float):
        """Actualiza la barra de progreso (0.0 - 1.0)"""
        self.progress_var.set(value)


class ModernHeader(ctk.CTkFrame):
    """Header con logo y navegación principal"""
    
    def __init__(self, master, title: str = "VINI", subtitle: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=Colors.PRIMARY,
            border_width=0,
            **kwargs
        )
        
        # Frame interno
        inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        inner_frame.pack(fill="x", padx=20, pady=15)
        
        # Título
        title_label = ctk.CTkLabel(
            inner_frame,
            text=title,
            font=("Segoe UI", FontSizes.TITLE_EXTRA_LARGE, "bold"),
            text_color=Colors.ACCENT_GOLD
        )
        title_label.pack(anchor="w")
        
        # Subtítulo
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                inner_frame,
                text=subtitle,
                font=("Segoe UI", FontSizes.TITLE_SMALL),
                text_color=Colors.TEXT_SECONDARY
            )
            subtitle_label.pack(anchor="w", pady=(2, 0))


class ModernFilterPanel(ctk.CTkFrame):
    """Panel de filtros avanzados"""
    
    def __init__(self, master, filters: Dict[str, List[str]] = None, **kwargs):
        super().__init__(
            master,
            fg_color=Colors.BG_SECONDARY,
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER_COLOR,
            **kwargs
        )
        
        self.filters = filters or {}
        self.filter_values = {}
        
        # Título
        title = ctk.CTkLabel(
            self,
            text="Filtros",
            font=("Segoe UI", FontSizes.TITLE_SMALL, "bold"),
            text_color=Colors.TEXT_PRIMARY
        )
        title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Scroll frame
        scroll_frame = ModernScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear filtros
        for filter_name, options in self.filters.items():
            # Label del filtro
            filter_label = ctk.CTkLabel(
                scroll_frame,
                text=filter_name,
                font=("Segoe UI", FontSizes.TEXT_SMALL, "bold"),
                text_color=Colors.TEXT_PRIMARY
            )
            filter_label.pack(anchor="w", pady=(10, 5))
            
            # Combobox
            filter_combo = ModernCombobox(
                scroll_frame,
                values=options,
                width=200
            )
            filter_combo.pack(anchor="w", pady=(0, 10))
            self.filter_values[filter_name] = filter_combo
        
        # Botones
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=15)
        
        self.btn_apply = ModernButton(button_frame, text="Aplicar", variant="primary")
        self.btn_apply.pack(side="left", padx=(0, 10))
        
        self.btn_clear = ModernButton(button_frame, text="Limpiar", variant="secondary")
        self.btn_clear.pack(side="left")
    
    def get_filter_values(self) -> Dict[str, str]:
        """Obtiene los valores de los filtros"""
        return {k: v.get() for k, v in self.filter_values.items()}
    
    def clear_filters(self):
        """Limpia todos los filtros"""
        for combo in self.filter_values.values():
            combo.set("")


class ModernNotification(ctk.CTkToplevel):
    """Notificación emergente"""
    
    def __init__(self, master, message: str = "", notification_type: str = "info", duration: int = 3000, icon_path=None):
        super().__init__(master)
        
        self.title("VINI - Notificación")
        self.geometry("350x100")
        self.configure(fg_color=Colors.BG_SECONDARY, border_width=1, border_color=Colors.BORDER_COLOR)
        
        # Intentar establecer icono
        if icon_path:
            try:
                import tkinter as tk
                self.iconbitmap(str(icon_path))
            except tk.TclError as e:
                pass  # Ignorar silenciosamente si falla
        
        # Sin decoración de ventana
        self.attributes("-topmost", True)
        self.transient(master)
        
        # Colores según tipo
        color_map = {
            "info": Colors.PRIMARY_LIGHT,
            "success": Colors.ACCENT_GREEN,
            "error": Colors.ACCENT_RED,
            "warning": Colors.ACCENT_GOLD
        }
        border_color = color_map.get(notification_type, Colors.PRIMARY_LIGHT)
        
        # Frame de borde
        border_frame = ctk.CTkFrame(self, fg_color=border_color, corner_radius=8)
        border_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Frame interno
        frame = ctk.CTkFrame(border_frame, fg_color=Colors.BG_SECONDARY, corner_radius=6)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Contenido
        label = ctk.CTkLabel(
            frame,
            text=message,
            font=("Segoe UI", FontSizes.TEXT_NORMAL),
            text_color=Colors.TEXT_PRIMARY,
            wraplength=320
        )
        label.pack(padx=15, pady=15)
        
        # Posicionar en la esquina superior derecha
        self.update_idletasks()
        master.update_idletasks()
        
        x = master.winfo_x() + master.winfo_width() - 370
        y = master.winfo_y() + 20
        
        self.geometry(f"+{x}+{y}")
        
        # Auto-cerrar
        self.after(duration, self.destroy)


# ============================================================================
# TEMAS Y CONFIGURACIÓN GLOBAL
# ============================================================================

def setup_app_theme():
    """Configura el tema global de la aplicación"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


# ============================================================================
# UTILIDADES
# ============================================================================

def load_image(path: str, size: Tuple[int, int] = (200, 200)) -> ImageTk.PhotoImage:
    """Carga y redimensiona una imagen"""
    try:
        img = Image.open(path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Error cargando imagen {path}: {e}")
        return None


def create_placeholder_image(width: int = 200, height: int = 200) -> ImageTk.PhotoImage:
    """Crea una imagen placeholder"""
    img = Image.new('RGB', (width, height), Colors.BG_TERTIARY)
    return ImageTk.PhotoImage(img)
