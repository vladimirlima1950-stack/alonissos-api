from fastapi import FastAPI, UploadFile, File
import duckdb
import pandas as pd

app = FastAPI()

@app.get("/")
def root():
    return {"status": "online", "message": "API FastAPI funcionando no Railway!"}

@app.post("/processar")
async def processar_arquivo(arquivo: UploadFile = File(...)):
    df = pd.read_csv(arquivo.file)
    con = duckdb.connect()
    resultado = con.execute("SELECT COUNT(*) AS linhas FROM df").fetchdf()
    return {"linhas": int(resultado.loc[0, "linhas"])}
