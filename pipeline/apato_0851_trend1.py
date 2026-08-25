# apato_0851_trend1



# apato_0851_trend1 - versão multi-cliente

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

# ============================================================
# 1) Criar tb_trend1_temp com médias por SKU
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_trend1_temp")
conn.execute("""
    CREATE TABLE tb_trend1_temp AS
    SELECT 
        s.sku,
        s.qtde_pedida_dessas AS y_qtde,
        s.ordem AS x_ordem,
        a.media_ordem AS media_x,
        a.media_dessas AS media_y
    FROM tb_sazon6 s
    JOIN (
        SELECT sku, AVG(ordem) AS media_ordem, AVG(qtde_pedida_dessas) AS media_dessas
        FROM tb_sazon6
        GROUP BY sku
    ) a ON s.sku = a.sku
""")

# ============================================================
# 2) Criar tb_trend2_temp com produtos estatísticos
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_trend2_temp")
conn.execute("""
    CREATE TABLE tb_trend2_temp AS
    SELECT 
        t.sku,
        t.y_qtde,
        t.x_ordem,
        t.media_x,
        t.media_y,
        POW(t.x_ordem - t.media_x, 2) AS prod_x,
        POW(t.y_qtde - t.media_y, 2) AS prod_y,
        (t.x_ordem - t.media_x) * t.y_qtde AS prod_xy
    FROM tb_trend1_temp t
""")

# ============================================================
# 3) Criar tb_trend2_temp2 com somatórios por SKU
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_trend2_temp2")
conn.execute("""
    CREATE TABLE tb_trend2_temp2 AS
    SELECT 
        sku,
        SUM(prod_x) AS Soma_Sxx,
        SUM(prod_y) AS Soma_Syy,
        SUM(prod_xy) AS Soma_Sxy
    FROM tb_trend2_temp
    GROUP BY sku
""")

# ============================================================
# 4) Criar tb_trend3_somas_e_medias_fase1
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_trend3_somas_e_medias_fase1")
conn.execute("""
    CREATE TABLE tb_trend3_somas_e_medias_fase1 AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY t.sku) AS id_reg,
        t.sku,
        t.media_x,
        t.media_y,
        s.Soma_Sxx,
        s.Soma_Syy,
        s.Soma_Sxy,
        s.Soma_Sxy / NULLIF(s.Soma_Sxx, 0) AS inclina_b,
        t.media_y - (s.Soma_Sxy / NULLIF(s.Soma_Sxx, 0)) * t.media_x AS intersec_a,
        NULL::DECIMAL(20,4) AS erro_Eb,
        NULL::DECIMAL(20,4) AS tcalc,
        NULL::VARCHAR AS trend_notrend
    FROM (
        SELECT sku, media_x, media_y
        FROM tb_trend1_temp
        GROUP BY sku, media_x, media_y
    ) t
    JOIN tb_trend2_temp2 s ON t.sku = s.sku
""")

# ============================================================
# 5) Calcular erro_Eb
# ============================================================

conn.execute("""
    UPDATE tb_trend3_somas_e_medias_fase1
    SET erro_Eb = POW(((Soma_Syy - inclina_b * Soma_Sxy) / ((24 - 2) * Soma_Sxx)), 0.5)
    WHERE Soma_Sxx != 0
""")

# ============================================================
# 6) Calcular tcalc
# ============================================================

conn.execute("""
    UPDATE tb_trend3_somas_e_medias_fase1
    SET tcalc = CASE
        WHEN erro_Eb = 0 THEN 9999
        ELSE inclina_b / erro_Eb
    END
""")

# ============================================================
# 7) Classificar como trend ou notrend
# ============================================================

conn.execute("""
    UPDATE tb_trend3_somas_e_medias_fase1
    SET trend_notrend = CASE
        WHEN inclina_b = 0 THEN 'notrend'
        WHEN tcalc > 2.047 THEN 'trend'
        WHEN tcalc <= 2.047 AND tcalc >= 0 THEN 'notrend'
        WHEN tcalc < -2.047 THEN 'trend'
        WHEN tcalc >= -2.047 AND tcalc < 0 THEN 'notrend'
    END
""")

print("Tabela tb_trend3_somas_e_medias_fase1 criada com sucesso com análise de tendência por SKU.")

conn.close()
