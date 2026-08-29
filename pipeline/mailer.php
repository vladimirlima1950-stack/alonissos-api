use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require __DIR__ . '/phpmailer/src/Exception.php';
require __DIR__ . '/phpmailer/src/PHPMailer.php';
require __DIR__ . '/phpmailer/src/SMTP.php';

function enviarEmailTitan($para, $assunto, $mensagemHTML) {

    // Confirma que a função foi chamada
    error_log("TESTE: enviarEmailTitan() foi chamada para: $para");

    $mail = new PHPMailer(true);

    // DEBUG SMTP — ESSENCIAL PARA DESCOBRIR O PROBLEMA
    $mail->SMTPDebug = 2;
    $mail->Debugoutput = function($str, $level) {
        error_log("SMTP DEBUG: $str");
    };

    try {
        // Configuração SMTP Titan
        $mail->isSMTP();
        $mail->Host       = 'smtp.titan.email';
        $mail->SMTPAuth   = true;
        $mail->Username   = 'vladimir.lima@mupeconsult.com';
        $mail->Password   = 'Vlagoshost1950#'; // manter por enquanto
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port       = 587;

        $mail->CharSet = 'UTF-8';
        $mail->Encoding = 'base64';

        // Necessário para Railway (certificados)
        $mail->SMTPOptions = [
            'ssl' => [
                'verify_peer'       => false,
                'verify_peer_name'  => false,
                'allow_self_signed' => true
            ]
        ];

        // Testar existência dos arquivos antes de anexar
        $arquivos = [
            '/app/clientes/7/saida/tabela_apres2.xlsx',
            '/app/clientes/7/saida/tabela_demandas_previsoes.xlsx',
            '/app/clientes/7/saida/tabela_estoques_segurança.xlsx',
            '/app/clientes/7/saida/tabela_estoques_valores.xlsx',
            '/app/clientes/7/saida/tabela_tempo_programas.xlsx'
        ];

        foreach ($arquivos as $arquivo) {
            if (!file_exists($arquivo)) {
                error_log("ERRO: arquivo não encontrado: $arquivo");
            } else {
                error_log("OK: arquivo encontrado: $arquivo");
            }
        }

        // Remetente e destinatário
        $mail->setFrom('vladimir.lima@mupeconsult.com', 'MUPE Consultoria');
        $mail->addAddress($para);

        // Anexos
        foreach ($arquivos as $arquivo) {
            if (file_exists($arquivo)) {
                $mail->addAttachment($arquivo);
            }
        }

        // Conteúdo do e-mail
        $mail->isHTML(true);
        $mail->Subject = $assunto;
        $mail->Body    = $mensagemHTML;

        // Envio
        if (!$mail->send()) {
            error_log("ERRO AO ENVIAR EMAIL: " . $mail->ErrorInfo);
        } else {
            error_log("EMAIL ENVIADO COM SUCESSO para: $para");
        }

    } catch (Exception $e) {
        error_log("ERRO PHPMailer (Exception): " . $e->getMessage());
    }
}
