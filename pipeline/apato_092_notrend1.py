# apato_092_notrend1



# apato_092_notrend1 - versão multi-cliente
# Equivalente 100% ao MySQL sp8_A_notrend1

import sys
import os
import duckdb

def apato_092_notrend1(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    print("Iniciando apato_092_notrend1...")

    # ============================================================
    # Fase 1 — Criar tabela base com todos os SKUs
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_notrend_fase1")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_notrend_fase1 AS
        SELECT sku, qtde_pedida, ordem
        FROM tb_A_nonsazon1
        ORDER BY sku, ordem
    """)

    # ============================================================
    # Fase 1.5 — Remover SKUs com tendência 'notrend'
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_aux22")
    con.execute("""
        CREATE TABLE tb_aux22 AS
        SELECT DISTINCT sku, trend_notrend
        FROM tb_A_trend3_somas_e_medias_fase1
    """)

    con.execute("DELETE FROM tb_aux22 WHERE trend_notrend = 'notrend'")

    con.execute("""
        DELETE FROM tb_A_nonsazon12_notrend_fase1
        USING tb_aux22
        WHERE tb_A_nonsazon12_notrend_fase1.sku = tb_aux22.sku
    """)

    # ============================================================
    # Fase 2 — Aplicar fatores de suavização
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_notrend_fase2")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_notrend_fase2 AS
        SELECT * FROM tb_A_nonsazon12_notrend_fase1
    """)

    con.execute("ALTER TABLE tb_A_nonsazon12_notrend_fase2 ADD COLUMN fatores DECIMAL(10,2)")

    con.execute("""
        UPDATE tb_A_nonsazon12_notrend_fase2
        SET fatores = qtde_pedida * coef
        FROM tb_fatores_suaviz
        WHERE ordem = id_ordem2
    """)

    # ============================================================
    # Fase 3 — Calcular previsões
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_notrend_fase3")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_notrend_fase3 AS
        SELECT * FROM tb_A_nonsazon12_notrend_fase2
    """)

    con.execute("ALTER TABLE tb_A_nonsazon12_notrend_fase3 ADD COLUMN previsao DECIMAL(10,2)")

    con.execute("DROP TABLE IF EXISTS tb_nonsazon_notrend_aux7")
    con.execute("""
        CREATE TABLE tb_nonsazon_notrend_aux7 AS
        SELECT sku, SUM(fatores) AS soma
        FROM tb_A_nonsazon12_notrend_fase2
        GROUP BY sku
    """)

    con.execute("""
        UPDATE tb_A_nonsazon12_notrend_fase3
        SET previsao = soma
        FROM tb_nonsazon_notrend_aux7
        WHERE tb_A_nonsazon12_notrend_fase3.sku = tb_nonsazon_notrend_aux7.sku
    """)

    print("Procedimento apato_092_notrend1 executado com sucesso.")

    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_092_notrend1(pasta_cliente)
