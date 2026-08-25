<?php
require 'c:/xampp/php/vendor/autoload.php';

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\Alignment;
use PhpOffice\PhpSpreadsheet\Style\NumberFormat;

// ---------------------------------------------------------
// RECEBE O CAMINHO COMPLETO DA PASTA DO CLIENTE
// ---------------------------------------------------------
if (!isset($argv[1]) || empty($argv[1])) {
    die("Erro: O caminho da pasta do cliente não foi fornecido como argumento.\n");
}

$pasta_cliente = $argv[1];
$pasta_saida = $pasta_cliente . "/saida";

if (!is_dir($pasta_saida)) {
    mkdir($pasta_saida, 0777, true);
}

// Caminho do DuckDB ajustado para o padrão do Windows (\)
$caminho_duckdb = str_replace('/', '\\', $pasta_cliente . '/processamento/previsao.duckdb');
$filePath = $pasta_saida . "/tabela_tempo_programa.xlsx";
$logPath  = 'C:/xampp/php/logs/php_error_log';

// ---------------------------------------------------------
// CONECTA AO DUCKDB VIA PDO ODBC
// ---------------------------------------------------------
$dsn = "odbc:Driver={DuckDB Driver};Database=" . $caminho_duckdb;

try {
    $pdo = new PDO($dsn);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro ao conectar ao DuckDB (" . $caminho_duckdb . "): " . $e->getMessage() . "\n");
}

// ---------------------------------------------------------
// CONSULTA DIRETA AO DUCKDB
// ---------------------------------------------------------
$sql = "SELECT nome_programa, inicio, fim, evento FROM tb_tempo_programa";
$stmt = $pdo->query($sql);

$data = [];
while ($row = $stmt->fetch(PDO::FETCH_NUM)) {
    $data[] = $row;
}

// ---------------------------------------------------------
// INICIA A PLANILHA SPREADSHEET
// ---------------------------------------------------------
$spreadsheet = new Spreadsheet();
$sheet = $spreadsheet->getActiveSheet();

$cabecalhos = ['nome_programa', 'inicio', 'fim', 'evento'];
$sheet->fromArray($cabecalhos, null, 'A1');

$sheet->getStyle('A1:D1')->applyFromArray([
    'font' => ['bold' => true],
    'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER]
]);

foreach (range('A', 'D') as $col) {
    $sheet->getColumnDimension($col)->setWidth(30);
}

// Insere os dados coletados do PDO
if (!empty($data)) {
    $sheet->fromArray($data, null, 'A2');
}

$totalLinhas = count($data) + 1;

if ($totalLinhas > 1) {
    $sheet->getStyle("B2:B$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_DATE_DATETIME);
    $sheet->getStyle("C2:C$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_DATE_DATETIME);
}

// ---------------------------------------------------------
// SALVA O ARQUIVO EXCEL E FECHA A CONEXÃO
// ---------------------------------------------------------
$writer = new Xlsx($spreadsheet);
$writer->save($filePath);

// Libera cursores e fecha a conexão PDO ODBC
$stmt = null;
$pdo = null;

file_put_contents($logPath, "✅ Planilha DuckDB salva em: $filePath\n", FILE_APPEND);

echo "✅ Planilha de tempos de execução gerada com sucesso em: $filePath\n";
?>