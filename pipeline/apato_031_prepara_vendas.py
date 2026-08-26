import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    # Conectando ao banco DuckDB
    con = duckdb.connect(database=caminho_banco, read_only=False)

    # ============================================================
    # 1) tb_vendas_data_anomes
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_vendas_data_anomes")
    con.execute("""
        CREATE TABLE tb_vendas_data_anomes (
            sku VARCHAR(20),
            numero_ordem VARCHAR(20),
            data_desejada DATE,
            qtde_pedida DECIMAL(10,2),
            ano_mes INTEGER
        )
    """)

    con.execute("""
        INSERT INTO tb_vendas_data_anomes (sku, numero_ordem, data_desejada, qtde_pedida)
        SELECT sku, numero_ordem, data_desejada, qtde_pedida
        FROM tb_vendas
    """)

    con.execute("""
        UPDATE tb_vendas_data_anomes
        SET ano_mes = CAST(strftime(data_desejada, '%Y%m') AS INTEGER)
    """)

    # ============================================================
    # 2) tb_date_aux2
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_date_aux2")
    con.execute("""
        CREATE TABLE tb_date_aux2 (
            fase1 DATE,
            fase2 INTEGER
        )
    """)

    con.execute("""
        INSERT INTO tb_date_aux2 (fase1)
        SELECT fase1 FROM tb_date_aux1
    """)

    con.execute("""
        UPDATE tb_date_aux2
        SET fase2 = CAST(strftime(fase1, '%Y%m') AS INTEGER)
    """)

    # ============================================================
    # 3) tb_date_aux3
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_date_aux3")
    con.execute("""
        CREATE TABLE tb_date_aux3 AS
        SELECT fase2
        FROM tb_date_aux2
        GROUP BY fase2
    """)

    # ============================================================
    # 4) tb_pecas_somente
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_pecas_somente")
    con.execute("""
        CREATE TABLE tb_pecas_somente AS
        SELECT sku
        FROM tb_vendas
        GROUP BY sku
    """)

    # ============================================================
    # 5) tb_peca_fase2
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_peca_fase2")
    con.execute("""
        CREATE TABLE tb_peca_fase2 (
            peca VARCHAR(20),
            fase2 INTEGER
        )
    """)

    con.execute("""
        INSERT INTO tb_peca_fase2 (peca, fase2)
        SELECT sku, fase2
        FROM tb_pecas_somente, tb_date_aux3
    """)

    # ============================================================
    # 6) tb_vendas_total1
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_vendas_total1")
    con.execute("""
        CREATE TABLE tb_vendas_total1 AS
        SELECT sku, numero_ordem, qtde_pedida, ano_mes
        FROM tb_vendas_data_anomes
    """)

    con.execute("""
        INSERT INTO tb_vendas_total1 (sku, ano_mes)
        SELECT peca, fase2
        FROM tb_peca_fase2
    """)

    # ============================================================
    # 7) tb_date_aux4
    # ============================================================

    con.execute("DROP TABLE IF EXISTS tb_date_aux4")
    con.execute("""
        CREATE TABLE tb_date_aux4 (
            ordem INTEGER PRIMARY KEY,
            fase3 INTEGER
        )
    """)

    con.execute("""
        INSERT INTO tb_date_aux4 (ordem, fase3)
        SELECT 
            ROW_NUMBER() OVER (ORDER BY fase2) AS ordem,
            fase2
        FROM tb_date_aux3
    """)

    print("sp31_prepara_vendas replicado fielmente em Python.")

    con.close()
