<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Redefinir senha - MUPE Consultoria</title>
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
        h2 {
            margin-top: 0;
            font-size: 20px;
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
        input[type="password"] {
            width: 100%;
            padding: 9px 10px;
            margin-bottom: 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
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
        .back-btn {
            background: #6b7280;
            margin-top: 10px;
        }
        .back-btn:hover {
            background: #4b5563;
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
    <h2>Redefinir senha</h2>

    <form method="POST">
        <label for="nova_senha">Nova senha:</label>
        <input type="password" name="nova_senha" id="nova_senha" required>

        <button type="submit">Salvar nova senha</button>
    </form>

    <form action="login.php" method="GET">
        <button class="back-btn">Voltar ao login</button>
    </form>

    <div class="footer">
        &copy; <?= date('Y'); ?> MUPE Consultoria
    </div>
</div>

</body>
</html>
