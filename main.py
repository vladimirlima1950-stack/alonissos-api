from fastapi import FastAPI, UploadFile, File
import os

app = FastAPI()

BASE_CLIENTES = "/app/clientes"

@app.get("/")
def root():
    return {"status": "online", "message": "API FastAPI funcionando no Railway!"}

@app.post("/upload/{cliente}/{campo}")
async def upload_arquivo(cliente: str, campo: str, arquivo: UploadFile = File(...)):
    pasta_cliente = os.path.join(BASE_CLIENTES, cliente)
    pasta_entrada = os.path.join(pasta_cliente, "entrada")

    os.makedirs(pasta_entrada, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_entrada, f"{campo}.csv")

    with open(caminho_arquivo, "wb") as f:
        f.write(await arquivo.read())

    return {"status": "OK", "mensagem": f"Arquivo {campo} recebido para o cliente {cliente}"}
