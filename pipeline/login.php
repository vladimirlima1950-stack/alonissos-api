<?php
require 'conexao.php';
require 'mailer.php';

ini_set('display_errors', 1);
error_reporting(E_ALL);

// LOGIN NORMAL
if (isset($_POST['email']) && isset($_POST['senha'])) {

    $sql = "SELECT * FROM clientes WHERE email = :e";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':e' => $_POST['email']]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user && password_verify($_POST['senha'], $user['senha_hash'])) {
        echo "Login OK. Bem-vindo, " . $user['nome'];
        exit;
    } else {
        $erroLogin = "Email ou senha incorretos.";
    }
}

// RECUPERAÇÃO DE SENHA
if (isset($_POST['recuperar_email'])) {

    $email = $_POST['recuperar_email'];

    $sql = "SELECT * FROM clientes WHERE email = :e";
    $stmt = $pdo->prepare($sql);
    $stmt->execute([':e' => $email]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$user) {
        $erroRecuperacao = "Email não encontrado.";
    } else {
        $token = bin2hex(random_bytes(16));

        $sql = "UPDATE clientes SET token_recuperacao = :t WHERE id = :id";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([':t' => $token, ':id' => $user['id']]);

        $link = "https://mupeconsult.com/sistema/redefinir.php?token=" . $token;

        $mensagemHTML = "
            <p>Olá, {$user['nome']}!</p>
            <p>Você solicitou a recuperação de senha.</p>
            <p>Clique no link abaixo para redefinir sua senha:</p>
            <p><a href='$link'>$link</a></p>
            <p>Se você não solicitou isso, ignore este email.</p>
        ";

        enviarEmailTitan($email, "Recuperação de senha", $mensagemHTML);

        $sucessoRecuperacao = "Um link de recuperação foi enviado para seu email.";
    }
}
?>
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>MUPE Consultoria - Acesso ao Sistema</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f3f4f6;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 420px;
            margin: 60px auto;
            background: #ffffff;
            padding: 30px 35px;
            border-radius: 10px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        }
        .logo {
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 20px;
            color: #1f2933;
        }
        h2 {
            margin-top: 0;
            font-size: 18px;
            color: #1f2933;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-size: 13px;
            color: #4b5563;
        }
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 9px 10px;
            margin-bottom: 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        input[type="email"]:focus,
        input[type="password"]:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 1px #2563eb33;
        }
        button {
            width: 100%;
            padding: 10px;
            background: #2563eb;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 5px;
        }
        button:hover {
            background: #1d4ed8;
        }
        .sub-button {
            background: #6b7280;
            margin-top: 8px;
        }
        .sub-button:hover {
            background: #4b5563;
        }
        .section {
            margin-top: 25px;
        }
        .msg-erro {
            background: #fee2e2;
            color: #b91c1c;
            padding: 8px 10px;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .msg-sucesso {
            background: #dcfce7;
            color: #166534;
            padding: 8px 10px;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 15px;
            font-size: 12px;
            color: #9ca3af;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="logo">MUPE Consultoria<br><span style="font-size:12px;color:#6b7280;">Acesso ao Sistema</span></div>

    <?php if (!empty($erroLogin)): ?>
        <div class="msg-erro"><?= $erroLogin; ?></div>
    <?php endif; ?>

    <h2>Login</h2>
    <form method="POST">
        <label for="email">Email</label>
        <input type="email" name="email" id="email" required>

        <label for="senha">Senha</label>
        <input type="password" name="senha" id="senha" required>

        <button type="submit">Entrar</button>
    </form>

    <div class="section">
        <?php if (!empty($erroRecuperacao)): ?>
            <div class="msg-erro"><?= $erroRecuperacao; ?></div>
        <?php endif; ?>

        <?php if (!empty($sucessoRecuperacao)): ?>
            <div class="msg-sucesso"><?= $sucessoRecuperacao; ?></div>
        <?php endif; ?>

        <h2>Esqueci a senha</h2>
        <form method="POST">
            <label for="recuperar_email">Seu email</label>
            <input type="email" name="recuperar_email" id="recuperar_email" required>
            <button type="submit" class="sub-button">Enviar link de recuperação</button>
        </form>
    </div>

    <div class="footer">
        &copy; <?= date('Y'); ?> MUPE Consultoria
    </div>
</div>
</body>
</html>
