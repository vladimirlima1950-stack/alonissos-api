# apato_000_master_pipeline.py
# Pipeline mestre automático — processa todos os clientes, um por vez

import os
import sys
import importlib
from datetime import datetime
import duckdb

# ============================================================
# Ajuste CRÍTICO: adiciona a pasta "pipeline" ao PYTHONPATH
# ============================================================

sys.path.append(os.path.join(os.path.dirname(__file__), "pipeline"))


# ============================================================
# Função para processar UM cliente
# ============================================================

def processar_cliente(pasta_cliente):
    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    pasta_logs = os.path.join(pasta_cliente, "logs")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    os.makedirs(pasta_processamento, exist_ok=True)
    os.makedirs(pasta_logs, exist_ok=True)

    log_file = os.path.join(pasta_logs, "pipeline_log.txt")

    def log(msg):
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} - {msg}\n")
        print(msg)

    # ============================================================
    # 0) Verificar se há arquivos de entrada
    # ============================================================

    pasta_entrada = os.path.join(pasta_cliente, "entrada")

    arquivos_entrada = [
        f for f in os.listdir(pasta_entrada)
        if os.path.isfile(os.path.join(pasta_entrada, f))
    ]

    if len(arquivos_entrada) == 0:
        log("Nenhum arquivo de entrada encontrado. Cliente será ignorado.")
        log(f"FINALIZADO (SEM PROCESSAMENTO) PARA O CLIENTE: {pasta_cliente}")
        return

    log("==============================================")
    log(f"INÍCIO DO PROCESSAMENTO DO CLIENTE: {pasta_cliente}")
    log("==============================================")

    # ============================================================
    # 1) Recriar banco DuckDB do zero
    # ============================================================

    if os.path.exists(caminho_banco):
        os.remove(caminho_banco)
        log("Banco DuckDB removido para recriação.")

    con = duckdb.connect(caminho_banco, read_only=False)
    con.execute("""
        CREATE TABLE tb_tempo_programa (
            nome_programa TEXT,
            inicio TIMESTAMP,
            fim TIMESTAMP,
            evento TEXT
        )
    """)
    con.close()
    log("Banco DuckDB recriado e tabela de tempo inicializada.")

    # ============================================================
    # 2) Lista oficial de scripts Python
    # ============================================================

    programas_python = [
        "apato_022_cria_tabelas_originais",
        "apato_022_cria_tabelas_originais_complementares",
        "apato_030_insere_data",
        "apato_031_prepara_vendas",
        "apato_040_elimina_ordem",
        "apato_050_media_pedidos",
        "apato_060_class_ABC_pedidos",
        "apato_070_class_ABC_valores1A",
        "apato_071_class_ABC_valores1B",
        "apato_072_class_ABC_valores_1C",
        "apato_080_sazon1",
        "apato_081_sazon1A",
        "apato_082_sazon2",

        # BLOCO apato_083 — todas as fases
        "apato_083_sazon3_fase1AA",
        "apato_083_sazon3_fase1AB",
        "apato_083_sazon3_fase1AC",
        "apato_083_sazon3_fase1BA",
        "apato_083_sazon3_fase1BB",
        "apato_083_sazon3_fase1BC",
        "apato_083_sazon3_fase1CA",
        "apato_083_sazon3_fase1CB",
        "apato_083_sazon3_fase1CC",

        "apato_084_sazon4",
        "apato_085_sazon5",
        "apato_0851_trend1",
        "apato_085_sazon3_nontrend1",
        "apato_086_sazon3_nontrend2",
        "apato_087_sazon4_trend1",
        "apato_088_sazon_trend_ln1",
        "apato_089_nonsazon1",

        # BLOCO apato_0891 — todas as fases
        "apato_0891_nonsazon2_AA",
        "apato_0891_nonsazon2_AB",
        "apato_0891_nonsazon2_AC",
        "apato_0891_nonsazon2_BA",
        "apato_0891_nonsazon2_BB",
        "apato_0891_nonsazon2_BC",
        "apato_0891_nonsazon2_CA",
        "apato_0891_nonsazon2_CB",
        "apato_0891_nonsazon2_CC",
        "apato_0891_nonsazon2_unir_fase1",

        "apato_091_trend1",
        "apato_092_notrend1",
        "apato_093_sazon_notrend_SS1",
        "apato_094_sazon_trend_SS1",
        "apato_095_nonsazon_notrend_SS1",
        "apato_096_nonsazon_trend_SS1",
        "apato_097_CDEF_complementar",
        "apato_100_resumo1",
        "apato_102_tabelas_estoq_segur",
        "apato_103_104_unificado_otimizado",
        "apato_105_junta_tabelas_estoq_segur1",
        "apato_106_apresenta1",

        # NOVOS PROGRAMAS (substituem os PHP)
        "apato_gera_plan_tb_apres1_fim",
        "apato_gera_plan_tb_apres2_fim",
        "apato_gera_plan_tb_demandas_previsoes",
        "apato_gera_plan_tb_estoques_segurança",
        "apato_gera_plan_tb_estoques_valores_fim",
        "apato_gera_plan_tb_tempo_programas",
    ]

    # ============================================================
    # 3) Execução dos scripts Python (via import + run)
    # ============================================================

    evento = "OK"

    for programa in programas_python:
        inicio = datetime.now()
        log(f"Executando: {programa}")

        try:
            # IMPORT CORRIGIDO
            modulo = importlib.import_module(f"pipeline.{programa}")
            modulo.run(pasta_cliente)

            evento = "OK"
            log(f"{programa} concluído.")

        except Exception as e:
            evento = f"ERRO: {e}"
            log(f"ERRO ao executar {programa}: {evento}")
            log("Pipeline interrompido para este cliente.")

            fim = datetime.now()
            con = duckdb.connect(caminho_banco, read_only=False)
            con.execute(
                "INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)",
                [programa, inicio, fim, evento],
            )
            con.close()
            break

        fim = datetime.now()

        con = duckdb.connect(caminho_banco, read_only=False)
        con.execute(
            "INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)",
            [programa, inicio, fim, evento],
        )
        con.close()

    if evento != "OK":
        log(f"FINALIZADO COM ERRO PARA O CLIENTE: {pasta_cliente}")
        log("==============================================\n")
        return

    log(f"FINALIZADO COM SUCESSO PARA O CLIENTE: {pasta_cliente}")
    log("==============================================\n")


# ============================================================
# Execução direta (modo desktop)
# ============================================================

def apato_000_master_pipeline():

    base_clientes = r"D:\AAAAAA_processamentos\clientes"

    clientes = [
        os.path.join(base_clientes, nome)
        for nome in os.listdir(base_clientes)
        if os.path.isdir(os.path.join(base_clientes, nome))
    ]

    print("Clientes detectados:")
    for c in clientes:
        print(" -", c)

    print("\nIniciando processamento sequencial...\n")

    for cliente in clientes:
        processar_cliente(cliente)

    print("\n=== PIPELINE COMPLETO ===")


if __name__ == "__main__":
    apato_000_master_pipeline()
