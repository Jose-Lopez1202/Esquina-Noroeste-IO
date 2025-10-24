
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple, Optional, Dict
import copy

class TransportResult:
    def __init__(
        self,
        allocation: List[List[float]],
        total_cost: float,
        steps: List[Dict],
        balanced: bool,
        dummy_added: Optional[str],
        costs: List[List[float]]
    ):
        self.allocation = allocation
        self.total_cost = total_cost
        self.steps = steps
        self.balanced = balanced
        self.dummy_added = dummy_added
        self.costs = costs

def _balance_problem(
    costs: List[List[float]],
    supply: List[float],
    demand: List[float],
    dummy_cost: float = 0.0
) -> Tuple[List[List[float]], List[float], List[float], bool, Optional[str]]:
    s_sum = sum(supply)
    d_sum = sum(demand)

    if abs(s_sum - d_sum) < 1e-9:
        return [row[:] for row in costs], supply[:], demand[:], True, None

    c = [row[:] for row in costs]
    if s_sum > d_sum:
        faltante = s_sum - d_sum
        for row in c:
            row.append(dummy_cost)
        demand_bal = demand[:] + [faltante]
        return c, supply[:], demand_bal, False, 'col'
    else:
        faltante = d_sum - s_sum
        c.append([dummy_cost] * len(demand))
        supply_bal = supply[:] + [faltante]
        return c, supply_bal, demand[:], False, 'row'

def northwest_corner( #en este apartado empezamos con la función de la esquina noroeste
    costs: List[List[float]],
    supply: List[float],
    demand: List[float],
    dummy_cost: float = 0.0,
    tie_priority: str = "col"  
) -> TransportResult:
    c, s, d, balanced, dummy_added = _balance_problem(costs, supply, demand, dummy_cost)

    m, n = len(s), len(d)
    alloc = [[0.0 for _ in range(n)] for _ in range(m)]

    i = j = 0
    steps: List[Dict] = []
    s_rem = s[:]
    d_rem = d[:]

    while i < m and j < n:
        x = min(s_rem[i], d_rem[j])
        alloc[i][j] = x
        s_rem[i] -= x
        d_rem[j] -= x

        steps.append({
            "pos": (i, j),
            "asignado": x,
            "oferta_restante_fila_i": s_rem[i],
            "demanda_restante_col_j": d_rem[j]
        })

        if abs(s_rem[i]) < 1e-9 and abs(d_rem[j]) < 1e-9:
            if tie_priority == "col":
                if j + 1 < n: j += 1
                elif i + 1 < m: i += 1
                else: break
            else:  # row
                if i + 1 < m: i += 1
                elif j + 1 < n: j += 1
                else: break
        elif abs(s_rem[i]) < 1e-9:
            i += 1
        elif abs(d_rem[j]) < 1e-9:
            j += 1
        else:
            break

    total_cost = 0.0
    for r in range(m):
        for ccol in range(n):
            total_cost += alloc[r][ccol] * c[r][ccol]

    return TransportResult(alloc, total_cost, steps, balanced, dummy_added, c)

