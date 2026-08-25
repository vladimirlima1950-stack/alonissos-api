<?php
session_start();
require 'conexao.php';

// Se o cliente já estiver logado, redireciona
if (isset($_SESSION['cliente_id'])) {
    header("Location: area-do-cliente.php");
    exit();
}

$mensagem = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Captura os dados do formulário
    $nome    = trim($_POST['nome']);
    $email   = trim($_POST['email']);
    $empresa = trim($_POST['empresa']);
    $senha   = $_POST['senha'];
    $confirmar = $_POST['confirmar'];

    // Validação básica
    if (empty($nome) || empty($email) || empty($empresa) || empty($senha) || empty($confirmar)) {
        $mensagem = "Por favor, preencha todos os campos.";
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $mensagem = "Email inválido.";
    } elseif ($senha !== $confirmar) {
        $mensagem = "As senhas não coincidem.";
    } else {

        // Verifica se o email já existe
        $sql = "SELECT id FROM clientes WHERE email = :email LIMIT 1";
        $stmt = $pdo->prepare($sql);
        $stmt->execute([':email' => $email]);

        if ($stmt->rowCount() > 0) {
            $mensagem = "Este email já está cadastrado.";
        } else {

            // Cria hash seguro da senha
            $senha_hash = password_hash($senha, PASSWORD_DEFAULT);

            // Insere no banco
            $sql = "INSERT INTO clientes (nome, email, empresa, senha_hash, data_cadastro)
                    VALUES (:n, :e, :emp, :s, NOW())";

            $stmt = $pdo->prepare($sql);

            try {
                $stmt->execute([
                    ':n'   => $nome,
                    ':e'   => $email,
                    ':emp' => $empresa,
                    ':s'   => $senha_hash
                ]);

                $mensagem = "Cadastro realizado com sucesso! Você já pode fazer login.";

            } catch (PDOException $e) {
                $mensagem = "Erro ao cadastrar: " . $e->getMessage();
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Cadastro - MUPE Consultoria</title>
</head>
<body>

<h2>Cadastro de Cliente</h2>

<?php if (!empty($mensagem)) : ?>
    <p><strong><?php echo $mensagem; ?></strong></p>
<?php endif; ?>

<form method="POST" action="cadastro.php">
    <label>Nome:</label><br>
    <input type="text" name="nome"><br><br>

    <label>Email:</label><br>
    <input type="email" name="email"><br><br>

    <label>Empresa:</label><br>
    <input type="text" name="empresa"><br><br>

    <label>Senha:</label><br>
    <input type="password" name="senha"><br><br>

    <label>Confirmar Senha:</label><br>
    <input type="password" name="confirmar"><br><br>

    <button type="submit">Cadastrar</button>
</form>

<p>
    Já possui cadastro?
    <a href="login.php">Fazer Login</a>
</p>

</body>
</html>
