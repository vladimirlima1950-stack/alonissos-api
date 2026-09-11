# pipeline/apato_mrp_gera_planilha_visual.py
# Gera planilha Excel avançada do MRP, com dashboard, gráficos e abas detalhadas.

import os
import duckdb
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.chart import LineChart, Reference

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

    resumo_sku = df_mrp.groupby("sku").agg({
        "demanda": "sum",
        "previsao": "sum",
        "ordem_planejada": "sum",
        "custo_ordem_planejada": "sum",
        "leadtime_dias": "max"
    }).reset_index()

    ws_sku.append(list(resumo_sku.columns))
    for _, row in resumo_sku.iterrows():
        ws_sku.append(list(row.values))

    # ============================================================
    # 6) Aba: Custos Consolidados
    # ============================================================

    ws_custo = wb.create_sheet("Custos")

    custo_mes = df_mrp.groupby("mes_num")["custo_ordem_planejada"].sum().reset_index()
    custo_mes.columns = ["mes_num", "custo_total"]

    ws_custo.append(["mes_num", "custo_total"])
    for _, row in custo_mes.iterrows():
        ws_custo.append(list(row.values))

    # ============================================================
    # 7) Aba: Dashboard
    # ============================================================

    ws_dash = wb.create_sheet("Dashboard")

    ws_dash["A1"] = "Dashboard MRP Avançado"
    ws_dash["A1"].font = Font(size=16, bold=True)

    ws_dash["A3"] = "Resumo Geral"
    ws_dash["A3"].font = Font(size=14, bold=True)

    total_custo = df_mrp["custo_ordem_planejada"].sum()
    total_ordens = df_mrp["ordem_planejada"].sum()

    ws_dash["A5"] = "Custo Total Planejado:"
    ws_dash["B5"] = total_custo

    ws_dash["A6"] = "Total de Ordens Planejadas:"
    ws_dash["B6"] = total_ordens

    # ============================================================
    # 8) Gráfico de custo mensal
    # ============================================================

    chart = LineChart()
    chart.title = "Custo Mensal Planejado"
    chart.y_axis.title = "Custo"
    chart.x_axis.title = "Mês"

    data = Reference(ws_custo, min_col=2, min_row=1, max_row=len(custo_mes) + 1)
    categorias = Reference(ws_custo, min_col=1, min_row=2, max_row=len(custo_mes) + 1)

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categorias)

    ws_dash.add_chart(chart, "D5")

    # ============================================================
    # 9) Salvar planilha
    # ============================================================

    caminho_planilha = os.path.join(pasta_processamento, "mrp.xlsx")
    wb.save(caminho_planilha)

    # ============================================================
    # 10) Registrar tempo no pipeline
    # ============================================================

    fim = datetime.now()
    con.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, ["apato_mrp_gera_planilha_visual", inicio, fim, "OK"])

    con.close()
