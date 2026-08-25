# apato_extrai_endereco_partindo_cnpj



import pandas as pd
import requests
import time

# Caminho completo da planilha
caminho_arquivo = r"D:\Mupe Consultoria\Projeto Vendas\CNPJs.xlsx"

# Carregar a planilha
df = pd.read_excel(caminho_arquivo)

# Função para consultar CNPJ na BrasilAPI
def consultar_cnpj(cnpj):
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            dados = response.json()
            return {
                "logradouro": dados.get("logradouro", ""),
                "numero": dados.get("numero", ""),
                "bairro": dados.get("bairro", ""),
                "municipio_endereco": dados.get("municipio", ""),
                "uf_endereco": dados.get("uf", ""),
                "cep": dados.get("cep", "")
            }
        else:
            return {
                "logradouro": "", "numero": "", "bairro": "",
                "municipio_endereco": "", "uf_endereco": "", "cep": ""
            }
    except:
        return {
            "logradouro": "", "numero": "", "bairro": "",
            "municipio_endereco": "", "uf_endereco": "", "cep": ""
        }

# Criar colunas para os dados
for coluna in ["logradouro", "numero", "bairro", "municipio_endereco", "uf_endereco", "cep"]:
    df[coluna] = ""

# Iterar sobre os CNPJs
for i, row in df.iterrows():
    cnpj = str(row["CNPJ_Basico"]).zfill(14)  # garantir 14 dígitos
    dados_endereco = consultar_cnpj(cnpj)
    for chave, valor in dados_endereco.items():
        df.at[i, chave] = valor
    time.sleep(0.5)  # evitar sobrecarga na API

# Salvar nova planilha no mesmo diretório
df.to_excel(r"D:\Mupe Consultoria\Projeto Vendas\CNPJs_enriquecida.xlsx", index=False)