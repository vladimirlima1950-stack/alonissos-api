# pipeline/apato_mrp_gera_planilha_visual.py
# Gera planilha Excel do MRP, com abas essenciais (sem gráfico, sem dashboard, sem custos).

import os
import duckdb
import pandas as pd
from datetime import datetime
from openpyxl import Workbook

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(caminho_banco, read_only=False)
    inicio = datetime.now()

    # ============================================================
    # 1) Ler tabelas necessárias
    # ============================================================

    df_mrp = con.execute("SELECT * FROM tb_mrp_completo").df()
    df_dmd_fcst = con.execute("SELECT * FROM tb_dmd_fcst_res_fim").df()
    df_seg = con.execute("SELECT * FROM tb_estoq_segur_12meses_res_fim").df()
    df_estoque = con.execute("SELECT sku, qtde_orig AS estoque_atual FROM tb_estoques_orig").df()
    df_leadtime = con.execute("SELECT sku, leadtime AS leadtime_dias FROM tb_leadtime_orig").df()
    df_custo = con.execute("SELECT sku, custo_unit AS custo_unitario FROM tb_custo_orig").df()

    # ============================================================
    # 2) Criar workbook
    # ============================================================

    wb = Workbook()

    # ============================================================
    # 3) Aba: MRP Completo
    # ============================================================

    ws_mrp = wb.active
    ws_mrp.title = "MRP Completo"

    ws_mrp.append(list(df_mrp.columns))
    for _, row in df_mrp.iterrows():
        ws_mrp.append(list(row.values))

    # ============================================================
    # 4) Aba: Base de Dados
    # ============================================================

    ws_base = wb.create_sheet("Base de Dados")

    df_base = (
        df_dmd_fcst
        .merge(df_seg, on="sku", how="left")
        .merge(df_estoque, on="sku", how="left")
        .merge(df_leadtime, on="sku", how="left")
        .merge(df_custo, on="sku", how="left")
    )

    ws_base.append(list(df_base.columns))
    for _, row in df_base.iterrows():
        ws_base.append(list(row.values))

    # ============================================================
    # 5) Aba: Dados do SKU (resumo por SKU)
    # ============================================================

    ws_sku = wb.create_sheet("Dados do SKU")

    # resumo sem ordem_planejada e sem custo_ordem_planejada
    resumo_sku = df_mrp.groupby("sku").agg({
        "demanda": "sum",
        "previsao": "sum",
        "leadtime_dias": "max"
    }).reset_index()

    # adicionar custo_unitario
    resumo_sku = resumo_sku.merge(df_custo, on="sku", how="left")

    ws_sku.append(list(resumo_sku.columns))
    for _, row in resumo_sku.iterrows():
        ws_sku.append(list(row.values))

    # ============================================================
    # 6) Salvar planilha
    # ============================================================

    pasta_saida = os.path.join(pasta_cliente, "saida")
    os.makedirs(pasta_saida, exist_ok=True)

    caminho_planilha = os.path.join(pasta_saida, "mrp.xlsx")
    wb.save(caminho_planilha)

    # ============================================================
    # 7) Registrar tempo no pipeline
    # ============================================================

    fim = datetime.now()
    con.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, ["apato_mrp_gera_planilha_visual", inicio, fim, "OK"])

    con.close()
