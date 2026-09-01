import os
import requests


print("Testando API HTTP do Resend...")

API_TOKEN = os.getenv("RESEND_API_KEY")

url = "https://api.resend.com/emails"

payload = {
    "from": "Vladimir de Lima<onboarding@resend.dev>",
    "to": ["vladimir.lima.mupe.consultoria@gmail.com"],
    "subject": "Teste API Resend",
    "html": "<p>Este é um teste via API HTTP.</p>"
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
    print("API_TOKEN:", API_TOKEN)
