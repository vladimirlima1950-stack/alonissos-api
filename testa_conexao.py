import os
import smtplib

smtp_server = os.getenv("MAIL_SERVER")
smtp_port = int(os.getenv("MAIL_PORT"))

print("Testando conexão com Mailtrap...")

try:
    server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
    print("Conexão estabelecida com sucesso!")
    server.quit()

except Exception as e:
    print("Falha ao conectar:", e)
