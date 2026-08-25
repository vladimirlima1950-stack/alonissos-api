# apato_100_resumo1.py
# Compatível 100% com o MySQL sp10_resumo1


# Baseado no programa inglês aduck_100_resumo1.py

# apato_100_resumo1 - versão multi-cliente
# Compatível 100% com o MySQL sp10_resumo1

import sys
import os
import duckdb
from datetime import datetime

def apato_100_resumo1(pasta_cliente):

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    resultado = apato_100_resumo1(pasta_cliente)
    print(resultado)
