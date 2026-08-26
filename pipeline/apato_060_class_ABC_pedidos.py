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
    # 1) Criar tb_class_pedidos2 com colunas adicionais
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos2")
    conn.execute("""
        CREATE TABLE tb_class_pedidos2 AS
        SELECT *,
               0 AS ordem_linha,
               0.0::DECIMAL(18,10) AS porct,
               0.0::DECIMAL(18,10) AS porct_acum,
               ''::VARCHAR AS class_ABC_pedidos
        FROM tb_class_pedidos1
        ORDER BY pedidos_12meses DESC
    """)

    # ============================================================
    # 2) Numeração manual (igual ao MySQL)
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS temp_ordem")
    conn.execute("""
        CREATE TABLE temp_ordem AS
        SELECT sku,
               row_number() OVER (ORDER BY pedidos_12meses DESC) AS ordem_linha
        FROM tb_class_pedidos2
    """)

    conn.execute("""
        UPDATE tb_class_pedidos2
        SET ordem_linha = (
            SELECT ordem_linha
            FROM temp_ordem
            WHERE temp_ordem.sku = tb_class_pedidos2.sku
        )
    """)

    # ============================================================
    # 3) Corrigir valores nulos
    # ============================================================

    conn.execute("""
        UPDATE tb_class_pedidos2
        SET pedidos_12meses = COALESCE(pedidos_12meses, 0)
    """)

    # ============================================================
    # 4) Total de pedidos
    # ============================================================

    tot_pedidos = conn.execute("""
        SELECT SUM(pedidos_12meses) FROM tb_class_pedidos2
    """).fetchone()[0] or 0

    # ============================================================
    # 5) Calcular porct e porct_acum (igual ao loop do MySQL)
    # ============================================================

    df = conn.execute("""
        SELECT ordem_linha, sku, pedidos_12meses
        FROM tb_class_pedidos2
        ORDER BY ordem_linha
    """).fetchdf()

    df["porct"] = df["pedidos_12meses"] / tot_pedidos if tot_pedidos > 0 else 0
    df["porct_acum"] = df["porct"].cumsum()

    for _, row in df.iterrows():
        conn.execute("""
            UPDATE tb_class_pedidos2
            SET porct = ?, porct_acum = ?
            WHERE ordem_linha = ?
        """, [float(row["porct"]), float(row["porct_acum"]), int(row["ordem_linha"])])

    # ============================================================
    # 6) Classificação ABC por percentual acumulado
    # ============================================================

    conn.execute("""
        UPDATE tb_class_pedidos2
        SET class_ABC_pedidos = CASE
            WHEN porct_acum < 0.8 THEN 'A'
            WHEN porct_acum >= 0.8 AND porct_acum < 0.95 THEN 'B'
            WHEN porct_acum >= 0.95 AND porct_acum < 1.1 THEN 'C'
            ELSE 'D'
        END
    """)

    # ============================================================
    # 7) Ajustes adicionais
    # ============================================================

    conn.execute("""
        UPDATE tb_class_pedidos2
        SET class_ABC_pedidos = 'D'
        WHERE pedidos_12meses = 0
    """)

    conn.execute("""
        UPDATE tb_class_pedidos2
        SET class_ABC_pedidos = 'E'
        WHERE LOWER(situacao) LIKE 'inativo%'
    """)

    # ============================================================
    # 8) Verificar necessidade de reclassificação
    # ============================================================

    ver_pedidos = conn.execute("""
        SELECT MIN(pedidos_12meses)
        FROM tb_class_pedidos2
        WHERE class_ABC_pedidos = 'A'
    """).fetchone()[0] or 0

    # ============================================================
    # 9) Reclassificação por faixas absolutas
    # ============================================================

    if ver_pedidos < 12:
        conn.execute("""
            UPDATE tb_class_pedidos2
            SET class_ABC_pedidos = CASE
                WHEN LOWER(situacao) LIKE 'inativo%' THEN 'E'
                WHEN pedidos_12meses >= 12 THEN 'A'
                WHEN pedidos_12meses >= 6 AND pedidos_12meses < 12 THEN 'B'
                WHEN pedidos_12meses >= 1 AND pedidos_12meses < 6 THEN 'C'
                WHEN pedidos_12meses = 0 THEN 'D'
            END
        """)

    print("tb_class_pedidos2 criada e classificada exatamente como no MySQL.")

    conn.close()
