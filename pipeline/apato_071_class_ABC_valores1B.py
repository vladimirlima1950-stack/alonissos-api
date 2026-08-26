import os
import duckdb
import pandas as pd

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Criar tabela intermediária com agregação por SKU
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_class_valores21")
    conn.execute("""
        CREATE TABLE tb_class_valores21 AS
        SELECT 
            sku,
            SUM(valor_ordem) AS valor_ordem_12meses,
            MAX(situacao) AS situacao
        FROM tb_class_valores1
        GROUP BY sku
        ORDER BY valor_ordem_12meses DESC, sku
    """)

    # ============================================================
    # 2) Calcular total de valores
    # ============================================================

    tot_valores = float(conn.execute("""
        SELECT SUM(valor_ordem_12meses) FROM tb_class_valores21
    """).fetchone()[0] or 0)

    # ============================================================
    # 3) Criar tabela final
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_class_valores2")
    conn.execute("""
        CREATE TABLE tb_class_valores2 (
            sku VARCHAR(30),
            valor_ordem_12meses DECIMAL(15,6),
            situacao VARCHAR(50),
            porct DECIMAL(10,6),
            porct_acum DECIMAL(10,6),
            class_ABC_valores VARCHAR(2),
            id INT
        )
    """)

    # ============================================================
    # 4) Calcular percentuais e inserir na tabela final
    # ============================================================

    df = conn.execute("""
        SELECT sku, valor_ordem_12meses, situacao
        FROM tb_class_valores21
        ORDER BY valor_ordem_12meses DESC, sku
    """).fetchdf()

    acumulado = 0.0

    for idx, row in df.iterrows():
        sku = row['sku']
        valor = float(row['valor_ordem_12meses'])
        situacao = row['situacao']

        porct = valor / tot_valores if tot_valores > 0 else 0.0
        acumulado += porct

        conn.execute("""
            INSERT INTO tb_class_valores2 (sku, valor_ordem_12meses, situacao, porct, porct_acum, class_ABC_valores, id)
            VALUES (?, ?, ?, ?, ?, NULL, ?)
        """, [sku, valor, situacao, porct, acumulado, idx + 1])

    print("Tabela tb_class_valores2 criada com sucesso com percentuais e acumulados.")

    conn.close()
