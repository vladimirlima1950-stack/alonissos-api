<?php
session_start();

if (!isset($_SESSION['logado']) || $_SESSION['logado'] !== true) {
    header("Location: login.php");
    exit;
}

$cliente = $_SESSION['usuario']; // identificação automática
$railway_base = "https://web-production-01e8c.up.railway.app"; // coloque sua URL aqui

function enviarArquivoParaRailway($campo, $cliente, $railway_base) {
    if (!isset($_FILES[$campo]) || $_FILES[$campo]['error'] !== UPLOAD_ERR_OK) {
        return "Arquivo '$campo' não enviado.";
    }

    $arquivo = $_FILES[$campo];

    $curl = curl_init();

    curl_setopt_array($curl, [
        CURLOPT_URL => "$railway_base/upload/$cliente/$campo",
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => [
            "arquivo" => curl_file_create(
                $arquivo['tmp_name'],
                $arquivo['type'],
                $arquivo['name']
            )
        ],
        CURLOPT_RETURNTRANSFER => true
    ]);

    $resposta = curl_exec($curl);
    curl_close($curl);

    return $resposta;
}

$mensagens = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Enviar cada arquivo ao Railway
    $mensagens[] = enviarArquivoParaRailway("custos", $cliente, $railway_base);
    $mensagens[] = enviarArquivoParaRailway("leadtime", $cliente, $railway_base);
    $mensagens[] = enviarArquivoParaRailway("vendas", $cliente, $railway_base);
    $mensagens[] = enviarArquivoParaRailway("status", $cliente, $railway_base);
    $mensagens[] = enviarArquivoParaRailway("estoques", $cliente, $railway_base);

    // Acionar processamento no Railway
    $curl = curl_init();
    curl_setopt_array($curl, [
        CURLOPT_URL => "$railway_base/processar/$cliente",
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true
    ]);
    $processamento = curl_exec($curl);
    curl_close($curl);

    $mensagens[] = $processamento;
}
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Envio de Arquivos - MUPE Consultoria</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    margin: 0;
    padding: 0;
}
.container {
    max-width: 600px;
    margin: 40px auto;
    background: #ffffff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
}
h2 {
    margin-top: 0;
    font-size: 22px;
    color: #1f2933;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 8px;
}
label {
    font-weight: bold;
    margin-top: 15px;
    display: block;
}
input[type="file"] {
    margin-top: 5px;
}
button {
    width: 100%;
    padding: 12px;
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 15px;
    cursor: pointer;
    margin-top: 20px;
}
button:hover {
    background: #1d4ed8;
}
.msg {
    background: #e0f2fe;
    padding: 10px;
    border-radius: 6px;
    margin-top: 15px;
    color: #0369a1;
    font-size: 14px;
}
</style>
</head>
<body>

<div class="container">
    <h2>Envio de Arquivos</h2>
    <p>Cliente identificado: <strong><?= htmlspecialchars($cliente) ?></strong></p>

    <form method="POST" enctype="multipart/form-data">

        <label>Arquivo de Custos (.csv)</label>
        <input type="file" name="custos" required>

        <label>Arquivo de Leadtimes (.csv)</label>
        <input type="file" name="leadtime" required>

        <label>Arquivo de Vendas (.csv)</label>
        <input type="file" name="vendas" required>

        <label>Arquivo de Status (.csv)</label>
        <input type="file" name="status" required>

        <label>Arquivo de Estoques (.csv)</label>
        <input type="file" name="estoques" required>

        <button type="submit">Enviar arquivos e iniciar processamento</button>
    </form>

    <?php if (!empty($mensagens)): ?>
        <div class="msg">
            <?php foreach ($mensagens as $m): ?>
                <p><?= htmlspecialchars($m) ?></p>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>
</div>

</body>
</html>
