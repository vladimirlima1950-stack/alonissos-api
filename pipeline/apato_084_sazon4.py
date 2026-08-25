# apato_084_sazon4.py



# apato_084_sazon4 - versão multi-cliente

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
conn = duckdb.connect(database=caminho_banco, read_only=False)

# ============================================================
# 1) Consolidar tb_sazon3AA…CC dentro de tb_sazon3
# ============================================================

tabelas_fonte = [
    "tb_sazon3AA", "tb_sazon3AB", "tb_sazon3AC",
    "tb_sazon3BA", "tb_sazon3BB", "tb_sazon3BC",
    "tb_sazon3CA", "tb_sazon3CB", "tb_sazon3CC"
]

for tabela in tabelas_fonte:
    conn.execute(f"""
        INSERT INTO tb_sazon3 (sku, qtde_pedida, ano_mes, ordem, media_24meses,
                               media_2meses, indice_sazon)
        SELECT sku, qtde_pedida, ano_mes, ordem, media_24meses,
               media_2meses, indice_sazon
        FROM {tabela}
    """)

# ============================================================
# 2) Criar tb_sazon4 (equivalente ao MySQL)
# ============================================================

conn.execute("DROP TABLE IF EXISTS tb_sazon4")

conn.execute("""
    CREATE TABLE tb_sazon4 AS
    SELECT
        ROW_NUMBER() OVER (ORDER BY sku, ordem) AS id_reg,
        sku,
        qtde_pedida,
        ano_mes,
        ordem,
        media_24meses,
        media_2meses,
        indice_sazon,
        NULL::DECIMAL(10,2) AS qtde_pedida_dessas
    FROM tb_sazon3
    ORDER BY sku, ordem
""")

# ============================================================
# 3) Atualizar qtde_pedida_dessas
# ============================================================

conn.execute("""
    UPDATE tb_sazon4
    SET qtde_pedida_dessas = qtde_pedida / NULLIF(indice_sazon, 0)
""")

print("tb_sazon4 criada e atualizada com sucesso (equivalente ao sp8_sazon4).")

conn.close()
