import os
import duckdb
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, numbers

def run(pasta_cliente):

    pasta_saida = os.path.join(pasta_cliente, "saida")
    os.makedirs(pasta_saida, exist_ok=True)

    caminho_duckdb = os.path.join(pasta_cliente, "processamento", "previsao.duckdb")

    con = duckdb.connect(caminho_duckdb, read_only=False)

    # ============================================================
    # CONSULTA AO BANCO (ESTOQUES VALORES)
    # ============================================================
    df = con.execute("""
        SELECT class_abc_pedidos, class_abc_valores, sku,
               qtde, custo_unit, total_valor_sku, porc_valor_estoque
        FROM tb_estoques_valores_fim
    """).df()

    # ============================================================
    # TÍTULOS E CAMPOS (mantidos exatamente como no PHP)
    # ============================================================
    titulos = [
        'frequência de pedidos', 'importância no faturamento', 'sku número',
        'quantidade no estoque', 'custo unitário', 'valor total em estoque',
        'porcentagem do valor do estoque'
    ]

    campos = [
        'class_abc_pedidos', 'class_abc_valores', 'sku',
        'qtde', 'custo_unit', 'total_valor_sku', 'porc_valor_estoque'
    ]

    # ============================================================
    # CRIAÇÃO DA PLANILHA
    # ============================================================
    wb = Workbook()
    ws = wb.active

    # Cabeçalhos
    for idx, titulo in enumerate(titulos, start=1):
        cell = ws.cell(row=1, column=idx)
        cell.value = titulo
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = 18

    # ============================================================
    # PREENCHENDO DADOS
    # ============================================================
    linha = 2

    for _, row in df.iterrows():
        for col_idx, campo in enumerate(campos, start=1):

            valor = row[campo]
            cell = ws.cell(row=linha, column=col_idx)

            # Alinhamento igual ao PHP
            if campo == "sku":
                cell.alignment = Alignment(horizontal="left")
            else:
                cell.alignment = Alignment(horizontal="center")

            # Valor
            if isinstance(valor, (int, float)):
                cell.value = float(valor)
            else:
                cell.value = valor

            # Formatação numérica específica por campo (igual ao PHP)
            if isinstance(valor, (int, float)):
                if campo == "qtde":
                    cell.number_format = numbers.FORMAT_NUMBER
                elif campo in ("custo_unit", "total_valor_sku"):
                    cell.number_format = "#,##0.00"
                elif campo == "porc_valor_estoque":
                    cell.number_format = "0.00%"

        linha += 1

    # ============================================================
    # SALVA ARQUIVO
    # ============================================================
    caminho_arquivo = os.path.join(pasta_saida, "tabela_estoques_valores.xlsx")
    wb.save(caminho_arquivo)

    print(f"Planilha gerada com sucesso em: {caminho_arquivo}")

    return caminho_arquivo
