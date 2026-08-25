# apato_vendas_extraidor_empresas



import os
import pandas as pd
from tqdm import tqdm  # ← Adiciona a barra de progresso

# Caminhos
caminho_base = r'D:\Mupe Consultoria\Projeto Vendas'
caminho_empresas = os.path.join(caminho_base, 'Empresas')
caminho_filtrado = os.path.join(caminho_base, 'estabelecimentos_filtrados.csv')

# Colunas dos arquivos de empresas (sem cabeçalho)
colunas_empresas = [
    'CNPJ_Basico', 'Razao_Social', 'Natureza_Juridica', 'Qualificacao_Responsavel',
    'Capital_Social', 'Porte_Empresa', 'Ente_Federativo'
]

# Listar arquivos
arquivos_empresas = [
    os.path.join(caminho_empresas, f)
    for f in os.listdir(caminho_empresas)
    if 'EMPRECSV' in f
]

# Função para ler empresas com barra de progresso
def ler_empresas(arquivos, colunas):
    dfs = []
    for arq in tqdm(arquivos, desc="📦 Lendo arquivos de empresas"):
        try:
            df = pd.read_csv(
                arq,
                sep=';',
                header=None,
                names=colunas,
                encoding='latin1',
                dtype=str,
                on_bad_lines='skip',
                low_memory=False
            )
            dfs.append(df)
        except Exception as e:
            print(f"❌ Erro ao ler {arq}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# Carregar dados
df_estabelecimentos = pd.read_csv(caminho_filtrado, dtype=str)
df_empresas = ler_empresas(arquivos_empresas, colunas_empresas)

# Juntar pelo CNPJ básico
df_final = df_estabelecimentos.merge(df_empresas, on='CNPJ_Basico', how='left')

# Selecionar colunas úteis
colunas_desejadas = [
    'CNPJ_Basico',
    'Razao_Social',
    'CNAE_Fiscal_Principal',
    'UF',
    'Municipio',
    'Situacao_Cadastral',
    'Data_Inicio_Atividade'
]
colunas_existentes = [col for col in colunas_desejadas if col in df_final.columns]
df_final = df_final[colunas_existentes]

# Salvar como Excel
caminho_saida = os.path.join(caminho_base, 'Base_CNAE_Filtrada.xlsx')
df_final.to_excel(caminho_saida, index=False)

print(f"\n✅ Base final gerada com sucesso: {caminho_saida}")