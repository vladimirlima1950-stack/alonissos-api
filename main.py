from fastapi import FastAPI, UploadFile, File, Request
import os
import ssl
import subprocess
import requests
import base64

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
# NOVA FUNÇÃO DE ENVIO DE E‑MAIL (RESEND API)
# ============================================================

def enviar_email_resend(cliente, email_destino, anexos):

    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("ERRO: RESEND_API_KEY não encontrada no ambiente Railway.")
        return

    html_body = f"""
        <h2>Relatórios Gerados com Sucesso</h2>
        <p>Olá,</p>
        <p>Os relatórios do cliente <strong>{cliente}</strong> foram processados com sucesso.</p>
        <p>As planilhas estão anexadas a este e‑mail.</p>
        <p>Atenciosamente,<br>MUPE Consultoria</p>
    """

    lista_anexos = []
    for arquivo in anexos:
        try:
            with open(arquivo, "rb") as f:
                lista_anexos.append({
                    "filename": os.path.basename(arquivo),
                    "content": base64.b64encode(f.read()).decode(),
                    "type": "application/octet-stream"
                })
        except Exception as e:
            print(f"ERRO ao anexar {arquivo}: {e}")

    payload = {
        "from": "MUPE Consultoria <vladimir.lima@mupeconsult.com>",
        "to": [email_destino],
        "subject": f"Relatórios gerados para o cliente {cliente}",
        "html": html_body,
        "attachments": lista_anexos
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        print("RESEND — Status:", r.status_code)
        print("RESEND — Resposta:", r.text)
    except Exception as e:
        print("ERRO ao enviar via Resend:", e)


# ============================================================
# PROCESSAMENTO EM BACKGROUND (SEM TIMEOUT)
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

    # Cria as pastas necessárias
    pasta_entrada = os.path.join(pasta_cliente, "entrada")
    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    pasta_saida = os.path.join(pasta_cliente, "saida")
    pasta_logs = os.path.join(pasta_cliente, "logs")

    os.makedirs(pasta_entrada, exist_ok=True)
    os.makedirs(pasta_processamento, exist_ok=True)
    os.makedirs(pasta_saida, exist_ok=True)
    os.makedirs(pasta_logs, exist_ok=True)

    print("PROCESSAMENTO AGENDADO — rodará em background")

    # ============================================================
    # DISPARA O PROCESSAMENTO EM BACKGROUND
    # ============================================================

    subprocess.Popen([
        "python3",
        "-c",
        f"""
import os
from pipeline.apato_000_master_pipeline import processar_cliente
from main import enviar_email_resend

cliente = '{cliente}'
email_cliente = '{email_cliente}'

pasta_cliente = '/app/clientes/' + cliente

processar_cliente(pasta_cliente)

anexos = [
    f"/app/clientes/{cliente}/saida/tabela_apres1.xlsx",
    f"/app/clientes/{cliente}/saida/tabela_apres2.xlsx",
    f"/app/clientes/{cliente}/saida/tabela_demandas_previsoes.xlsx",
    f"/app/clientes/{cliente}/saida/tabela_estoques_segurança.xlsx",
    f"/app/clientes/{cliente}/saida/tabela_estoques_valores.xlsx",
    f"/app/clientes/{cliente}/saida/tabela_tempo_programa.xlsx"
]

enviar_email_resend(cliente, email_cliente, anexos)
print("PROCESSAMENTO + EMAIL FINALIZADOS")
        """
    ])

    return {
        "status": "OK",
        "mensagem": "Processamento iniciado em background. O e‑mail será enviado automaticamente."
    }
