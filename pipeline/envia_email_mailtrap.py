import requests, base64

TOKEN = "db6531f2c852b38da49885d3bb491bff"

arquivo = "/app/clientes/6/saida/tabela_estoques_segurança.xlsx"

with open(arquivo, "rb") as f:
    content = base64.b64encode(f.read()).decode()

payload = {
    "from": {"email": "vladimir.lima@mupeconsult.com"},
    "to": [{"email": "vladimir.lima@mupeconsult.com"}],
    "subject": "Relatório do cliente",
    "html": "<h2>Relatório em anexo</h2>",
    "attachments": [
        {
            "content": content,
            "type": "application/octet-stream",
            "filename": "tabela_estoques_segurança.xlsx"
        }
    ]
}

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

r = requests.post("https://send.api.mailtrap.io/api/send", json=payload, headers=headers)
print(r.status_code, r.text)
