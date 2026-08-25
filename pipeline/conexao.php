<?php
$host = "localhost";
$db   = "mupeco99_db_mupeclientes";   // nome correto do banco
$user = "mupeco99_lima";       // nome correto do usuário MySQL
$pass = "(Mu1Pe2Con3)";   // senha correta do usuário

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Erro ao conectar: " . $e->getMessage());
}
?>
