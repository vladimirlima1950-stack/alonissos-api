# apato_vendas_gerador de cnaes



import os
import pandas as pd
from tqdm import tqdm

# Caminho da pasta de estabelecimentos
caminho_estabelecimentos = r'D:\Mupe Consultoria\Projeto Vendas\Estabelecimentos'

# CNAEs-alvo
cnaes_desejados = ['4661300', '4662100', '2853400']

# Colunas dos arquivos de estabelecimentos (sem cabeçalho)
colunas_estabelecimentos = [
    'CNPJ_Basico', 'CNPJ_Ordem', 'CNPJ_DV', 'Identificador_Matriz_Filial',
    'Nome_Fantasia', 'Situacao_Cadastral', 'Data_Situacao_Cadastral',
    'Motivo_Situacao_Cadastral', 'Nome_Cidade_Exterior', 'Pais',
    'Data_Inicio_Atividade', 'CNAE_Fiscal_Principal', 'CNAE_Fiscal_Secundaria',
    'Tipo_Logradouro', 'Logradouro', 'Numero', 'Complemento',
    'Bairro', 'CEP', 'UF', 'Municipio', 'DDD_1', 'Telefone_1',
    'DDD_2', 'Telefone_2', 'DDD_Fax', 'Fax', 'Email', 'Situacao_Especial',
    'Data_Situacao_Especial'
]

# Listar arquivos
todos_arquivos = [
    os.path.join(caminho_estabelecimentos, f)
    for f in os.listdir(caminho_estabelecimentos)
    if 'ESTABELE' in f
]

# 🔁 Controle por lote (ex: processar só os 5 primeiros arquivos)
arquivos_lote = todos_arquivos[:5]  # Altere para [:10], [:20], etc. conforme desejar

# Função com barra de progresso
def ler_estabelecimentos_filtrados(arquivos, colunas, filtro_cnaes):
    dfs = []
    for arq in tqdm(arquivos, desc="🔍 Processando arquivos"):
        try:
            for chunk in pd.read_csv(
                arq,
                sep=';',
                header=None,
                names=colunas,
                encoding='latin1',
                dtype=str,
                on_bad_lines='skip',
                low_memory=False,
                chunksize=100_000
            ):
                filtrado = chunk[chunk['CNAE_Fiscal_Principal'].isin(filtro_cnaes)]
                dfs.append(filtrado)
        except Exception as e:
            print(f"❌ Erro ao ler {arq}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# Gerar base filtrada
df_filtrado = ler_estabelecimentos_filtrados(arquivos_lote, colunas_estabelecimentos, cnaes_desejados)

# Salvar como CSV
caminho_saida = r'D:\Mupe Consultoria\Projeto Vendas\estabelecimentos_filtrados.csv'
df_filtrado.to_csv(caminho_saida, index=False, encoding='utf-8')

print(f"\n✅ Arquivo filtrado gerado com sucesso: {caminho_saida}")