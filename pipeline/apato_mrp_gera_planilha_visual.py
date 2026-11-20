# pipeline/apato_mrp_gera_planilha_visual.py
# Gera planilha Excel do MRP, com abas essenciais (sem gráfico, sem dashboard, sem custos).

import os
import duckdb
import pandas as pd
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import numbers
from pipeline.translation import ler_idioma


    
def run(pasta_cliente):

    idioma = ler_idioma(pasta_cliente)

    pasta_processamento = os.path.join(
        pasta_cliente,
        "processamento"
    )    
    
    
    
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
    
    
    if idioma == "en":

        nome_template = "Graficos auxiliares EN.xlsx"

    else:

        nome_template = "Graficos auxiliares PT.xlsx"


    caminho_template = os.path.join(
        os.path.dirname(__file__),
        "templates",
        nome_template
    )
    
    
    
    
    wb = load_workbook(caminho_template)
    

    

    # ============================================================
    # 3) Aba: MRP Completo
    # ============================================================

    if idioma == "en":
        ws_mrp = wb.create_sheet("Complete MRP")
    else:
        ws_mrp = wb.create_sheet("MRP Completo")

    
    cabecalhos_mrp_pt = [
        "SKU",
        "Mês",
        "Demanda",
        "Previsão",
        "Estoque de Segurança",
        "Estoque Inicial",
        "Necessidade Líquida",
        "Ordem Planejada",
        "Mês de Liberação",
        "Estoque Projetado",
        "Custo da Ordem Planejada",
        "Lead Time (dias)"
    ]

    cabecalhos_mrp_en = [
        "SKU",
        "Month",
        "Demand",
        "Forecast",
        "Safety Stock",
        "Initial Inventory",
        "Net Requirement",
        "Planned Order",
        "Release Month",
        "Projected Inventory",
        "Planned Order Cost",
        "Lead Time (Days)"
    ]

    if idioma == "en":
        ws_mrp.append(cabecalhos_mrp_en)
    else:
        ws_mrp.append(cabecalhos_mrp_pt)
        
    
    
    
    
    

    for _, row in df_mrp.iterrows():
        ws_mrp.append(list(row.values))

    # Formatar custo_ordem_planejada com 2 casas decimais
    col_custo_op = df_mrp.columns.get_loc("custo_ordem_planejada") + 1

    for row in range(2, ws_mrp.max_row + 1):
        ws_mrp.cell(row=row, column=col_custo_op).number_format = '#,##0.00'

    # ============================================================
    # 4) Aba: Base de Dados
    # ============================================================

    if idioma == "en":
        ws_base = wb.create_sheet("Data Repository")
    else:
        ws_base = wb.create_sheet("Base de Dados")

    df_base = (
        df_dmd_fcst
        .merge(df_seg, on="sku", how="left")
        .merge(df_estoque, on="sku", how="left")
        .merge(df_leadtime, on="sku", how="left")
        .merge(df_custo, on="sku", how="left")
    )

    
    
    
    cabecalhos_base_pt = [
        "Frequência de Pedidos",
        "Importância no Faturamento",
        "SKU",

        "Mês -24",
        "Mês -23",
        "Mês -22",
        "Mês -21",
        "Mês -20",
        "Mês -19",
        "Mês -18",
        "Mês -17",
        "Mês -16",
        "Mês -15",
        "Mês -14",
        "Mês -13",
        "Mês -12",
        "Mês -11",
        "Mês -10",
        "Mês -9",
        "Mês -8",
        "Mês -7",
        "Mês -6",
        "Mês -5",
        "Mês -4",
        "Mês -3",
        "Mês -2",
        "Mês -1",

        "Mês Corrente",

        "Mês +1",
        "Mês +2",
        "Mês +3",
        "Mês +4",
        "Mês +5",
        "Mês +6",
        "Mês +7",
        "Mês +8",
        "Mês +9",
        "Mês +10",
        "Mês +11",

        "Classe ABC Pedidos",
        "Classe ABC Valores",

        "ES Mês Corrente",
        "ES Mês +1",
        "ES Mês +2",
        "ES Mês +3",
        "ES Mês +4",
        "ES Mês +5",
        "ES Mês +6",
        "ES Mês +7",
        "ES Mês +8",
        "ES Mês +9",
        "ES Mês +10",
        "ES Mês +11",

        "Estoque Atual",
        "Lead Time (dias)",
        "Custo Unitário"
    ]

    cabecalhos_base_en = [
        "Order Frequency",
        "Revenue Importance",
        "SKU",

        "Month -24",
        "Month -23",
        "Month -22",
        "Month -21",
        "Month -20",
        "Month -19",
        "Month -18",
        "Month -17",
        "Month -16",
        "Month -15",
        "Month -14",
        "Month -13",
        "Month -12",
        "Month -11",
        "Month -10",
        "Month -9",
        "Month -8",
        "Month -7",
        "Month -6",
        "Month -5",
        "Month -4",
        "Month -3",
        "Month -2",
        "Month -1",

        "Current Month",

        "Month +1",
        "Month +2",
        "Month +3",
        "Month +4",
        "Month +5",
        "Month +6",
        "Month +7",
        "Month +8",
        "Month +9",
        "Month +10",
        "Month +11",

        "ABC Order Class",
        "ABC Revenue Class",

        "SS Current Month",
        "SS Month +1",
        "SS Month +2",
        "SS Month +3",
        "SS Month +4",
        "SS Month +5",
        "SS Month +6",
        "SS Month +7",
        "SS Month +8",
        "SS Month +9",
        "SS Month +10",
        "SS Month +11",

        "Current Inventory",
        "Lead Time (Days)",
        "Unit Cost"
    ]

    if idioma == "en":
        ws_base.append(cabecalhos_base_en)
    else:
        ws_base.append(cabecalhos_base_pt)
            
    
    
    for _, row in df_base.iterrows():
        ws_base.append(list(row.values))

    # ============================================================
    # 5) Aba: Dados do SKU (resumo por SKU)
    # ============================================================

    if idioma == "en":
        ws_sku = wb.create_sheet("SKU Data")
    else:
        ws_sku = wb.create_sheet("Dados do SKU")

    # resumo sem ordem_planejada e sem custo_ordem_planejada
    resumo_sku = df_mrp.groupby("sku").agg({
        "demanda": "sum",
        "previsao": "sum",
        "leadtime_dias": "max"
    }).reset_index()

    # adicionar custo_unitario
    resumo_sku = resumo_sku.merge(df_custo, on="sku", how="left")

    
    cabecalhos_sku_pt = [
        "SKU",
        "Demanda",
        "Previsão",
        "Lead Time (dias)",
        "Custo Unitário"
    ]

    cabecalhos_sku_en = [
        "SKU",
        "Demand",
        "Forecast",
        "Lead Time (Days)",
        "Unit Cost"
    ]

    if idioma == "en":
        ws_sku.append(cabecalhos_sku_en)
    else:
        ws_sku.append(cabecalhos_sku_pt)
    
    
    
    
    for _, row in resumo_sku.iterrows():
        ws_sku.append(list(row.values))

    # Formatar custo_unitario com 2 casas decimais
    col_custo = resumo_sku.columns.get_loc("custo_unitario") + 1

    for row in range(2, ws_sku.max_row + 1):
        ws_sku.cell(row=row, column=col_custo).number_format = '#,##0.00'

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
