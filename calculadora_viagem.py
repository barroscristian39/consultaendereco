"""
Calculadora de Custo de Viagem por CEP
=======================================
Programa 100% em Python (Tkinter) que:
 1. Busca o endereço a partir do CEP de origem (API ViaCEP)
 2. Permite adicionar o número do endereço de origem
 3. Busca o endereço a partir do CEP de destino (API ViaCEP)
 4. Permite adicionar o número do endereço de destino
 5. Geocodifica os dois endereços (API Nominatim/OpenStreetMap)
 6. Calcula a distância rodoviária entre eles (API OSRM)
 7. Permite marcar "Ida e volta" (dobra a distância) - o custo é
    recalculado automaticamente ao marcar/desmarcar
 8. Calcula o custo da viagem com base no consumo do carro (km/l)
    e no preço do combustível (R$/litro)
 
Dependência externa: apenas a biblioteca "requests".
Todas as APIs usadas (ViaCEP, Nominatim, OSRM) são gratuitas e não
exigem chave de API. É necessário estar conectado à internet.
 
Para gerar o executável (.exe), veja o arquivo README.md incluído.
"""
 
import threading
import tkinter as tk
from tkinter import ttk, messagebox
 
import requests
 
# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
HEADERS = {"User-Agent": "CalculadoraViagemCEP/1.0 (uso pessoal)"}
TIMEOUT = 15
 
 
# ---------------------------------------------------------------------------
# Funções de integração com APIs externas
# ---------------------------------------------------------------------------
def buscar_endereco_por_cep(cep: str) -> dict:
    """Consulta a API pública ViaCEP e retorna os dados do endereço."""
    cep_limpo = "".join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        raise ValueError("CEP inválido. Digite os 8 dígitos do CEP.")
 
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    dados = resp.json()
 
    if dados.get("erro"):
        raise ValueError("CEP não encontrado.")
 
    return dados
 
 
def montar_endereco_completo(dados_cep: dict, numero: str):
    """Monta uma string de endereço completo para geocodificação."""
    partes = []
    logradouro = dados_cep.get("logradouro", "").strip()
    bairro = dados_cep.get("bairro", "").strip()
    cidade = dados_cep.get("localidade", "").strip()
    uf = dados_cep.get("uf", "").strip()
    cep = dados_cep.get("cep", "").strip()
 
    if logradouro:
        rua = f"{logradouro}, {numero}" if numero else logradouro
        partes.append(rua)
    if bairro:
        partes.append(bairro)
    if cidade:
        partes.append(cidade)
    if uf:
        partes.append(uf)
    partes.append("Brasil")
 
    endereco = ", ".join(partes)
    return endereco, cep
 
 
