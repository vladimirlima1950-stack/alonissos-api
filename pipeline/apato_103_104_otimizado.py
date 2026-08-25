# apato_103_104_unificado_otimizado.py




# apato_103_104_unificado_otimizado - versão multi-cliente
# Equivalente ao MySQL sp103 + sp104 unificados

import sys
import os
import duckdb

def apato_103_104_unificado(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("1. Conectando ao DuckDB...")
    con = duckdb.connect(caminho_banco, read_only=False)

    try:
        # ============================================================
        # BLOCO 1 — recriar corr_menosXX, corr, corr_maisXX (apato_101)
        # ============================================================
        print("2. Recriando tabelas de correlação (apato_101)...")

        mes_row = con.execute("SELECT MIN(ordem) AS mes FROM tb_resumo1;").fetchone()
        if mes_row is None or mes_row[0] is None:
            print("Nenhum registro em tb_resumo1 para calcular 'mes'.")
            return
        mes = int(mes_row[0])

        # 24 tabelas corr_menosXX
        for i in range(24, 0, -1):
            nome_tabela = f"tb_corr_menos{i}"
            nome_coluna = f"corr_menos{i}"
            ordem_alvo = mes + (24 - i)
            con.execute(f"DROP TABLE IF EXISTS {nome_tabela};")
            con.execute(f"""
                CREATE TABLE {nome_tabela} AS
                SELECT
                    sku,
                    qtde_pedida AS {nome_coluna}
                FROM tb_resumo1
                WHERE ordem = {ordem_alvo}
                ORDER BY sku;
            """)

        # tabela corr (previsão corrente)
        con.execute("DROP TABLE IF EXISTS tb_corr;")
        con.execute(f"""
            CREATE TABLE tb_corr AS
            SELECT
                sku,
                previsao AS mes_corrente
            FROM tb_resumo1
            WHERE ordem = {mes}
            ORDER BY sku;
        """)

        # 11 tabelas corr_maisXX
        for i in range(1, 12):
            nome_tabela = f"tb_corr_mais{i}"
            nome_coluna = f"corr_mais{i}"
            ordem_alvo = mes + i
            con.execute(f"DROP TABLE IF EXISTS {nome_tabela};")
            con.execute(f"""
                CREATE TABLE {nome_tabela} AS
                SELECT
                    sku,
                    previsao AS {nome_coluna}
                FROM tb_resumo1
                WHERE ordem = {ordem_alvo}
                ORDER BY sku;
            """)

        # ============================================================
        # BLOCO 2 — tabela unificada + PIVOT (apato_103 otimizado)
        # ============================================================
        print("3. Criando tabela unificada tb_corr_unificada...")

        con.execute("DROP TABLE IF EXISTS tb_corr_unificada;")

        con.execute("""
            CREATE TABLE tb_corr_unificada AS
            SELECT
                sku,
                CASE
                    WHEN tipo = 'menos' THEN 'corr_menos' || lag
                    WHEN tipo = 'mais'  THEN 'corr_mais'  || lag
                    WHEN tipo = 'corr'  THEN 'corr'
                END AS coluna_final,
                valor
            FROM (
                SELECT sku, 'menos' AS tipo, 24 AS lag, corr_menos24 AS valor FROM tb_corr_menos24
                UNION ALL SELECT sku, 'menos', 23, corr_menos23 FROM tb_corr_menos23
                UNION ALL SELECT sku, 'menos', 22, corr_menos22 FROM tb_corr_menos22
                UNION ALL SELECT sku, 'menos', 21, corr_menos21 FROM tb_corr_menos21
                UNION ALL SELECT sku, 'menos', 20, corr_menos20 FROM tb_corr_menos20
                UNION ALL SELECT sku, 'menos', 19, corr_menos19 FROM tb_corr_menos19
                UNION ALL SELECT sku, 'menos', 18, corr_menos18 FROM tb_corr_menos18
                UNION ALL SELECT sku, 'menos', 17, corr_menos17 FROM tb_corr_menos17
                UNION ALL SELECT sku, 'menos', 16, corr_menos16 FROM tb_corr_menos16
                UNION ALL SELECT sku, 'menos', 15, corr_menos15 FROM tb_corr_menos15
                UNION ALL SELECT sku, 'menos', 14, corr_menos14 FROM tb_corr_menos14
                UNION ALL SELECT sku, 'menos', 13, corr_menos13 FROM tb_corr_menos13
                UNION ALL SELECT sku, 'menos', 12, corr_menos12 FROM tb_corr_menos12
                UNION ALL SELECT sku, 'menos', 11, corr_menos11 FROM tb_corr_menos11
                UNION ALL SELECT sku, 'menos', 10, corr_menos10 FROM tb_corr_menos10
                UNION ALL SELECT sku, 'menos', 9, corr_menos9 FROM tb_corr_menos9
                UNION ALL SELECT sku, 'menos', 8, corr_menos8 FROM tb_corr_menos8
                UNION ALL SELECT sku, 'menos', 7, corr_menos7 FROM tb_corr_menos7
                UNION ALL SELECT sku, 'menos', 6, corr_menos6 FROM tb_corr_menos6
                UNION ALL SELECT sku, 'menos', 5, corr_menos5 FROM tb_corr_menos5
                UNION ALL SELECT sku, 'menos', 4, corr_menos4 FROM tb_corr_menos4
                UNION ALL SELECT sku, 'menos', 3, corr_menos3 FROM tb_corr_menos3
                UNION ALL SELECT sku, 'menos', 2, corr_menos2 FROM tb_corr_menos2
                UNION ALL SELECT sku, 'menos', 1, corr_menos1 FROM tb_corr_menos1

                UNION ALL SELECT sku, 'corr', 0, mes_corrente FROM tb_corr

                UNION ALL SELECT sku, 'mais', 1, corr_mais1 FROM tb_corr_mais1
                UNION ALL SELECT sku, 'mais', 2, corr_mais2 FROM tb_corr_mais2
                UNION ALL SELECT sku, 'mais', 3, corr_mais3 FROM tb_corr_mais3
                UNION ALL SELECT sku, 'mais', 4, corr_mais4 FROM tb_corr_mais4
                UNION ALL SELECT sku, 'mais', 5, corr_mais5 FROM tb_corr_mais5
                UNION ALL SELECT sku, 'mais', 6, corr_mais6 FROM tb_corr_mais6
                UNION ALL SELECT sku, 'mais', 7, corr_mais7 FROM tb_corr_mais7
                UNION ALL SELECT sku, 'mais', 8, corr_mais8 FROM tb_corr_mais8
                UNION ALL SELECT sku, 'mais', 9, corr_mais9 FROM tb_corr_mais9
                UNION ALL SELECT sku, 'mais', 10, corr_mais10 FROM tb_corr_mais10
                UNION ALL SELECT sku, 'mais', 11, corr_mais11 FROM tb_corr_mais11
            );
        """)

        print("4. Criando tabela tb_dmd_fcst via PIVOT...")

        con.execute("DROP TABLE IF EXISTS tb_dmd_fcst;")

        con.execute("""
            CREATE TABLE tb_dmd_fcst AS
            SELECT *
            FROM tb_corr_unificada
            PIVOT (
                SUM(valor)
                FOR coluna_final IN (
                    'corr_menos24', 'corr_menos23', 'corr_menos22', 'corr_menos21',
                    'corr_menos20', 'corr_menos19', 'corr_menos18', 'corr_menos17',
                    'corr_menos16', 'corr_menos15', 'corr_menos14', 'corr_menos13',
                    'corr_menos12', 'corr_menos11', 'corr_menos10', 'corr_menos9',
                    'corr_menos8', 'corr_menos7', 'corr_menos6', 'corr_menos5',
                    'corr_menos4', 'corr_menos3', 'corr_menos2', 'corr_menos1',
                    'corr',
                    'corr_mais1', 'corr_mais2', 'corr_mais3', 'corr_mais4',
                    'corr_mais5', 'corr_mais6', 'corr_mais7', 'corr_mais8',
                    'corr_mais9', 'corr_mais10', 'corr_mais11'
                )
            );
        """)

        # ============================================================
        # BLOCO 3 — apato_104 (com correção do GROUP BY)
        # ============================================================
        print("5. Criando tabela tb_dmd_fcst_res...")

        con.execute("DROP TABLE IF EXISTS tb_dmd_fcst_res;")

        con.execute("""
            CREATE TABLE tb_dmd_fcst_res AS
            SELECT *
            FROM tb_dmd_fcst
            ORDER BY sku;
        """)

        print("6. Adicionando colunas de classificação...")

        con.execute("ALTER TABLE tb_dmd_fcst_res ADD COLUMN class_pedidos VARCHAR;")
        con.execute("ALTER TABLE tb_dmd_fcst_res ADD COLUMN class_valores VARCHAR;")

        print("7. Atualizando class_pedidos...")

        con.execute("""
            UPDATE tb_dmd_fcst_res
            SET class_pedidos = p.class_ABC_pedidos
            FROM tb_class_pedidos2 p
            WHERE tb_dmd_fcst_res.sku = p.sku;
        """)

        print("8. Atualizando class_valores...")

        con.execute("""
            UPDATE tb_dmd_fcst_res
            SET class_valores = v.class_ABC_valores
            FROM tb_class_valores2 v
            WHERE tb_dmd_fcst_res.sku = v.sku;
        """)

        print("9. Criando tabela tb_dmd_fcst_res_fim...")

        con.execute("DROP TABLE IF EXISTS tb_dmd_fcst_res_fim;")

        con.execute("""
            CREATE TABLE tb_dmd_fcst_res_fim AS
            SELECT
                class_pedidos,
                class_valores,
                sku,
                corr_menos24, corr_menos23, corr_menos22,
                corr_menos21, corr_menos20, corr_menos19,
                corr_menos18, corr_menos17, corr_menos16,
                corr_menos15, corr_menos14, corr_menos13,
                corr_menos12, corr_menos11, corr_menos10,
                corr_menos9, corr_menos8, corr_menos7,
                corr_menos6, corr_menos5, corr_menos4,
                corr_menos3, corr_menos2, corr_menos1,
                corr,
                corr_mais1, corr_mais2, corr_mais3,
                corr_mais4, corr_mais5, corr_mais6,
                corr_mais7, corr_mais8, corr_mais9,
                corr_mais10, corr_mais11
            FROM tb_dmd_fcst_res
            ORDER BY class_pedidos, class_valores, sku;
        """)

        print("10. Aplicando FLOOR em todas as colunas numéricas...")

        con.execute("""
            UPDATE tb_dmd_fcst_res_fim
            SET
                corr_menos24 = FLOOR(corr_menos24),
                corr_menos23 = FLOOR(corr_menos23),
                corr_menos22 = FLOOR(corr_menos22),
                corr_menos21 = FLOOR(corr_menos21),
                corr_menos20 = FLOOR(corr_menos20),
                corr_menos19 = FLOOR(corr_menos19),
                corr_menos18 = FLOOR(corr_menos18),
                corr_menos17 = FLOOR(corr_menos17),
                corr_menos16 = FLOOR(corr_menos16),
                corr_menos15 = FLOOR(corr_menos15),
                corr_menos14 = FLOOR(corr_menos14),
                corr_menos13 = FLOOR(corr_menos13),
                corr_menos12 = FLOOR(corr_menos12),
                corr_menos11 = FLOOR(corr_menos11),
                corr_menos10 = FLOOR(corr_menos10),
                corr_menos9 = FLOOR(corr_menos9),
                corr_menos8 = FLOOR(corr_menos8),
                corr_menos7 = FLOOR(corr_menos7),
                corr_menos6 = FLOOR(corr_menos6),
                corr_menos5 = FLOOR(corr_menos5),
                corr_menos4 = FLOOR(corr_menos4),
                corr_menos3 = FLOOR(corr_menos3),
                corr_menos2 = FLOOR(corr_menos2),
                corr_menos1 = FLOOR(corr_menos1),
                corr = FLOOR(corr),
                corr_mais1 = FLOOR(corr_mais1),
                corr_mais2 = FLOOR(corr_mais2),
                corr_mais3 = FLOOR(corr_mais3),
                corr_mais4 = FLOOR(corr_mais4),
                corr_mais5 = FLOOR(corr_mais5),
                corr_mais6 = FLOOR(corr_mais6),
                corr_mais7 = FLOOR(corr_mais7),
                corr_mais8 = FLOOR(corr_mais8),
                corr_mais9 = FLOOR(corr_mais9),
                corr_mais10 = FLOOR(corr_mais10),
                corr_mais11 = FLOOR(corr_mais11);
        """)

        print("11. Programa unificado concluído com sucesso.")

    finally:
        con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_103_104_unificado(pasta_cliente)