#En este apartado comenzamos con la interfaz lo cual usamos la libreria Tkinter
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Esquina Noroeste — Modelo de Transporte")
        self.geometry("980x650")

        # Top controls
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=6)

        ttk.Label(top, text="Orígenes (m):").pack(side="left")
        self.entry_m = ttk.Entry(top, width=5)
        self.entry_m.pack(side="left", padx=(4,12))
        ttk.Label(top, text="Destinos (n):").pack(side="left")
        self.entry_n = ttk.Entry(top, width=5)
        self.entry_n.pack(side="left", padx=(4,12))

        ttk.Button(top, text="Generar tabla", command=self.generar_tabla).pack(side="left", padx=6)
        ttk.Button(top, text="Ejemplo rápido", command=self.cargar_ejemplo).pack(side="left", padx=6)

        self.tie_var = tk.StringVar(value="col")
        ttk.Label(top, text="Prioridad a consumir:").pack(side="left", padx=(16,4))
        ttk.Radiobutton(top, text="Columna", variable=self.tie_var, value="col").pack(side="left")
        ttk.Radiobutton(top, text="Fila", variable=self.tie_var, value="row").pack(side="left")

      
        ttk.Button(top, text="Limpiar", command=self.limpiar_campos).pack(side="right", padx=4)
        ttk.Button(top, text="Calcular", command=self.calcular).pack(side="right")

      
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=10, pady=6)

        
        left = ttk.LabelFrame(mid, text="Entradas")
        left.pack(side="left", fill="both", expand=True)

        self.scroll = ScrollableFrame(left)
        self.scroll.pack(fill="both", expand=True, padx=6, pady=6)

     
        right = ttk.LabelFrame(mid, text="Resultados")
        right.pack(side="right", fill="both", expand=True, padx=(8,0))

        self.text_res = tk.Text(right, wrap="word", height=30)
        self.text_res.pack(fill="both", expand=True, padx=6, pady=6)

        self.cost_entries = []  
        self.supply_entries = []  
        self.demand_entries = [] 

    def clear_grid(self):
        for widget in self.scroll.scrollable_frame.winfo_children():
            widget.destroy()
        self.cost_entries = []
        self.supply_entries = []
        self.demand_entries = []

    def generar_tabla(self):
        try:
            m = int(self.entry_m.get())
            n = int(self.entry_n.get())
            if m <= 0 or n <= 0 or m > 50 or n > 50:
                raise ValueError("Dimensiones deben ser entre 1 y 50.")
        except Exception as e:
            messagebox.showerror("Error", f"Dimensiones inválidas: {e}")
            return

        self.clear_grid()

      
        ttk.Label(self.scroll.scrollable_frame, text="Costos (m x n)").grid(row=0, column=0, columnspan=n, pady=(0,4))
        for j in range(n):
            ttk.Label(self.scroll.scrollable_frame, text=f"D{j+1}", anchor="center").grid(row=1, column=j, padx=2)

      
        self.cost_entries = []
        for i in range(m):
            row_entries = []
            for j in range(n):
                e = ttk.Entry(self.scroll.scrollable_frame, width=7, justify="right")
                e.grid(row=i+2, column=j, padx=2, pady=1)
                row_entries.append(e)
            self.cost_entries.append(row_entries)

        
        ttk.Label(self.scroll.scrollable_frame, text="Oferta").grid(row=1, column=n+1, padx=(8,2))
        self.supply_entries = []
        for i in range(m):
            e = ttk.Entry(self.scroll.scrollable_frame, width=9, justify="right")
            e.grid(row=i+2, column=n+1, padx=(8,2), pady=1)
            self.supply_entries.append(e)

        
        ttk.Label(self.scroll.scrollable_frame, text="Demanda").grid(row=m+2, column=0, columnspan=n, pady=(8,0))
        self.demand_entries = []
        for j in range(n):
            e = ttk.Entry(self.scroll.scrollable_frame, width=9, justify="right")
            e.grid(row=m+3, column=j, pady=1)
            self.demand_entries.append(e)

       
        ttk.Label(self.scroll.scrollable_frame, text="Tip: doble clic en 'Ejemplo rápido' para rellenar valores de prueba.").grid(row=m+4, column=0, columnspan=n+2, pady=(6,2))

    def cargar_ejemplo(self):
       
        self.entry_m.delete(0, tk.END); self.entry_m.insert(0, "3")
        self.entry_n.delete(0, tk.END); self.entry_n.insert(0, "4")
        self.generar_tabla()

        costs = [
            [8, 6, 10, 9],
            [9, 7, 4, 2],
            [3, 4, 2, 5]
        ]
        supply = [35, 50, 40]
        demand = [30, 40, 20, 35]

        for i in range(3):
            for j in range(4):
                self.cost_entries[i][j].insert(0, str(costs[i][j]))
        for i in range(3):
            self.supply_entries[i].insert(0, str(supply[i]))
        for j in range(4):
            self.demand_entries[j].insert(0, str(demand[j]))

    def leer_matriz(self) -> Tuple[List[List[float]], List[float], List[float]]:
        if not self.cost_entries:
            raise ValueError("Primero genera la tabla.")
        m = len(self.cost_entries)
        n = len(self.cost_entries[0])

        costs = []
        for i in range(m):
            row = []
            for j in range(n):
                val = float(self.cost_entries[i][j].get())
                row.append(val)
            costs.append(row)

        supply = [float(e.get()) for e in self.supply_entries]
        demand = [float(e.get()) for e in self.demand_entries]

        
        if any(x < 0 for x in sum(costs, [])):
            raise ValueError("Los costos no pueden ser negativos.")
        if any(x < 0 for x in supply) or any(x < 0 for x in demand):
            raise ValueError("Oferta y Demanda no pueden ser negativas.")
        if sum(supply) == 0 or sum(demand) == 0:
            raise ValueError("La suma de oferta y demanda debe ser > 0.")

        return costs, supply, demand

    def calcular(self):
        try:
            costs, supply, demand = self.leer_matriz()
            tie = self.tie_var.get()
            res = northwest_corner(costs, supply, demand, dummy_cost=0.0, tie_priority=tie)

           
            self.text_res.delete("1.0", tk.END)
            self.text_res.insert(tk.END, f"Costo total: {res.total_cost:.2f}\n")

           
            if res.balanced:
                self.text_res.insert(tk.END, "El problema está balanceado (oferta = demanda).\n")
            else:
                self.text_res.insert(tk.END, "El problema no estaba balanceado; se completó con un origen o destino auxiliar para poder calcular.\n")

            self.text_res.insert(tk.END, "\nPasos:\n")
            for k, step in enumerate(res.steps, 1):
                i0, j0 = step['pos']
                i1, j1 = i0 + 1, j0 + 1  
                asignado = step['asignado']
                of_rem = step['oferta_restante_fila_i']
                dem_rem = step['demanda_restante_col_j']

                texto = (
                    f"{k:02d}) Se asignaron {asignado:g} unidades a la demanda de la columna {j1} "
                    f"desde la oferta de la fila {i1}. "
                    f"Ahora la oferta de la fila {i1} queda en {of_rem:g} "
                    f"y la demanda de la columna {j1} queda en {dem_rem:g}.\n"
                )
                self.text_res.insert(tk.END, texto)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def limpiar_campos(self):
        
        for row in self.cost_entries:
            for e in row:
                e.delete(0, tk.END)
        for e in self.supply_entries:
            e.delete(0, tk.END)
        for e in self.demand_entries:
            e.delete(0, tk.END)
        self.text_res.delete("1.0", tk.END)

if __name__ == "__main__":
    App().mainloop()
