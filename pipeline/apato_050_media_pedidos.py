# apato_050_media_pedidos


# apato_050_media_pedidos - versão multi-cliente

import sys
import os
import duckdb

# ============================================================
# 1. RECEBE O CAMINHO DO CLIENTE
# ============================================================

if len(sys.argv) < 2:
    print("Erro: o programa deve receber o caminho do cliente como parâmetro.")
    sys.exit(1)

pasta_cliente = sys.argv[1]
pasta_processamento = os.path.join(pasta_cliente, "processamento")

# Banco DuckDB do cliente
caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
conn = duckdb.connect(caminho_banco)

# ------------------------------------------------------------
# 1) Limites de ordem (12 meses)
# ------------------------------------------------------------
limmax = conn.execute("SELECT MAX(ordem) FROM tb_vendas_total2").fetchone()[0]
limmin = limmax - 11

# ------------------------------------------------------------
# 2) Tabela temporária com SKUs únicos
# ------------------------------------------------------------
conn.execute("DROP TABLE IF EXISTS temp_skus")
conn.execute("""
    CREATE TABLE temp_skus AS
    SELECT DISTINCT sku
    FROM tb_vendas_total2
""")

# Total de SKUs
total_skus = conn.execute("SELECT COUNT(*) FROM temp_skus").fetchone()[0] or 0
bloco_size = 1000
offset = 0

# ------------------------------------------------------------
# 3) Tabela final tb_class_pedidos1
# ------------------------------------------------------------
conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1")
conn.execute("""
    CREATE TABLE tb_class_pedidos1 (
        sku VARCHAR(50),
        pedidos_12meses INT,
        media_pedidos_12meses DECIMAL(10,2),
        ttpedida DECIMAL(10,2),
        qtde DECIMAL(10,2),
        situacao VARCHAR(10)
    )
""")

# ------------------------------------------------------------
# 4) Loop de blocos (espelho do WHILE do MySQL)
# ------------------------------------------------------------
while offset < total_skus:

    # SKUs do bloco atual
    conn.execute("DROP TABLE IF EXISTS temp_bloco_skus")
    conn.execute("""
        CREATE TABLE temp_bloco_skus AS
        SELECT sku
        FROM temp_skus
        ORDER BY sku
        LIMIT ? OFFSET ?
    """, [bloco_size, offset])

    # Dados de pedidos para SKUs do bloco
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1A")
    conn.execute("""
        CREATE TABLE tb_class_pedidos1A AS
        SELECT v.*
        FROM tb_vendas_total2 v
        JOIN temp_bloco_skus b ON v.sku = b.sku
        WHERE v.ordem BETWEEN ? AND ?
    """, [limmin, limmax])

    # Adiciona coluna estoque
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1A_tmp")
    conn.execute("""
        CREATE TABLE tb_class_pedidos1A_tmp AS
        SELECT 
            a.*,
            COALESCE(e.qtde_orig, 0) AS estoque
        FROM tb_class_pedidos1A a
        LEFT JOIN tb_estoques e ON a.sku = e.sku
    """)
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1A")
    conn.execute("ALTER TABLE tb_class_pedidos1A_tmp RENAME TO tb_class_pedidos1A")

    # Calcula agregados (temp_resultados)
    conn.execute("DROP TABLE IF EXISTS temp_resultados")
    conn.execute("""
        CREATE TABLE temp_resultados AS
        SELECT 
            sku,
            COUNT(numero_ordem) AS pedidos_12meses,
            COUNT(numero_ordem) / 12.0 AS media_pedidos_12meses,
            SUM(qtde_pedida) AS ttpedida,
            AVG(estoque) AS qtde
        FROM tb_class_pedidos1A
        GROUP BY sku
    """)

    # Situação e ajustes (tb_class_pedidos1B)
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1B")
    conn.execute("""
        CREATE TABLE tb_class_pedidos1B AS
        SELECT 
            sku, 
            COUNT(numero_ordem) AS ordens
        FROM tb_class_pedidos1A
        WHERE numero_ordem != 'X'
        GROUP BY sku
    """)

    # Inserir na tabela final
    conn.execute("""
        INSERT INTO tb_class_pedidos1 (sku, pedidos_12meses, media_pedidos_12meses, ttpedida, qtde, situacao)
        SELECT 
            r.sku,
            CASE WHEN r.ttpedida = 0 THEN 0 ELSE COALESCE(b.ordens, 0) END AS pedidos_12meses,
            CASE WHEN r.ttpedida = 0 THEN 0 ELSE r.media_pedidos_12meses END AS media_pedidos_12meses,
            r.ttpedida,
            COALESCE(r.qtde, 0) AS qtde,
            COALESCE(s.situacao, 'ATIVO') AS situacao
        FROM temp_resultados r
        LEFT JOIN tb_class_pedidos1B b ON r.sku = b.sku
        LEFT JOIN tb_sku_status s ON r.sku = s.sku
    """)

    # Próximo bloco
    offset += bloco_size

    # Limpa temporários do bloco
    conn.execute("DROP TABLE IF EXISTS temp_bloco_skus")
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1A")
    conn.execute("DROP TABLE IF EXISTS tb_class_pedidos1B")
    conn.execute("DROP TABLE IF EXISTS temp_resultados")

# ------------------------------------------------------------
# 5) Remove SKUs sem pedidos e sem estoque
# ------------------------------------------------------------
conn.execute("""
    DELETE FROM tb_class_pedidos1
    WHERE pedidos_12meses = 0 AND qtde = 0
""")

# Limpa temp_skus
conn.execute("DROP TABLE IF EXISTS temp_skus")

print("sp5_media_pedidos (versão DuckDB/Python) executado com sucesso. Tabela tb_class_pedidos1 criada.")

conn.close()
