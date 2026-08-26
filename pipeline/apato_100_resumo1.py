import os
import duckdb
from datetime import datetime

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    inicio = datetime.now()
    con = duckdb.connect(caminho_banco, read_only=False)

    # ============================================================
    # 1) Criar tabela tb_resumo1
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_resumo1;")

    con.execute("""
        CREATE TABLE tb_resumo1 (
            sku VARCHAR,
            lead_time_dias INTEGER,
            ordem INTEGER,
            qtde_pedida DECIMAL(10,2),
            previsao DECIMAL(10,2),
            estoq_segur DECIMAL(10,2)
        );
    """)

    # ============================================================
    # 2) Inserir dados de tb_nonsazon15_trend_SS1
    # ============================================================
    con.execute("""
        INSERT INTO tb_resumo1 (sku, lead_time_dias, ordem, qtde_pedida, previsao, estoq_segur)
        SELECT sku, lead_time_dias, ordem, qtde_pedida, previsoes, estoq_segur
        FROM tb_nonsazon15_trend_SS1;
    """)

    # ============================================================
    # 3) Inserir dados de tb_nonsazon13_notrend_SS1
    # ============================================================
    con.execute("""
        INSERT INTO tb_resumo1 (sku, lead_time_dias, ordem, qtde_pedida, previsao, estoq_segur)
        SELECT sku, lead_time_dias, ordem, qtde_pedida, previsao, estoq_segur
        FROM tb_nonsazon13_notrend_SS1;
    """)

    # ============================================================
    # 4) Inserir dados de tb_sazon12_trend_SS1
    # ============================================================
    con.execute("""
        INSERT INTO tb_resumo1 (sku, lead_time_dias, ordem, qtde_pedida, previsao, estoq_segur)
        SELECT sku, lead_time_dias, ordem, qtde_pedida, previsoes, estoq_segur_is
        FROM tb_sazon12_trend_SS1;
    """)

    # ============================================================
    # 5) Inserir dados de tb_sazon11_notrend_SS1
    # ============================================================
    con.execute("""
        INSERT INTO tb_resumo1 (sku, lead_time_dias, ordem, qtde_pedida, previsao, estoq_segur)
        SELECT sku, lead_time_dias, ordem, qtde_pedida, previsoes, estoq_segur_is
        FROM tb_sazon11_notrend_SS1;
    """)

    con.close()
    fim = datetime.now()

    return {
        "nome_programa": "apato_100_resumo1",
        "inicio": str(inicio),
        "fim": str(fim),
        "status": "OK",
        "mensagem": "Programa executado com sucesso."
    }