def geocodificar(endereco: str, cep_fallback: str = None):
    """Converte um endereço em coordenadas (lat, lon) usando o Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": endereco, "format": "json", "limit": 1, "countrycodes": "br"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    resultados = resp.json()
 
    if not resultados and cep_fallback:
        params["q"] = f"{cep_fallback}, Brasil"
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resultados = resp.json()
 
    if not resultados:
        raise ValueError(f"Não foi possível localizar as coordenadas para:\n{endereco}")
 
    lat = float(resultados[0]["lat"])
    lon = float(resultados[0]["lon"])
    return lat, lon
 
 
def calcular_distancia_km(coord_origem, coord_destino) -> float:
    """Calcula a distância rodoviária (km) entre duas coordenadas usando OSRM."""
    lat1, lon1 = coord_origem
    lat2, lon2 = coord_destino
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}"
    )
    params = {"overview": "false"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    dados = resp.json()
 
    if dados.get("code") != "Ok":
        raise ValueError("Não foi possível calcular a rota entre os endereços.")
 
    distancia_metros = dados["routes"][0]["distance"]
    return distancia_metros / 1000.0
 
 
# ---------------------------------------------------------------------------
# Interface gráfica (Tkinter)
# ---------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Custo de Viagem por CEP")
        self.geometry("620x840")
        self.minsize(600, 760)
 
        self.dados_cep_origem = None
        self.dados_cep_destino = None
 
        # Guarda o último resultado de rota calculado, para poder
        # recalcular o custo instantaneamente (sem chamar as APIs de novo)
        # quando o usuário mexer no checkbox de ida/volta, no consumo
        # ou no preço do combustível.
        self.ultimo_km_ida = None
        self.ultimo_endereco_origem = None
        self.ultimo_endereco_destino = None
 
        self._montar_layout()
 
    # ------------------------------------------------------------------
    def _montar_layout(self):
        pad = {"padx": 12, "pady": 5}
 
        # ---- Área rolável (scroll) para caber tudo em telas menores ----
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        container = tk.Frame(canvas)
 
        container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
 
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
 
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
 
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
 
        raiz = container  # tudo abaixo usa "raiz" como pai, dentro do scroll
 
        titulo = tk.Label(
            raiz, text="Calculadora de Custo de Viagem",
            font=("Segoe UI", 15, "bold"),
        )
        titulo.pack(pady=(14, 6))
 
        # ---------------- ORIGEM ----------------
        frame_origem = ttk.LabelFrame(raiz, text="Origem")
        frame_origem.pack(fill="x", **pad)
 
        tk.Label(frame_origem, text="CEP de origem:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_cep_origem = tk.Entry(frame_origem, width=15)
        self.entry_cep_origem.grid(row=0, column=1, sticky="w", padx=5)
        tk.Button(frame_origem, text="Buscar CEP", command=self.buscar_origem).grid(
            row=0, column=2, padx=5
        )
 
        self.label_endereco_origem = tk.Label(
            frame_origem, text="Endereço: -", justify="left", wraplength=520,
            fg="#333333",
        )
        self.label_endereco_origem.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=2)
 
        tk.Label(frame_origem, text="Número:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.entry_numero_origem = tk.Entry(frame_origem, width=10)
        self.entry_numero_origem.grid(row=2, column=1, sticky="w", padx=5)
 
        # ---------------- DESTINO ----------------
        frame_destino = ttk.LabelFrame(raiz, text="Destino")
        frame_destino.pack(fill="x", **pad)
 
        tk.Label(frame_destino, text="CEP de destino:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_cep_destino = tk.Entry(frame_destino, width=15)
        self.entry_cep_destino.grid(row=0, column=1, sticky="w", padx=5)
        tk.Button(frame_destino, text="Buscar CEP", command=self.buscar_destino).grid(
            row=0, column=2, padx=5
        )
 
        self.label_endereco_destino = tk.Label(
            frame_destino, text="Endereço: -", justify="left", wraplength=520,
            fg="#333333",
        )
        self.label_endereco_destino.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=2)
 
        tk.Label(frame_destino, text="Número:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.entry_numero_destino = tk.Entry(frame_destino, width=10)
        self.entry_numero_destino.grid(row=2, column=1, sticky="w", padx=5)
 
        # ---------------- VIAGEM ----------------
        frame_viagem = ttk.LabelFrame(raiz, text="Dados da viagem")
        frame_viagem.pack(fill="x", **pad)
 
        self.var_ida_volta = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(
            frame_viagem, text="Calcular ida e volta", variable=self.var_ida_volta,
            command=self._recalcular_custo_ao_vivo,
        )
        chk.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=4)
 
        tk.Label(frame_viagem, text="Consumo do carro (km por litro):").grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        self.entry_kml = tk.Entry(frame_viagem, width=10)
        self.entry_kml.grid(row=1, column=1, sticky="w", padx=5)
        self.entry_kml.bind("<KeyRelease>", lambda e: self._recalcular_custo_ao_vivo())
 
        tk.Label(frame_viagem, text="Preço do litro da gasolina (R$):").grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        self.entry_preco = tk.Entry(frame_viagem, width=10)
        self.entry_preco.grid(row=2, column=1, sticky="w", padx=5)
        self.entry_preco.bind("<KeyRelease>", lambda e: self._recalcular_custo_ao_vivo())
 
        # ---------------- AÇÃO ----------------
        self.btn_calcular = tk.Button(
            raiz,
            text="Calcular distância e custo",
            font=("Segoe UI", 11, "bold"),
            bg="#2e7d32",
            fg="white",
            activebackground="#256428",
            activeforeground="white",
            command=self.calcular,
        )
        self.btn_calcular.pack(pady=14, ipadx=12, ipady=8)
 
        self.label_status = tk.Label(raiz, text="", fg="#1565c0", font=("Segoe UI", 9))
        self.label_status.pack()
 
        # ---------------- RESULTADO ----------------
        frame_resultado = ttk.LabelFrame(raiz, text="Resultado")
        frame_resultado.pack(fill="both", expand=True, **pad)
 
        self.label_placeholder = tk.Label(
            frame_resultado,
            text="Preencha os campos acima e clique em \"Calcular distância e custo\".",
            justify="left",
            font=("Segoe UI", 10),
            fg="#777777",
            wraplength=540,
        )
        self.label_placeholder.pack(padx=10, pady=14, anchor="w")
 
        # Endereços usados no último cálculo (texto pequeno, cinza)
        self.label_res_enderecos = tk.Label(
            frame_resultado, text="", justify="left", font=("Segoe UI", 9),
            fg="#555555", wraplength=560,
        )
 
        self.separador1 = ttk.Separator(frame_resultado, orient="horizontal")
 
        # Grade com os números da viagem (distância, modo, litros)
        self.grid_dados = tk.Frame(frame_resultado)
 
        def _linha_dado(parent, row, rotulo):
            tk.Label(parent, text=rotulo, font=("Segoe UI", 10), anchor="w").grid(
                row=row, column=0, sticky="w", padx=(4, 14), pady=4
            )
            valor = tk.Label(parent, text="-", font=("Segoe UI", 10, "bold"), anchor="w")
            valor.grid(row=row, column=1, sticky="w", pady=4)
            return valor
 
        self.val_distancia_ida = _linha_dado(self.grid_dados, 0, "Distância só de ida:")
        self.val_modo = _linha_dado(self.grid_dados, 1, "Modo da viagem:")
        self.val_distancia_total = _linha_dado(self.grid_dados, 2, "Distância total considerada:")
        self.val_litros = _linha_dado(self.grid_dados, 3, "Combustível estimado:")
 
        self.separador2 = ttk.Separator(frame_resultado, orient="horizontal")
 
        # Caixa de destaque com o valor total em R$
        self.frame_custo = tk.Frame(
            frame_resultado, bg="#e8f5e9",
            highlightbackground="#2e7d32", highlightthickness=1,
        )
        tk.Label(
            self.frame_custo, text="CUSTO TOTAL ESTIMADO DA VIAGEM",
            font=("Segoe UI", 10, "bold"), bg="#e8f5e9", fg="#1b5e20",
        ).pack(pady=(12, 0))
 
        self.val_custo_total = tk.Label(
            self.frame_custo, text="R$ 0,00",
            font=("Segoe UI", 28, "bold"), bg="#e8f5e9", fg="#1b5e20",
        )
        self.val_custo_total.pack(pady=(0, 4))
 
        self.label_custo_detalhe = tk.Label(
            self.frame_custo, text="",
            font=("Segoe UI", 9), bg="#e8f5e9", fg="#2e7d32",
        )
        self.label_custo_detalhe.pack(pady=(0, 12))
 
    # ------------------------------------------------------------------
    def _set_status(self, texto, cor="#1565c0"):
        self.label_status.config(text=texto, fg=cor)
        self.update_idletasks()
 
    # ------------------------------------------------------------------
    def _mostrar_area_resultado(self):
        """Esconde o placeholder inicial e mostra os widgets de resultado."""
        self.label_placeholder.pack_forget()
        self.label_res_enderecos.pack(padx=10, pady=(10, 4), anchor="w")
        self.separador1.pack(fill="x", padx=10, pady=8)
        self.grid_dados.pack(padx=10, pady=2, anchor="w")
        self.separador2.pack(fill="x", padx=10, pady=8)
        self.frame_custo.pack(fill="x", padx=10, pady=(2, 14))
 
    # ------------------------------------------------------------------
    def _ler_kml_preco(self):
        """Lê e valida os campos de consumo e preço. Retorna (kml, preco) ou None."""
        try:
            kml = float(self.entry_kml.get().replace(",", "."))
            preco = float(self.entry_preco.get().replace(",", "."))
            if kml <= 0 or preco <= 0:
                return None
            return kml, preco
        except ValueError:
            return None
 
    # ------------------------------------------------------------------
    def _recalcular_custo_ao_vivo(self):
        """
        Recalcula apenas o custo (sem consultar as APIs de novo), usando a
        última distância de ida já calculada. É chamado automaticamente ao
        marcar/desmarcar "ida e volta" ou ao editar consumo/preço.
        """
        if self.ultimo_km_ida is None:
            return  # ainda não foi feito nenhum cálculo de rota
 
        valores = self._ler_kml_preco()
        if valores is None:
            return
 
        kml, preco = valores
        ida_volta = self.var_ida_volta.get()
        km_total = self.ultimo_km_ida * 2 if ida_volta else self.ultimo_km_ida
        litros = km_total / kml
        custo_total = litros * preco
 
        self.val_modo.config(text="Ida e volta" if ida_volta else "Somente ida")
        self.val_distancia_total.config(text=f"{km_total:.1f} km")
        self.val_litros.config(text=f"{litros:.2f} litros")
        self.val_custo_total.config(text=f"R$ {custo_total:.2f}".replace(".", ","))
        self.label_custo_detalhe.config(
            text=f"({km_total:.1f} km ÷ {kml:.1f} km/l × R$ {preco:.2f}/L)".replace(".", ",")
        )
 
    # ------------------------------------------------------------------
    def buscar_origem(self):
        self._buscar_cep_generico(
            self.entry_cep_origem,
            self.label_endereco_origem,
            eh_origem=True,
        )
 
    def buscar_destino(self):
        self._buscar_cep_generico(
            self.entry_cep_destino,
            self.label_endereco_destino,
            eh_origem=False,
        )
 
    def _buscar_cep_generico(self, entry_cep, label_endereco, eh_origem):
        cep = entry_cep.get().strip()
        self._set_status("Buscando CEP...")
 
        def worker():
            try:
                dados = buscar_endereco_por_cep(cep)
                texto = (
                    f"Endereço: {dados.get('logradouro', '(sem logradouro)')} - "
                    f"{dados.get('bairro', '')} - {dados.get('localidade', '')}/"
                    f"{dados.get('uf', '')}"
                )
                if eh_origem:
                    self.dados_cep_origem = dados
                else:
                    self.dados_cep_destino = dados
 
                self.after(0, lambda: label_endereco.config(text=texto))
                self.after(0, lambda: self._set_status("CEP encontrado com sucesso.", "#2e7d32"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Erro: {e}", "#c62828"))
                self.after(0, lambda: messagebox.showerror("Erro ao buscar CEP", str(e)))
 
        threading.Thread(target=worker, daemon=True).start()
 
    # ------------------------------------------------------------------
    def calcular(self):
        if not self.dados_cep_origem:
            messagebox.showwarning("Atenção", "Busque o CEP de origem primeiro.")
            return
        if not self.dados_cep_destino:
            messagebox.showwarning("Atenção", "Busque o CEP de destino primeiro.")
            return
 
        valores = self._ler_kml_preco()
        if valores is None:
            messagebox.showwarning(
                "Atenção",
                "Preencha o consumo (km/l) e o preço do litro com números válidos.",
            )
            return
        kml, preco = valores
 
        numero_origem = self.entry_numero_origem.get().strip()
        numero_destino = self.entry_numero_destino.get().strip()
        ida_volta = self.var_ida_volta.get()
 
        self.btn_calcular.config(state="disabled")
        self._set_status("Calculando rota, aguarde...")
 
        def worker():
            try:
                endereco_origem, cep_origem = montar_endereco_completo(
                    self.dados_cep_origem, numero_origem
                )
                endereco_destino, cep_destino = montar_endereco_completo(
                    self.dados_cep_destino, numero_destino
                )
 
                coord_origem = geocodificar(endereco_origem, cep_origem)
                coord_destino = geocodificar(endereco_destino, cep_destino)
 
                km_ida = calcular_distancia_km(coord_origem, coord_destino)
                km_total = km_ida * 2 if ida_volta else km_ida
 
                litros = km_total / kml
                custo_total = litros * preco
 
                def atualizar_ui():
                    # guarda para permitir recálculo instantâneo depois
                    self.ultimo_km_ida = km_ida
 
                    self._mostrar_area_resultado()
 
                    self.label_res_enderecos.config(
                        text=f"Origem: {endereco_origem}\nDestino: {endereco_destino}"
                    )
                    self.val_distancia_ida.config(text=f"{km_ida:.1f} km")
                    self.val_modo.config(text="Ida e volta" if ida_volta else "Somente ida")
                    self.val_distancia_total.config(text=f"{km_total:.1f} km")
                    self.val_litros.config(text=f"{litros:.2f} litros".replace(".", ","))
                    self.val_custo_total.config(
                        text=f"R$ {custo_total:.2f}".replace(".", ",")
                    )
                    self.label_custo_detalhe.config(
                        text=(
                            f"({km_total:.1f} km ÷ {kml:.1f} km/l × "
                            f"R$ {preco:.2f}/L)"
                        ).replace(".", ",")
                    )
                    self._set_status("Cálculo concluído.", "#2e7d32")
 
                self.after(0, atualizar_ui)
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Erro: {e}", "#c62828"))
                self.after(0, lambda: messagebox.showerror("Erro ao calcular", str(e)))
            finally:
                self.after(0, lambda: self.btn_calcular.config(state="normal"))
 
        threading.Thread(target=worker, daemon=True).start()
 
 
if __name__ == "__main__":
    app = App()
    app.mainloop()
