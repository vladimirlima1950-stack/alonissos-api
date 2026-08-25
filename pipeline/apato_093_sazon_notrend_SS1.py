# apato_093_sazon_notrend_SS1.py
# Equivalente 100% ao MySQL sp9_sazon_notrend_SS1

# Equivalente 100% ao MySQL sp9_sazon_notrend_SS1




import sys
import os
import duckdb

def apato_093_sazon_notrend_SS1(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(database=caminho_banco, read_only=False)

    print("Iniciando apato_093_sazon_notrend_SS1...")

    # ============================================================
    # 1) Tabela principal SS1
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_SS1")
    con.execute("""
        CREATE TABLE tb_sazon11_notrend_SS1 (
            id_num INTEGER,
            sku VARCHAR(30),
            ordem INTEGER,
            qtde_pedida_dessas DECIMAL(13,2),
            alisado DECIMAL(13,2),
            previsoes DECIMAL(13,2),
            indice_sazon DECIMAL(13,2),
            media_demanda_dessas DECIMAL(20,2),
            desvpad_demanda_dessas DECIMAL(20,2),
            invnorm DECIMAL(20,2),
            lead_time_dias INTEGER,
            estoq_segur_is DECIMAL(20,2),
            desv_pad_corr DECIMAL(20,2),
            ABC_pedidos VARCHAR(2),
            ABC_valores VARCHAR(2),
            custo_unit DECIMAL(20,4),
            qtde_pedida DECIMAL(10,2),
            cv_demanda DECIMAL(20,6),
            media_prev_12 DECIMAL(20,6),
            desv_pad_futuro DECIMAL(20,6),
            usar_futuro BOOLEAN
        )
    """)

    # ============================================================
    # 2) Tabela SS0 (médias, desvios, CV)
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_sazon11_notrend_SS0")
    con.execute("""
        CREATE TABLE tb_sazon11_notrend_SS0 AS
        SELECT
            sku,
            AVG(qtde_pedida_dessas) AS media_demanda_dessas,
            STDDEV_POP(qtde_pedida_dessas) AS stddev_demanda_dessas,
            CASE
                WHEN AVG(qtde_pedida_dessas) > 0
                THEN STDDEV_POP(qtde_pedida_dessas) / AVG(qtde_pedida_dessas)
                ELSE 0
            END AS cv_demanda
        FROM tb_sazon11_notrend_fase3
        GROUP BY sku
    """)

    # ============================================================
    # 3) Inserir dados base em SS1
    # ============================================================
    con.execute("""
        INSERT INTO tb_sazon11_notrend_SS1 (
            id_num, sku, ordem,
            qtde_pedida_dessas, alisado, previsoes, indice_sazon
        )
        SELECT
            id_num, sku, ordem,
            qtde_pedida_dessas, alisado, previsoes, indice_sazon
        FROM tb_sazon11_notrend_fase3
        ORDER BY id_num
    """)

    # ============================================================
    # 4) Lead time
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET lead_time_dias = t.leadtime
        FROM tb_leadtime AS t
        WHERE tb_sazon11_notrend_SS1.sku = t.sku
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET lead_time_dias = 30
        WHERE lead_time_dias IS NULL
    """)

    # ============================================================
    # 5) Médias, desvios e CV
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET media_demanda_dessas = s.media_demanda_dessas,
            desvpad_demanda_dessas = s.stddev_demanda_dessas,
            cv_demanda = s.cv_demanda
        FROM tb_sazon11_notrend_SS0 AS s
        WHERE tb_sazon11_notrend_SS1.sku = s.sku
    """)

    # ============================================================
    # 6) Desvio corrigido pelo lead time
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET desv_pad_corr =
            desvpad_demanda_dessas * POW((lead_time_dias::DOUBLE / 30.0), 0.5)
    """)

    # ============================================================
    # 7) Classes ABC e custo unitário
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET ABC_pedidos = p.class_ABC_pedidos
        FROM tb_class_pedidos2 AS p
        WHERE tb_sazon11_notrend_SS1.sku = p.sku
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET ABC_valores = v.class_ABC_valores
        FROM tb_class_valores2 AS v
        WHERE tb_sazon11_notrend_SS1.sku = v.sku
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET custo_unit = c.custo_unit
        FROM tb_custos AS c
        WHERE tb_sazon11_notrend_SS1.sku = c.sku
    """)

    # ============================================================
    # 8) media_prev_12
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET media_prev_12 = t.media_prev_12
        FROM (
            SELECT sku, AVG(previsoes) AS media_prev_12
            FROM tb_sazon11_notrend_SS1
            GROUP BY sku
        ) AS t
        WHERE tb_sazon11_notrend_SS1.sku = t.sku
    """)

    # ============================================================
    # 9) usar_futuro
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET usar_futuro =
            CASE
                WHEN media_prev_12 < 0.8 * media_demanda_dessas THEN TRUE
                WHEN cv_demanda > 0.5 THEN TRUE
                ELSE FALSE
            END
    """)

    # ============================================================
    # 10) desv_pad_futuro
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET desv_pad_futuro =
            cv_demanda * media_prev_12 *
            POW((lead_time_dias::DOUBLE / 30.0), 0.5)
        WHERE usar_futuro = TRUE
    """)

    # ============================================================
    # 11) invnorm histórico
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET invnorm = (
            desv_pad_corr *
            CASE
                WHEN ABC_pedidos = 'A' AND custo_unit < 10 THEN 2.33
                WHEN ABC_pedidos = 'B' AND custo_unit < 10 THEN 2.06
                WHEN ABC_pedidos = 'C' AND custo_unit < 10 THEN 1.89
                WHEN ABC_pedidos = 'A' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.75
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.65
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.56
                WHEN ABC_pedidos = 'A' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.48
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.41
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.34
                WHEN ABC_pedidos = 'A' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.29
                WHEN ABC_pedidos = 'B' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.23
                WHEN ABC_pedidos = 'C' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.18
                WHEN ABC_pedidos = 'A' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.13
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.08
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.04
                WHEN ABC_pedidos = 'A' AND custo_unit >= 100000 THEN 0.99
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100000 THEN 0.96
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100000 THEN 0.92
            END
        ) + media_demanda_dessas
        WHERE usar_futuro = FALSE
    """)

    # ============================================================
    # 12) invnorm futuro
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET invnorm = (
            desv_pad_futuro *
            CASE
                WHEN ABC_pedidos = 'A' AND custo_unit < 10 THEN 2.33
                WHEN ABC_pedidos = 'B' AND custo_unit < 10 THEN 2.06
                WHEN ABC_pedidos = 'C' AND custo_unit < 10 THEN 1.89
                WHEN ABC_pedidos = 'A' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.75
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.65
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10 AND custo_unit < 100 THEN 1.56
                WHEN ABC_pedidos = 'A' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.48
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.41
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100 AND custo_unit < 1000 THEN 1.34
                WHEN ABC_pedidos = 'A' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.29
                WHEN ABC_pedidos = 'B' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.23
                WHEN ABC_pedidos = 'C' AND custo_unit >= 1000 AND custo_unit < 10000 THEN 1.18
                WHEN ABC_pedidos = 'A' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.13
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.08
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10000 AND custo_unit < 100000 THEN 1.04
                WHEN ABC_pedidos = 'A' AND custo_unit >= 100000 THEN 0.99
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100000 THEN 0.96
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100000 THEN 0.92
            END
        ) + media_prev_12
        WHERE usar_futuro = TRUE
    """)

    # ============================================================
    # 13) Estoque de segurança
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET estoq_segur_is = (invnorm - media_demanda_dessas) * indice_sazon
        WHERE usar_futuro = FALSE
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET estoq_segur_is = (invnorm - media_prev_12) * indice_sazon
        WHERE usar_futuro = TRUE
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET estoq_segur_is = LEAST(estoq_segur_is, media_prev_12 * 1.5)
    """)

    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET estoq_segur_is = 0
        WHERE media_prev_12 = 0
    """)

    # ============================================================
    # 14) qtde_pedida (fase1)
    # ============================================================
    con.execute("""
        UPDATE tb_sazon11_notrend_SS1
        SET qtde_pedida = f.qtde_pedida
        FROM tb_sazon11_notrend_fase1 AS f
        WHERE tb_sazon11_notrend_SS1.sku = f.sku
        AND tb_sazon11_notrend_SS1.ordem = f.ordem
    """)

    print("apato_093_sazon_notrend_SS1 executado com sucesso — equivalente ao MySQL sp9_sazon_notrend_SS1.")

    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_093_sazon_notrend_SS1(pasta_cliente)
