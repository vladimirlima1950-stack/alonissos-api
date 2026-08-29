from fastapi import FastAPI, UploadFile, File, Request
import os
import json
import smtplib
import ssl
from email.message import EmailMessage

# Importa o pipeline mestre
from pipeline.apato_000_master_pipeline import processar_cliente

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
        "processar": "/processar/{cliente}?email=EMAIL_DO_CLIENTE"
    }

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
# FUNÇÃO DE ENVIO DE E‑MAIL DIRETO PELO RAILWAY
# ============================================================

def enviar_email_python(cliente, email_destino, anexos):
    msg = EmailMessage()
    msg["Subject"] = f"Relatórios gerados para o cliente {cliente}"
    msg["From"] = "vladimir.lima@mupeconsult.com"
    msg["To"] = email_destino

    msg.set_content("Relatórios anexados.")
    msg.add_alternative(f"""
        <h2>Relatórios Gerados com Sucesso</h2>
        <p>Olá,</p>
        <p>Os relatórios do cliente <strong>{cliente}</strong> foram processados com sucesso.</p>
        <p>As planilhas estão anexadas a este e‑mail.</p>
        <p>Atenciosamente,<br>MUPE Consultoria</p>
    """, subtype="html")

    # Anexos
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
        with smtplib.SMTP("smtp.titan.email", 587) as smtp:
            smtp.starttls(context=contexto)
            smtp.login("vladimir.lima@mupeconsult.com", "Vlagoshost1950#")
            smtp.send_message(msg)
            print(f"E‑mail enviado para {email_destino}")
    except Exception as e:
        print(f"ERRO ao enviar e‑mail: {e}")

# ============================================================
# PROCESSAMENTO COMPLETO + ENVIO DE E‑MAIL DIRETO
# ============================================================

@app.post("/processar/{cliente}")
def processar(request: Request, cliente: str):

    # Captura o e‑mail enviado pelo HostGator
    email_cliente = request.query_params.get("email")

    if not email_cliente:
        return {
            "status": "ERRO",
            "mensagem": "E-mail do cliente não foi enviado pelo HostGator."
        }

    pasta_cliente = os.path.join(BASE_CLIENTES, cliente)

    # Garante estrutura mínima
    pasta_entrada = os.path.join(pasta_cliente, "entrada")
    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    pasta_saida = os.path.join(pasta_cliente, "saida")
    pasta_logs = os.path.join(pasta_cliente, "logs")

    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_processamento, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)
    os.makedirs(pasta_logs, exist_ok=True)

    # Executa o pipeline
    try:
        processar_cliente(pasta_cliente)

        # Caminhos dos anexos gerados pelo pipeline
        anexos = [
            f"/app/clientes/{cliente}/saida/tabela_apres2.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_demandas_previsoes.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_estoques_segurança.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_estoques_valores_fim.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_tempo_programa.xlsx"
        ]

        # Envio direto pelo Railway
        enviar_email_python(cliente, email_cliente, anexos)

        return {
            "status": "OK",
            "mensagem": f"Processamento concluído e e‑mail enviado para {email_cliente}"
        }

    except Exception as e:
        return {
            "status": "ERRO",
            "mensagem": f"Falha ao processar cliente {cliente}: {str(e)}"
        }
