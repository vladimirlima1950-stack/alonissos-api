import os
import duckdb
from datetime import datetime

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    inicio = datetime.now()
    con = duckdb.connect(caminho_banco, read_only=False)

    # ============================================================
    # SS0 – Estatísticas por SKU
    # ============================================================
    con.execute("""
        DROP TABLE IF EXISTS tb_nonsazon15_trend_SS0;

        CREATE TABLE tb_nonsazon15_trend_SS0 AS
        SELECT
            sku,
            AVG(qtde_pedida) AS media_demanda,
            STDDEV_POP(qtde_pedida) AS desvpad_demanda
        FROM tb_a_nonsazon12_trend_fase3
        GROUP BY sku;
    """)

    # ============================================================
    # SS1 – Tabela consolidada
    # ============================================================
    con.execute("""
        DROP TABLE IF EXISTS tb_nonsazon15_trend_SS1;

        CREATE TABLE tb_nonsazon15_trend_SS1 AS
        SELECT
            sku,
            ordem,
            qtde_pedida,
            previsoes,
            NULL::DECIMAL(10,2) AS media_demanda,
            NULL::DECIMAL(20,2) AS desvpad_demanda,
            NULL::DECIMAL(20,2) AS invnorm,
            NULL::INTEGER AS lead_time_dias,
            NULL::DECIMAL(20,2) AS desv_pad_corr,
            NULL::DECIMAL(20,2) AS estoq_segur
        FROM tb_a_nonsazon12_trend_fase3
        ORDER BY sku, ordem;
    """)

    # ============================================================
    # Lead time
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET lead_time_dias = lt.leadtime
        FROM tb_leadtime AS lt
        WHERE tb_nonsazon15_trend_SS1.sku = lt.sku;
    """)

    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET lead_time_dias = 30
        WHERE lead_time_dias IS NULL;
    """)

    # ============================================================
    # Média e desvio
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET media_demanda = s.media_demanda,
            desvpad_demanda = s.desvpad_demanda
        FROM tb_nonsazon15_trend_SS0 AS s
        WHERE tb_nonsazon15_trend_SS1.sku = s.sku;
    """)

    # ============================================================
    # Desvio corrigido
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET desv_pad_corr = desvpad_demanda * POW((lead_time_dias::DOUBLE / 30.0), 0.5);
    """)

    # ============================================================
    # Classes ABC
    # ============================================================
    con.execute("""
        ALTER TABLE tb_nonsazon15_trend_SS1 ADD COLUMN ABC_pedidos VARCHAR(2);
        ALTER TABLE tb_nonsazon15_trend_SS1 ADD COLUMN ABC_valores VARCHAR(2);

        UPDATE tb_nonsazon15_trend_SS1
        SET ABC_pedidos = p.class_ABC_pedidos
        FROM tb_class_pedidos2 AS p
        WHERE tb_nonsazon15_trend_SS1.sku = p.sku;

        UPDATE tb_nonsazon15_trend_SS1
        SET ABC_valores = v.class_ABC_valores
        FROM tb_class_valores2 AS v
        WHERE tb_nonsazon15_trend_SS1.sku = v.sku;
    """)

    # ============================================================
    # Custos
    # ============================================================
    con.execute("""
        ALTER TABLE tb_nonsazon15_trend_SS1 ADD COLUMN custo_unit DECIMAL(20,4);

        UPDATE tb_nonsazon15_trend_SS1
        SET custo_unit = c.custo_unit
        FROM tb_custos AS c
        WHERE tb_nonsazon15_trend_SS1.sku = c.sku;
    """)

    # ============================================================
    # invnorm (histórico)
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (2.33 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit < 10;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (2.06 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit < 10;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.89 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit < 10;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.75 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit >= 10 AND custo_unit < 100;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.65 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit >= 10 AND custo_unit < 100;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.56 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit >= 10 AND custo_unit < 100;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.48 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit >= 100 AND custo_unit < 1000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.41 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit >= 100 AND custo_unit < 1000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.34 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit >= 100 AND custo_unit < 1000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.29 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit >= 1000 AND custo_unit < 10000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.23 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit >= 1000 AND custo_unit < 10000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.18 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit >= 1000 AND custo_unit < 10000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.13 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit >= 10000 AND custo_unit < 100000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.08 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit >= 10000 AND custo_unit < 100000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (1.04 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit >= 10000 AND custo_unit < 100000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (0.99 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'A' AND custo_unit >= 100000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (0.96 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'B' AND custo_unit >= 100000;

        UPDATE tb_nonsazon15_trend_SS1
        SET invnorm = (0.92 * desv_pad_corr) + media_demanda
        WHERE ABC_pedidos = 'C' AND custo_unit >= 100000;
    """)

    # ============================================================
    # Estoque de segurança
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET estoq_segur = (invnorm - media_demanda);
    """)

    # ============================================================
    # Previsões negativas / zero
    # ============================================================
    con.execute("""
        UPDATE tb_nonsazon15_trend_SS1
        SET previsoes = 0
        WHERE previsoes < 0;

        UPDATE tb_nonsazon15_trend_SS1
        SET estoq_segur = 0
        WHERE previsoes = 0;
    """)

    con.close()
    fim = datetime.now()

    return {
        "nome_programa": "apato_096_nonsazon_trend_SS1",
        "inicio": str(inicio),
        "fim": str(fim),
        "status": "OK",
        "mensagem": "Programa executado com sucesso."
    }
