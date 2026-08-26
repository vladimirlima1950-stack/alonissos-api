import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(database=caminho_banco, read_only=False)

    # ============================================================
    # 1) Criar tb_sazon5 (equivalente ao MySQL)
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon5")

    conn.execute("""
        CREATE TABLE tb_sazon5 AS
        SELECT
            sku,
            SUM(qtde_pedida) AS qtdepedida,
            SUM(indice_sazon) AS indicesazon,
            STDDEV_SAMP(qtde_pedida) AS desvpad_orig,
            STDDEV_SAMP(qtde_pedida_dessas) AS desvpad_dessas,
            NULL::VARCHAR AS sazon_nonsazon
        FROM tb_sazon4
        GROUP BY sku
        ORDER BY sku
    """)

    # ============================================================
    # 2) Aplicar regras de sazonalidade (equivalente ao MySQL)
    # ============================================================

    # Regra 1: nonsazon quando índice > 25.6 e qtdepedida < 12
    conn.execute("""
        UPDATE tb_sazon5
        SET sazon_nonsazon = 'nonsazon'
        WHERE indicesazon > 25.6
          AND qtdepedida < 12
          AND sazon_nonsazon IS NULL
    """)

    # Regra 2: sazonal quando desvio original >= 1.20 * desvio dessazonalizado
    conn.execute("""
        UPDATE tb_sazon5
        SET sazon_nonsazon = 'sazon'
        WHERE desvpad_orig >= 1.20 * desvpad_dessas
          AND sazon_nonsazon IS NULL
    """)

    # Regra 3: nonsazon quando desvio original < 1.20 * desvio dessazonalizado
    conn.execute("""
        UPDATE tb_sazon5
        SET sazon_nonsazon = 'nonsazon'
        WHERE desvpad_orig < 1.20 * desvpad_dessas
          AND sazon_nonsazon IS NULL
    """)

    # ============================================================
    # 3) Criar tb_sazon6 (equivalente ao MySQL)
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon6")

    conn.execute("""
        CREATE TABLE tb_sazon6 AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY s.sku, s.ordem) AS id_num,
            s.sku,
            s.qtde_pedida,
            s.ano_mes,
            s.ordem,
            s.media_24meses,
            s.media_2meses,
            s.indice_sazon,
            s.qtde_pedida_dessas,
            t.sazon_nonsazon
        FROM tb_sazon4 s
        INNER JOIN tb_sazon5 t
            ON s.sku = t.sku
        WHERE t.sazon_nonsazon = 'sazon'
        ORDER BY s.sku, s.ordem
    """)

    print("tb_sazon5 e tb_sazon6 criadas e atualizadas com sucesso (equivalente ao sp8_sazon5).")

    conn.close()
