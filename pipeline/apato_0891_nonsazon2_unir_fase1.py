import os
import duckdb
import pandas as pd

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("1. Conectando ao DuckDB...")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    try:
        print("2. Carregando tabelas fase1...")

        tabelas_origem = {
            "AA": "tb_A_trend3_somas_e_medias_fase1_AA",
            "AB": "tb_A_trend3_somas_e_medias_fase1_AB",
            "AC": "tb_A_trend3_somas_e_medias_fase1_AC",
            "BA": "tb_A_trend3_somas_e_medias_fase1_BA",
            "BB": "tb_A_trend3_somas_e_medias_fase1_BB",
            "BC": "tb_A_trend3_somas_e_medias_fase1_BC",
            "CA": "tb_A_trend3_somas_e_medias_fase1_CA",
            "CB": "tb_A_trend3_somas_e_medias_fase1_CB",
            "CC": "tb_A_trend3_somas_e_medias_fase1_CC"
        }

        lista_dfs = []

        tabelas_existentes = set(
            con.execute("SHOW TABLES").df()["name"].tolist()
        )

        for origem, tabela in tabelas_origem.items():
            print(f"   - Verificando {tabela} ...")

            if tabela not in tabelas_existentes:
                print(f"     (Tabela {tabela} não existe — criando DF vazio)")
                df = pd.DataFrame()
            else:
                df = con.execute(f"SELECT * FROM {tabela}").df()
                if df.empty:
                    print(f"     (Tabela {tabela} vazia — DF vazio)")
                    df = pd.DataFrame()

            df = df.dropna(axis=1, how='all')

            if not df.empty:
                df["origem"] = origem
                lista_dfs.append(df)

        print("3. Unindo todas as fases...")

        if lista_dfs:
            df_final = pd.concat(lista_dfs, ignore_index=True)
        else:
            print("   Nenhuma fase com dados — criando tabela final vazia.")
            df_final = pd.DataFrame(columns=[
                "sku", "media_x", "media_y", "Soma_Sxx", "Soma_Syy",
                "Soma_Sxy", "inclina_b", "intersec_a", "erro_Eb",
                "tcalc", "trend_notrend", "origem"
            ])

        print("4. Gravando tabela final no DuckDB...")

        con.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1")
        con.register("df_unida", df_final)

        con.execute("""
            CREATE TABLE tb_A_trend3_somas_e_medias_fase1 AS
            SELECT * FROM df_unida
        """)

        print("apato_0891_nonsazon2_unir_fase1 executado com sucesso.")

    finally:
        con.close()
