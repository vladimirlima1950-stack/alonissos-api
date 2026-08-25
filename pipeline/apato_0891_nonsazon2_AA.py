#  apato_0891_nonsazon2_AA


# apato_0891_nonsazon2_AA - versão multi-cliente

import sys
import os
import numpy as np
import pandas as pd
import duckdb

def apato_0891_nonsazon2_AA(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("1. Conectando ao DuckDB e consultando os dados...")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    try:
        # Consulta equivalente ao filtro A/A
        query = """
            SELECT 
                t2.sku,
                t2.x_ordem,
                t2.y_qtde,
                t1.media_x,
                t1.media_y
            FROM tb_A_trend2_temp t2
            INNER JOIN tb_A_trend1_temp t1 ON t2.sku = t1.sku
            WHERE t2.class_ABC_pedidos = 'A'
              AND t2.class_ABC_valores = 'A'
        """

        df = con.execute(query).df()

        if df.empty:
            print("Nenhum SKU encontrado para classe A/A.")
            return

        print("2. Calculando produtos dos desvios...")

        df["prod_x"]  = (df["x_ordem"] - df["media_x"]) ** 2
        df["prod_y"]  = (df["y_qtde"]  - df["media_y"]) ** 2
        df["prod_xy"] = (df["x_ordem"] - df["media_x"]) * df["y_qtde"]

        print("3. Agrupando somatórios por SKU...")

        res = df.groupby("sku").agg(
            media_x=("media_x", "first"),
            media_y=("media_y", "first"),
            Soma_Sxx=("prod_x", "sum"),
            Soma_Syy=("prod_y", "sum"),
            Soma_Sxy=("prod_xy", "sum")
        ).reset_index()

        print("4. Calculando regressão linear...")

        # Inclinação
        res["inclina_b"] = res["Soma_Sxy"] / res["Soma_Sxx"]

        # Intercepto
        res["intersec_a"] = res["media_y"] - (res["inclina_b"] * res["media_x"])

        # Erro padrão da inclinação
        termo_erro = (res["Soma_Syy"] - res["inclina_b"] * res["Soma_Sxy"]) / (22 * res["Soma_Sxx"])
        termo_erro = np.maximum(termo_erro, 0)
        res["erro_Eb"] = np.sqrt(termo_erro)

        # tcalc
        res["tcalc"] = np.where(res["erro_Eb"] == 0, 9999, res["inclina_b"] / res["erro_Eb"])

        # trend / notrend
        res["trend_notrend"] = np.where(
            (res["erro_Eb"] == 0) | (res["tcalc"] > 2.047) | (res["tcalc"] < -2.047),
            "trend",
            "notrend"
        )

        print("5. Gravando tabela final no DuckDB...")

        con.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1_AA")
        con.register("df_final_AA", res)
        con.execute("""
            CREATE TABLE tb_A_trend3_somas_e_medias_fase1_AA AS
            SELECT * FROM df_final_AA
        """)

        print("apato_0891_nonsazon2_AA executado com sucesso — versão Pandas/Numpy equivalente ao MySQL.")

    finally:
        con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_0891_nonsazon2_AA(pasta_cliente)
