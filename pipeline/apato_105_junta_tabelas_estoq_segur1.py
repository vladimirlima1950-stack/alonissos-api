# apato_105_junta_tabelas_estoque_segur1
# import mysql.connector


# apato_105_junta_tabelas_estoq_segur1 - versão multi-cliente
# Equivalente ao MySQL sp14

import sys
import os
import duckdb

def apato_105_junta_tabelas_estoq_segur1(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("1. Conectando ao DuckDB...")
    con = duckdb.connect(caminho_banco, read_only=False)

    try:
        # ============================================================
        # 1) Criar tb_estoq_segur_12meses via JOIN (equivalente ao SP14)
        # ============================================================
        print("2. Criando tabela tb_estoq_segur_12meses...")

        con.execute("DROP TABLE IF EXISTS tb_estoq_segur_12meses;")

        con.execute("""
            CREATE TABLE tb_estoq_segur_12meses AS
            SELECT
                t0.sku,
                t0.es_mes_corrente,
                t1.es_corr_mais1,
                t2.es_corr_mais2,
                t3.es_corr_mais3,
                t4.es_corr_mais4,
                t5.es_corr_mais5,
                t6.es_corr_mais6,
                t7.es_corr_mais7,
                t8.es_corr_mais8,
                t9.es_corr_mais9,
                t10.es_corr_mais10,
                t11.es_corr_mais11
            FROM tb_es_corr t0
            LEFT JOIN tb_es_corr_mais1 t1 USING (sku)
            LEFT JOIN tb_es_corr_mais2 t2 USING (sku)
            LEFT JOIN tb_es_corr_mais3 t3 USING (sku)
            LEFT JOIN tb_es_corr_mais4 t4 USING (sku)
            LEFT JOIN tb_es_corr_mais5 t5 USING (sku)
            LEFT JOIN tb_es_corr_mais6 t6 USING (sku)
            LEFT JOIN tb_es_corr_mais7 t7 USING (sku)
            LEFT JOIN tb_es_corr_mais8 t8 USING (sku)
            LEFT JOIN tb_es_corr_mais9 t9 USING (sku)
            LEFT JOIN tb_es_corr_mais10 t10 USING (sku)
            LEFT JOIN tb_es_corr_mais11 t11 USING (sku);
        """)

        print("3. Criando tabela tb_estoq_segur_12meses_res...")

        con.execute("DROP TABLE IF EXISTS tb_estoq_segur_12meses_res;")

        con.execute("""
            CREATE TABLE tb_estoq_segur_12meses_res AS
            SELECT
                sku,
                SUM(es_mes_corrente) AS es_mes_corrente,
                SUM(es_corr_mais1) AS es_corr_mais1,
                SUM(es_corr_mais2) AS es_corr_mais2,
                SUM(es_corr_mais3) AS es_corr_mais3,
                SUM(es_corr_mais4) AS es_corr_mais4,
                SUM(es_corr_mais5) AS es_corr_mais5,
                SUM(es_corr_mais6) AS es_corr_mais6,
                SUM(es_corr_mais7) AS es_corr_mais7,
                SUM(es_corr_mais8) AS es_corr_mais8,
                SUM(es_corr_mais9) AS es_corr_mais9,
                SUM(es_corr_mais10) AS es_corr_mais10,
                SUM(es_corr_mais11) AS es_corr_mais11
            FROM tb_estoq_segur_12meses
            GROUP BY sku;
        """)

        print("4. Adicionando colunas de classificação...")

        con.execute("ALTER TABLE tb_estoq_segur_12meses_res ADD COLUMN class_abc_pedidos VARCHAR;")
        con.execute("ALTER TABLE tb_estoq_segur_12meses_res ADD COLUMN class_abc_valores VARCHAR;")

        print("5. Atualizando class_abc_pedidos...")

        con.execute("""
            UPDATE tb_estoq_segur_12meses_res
            SET class_abc_pedidos = p.class_ABC_pedidos
            FROM tb_class_pedidos2 p
            WHERE tb_estoq_segur_12meses_res.sku = p.sku;
        """)

        print("6. Atualizando class_abc_valores...")

        con.execute("""
            UPDATE tb_estoq_segur_12meses_res
            SET class_abc_valores = v.class_ABC_valores
            FROM tb_class_valores2 v
            WHERE tb_estoq_segur_12meses_res.sku = v.sku;
        """)

        print("7. Criando tabela tb_estoq_segur_12meses_res_fim...")

        con.execute("DROP TABLE IF EXISTS tb_estoq_segur_12meses_res_fim;")

        con.execute("""
            CREATE TABLE tb_estoq_segur_12meses_res_fim AS
            SELECT
                class_abc_pedidos,
                class_abc_valores,
                sku,
                es_mes_corrente,
                es_corr_mais1,
                es_corr_mais2,
                es_corr_mais3,
                es_corr_mais4,
                es_corr_mais5,
                es_corr_mais6,
                es_corr_mais7,
                es_corr_mais8,
                es_corr_mais9,
                es_corr_mais10,
                es_corr_mais11
            FROM tb_estoq_segur_12meses_res
            ORDER BY class_abc_pedidos, class_abc_valores, sku;
        """)

        print("8. Aplicando FLOOR() em todas as colunas numéricas...")

        con.execute("""
            UPDATE tb_estoq_segur_12meses_res_fim
            SET
                es_mes_corrente = FLOOR(es_mes_corrente),
                es_corr_mais1 = FLOOR(es_corr_mais1),
                es_corr_mais2 = FLOOR(es_corr_mais2),
                es_corr_mais3 = FLOOR(es_corr_mais3),
                es_corr_mais4 = FLOOR(es_corr_mais4),
                es_corr_mais5 = FLOOR(es_corr_mais5),
                es_corr_mais6 = FLOOR(es_corr_mais6),
                es_corr_mais7 = FLOOR(es_corr_mais7),
                es_corr_mais8 = FLOOR(es_corr_mais8),
                es_corr_mais9 = FLOOR(es_corr_mais9),
                es_corr_mais10 = FLOOR(es_corr_mais10),
                es_corr_mais11 = FLOOR(es_corr_mais11);
        """)

        print("9. apato_105_junta_tabelas_estoq_segur1 concluído com sucesso.")

    finally:
        con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_105_junta_tabelas_estoq_segur1(pasta_cliente)
