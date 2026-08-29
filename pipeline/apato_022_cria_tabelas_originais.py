import os
import duckdb
import pandas as pd
from datetime import datetime

# ============================================================
# Função para localizar arquivo por palavra‑chave
# ============================================================

def encontrar_arquivo(pasta_entrada, palavra):
    palavra = palavra.lower()
    for nome in os.listdir(pasta_entrada):
        nome_lower = nome.lower()
        if palavra in nome_lower and nome_lower.endswith(".csv"):
            return os.path.join(pasta_entrada, nome)
    raise FileNotFoundError(f"Nenhum arquivo contendo '{palavra}' encontrado em {pasta_entrada}")


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

def preparar_tabela(conn, nome_tabela, ddl):
    conn.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
    conn.execute(ddl)
    print(f" Tabela {nome_tabela} recriada.")


# ============================================================
# Função principal chamada pelo pipeline mestre
# ============================================================

def run(pasta_cliente):

    pasta_entrada = os.path.join(pasta_cliente, "entrada")
    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    os.makedirs(pasta_processamento, exist_ok=True)

    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1. tb_custo_orig  (palavra‑chave: "custo")
    # ============================================================

    preparar_tabela(conn, "tb_custo_orig", """
    CREATE TABLE tb_custo_orig (
        sku TEXT,
        custo_unit DOUBLE
    )
    """)

    arquivo_custo = encontrar_arquivo(pasta_entrada, "custo")

    df_custo = pd.read_csv(arquivo_custo, sep=';', encoding='latin1', header=None)
    df_custo.columns = ['sku', 'custo_unit']

    df_custo['custo_unit'] = df_custo['custo_unit'].apply(lambda x: converte_numero(x, 1.00))
    df_custo.loc[df_custo['custo_unit'] < 0, 'custo_unit'] = 1

    df_custo = df_custo.groupby('sku', as_index=False)['custo_unit'].max()

    conn.register('df_custo', df_custo)
    conn.execute("CREATE OR REPLACE TABLE tb_custo_orig AS SELECT * FROM df_custo")
    conn.execute("DROP TABLE IF EXISTS tb_custos")
    conn.execute("CREATE TABLE tb_custos AS SELECT * FROM df_custo")

    # ============================================================
    # 2. tb_estoques_orig  (palavra‑chave: "estoque")
    # ============================================================

    preparar_tabela(conn, "tb_estoques_orig", """
    CREATE TABLE tb_estoques_orig (
        sku TEXT,
        qtde_orig DOUBLE
    )
    """)

    arquivo_estoque = encontrar_arquivo(pasta_entrada, "estoque")

    df_estoque = pd.read_csv(arquivo_estoque, sep=';', encoding='latin1', header=None)
    df_estoque.columns = ['sku', 'qtde_orig']

    df_estoque['qtde_orig'] = df_estoque['qtde_orig'].apply(lambda x: converte_numero(x, 0))
    df_estoque = df_estoque.groupby('sku', as_index=False)['qtde_orig'].sum()
    df_estoque['qtde_orig'] = df_estoque['qtde_orig'].apply(lambda x: max(x, 0))

    conn.register('df_estoque', df_estoque)
    conn.execute("CREATE OR REPLACE TABLE tb_estoques_orig AS SELECT * FROM df_estoque")
    conn.execute("DROP TABLE IF EXISTS tb_estoques")
    conn.execute("CREATE TABLE tb_estoques AS SELECT * FROM df_estoque")

    # ============================================================
    # 3. tb_leadtime_orig  (palavra‑chave: "leadtime")
    # ============================================================

    preparar_tabela(conn, "tb_leadtime_orig", """
    CREATE TABLE tb_leadtime_orig (
        sku TEXT,
        leadtime INTEGER
    )
    """)

    arquivo_lead = encontrar_arquivo(pasta_entrada, "leadtime")

    df_lead = pd.read_csv(arquivo_lead, sep=';', encoding='latin1', header=None)
    df_lead.columns = ['sku', 'leadtime']

    df_lead['leadtime'] = df_lead['leadtime'].apply(lambda x: converte_numero(x, 30))
    df_lead['leadtime'] = df_lead['leadtime'].fillna(30).astype(int)
    df_lead = df_lead.groupby('sku', as_index=False)['leadtime'].max()

    conn.register('df_lead', df_lead)
    conn.execute("DELETE FROM tb_leadtime_orig")
    conn.execute("INSERT INTO tb_leadtime_orig SELECT * FROM df_lead")

    conn.execute("DROP TABLE IF EXISTS tb_leadtime")
    conn.execute("CREATE TABLE tb_leadtime AS SELECT sku, leadtime FROM tb_leadtime_orig")

    # ============================================================
    # 4. tb_sku_status_orig  (palavra‑chave: "status")
    # ============================================================

    preparar_tabela(conn, "tb_sku_status_orig", """
    CREATE TABLE tb_sku_status_orig (
        sku TEXT,
        situacao TEXT
    )
    """)

    arquivo_status = encontrar_arquivo(pasta_entrada, "status")

    df_status = pd.read_csv(arquivo_status, sep=';', encoding='latin1', header=None)
    df_status.columns = ['sku', 'situacao']
    df_status['situacao'] = df_status['situacao'].fillna('ATIVO')

    conn.register('df_status', df_status)
    conn.execute("DROP TABLE IF EXISTS tb_sku_status")
    conn.execute("CREATE TABLE tb_sku_status AS SELECT * FROM df_status")

    # ============================================================
    # 5. tb_vendas_orig  (palavra‑chave: "venda")
    # ============================================================

    preparar_tabela(conn, "tb_vendas_orig", """
    CREATE TABLE tb_vendas_orig (
        sku TEXT,
        numero_ordem TEXT,
        data_desejada DATE,
        qtde_desejada_orig DOUBLE
    )
    """)

    arquivo_vendas = encontrar_arquivo(pasta_entrada, "venda")

    df_vendas = pd.read_csv(arquivo_vendas, sep=';', encoding='latin1', header=None)
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
