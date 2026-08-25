# apato_001_comandante

import os

# Caminho do banco DuckDB
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'

# 🔥 Sempre recria o banco do zero
if os.path.exists(caminho_banco):
    os.remove(caminho_banco)



import duckdb
import subprocess
from datetime import datetime

# Caminho do banco DuckDB
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'

# Inicializa a tabela de controle de tempo
conn = duckdb.connect(database=caminho_banco, read_only=False)
conn.execute("DROP TABLE IF EXISTS tb_tempo_programa")
conn.execute("""
CREATE TABLE tb_tempo_programa (
    nome_programa TEXT,
    inicio TIMESTAMP,
    fim TIMESTAMP,
    evento TEXT
)
""")
conn.close()

# ============================================================
# LISTA ATUALIZADA DE PROGRAMAS PYTHON
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
    "apato_103_104_otimizado",
    "apato_105_junta_tabelas_estoq_segur1",
    "apato_106_apresenta1"
]

# ============================================================
# LISTA DE PROGRAMAS PHP
# ============================================================

programas_php = [
    "alon_prev_gera_plan_tb_apres1_fim.php",
    "alon_prev_gera_plan_tb_apres2_fim.php",
    "alon_prev_gera_plan_tb_demandas_previsoes.php",
    "alon_prev_gera_plan_tb_estoques_segurança.php",
    "alon_prev_gera_plan_tb_estoques_valores_fim.php",
    "alon_prev_gera_plan_tb_tempo_programas.php"
]

# Caminho base dos scripts
caminho_scripts = r'C:\xampp\htdocs\dashboard\alonissos\PYTHON_DuckDB_programas'
php_exe = r'C:\xampp\php\php.exe'  # Caminho completo do PHP

# ============================================================
# EXECUÇÃO DOS PROGRAMAS PYTHON
# ============================================================

for programa in programas_python:
    inicio = datetime.now()
    caminho_script = f"{caminho_scripts}\\{programa}.py"
    print(f"🚀 Executando: {programa}")

    try:
        resultado = subprocess.run(
            ["python", caminho_script],
            capture_output=True,
            text=True,
            check=True
        )
        evento = "OK"
    except subprocess.CalledProcessError as e:
        evento = f"ERRO: {e.stderr.strip()}"
        print(f"❌ Erro ao executar {programa}: {evento}")

    fim = datetime.now()

    conn = duckdb.connect(database=caminho_banco, read_only=False)
    conn.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, [programa, inicio, fim, evento])
    conn.close()

# ============================================================
# EXECUÇÃO DOS PROGRAMAS PHP
# ============================================================

for programa in programas_php:
    inicio = datetime.now()
    caminho_script = f"{caminho_scripts}\\{programa}"
    print(f"📦 Executando PHP: {programa}")

    try:
        resultado = subprocess.run(
            [php_exe, caminho_script],
            stdout=open("php_log.txt", "a", encoding="utf-8", errors="ignore"),
            stderr=open("php_log.txt", "a", encoding="utf-8", errors="ignore"),
            check=True
        )
        evento = "OK"
    except subprocess.CalledProcessError as e:
        evento = f"ERRO: {e.stderr.strip()}"
        print(f"❌ Erro ao executar {programa}: {evento}")

    fim = datetime.now()

    conn = duckdb.connect(database=caminho_banco, read_only=False)
    conn.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, [programa, inicio, fim, evento])
    conn.close()

print(" Execução completa. Tabela de tempo atualizada.")

# ============================================================
# LIMPEZA DAS TABELAS (EXCETO tb_tempo_programa)
# ============================================================

conn = duckdb.connect(database=caminho_banco, read_only=False)
tabelas = conn.execute("SHOW TABLES").fetchdf()

for nome in tabelas['name']:
    if nome != 'tb_tempo_programa':  # preserva a tabela de controle
        try:
            conn.execute(f'DROP TABLE IF EXISTS "{nome}"')

            print(f"🧹 Tabela eliminada: {nome}")
        except Exception as e:
            print(f"⚠️ Erro ao eliminar {nome}: {e}")

conn.close()
print("🧼 Todas as tabelas foram eliminadas (exceto tb_tempo_programa).")
