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
 7. Permite marcar "Ida e volta" (dobra a distância)
 8. Calcula o custo da viagem com base no consumo do carro (km/l)
    e no preço do combustível (R$/litro)

Dependência externa: apenas a biblioteca "requests".
Todas as APIs usadas (ViaCEP, Nominatim, OSRM) são gratuitas e não
exigem chave de API. É necessário estar conectado à internet.

Para gerar o executável (.exe), veja o arquivo README.md incluído.
"""

import json
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


def montar_endereco_completo(dados_cep: dict, numero: str) -> str:
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
        # Fallback: tenta geocodificar apenas pelo CEP
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
        self.geometry("560x640")
        self.resizable(False, False)

        self.dados_cep_origem = None
        self.dados_cep_destino = None

        self._montar_layout()

    # ------------------------------------------------------------------
    def _montar_layout(self):
        pad = {"padx": 10, "pady": 4}

        titulo = tk.Label(
            self, text="Calculadora de Custo de Viagem", font=("Segoe UI", 14, "bold")
        )
        titulo.pack(pady=(10, 5))

        # ---------------- ORIGEM ----------------
        frame_origem = ttk.LabelFrame(self, text="Origem")
        frame_origem.pack(fill="x", **pad)

        tk.Label(frame_origem, text="CEP de origem:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_cep_origem = tk.Entry(frame_origem, width=15)
        self.entry_cep_origem.grid(row=0, column=1, sticky="w", padx=5)
        tk.Button(frame_origem, text="Buscar CEP", command=self.buscar_origem).grid(
            row=0, column=2, padx=5
        )

        self.label_endereco_origem = tk.Label(
            frame_origem, text="Endereço: -", justify="left", wraplength=500
        )
        self.label_endereco_origem.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=2)

        tk.Label(frame_origem, text="Número:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.entry_numero_origem = tk.Entry(frame_origem, width=10)
        self.entry_numero_origem.grid(row=2, column=1, sticky="w", padx=5)

        # ---------------- DESTINO ----------------
        frame_destino = ttk.LabelFrame(self, text="Destino")
        frame_destino.pack(fill="x", **pad)

        tk.Label(frame_destino, text="CEP de destino:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.entry_cep_destino = tk.Entry(frame_destino, width=15)
        self.entry_cep_destino.grid(row=0, column=1, sticky="w", padx=5)
        tk.Button(frame_destino, text="Buscar CEP", command=self.buscar_destino).grid(
            row=0, column=2, padx=5
        )

        self.label_endereco_destino = tk.Label(
            frame_destino, text="Endereço: -", justify="left", wraplength=500
        )
        self.label_endereco_destino.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=2)

        tk.Label(frame_destino, text="Número:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.entry_numero_destino = tk.Entry(frame_destino, width=10)
        self.entry_numero_destino.grid(row=2, column=1, sticky="w", padx=5)

        # ---------------- VIAGEM ----------------
        frame_viagem = ttk.LabelFrame(self, text="Dados da viagem")
        frame_viagem.pack(fill="x", **pad)

        self.var_ida_volta = tk.BooleanVar(value=False)
        tk.Checkbutton(
            frame_viagem, text="Calcular ida e volta", variable=self.var_ida_volta
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=4)

        tk.Label(frame_viagem, text="Consumo do carro (km por litro):").grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        self.entry_kml = tk.Entry(frame_viagem, width=10)
        self.entry_kml.grid(row=1, column=1, sticky="w", padx=5)

        tk.Label(frame_viagem, text="Preço do litro da gasolina (R$):").grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        self.entry_preco = tk.Entry(frame_viagem, width=10)
        self.entry_preco.grid(row=2, column=1, sticky="w", padx=5)

        # ---------------- AÇÃO ----------------
        self.btn_calcular = tk.Button(
            self,
            text="Calcular distância e custo",
            font=("Segoe UI", 11, "bold"),
            bg="#2e7d32",
            fg="white",
            command=self.calcular,
        )
        self.btn_calcular.pack(pady=12, ipadx=10, ipady=6)

        self.label_status = tk.Label(self, text="", fg="blue")
        self.label_status.pack()

        # ---------------- RESULTADO ----------------
        frame_resultado = ttk.LabelFrame(self, text="Resultado")
        frame_resultado.pack(fill="both", expand=True, **pad)

        self.label_resultado = tk.Label(
            frame_resultado,
            text="Preencha os campos acima e clique em Calcular.",
            justify="left",
            font=("Segoe UI", 11),
            wraplength=500,
        )
        self.label_resultado.pack(padx=10, pady=10, anchor="w")

    # ------------------------------------------------------------------
    def _set_status(self, texto, cor="blue"):
        self.label_status.config(text=texto, fg=cor)
        self.update_idletasks()

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
                self.after(0, lambda: self._set_status("CEP encontrado com sucesso.", "green"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Erro: {e}", "red"))
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

        try:
            kml = float(self.entry_kml.get().replace(",", "."))
            preco = float(self.entry_preco.get().replace(",", "."))
            if kml <= 0 or preco <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Atenção",
                "Preencha o consumo (km/l) e o preço do litro com números válidos.",
            )
            return

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

                km = calcular_distancia_km(coord_origem, coord_destino)
                km_total = km * 2 if ida_volta else km

                litros = km_total / kml
                custo_total = litros * preco

                texto_resultado = (
                    f"Origem: {endereco_origem}\n"
                    f"Destino: {endereco_destino}\n\n"
                    f"Distância (só ida): {km:.1f} km\n"
                    f"Modo: {'Ida e volta' if ida_volta else 'Somente ida'}\n"
                    f"Distância total considerada: {km_total:.1f} km\n\n"
                    f"Combustível gasto: {litros:.2f} litros\n"
                    f"Custo total estimado da viagem: R$ {custo_total:.2f}"
                )

                self.after(0, lambda: self.label_resultado.config(text=texto_resultado))
                self.after(0, lambda: self._set_status("Cálculo concluído.", "green"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"Erro: {e}", "red"))
                self.after(0, lambda: messagebox.showerror("Erro ao calcular", str(e)))
            finally:
                self.after(0, lambda: self.btn_calcular.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
