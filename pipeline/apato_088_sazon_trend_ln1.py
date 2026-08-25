# apato_088_sazon_trend_ln1 — versão 100% equivalente ao MySQL


# apato_088_sazon_trend_ln1 - versão multi-cliente

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
# tb_sazon_trend_ln111 — SKUs com inclina_b < 0 e previsoes < 1
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon_trend_ln111;")
con.execute("""
    CREATE TABLE tb_sazon_trend_ln111 AS
    SELECT DISTINCT sku
    FROM tb_sazon12_trend_fase3
    WHERE inclina_b < 0
      AND previsoes < 1;
""")

# ---------------------------------------------------------
# tb_sazon_trend_ln112 — base para regressão LN
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon_trend_ln112;")
con.execute("""
    CREATE TABLE tb_sazon_trend_ln112 AS
    SELECT
        f.id_num,
        f.sku,
        f.qtde_pedida,
        f.ordem,
        f.qtde_pedida_dessas,
        f.indice_sazon
    FROM tb_sazon12_trend_fase3 f
    INNER JOIN tb_sazon_trend_ln111 l
        ON f.sku = l.sku;
""")

# adiciona colunas exatamente como no MySQL
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN ordem_ln DECIMAL(10,4);")
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN qtde_pedida_dessas_ln DECIMAL(20,4);")

# ordem_ln = ordem
con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET ordem_ln = ordem;
""")

# qtde_pedida_dessas_ln = ln(qtde_pedida_dessas) ou 1 quando <= 0
con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET qtde_pedida_dessas_ln =
        CASE
            WHEN qtde_pedida_dessas <= 0 THEN 1
            ELSE LN(qtde_pedida_dessas)
        END;
""")

# ---------------------------------------------------------
# tb_sazon_trend_ln113 — médias por SKU
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon_trend_ln113;")
con.execute("""
    CREATE TABLE tb_sazon_trend_ln113 AS
    SELECT
        sku,
        AVG(ordem_ln) AS media_ordem_ln,
        AVG(qtde_pedida_dessas_ln) AS media_dessas_ln
    FROM tb_sazon_trend_ln112
    GROUP BY sku;
""")

# adiciona colunas de médias
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN media_ordem_ln DECIMAL(20,4);")
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN media_dessas_ln DECIMAL(20,4);")

# UPDATE com JOIN — igual ao MySQL
con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET media_ordem_ln = m.media_ordem_ln,
        media_dessas_ln = m.media_dessas_ln
    FROM tb_sazon_trend_ln113 m
    WHERE tb_sazon_trend_ln112.sku = m.sku;
""")

# ---------------------------------------------------------
# variâncias e covariância
# ---------------------------------------------------------
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN x_xm2 DECIMAL(10,4);")
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN y_ym2 DECIMAL(10,4);")
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN x_xm_y DECIMAL(10,4);")

con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET x_xm2 = POW(ordem_ln - media_ordem_ln, 2),
        y_ym2 = POW(qtde_pedida_dessas_ln - media_dessas_ln, 2),
        x_xm_y = (ordem_ln - media_ordem_ln) * qtde_pedida_dessas_ln;
""")

# ---------------------------------------------------------
# tb_sazon_trend_ln114 — Sxx e Sxy
# ---------------------------------------------------------
con.execute("DROP TABLE IF EXISTS tb_sazon_trend_ln114;")
con.execute("""
    CREATE TABLE tb_sazon_trend_ln114 AS
    SELECT
        sku,
        SUM(x_xm2) AS Sxx,
        SUM(x_xm_y) AS Sxy
    FROM tb_sazon_trend_ln112
    GROUP BY sku;
""")

# inclina_b
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN inclina_b DECIMAL(10,4);")

con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET inclina_b = t.Sxy / t.Sxx
    FROM tb_sazon_trend_ln114 t
    WHERE tb_sazon_trend_ln112.sku = t.sku;
""")

# intersec_a
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN intersec_a DECIMAL(10,4);")

con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET intersec_a = media_dessas_ln - (inclina_b * media_ordem_ln);
""")

# ---------------------------------------------------------
# previsao_ln e previsao_exp_saz
# ---------------------------------------------------------
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN previsao_ln DECIMAL(10,4);")
con.execute("ALTER TABLE tb_sazon_trend_ln112 ADD COLUMN previsao_exp_saz DECIMAL(20,2);")

con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET previsao_ln = intersec_a + inclina_b * (ordem + 24);
""")

con.execute("""
    UPDATE tb_sazon_trend_ln112
    SET previsao_exp_saz = EXP(previsao_ln) * indice_sazon;
""")

# ---------------------------------------------------------
# Atualiza tb_sazon12_trend_fase3 — JOIN exato do MySQL
# ---------------------------------------------------------
con.execute("""
    UPDATE tb_sazon12_trend_fase3
    SET previsoes = ln.previsao_exp_saz
    FROM tb_sazon_trend_ln112 ln
    WHERE tb_sazon12_trend_fase3.sku = ln.sku
      AND tb_sazon12_trend_fase3.ordem = ln.ordem;
""")

print("Procedimento apato_088_sazon_trend_ln1 — versão idêntica ao MySQL executado com sucesso.")

con.close()
