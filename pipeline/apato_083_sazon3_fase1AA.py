# apato_083_sazon3_fase1AA.py


# apato_083_sazon3_fase1AA - versão multi-cliente

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
# 1) Carregar tb_sazon3AA e tb_sazon1BAA
# ============================================================

df_sazon3AA = conn.execute("""
    SELECT * FROM tb_sazon3AA ORDER BY sku, ordem
""").fetchdf()

df_sazon1BAA = conn.execute("""
    SELECT sku FROM tb_sazon1BAA ORDER BY id_reg
""").fetchdf()

# ============================================================
# 2) Calcular média de 2 meses (ordem atual + ordem+12)
# ============================================================

media_updates = []

for sku in df_sazon1BAA['sku']:
    df_sku = df_sazon3AA[df_sazon3AA['sku'] == sku].sort_values('ordem')

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
        UPDATE tb_sazon3AA
        SET media_2meses = ?
        WHERE sku = ? AND ordem = ?
    """, [media, sku, ordem])

# ============================================================
# 4) Correções mínimas
# ============================================================

conn.execute("""
    UPDATE tb_sazon3AA
    SET media_2meses = 0.1
    WHERE media_2meses IS NULL OR media_2meses < 0.1
""")

# ============================================================
# 5) Calcular índice de sazonalidade
# ============================================================

conn.execute("""
    UPDATE tb_sazon3AA
    SET indice_sazon = media_2meses / NULLIF(media_24meses, 0)
""")

conn.execute("""
    UPDATE tb_sazon3AA
    SET indice_sazon = 0.1
    WHERE indice_sazon IS NULL OR indice_sazon < 0.1
""")

print("tb_sazon3AA atualizada com sucesso (equivalente ao sp8_sazon3_fase1AA).")

conn.close()
