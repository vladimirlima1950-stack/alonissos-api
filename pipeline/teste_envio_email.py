def run():
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText("Teste de envio de e-mail via Railway.")
    msg["Subject"] = "Teste Railway"
    msg["From"] = "vladimir.lima.1950@gmail.com"
    msg["To"] = "vladimir.lima.mupe.consultoria@gmail.com"

    try:
        with smtplib.SMTP("smtp.seuservidor.com", 587, timeout=20) as server:
            server.starttls()
            server.login("vladimir.lima.mupe.consultoria", "db6531f2c852b38da49885d3bb491bff")
            server.send_message(msg)

        return {"status": "OK", "mensagem": "E-mail enviado com sucesso!"}

    except Exception as e:
        return {"status": "ERRO", "mensagem": str(e)}
