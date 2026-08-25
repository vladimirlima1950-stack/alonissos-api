# apato_auxiliar_instruções_mysql.py

import duckdb
import pandas as pd

# Ajustes de exibição para evitar truncamento
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)

# Conectando ao banco
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'
con = duckdb.connect(database=caminho_banco, read_only=False)

# Nome da tabela que você quer visualizar
nome_tabela = 'tb_apres2_fim'

# Consulta segura
try:
    df = con.execute(f"SELECT * FROM {nome_tabela} LIMIT 50").fetchdf()
    print(df.to_string(index=False))
except Exception as e:
    print(f"Erro ao consultar a tabela '{nome_tabela}': {e}")

# Encerra a conexão
con.close()