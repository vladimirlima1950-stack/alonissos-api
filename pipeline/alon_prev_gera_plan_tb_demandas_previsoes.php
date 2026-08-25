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
$sql = "SELECT * FROM tb_dmd_fcst_res_fim";
$stmt = $pdo->query($sql);

// Cabeçalhos da planilha
$titulos = [
    'frequência de pedidos', 'importância no faturamento', 'sku número',
    'corr_menos24','corr_menos23','corr_menos22','corr_menos21','corr_menos20','corr_menos19','corr_menos18',
    'corr_menos17','corr_menos16','corr_menos15','corr_menos14','corr_menos13','corr_menos12','corr_menos11',
    'corr_menos10','corr_menos9','corr_menos8','corr_menos7','corr_menos6','corr_menos5','corr_menos4','corr_menos3',
    'corr_menos2','corr_menos1','mês corrente','corr_mais1','corr_mais2','corr_mais3','corr_mais4','corr_mais5',
    'corr_mais6','corr_mais7','corr_mais8','corr_mais9','corr_mais10','corr_mais11'
];

$campos = [
    'class_pedidos','class_valores','sku',
    'corr_menos24','corr_menos23','corr_menos22','corr_menos21','corr_menos20','corr_menos19','corr_menos18',
    'corr_menos17','corr_menos16','corr_menos15','corr_menos14','corr_menos13','corr_menos12','corr_menos11',
    'corr_menos10','corr_menos9','corr_menos8','corr_menos7','corr_menos6','corr_menos5','corr_menos4','corr_menos3',
    'corr_menos2','corr_menos1','corr','corr_mais1','corr_mais2','corr_mais3','corr_mais4','corr_mais5',
    'corr_mais6','corr_mais7','corr_mais8','corr_mais9','corr_mais10','corr_mais11'
];

// ============================================================
// CRIAÇÃO DA PLANILHA SPREADSHEET
// ============================================================
$spreadsheet = new Spreadsheet();
$sheet = $spreadsheet->getActiveSheet();

// Cabeçalhos
$col = 'A';
foreach ($titulos as $titulo) {
    $cell = $col . '1';
    $sheet->setCellValue($cell, $titulo);

    $sheet->getStyle($cell)->applyFromArray([
        'alignment' => [
            'wrapText' => true,
            'horizontal' => Alignment::HORIZONTAL_LEFT,
            'vertical' => Alignment::VERTICAL_CENTER
        ],
        'font' => ['bold' => true]
    ]);

    $sheet->getColumnDimension($col)->setWidth(15);
    $col++;
}

// ============================================================
// LINHAS DE DADOS
// ============================================================
$rowCount = 2;

while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $col = 'A';

    foreach ($campos as $campo) {
        $cell = $col . $rowCount;
        $valor = $row[$campo];

        // Alinhamento
        $alinhamento = ($campo === 'sku') ? Alignment::HORIZONTAL_LEFT : Alignment::HORIZONTAL_CENTER;
        $sheet->getStyle($cell)->getAlignment()->setHorizontal($alinhamento);

        // Valor
        $sheet->setCellValue($cell, is_numeric($valor) ? floatval($valor) : $valor);

        // Formatação numérica
        if (strpos($campo, 'corr') !== false || is_numeric($valor)) {
            $sheet->getStyle($cell)->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER);
        }

        $col++;
    }

    $rowCount++;
}

// ============================================================
// SALVA NA PASTA DO CLIENTE E FECHA A CONEXÃO
// ============================================================
$filePath = $pasta_saida . "/tabela_demandas_previsoes.xlsx";

$writer = new Xlsx($spreadsheet);
$writer->save($filePath);

// Libera cursores e fecha a conexão PDO ODBC
$stmt = null;
$pdo = null;

// Logs
file_put_contents('C:\xampp\php\logs\php_error_log', "Planilha salva em: $filePath\n", FILE_APPEND);
file_put_contents('C:\xampp\php\logs\php_error_log', "Final de alon_prev_gera_plan_tb_demandas_previsoes.php\n", FILE_APPEND);

echo "✅ Planilha gerada com sucesso em: $filePath\n";
?>