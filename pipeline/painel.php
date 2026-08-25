<?php
session_start();

if (!isset($_SESSION['cliente_id'])) {
    die("Acesso negado.");
}

echo "<h1>Bem-vindo, " . $_SESSION['nome'] . "</h1>";
echo "<p>Sua pasta: " . $_SESSION['pasta_base'] . "</p>";
?>
