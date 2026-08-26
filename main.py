from fastapi import FastAPI, UploadFile, File
import os
import shutil

# Importa o pipeline mestre
from pipeline.apato_000_master_pipeline import processar_cliente

app = FastAPI()

BASE_CLIENTES = "/app/clientes"

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "API FastAPI funcionando no Railway!",
        "upload": "/upload/{cliente}/{campo}",
        "processar": "/processar/{cliente}"
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
# PROCESSAMENTO COMPLETO DO CLIENTE
# ============================================================

@app.post("/processar/{cliente}")
def processar(cliente: str):

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

    # Chama o pipeline mestre
    try:
        processar_cliente(pasta_cliente)
        return {
            "status": "OK",
            "mensagem": f"Processamento concluído para o cliente {cliente}"
        }
    except Exception as e:
        return {
            "status": "ERRO",
            "mensagem": f"Falha ao processar cliente {cliente}: {str(e)}"
        }
