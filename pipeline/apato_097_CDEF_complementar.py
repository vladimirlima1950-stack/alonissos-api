import os
import duckdb
from datetime import datetime

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    inicio = datetime.now()
    con = duckdb.connect(caminho_banco, read_only=False)

    # ============================================================
    # 1) Obter total de SKUs
    # ============================================================
    total_skus = con.execute("""
        SELECT COUNT(DISTINCT sku)
        FROM tb_vendas_total2
    """).fetchone()[0]

    v_offset = 0
    v_limit = 1000

    # ============================================================
    # 2) Criar tabela final
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_DEF_complementar;")
    con.execute("""
        CREATE TABLE tb_DEF_complementar (
            sku VARCHAR,
            ano_mes VARCHAR,
            qtde DECIMAL(13,2),
            class_ABC_pedidos VARCHAR,
            lead_time_dias INTEGER,
            previsao DECIMAL(10,2),
            estoq_segur DECIMAL(10,2)
        );
    """)

    # ============================================================
    # 3) Processamento em blocos
    # ============================================================
    while True:

        con.execute("DROP TABLE IF EXISTS temp_skus;")
        con.execute(f"""
            CREATE TEMP TABLE temp_skus AS
            SELECT sku
            FROM (
                SELECT DISTINCT sku
                FROM tb_vendas_total2
                ORDER BY sku
                LIMIT {v_limit} OFFSET {v_offset}
            );
        """)

        count_block = con.execute("SELECT COUNT(*) FROM temp_skus;").fetchone()[0]
        if count_block == 0:
            break

        con.execute("""
            INSERT INTO tb_DEF_complementar (sku, ano_mes, qtde)
            SELECT v.sku, v.ano_mes, SUM(v.qtde_pedida)
            FROM tb_vendas_total2 v
            INNER JOIN temp_skus t ON v.sku = t.sku
            GROUP BY v.sku, v.ano_mes;
        """)

        v_offset += v_limit

    # ============================================================
    # 4) Atualizar classificação ABC
    # ============================================================
    con.execute("""
        UPDATE tb_DEF_complementar
        SET class_ABC_pedidos = cp.class_ABC_pedidos
        FROM tb_class_pedidos2 cp
        WHERE tb_DEF_complementar.sku = cp.sku;
    """)

    # ============================================================
    # 5) Reclassificar SKUs inativos como 'E'
    # ============================================================
    con.execute("""
        UPDATE tb_DEF_complementar
        SET class_ABC_pedidos = 'E'
        FROM tb_sku_status_orig s
        WHERE tb_DEF_complementar.sku = s.sku
          AND s.situacao = 'INATIVO';
    """)

    # ============================================================
    # 6) Preencher nulos com 'D'
    # ============================================================
    con.execute("""
        UPDATE tb_DEF_complementar
        SET class_ABC_pedidos = 'D'
        WHERE class_ABC_pedidos IS NULL;
    """)

    # ============================================================
    # 7) Remover SKUs das classes A, B, C
    # ============================================================
    con.execute("""
        DELETE FROM tb_DEF_complementar
        WHERE class_ABC_pedidos IN ('A', 'B', 'C')
           OR class_ABC_pedidos IS NULL;
    """)

    # ============================================================
    # 8) Preencher previsao e estoq_segur com zero
    # ============================================================
    con.execute("""
        UPDATE tb_DEF_complementar
        SET previsao = 0,
            estoq_segur = 0;
    """)

    # ============================================================
    # 9) Atualizar lead_time_dias
    # ============================================================
    con.execute("""
        UPDATE tb_DEF_complementar
        SET lead_time_dias = lt.leadtime
        FROM (
            SELECT sku, leadtime
            FROM tb_leadtime
            GROUP BY sku, leadtime
        ) AS lt
        WHERE tb_DEF_complementar.sku = lt.sku;
    """)

    con.close()
    fim = datetime.now()

    return {
        "nome_programa": "apato_097_CDEF_complementar",
        "inicio": str(inicio),
        "fim": str(fim),
        "status": "OK",
        "mensagem": "Programa executado com sucesso."
    }
