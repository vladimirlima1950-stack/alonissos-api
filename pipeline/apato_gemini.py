import numpy as np
import pandas as pd
import duckdb

# Caminho do seu banco DuckDB
caminho_banco = r'D:\Mupe Consultoria\Projeto AAA - Alonissos\BANCO Previsão\Dominante_Python_DuckDB\previsao.duckdb'

def processar_tendencia_duckdb():
    print("1. Conectando ao DuckDB e consultando os dados...")
    
    # Conexão com o banco DuckDB
    con = duckdb.connect(database=caminho_banco, read_only=False)
    
    try:
        # Consulta SQL para trazer os dados filtrados unindo as duas tabelas
        query_dados = """
            SELECT 
                t2.sku, 
                t2.x_ordem, 
                t2.y_qtde,
                t1.media_x,
                t1.media_y
            FROM tb_A_trend2_temp t2
            INNER JOIN tb_A_trend1_temp t1 ON t2.sku = t1.sku
            WHERE t2.class_abc_pedidos = 'A' AND t2.class_abc_valores = 'B'
        """
        
        # O DuckDB permite exportar o resultado diretamente para um DataFrame Pandas
        df = con.execute(query_dados).df()
        
        if df.empty:
            print("Nenhum dado encontrado para o filtro A/B.")
            return

        print("2. Calculando desvios e somatórios por SKU...")

        # Etapa 4 do MySQL: Cálculos dos produtos dos desvios
        df['prod_x']  = (df['x_ordem'] - df['media_x']) ** 2
        df['prod_y']  = (df['y_qtde']  - df['media_y']) ** 2
        df['prod_xy'] = (df['x_ordem'] - df['media_x']) * df['y_qtde']

        # Etapa 5 & 6: Agrupamento e Somas por SKU
        res = df.groupby('sku').agg(
            media_x=('media_x', 'first'),
            media_y=('media_y', 'first'),
            Soma_Sxx=('prod_x', 'sum'),
            Soma_Syy=('prod_y', 'sum'),
            Soma_Sxy=('prod_xy', 'sum')
        ).reset_index()

        print("3. Executando cálculos da Regressão Linear...")

        # Etapa 7: Cálculos estatísticos finais (Vetorizados com NumPy/Pandas)
        
        # Inclinação (b) e Intercepto (a)
        res['inclina_b']  = res['Soma_Sxy'] / res['Soma_Sxx']
        res['intersec_a'] = res['media_y'] - (res['inclina_b'] * res['media_x'])

        # Erro Padrão da Inclinação (erro_Eb)
        # Fórmula: sqrt( (Syy - b * Sxy) / ((24 - 2) * Sxx) )
        termo_erro = (res['Soma_Syy'] - (res['inclina_b'] * res['Soma_Sxy'])) / (22 * res['Soma_Sxx'])
        
        # Proteção contra valores negativos residuais por precisão de ponto flutuante
        termo_erro = np.maximum(termo_erro, 0)
        res['erro_Eb'] = np.sqrt(termo_erro)

        # Teste t (tcalc)
        res['tcalc'] = np.where(
            res['erro_Eb'] == 0, 
            9999.0, 
            res['inclina_b'] / res['erro_Eb']
        )

        # Classificação final (trend vs notrend)
        condicoes = [
            (res['erro_Eb'] == 0),
            (res['tcalc'] > 2.047) | (res['tcalc'] < -2.047)
        ]
        res['trend_notrend'] = np.select(condicoes, ['trend', 'trend'], default='notrend')

        print("4. Gravando a tabela final no DuckDB...")

        # Cria ou sobrescreve a tabela final diretamente dentro do DuckDB
        con.execute("DROP TABLE IF EXISTS tb_A_trend3_somas_e_medias_fase1_AB")
        
        # O DuckDB consegue registrar e salvar um DataFrame do Pandas diretamente como uma tabela no banco!
        con.register('df_resultado_temp', res)
        con.execute("CREATE TABLE tb_A_trend3_somas_e_medias_fase1_AB AS SELECT * FROM df_resultado_temp")
        
        print("Sucesso! Tabela 'tb_A_trend3_somas_e_medias_fase1_AB' criada com sucesso no DuckDB.")

    finally:
        # Fecha a conexão com o banco para liberar o arquivo .duckdb
        con.close()

if __name__ == "__main__":
    processar_tendencia_duckdb()