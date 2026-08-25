# apato_0891_nonsazon2_CC.py
# Equivalente 100% ao MySQL sp8_A_nonsazon2_CC




# apato_0891_nonsazon2_CC - versão multi-cliente
# Equivalente 100% ao MySQL sp8_A_nonsazon2_CC

import sys
import os
import duckdb
import pandas as pd

def apato_0891_nonsazon2_CC(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("1. Conectando ao DuckDB...")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    try:
        print("2. Buscando SKUs da classe C/C...")

        df = con.execute("""
            SELECT DISTINCT sku
            FROM tb_A_trend2_temp
            WHERE class_ABC_pedidos = 'C'
              AND class_ABC_valores = 'C'
        """).df()

        if df.empty:
            print("Nenhum SKU encontrado para classe C/C.")
            return

        print("3. Preparando DataFrame final...")

        df_final = pd.DataFrame({
            "sku": df["sku"],
            "media_x": None,
            "media_y": None,
            "Soma_Sxx": None,
            "Soma_Syy": None,
            "Soma_Sxy": None,
            "inclina_b": None,
            "intersec_a": None,
            "erro_Eb": None,
            "tcalc": None,
            "trend_notrend": "notrend"
        })

        print("4. Gravando tabela final no DuckDB...")

        con.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1_CC")
        con.register("df_final_CC", df_final)

        con.execute("""
            CREATE TABLE tb_A_trend3_somas_e_medias_fase1_CC AS
            SELECT * FROM df_final_CC
        """)

        print("apato_0891_nonsazon2_CC executado com sucesso — equivalente ao MySQL.")

    finally:
        con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_0891_nonsazon2_CC(pasta_cliente)
