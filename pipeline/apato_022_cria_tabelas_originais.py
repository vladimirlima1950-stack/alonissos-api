# apato_022_cria_tabelas_originais - português

# apato_022_cria_tabelas_originais - versão multi-cliente

import sys
import os
import duckdb
import pandas as pd
from datetime import datetime

# ============================================================
# 1. RECEBE O CAMINHO DO CLIENTE
# ============================================================

if len(sys.argv) < 2:
    print("Erro: o programa deve receber o caminho do cliente como parâmetro.")
    sys.exit(1)

pasta_cliente = sys.argv[1]

pasta_entrada = os.path.join(pasta_cliente, "entrada")
pasta_processamento = os.path.join(pasta_cliente, "processamento")

os.makedirs(pasta_processamento, exist_ok=True)

# Banco DuckDB do cliente
caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
conn = duckdb.connect(caminho_banco)

# ============================================================
# Funções auxiliares
# ============================================================

def converte_numero(valor, padrao=1.00):
    try:
        return float(str(valor).replace(',', '.'))
    except:
        return padrao

def converte_data(valor):
    try:
        valor = str(valor).strip()
        if not valor or valor.lower() in ['nan', 'nat']:
            return None
        try:
            return datetime.strptime(valor, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return datetime.strptime(valor, '%d/%m/%y').strftime('%Y-%m-%d')
    except:
        return None

def preparar_tabela(nome_tabela, ddl):
    conn.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
    conn.execute(ddl)
    print(f" Tabela {nome_tabela} recriada.")


# ============================================================
# 1. tb_custo_orig
# ============================================================

preparar_tabela("tb_custo_orig", """
CREATE TABLE tb_custo_orig (
    sku TEXT,
    custo_unit DOUBLE
)
""")

df_custo = pd.read_csv(
    os.path.join(pasta_entrada, "tb_custo_orig.csv"),
    sep=';',
    encoding='latin1',
    header=None
)

df_custo.columns = ['sku', 'custo_unit']

df_custo['custo_unit'] = df_custo['custo_unit'].apply(lambda x: converte_numero(x, 1.00))
df_custo.loc[df_custo['custo_unit'] < 0, 'custo_unit'] = 1

df_custo = df_custo.groupby('sku', as_index=False)['custo_unit'].max()

conn.register('df_custo', df_custo)
conn.execute("CREATE OR REPLACE TABLE tb_custo_orig AS SELECT * FROM df_custo")

conn.execute("DROP TABLE IF EXISTS tb_custos")
conn.execute("CREATE TABLE tb_custos AS SELECT * FROM df_custo")


# ============================================================
# 2. tb_estoques_orig
# ============================================================

preparar_tabela("tb_estoques_orig", """
CREATE TABLE tb_estoques_orig (
    sku TEXT,
    qtde_orig DOUBLE
)
""")

df_estoque = pd.read_csv(
    os.path.join(pasta_entrada, "tb_estoques_orig.csv"),
    sep=';',
    encoding='latin1',
    header=None
)

df_estoque.columns = ['sku', 'qtde_orig']

df_estoque['qtde_orig'] = df_estoque['qtde_orig'].apply(lambda x: converte_numero(x, 0))
df_estoque = df_estoque.groupby('sku', as_index=False)['qtde_orig'].sum()
df_estoque['qtde_orig'] = df_estoque['qtde_orig'].apply(lambda x: max(x, 0))

conn.register('df_estoque', df_estoque)
conn.execute("CREATE OR REPLACE TABLE tb_estoques_orig AS SELECT * FROM df_estoque")

conn.execute("DROP TABLE IF EXISTS tb_estoques")
conn.execute("CREATE TABLE tb_estoques AS SELECT * FROM df_estoque")


# ============================================================
# 3. tb_leadtime_orig
# ============================================================

preparar_tabela("tb_leadtime_orig", """
CREATE TABLE tb_leadtime_orig (
    sku TEXT,
    leadtime INTEGER
)
""")

df_lead = pd.read_csv(
    os.path.join(pasta_entrada, "tb_leadtime_orig.csv"),
    sep=';',
    encoding='latin1',
    header=None
)

df_lead.columns = ['sku', 'leadtime']

df_lead['leadtime'] = df_lead['leadtime'].apply(lambda x: converte_numero(x, 30))
df_lead['leadtime'] = df_lead['leadtime'].fillna(30).astype(int)

df_lead = df_lead.groupby('sku', as_index=False)['leadtime'].max()

conn.register('df_lead', df_lead)
conn.execute("DELETE FROM tb_leadtime_orig")
conn.execute("INSERT INTO tb_leadtime_orig SELECT * FROM df_lead")

conn.execute("DROP TABLE IF EXISTS tb_leadtime")
conn.execute("""
    CREATE TABLE tb_leadtime AS
    SELECT sku, leadtime
    FROM tb_leadtime_orig
""")


# ============================================================
# 4. tb_sku_status_orig
# ============================================================

preparar_tabela("tb_sku_status_orig", """
CREATE TABLE tb_sku_status_orig (
    sku TEXT,
    situacao TEXT
)
""")

df_status = pd.read_csv(
    os.path.join(pasta_entrada, "tb_sku_status_orig.csv"),
    sep=';',
    encoding='latin1',
    header=None
)

df_status.columns = ['sku', 'situacao']

df_status['situacao'] = df_status['situacao'].fillna('ATIVO')

conn.register('df_status', df_status)
conn.execute("DROP TABLE IF EXISTS tb_sku_status")
conn.execute("CREATE TABLE tb_sku_status AS SELECT * FROM df_status")


# ============================================================
# 5. tb_vendas_orig
# ============================================================

preparar_tabela("tb_vendas_orig", """
CREATE TABLE tb_vendas_orig (
    sku TEXT,
    numero_ordem TEXT,
    data_desejada DATE,
    qtde_desejada_orig DOUBLE
)
""")

df_vendas = pd.read_csv(
    os.path.join(pasta_entrada, "tb_vendas_orig.csv"),
    sep=';',
    encoding='latin1',
    header=None
)

df_vendas.columns = ['sku', 'numero_ordem', 'data_desejada', 'qtde_desejada_orig']

df_vendas['numero_ordem'] = df_vendas['numero_ordem'].fillna('AAAAAA')
df_vendas['data_desejada'] = df_vendas['data_desejada'].apply(converte_data)
df_vendas['qtde_desejada_orig'] = df_vendas['qtde_desejada_orig'].apply(lambda x: converte_numero(x, 0))

conn.register('df_vendas', df_vendas)
conn.execute("INSERT INTO tb_vendas_orig SELECT * FROM df_vendas")

conn.execute("DROP TABLE IF EXISTS tb_vendas")
conn.execute("""
    CREATE TABLE tb_vendas AS
    SELECT 
        sku,
        numero_ordem,
        data_desejada,
        qtde_desejada_orig AS qtde_pedida_orig,
        qtde_desejada_orig AS qtde_pedida
    FROM tb_vendas_orig
""")

print("Todas as tabelas foram recriadas e os dados foram importados com sucesso!")

conn.close()
