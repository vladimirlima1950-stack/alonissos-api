# apato_106_apresenta1


# apato_106_apresenta1 - versão multi-cliente
# Equivalente ao MySQL sp_apresenta1

import sys
import os
import duckdb
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def apato_106_apresenta1(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("Conectando ao DuckDB:", caminho_banco)
    con = duckdb.connect(caminho_banco, read_only=False)

    # -------------------------------------------------------------------------
    # 1. Tabela tb_estoques_valores
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_estoques_valores AS
        WITH total_val AS (
            SELECT SUM(e.qtde_orig * c.custo_unit) AS valtotal
            FROM tb_estoques_orig e
            INNER JOIN tb_custo_orig c ON e.sku = c.sku
        )
        SELECT 
            ROW_NUMBER() OVER () AS id_sku,
            cp.class_ABC_pedidos AS class_abc_pedidos,
            cv.class_ABC_valores AS class_abc_valores,
            e.sku,
            e.qtde_orig,
            c.custo_unit,
            (e.qtde_orig * c.custo_unit) AS total_valor_sku,
            ((e.qtde_orig * c.custo_unit) / NULLIF(tv.valtotal, 0)) AS porc_valor_estoque
        FROM tb_estoques_orig e
        INNER JOIN tb_custo_orig c ON e.sku = c.sku
        LEFT JOIN tb_class_pedidos2 cp ON e.sku = cp.sku
        LEFT JOIN tb_class_valores2 cv ON e.sku = cv.sku
        CROSS JOIN total_val tv;
    """)

    # -------------------------------------------------------------------------
    # 2. Tabela tb_estoques_valores_fim
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_estoques_valores_fim AS
        SELECT 
            class_abc_pedidos AS class_ABC_pedidos,
            class_abc_valores AS class_ABC_valores,
            sku,
            qtde_orig AS qtde,
            custo_unit,
            total_valor_sku,
            porc_valor_estoque
        FROM tb_estoques_valores
        ORDER BY 
            CASE class_abc_pedidos 
                WHEN 'A' THEN 1 
                WHEN 'B' THEN 2 
                WHEN 'C' THEN 3 
                ELSE 4 
            END,
            CASE class_abc_valores 
                WHEN 'A' THEN 1 
                WHEN 'B' THEN 2 
                WHEN 'C' THEN 3 
                ELSE 4 
            END,
            sku;
    """)

    # -------------------------------------------------------------------------
    # 3. Tabela tb_apres1
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_apres1 AS
        WITH total_skus AS (
            SELECT COUNT(DISTINCT sku) AS skutotal FROM tb_class_pedidos2
        ),
        cp_com_ordem AS (
            SELECT *, ROW_NUMBER() OVER () AS id_origem FROM tb_class_pedidos2
        )
        SELECT 
            cp.id_origem,
            cp.sku,
            cp.situacao AS ativo_inativo,
            cp.class_ABC_pedidos AS class_pedidos,
            cv.class_ABC_valores AS class_custo,
            1 AS qtde_skus,
            (1.0 / NULLIF(ts.skutotal, 0)) * 100.0 AS porc_skus,
            cp.pedidos_12meses AS qtde_pedidos,
            (cp.porct * 100.0) AS porc_pedidos,
            cv.valor_ordem_12meses AS custo_12meses,
            (cv.porct * 100.0) AS porc_custo_12meses,
            ev.total_valor_sku AS custo_estoque,
            (ev.porc_valor_estoque * 100) AS porc_custo_estoque,
            
            CASE 
                WHEN COALESCE(ev.total_valor_sku, 0) = 0 THEN 999.0
                WHEN ev.total_valor_sku > 0 THEN cv.valor_ordem_12meses / ev.total_valor_sku
            END AS giro_estoque_sku,
            
            CASE 
                WHEN COALESCE(ev.total_valor_sku, 0) <= 0 AND COALESCE(cv.valor_ordem_12meses, 0) > 0 THEN 0.0
                WHEN ev.total_valor_sku > 0 AND cv.valor_ordem_12meses > 0 THEN (ev.total_valor_sku / cv.valor_ordem_12meses) * 52.0
                WHEN COALESCE(ev.total_valor_sku, 0) <= 0 AND COALESCE(cv.valor_ordem_12meses, 0) = 0 THEN NULL
                WHEN ev.total_valor_sku > 0 AND COALESCE(cv.valor_ordem_12meses, 0) = 0 THEN 999.0
            END AS cobertura_semanas_sku
            
        FROM cp_com_ordem cp
        LEFT JOIN tb_class_valores2 cv ON cp.sku = cv.sku
        LEFT JOIN tb_estoques_valores ev ON cp.sku = ev.sku
        CROSS JOIN total_skus ts;
    """)

    # -------------------------------------------------------------------------
    # 4. Tabela tb_apres1_fim
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_apres1_fim AS
        SELECT 
            sku,
            ativo_inativo,
            class_pedidos,
            class_custo,
            qtde_pedidos,
            porc_pedidos / 100.0 AS porc_pedidos,
            custo_12meses,
            porc_custo_12meses / 100.0 AS porc_custo_12meses,
            custo_estoque,
            porc_custo_estoque / 100.0 AS porc_custo_estoque,
            giro_estoque_sku,
            cobertura_semanas_sku
        FROM tb_apres1
        ORDER BY class_pedidos, class_custo, id_origem;
    """)

    # -------------------------------------------------------------------------
    # 5. Tabela tb_apres2
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_apres2 AS
        SELECT 
            class_pedidos AS classe_de_pedidos,
            class_custo AS classe_de_custo,
            SUM(qtde_skus) AS qtde_skus,
            SUM(porc_skus) AS porc_skus,
            SUM(qtde_pedidos) AS qtde_pedidos,
            SUM(porc_pedidos) AS porc_pedidos,
            SUM(custo_12meses) AS custo_12meses,
            SUM(porc_custo_12meses) AS porc_custo_12meses,
            SUM(custo_estoque) AS custo_estoque,
            SUM(porc_custo_estoque) AS porc_custo_estoque
        FROM tb_apres1
        GROUP BY class_pedidos, class_custo
        ORDER BY class_pedidos, class_custo;
    """)

    # -------------------------------------------------------------------------
    # 6. Tabela tb_apres2_fim
    # -------------------------------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE tb_apres2_fim AS
        SELECT 
            classe_de_pedidos,
            classe_de_custo,
            qtde_skus,
            porc_skus / 100.0 AS porc_skus,
            qtde_pedidos,
            porc_pedidos / 100.0 AS porc_pedidos,
            custo_12meses,
            porc_custo_12meses / 100.0 AS porc_custo_12meses,
            custo_estoque,
            porc_custo_estoque / 100.0 AS porc_custo_estoque,
            CASE 
                WHEN custo_estoque > 0 THEN (custo_12meses / custo_estoque)
                ELSE NULL
            END AS giro_do_estoque
        FROM tb_apres2
        ORDER BY classe_de_pedidos, classe_de_custo;
    """)

    print("apato_106_apresenta1 executado com sucesso.")
    return con


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_106_apresenta1(pasta_cliente)
