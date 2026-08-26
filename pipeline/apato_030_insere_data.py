import os
import duckdb
from datetime import datetime
from dateutil.relativedelta import relativedelta

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 2. CRIAÇÃO DA TABELA DE DATAS
    # ============================================================

    # Elimina e recria a tabela
    conn.execute("DROP TABLE IF EXISTS tb_date_aux1")
    conn.execute("CREATE TABLE tb_date_aux1 (fase1 DATE)")

    # Insere 26 datas: da data atual até 25 meses atrás
    data_atual = datetime.today()
    for i in range(26):
        data_inserir = data_atual - relativedelta(months=i)
        conn.execute("INSERT INTO tb_date_aux1 VALUES (?)", [data_inserir.date()])

    print("Tabela tb_date_aux1 recriada e preenchida com 26 datas mensais retroativas.")

    conn.close()
