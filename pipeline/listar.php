<?php
require 'conexao.php';

$sql = "SELECT id, nome, email, criado_em FROM clientes ORDER BY id DESC";
$stmt = $pdo->query($sql);

echo "<h2>Clientes cadastrados</h2>";

foreach ($stmt as $row) {
    echo "ID: {$row['id']} — {$row['nome']} — {$row['email']} — {$row['criado_em']}<br>";
}
?>
