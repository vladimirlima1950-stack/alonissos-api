import os
import duckdb

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("Iniciando apato_095_nonsazon_notrend_SS1...")
    con = duckdb.connect(caminho_banco, read_only=False)

    try:
        # ============================================================
        # 2) Estatísticas por SKU — SS0
        # ============================================================
        con.execute("""
            DROP TABLE IF EXISTS tb_nonsazon13_notrend_SS0;

            CREATE TABLE tb_nonsazon13_notrend_SS0 AS
            SELECT
                sku,
                AVG(qtde_pedida) AS media_demanda,
                STDDEV_POP(qtde_pedida) AS desvpad_demanda
            FROM tb_a_nonsazon12_notrend_fase3
            GROUP BY sku;
        """)

        # ============================================================
        # 3) Tabela consolidada SS1
        # ============================================================
        con.execute("""
            DROP TABLE IF EXISTS tb_nonsazon13_notrend_SS1;

            CREATE TABLE tb_nonsazon13_notrend_SS1 AS
            SELECT
                f.sku,
                f.ordem,
                f.qtde_pedida,
                CASE WHEN f.previsao < 0 THEN 0 ELSE f.previsao END AS previsao,
                t0.media_demanda,
                t0.desvpad_demanda,
                COALESCE(lt.leadtime, 30) AS lead_time_dias,
                NULL AS desv_pad_corr,
                NULL AS invnorm,
                NULL AS estoq_segur,
                cp.class_ABC_pedidos AS ABC_pedidos,
                cv.class_ABC_valores AS ABC_valores,
                c.custo_unit
            FROM tb_a_nonsazon12_notrend_fase3 f
            LEFT JOIN tb_nonsazon13_notrend_SS0 t0 ON f.sku = t0.sku
            LEFT JOIN tb_leadtime lt ON f.sku = lt.sku
            LEFT JOIN tb_class_pedidos2 cp ON f.sku = cp.sku
            LEFT JOIN tb_class_valores2 cv ON f.sku = cv.sku
            LEFT JOIN tb_custos c ON f.sku = c.sku
            ORDER BY f.sku, f.ordem;
        """)

        # ============================================================
        # 4) Desvio padrão corrigido
        # ============================================================
        con.execute("""
            UPDATE tb_nonsazon13_notrend_SS1
            SET desv_pad_corr = desvpad_demanda * POW(lead_time_dias / 30.0, 0.5);
        """)

        # ============================================================
        # 5) invnorm (regra CASE)
        # ============================================================
        con.execute("""
            UPDATE tb_nonsazon13_notrend_SS1
            SET invnorm = CASE
                WHEN ABC_pedidos = 'A' AND custo_unit < 10 THEN (2.33 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit < 10 THEN (2.06 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit < 10 THEN (1.89 * desv_pad_corr) + media_demanda

                WHEN ABC_pedidos = 'A' AND custo_unit >= 10 AND custo_unit < 100 THEN (1.75 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10 AND custo_unit < 100 THEN (1.65 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10 AND custo_unit < 100 THEN (1.56 * desv_pad_corr) + media_demanda

                WHEN ABC_pedidos = 'A' AND custo_unit >= 100 AND custo_unit < 1000 THEN (1.48 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100 AND custo_unit < 1000 THEN (1.41 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100 AND custo_unit < 1000 THEN (1.34 * desv_pad_corr) + media_demanda

                WHEN ABC_pedidos = 'A' AND custo_unit >= 1000 AND custo_unit < 10000 THEN (1.29 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit >= 1000 AND custo_unit < 10000 THEN (1.23 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit >= 1000 AND custo_unit < 10000 THEN (1.18 * desv_pad_corr) + media_demanda

                WHEN ABC_pedidos = 'A' AND custo_unit >= 10000 AND custo_unit < 100000 THEN (1.13 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit >= 10000 AND custo_unit < 100000 THEN (1.08 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit >= 10000 AND custo_unit < 100000 THEN (1.04 * desv_pad_corr) + media_demanda

                WHEN ABC_pedidos = 'A' AND custo_unit >= 100000 THEN (0.99 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'B' AND custo_unit >= 100000 THEN (0.96 * desv_pad_corr) + media_demanda
                WHEN ABC_pedidos = 'C' AND custo_unit >= 100000 THEN (0.92 * desv_pad_corr) + media_demanda

                ELSE media_demanda
            END;
        """)

        # ============================================================
        # 6) Estoque de segurança
        # ============================================================
        con.execute("""
            UPDATE tb_nonsazon13_notrend_SS1
            SET estoq_segur = CASE
                WHEN previsao = 0 THEN 0
                ELSE GREATEST(invnorm - media_demanda, 0)
            END;
        """)

        print("apato_095_nonsazon_notrend_SS1 executado com sucesso.")

    finally:
        con.close()
