<?php
// Substitua pelo caminho do banco de um dos seus clientes
$caminho_banco = 'D:\AAAAAA_processamentos\clientes\cliente_A\processamento\previsao.duckdb';

// String de Conexão ODBC usando o driver instalado
$dsn = "odbc:Driver={DuckDB Driver};Database=" . $caminho_banco;

try {
    $pdo = new PDO($dsn);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    echo "✅ Conexão via ODBC realizada com sucesso!\n";

    // Consulta de teste
    $stmt = $pdo->query("SELECT * FROM tb_tempo_programa LIMIT 5");
    $registros = $stmt->fetchAll(PDO::FETCH_ASSOC);

    print_r($registros);

} catch (PDOException $e) {
    echo "❌ Erro na conexão: " . $e->getMessage() . "\n";
}