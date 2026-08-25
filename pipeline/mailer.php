<?php
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
        $mail->Password   = 'Vlagoshost1950#';
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port       = 587;

		$mail->CharSet = 'UTF-8';
		$mail->Encoding = 'base64';


        $mail->setFrom('vladimir.lima@mupeconsult.com', 'MUPE Consultoria');
        $mail->addAddress($para);

        $mail->isHTML(true);
        $mail->Subject = $assunto;
        $mail->Body    = $mensagemHTML;

        if (!$mail->send()) {
            echo "<b>Erro ao enviar email:</b> " . $mail->ErrorInfo;
        } else {
            echo "<b>Email enviado com sucesso.</b>";
        }

    } catch (Exception $e) {
        echo "<b>Erro PHPMailer:</b> " . $mail->ErrorInfo;
    }
}
?>
