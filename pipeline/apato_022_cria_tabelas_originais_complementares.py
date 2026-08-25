# apato_022_cria_tabelas_originais_complementares

# apato_022_cria_tabelas_originais_complementares - versão multi-cliente

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
conn = duckdb.connect(caminho_banco)

# ============================================================
# 2. EXECUÇÃO DAS TABELAS COMPLEMENTARES
# ============================================================

# 1. tb_vendas_sku_somente
conn.execute("DROP TABLE IF EXISTS tb_vendas_sku_somente")
conn.execute("""
    CREATE TABLE tb_vendas_sku_somente AS
    SELECT DISTINCT sku FROM tb_vendas
    ORDER BY sku
""")

# 2. tb_estoques_sku_somente
conn.execute("DROP TABLE IF EXISTS tb_estoques_sku_somente")
conn.execute("""
    CREATE TABLE tb_estoques_sku_somente AS
    SELECT DISTINCT sku FROM tb_estoques
    ORDER BY sku
""")

# 3. Remover SKUs que já existem em vendas
conn.execute("""
    DELETE FROM tb_estoques_sku_somente
    USING tb_vendas_sku_somente
    WHERE tb_estoques_sku_somente.sku = tb_vendas_sku_somente.sku
""")

# 4. Inserir SKUs faltantes em tb_vendas
conn.execute("""
    INSERT INTO tb_vendas (sku, numero_ordem, data_desejada, qtde_pedida_orig, qtde_pedida)
    SELECT sku, 'AAAAAA', NULL, 0, 0
    FROM tb_estoques_sku_somente
""")

print("Complemento executado: SKUs faltantes adicionados em tb_vendas.")

conn.close()
