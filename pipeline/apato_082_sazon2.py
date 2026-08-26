import os
import duckdb

def run(pasta_cliente):

    # Pasta de processamento do cliente
    pasta_processamento = os.path.join(pasta_cliente, "processamento")

    # Banco DuckDB do cliente
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")
    conn = duckdb.connect(database=caminho_banco, read_only=False)

    # ============================================================
    # 1. DROP TABLES (18 tabelas)
    # ============================================================

    tabelas_drop = [
        "tb_sazon1BAA", "tb_sazon1BAB", "tb_sazon1BAC",
        "tb_sazon1BACM1", "tb_sazon1BACM2",
        "tb_sazon1BBA", "tb_sazon1BBB", "tb_sazon1BBC",
        "tb_sazon1BBCM1", "tb_sazon1BBCM2",
        "tb_sazon1BCA", "tb_sazon1BCB", "tb_sazon1BCC",
        "tb_sazon3", "tb_sazon3AA", "tb_sazon3AB", "tb_sazon3AC",
        "tb_sazon3BA", "tb_sazon3BB", "tb_sazon3BC",
        "tb_sazon3CA", "tb_sazon3CB", "tb_sazon3CC"
    ]

    for t in tabelas_drop:
        conn.execute(f"DROP TABLE IF EXISTS {t}")

    # ============================================================
    # 2. Criar tb_sazon3 (base)
    # ============================================================

    conn.execute("""
        CREATE TABLE tb_sazon3 (
            id_reg INTEGER,
            sku VARCHAR,
            qtde_pedida DECIMAL(10,2),
            ano_mes INTEGER,
            ordem INTEGER,
            media_24meses DECIMAL(13,2),
            media_2meses DECIMAL(13,2),
            indice_sazon DECIMAL(13,2)
        )
    """)

    # ============================================================
    # 3. Criar tb_sazon3AA…tb_sazon3CC (9 tabelas)
    # ============================================================

    grupos = ["AA","AB","AC","BA","BB","BC","CA","CB","CC"]

    for g in grupos:
        conn.execute(f"CREATE TABLE tb_sazon3{g} AS SELECT * FROM tb_sazon3 WHERE 1=0")

    # ============================================================
    # 4. Inserir dados nas tabelas tb_sazon3AA…tb_sazon3CC
    # ============================================================

    def insere(grupo, ped, val):
        conn.execute(f"""
            INSERT INTO tb_sazon3{grupo} (id_reg, sku, qtde_pedida, ano_mes, ordem, media_24meses, media_2meses, indice_sazon)
            SELECT
                ROW_NUMBER() OVER (ORDER BY sku, ordem),
                sku, qtde_pedida, ano_mes, ordem, media_24meses, media_2meses, indice_sazon
            FROM tb_sazon2
            WHERE class_abc_pedidos = '{ped}' AND class_abc_valores = '{val}'
            ORDER BY sku, ordem
        """)

    insere("AA","A","A")
    insere("AB","A","B")
    insere("AC","A","C")
    insere("BA","B","A")
    insere("BB","B","B")
    insere("BC","B","C")
    insere("CA","C","A")
    insere("CB","C","B")
    insere("CC","C","C")

    # ============================================================
    # 5. Criar tb_sazon1BAA…tb_sazon1BCC (9 tabelas)
    # ============================================================

    def cria_lista(nome, tabela):
        conn.execute(f"""
            CREATE TABLE {nome} AS
            SELECT ROW_NUMBER() OVER (ORDER BY sku) AS id_reg, sku
            FROM (SELECT DISTINCT sku FROM {tabela} ORDER BY sku)
        """)

    cria_lista("tb_sazon1BAA", "tb_sazon3AA")
    cria_lista("tb_sazon1BAB", "tb_sazon3AB")
    cria_lista("tb_sazon1BAC", "tb_sazon3AC")
    cria_lista("tb_sazon1BBA", "tb_sazon3BA")
    cria_lista("tb_sazon1BBB", "tb_sazon3BB")
    cria_lista("tb_sazon1BBC", "tb_sazon3BC")
    cria_lista("tb_sazon1BCA", "tb_sazon3CA")
    cria_lista("tb_sazon1BCB", "tb_sazon3CB")
    cria_lista("tb_sazon1BCC", "tb_sazon3CC")

    # ============================================================
    # 6. Criar BACM1 / BACM2 (divisão metade)
    # ============================================================

    qtpecs = conn.execute("SELECT MAX(id_reg)/2 FROM tb_sazon1BAC").fetchone()[0]

    conn.execute("""
        CREATE TABLE tb_sazon1BACM1 AS
        SELECT * FROM tb_sazon1BAC WHERE id_reg <= ?
    """, [qtpecs])

    conn.execute("""
        CREATE TABLE tb_sazon1BACM2 AS
        SELECT * FROM tb_sazon1BAC WHERE id_reg > ?
    """, [qtpecs])

    # ============================================================
    # 7. Criar BBCM1 / BBCM2 (divisão metade)
    # ============================================================

    qtpecs2 = conn.execute("SELECT MAX(id_reg)/2 FROM tb_sazon1BBC").fetchone()[0]

    conn.execute("""
        CREATE TABLE tb_sazon1BBCM1 AS
        SELECT * FROM tb_sazon1BBC WHERE id_reg <= ?
    """, [qtpecs2])

    conn.execute("""
        CREATE TABLE tb_sazon1BBCM2 AS
        SELECT * FROM tb_sazon1BBC WHERE id_reg > ?
    """, [qtpecs2])

    print("apato_082_sazon2.py executado com sucesso — todas as tabelas criadas conforme MySQL sp8_sazon2.")

    conn.close()
