<?php
require 'conexao.php';

$email = "vladimir.lima@mupeconsult.com";

$sql = "SELECT * FROM clientes WHERE email = :e";
$stmt = $pdo->prepare($sql);
$stmt->execute([':e' => $email]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

var_dump($user);
