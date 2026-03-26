import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import DatabaseManager
import os
import sys

class AutoHideScrollbar(tk.Scrollbar):
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            if self.winfo_ismapped():
                self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side="right", fill="y")
        tk.Scrollbar.set(self, lo, hi)

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class InformeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Planta Villa Bicentenario Mantencion 2026")
        self.root.minsize(800, 600)

        # Configurar estilo para filas más altas en el Treeview
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Treeview', rowheight=30)
            style.configure('StatusOk.TLabel', foreground='green')
            style.configure('StatusBad.TLabel', foreground='red')
        except:
            pass
        self.db = None
        self.status_var = tk.StringVar(value="Sin conexión")
        try:
            self.db = DatabaseManager()
            self.status_var.set("Conectado")
        except Exception:
            self.status_var.set("Sin conexión")

        self.selected_id = None

        # Variables simples (las multilínea no usan StringVar)
        self.var_nombre = tk.StringVar()
        self.var_lugar = tk.StringVar()
        self.var_planta = tk.StringVar()
        self.var_fecha_inst = tk.StringVar()
        self.var_horometro = tk.StringVar()
        self.var_fecha_ingreso = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
        self.var_mantencion = tk.StringVar()
        self.var_prox_mant = tk.StringVar()
        self.var_baja = tk.BooleanVar()

        self.create_layout()
        self.load_data()

    def create_layout(self):
        self.toolbar_logo_img = None
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Panel Izquierdo: Formulario ---
        left_frame = ttk.Frame(main_frame, width=360) 
        left_frame.pack(side="left", fill="both", padx=(0, 5))
        left_frame.pack_propagate(False)
        left_canvas = tk.Canvas(left_frame, highlightthickness=0)
        left_vsb = AutoHideScrollbar(left_frame, orient="vertical", command=left_canvas.yview)
        self.scrollable_frame = ttk.Frame(left_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        canvas_window_id = left_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        def configure_canvas_width(event):
            left_canvas.itemconfig(canvas_window_id, width=event.width)
        left_canvas.bind("<Configure>", configure_canvas_width)
        left_canvas.configure(yscrollcommand=left_vsb.set)
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        left_canvas.pack(side="left", fill="both", expand=True)
        left_vsb.pack(side="right", fill="y")
        def _activate_scroll():
            left_canvas.yview_scroll(1, "units")
            left_canvas.yview_scroll(-1, "units")
        left_canvas.after(150, _activate_scroll)
        self.create_form_widgets(self.scrollable_frame)

        # --- Panel Derecho: Tabla ---
        # Ocupa todo el espacio restante
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True)
        self.create_table_widgets(right_frame)
        footer = ttk.Frame(self.root)
        footer.pack(side="bottom", fill="x")
        tk.Label(footer, text="Hecho por Lucas Caro", font=("Arial", 9, "italic"), fg="#7f8c8d").pack(side="right", padx=10, pady=3)

    def create_form_widgets(self, parent):
        ttk.Label(parent, text="Ingreso de Datos", font=("Arial", 12, "bold")).pack(pady=10)

        def create_field(label_text, variable):
            frame = ttk.Frame(parent)
            frame.pack(fill="x", padx=10, pady=2)
            ttk.Label(frame, text=label_text).pack(anchor="w")
            ttk.Entry(frame, textvariable=variable).pack(fill="x")

        create_field("Nombre Equipo:", self.var_nombre)
        
        # Descripción (Multilínea)
        ttk.Label(parent, text="Descripción:").pack(anchor="w", padx=10, pady=2)
        self.txt_descripcion = tk.Text(parent, height=3, width=30)
        self.txt_descripcion.pack(fill="x", padx=10, pady=2)

        create_field("Lugar de Instalación:", self.var_lugar)
        create_field("Planta:", self.var_planta)
        create_field("Fecha Instalación (DD-MM-YYYY):", self.var_fecha_inst)
        create_field("Horómetro:", self.var_horometro)
        
        f_ingreso = ttk.Frame(parent)
        f_ingreso.pack(fill="x", padx=10, pady=2)
        ttk.Label(f_ingreso, text="Fecha Ingreso Datos (Auto):").pack(anchor="w")
        ttk.Entry(f_ingreso, textvariable=self.var_fecha_ingreso, state="readonly").pack(fill="x")

        create_field("Mantención Realizada:", self.var_mantencion)
        create_field("Próxima Mantención (DD-MM-YYYY):", self.var_prox_mant)
        
        ttk.Checkbutton(parent, text="Dar de Baja", variable=self.var_baja).pack(anchor="w", padx=10, pady=5)
        
        # Otros (Multilínea)
        ttk.Label(parent, text="Otros:").pack(anchor="w", padx=10, pady=2)
        self.txt_otros = tk.Text(parent, height=3, width=30)
        self.txt_otros.pack(fill="x", padx=10, pady=2)

        # Observaciones (Multilínea)
        ttk.Label(parent, text="Observaciones:").pack(anchor="w", padx=10, pady=2)
        self.txt_observaciones = tk.Text(parent, height=3, width=30)
        self.txt_observaciones.pack(fill="x", padx=10, pady=2)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=15)
        
        self.btn_guardar = ttk.Button(btn_frame, text="Guardar Nuevo", command=self.save_data)
        self.btn_guardar.pack(fill="x", pady=2)
        
        self.btn_actualizar = ttk.Button(btn_frame, text="Actualizar Seleccionado", command=self.update_data, state="disabled")
        self.btn_actualizar.pack(fill="x", pady=2)
        
        ttk.Button(btn_frame, text="Limpiar Formulario", command=self.clear_form).pack(fill="x", pady=2)

    def create_table_widgets(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", padx=5, pady=5)
        ttk.Button(toolbar, text="Eliminar Seleccionado", command=self.delete_data).pack(side="right")
        ttk.Button(toolbar, text="Recargar Tabla", command=self.load_data).pack(side="right", padx=5)
        ttk.Label(toolbar, text="Doble clic en una fila para ver detalles completos", font=("Arial", 9, "italic")).pack(side="left")
        status_area = ttk.Frame(toolbar)
        status_area.pack(side="right")
        self.status_label = ttk.Label(status_area, textvariable=self.status_var, style=("StatusOk.TLabel" if self.db else "StatusBad.TLabel"))
        self.status_label.pack(side="right", padx=5)
        self.retry_btn = ttk.Button(status_area, text="Reintentar conexión", command=self.retry_connection)
        if not self.db:
            self.retry_btn.pack(side="right")

        columns = ("id", "nombre", "desc", "lugar", "planta", "f_inst", "horom", "f_ingr", "mant", "obs", "prox", "baja", "otros")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        headers = {
            "id": "ID", "nombre": "Equipo", "desc": "Desc.", "lugar": "Lugar",
            "planta": "Planta", "f_inst": "F. Inst.", "horom": "Horóm.",
            "f_ingr": "F. Ingreso", "mant": "Mantención", "obs": "Obs.",
            "prox": "Próx. Mant.", "baja": "Baja", "otros": "Otros"
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=80, minwidth=50)

        self.tree.column("id", width=30)
        self.tree.column("nombre", width=100)
        self.tree.column("obs", width=150)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)

        self.tree.pack(side="top", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        # Sin scrollbar horizontal para una visual más limpia

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)

    def retry_connection(self):
        try:
            self.db = DatabaseManager()
            self.status_var.set("Conectado")
            self.status_label.configure(style="StatusOk.TLabel")
            if self.retry_btn.winfo_ismapped():
                self.retry_btn.pack_forget()
            self.load_data()
        except Exception:
            self.db = None
            self.status_var.set("Sin conexión")
            self.status_label.configure(style="StatusBad.TLabel")
            if not self.retry_btn.winfo_ismapped():
                self.retry_btn.pack(side="right")
    def get_form_data(self):
        return {
            'nombre_equipo': self.var_nombre.get(),
            'descripcion': self.txt_descripcion.get("1.0", tk.END).strip(),
            'lugar_instalacion': self.var_lugar.get(),
            'planta': self.var_planta.get(),
            'fecha_instalacion': self.var_fecha_inst.get(),
            'horometro': float(self.var_horometro.get()) if self.var_horometro.get() else 0.0,
            'fecha_ingreso': self.var_fecha_ingreso.get(),
            'mantencion': self.var_mantencion.get(),
            'observaciones': self.txt_observaciones.get("1.0", tk.END).strip(),
            'proxima_mantencion': self.var_prox_mant.get(),
            'baja': self.var_baja.get(),
            'otros': self.txt_otros.get("1.0", tk.END).strip()
        }

    def save_data(self):
        data = self.get_form_data()
        if not data['nombre_equipo']:
            messagebox.showerror("Error", "El nombre del equipo es obligatorio.")
            return

        if self.db.add_report(data):
            messagebox.showinfo("Éxito", "Informe guardado correctamente.")
            self.clear_form()
            self.load_data()
        else:
            messagebox.showerror("Error", "No se pudo guardar en la base de datos.")

    def update_data(self):
        if not self.selected_id:
            return
        
        data = self.get_form_data()
        if self.db.update_report(self.selected_id, data):
            messagebox.showinfo("Éxito", "Informe actualizado correctamente.")
            self.clear_form()
            self.load_data()
        else:
            messagebox.showerror("Error", "No se pudo actualizar.")

    def delete_data(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione un registro para eliminar.")
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este registro?"):
            item = self.tree.item(selected[0])
            id_reporte = item['values'][0]
            if self.db.delete_report(id_reporte):
                self.load_data()
                self.clear_form()
            else:
                messagebox.showerror("Error", "No se pudo eliminar.")

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        
        self.selected_id = values[0]
        self.var_nombre.set(values[1])
        
        # Descripción
        self.txt_descripcion.delete("1.0", tk.END)
        self.txt_descripcion.insert("1.0", values[2])
        
        self.var_lugar.set(values[3])
        self.var_planta.set(values[4])
        self.var_fecha_inst.set(values[5])
        self.var_horometro.set(values[6])
        # No actualizamos la fecha de ingreso automática
        self.var_mantencion.set(values[8])
        
        # Observaciones
        self.txt_observaciones.delete("1.0", tk.END)
        self.txt_observaciones.insert("1.0", values[9])
        
        self.var_prox_mant.set(values[10])
        self.var_baja.set(True if values[11] == '1' or values[11] == 1 else False)
        
        # Otros
        self.txt_otros.delete("1.0", tk.END)
        self.txt_otros.insert("1.0", values[12])

        self.btn_actualizar.config(state="normal")
        self.btn_guardar.config(state="disabled")

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        
        # Crear ventana emergente estilo "Ficha Técnica"
        top = tk.Toplevel(self.root)
        top.title(f"Ficha Técnica: {values[1]}")
        top.geometry("700x850")
        top.configure(bg="#f5f5f5") # Fondo gris claro
        
        # Título Principal
        header_frame = tk.Frame(top, bg="#2c3e50", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text=f"FICHA TÉCNICA DEL EQUIPO", font=("Arial", 16, "bold"), fg="white", bg="#2c3e50").pack()
        tk.Label(header_frame, text=values[1], font=("Arial", 14), fg="#bdc3c7", bg="#2c3e50").pack()

        # Canvas para scroll
        canvas = tk.Canvas(top, bg="#f5f5f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f5f5", padx=20, pady=20)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        canvas.bind("<Configure>", configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Estilos ---
        style_label_title = ("Arial", 9, "bold")
        style_label_val = ("Arial", 10)
        bg_color = "#f5f5f5"

        def create_section(parent, title):
            frame = tk.LabelFrame(parent, text=title, font=("Arial", 11, "bold", "italic"), bg=bg_color, fg="#2980b9", padx=15, pady=10, relief="groove")
            frame.pack(fill="x", pady=10)
            return frame

        def add_row(parent, label1, val1, label2=None, val2=None):
            row = tk.Frame(parent, bg=bg_color)
            row.pack(fill="x", pady=5)
            
            # Columna 1
            f1 = tk.Frame(row, bg=bg_color)
            f1.pack(side="left", fill="x", expand=True)
            tk.Label(f1, text=label1, font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
            tk.Label(f1, text=val1, font=style_label_val, bg=bg_color, wraplength=300, justify="left").pack(anchor="w")
            
            # Columna 2 (Opcional)
            if label2:
                f2 = tk.Frame(row, bg=bg_color)
                f2.pack(side="left", fill="x", expand=True, padx=(20, 0))
                tk.Label(f2, text=label2, font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
                tk.Label(f2, text=val2, font=style_label_val, bg=bg_color, wraplength=300, justify="left").pack(anchor="w")

        def add_multiline(parent, label, value):
            frame = tk.Frame(parent, bg=bg_color)
            frame.pack(fill="x", pady=8)
            tk.Label(frame, text=label, font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
            
            # Calcular altura
            num_lines = value.count('\n') + int(len(value) / 80) + 2
            if num_lines < 3: num_lines = 3
            
            txt = tk.Text(frame, height=num_lines, font=("Consolas", 10), bg="white", relief="flat", padx=10, pady=10)
            txt.insert("1.0", value)
            txt.configure(state="disabled")
            txt.pack(fill="x", pady=2)
            # Borde sutil
            frame_border = tk.Frame(frame, bg="#bdc3c7", height=1)
            frame_border.pack(fill="x")

        # --- Sección 1: Identificación y Ubicación ---
        sec_info = create_section(scroll_frame, "Identificación y Ubicación")
        add_row(sec_info, "ID Registro:", str(values[0]), "Nombre Equipo:", values[1])
        add_row(sec_info, "Lugar Instalación:", values[3], "Planta:", values[4])

        # --- Sección 2: Datos Técnicos ---
        sec_tec = create_section(scroll_frame, "Datos Técnicos y Estado")
        baja_str = "SÍ (Dado de Baja)" if (values[11] == 1 or values[11] == '1') else "Operativo"
        val_baja_fg = "red" if (values[11] == 1 or values[11] == '1') else "green"
        
        # Fila personalizada para Baja con color
        row_tec = tk.Frame(sec_tec, bg=bg_color)
        row_tec.pack(fill="x", pady=5)
        
        f_inst = tk.Frame(row_tec, bg=bg_color)
        f_inst.pack(side="left", fill="x", expand=True)
        tk.Label(f_inst, text="Fecha Instalación:", font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
        tk.Label(f_inst, text=values[5], font=style_label_val, bg=bg_color).pack(anchor="w")
        
        f_horom = tk.Frame(row_tec, bg=bg_color)
        f_horom.pack(side="left", fill="x", expand=True, padx=(20,0))
        tk.Label(f_horom, text="Horómetro:", font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
        tk.Label(f_horom, text=str(values[6]), font=style_label_val, bg=bg_color).pack(anchor="w")

        row_est = tk.Frame(sec_tec, bg=bg_color)
        row_est.pack(fill="x", pady=5)
        
        f_ingr = tk.Frame(row_est, bg=bg_color)
        f_ingr.pack(side="left", fill="x", expand=True)
        tk.Label(f_ingr, text="Fecha Ingreso Datos:", font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
        tk.Label(f_ingr, text=values[7], font=style_label_val, bg=bg_color).pack(anchor="w")
        
        f_baja = tk.Frame(row_est, bg=bg_color)
        f_baja.pack(side="left", fill="x", expand=True, padx=(20,0))
        tk.Label(f_baja, text="Estado Actual:", font=style_label_title, bg=bg_color, fg="#7f8c8d").pack(anchor="w")
        tk.Label(f_baja, text=baja_str, font=("Arial", 10, "bold"), bg=bg_color, fg=val_baja_fg).pack(anchor="w")

        # --- Sección 3: Mantención ---
        sec_mant = create_section(scroll_frame, "Historial de Mantención")
        add_row(sec_mant, "Última Mantención:", values[8], "Próxima Mantención:", values[10])

        # --- Sección 4: Detalles Extensos ---
        sec_det = create_section(scroll_frame, "Detalles Adicionales")
        add_multiline(sec_det, "Descripción del Equipo:", values[2])
        add_multiline(sec_det, "Observaciones:", values[9])
        add_multiline(sec_det, "Otros:", values[12])
        
        # Botón Cerrar
        ttk.Button(scroll_frame, text="Cerrar Ficha", command=top.destroy).pack(pady=20, ipadx=20)

    def clear_form(self):
        self.selected_id = None
        self.var_nombre.set("")
        self.txt_descripcion.delete("1.0", tk.END)
        self.var_lugar.set("")
        self.var_planta.set("")
        self.var_fecha_inst.set("")
        self.var_horometro.set("")
        self.var_mantencion.set("")
        self.var_prox_mant.set("")
        self.var_baja.set(False)
        self.txt_otros.delete("1.0", tk.END)
        self.txt_observaciones.delete("1.0", tk.END)
        
        self.var_fecha_ingreso.set(datetime.now().strftime("%d-%m-%Y"))
        
        self.btn_actualizar.config(state="disabled")
        self.btn_guardar.config(state="normal")

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.db:
            return
        try:
            rows = self.db.get_reports()
            for row in rows:
                self.tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error al cargar datos: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    # No theme_use here to allow init style config in class
    app = InformeApp(root)
    root.mainloop()
