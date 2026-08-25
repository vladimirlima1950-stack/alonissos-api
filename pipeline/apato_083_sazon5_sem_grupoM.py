# apato_083_sazon5_sem_grupoM.py

import duckdb

caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'
conn = duckdb.connect(caminho_banco)

# 1. Tendência: média dos primeiros 6 meses vs últimos 6 meses
conn.execute("DROP TABLE IF EXISTS tb_sazon4_trend_base")
conn.execute("""
    CREATE TABLE tb_sazon4_trend_base AS
    SELECT
        sku,
        AVG(CASE WHEN ordem <= 6 THEN qtde_pedida_dessas END) AS media_ini,
        AVG(CASE WHEN ordem >= 18 THEN qtde_pedida_dessas END) AS media_fim
    FROM tb_sazon4
    GROUP BY sku
""")

# 2. Classificação de tendência
conn.execute("DROP TABLE IF EXISTS tb_sazon4_trend_flag")
conn.execute("""
    CREATE TABLE tb_sazon4_trend_flag AS
    SELECT
        sku,
        media_ini,
        media_fim,
        CASE
            WHEN media_ini IS NULL OR media_fim IS NULL THEN 'SEM_TENDENCIA'
            WHEN media_fim > media_ini * 1.10 THEN 'COM_TENDENCIA'
            WHEN media_fim < media_ini * 0.90 THEN 'COM_TENDENCIA'
            ELSE 'SEM_TENDENCIA'
        END AS flag_tendencia
    FROM tb_sazon4_trend_base
""")

# 3. Sazonalidade: desvio padrão do índice_sazon
conn.execute("DROP TABLE IF EXISTS tb_sazon4_sazon_flag")
conn.execute("""
    CREATE TABLE tb_sazon4_sazon_flag AS
    SELECT
        sku,
        AVG(indice_sazon) AS media_indice,
        STDDEV(indice_sazon) AS desvio_indice,
        CASE
            WHEN desvio_indice IS NULL THEN 'NAO_SAZONAL'
            WHEN desvio_indice > 0.20 THEN 'SAZONAL'
            ELSE 'NAO_SAZONAL'
        END AS flag_sazonal
    FROM tb_sazon4
    GROUP BY sku
""")

# 4. Junta tendência + sazonalidade
conn.execute("DROP TABLE IF EXISTS tb_sazon4_class_final")
conn.execute("""
    CREATE TABLE tb_sazon4_class_final AS
    SELECT
        s.sku,
        s.flag_sazonal,
        t.flag_tendencia
    FROM tb_sazon4_sazon_flag s
    LEFT JOIN tb_sazon4_trend_flag t
      ON s.sku = t.sku
""")

# 5. Tabelas finais

# 5.1 Sazonal sem tendência
conn.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_SS1")
conn.execute("""
    CREATE TABLE tb_sazon11_notrend_SS1 AS
    SELECT f.*, d.*
    FROM tb_sazon4_class_final f
    JOIN tb_sazon4 d ON f.sku = d.sku
    WHERE f.flag_sazonal = 'SAZONAL'
      AND f.flag_tendencia = 'SEM_TENDENCIA'
""")

# 5.2 Sazonal com tendência
conn.execute("DROP TABLE IF EXISTS tb_sazon12_trend_SS1")
conn.execute("""
    CREATE TABLE tb_sazon12_trend_SS1 AS
    SELECT f.*, d.*
    FROM tb_sazon4_class_final f
    JOIN tb_sazon4 d ON f.sku = d.sku
    WHERE f.flag_sazonal = 'SAZONAL'
      AND f.flag_tendencia = 'COM_TENDENCIA'
""")

# 5.3 Não sazonal sem tendência
conn.execute("DROP TABLE IF EXISTS tb_nonsazon13_notrend_SS1")
conn.execute("""
    CREATE TABLE tb_nonsazon13_notrend_SS1 AS
    SELECT f.*, d.*
    FROM tb_sazon4_class_final f
    JOIN tb_sazon4 d ON f.sku = d.sku
    WHERE f.flag_sazonal = 'NAO_SAZONAL'
      AND f.flag_tendencia = 'SEM_TENDENCIA'
""")

# 5.4 Não sazonal com tendência
conn.execute("DROP TABLE IF EXISTS tb_nonsazon15_trend_SS1")
conn.execute("""
    CREATE TABLE tb_nonsazon15_trend_SS1 AS
    SELECT f.*, d.*
    FROM tb_sazon4_class_final f
    JOIN tb_sazon4 d ON f.sku = d.sku
    WHERE f.flag_sazonal = 'NAO_SAZONAL'
      AND f.flag_tendencia = 'COM_TENDENCIA'
""")

print("Módulo 083 sem grupo_M concluído com sucesso.")

conn.close()
