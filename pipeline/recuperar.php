<?php
require 'conexao.php';
require 'mailer.php'; // seu arquivo que envia email

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];

    // Verifica se o email existe
    $sql = "SELECT * FROM clientes WHERE email = :e";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':e' => $email]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user) {
        // Gera token
        $token = bin2hex(random_bytes(16));

        // Salva token no banco
        $sql = "UPDATE clientes SET token_recuperacao = :t WHERE email = :e";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([':t' => $token, ':e' => $email]);

        // Link de recuperação
        $link = "https://mupeconsult.com/sistema/redefinir.php?token=" . $token;

        // Envia email
        enviarEmail($email, "Recuperação de senha", 
            "Clique no link para redefinir sua senha: $link");

        echo "Um link de recuperação foi enviado para seu email.";
    } else {
        echo "Email não encontrado.";
    }
}
?>

<form method="POST" action="/sistema/recuperar.php">
    Email cadastrado: <input name="email"><br>
    <button type="submit">Enviar link de recuperação</button>
</form>

