#   apato_103_junta_tabelas_dmd_fcst1


import duckdb

CAMINHO_BANCO = r"D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb"

def apato_103_junta_tabelas_dmd_fcst1(db_path: str = CAMINHO_BANCO):

    print("1. Conectando ao DuckDB...")
    con = duckdb.connect(db_path)

    try:
        print("2. Removendo tabela tb_dmd_fcst (se existir)...")
        con.execute("DROP TABLE IF EXISTS tb_dmd_fcst;")

        print("3. Criando tabela tb_dmd_fcst via JOIN das tabelas parciais...")

        con.execute("""
            CREATE TABLE tb_dmd_fcst AS
            SELECT
                t24.sku,

                t24.corr_menos24,
                t23.corr_menos23,
                t22.corr_menos22,
                t21.corr_menos21,
                t20.corr_menos20,
                t19.corr_menos19,
                t18.corr_menos18,
                t17.corr_menos17,
                t16.corr_menos16,
                t15.corr_menos15,
                t14.corr_menos14,
                t13.corr_menos13,
                t12.corr_menos12,
                t11.corr_menos11,
                t10.corr_menos10,
                t9.corr_menos9,
                t8.corr_menos8,
                t7.corr_menos7,
                t6.corr_menos6,
                t5.corr_menos5,
                t4.corr_menos4,
                t3.corr_menos3,
                t2.corr_menos2,
                t1.corr_menos1,

                tc.mes_corrente AS corr,

                tm1.corr_mais1,
                tm2.corr_mais2,
                tm3.corr_mais3,
                tm4.corr_mais4,
                tm5.corr_mais5,
                tm6.corr_mais6,
                tm7.corr_mais7,
                tm8.corr_mais8,
                tm9.corr_mais9,
                tm10.corr_mais10,
                tm11.corr_mais11

            FROM tb_corr_menos24 t24
            LEFT JOIN tb_corr_menos23 t23 USING (sku)
            LEFT JOIN tb_corr_menos22 t22 USING (sku)
            LEFT JOIN tb_corr_menos21 t21 USING (sku)
            LEFT JOIN tb_corr_menos20 t20 USING (sku)
            LEFT JOIN tb_corr_menos19 t19 USING (sku)
            LEFT JOIN tb_corr_menos18 t18 USING (sku)
            LEFT JOIN tb_corr_menos17 t17 USING (sku)
            LEFT JOIN tb_corr_menos16 t16 USING (sku)
            LEFT JOIN tb_corr_menos15 t15 USING (sku)
            LEFT JOIN tb_corr_menos14 t14 USING (sku)
            LEFT JOIN tb_corr_menos13 t13 USING (sku)
            LEFT JOIN tb_corr_menos12 t12 USING (sku)
            LEFT JOIN tb_corr_menos11 t11 USING (sku)
            LEFT JOIN tb_corr_menos10 t10 USING (sku)
            LEFT JOIN tb_corr_menos9 t9 USING (sku)
            LEFT JOIN tb_corr_menos8 t8 USING (sku)
            LEFT JOIN tb_corr_menos7 t7 USING (sku)
            LEFT JOIN tb_corr_menos6 t6 USING (sku)
            LEFT JOIN tb_corr_menos5 t5 USING (sku)
            LEFT JOIN tb_corr_menos4 t4 USING (sku)
            LEFT JOIN tb_corr_menos3 t3 USING (sku)
            LEFT JOIN tb_corr_menos2 t2 USING (sku)
            LEFT JOIN tb_corr_menos1 t1 USING (sku)

            LEFT JOIN tb_corr tc USING (sku)

            LEFT JOIN tb_corr_mais1 tm1 USING (sku)
            LEFT JOIN tb_corr_mais2 tm2 USING (sku)
            LEFT JOIN tb_corr_mais3 tm3 USING (sku)
            LEFT JOIN tb_corr_mais4 tm4 USING (sku)
            LEFT JOIN tb_corr_mais5 tm5 USING (sku)
            LEFT JOIN tb_corr_mais6 tm6 USING (sku)
            LEFT JOIN tb_corr_mais7 tm7 USING (sku)
            LEFT JOIN tb_corr_mais8 tm8 USING (sku)
            LEFT JOIN tb_corr_mais9 tm9 USING (sku)
            LEFT JOIN tb_corr_mais10 tm10 USING (sku)
            LEFT JOIN tb_corr_mais11 tm11 USING (sku);
        """)

        print("4. Tabela tb_dmd_fcst criada com sucesso.")

    finally:
        con.close()


if __name__ == "__main__":
    apato_103_junta_tabelas_dmd_fcst1()
