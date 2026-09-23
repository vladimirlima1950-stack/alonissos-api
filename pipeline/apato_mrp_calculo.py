# pipeline/apato_mrp_calculo.py
# Calcula MRP completo por SKU e mês, incluindo custo estimado,
# e grava em tb_mrp_completo no DuckDB.

import os
import duckdb
import pandas as pd
from datetime import datetime, timedelta

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(caminho_banco, read_only=False)
    inicio = datetime.now()

    # ============================================================
    # 1) Ler tabelas reais
    # ============================================================

    tb_custo = con.execute("""
        SELECT sku, custo_unit AS custo_unitario
        FROM tb_custo_orig
    """).df()

    tb_estoque = con.execute("""
        SELECT sku, qtde_orig AS estoque_atual
        FROM tb_estoques_orig
    """).df()

    tb_leadtime = con.execute("""
        SELECT sku, leadtime AS leadtime_dias
        FROM tb_leadtime_orig
    """).df()

    tb_dmd_fcst = con.execute("""
        SELECT *
        FROM tb_dmd_fcst_res_fim
    """).df()

    tb_estoq_seg = con.execute("""
        SELECT *
        FROM tb_estoq_segur_12meses_res_fim
    """).df()

    # ============================================================
    # 2) Demandas (24 meses) e Previsões (12 meses)
    # ============================================================

    colunas_dmd = [
        'corr_menos24','corr_menos23','corr_menos22','corr_menos21','corr_menos20',
        'corr_menos19','corr_menos18','corr_menos17','corr_menos16','corr_menos15',
        'corr_menos14','corr_menos13','corr_menos12','corr_menos11','corr_menos10',
        'corr_menos9','corr_menos8','corr_menos7','corr_menos6','corr_menos5',
        'corr_menos4','corr_menos3','corr_menos2','corr_menos1'
    ]

    colunas_fcst = [
        'corr',
        'corr_mais1','corr_mais2','corr_mais3','corr_mais4','corr_mais5',
        'corr_mais6','corr_mais7','corr_mais8','corr_mais9','corr_mais10',
        'corr_mais11'
    ]

    linhas = []

    for _, row in tb_dmd_fcst.iterrows():
        sku = row["sku"]

        # 24 meses de demanda (histórico: meses 1–24)
        for i, col in enumerate(colunas_dmd):
            mes_num = i + 1
            demanda = row[col]
            linhas.append({
                "sku": sku,
                "mes_num": mes_num,
                "demanda": demanda,
                "previsao": 0
            })

        # 12 meses de previsão (meses 25–36)
        for i, col in enumerate(colunas_fcst):
            mes_num = 24 + i + 1
            previsao = row[col]
            linhas.append({
                "sku": sku,
                "mes_num": mes_num,
                "demanda": 0,
                "previsao": previsao
            })

    df_dmd_fcst_long = pd.DataFrame(linhas)

    # ============================================================
    # 3) Estoque de segurança (12 meses)
    # ============================================================

    colunas_seg = [
        'es_mes_corrente',
        'es_corr_mais1','es_corr_mais2','es_corr_mais3','es_corr_mais4',
        'es_corr_mais5','es_corr_mais6','es_corr_mais7','es_corr_mais8',
        'es_corr_mais9','es_corr_mais10','es_corr_mais11'
    ]

    linhas_seg = []

    for _, row in tb_estoq_seg.iterrows():
        sku = row["sku"]
        for i, col in enumerate(colunas_seg):
            mes_num = i + 25
            seg = row[col]
            linhas_seg.append({
                "sku": sku,
                "mes_num": mes_num,
                "estoque_seguranca": seg
            })

    df_seg_long = pd.DataFrame(linhas_seg)

    # ============================================================
    # 4) Unir tudo
    # ============================================================

    base = df_dmd_fcst_long.merge(tb_estoque, on="sku", how="left")
    base = base.merge(tb_leadtime, on="sku", how="left")
    base = base.merge(df_seg_long, on=["sku", "mes_num"], how="left")

    

    base = base.merge(tb_custo, on="sku", how="left")

    base = base.sort_values(["sku", "mes_num"])

    # ============================================================
    # 5) Cálculo MRP (histórico + previsão com leadtime)
    # ============================================================

    resultados = []

    for sku, grupo in base.groupby("sku"):
        grupo = grupo.copy().reset_index(drop=True)
        estq_proj_anterior = None

        for i, row in grupo.iterrows():

            demanda = row["demanda"] or 0
            previsao = row["previsao"] or 0
            estq_seg = row.get("estoque_seguranca", 0) or 0

            
            leadtime_val = row.get("leadtime_dias", 30)
            if pd.isna(leadtime_val):
                leadtime_val = 30

            custo_unit = row.get("custo_unitario", 0) or 0

            # Estoque inicial
            if i == 0:
                estq_inicial = row.get("estoque_atual", 0) or 0
            else:
                estq_inicial = estq_proj_anterior

            mes_num = row["mes_num"]

            


            # ============================
            # Meses 1–24: histórico → sem ordens, sem consumo de estoque
            # ============================
            mes_liberacao_num = None
            if mes_num <= 24:
                estq_seg = 0
                ordem_planejada = 0
                necessidade_bruta = 0
                necessidade_liquida = 0

                # Estoque projetado não é consumido no histórico
                estq_proj = estq_inicial

            else:
                # ============================
                # Meses 25+: previsão → cálculo completo com leadtime
                # ============================

                # Leadtime convertido em meses (ceil)
                meses_voltar = int((leadtime_val + 29) // 30)
                mes_liberacao_num = mes_num - meses_voltar
                if mes_liberacao_num < 25:
                    mes_liberacao_num = 25  # nunca liberar em meses históricos

                necessidade_bruta = max(0, previsao)
                necessidade_liquida = max(0, previsao + estq_seg - estq_inicial)
                ordem_planejada = necessidade_liquida

                estq_proj = estq_inicial - previsao + ordem_planejada

            estq_proj_anterior = estq_proj

            resultados.append({
                "sku": sku,
                "mes_num": mes_num,
                "demanda": demanda,
                "previsao": previsao,
                "estoque_seguranca": estq_seg,
                "estoque_inicial": estq_inicial,
                # "necessidade_bruta": necessidade_bruta,
                "necessidade_liquida": necessidade_liquida,
                "ordem_planejada": ordem_planejada,
                "mes_liberacao": mes_liberacao_num,
                "estoque_projetado": estq_proj,
                "custo_ordem_planejada": ordem_planejada * custo_unit,
                "leadtime_dias": leadtime_val
            })

    df_mrp = pd.DataFrame(resultados)

    # ============================================================
    # 6) Gravar no DuckDB
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_mrp_completo")
    con.execute("CREATE TABLE tb_mrp_completo AS SELECT * FROM df_mrp")

    fim = datetime.now()
    con.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, ["apato_mrp_calculo", inicio, fim, "OK"])

    con.close()
