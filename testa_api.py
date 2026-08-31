import os
import requests

print("Testando API HTTP do Mailtrap...")

API_TOKEN = os.getenv("MAILTRAP_TOKEN")

url = "https://send.api.mailtrap.io/api/send"

payload = {
    "from": {
        "email": "teste@mupe.com.br"
    },
    "to": [
        {
            "email": "teste@mupe.com.br"
        }
    ],
    "subject": "Teste API Mailtrap",
    "text": "Este é um teste via API HTTP."
}

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

try:
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Status:", r.status_code)
    print("Resposta:", r.text)
except Exception as e:
    print("Erro ao chamar API:", e)
