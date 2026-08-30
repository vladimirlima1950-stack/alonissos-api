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

response = requests.post(url, data=data)

print("STATUS:", response.status_code)
print("RESPOSTA:", response.text)
