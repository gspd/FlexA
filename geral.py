#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import socket
from threading import Thread

class EnviaMensagem(Thread):
    """Classe para envio de mensagens e arquivos entre nós da rede"""

    def __init__ (self, ip_destino, porta_destino, estacao, opcao, *cabecalho):
        """Construtor da classe EnviaMensagem

        Parâmetros de entrada:
        ip_destino -- IP destino da mensagem
        porta_destino -- porta destino da mensagem
        estacao -- tipo de estação destino ('servidor', 'replica', 'cliente')
        opcao -- tipo de operação a ser realizada
        cabecalho (opcional) -- resto do cabeçalho da mensagem; caso seja
        enviado algum arquivo, o nome do mesmo deve ser passado como primeira
        entrada do cabeçalho

        """

        # Inicia a classe thread
        Thread.__init__(self)
        # Criando cabeçalho padrão
        header = '<div>' + str(estacao) + '#' +  str(opcao) + '#'
        # Adicionando o resto do cabeçalho excluindo o último elemento
        for campo in cabecalho[:-1]:
            header = header + campo + '#'
        # Último item da lista não adiciona '#', só o '<div>'
        header = header + cabecalho[-1] + '<div>'
        
        # Se o nome do arquivo for passado ele é o primeiro item do
        # cabeçalho
        try:
            self.nome_arquivo = cabecalho[0]
        except IndexError:
            self.nome_arquivo = None
        
        # Inicializando variáveis da classe
        self.header = header
        self.tamanho_header = str(len(header)).zfill(3)
        try:
            self.ip_destino = str(ip_destino)
            self.porta_destino = int(porta_destino)
        except ValueError:
            sys.exit('Valor de entrada inválida')

    def run(self):
        """Envia a mensagem e o arquivo.
        
        Retorna 0 em caso de sucesso, -1 no caso contrário.
        
        """

        # Cria o socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest = (self.ip_destino, self.porta_destino)
            sock.connect(dest)
        except IOError:
            err = "Falha ao criar o socket para o IP " + self.ip_destino + \
            " na porta " + self.porta_destino
            sys.exit(err)

        # Envia o cabeçalho e seu tamanho
        try:
            sock.send(tamanho_header)
            sock.send(header)
        except:
            err = "Falha ao enviar o cabeçalho da mensagem: " + header
            sys.exit(err)

        # Abre o arquivo caso ele exista
        if self.nome_arquivo is not None:
            try:
                caminho = os.path.abspath(self.nome_arquivo)
                nome = os.path.basename(caminho)
                arquivo = open(caminho).read()
                tamanho_arquivo = len(arquivo)
                # E envia o arquivo
                totalsent = 0
                while(totalsent < tamanho_arquivo):
                    sent = sock.send(arquivo[totalsent:])
                    if sent == 0:
                        err = 'Não conseguiu enviar o arquivo'
                        sys.exit(err)
                    totalsent = totalsent + sent
            # Caso o arquivo não exista, ignora
            except IOError:
                pass

        # Fecha o socket e retorna que tudo deu certo
        sock.close()
        return 0

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
