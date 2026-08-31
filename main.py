from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}


from fastapi import FastAPI, UploadFile, File, Request
import os
import smtplib
import ssl
import threading
from email.message import EmailMessage

# Importa o pipeline mestre
from pipeline.apato_000_master_pipeline import processar_cliente

# Importa a função run() do teste de e-mail
from pipeline.teste_envio_email import run as teste_email_run

app = FastAPI()

BASE_CLIENTES = "/app/clientes"

# ============================================================
# STATUS DA API
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "API FastAPI funcionando no Railway!",
        "upload": "/upload/{cliente}/{campo}",
        "processar": "/processar/{cliente}?email=EMAIL_DO_CLIENTE",
        "teste_email": "/teste-email"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# TESTE DE ENVIO DE E‑MAIL
# ============================================================

@app.get("/teste-email")
def teste_email():
    return teste_email_run()

# ============================================================
# UPLOAD DE ARQUIVOS CSV
# ============================================================

@app.post("/upload/{cliente}/{campo}")
async def upload_arquivo(cliente: str, campo: str, arquivo: UploadFile = File(...)):
    pasta_cliente = os.path.join(BASE_CLIENTES, cliente)
    pasta_entrada = os.path.join(pasta_cliente, "entrada")

    os.makedirs(pasta_entrada, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_entrada, f"{campo}.csv")

    with open(caminho_arquivo, "wb") as f:
        f.write(await arquivo.read())

    return {
        "status": "OK",
        "mensagem": f"Arquivo {campo}.csv recebido para o cliente {cliente}"
    }

# ============================================================
# FUNÇÃO DE ENVIO DE E‑MAIL (CORRIGIDA PARA MAILTRAP)
# ============================================================

def enviar_email_python(cliente, email_destino, anexos):
    msg = EmailMessage()
    msg["Subject"] = f"Relatórios gerados para o cliente {cliente}"
    msg["From"] = os.getenv("MAIL_FROM")
    msg["To"] = email_destino

    msg.set_content("Relatórios anexados.")
    msg.add_alternative(f"""
        <h2>Relatórios Gerados com Sucesso</h2>
        <p>Olá,</p>
        <p>Os relatórios do cliente <strong>{cliente}</strong> foram processados com sucesso.</p>
        <p>As planilhas estão anexadas a este e‑mail.</p>
        <p>Atenciosamente,<br>MUPE Consultoria</p>
    """, subtype="html")

    for arquivo in anexos:
        try:
            with open(arquivo, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="octet-stream",
                    filename=os.path.basename(arquivo)
                )
        except Exception as e:
            print(f"ERRO ao anexar {arquivo}: {e}")

    contexto = ssl.create_default_context()

    try:
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT"))
        smtp_user = os.getenv("MAIL_USERNAME")
        smtp_pass = os.getenv("MAIL_PASSWORD")

        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls(context=contexto)
            smtp.login(smtp_user, smtp_pass)

            smtp.send_message(msg)
            print("EMAIL OK — mensagem enviada com sucesso")

    except Exception as e:
        print(f"ERRO ao enviar e‑mail: {e}")

# ============================================================
# PROCESSAMENTO COMPLETO EM BACKGROUND
# ============================================================

@app.post("/processar/{cliente}")
def processar(request: Request, cliente: str):

    email_cliente = request.query_params.get("email")

    if not email_cliente:
        return {
            "status": "ERRO",
            "mensagem": "E-mail do cliente não foi enviado pelo HostGator."
        }

    pasta_cliente = os.path.join(BASE_CLIENTES, cliente)

    pasta_entrada = os.path.join(pasta_cliente, "entrada")
    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    pasta_saida = os.path.join(pasta_cliente, "saida")
    pasta_logs = os.path.join(pasta_cliente, "logs")

    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_processamento, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)
    os.makedirs(pasta_logs, exist_ok=True)

    def tarefa_background():
        try:
            print("PROCESSAMENTO EM BACKGROUND INICIADO")

            processar_cliente(pasta_cliente)

            anexos = [
                f"/app/clientes/{cliente}/saida/tabela_apres2.xlsx",
                f"/app/clientes/{cliente}/saida/tabela_demandas_previsoes.xlsx",
                f"/app/clientes/{cliente}/saida/tabela_estoques_segurança.xlsx",
                f"/app/clientes/{cliente}/saida/tabela_estoques_valores.xlsx",
                f"/app/clientes/{cliente}/saida/tabela_tempo_programa.xlsx"
            ]

            enviar_email_python(cliente, email_cliente, anexos)

            print("PROCESSAMENTO + EMAIL FINALIZADOS")

        except Exception as e:
            print("ERRO NO PROCESSAMENTO EM BACKGROUND:", e)

    threading.Thread(target=tarefa_background).start()

    return {
        "status": "OK",
        "mensagem": "Processamento iniciado. O e-mail será enviado automaticamente ao final."
    }
