# apato_auxiliar_ver_tablelas_duckdb



import duckdb

# Conectando ao banco
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'
con = duckdb.connect(database=caminho_banco, read_only=False)

# Listando todas as tabelas
tabelas = con.execute("SHOW TABLES").fetchdf()
nomes = tabelas['name'].tolist()

# Paginação em blocos de 10
bloco = 10
total = len(nomes)
for i in range(0, total, bloco):
    print(f"\n🔹 Tabelas {i+1} a {min(i+bloco, total)} de {total}:")
    for nome in nomes[i:i+bloco]:
        print(f" - {nome}")
    if i + bloco < total:
        input("Pressione Enter para ver mais...")

        