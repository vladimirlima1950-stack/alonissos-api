import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Adicionar colunas à tabela tb_vendas_total3
    # ============================================================

    conn.execute("ALTER TABLE tb_vendas_total3 ADD COLUMN class_ABC_pedidos VARCHAR(1)")
    conn.execute("ALTER TABLE tb_vendas_total3 ADD COLUMN class_ABC_valores VARCHAR(1)")
    conn.execute("ALTER TABLE tb_vendas_total3 ADD COLUMN freq INT")

    # ============================================================
    # 2) Atualizar class_ABC_pedidos
    # ============================================================

    conn.execute("""
        UPDATE tb_vendas_total3
        SET class_ABC_pedidos = (
            SELECT class_ABC_pedidos
            FROM tb_class_pedidos2
            WHERE tb_class_pedidos2.sku = tb_vendas_total3.sku
        )
    """)

    # ============================================================
    # 3) Atualizar class_ABC_valores
    # ============================================================

    conn.execute("""
        UPDATE tb_vendas_total3
        SET class_ABC_valores = (
            SELECT class_ABC_valores
            FROM tb_class_valores2
            WHERE tb_class_valores2.sku = tb_vendas_total3.sku
        )
    """)

    # ============================================================
    # 4) Atualizar freq
    # ============================================================

    conn.execute("""
        UPDATE tb_vendas_total3
        SET freq = (
            SELECT freq_tot
            FROM tb_pedidos_freq2
            WHERE tb_pedidos_freq2.sku = tb_vendas_total3.sku
        )
    """)

    # ============================================================
    # 5) Criar tabela tb_sazon1
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon1")
    conn.execute("""
        CREATE TABLE tb_sazon1 AS
        SELECT sku, AVG(qtde_pedida) AS media_24meses
        FROM tb_vendas_total3
        WHERE class_ABC_pedidos IN ('A', 'B', 'C')
        GROUP BY sku
    """)

    # ============================================================
    # 6) Criar tabela tb_sazon2
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_sazon2")
    conn.execute("""
        CREATE TABLE tb_sazon2 AS
        SELECT sku, qtde_pedida, ano_mes, ordem,
               NULL::DECIMAL(13,2) AS media_24meses,
               NULL::DECIMAL(13,2) AS media_2meses,
               NULL::DECIMAL(13,2) AS indice_sazon,
               class_ABC_pedidos,
               class_ABC_valores
        FROM tb_vendas_total3
        WHERE freq > 12
    """)

    # ============================================================
    # 7) Atualizar média de 24 meses
    # ============================================================

    conn.execute("""
        UPDATE tb_sazon2
        SET media_24meses = (
            SELECT media_24meses
            FROM tb_sazon1
            WHERE tb_sazon1.sku = tb_sazon2.sku
        )
    """)

    print("Tabelas tb_sazon1 e tb_sazon2 criadas e atualizadas com sucesso.")

    conn.close()
