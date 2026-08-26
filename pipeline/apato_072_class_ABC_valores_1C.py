import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Classificação ABC por valor acumulado e situação
    # ============================================================

    conn.execute("""
        UPDATE tb_class_valores2
        SET class_ABC_valores = CASE
            WHEN porct_acum < 0.8
                 AND TRIM(situacao) ILIKE '%ativ%'
            THEN 'A'

            WHEN porct_acum >= 0.8 AND porct_acum < 0.95
                 AND TRIM(situacao) ILIKE '%ativ%'
            THEN 'B'

            WHEN porct_acum >= 0.95 AND porct_acum < 1.1
                 AND TRIM(situacao) ILIKE '%ativ%'
            THEN 'C'

            ELSE 'D'
        END
    """)

    # ============================================================
    # 2) Reclassificar como 'D' os SKUs com valor zero
    # ============================================================

    conn.execute("""
        UPDATE tb_class_valores2
        SET class_ABC_valores = 'D'
        WHERE valor_ordem_12meses = 0
    """)

    # ============================================================
    # 3) Reclassificar como 'E' os SKUs inativos
    # ============================================================

    conn.execute("""
        UPDATE tb_class_valores2
        SET class_ABC_valores = 'E'
        WHERE TRIM(situacao) ILIKE '%inativ%'
    """)

    print("Classificação ABC por valor aplicada com sucesso na tabela tb_class_valores2.")

    conn.close()
