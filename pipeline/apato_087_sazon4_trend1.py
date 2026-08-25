# apato_087_sazon4_trend1 — versão 100% equivalente ao MySQL




# apato_087_sazon4_trend1 - versão multi-cliente

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

# ---------------------------------------------------------
# 1) tb_sazon12_trend_fase1  (igual ao MySQL)
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon12_trend_fase1;")
con.execute("""
    CREATE TABLE tb_sazon12_trend_fase1 AS
    SELECT id_num, sku, qtde_pedida, ordem, qtde_pedida_dessas, indice_sazon
    FROM tb_sazon6
    ORDER BY id_num;
""")

# ---------------------------------------------------------
# 2) DELETE com INNER JOIN (igual ao MySQL)
# ---------------------------------------------------------
con.execute("""
    DELETE FROM tb_sazon12_trend_fase1
    USING tb_trend3_somas_e_medias_fase1
    WHERE tb_sazon12_trend_fase1.sku = tb_trend3_somas_e_medias_fase1.sku
      AND tb_trend3_somas_e_medias_fase1.trend_notrend <> 'trend';
""")

# ---------------------------------------------------------
# 3) tb_sazon12_trend_fase2 (igual ao MySQL)
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon12_trend_fase2;")
con.execute("""
    CREATE TABLE tb_sazon12_trend_fase2 AS
    SELECT *
    FROM tb_sazon12_trend_fase1;
""")

# adiciona colunas exatamente como no MySQL (uma por vez)
con.execute("""
    ALTER TABLE tb_sazon12_trend_fase2
    ADD COLUMN inclina_b DECIMAL(13,4);
""")

con.execute("""
    ALTER TABLE tb_sazon12_trend_fase2
    ADD COLUMN intersec_a DECIMAL(13,4);
""")

# ---------------------------------------------------------
# 4) UPDATE com INNER JOIN (igual ao MySQL)
# ---------------------------------------------------------
con.execute("""
    UPDATE tb_sazon12_trend_fase2
    SET inclina_b = t.inclina_b,
        intersec_a = t.intersec_a
    FROM tb_trend3_somas_e_medias_fase1 t
    WHERE tb_sazon12_trend_fase2.sku = t.sku;
""")

# ---------------------------------------------------------
# 5) tb_sazon12_trend_fase3 (igual ao MySQL)
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon12_trend_fase3;")
con.execute("""
    CREATE TABLE tb_sazon12_trend_fase3 AS
    SELECT *
    FROM tb_sazon12_trend_fase2;
""")

con.execute("""
    ALTER TABLE tb_sazon12_trend_fase3
    ADD COLUMN previsoes DECIMAL(13,4);
""")

# ---------------------------------------------------------
# 6) cálculo das previsões (igual ao MySQL)
# ---------------------------------------------------------
con.execute("""
    UPDATE tb_sazon12_trend_fase3
    SET previsoes = (intersec_a + inclina_b * (ordem + 24)) * indice_sazon;
""")

# ---------------------------------------------------------
# 7) previsões negativas viram zero (igual ao MySQL)
# ---------------------------------------------------------
con.execute("""
    UPDATE tb_sazon12_trend_fase3
    SET previsoes = 0
    WHERE previsoes < 0;
""")

print("Procedimento apato_087_sazon4_trend1 — versão idêntica ao MySQL executado com sucesso.")

con.close()
