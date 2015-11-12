#!/bin/python3

import subprocess
import random
import sys
from time import sleep

arquivo_envio = "resut_envio"
arquivo_receb = "resut_receb"
#lista de todos os arquivos que serão enviados e recebidos
lista_arquivos = ["1MB", "5MB", "10MB", "25MB", "50MB"]
#lista com todas as ações que serão testadas
lista_operacoes = ["-p", "-g"]

soma_tempos_envio = {key: 0 for key in lista_arquivos}
soma_tempos_receb = {key: 0 for key in lista_arquivos}
iter_envio = {key: 0 for key in lista_arquivos}
iter_receb = {key: 0 for key in lista_arquivos}

#envia os arquivos primeira vez para não dar erro de não encontrado
for arquivo in lista_arquivos:
    subprocess.check_output("~/git/flexa-ng/flexa.py -p {}".format(arquivo), shell=True)

print("Começando os testes.")
while(True):
    arquivo = lista_arquivos[ random.randint( 0,len(lista_arquivos)-1 ) ]
    operacao = lista_operacoes[ random.randint( 0,len(lista_operacoes)-1 ) ]

    #abre os arquivos com os resultados e executa o teste
    if(operacao=="-p"):
        nome_arquivo_result = arquivo_envio + arquivo + operacao + ".txt"
    if(operacao=="-g"):
        nome_arquivo_result = arquivo_receb + arquivo + operacao + ".txt"

    print(nome_arquivo_result)
    with open(nome_arquivo_result, "a") as file:
        saida = subprocess.check_output("~/git/flexa-ng/flexa.py {} {}".format(operacao, arquivo), shell=True)
        try:
            tempo=float(saida)
        except:
            print("Crash no sistema, saida: ", saida)
            sys.exit()

        if(operacao=="-p"):
            soma_tempos_envio[arquivo] += tempo
            iter_envio[arquivo] += 1
            file.write( "Tempo: {} Iterações: {} Media Tempo: {}\n".format(tempo, iter_envio[arquivo], soma_tempos_envio[arquivo]/iter_envio[arquivo]) )
        if(operacao=="-g"):
            soma_tempos_envio[arquivo] += tempo
            iter_receb[arquivo] += 1
            file.write( "Tempo: {} Iterações: {} Media Tempo: {}\n".format(tempo, iter_receb[arquivo], soma_tempos_envio[arquivo]/iter_receb[arquivo]) )

    sleep(random.randint(10,30))

