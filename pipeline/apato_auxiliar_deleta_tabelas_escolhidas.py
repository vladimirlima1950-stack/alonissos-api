# apato_000_deleta_tabelas_escolhidas



import duckdb

# Caminho completo do banco DuckDB
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'

# Conecta ao banco
conn = duckdb.connect(caminho_banco)

# Exclui a tabela desejada
conn.execute("DROP TABLE IF EXISTS clientes_usos")

print("Tabela 'tb_sk_status' excluída com sucesso!")