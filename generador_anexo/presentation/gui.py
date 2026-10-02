# -*- coding: utf-8 -*-
"""Capa de PRESENTACION: interfaz grafica (GUI) con Tkinter.

Como se usa:
    py interfaz_anexo.py
"""

import glob
import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk

from ..config.settings import CARPETA
from .composicion import leer_preliminares, procesar

# filas de la zona superior de la GUI ocupadas por los campos de archivo.
FILA_ENCABEZADO = 2
FILA_ACTIVIDAD = 3

# espera antes de releer la exogena cuando la ruta se escribe a mano.
MS_ESPERA_RELECTURA = 400


def detectar(patron, excluir=()):
    candidatos = glob.glob(os.path.join(CARPETA, patron))
    candidatos = [f for f in candidatos
                  if not any(os.path.basename(f).startswith(p) for p in excluir)]
    return max(candidatos, key=os.path.getmtime) if candidatos else ""


class App:
    def __init__(self, root):
        self.root = root
        root.title("Anexo Formulario 210 - Generator")
        root.geometry("820x620")
        root.minsize(700, 500)

        self.var_exo = tk.StringVar(value=detectar("*Exogena*.xlsx"))
        self.var_salida = tk.StringVar()
        self.var_final = tk.StringVar()
        self.var_encabezado = tk.StringVar()
        self.var_actividad = tk.StringVar()
        self.var_venta_mas2 = tk.BooleanVar(value=False)
        self.var_subcontrato = tk.BooleanVar(value=False)

        # Ultimo valor que escribio la app sola en cada campo. Si el campo
        # sigue con ese valor (o vacio) se puede sobrescribir al cambiar de
        # exogena; si el usuario lo edito a mano, se respeta.
        self._auto_salida = ""
        self._auto_encabezado = ""
        self._exo_previa = ""
        self._id_espera = None

        self._construir_widgets()
        self.var_exo.trace_add("write", self._exo_cambiada)
        self._precargar_encabezado()

    def _construir_widgets(self):
        marco = ttk.Frame(self.root, padding="10")
        marco.pack(fill="both", expand=True)

        self._fila(marco, 0, "Informacion Exogena:",
                   self.var_exo, self._buscar_exo)
        self._fila(marco, 1, "Archivo de salida:",
                   self.var_salida, self._buscar_salida)
        self._fila(marco, 2, "Identificacion:", self.var_encabezado,
                   None, editable=True)
        self._fila(marco, 3, "Actividad economica:", self.var_actividad,
                   None, editable=True)
        ttk.Checkbutton(
            marco,
            text="Venta de activos fijos poseida mas de 2 anos "
                 "(va a ganancia ocasional)",
            variable=self.var_venta_mas2).grid(
            row=4, column=1, columnspan=3, sticky="w")
        ttk.Checkbutton(
            marco,
            text="Subcontrato 2 o mas personas por 90 dias o mas "
                 "(honorarios/comisiones/servicios van a renta no laboral)",
            variable=self.var_subcontrato).grid(
            row=5, column=1, columnspan=3, sticky="w")
        ttk.Label(marco, textvariable=self.var_final,
                  foreground="#1a6b1a").grid(row=6, column=1, columnspan=3,
                                             sticky="w", pady=(2, 8))

        bots = ttk.Frame(marco)
        bots.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        self.btn_generar = ttk.Button(bots, text="Generar anexo",
                                      command=self.generar)
        self.btn_generar.pack(side="left")
        self.btn_abrir = ttk.Button(bots, text="Abrir archivo generado",
                                    command=self.abrir, state="disabled")
        self.btn_abrir.pack(side="left", padx=(8, 0))
        self.lbl_estado = ttk.Label(bots, text="")
        self.lbl_estado.pack(side="left", padx=(12, 0))

        self.txt = scrolledtext.ScrolledText(marco, height=20, wrap="none",
                                             state="disabled")
        self.txt.grid(row=8, column=0, columnspan=4, sticky="nsew")
        marco.rowconfigure(7, weight=1)
        marco.columnconfigure(1, weight=1)
        marco.columnconfigure(2, weight=1)

    def _fila(self, marco, fila, etiqueta, var, comando, editable=False):
        ttk.Label(marco, text=etiqueta).grid(row=fila, column=0, sticky="e",
                                             padx=(0, 6), pady=4)
        entry = ttk.Entry(marco, textvariable=var)
        entry.grid(row=fila, column=1, columnspan=2, sticky="ew", pady=2)
        if comando:
            ttk.Button(marco, text="Buscar...", command=comando).grid(
                row=fila, column=3, padx=(6, 0), pady=2)

    def _buscar_exo(self):
        r = filedialog.askopenfilename(
            title="Informacion Exogena", filetypes=[("Excel", "*.xlsx")])
        if r:
            self.var_exo.set(r)

    def _exo_cambiada(self, *_):
        """Reactiva el precargado cuando cambia la exogena, con espera para
        no releer el .xlsx en cada tecla si la ruta se escribe a mano."""
        if self._id_espera is not None:
            self.root.after_cancel(self._id_espera)
        self._id_espera = self.root.after(MS_ESPERA_RELECTURA,
                                          self._precargar_encabezado)

    def _es_automático(self, var, auto):
        """True si el campo sigue con el valor que puso la app o esta vacio,
        es decir que el usuario no lo ha editado a mano."""
        actual = var.get().strip()
        return actual == "" or actual == auto.strip()

    def _precargar_encabezado(self):
        """Recalcula 'Identificacion' y el archivo de salida desde la exogena
        elegida. Sobrescribe lo que la app habia puesto antes, pero respeta
        lo que el usuario haya escrito a mano."""
        self._id_espera = None
        exo = self.var_exo.get().strip()
        self._descartar_corrida_previa()
        nombre = ""
        if exo and os.path.isfile(exo):
            try:
                linea, nombre = leer_preliminares(exo)
            except Exception:
                linea = ""
            if linea and self._es_automático(self.var_encabezado,
                                             self._auto_encabezado):
                self.var_encabezado.set(linea)
                self._auto_encabezado = linea

        # Sin nombre de consultante (o sin exogena) se sugiere la fecha de hoy.
        if self._es_automático(self.var_salida, self._auto_salida):
            destino = os.path.join(CARPETA, nombre or
                                   f"Anexo 210 - {date.today().isoformat()}.xlsx")
            self.var_salida.set(destino)
            self._auto_salida = destino

        self._exo_previa = exo

    def _descartar_corrida_previa(self):
        """Al cambiar de exogena el 'Abrir archivo generado' y el mensaje
        verde ya no aplican: que no apunten a la corrida anterior."""
        if self._exo_previa and self._exo_previa != self.var_exo.get().strip():
            self.var_final.set("")
            self.btn_abrir.config(state="disabled", command=self.abrir)
            self.lbl_estado.config(text="")
            self._escribir("")

    def _buscar_salida(self):
        r = filedialog.asksaveasfilename(
            title="Guardar anexo como", defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")], initialfile=os.path.basename(
                self.var_salida.get()))
        if r:
            self.var_salida.set(r)

    def _escribir(self, texto):
        self.txt.config(state="normal")
        self.txt.delete("1.0", tk.END)
        self.txt.insert("1.0", texto)
        self.txt.config(state="disabled")

    def generar(self):
        exo = self.var_exo.get().strip()
        salida = self.var_salida.get().strip()
        if not exo or not os.path.isfile(exo):
            messagebox.showerror("Falta archivo",
                                 "Seleccione la Informacion Exogena.")
            return
        if not salida:
            nombre = simpledialog.askstring(
                "Nombre del archivo",
                "No encontramos el nombre del consultante en la exogena.\n"
                "Escriba el nombre del archivo (sin .xlsx):",
                parent=self.root)
            if not nombre:
                return
            salida = os.path.join(CARPETA, f"{nombre}.xlsx")
            self.var_salida.set(salida)

        self.btn_generar.config(state="disabled")
        self.lbl_estado.config(text="Generando...")
        self.var_final.set("")
        self.root.update_idletasks()
        try:
            reporte, salida_final, _ = procesar(
                exo, salida,
                actividad=self.var_actividad.get().strip(),
                encabezado=self.var_encabezado.get().strip(),
                venta_activos_mas_2_anos=bool(self.var_venta_mas2.get()),
            subcontrato_2_mas=bool(self.var_subcontrato.get()))
        except Exception as e:
            self._escribir(f"ERROR: {e}")
            self.lbl_estado.config(text="Error")
            self.btn_generar.config(state="normal")
            return
        self._escribir(reporte)
        self.var_final.set(f"Archivo generado: {salida_final}")
        self.btn_abrir.config(state="normal",
                              command=lambda: self.abrir(salida_final))
        self.lbl_estado.config(text="Listo")
        self.btn_generar.config(state="normal")

    def abrir(self, ruta=None):
        ruta = ruta or self.var_final.get().replace("Archivo generado: ", "")
        if ruta and os.path.isfile(ruta):
            try:
                os.startfile(ruta)
            except Exception as e:
                messagebox.showerror("No se pudo abrir", str(e))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0


__all__ = ["main", "App"]