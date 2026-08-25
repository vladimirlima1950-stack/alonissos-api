<?php
$DATABASE_URL = "postgresql://postgres:UnqnPTPiLGqgpJsEZNYvlvePsytgFtyb@altaria.proxy.rlwy.net:53642/railway";

$db = parse_url($DATABASE_URL);

$host = $db['host'];
$port = $db['port'];
$user = $db['user'];
$pass = $db['pass'];
$name = ltrim($db['path'], '/');

try {
    $pdo = new PDO("pgsql:host=$host;port=$port;dbname=$name", $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
    ]);

    echo "Conexão OK — HostGator está acessando o Railway!";
} catch (PDOException $e) {
    echo "Erro ao conectar: " . $e->getMessage();
}
?>
