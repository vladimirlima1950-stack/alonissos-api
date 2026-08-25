# apato_090_nonsazon2



import duckdb

# Caminho do banco DuckDB
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'
conn = duckdb.connect(caminho_banco)

# 1. Criar cópia de trabalho tb_A_trend2_temp_filtro_AA
conn.execute("DROP TABLE IF EXISTS tb_A_trend2_temp_filtro_AA")
conn.execute("""
    CREATE TABLE tb_A_trend2_temp_filtro_AA AS
    SELECT * FROM tb_A_trend2_temp
""")

# 2. Atualizar médias via JOIN
conn.execute("""
    UPDATE tb_A_trend2_temp_filtro_AA
    SET media_x = t1.media_x,
        media_y = t1.media_y
    FROM tb_A_trend1_temp t1
    WHERE tb_A_trend2_temp_filtro_AA.sku = t1.sku
""")

# 3. Calcular produtos estatísticos
conn.execute("""
    UPDATE tb_A_trend2_temp_filtro_AA
    SET prod_x = POW(x_ordem - media_x, 2),
        prod_y = POW(y_qtde - media_y, 2),
        prod_xy = (x_ordem - media_x) * y_qtde
""")

# 4. Criar somatórios por SKU
conn.execute("DROP TABLE IF EXISTS tb_A_trend2_temp2_AA")
conn.execute("""
    CREATE TABLE tb_A_trend2_temp2_AA AS
    SELECT sku,
           SUM(prod_x) AS Soma_Sxx,
           SUM(prod_y) AS Soma_Syy,
           SUM(prod_xy) AS Soma_Sxy
    FROM tb_A_trend2_temp_filtro_AA
    GROUP BY sku
""")

# 5. Criar tabela de resultados intermediária
conn.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1_AA")
conn.execute("""
    CREATE TABLE tb_A_trend3_somas_e_medias_fase1_AA AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY f.sku) AS id_reg,
        f.sku,
        MAX(f.media_x) AS media_x,
        MAX(f.media_y) AS media_y,
        s.Soma_Sxx,
        s.Soma_Syy,
        s.Soma_Sxy,
        NULL::DECIMAL(20,4) AS inclina_b,
        NULL::DECIMAL(20,4) AS intersec_a,
        NULL::DECIMAL(20,4) AS erro_Eb,
        NULL::DECIMAL(20,4) AS tcalc,
        NULL::VARCHAR AS trend_notrend
    FROM tb_A_trend2_temp_filtro_AA f
    JOIN tb_A_trend2_temp2_AA s ON f.sku = s.sku
    GROUP BY f.sku, s.Soma_Sxx, s.Soma_Syy, s.Soma_Sxy
""")

# 6. Calcular inclinação e intercepto
conn.execute("""
    UPDATE tb_A_trend3_somas_e_medias_fase1_AA
    SET inclina_b = Soma_Sxy / NULLIF(Soma_Sxx, 0),
        intersec_a = media_y - (Soma_Sxy / NULLIF(Soma_Sxx, 0)) * media_x
""")

# 7. Calcular erro padrão da inclinação
conn.execute("""
    UPDATE tb_A_trend3_somas_e_medias_fase1_AA
    SET erro_Eb = POW((Soma_Syy - inclina_b * Soma_Sxy) / ((24 - 2) * NULLIF(Soma_Sxx, 0)), 0.5)
""")

# 8. Calcular tcalc
conn.execute("""
    UPDATE tb_A_trend3_somas_e_medias_fase1_AA
    SET tcalc = CASE
        WHEN erro_Eb = 0 THEN 9999
        ELSE inclina_b / erro_Eb
    END
""")

# 9. Classificar como trend ou notrend
conn.execute("""
    UPDATE tb_A_trend3_somas_e_medias_fase1_AA
    SET trend_notrend = CASE
        WHEN erro_Eb = 0 THEN 'trend'
        WHEN tcalc > 2.047 OR tcalc < -2.047 THEN 'trend'
        ELSE 'notrend'
    END
""")

# 10. Consolidar na tabela final
conn.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1")
conn.execute("""
    CREATE TABLE tb_A_trend3_somas_e_medias_fase1 AS
    SELECT 
        id_reg,
        sku,
        media_x,
        media_y,
        Soma_Sxx,
        Soma_Syy,
        Soma_Sxy,
        inclina_b,
        intersec_a,
        erro_Eb,
        tcalc,
        trend_notrend,
        'AA' AS origem
    FROM tb_A_trend3_somas_e_medias_fase1_AA
""")

print(" Script executado com sucesso: análise de tendência para SKUs não sazonais concluída e consolidada.")

# Encerra a conexão com o banco
conn.close()
