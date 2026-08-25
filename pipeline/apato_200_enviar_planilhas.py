# enviar_planilhas.py


import os
import glob
import smtplib
import pandas as pd
import unicodedata
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime

BASE_CLIENTES = "D:/AAAAAA_processamentos/clientes"
PLANILHA_REL = "D:/AAAAAA_processamentos/relacionamentos/relacionamentos.xlsx"

REMETENTE = "vladimir.lima.mupe.consultoria@gmail.com"
SENHA = "teyk klrf oaqa fnzl"  # senha de app do Gmail

# ---------------------------------------------------------
# NORMALIZAÇÃO DE NOMES DE ARQUIVOS (remove acentos)
# ---------------------------------------------------------
def normalizar_nome_arquivo(nome):
    nome_sem_acentos = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
    nome_final = nome_sem_acentos.replace(" ", "_")
    return nome_final

# ---------------------------------------------------------
# REGISTRO DE LOGS NA PASTA logs/
# ---------------------------------------------------------
def registrar_log(pasta_cliente, texto):
    pasta_logs = f"{pasta_cliente}/logs"
    if not os.path.exists(pasta_logs):
        os.makedirs(pasta_logs)

    caminho_log = f"{pasta_logs}/python_log.txt"
    with open(caminho_log, "a") as log:
        log.write(f"{datetime.now()} - {texto}\n")

# ---------------------------------------------------------
# ENVIO DE EMAIL
# ---------------------------------------------------------
def enviar_email(destinatario, mensagem, arquivos, pasta_cliente):
    msg = MIMEMultipart()
    msg["From"] = REMETENTE
    msg["To"] = destinatario
    msg["Subject"] = "Planilhas atualizadas"
    msg.attach(MIMEText(mensagem, "plain"))

    for arquivo in arquivos:
        nome_original = os.path.basename(arquivo)
        nome_normalizado = normalizar_nome_arquivo(nome_original)

        with open(arquivo, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={nome_normalizado}")
            msg.attach(parte)

        registrar_log(pasta_cliente, f"arquivo '{nome_original}' enviado como '{nome_normalizado}'")

    servidor = smtplib.SMTP("smtp.gmail.com", 587)
    servidor.starttls()
    servidor.login(REMETENTE, SENHA)
    servidor.send_message(msg)
    servidor.quit()

# ---------------------------------------------------------
# PROCESSAMENTO DOS CLIENTES
# ---------------------------------------------------------
def processar_clientes():
    rel = pd.read_excel(PLANILHA_REL)

    clientes = dict(zip(rel["cliente"], rel["e-mail do contato"]))
    contatos = dict(zip(rel["cliente"], rel["contato na empresa"]))

    for codigo_cliente in clientes:
        nome_pasta = f"cliente_{codigo_cliente}"
        pasta_cliente = f"{BASE_CLIENTES}/{nome_pasta}"
        pasta_saida = f"{pasta_cliente}/saida"

        if not os.path.exists(pasta_cliente):
            continue

        arquivos_saida = glob.glob(f"{pasta_saida}/*")

        if not arquivos_saida:
            registrar_log(pasta_cliente, "pasta de saída vazia, nenhum envio realizado")
            continue

        email_cliente = clientes[codigo_cliente]
        contato = contatos.get(codigo_cliente, "")
        primeiro_nome = contato.split()[0] if contato else "Olá"

        mensagem = (
            f"Olá, {primeiro_nome}!\n\n"
            "Em resultado do processamento dos seus dados, estamos enviando as planilhas resultantes.\n\n"
            "Caso haja alguma dúvida ou se precisar de qualquer informação adicional, por favor, entre em contato comigo.\n\n"
            "Obrigado!\n\n"
            "Atenciosamente,\n"
            "Vladimir Lima\n"
            "MUPE Consultoria\n"
            "E-mail: vladimir.lima.mupe.consultoria@gmail.com\n"
            "Celular: 19 99783 5054\n"
        )

        enviar_email(email_cliente, mensagem, arquivos_saida, pasta_cliente)

        for arquivo in arquivos_saida:
            os.remove(arquivo)

        registrar_log(pasta_cliente, f"enviado para {email_cliente}")

# ---------------------------------------------------------
# EXECUÇÃO
# ---------------------------------------------------------
processar_clientes()
