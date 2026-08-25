<?php
setlocale(LC_NUMERIC, 'pt_BR');

require 'c:/xampp/php/vendor/autoload.php';

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\Alignment;
use PhpOffice\PhpSpreadsheet\Style\NumberFormat;

// ============================================================
// RECEBE O CAMINHO DO CLIENTE DO MASTER PIPELINE
// ============================================================
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

// ============================================================
// CONECTA AO DUCKDB VIA PDO ODBC
// ============================================================
$dsn = "odbc:Driver={DuckDB Driver};Database=" . $caminho_duckdb;

try {
    $pdo = new PDO($dsn);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro ao conectar ao DuckDB (" . $caminho_duckdb . "): " . $e->getMessage() . "\n");
}

// ============================================================
// CONSULTA AO BANCO DE DADOS
// ============================================================
$sql = "SELECT classe_de_pedidos, classe_de_custo, qtde_skus, porc_skus, qtde_pedidos, porc_pedidos,
               custo_12meses, porc_custo_12meses, custo_estoque, porc_custo_estoque, giro_do_estoque
        FROM tb_apres2_fim";

$stmt = $pdo->query($sql);

// Cabeçalhos e campos da consulta
$colunas = [
    'frequência de pedidos',
    'importância no faturamento',
    'quantidade de diferentes produtos',
    'porcentagem do produto',
    'quantidade de pedidos em 12 meses',
    'porcentagem de pedidos em 12 meses',
    'custo do produto em 12 meses',
    'porcentagem do custo em 12 meses',
    'custo do estoque',
    'porcentagem do custo do estoque',
    'giro do estoque'
];

$campos = [
    'classe_de_pedidos',
    'classe_de_custo',
    'qtde_skus',
    'porc_skus',
    'qtde_pedidos',
    'porc_pedidos',
    'custo_12meses',
    'porc_custo_12meses',
    'custo_estoque',
    'porc_custo_estoque',
    'giro_do_estoque'
];

// ============================================================
// CRIAÇÃO DA PLANILHA SPREADSHEET
// ============================================================
$spreadsheet = new Spreadsheet();
$sheet = $spreadsheet->getActiveSheet();

// Cabeçalhos
$colIndex = 'A';
foreach ($colunas as $titulo) {
    $cell = $colIndex . '1';
    $sheet->setCellValue($cell, $titulo);
    $colIndex++;
}

// Estilo dos cabeçalhos
$sheet->getStyle('A1:K1')->applyFromArray([
    'alignment' => [
        'horizontal' => Alignment::HORIZONTAL_LEFT,
        'vertical' => Alignment::VERTICAL_CENTER,
        'wrapText' => true
    ],
    'font' => ['bold' => true]
]);

// Largura padrão das colunas
foreach (range('A', 'K') as $col) {
    $sheet->getColumnDimension($col)->setWidth(15);
}

// ============================================================
// PREENCHENDO DADOS DO RESULTADO PDO
// ============================================================
$rowCount = 2;
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $colIndex = 'A';
    foreach ($campos as $campo) {
        $cell = $colIndex . $rowCount;
        $valor = $row[$campo];

        $sheet->setCellValue($cell, is_numeric($valor) ? floatval($valor) : $valor);

        if (is_numeric($valor)) {
            $sheet->getStyle($cell)->getAlignment()->setHorizontal(Alignment::HORIZONTAL_RIGHT);
        }

        if ($campo === 'qtde_skus' || $campo === 'qtde_pedidos') {
            $sheet->getStyle($cell)->getNumberFormat()->setFormatCode('0');
        } elseif (strpos($campo, 'porc') !== false) {
            $sheet->getStyle($cell)->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_PERCENTAGE_00);
        } elseif (is_numeric($valor)) {
            $sheet->getStyle($cell)->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER_COMMA_SEPARATED1);
        }

        $colIndex++;
    }
    $rowCount++;
}

// ============================================================
// SALVA NA PASTA DO CLIENTE E FECHA A CONEXÃO
// ============================================================
$filePath = $pasta_saida . "/tabela_apres2.xlsx";

$writer = new Xlsx($spreadsheet);
$writer->save($filePath);

// Libera os cursores e fecha a conexão PDO ODBC
$stmt = null;
$pdo = null;

// Mensagem final
echo "✅ Planilha gerada com sucesso em: $filePath\n";

?>