from fastapi import FastAPI, UploadFile, File, Request
import os
import requests
import json

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
# PROCESSAMENTO COMPLETO + ENVIO DE E‑MAIL (OPÇÃO A)
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
            f"/app/clientes/{cliente}/saida/tabela_estoques_seguranca.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_estoques_valores.xlsx",
            f"/app/clientes/{cliente}/saida/tabela_tempo_programa.xlsx"
        ]

        # Chama o mailer no HostGator
        requests.post(
            "https://mupeconsult.com/sistema/email.php",
            data={
                "cliente": cliente,
                "email": email_cliente,
                "anexos": json.dumps(anexos)
            }
        )

        return {
            "status": "OK",
            "mensagem": f"Processamento concluído e e‑mail enviado para {email_cliente}"
        }

    except Exception as e:
        return {
            "status": "ERRO",
            "mensagem": f"Falha ao processar cliente {cliente}: {str(e)}"
        }
