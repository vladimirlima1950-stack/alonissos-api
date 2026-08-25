# apato_091_trend1




# apato_091_trend1 - versão multi-cliente
# Equivalente 100% ao MySQL sp8_A_trend1

import sys
import os
import duckdb

def apato_091_trend1(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    print("Iniciando apato_091_trend1...")

    # ============================================================
    # 0) Obter total de SKUs únicos
    # ============================================================
    total_skus = con.execute("""
        SELECT COUNT(DISTINCT sku)
        FROM tb_A_nonsazon1
    """).fetchone()[0]

    v_offset = 0
    v_limit = 1000

    # ============================================================
    # 1) Criar tabela final fase1 (vazia)
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_trend_fase1")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_trend_fase1 (
            sku VARCHAR,
            qtde_pedida DECIMAL(13,2),
            ordem INTEGER
        )
    """)

    # ============================================================
    # 2) Loop de blocos (equivalente ao WHILE do MySQL)
    # ============================================================
    while True:

        con.execute("DROP TABLE IF EXISTS temp_skus")
        con.execute(f"""
            CREATE TABLE temp_skus AS
            SELECT sku
            FROM (
                SELECT DISTINCT sku
                FROM tb_A_nonsazon1
                ORDER BY sku
                LIMIT {v_limit} OFFSET {v_offset}
            )
        """)

        bloco_count = con.execute("SELECT COUNT(*) FROM temp_skus").fetchone()[0]
        if bloco_count == 0:
            break

        con.execute("""
            INSERT INTO tb_A_nonsazon12_trend_fase1 (sku, qtde_pedida, ordem)
            SELECT n.sku, n.qtde_pedida, n.ordem
            FROM tb_A_nonsazon1 n
            INNER JOIN temp_skus t ON n.sku = t.sku
            ORDER BY n.sku, n.ordem
        """)

        v_offset += v_limit

    # ============================================================
    # 3) Criar tabela auxiliar tb_aux1
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_aux1")
    con.execute("""
        CREATE TABLE tb_aux1 AS
        SELECT DISTINCT sku, trend_notrend
        FROM tb_A_trend3_somas_e_medias_fase1
    """)

    con.execute("DELETE FROM tb_aux1 WHERE trend_notrend = 'trend'")

    con.execute("""
        DELETE FROM tb_A_nonsazon12_trend_fase1
        USING tb_aux1
        WHERE tb_A_nonsazon12_trend_fase1.sku = tb_aux1.sku
    """)

    # ============================================================
    # 4) Fase 2 — adicionar inclina_b e intersec_a
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_trend_fase2")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_trend_fase2 AS
        SELECT * FROM tb_A_nonsazon12_trend_fase1
    """)

    con.execute("ALTER TABLE tb_A_nonsazon12_trend_fase2 ADD COLUMN inclina_b DECIMAL(13,4)")
    con.execute("ALTER TABLE tb_A_nonsazon12_trend_fase2 ADD COLUMN intersec_a DECIMAL(13,4)")

    con.execute("""
        UPDATE tb_A_nonsazon12_trend_fase2
        SET inclina_b = (
                SELECT t.inclina_b
                FROM tb_A_trend3_somas_e_medias_fase1 t
                WHERE t.sku = tb_A_nonsazon12_trend_fase2.sku
            ),
            intersec_a = (
                SELECT t.intersec_a
                FROM tb_A_trend3_somas_e_medias_fase1 t
                WHERE t.sku = tb_A_nonsazon12_trend_fase2.sku
            )
    """)

    # ============================================================
    # 5) Fase 3 — calcular previsões
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_A_nonsazon12_trend_fase3")
    con.execute("""
        CREATE TABLE tb_A_nonsazon12_trend_fase3 AS
        SELECT * FROM tb_A_nonsazon12_trend_fase2
    """)

    con.execute("ALTER TABLE tb_A_nonsazon12_trend_fase3 ADD COLUMN previsoes DECIMAL(13,2)")

    con.execute("""
        UPDATE tb_A_nonsazon12_trend_fase3
        SET previsoes = intersec_a + inclina_b * (ordem + 24)
    """)

    con.execute("""
        UPDATE tb_A_nonsazon12_trend_fase3
        SET previsoes = 0
        WHERE previsoes < 0
    """)

    print("Procedimento apato_091_trend1 executado com sucesso — equivalente ao MySQL sp8_A_trend1.")

    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_091_trend1(pasta_cliente)
