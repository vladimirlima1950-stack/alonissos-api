import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(caminho_banco)

    # ============================================================
    # 1) Intervalo de 12 ordens
    # ============================================================

    limmax = conn.execute("SELECT MAX(ordem) FROM tb_vendas_total2").fetchone()[0]
    limmin = limmax - 11

    # ============================================================
    # 2) Criar tabela final persistente
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_class_valores1")
    conn.execute("""
        CREATE TABLE tb_class_valores1 (
            sku VARCHAR(30),
            qtde_12meses DECIMAL(15,2),
            ordem INT,
            situacao VARCHAR(50),
            custo_unit DECIMAL(15,2),
            valor_ordem DECIMAL(15,2),
            estoque DECIMAL(10,2)
        )
    """)

    # ============================================================
    # 3) Criar tabela temporária de SKUs com grupos de 1000
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_skus_grupo_abc")
    conn.execute("""
        CREATE TABLE tb_skus_grupo_abc AS
        SELECT sku,
               CEIL(ROW_NUMBER() OVER (ORDER BY sku) / 1000.0) AS grupo
        FROM (SELECT DISTINCT sku FROM tb_vendas_total2)
    """)

    resultado = conn.execute("SELECT MAX(grupo) FROM tb_skus_grupo_abc").fetchone()[0]
    total_grupos = int(resultado or 0)

    # ============================================================
    # 4) Criar tabela temporária com grupo
    # ============================================================

    conn.execute("DROP TABLE IF EXISTS tb_vendas_com_grupo2")
    conn.execute("""
        CREATE TABLE tb_vendas_com_grupo2 AS
        SELECT v.*, g.grupo
        FROM tb_vendas_total2 v
        JOIN tb_skus_grupo_abc g ON v.sku = g.sku
    """)

    # ============================================================
    # 5) Loop por grupo
    # ============================================================

    for grupo_atual in range(1, total_grupos + 1):

        conn.execute("""
            INSERT INTO tb_class_valores1 (sku, qtde_12meses, ordem, situacao, custo_unit, valor_ordem, estoque)
            SELECT 
                v.sku,
                SUM(v.qtde_pedida) AS qtde_12meses,
                v.ordem,
                COALESCE(MAX(s.situacao), 'ATIVO') AS situacao,
                COALESCE(MAX(c.custo_unit), 0) AS custo_unit,
                SUM(v.qtde_pedida) * COALESCE(MAX(c.custo_unit), 0) AS valor_ordem,
                COALESCE(MAX(e.qtde_orig), 0) AS estoque
            FROM tb_vendas_com_grupo2 v
            LEFT JOIN tb_sku_status s ON v.sku = s.sku
            LEFT JOIN tb_custos c ON v.sku = c.sku
            LEFT JOIN tb_estoques e ON v.sku = e.sku
            WHERE v.grupo = ? AND v.ordem BETWEEN ? AND ?
            GROUP BY v.sku, v.ordem
            HAVING qtde_12meses > 0 OR MAX(e.qtde_orig) > 0
        """, [grupo_atual, limmin, limmax])

    print("tb_class_valores1 criada com sucesso, totalmente equivalente ao MySQL.")

    conn.close()
