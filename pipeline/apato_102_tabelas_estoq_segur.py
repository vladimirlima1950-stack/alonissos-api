# apato_102_tabelas_estoq_segur — equivalente ao sp12_tabelas_estoq_segur (MySQL)


# apato_102_tabelas_estoq_segur - versão multi-cliente
# Equivalente ao MySQL sp12_tabelas_estoq_segur

import sys
import os
import duckdb

def apato_102_tabelas_estoq_segur(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_banco = os.path.join(pasta_processamento, "previsao.duckdb")

    con = duckdb.connect(caminho_banco, read_only=False)

    # ============================================================
    # 1) mes = menor ordem da tb_resumo1
    # ============================================================
    mes_row = con.execute("SELECT MIN(ordem) AS mes FROM tb_resumo1;").fetchone()
    if mes_row is None or mes_row[0] is None:
        print("Nenhum registro em tb_resumo1 para calcular 'mes'.")
        con.close()
        return

    mes = int(mes_row[0])

    # ============================================================
    # 2) Criar tabela ES_corr (estoque de segurança do mês corrente)
    # ============================================================
    con.execute("DROP TABLE IF EXISTS tb_ES_corr;")
    con.execute(f"""
        CREATE TABLE tb_ES_corr AS
        SELECT
            sku,
            estoq_segur AS ES_mes_corrente
        FROM tb_resumo1
        WHERE ordem = {mes}
        ORDER BY sku;
    """)

    # ============================================================
    # 3) Criar tabelas ES_corr_mais1 até ES_corr_mais11
    # ============================================================
    for i in range(1, 12):
        nome_tabela = f"tb_ES_corr_mais{i}"
        nome_coluna = f"ES_corr_mais{i}"
        ordem_alvo = mes + i

        con.execute(f"DROP TABLE IF EXISTS {nome_tabela};")
        con.execute(f"""
            CREATE TABLE {nome_tabela} AS
            SELECT
                sku,
                estoq_segur AS {nome_coluna}
            FROM tb_resumo1
            WHERE ordem = {ordem_alvo}
            ORDER BY sku;
        """)

    print("Procedimento apato_102_tabelas_estoq_segur executado com sucesso.")

    con.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do cliente.")
        sys.exit(1)

    pasta_cliente = sys.argv[1]
    apato_102_tabelas_estoq_segur(pasta_cliente)
