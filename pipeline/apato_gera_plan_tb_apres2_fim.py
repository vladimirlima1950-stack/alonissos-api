import os
import duckdb
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, numbers
from pipeline.translation import t, ler_idioma


def run(pasta_cliente):

    idioma = ler_idioma(pasta_cliente)

    pasta_saida = os.path.join(pasta_cliente, "saida")
    os.makedirs(pasta_saida, exist_ok=True)

    caminho_duckdb = os.path.join(pasta_cliente, "processamento", "previsao.duckdb")

    con = duckdb.connect(caminho_duckdb, read_only=False)

    # ============================================================
    # CONSULTA AO BANCO DE DADOS
    # ============================================================
    df = con.execute("""
        SELECT classe_de_pedidos, classe_de_custo, qtde_skus, porc_skus,
               qtde_pedidos, porc_pedidos, custo_12meses, porc_custo_12meses,
               custo_estoque, porc_custo_estoque, giro_do_estoque
        FROM tb_apres2_fim
    """).df()

    # ============================================================
    # CABEÇALHOS E CAMPOS (mantidos exatamente como no PHP)
    # ============================================================
    
    colunas = [
        t("columns.frequencia_pedidos", idioma),
        t("columns.importancia_faturamento", idioma),
        t("columns.qtde_diferentes_produtos", idioma),
        t("columns.porc_produto", idioma),
        t("columns.qtde_pedidos_12m", idioma),
        t("columns.perc_pedidos_12m", idioma),
        t("columns.custo_produto_12m", idioma),
        t("columns.perc_custo_12m", idioma),
        t("columns.custo_estoque", idioma),
        t("columns.perc_custo_estoque", idioma),
        t("columns.giro_estoque", idioma)
    ]

    campos = [
        'classe_de_pedidos',
        'classe_de_custo',
        'qtde_skus',
        'porc_skus',
        'qtde_pedidos',
        'porc_pedidos',
        'custo_12meses',
        'porc_custo_12meses',
        'custo_estoque',
        'porc_custo_estoque',
        'giro_do_estoque'
    ]

    # ============================================================
    # CRIAÇÃO DA PLANILHA
    # ============================================================
    wb = Workbook()
    ws = wb.active

    # Cabeçalhos
    for idx, titulo in enumerate(colunas, start=1):
        cell = ws.cell(row=1, column=idx)
        cell.value = titulo
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = 15

    # ============================================================
    # PREENCHENDO DADOS
    # ============================================================
    linha = 2
    for _, row in df.iterrows():
        for col_idx, campo in enumerate(campos, start=1):
            valor = row[campo]
            cell = ws.cell(row=linha, column=col_idx)

            # mantém a lógica do PHP
            if isinstance(valor, (int, float)):
                cell.value = float(valor)
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.value = valor

            # formatação numérica igual ao PHP
            if campo in ('qtde_skus', 'qtde_pedidos'):
                cell.number_format = '0'
            elif 'porc' in campo:
                cell.number_format = numbers.FORMAT_PERCENTAGE_00
            elif isinstance(valor, (int, float)):
                cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

        linha += 1

    # ============================================================
    # SALVA ARQUIVO
    # ============================================================
    caminho_arquivo = os.path.join(pasta_saida, "tabela_apres2.xlsx")
    wb.save(caminho_arquivo)

    print(f"Planilha gerada com sucesso em: {caminho_arquivo}")

    return caminho_arquivo
