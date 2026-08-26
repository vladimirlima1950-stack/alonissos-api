import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Criar tb_sazon11_notrend_fase2 com soma dos coeficientes suavizados por SKU
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_fase2")
    conn.execute("""
        CREATE TABLE tb_sazon11_notrend_fase2 AS
        SELECT sku, SUM(coef_vs_qt_ped_dessas) AS alisado
        FROM tb_sazon11_notrend_fase1
        GROUP BY sku
    """)

    # ============================================================
    # 2) Criar tb_sazon11_notrend_fase3 com dados básicos
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_fase3")
    conn.execute("""
        CREATE TABLE tb_sazon11_notrend_fase3 AS
        SELECT id_num, sku, ordem, qtde_pedida_dessas,
               NULL::DECIMAL(13,6) AS alisado,
               NULL::DECIMAL(10,2) AS previsoes,
               NULL::DECIMAL(13,6) AS indice_sazon
        FROM tb_sazon11_notrend_fase1
        ORDER BY id_num
    """)

    # ============================================================
    # 3) Atualizar coluna alisado com valores da fase2
    # ============================================================

    conn.execute("""
        UPDATE tb_sazon11_notrend_fase3
        SET alisado = (
            SELECT alisado
            FROM tb_sazon11_notrend_fase2
            WHERE tb_sazon11_notrend_fase2.sku = tb_sazon11_notrend_fase3.sku
        )
    """)

    # ============================================================
    # 4) Atualizar coluna indice_sazon com valores da fase1
    # ============================================================

    conn.execute("""
        UPDATE tb_sazon11_notrend_fase3
        SET indice_sazon = (
            SELECT indice_sazon
            FROM tb_sazon11_notrend_fase1
            WHERE tb_sazon11_notrend_fase1.sku = tb_sazon11_notrend_fase3.sku
              AND tb_sazon11_notrend_fase1.ordem = tb_sazon11_notrend_fase3.ordem
        )
    """)

    # ============================================================
    # 5) Calcular previsões como produto de alisado e índice sazonal
    # ============================================================

    conn.execute("""
        UPDATE tb_sazon11_notrend_fase3
        SET previsoes = alisado * indice_sazon
    """)

    print("Tabelas tb_sazon11_notrend_fase2 e tb_sazon11_notrend_fase3 criadas e atualizadas com previsões mensais.")

    conn.close()
