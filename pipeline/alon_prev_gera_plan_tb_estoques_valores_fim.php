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
    // Força o PDO a converter os nomes das colunas de retorno para minúsculas
    $pdo->setAttribute(PDO::ATTR_CASE, PDO::CASE_LOWER);
} catch (PDOException $e) {
    die("Erro ao conectar ao DuckDB (" . $caminho_duckdb . "): " . $e->getMessage() . "\n");
}

// ============================================================
// CONSULTA AO BANCO (ESTOQUES VALORES)
// ============================================================
$sql = "SELECT class_abc_pedidos, class_abc_valores, sku, qtde, custo_unit, total_valor_sku, porc_valor_estoque FROM tb_estoques_valores_fim";

$stmt = $pdo->query($sql);

// ============================================================
// TÍTULOS E CAMPOS (CHAVES EM MINÚSCULAS)
// ============================================================
$titulos = [
    'frequência de pedidos', 'importância no faturamento', 'sku número',
    'quantidade no estoque', 'custo unitário', 'valor total em estoque', 'porcentagem do valor do estoque'
];

$campos = [
    'class_abc_pedidos', 'class_abc_valores', 'sku',
    'qtde', 'custo_unit', 'total_valor_sku', 'porc_valor_estoque'
];

// ============================================================
// CRIAÇÃO DA PLANILHA
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

    $sheet->getColumnDimension($col)->setWidth(18);
    $col++;
}

// ============================================================
// PREENCHENDO DADOS
// ============================================================
$rowCount = 2;

while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    $col = 'A';

    foreach ($campos as $campo) {
        $cell = $col . $rowCount;
        $valor = $row[$campo] ?? '';

        // Alinhamento
        $alinhamento = ($campo === 'sku') ? Alignment::HORIZONTAL_LEFT : Alignment::HORIZONTAL_CENTER;
        $sheet->getStyle($cell)->getAlignment()->setHorizontal($alinhamento);

        // Valor
        $sheet->setCellValue($cell, is_numeric($valor) ? floatval($valor) : $valor);

        // Formatação numérica específica por campo
        if (is_numeric($valor)) {
            if ($campo === 'qtde') {
                $sheet->getStyle($cell)->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_NUMBER);
            } elseif ($campo === 'custo_unit' || $campo === 'total_valor_sku') {
                $sheet->getStyle($cell)->getNumberFormat()->setFormatCode('#,##0.00');
            } elseif ($campo === 'porc_valor_estoque') {
                $sheet->getStyle($cell)->getNumberFormat()->setFormatCode('0.00%');
            }
        }

        $col++;
    }

    $rowCount++;
}

// ============================================================
// SALVA NA PASTA DO CLIENTE E FECHA A CONEXÃO
// ============================================================
$filePath = $pasta_saida . "/tabela_estoques_valores.xlsx";

$writer = new Xlsx($spreadsheet);
$writer->save($filePath);

// Libera cursores e fecha a conexão PDO ODBC
$stmt = null;
$pdo = null;

// Logs
file_put_contents('C:\xampp\php\logs\php_error_log', "Planilha salva em: $filePath\n", FILE_APPEND);
file_put_contents('C:\xampp\php\logs\php_error_log', "Final de alon_prev_gera_plan_tb_estoques_valores_fim.php\n", FILE_APPEND);

echo "✅ Planilha gerada com sucesso em: $filePath\n";
?>