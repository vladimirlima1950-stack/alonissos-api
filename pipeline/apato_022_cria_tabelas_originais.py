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
        
        if palavra in nome_lower and (
            nome_lower.endswith(".csv")
            or nome_lower.endswith(".xlsx")
            or nome_lower.endswith(".xls")
        ):
            return os.path.join(pasta_entrada, nome)
    raise FileNotFoundError(f"Nenhum arquivo contendo '{palavra}' encontrado em {pasta_entrada}")


# ============================================================
# Funções auxiliares
# ============================================================

def converte_numero(valor, padrao=0):
    try:

        if pd.isna(valor):
            return padrao

        valor = str(valor).strip()

        if valor == '':
            return padrao

        # Possui vírgula e ponto
        if ',' in valor and '.' in valor:

            # Formato americano
            # Ex: 1,234.56
            if valor.rfind('.') > valor.rfind(','):
                valor = valor.replace(',', '')

            # Formato brasileiro
            # Ex: 1.234,56
            else:
                valor = valor.replace('.', '')
                valor = valor.replace(',', '.')

        # Somente vírgula
        elif ',' in valor:
            valor = valor.replace(',', '.')

        return float(valor)
    except:
        return padrao


def converte_data(valor):
    try:
        if pd.isna(valor):
            return None

        data = pd.to_datetime(
            valor,
            errors='coerce',
            dayfirst=True
        )

        if pd.isna(data):
            return None
        return data.strftime('%Y-%m-%d')

    except: 
        return None


def ler_arquivo(caminho):
    if caminho.lower().endswith('.csv'):
        return pd.read_csv(
            caminho,
            sep=';',
            encoding='latin1',
            header=None,
            dtype=str
        )

    elif caminho.lower().endswith(('.xlsx', '.xls')):
        return pd.read_excel(
            caminho,
            header=None,
            dtype=str
        )
    else:
        raise ValueError(f"Formato não suportado: {caminho}")

    

    

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

    df_custo = ler_arquivo(arquivo_custo)
    if str(df_custo.iloc[0,0]).strip().upper() in ['SKU', 'CODIGO', 'CÓDIGO', 'ITEM']:
        df_custo = df_custo.iloc[1:]
        

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

    df_estoque = ler_arquivo(arquivo_estoque)
    if str(df_estoque.iloc[0,0]).strip().upper() in ['SKU', 'CODIGO', 'CÓDIGO', 'ITEM']:
        df_estoque = df_estoque.iloc[1:]

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

    df_lead = ler_arquivo(arquivo_lead)
    if str(df_lead.iloc[0,0]).strip().upper() in ['SKU', 'CODIGO', 'CÓDIGO', 'ITEM']:
        df_lead = df_lead.iloc[1:]

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

    df_status = ler_arquivo(arquivo_status)
    if str(df_status.iloc[0,0]).strip().upper() in ['SKU', 'CODIGO', 'CÓDIGO', 'ITEM']:
        df_status = df_status.iloc[1:]


    df_status.columns = ['sku', 'situacao']
    df_status['situacao'] = (
        df_status['situacao']
        .fillna('ATIVO')
        .astype(str)
        .str.strip()
        .str.upper()
    )



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

    df_vendas = ler_arquivo(arquivo_vendas)
    if str(df_vendas.iloc[0,0]).strip().upper() in ['SKU', 'CODIGO', 'CÓDIGO', 'ITEM']:
        df_vendas = df_vendas.iloc[1:]


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
