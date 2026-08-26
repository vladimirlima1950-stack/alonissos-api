import os
import duckdb

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    print("Iniciando apato_094_sazon_trend_SS1...")
    con = duckdb.connect(caminho_banco, read_only=False)

    try:
        # ============================================================
        # 2. Criar tb_sazon12_trend_SS0
        # ============================================================
        con.execute("""
            DROP TABLE IF EXISTS tb_sazon12_trend_SS0;

            CREATE TABLE tb_sazon12_trend_SS0 AS
            SELECT
                sku,
                AVG(qtde_pedida_dessas) AS media_demanda_dessas,
                STDDEV_POP(qtde_pedida_dessas) AS stddev_demanda_dessas,
                CASE
                    WHEN AVG(qtde_pedida_dessas) > 0
                    THEN STDDEV_POP(qtde_pedida_dessas) / AVG(qtde_pedida_dessas)
                    ELSE 0
                END AS cv_demanda
            FROM tb_sazon12_trend_fase3
            GROUP BY sku;
        """)

        # ============================================================
        # 3. Criar tb_sazon12_trend_SS1
        # ============================================================
        con.execute("""
            DROP TABLE IF EXISTS tb_sazon12_trend_SS1;

            CREATE TABLE tb_sazon12_trend_SS1 AS
            SELECT
                id_num, sku, ordem, qtde_pedida_dessas, previsoes, indice_sazon
            FROM tb_sazon12_trend_fase3
            ORDER BY id_num;
        """)

        # ============================================================
        # 4. Adicionar colunas básicas
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN media_demanda_dessas DECIMAL(20,2);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN desvpad_demanda_dessas DECIMAL(20,2);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN invnorm DECIMAL(20,2);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN lead_time_dias INTEGER;
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN estoq_segur_is DECIMAL(20,2);
        """)

        # ============================================================
        # 5. Lead time
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET lead_time_dias = t.leadtime
            FROM tb_leadtime AS t
            WHERE tb_sazon12_trend_SS1.sku = t.sku;
        """)

        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET lead_time_dias = 30
            WHERE lead_time_dias IS NULL;
        """)

        # ============================================================
        # 6. Médias e desvios
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET media_demanda_dessas = s.media_demanda_dessas,
                desvpad_demanda_dessas = s.stddev_demanda_dessas
            FROM tb_sazon12_trend_SS0 AS s
            WHERE tb_sazon12_trend_SS1.sku = s.sku;
        """)

        # ============================================================
        # 7. Desvio corrigido
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN desv_pad_corr DECIMAL(20,2);

            UPDATE tb_sazon12_trend_SS1
            SET desv_pad_corr = desvpad_demanda_dessas * POW((lead_time_dias::DOUBLE / 30.0), 0.5);
        """)

        # ============================================================
        # 8. Classes ABC
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN ABC_pedidos VARCHAR;
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN ABC_valores VARCHAR;

            UPDATE tb_sazon12_trend_SS1
            SET ABC_pedidos = p.class_ABC_pedidos
            FROM tb_class_pedidos2 AS p
            WHERE tb_sazon12_trend_SS1.sku = p.sku;

            UPDATE tb_sazon12_trend_SS1
            SET ABC_valores = v.class_ABC_valores
            FROM tb_class_valores2 AS v
            WHERE tb_sazon12_trend_SS1.sku = v.sku;
        """)

        # ============================================================
        # 9. Custos
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN custo_unit DECIMAL(20,4);

            UPDATE tb_sazon12_trend_SS1
            SET custo_unit = c.custo_unit
            FROM tb_custos AS c
            WHERE tb_sazon12_trend_SS1.sku = c.sku;
        """)

        # ============================================================
        # 10. Colunas futuro/histórico
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN cv_demanda DECIMAL(20,6);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN media_prev_12 DECIMAL(20,6);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN desv_pad_futuro DECIMAL(20,6);
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN usar_futuro BOOLEAN;
        """)

        # ============================================================
        # 11. cv_demanda
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET cv_demanda = s.cv_demanda
            FROM tb_sazon12_trend_SS0 AS s
            WHERE tb_sazon12_trend_SS1.sku = s.sku;
        """)

        # ============================================================
        # 12. média das previsões
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET media_prev_12 = t.media_prev_12
            FROM (
                SELECT sku, AVG(previsoes) AS media_prev_12
                FROM tb_sazon12_trend_SS1
                GROUP BY sku
            ) AS t
            WHERE tb_sazon12_trend_SS1.sku = t.sku;
        """)

        # ============================================================
        # 13. usar_futuro
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET usar_futuro =
                CASE
                    WHEN media_prev_12 < 0.8 * media_demanda_dessas THEN TRUE
                    WHEN cv_demanda > 0.5 THEN TRUE
                    ELSE FALSE
                END;
        """)

        # ============================================================
        # 14. desvio futuro
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET desv_pad_futuro = cv_demanda * media_prev_12 * POW((lead_time_dias::DOUBLE / 30.0), 0.5)
            WHERE usar_futuro = TRUE;
        """)

        # ============================================================
        # 15. invnorm histórico e futuro
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
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
            WHERE usar_futuro = FALSE;

            UPDATE tb_sazon12_trend_SS1
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
            WHERE usar_futuro = TRUE;
        """)

        # ============================================================
        # 16. Estoque de segurança
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET estoq_segur_is = (invnorm - media_demanda_dessas) * indice_sazon
            WHERE usar_futuro = FALSE;

            UPDATE tb_sazon12_trend_SS1
            SET estoq_segur_is = (invnorm - media_prev_12) * indice_sazon
            WHERE usar_futuro = TRUE;

            UPDATE tb_sazon12_trend_SS1
            SET estoq_segur_is = LEAST(estoq_segur_is, media_prev_12 * 1.5);
        """)

        # ============================================================
        # 17. Ajustes de previsões negativas
        # ============================================================
        con.execute("""
            UPDATE tb_sazon12_trend_SS1
            SET previsoes = 0
            WHERE previsoes <= 0;

            UPDATE tb_sazon12_trend_SS1
            SET estoq_segur_is = 0
            WHERE previsoes = 0;
        """)

        # ============================================================
        # 18. Inserir qtde_pedida
        # ============================================================
        con.execute("""
            ALTER TABLE tb_sazon12_trend_SS1 ADD COLUMN qtde_pedida DECIMAL(13,2);

            UPDATE tb_sazon12_trend_SS1
            SET qtde_pedida = f.qtde_pedida
            FROM tb_sazon12_trend_fase3 AS f
            WHERE tb_sazon12_trend_SS1.sku = f.sku
              AND tb_sazon12_trend_SS1.ordem = f.ordem;
        """)

        print("apato_094_sazon_trend_SS1 executado com sucesso.")

    finally:
        con.close()
