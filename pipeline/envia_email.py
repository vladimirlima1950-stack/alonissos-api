import requests
import json

url = "https://mupeconsult.com/sistema/email.php"

data = {
    "cliente": "Cliente Teste",
    "email": "vladimir.lima@mupeconsult.com",
    "anexos": json.dumps([
        "/app/clientes/6/saida/tabela_tempo_programa.xlsx"
    ])
}

headers = {
    "User-Agent": "PythonRequests/2.0"
}

response = requests.post(url, data=data, headers=headers)

print("STATUS:", response.status_code)
print("RESPOSTA:", response.text)
