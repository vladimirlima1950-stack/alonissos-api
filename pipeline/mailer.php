use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require __DIR__ . '/phpmailer/src/Exception.php';
require __DIR__ . '/phpmailer/src/PHPMailer.php';
require __DIR__ . '/phpmailer/src/SMTP.php';

function enviarEmailTitan($para, $assunto, $mensagemHTML) {

    $mail = new PHPMailer(true);

    try {
        $mail->isSMTP();
        $mail->Host       = 'smtp.titan.email';
        $mail->SMTPAuth   = true;
        $mail->Username   = 'vladimir.lima@mupeconsult.com';
        $mail->Password   = 'Vlagoshost1950#'; // deixamos assim por enquanto
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port       = 587;

        $mail->CharSet = 'UTF-8';
        $mail->Encoding = 'base64';

        // Necessário para Railway
        $mail->SMTPOptions = [
            'ssl' => [
                'verify_peer' => false,
                'verify_peer_name' => false,
                'allow_self_signed' => true
            ]
        ];

        $mail->setFrom('vladimir.lima@mupeconsult.com', 'MUPE Consultoria');
        $mail->addAddress($para);

        // Anexos das planilhas
        $mail->addAttachment('/app/clientes/7/saida/tabela_apres2.xlsx');
        $mail->addAttachment('/app/clientes/7/saida/tabela_demandas_previsoes.xlsx');
        $mail->addAttachment('/app/clientes/7/saida/tabela_estoques_segurança.xlsx');
        $mail->addAttachment('/app/clientes/7/saida/tabela_estoques_valores.xlsx');
        $mail->addAttachment('/app/clientes/7/saida/tabela_tempo_programas.xlsx');

        $mail->isHTML(true);
        $mail->Subject = $assunto;
        $mail->Body    = $mensagemHTML;

        if (!$mail->send()) {
            error_log("Erro ao enviar email: " . $mail->ErrorInfo);
        } else {
            error_log("Email enviado com sucesso para: $para");
        }

    } catch (Exception $e) {
        error_log("Erro PHPMailer: " . $e->getMessage());
    }
}
