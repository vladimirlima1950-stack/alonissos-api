import os
import duckdb
import pandas as pd

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Criar tb_sazon11_notrend_fase1 com dados de tb_sazon6
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_fase1")
    conn.execute("""
        CREATE TABLE tb_sazon11_notrend_fase1 AS
        SELECT id_num, sku, qtde_pedida, ordem, qtde_pedida_dessas, indice_sazon
        FROM tb_sazon6
        ORDER BY id_num
    """)

    # ============================================================
    # 2) Remover SKUs com tendência
    # ============================================================

    conn.execute("""
        DELETE FROM tb_sazon11_notrend_fase1
        WHERE sku IN (
            SELECT sku
            FROM tb_trend3_somas_e_medias_fase1
            WHERE trend_notrend = 'trend'
        )
    """)

    # ============================================================
    # 3) Criar tabela tb_ordens com ordens únicas
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_ordens")
    conn.execute("""
        CREATE TABLE tb_ordens AS
        SELECT DISTINCT ordem AS ord
        FROM tb_sazon6
        ORDER BY ordem
    """)

    # ============================================================
    # 4) Criar tabela tb_fatores_suaviz com coeficientes
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_fatores_suaviz")
    conn.execute("""
        CREATE TABLE tb_fatores_suaviz (
            id_ordem INT,
            id_ordem2 INT,
            coef DECIMAL(13,6)
        )
    """)

    coeficientes = [
        (1, 0.001181), (2, 0.001476), (3, 0.001845), (4, 0.002306),
        (5, 0.002882), (6, 0.003603), (7, 0.004504), (8, 0.005629),
        (9, 0.007037), (10, 0.008796), (11, 0.010995), (12, 0.013744),
        (13, 0.017180), (14, 0.021475), (15, 0.026844), (16, 0.033554),
        (17, 0.041943), (18, 0.052429), (19, 0.065536), (20, 0.081920),
        (21, 0.102400), (22, 0.128000), (23, 0.160000), (24, 0.200000)
    ]

    conn.executemany("INSERT INTO tb_fatores_suaviz (id_ordem, coef) VALUES (?, ?)", coeficientes)

    # ============================================================
    # 5) Atualizar id_ordem2 com base na sequência de ordens
    # ============================================================

    ordens = conn.execute("SELECT ord FROM tb_ordens ORDER BY ord").fetchall()
    for i, ordem in enumerate(ordens):
        conn.execute("""
            UPDATE tb_fatores_suaviz
            SET id_ordem2 = ?
            WHERE id_ordem = ?
        """, [ordem[0], i + 1])

    # ============================================================
    # 6) Adicionar coluna coef_vs_qt_ped_dessas
    # ============================================================

    conn.execute("""
        ALTER TABLE tb_sazon11_notrend_fase1 
        ADD COLUMN coef_vs_qt_ped_dessas DECIMAL(13,6)
    """)

    # ============================================================
    # 7) Atualizar coef_vs_qt_ped_dessas com multiplicação por coeficiente
    # ============================================================

    conn.execute("""
        UPDATE tb_sazon11_notrend_fase1
        SET coef_vs_qt_ped_dessas = qtde_pedida_dessas * (
            SELECT coef
            FROM tb_fatores_suaviz
            WHERE tb_fatores_suaviz.id_ordem2 = tb_sazon11_notrend_fase1.ordem
        )
    """)

    print("Tabelas tb_sazon11_notrend_fase1, tb_ordens e tb_fatores_suaviz criadas e atualizadas com sucesso.")

    conn.close()
