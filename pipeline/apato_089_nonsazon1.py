# apato_089_nonsazon1

# apato_089_nonsazon1.py

# apato_089_nonsazon1 - versão multi-cliente
# Equivalente 100% ao MySQL sp8_A_nonsazon1

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
con = duckdb.connect(database=caminho_banco, read_only=False)

# ============================================================
# 1) Tabela base tb_A_nonsazon1
# ============================================================

con.execute("DROP TABLE IF EXISTS tb_A_nonsazon1")
con.execute("""
    CREATE TABLE tb_A_nonsazon1 AS
    SELECT * FROM tb_vendas_total3
""")

con.execute("ALTER TABLE tb_A_nonsazon1 ADD COLUMN anal_yn VARCHAR(1)")

# ============================================================
# 2) Tabela tb_analisadas
# ============================================================

con.execute("DROP TABLE IF EXISTS tb_analisadas")
con.execute("""
    CREATE TABLE tb_analisadas (
        sku VARCHAR(30)
    )
""")

con.execute("""
    INSERT INTO tb_analisadas (sku)
    SELECT DISTINCT sku FROM tb_trend3_somas_e_medias_fase1
""")

# ============================================================
# 3) Marcar SKUs analisados
# ============================================================

con.execute("""
    UPDATE tb_A_nonsazon1
    SET anal_yn = 'Y'
    WHERE sku IN (SELECT sku FROM tb_analisadas)
""")

# ============================================================
# 4) Remover SKUs analisados
# ============================================================

con.execute("""
    DELETE FROM tb_A_nonsazon1
    WHERE anal_yn = 'Y'
""")

# ============================================================
# 5) Criar tabela tb_A_trend1_temp (estrutura igual ao MySQL)
# ============================================================

con.execute("DROP TABLE IF EXISTS tb_A_trend1_temp")
con.execute("""
    CREATE TABLE tb_A_trend1_temp (
        sku VARCHAR(30),
        class_ABC_pedidos VARCHAR(2),
        class_ABC_valores VARCHAR(2),
        y_qtde DECIMAL(20,2),
        x_ordem INT,
        media_x DECIMAL(20,2),
        media_y DECIMAL(20,2)
    )
""")

con.execute("""
    INSERT INTO tb_A_trend1_temp (sku, class_ABC_pedidos, class_ABC_valores, y_qtde, x_ordem)
    SELECT sku, class_ABC_pedidos, class_ABC_valores, qtde_pedida, ordem
    FROM tb_A_nonsazon1
""")

# ============================================================
# 6) Criar tabela tb_aux2 (médias)
# ============================================================

con.execute("DROP TABLE IF EXISTS tb_aux2")
con.execute("""
    CREATE TABLE tb_aux2 AS
    SELECT sku,
           AVG(qtde_pedida) AS media_y,
           AVG(ordem) AS media_x
    FROM tb_A_nonsazon1
    GROUP BY sku
""")

# ============================================================
# 7) Atualizar médias na tb_A_trend1_temp (JOIN equivalente ao MySQL)
# ============================================================

con.execute("""
    UPDATE tb_A_trend1_temp
    SET media_x = aux.media_x,
        media_y = aux.media_y
    FROM tb_aux2 AS aux
    WHERE tb_A_trend1_temp.sku = aux.sku
""")

# ============================================================
# 8) Criar tabela tb_A_trend2_temp (estrutura igual ao MySQL)
# ============================================================

con.execute("DROP TABLE IF EXISTS tb_A_trend2_temp")
con.execute("""
    CREATE TABLE tb_A_trend2_temp (
        sku VARCHAR(30),
        class_ABC_pedidos VARCHAR(2),
        class_ABC_valores VARCHAR(2),
        y_qtde DECIMAL(20,2),
        x_ordem INT,
        media_x DECIMAL(20,2),
        media_y DECIMAL(20,2),
        prod_x DECIMAL(20,2),
        prod_y DECIMAL(20,2),
        prod_xy DECIMAL(20,2)
    )
""")

con.execute("""
    INSERT INTO tb_A_trend2_temp (sku, class_ABC_pedidos, class_ABC_valores, y_qtde, x_ordem)
    SELECT sku, class_ABC_pedidos, class_ABC_valores, qtde_pedida, ordem
    FROM tb_A_nonsazon1
""")

print("apato_089_nonsazon1.py executado com sucesso — equivalente ao MySQL sp8_A_nonsazon1.")

con.close()
