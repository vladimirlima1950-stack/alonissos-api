<?php
require 'conexao.php';

ini_set('display_errors', 1);
error_reporting(E_ALL);

echo "DEBUG RECUPERAR<br>";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];

    echo "Email recebido: $email<br>";

    $sql = "SELECT * FROM clientes WHERE email = :e";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':e' => $email]);

    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user) {
        echo "Usuário encontrado:<br>";
        print_r($user);
    } else {
        echo "Nenhum usuário encontrado com esse email.";
    }
} else {
    echo "Nenhum POST recebido.";
}
