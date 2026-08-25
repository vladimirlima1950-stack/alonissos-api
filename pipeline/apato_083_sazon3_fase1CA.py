# apato_083_sazon3_fase1CA.py




# apato_083_sazon3_fase1CA - versão multi-cliente

import sys
import os
import duckdb
import pandas as pd

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
# 1) Carregar tb_sazon3CA e tb_sazon1BCA
# ============================================================

df_sazon3CA = conn.execute("""
    SELECT * FROM tb_sazon3CA ORDER BY sku, ordem
""").fetchdf()

df_sazon1BCA = conn.execute("""
    SELECT sku FROM tb_sazon1BCA ORDER BY id_reg
""").fetchdf()

# ============================================================
# 2) Calcular média de 2 meses (ordem atual + ordem+12)
# ============================================================

media_updates = []

for sku in df_sazon1BCA['sku']:
    df_sku = df_sazon3CA[df_sazon3CA['sku'] == sku].sort_values('ordem')

    ordens = df_sku['ordem'].tolist()

    for ordem in ordens:
        ordem_mais12 = ordem + 12

        if ordem_mais12 not in ordens:
            continue

        q1 = float(df_sku[df_sku['ordem'] == ordem]['qtde_pedida'].iloc[0])
        q2 = float(df_sku[df_sku['ordem'] == ordem_mais12]['qtde_pedida'].iloc[0])

        media = (q1 + q2) / 2

        media_updates.append((media, sku, ordem))
        media_updates.append((media, sku, ordem_mais12))

# ============================================================
# 3) Aplicar atualizações de media_2meses
# ============================================================

for media, sku, ordem in media_updates:
    conn.execute("""
        UPDATE tb_sazon3CA
        SET media_2meses = ?
        WHERE sku = ? AND ordem = ?
    """, [media, sku, ordem])

# ============================================================
# 4) Correções mínimas
# ============================================================

conn.execute("""
    UPDATE tb_sazon3CA
    SET media_2meses = 0.1
    WHERE media_2meses IS NULL OR media_2meses < 0.1
""")

# ============================================================
# 5) Calcular índice de sazonalidade
# ============================================================

conn.execute("""
    UPDATE tb_sazon3CA
    SET indice_sazon = media_2meses / NULLIF(media_24meses, 0)
""")

conn.execute("""
    UPDATE tb_sazon3CA
    SET indice_sazon = 0.1
    WHERE indice_sazon IS NULL OR indice_sazon < 0.1
""")

print("tb_sazon3CA atualizada com sucesso (equivalente ao sp8_sazon3_fase1CA).")

conn.close()
