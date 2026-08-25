# apato_080_sazon1


# apato_080_sazon1 - versão multi-cliente

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
# 1) Recriar tabela tb_vendas_total3
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_vendas_total3")
conn.execute("""
    CREATE TABLE tb_vendas_total3 (
        sku VARCHAR(30),
        qtde_pedida_orig DECIMAL(20,2),
        ano_mes INT,
        ordem INT,
        sinal VARCHAR(1),
        qtde_pedida DECIMAL(20,2),
        desvpad DECIMAL(20,2),
        media DECIMAL(20,2)
    )
""")

# ============================================================
# 2) Inserir dados agregados
# ============================================================

conn.execute("""
    INSERT INTO tb_vendas_total3 (sku, qtde_pedida_orig, ano_mes, ordem)
    SELECT sku, SUM(qtde_pedida), ano_mes, ordem
    FROM tb_vendas_total2
    GROUP BY sku, ano_mes, ordem
""")

# ============================================================
# 3) Recriar tabela tb_vendas_car1
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_vendas_car1")
conn.execute("""
    CREATE TABLE tb_vendas_car1 AS
    SELECT sku, class_abc_pedidos AS classe
    FROM tb_class_pedidos2
    WHERE class_abc_pedidos <= 'C'
""")

# ============================================================
# 4) Atualizar sinal com classe
# ============================================================

conn.execute("""
    UPDATE tb_vendas_total3
    SET sinal = (
        SELECT classe
        FROM tb_vendas_car1
        WHERE tb_vendas_car1.sku = tb_vendas_total3.sku
    )
""")

# ============================================================
# 5) Remover registros sem sinal
# ============================================================

conn.execute("""
    DELETE FROM tb_vendas_total3
    WHERE sinal IS NULL
""")

# ============================================================
# 6) Criar tabela auxiliar com média e desvio padrão
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_vendas1_aux")
conn.execute("""
    CREATE TABLE tb_vendas1_aux AS
    SELECT sku,
           AVG(qtde_pedida_orig) AS qtde,
           STDDEV_POP(qtde_pedida_orig) AS desvpad
    FROM tb_vendas_total3
    GROUP BY sku
""")

# ============================================================
# 7) Atualizar média e desvio padrão
# ============================================================

conn.execute("""
    UPDATE tb_vendas_total3
    SET media = (
        SELECT qtde FROM tb_vendas1_aux WHERE tb_vendas1_aux.sku = tb_vendas_total3.sku
    ),
    desvpad = (
        SELECT desvpad FROM tb_vendas1_aux WHERE tb_vendas1_aux.sku = tb_vendas_total3.sku
    )
""")

# ============================================================
# 8) Calcular qtde_pedida com base na sazonalidade
# ============================================================

conn.execute("""
    UPDATE tb_vendas_total3
    SET qtde_pedida = CASE
        WHEN media = 0 THEN qtde_pedida_orig
        WHEN (qtde_pedida_orig - media) / NULLIF(desvpad, 0) >= 3 THEN media + 2 * desvpad
        ELSE qtde_pedida_orig
    END
""")

# ============================================================
# 9) Corrigir valores nulos
# ============================================================

conn.execute("""
    UPDATE tb_vendas_total3
    SET qtde_pedida = qtde_pedida_orig
    WHERE qtde_pedida IS NULL
""")

# ============================================================
# 10) Criar tabela de frequência mensal
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_pedidos_freq1")
conn.execute("""
    CREATE TABLE tb_pedidos_freq1 AS
    SELECT sku,
           SUM(qtde_pedida) AS qtde_mes,
           ano_mes
    FROM tb_vendas_total3
    GROUP BY sku, ano_mes
""")

# ============================================================
# 11) Adicionar coluna de frequência
# ============================================================

conn.execute("ALTER TABLE tb_pedidos_freq1 ADD COLUMN freq INT")

# ============================================================
# 12) Atualizar frequência
# ============================================================

conn.execute("""
    UPDATE tb_pedidos_freq1
    SET freq = CASE
        WHEN qtde_mes > 0 THEN 1
        ELSE 0
    END
""")

# ============================================================
# 13) Criar tabela de frequência total por SKU
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_pedidos_freq2")
conn.execute("""
    CREATE TABLE tb_pedidos_freq2 AS
    SELECT sku,
           SUM(freq) AS freq_tot
    FROM tb_pedidos_freq1
    GROUP BY sku
""")

print("Tabelas de sazonalidade e frequência criadas com sucesso.")

conn.close()
