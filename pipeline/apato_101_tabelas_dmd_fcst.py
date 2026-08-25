# apato_101_tabelas_dmd_fcst — equivalente ao sp11_tabelas_dmd_fcst (MySQL)

import duckdb

CAMINHO_BANCO = r"D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb"

def apato_101_tabelas_dmd_fcst():
    con = duckdb.connect(CAMINHO_BANCO)

    # mes = menor ordem da tb_resumo1
    mes_row = con.execute("SELECT MIN(ordem) AS mes FROM tb_resumo1;").fetchone()
    if mes_row is None or mes_row[0] is None:
        print("Nenhum registro em tb_resumo1 para calcular 'mes'.")
        con.close()
        return
    mes = int(mes_row[0])

    # 24 tabelas de demanda (corr_menosXX)
    for i in range(24, 0, -1):
        nome_tabela = f"tb_corr_menos{i}"
        nome_coluna = f"corr_menos{i}"
        ordem_alvo = mes + (24 - i)
        con.execute(f"DROP TABLE IF EXISTS {nome_tabela};")
        con.execute(f"""
            CREATE TABLE {nome_tabela} AS
            SELECT
                sku,
                qtde_pedida AS {nome_coluna}
            FROM tb_resumo1
            WHERE ordem = {ordem_alvo}
            ORDER BY sku;
        """)

    # tabela de previsao corrente
    con.execute("DROP TABLE IF EXISTS tb_corr;")
    con.execute(f"""
        CREATE TABLE tb_corr AS
        SELECT
            sku,
            previsao AS mes_corrente
        FROM tb_resumo1
        WHERE ordem = {mes}
        ORDER BY sku;
    """)

    # 11 tabelas de previsao futura (corr_maisX)
    for i in range(1, 12):
        nome_tabela = f"tb_corr_mais{i}"
        nome_coluna = f"corr_mais{i}"
        ordem_alvo = mes + i
        con.execute(f"DROP TABLE IF EXISTS {nome_tabela};")
        con.execute(f"""
            CREATE TABLE {nome_tabela} AS
            SELECT
                sku,
                previsao AS {nome_coluna}
            FROM tb_resumo1
            WHERE ordem = {ordem_alvo}
            ORDER BY sku;
        """)

    print("Procedimento apato_101_tabelas_dmd_fcst — equivalente ao sp11_tabelas_dmd_fcst executado com sucesso.")

    con.close()


if __name__ == "__main__":
    apato_101_tabelas_dmd_fcst()
