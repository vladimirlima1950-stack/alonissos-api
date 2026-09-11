# pipeline/apato_envia_plan_mrp.py
# Envia a planilha MRP (mrp.xlsx) para o e-mail do cliente usando Resend.

import os
import duckdb
from datetime import datetime
import resend

def run(pasta_cliente):

    pasta_processamento = os.path.join(pasta_cliente, "processamento")
    caminho_arquivo = os.path.join(pasta_processamento, "mrp.xlsx")

    # ============================================================
    # Verificar se o arquivo existe
    # ============================================================

    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo MRP não encontrado: {caminho_arquivo}")
        return

    # ============================================================
    # Ler e-mail do cliente
    # ============================================================

    caminho_email = os.path.join(pasta_cliente, "email.txt")

    if not os.path.exists(caminho_email):
        print("Arquivo email.txt não encontrado. Não é possível enviar o MRP.")
        return

    with open(caminho_email, "r", encoding="utf-8") as f:
        email_cliente = f.read().strip()

    if email_cliente == "":
        print("email.txt está vazio. Não é possível enviar o MRP.")
        return

    # ============================================================
    # Conectar ao DuckDB para registrar tempo
    # ============================================================

    caminho_duckdb = os.path.join(pasta_processamento, "previsao.duckdb")
    con = duckdb.connect(caminho_duckdb, read_only=False)

    inicio = datetime.now()

    # ============================================================
    # Envio via Resend
    # ============================================================

    try:
        resend.api_key = os.environ.get("RESEND_API_KEY")

        params = {
            "from": "APATO IA <noreply@apato.com.br>",
            "to": [email_cliente],
            "subject": "MRP — Planejamento de Necessidades de Materiais",
            "html": """
                <p>Olá!</p>
                <p>Segue em anexo o arquivo MRP (Planejamento de Necessidades de Materiais).</p>
                <p>Este arquivo contém:</p>
                <ul>
                    <li>MRP Completo</li>
                    <li>Dashboard avançado</li>
                    <li>Custos estimados</li>
                    <li>Dados do SKU</li>
                </ul>
                <p>Atenciosamente,<br>APATO IA</p>
            """,
            "attachments": [
                {
                    "filename": "mrp.xlsx",
                    "path": caminho_arquivo
                }
            ]
        }

        resend.Emails.send(params)

        evento = "OK"
        print(f"MRP enviado com sucesso para: {email_cliente}")

    except Exception as e:
        evento = f"ERRO: {e}"
        print(f"Erro ao enviar MRP: {evento}")

    fim = datetime.now()

    # ============================================================
    # Registrar tempo no DuckDB
    # ============================================================

    con.execute("""
        INSERT INTO tb_tempo_programa VALUES (?, ?, ?, ?)
    """, ["apato_envia_plan_mrp", inicio, fim, evento])

    con.close()
