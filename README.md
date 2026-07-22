# Calculadora de Custo de Viagem por CEP

Programa 100% em Python (usa apenas `tkinter`, que já vem com o Python, e
`requests` para consultar as APIs).

## O que o programa faz

1. Você digita o **CEP de origem** e clica em "Buscar CEP" → o endereço aparece
   automaticamente.
2. Você digita o **número** do endereço de origem.
3. Você digita o **CEP de destino** e clica em "Buscar CEP" → o endereço aparece.
4. Você digita o **número** do endereço de destino.
5. Marca (ou não) a opção **"Calcular ida e volta"**.
6. Informa quantos **km o seu carro faz por litro** e o **preço do litro da
   gasolina**.
7. Clica em **"Calcular distância e custo"** e o programa mostra:
   - a distância só de ida,
   - a distância total (ida ou ida+volta),
   - quantos litros de combustível serão gastos,
   - o **custo total estimado da viagem em R$**.

## APIs usadas (todas gratuitas, sem necessidade de cadastro/chave)

- **ViaCEP** — converte CEP em endereço (rua, bairro, cidade, UF).
- **Nominatim (OpenStreetMap)** — converte o endereço em coordenadas
  (latitude/longitude).
- **OSRM** — calcula a distância real da rota rodoviária entre as duas
  coordenadas.

> É necessário estar conectado à internet para usar o programa, pois ele
> consulta essas três APIs públicas.

---

## Como executar o programa (sem gerar .exe)

1. Instale o Python 3.10 ou superior: https://www.python.org/downloads/
   (durante a instalação no Windows, marque a opção **"Add python.exe to PATH"**)
2. Abra o terminal (cmd/PowerShell) na pasta do projeto e instale a dependência:

   ```
   pip install requests
   ```

3. Execute:

   ```
   python calculadora_viagem.py
   ```

---

## Como gerar o executável (.exe) para Windows

O `.exe` precisa ser gerado **em um computador Windows** (o PyInstaller cria o
executável para o mesmo sistema operacional em que ele é executado).

1. Instale o Python no Windows (se ainda não tiver).
2. Abra o cmd/PowerShell na pasta onde está o arquivo `calculadora_viagem.py`.
3. Instale as dependências:

   ```
   pip install requests pyinstaller
   ```

4. Gere o executável com um único arquivo, sem console (só a janela gráfica):

   ```
   pyinstaller --onefile --windowed --name "CalculadoraViagem" calculadora_viagem.py
   ```

5. O executável ficará em:

   ```
   dist\CalculadoraViagem.exe
   ```

6. É só copiar esse `.exe` e usar/distribuir. Não precisa instalar Python na
   máquina que só vai **rodar** o programa — só é preciso Python na máquina
   onde você **gera** o `.exe`.

### Observações

- Se o Windows/antivírus alertar sobre o executável (comum com PyInstaller,
  por ser um "falso positivo"), você pode liberar manualmente ou assinar o
  executável digitalmente, se necessário para distribuição.
- Para trocar o ícone do programa, adicione `--icon=caminho\para\icone.ico`
  no comando do PyInstaller.
- Se quiser gerar o `.exe` a partir de um Mac/Linux, isso não é possível
  diretamente — o PyInstaller sempre compila para o sistema operacional em
  que está rodando.

---

## Estrutura do projeto

```
projeto_viagem/
├── calculadora_viagem.py   ← código-fonte do programa
├── requirements.txt        ← dependências (requests, pyinstaller)
└── README.md                ← este arquivo
```
