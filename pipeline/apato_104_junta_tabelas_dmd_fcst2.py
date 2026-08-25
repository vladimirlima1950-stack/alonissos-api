# apato_104_junta_tabelas_dmd_fcst2



import duckdb

CAMINHO_BANCO = r"D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb"

def apato_104_junta_tabelas_dmd_fcst2(db_path: str = CAMINHO_BANCO):

    print("1. Conectando ao DuckDB...")
    con = duckdb.connect(db_path)

    try:
        # ============================================================
        # 1) Criar tb_dmd_fcst_res com mesma estrutura de tb_dmd_fcst
        # ============================================================
        print("2. Criando tabela tb_dmd_fcst_res...")

        con.execute("DROP TABLE IF EXISTS tb_dmd_fcst_res;")

        con.execute("""
            CREATE TABLE tb_dmd_fcst_res AS
            SELECT *
            FROM tb_dmd_fcst
            LIMIT 0;
        """)

        # ============================================================
        # 2) Inserir dados agregados (SUM + GROUP BY)
        # ============================================================
        print("3. Inserindo agregados em tb_dmd_fcst_res...")

        con.execute("""
            INSERT INTO tb_dmd_fcst_res
            SELECT
                sku,
                SUM(corr_menos24), SUM(corr_menos23), SUM(corr_menos22),
                SUM(corr_menos21), SUM(corr_menos20), SUM(corr_menos19),
                SUM(corr_menos18), SUM(corr_menos17), SUM(corr_menos16),
                SUM(corr_menos15), SUM(corr_menos14), SUM(corr_menos13),
                SUM(corr_menos12), SUM(corr_menos11), SUM(corr_menos10),
                SUM(corr_menos9), SUM(corr_menos8), SUM(corr_menos7),
                SUM(corr_menos6), SUM(corr_menos5), SUM(corr_menos4),
                SUM(corr_menos3), SUM(corr_menos2), SUM(corr_menos1),
                SUM(corr),
                SUM(corr_mais1), SUM(corr_mais2), SUM(corr_mais3),
                SUM(corr_mais4), SUM(corr_mais5), SUM(corr_mais6),
                SUM(corr_mais7), SUM(corr_mais8), SUM(corr_mais9),
                SUM(corr_mais10), SUM(corr_mais11)
            FROM tb_dmd_fcst
            GROUP BY sku;
        """)

        # ============================================================
        # 3) Adicionar colunas class_pedidos e class_valores
        # ============================================================
        print("4. Adicionando colunas de classificação...")

        con.execute("ALTER TABLE tb_dmd_fcst_res ADD COLUMN class_pedidos VARCHAR;")
        con.execute("ALTER TABLE tb_dmd_fcst_res ADD COLUMN class_valores VARCHAR;")

        # ============================================================
        # 4) Preencher classes ABC via JOIN
        # ============================================================
        print("5. Atualizando class_pedidos...")

        con.execute("""
            UPDATE tb_dmd_fcst_res
            SET class_pedidos = p.class_ABC_pedidos
            FROM tb_class_pedidos2 p
            WHERE tb_dmd_fcst_res.sku = p.sku;
        """)

        print("6. Atualizando class_valores...")

        con.execute("""
            UPDATE tb_dmd_fcst_res
            SET class_valores = v.class_ABC_valores
            FROM tb_class_valores2 v
            WHERE tb_dmd_fcst_res.sku = v.sku;
        """)

        # ============================================================
        # 5) Criar tabela final tb_dmd_fcst_res_fim
        # ============================================================
        print("7. Criando tabela tb_dmd_fcst_res_fim...")

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
                corr, corr_mais1, corr_mais2,
                corr_mais3, corr_mais4, corr_mais5,
                corr_mais6, corr_mais7, corr_mais8,
                corr_mais9, corr_mais10, corr_mais11
            FROM tb_dmd_fcst_res
            ORDER BY class_pedidos, class_valores, sku;
        """)

        # ============================================================
        # 6) Aplicar FLOOR() em todas as colunas numéricas
        # ============================================================
        print("8. Aplicando FLOOR em todas as colunas numéricas...")

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

        print("9. apato_104_junta_tabelas_dmd_fcst2 concluído com sucesso.")

    finally:
        con.close()


if __name__ == "__main__":
    apato_104_junta_tabelas_dmd_fcst2()
