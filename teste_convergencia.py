#!/bin/python3

import subprocess

min_iter=15
iter=0
soma_tempos = 0
variacao_tolerada = 0.01
variacao = 1

arquivo_saida = "resultado.txt"
lista_arquivos = ["1MB", "10MB", "100MB", "300MB", "1GB" ]


file = open(arquivo_saida, "w")

for arquivo in lista_arquivos:

    while(iter<min_iter):
        iter += 1
        tempo = float(subprocess.check_output("~/git/flexa-ng/flexa.py -p {}".format(arquivo), shell=True))
        soma_tempos +=tempo
        print ("tempo atual", tempo)
    
    
    while(variacao > variacao_tolerada):
        
        media_aux = soma_tempos/iter
        
        iter += 1
        tempo = float(subprocess.check_output("~/git/flexa-ng/flexa.py -p 1MB", shell=True))
        soma_tempos +=tempo
        print ("tempo atual", tempo)
        media_atual = soma_tempos/iter
        
        variacao =  abs( (media_atual/media_aux) -1 )
        print("Iteração: ", iter, "Variação: ", variacao )

    file.write("Arquivo: {} tempo: {} Iterações: {}\n".format(soma_tempos/iter, arquivo, iter))
    iter=0
    variacao=1

file.close()

