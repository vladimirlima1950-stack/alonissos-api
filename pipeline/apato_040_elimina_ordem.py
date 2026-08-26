import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 2. EXECUÇÃO DA LÓGICA ORIGINAL
    # ============================================================

    # 1. Obter o valor máximo de 'ordem' na tb_date_aux4
    maxordem = conn.execute("SELECT MAX(ordem) FROM tb_date_aux4").fetchone()[0]

    # 2. Deletar os meses excedentes (mantendo apenas os últimos 24, excluindo o mês corrente)
    conn.execute(f"""
        DELETE FROM tb_date_aux4
        WHERE ordem <= {maxordem - 25}
    """)

    conn.execute(f"""
        DELETE FROM tb_date_aux4
        WHERE ordem = {maxordem}
    """)

    # 3. Atualizar tb_vendas_total1: zerar qtde_pedida onde for nula
    conn.execute("""
        UPDATE tb_vendas_total1
        SET qtde_pedida = 0
        WHERE qtde_pedida IS NULL
    """)

    # 4. Atualizar numero_ordem para "X" onde for nulo e qtde_pedida = 0
    conn.execute("""
        UPDATE tb_vendas_total1
        SET numero_ordem = 'X'
        WHERE numero_ordem IS NULL AND qtde_pedida = 0
    """)

    # 5. Atualizar numero_ordem para "AAAAAA" onde for nulo e qtde_pedida > 0
    conn.execute("""
        UPDATE tb_vendas_total1
        SET numero_ordem = 'AAAAAA'
        WHERE numero_ordem IS NULL AND qtde_pedida > 0
    """)

    # 6. Criar tb_vendas_total2 com histórico limitado a 24 meses
    conn.execute("DROP TABLE IF EXISTS tb_vendas_total2")
    conn.execute("""
        CREATE TABLE tb_vendas_total2 AS
        SELECT
            t1.sku,
            t1.numero_ordem,
            t1.qtde_pedida,
            t1.ano_mes,
            t2.ordem
        FROM tb_vendas_total1 t1
        INNER JOIN tb_date_aux4 t2
        ON t1.ano_mes = t2.fase3
    """)

    print("Meses excedentes eliminados e tabela tb_vendas_total2 criada com sucesso!")

    conn.close()
