<?php
require 'c:/xampp/php/vendor/autoload.php';

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\NumberFormat;
use PhpOffice\PhpSpreadsheet\Style\Alignment;

setlocale(LC_NUMERIC, 'pt_BR');

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
// CONSULTA AO BANCO DUCKDB
// ============================================================
$sql = "SELECT sku, ativo_inativo, class_pedidos, class_custo,
               qtde_pedidos, porc_pedidos, custo_12meses,
               porc_custo_12meses, custo_estoque, porc_custo_estoque,
               giro_estoque_sku, cobertura_semanas_sku
        FROM tb_apres1_fim";

$stmt = $pdo->query($sql);

// ============================================================
// INICIA PLANILHA SPREADSHEET
// ============================================================
$spreadsheet = new Spreadsheet();
$sheet = $spreadsheet->getActiveSheet();

// Cabeçalhos
$headers = [
    'sku número', 'ativo_inativo', 'frequência de pedidos', 'importância no faturamento',
    'quantidade de pedidos em 12 meses', 'porcentagem de pedidos em 12 meses',
    'custo do produto em 12 meses', 'porcentagem do custo em 12 meses',
    'custo do estoque', 'porcentagem do custo do estoque',
    'giro do estoque', 'cobertura em semanas'
];

$sheet->fromArray($headers, null, 'A1');

// Estilo de cabeçalho
$sheet->getStyle('A1:L1')->applyFromArray([
    'font' => ['bold' => true],
    'alignment' => ['horizontal' => Alignment::HORIZONTAL_CENTER]
]);

// Largura das colunas
foreach (range('A', 'L') as $col) {
    $sheet->getColumnDimension($col)->setWidth(20);
}

// ============================================================
// COLETA DADOS DO RESULTADO PDO
// ============================================================
$data = [];
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $data[] = [
        $row['sku'],
        $row['ativo_inativo'],
        $row['class_pedidos'],
        $row['class_custo'],
        (int)$row['qtde_pedidos'],
        (float)$row['porc_pedidos'],
        (float)$row['custo_12meses'],
        (float)$row['porc_custo_12meses'],
        (float)$row['custo_estoque'],
        (float)$row['porc_custo_estoque'],
        (float)$row['giro_estoque_sku'],
        (float)$row['cobertura_semanas_sku']
    ];
}

// Insere os dados
$sheet->fromArray($data, null, 'A2');

// Número total de linhas
$totalLinhas = count($data) + 1;

// Formatações
if ($totalLinhas > 1) {
    $sheet->getStyle("E2:E$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER);
    $sheet->getStyle("F2:F$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_PERCENTAGE_00);
    $sheet->getStyle("G2:G$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER_COMMA_SEPARATED1);
    $sheet->getStyle("H2:H$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_PERCENTAGE_00);
    $sheet->getStyle("I2:I$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER_COMMA_SEPARATED1);
    $sheet->getStyle("J2:J$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_PERCENTAGE_00);
    $sheet->getStyle("K2:K$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER_COMMA_SEPARATED1);
    $sheet->getStyle("L2:L$totalLinhas")->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER_COMMA_SEPARATED1);
}

// ============================================================
// SALVA NA PASTA DO CLIENTE E FECHA A CONEXÃO
// ============================================================
$filePath = $pasta_saida . "/tabela_apres1.xlsx";
$writer = new Xlsx($spreadsheet);
$writer->save($filePath);

// Libera os cursores e fecha a conexão PDO ODBC
$stmt = null;
$pdo = null;

echo "✅ Planilha gerada com sucesso em: " . $filePath . "\n";
?>