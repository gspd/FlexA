#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções para comunicação entre as partes do sistema"""

import os
import sys
import socket
import socketserver
from threading import Thread

# Compatibilidade entre o Python 2.x e 3.x
try:
    import cPickle
except ImportError:
    import pickle

__copyright__ = "Copyright 2013, Grupo de Sistemas Paralelos e Distribuídos"

class Tipos:
    ENVIA_ARQUIVO = 0x0001
    LISTA_ARQUIVOS = 0x0002
    REQUISITA_ARQUIVO = 0x0004
    EXCECAO = 0x0008
    ERRO = 0x0016

    strtipos_dict = {ENVIA_ARQUIVO: "Envia um arquivo ao servidor.",
                     LISTA_ARQUIVOS: "Lista arquivos disponíveis.",
                     REQUISITA_ARQUIVO: "Requista download de arquivo.",
                     EXCECAO: "Exceção ocorreu.",
                     ERRO: "Erro ocorreu."}

    def strtipos(tipo):
        try:
            return Tipos.strtipos_dict[tipo]
        except KeyError:
            return "Tipo de mensagem desconhecido."

class Erros:
    EDESC = 0x0001
    NIMPL = 0x0002

    strerro_dict = {EDESC: "Tipo de mensagem desconhecido.",
                    NIMPL: "Requisição não implementada."}

    def strerro(erro):
        try:
            return Erros.strerro_dict[erro]
        except KeyError:
            return "Código de erro desconhecido"

def codifica(tipo, dados):
    """Codifica uma mensagem e retorna um objeto a ser usado diretamente pelo
    socket para enviar uma mensagem.

    Variáveis:
    tipo -- tipo da mensagem a ser enviada. O tipo tem relação ao objetivo da
    mensagem. O tipo da mensagem influencia nos dados que deverão ser fornecidos
    dados -- objeto contendo os dados a serem enviados na mensagem. Os dados
    serão convertidos da maneira corretas para uso no sistema. Pode ser qualquer
    objeto que suporta o módulo Pickle.

    O processo de codificação realizado por essa função é sempre compatível
    com o processo de decodificação fornecido em uma mesma versão do FlexA.
    Desta forma:
    decodifica(codifica(tipo,dados)) == (tipo, dados)

    """

    return pickle.dumps((tipo, dados))

def decodifica(mensagem):
    """Decodifica uma mensagem recebida pelo socket. Retorna uma tupla
    (tipo, dados). Veja função codifica para mais informações.

    Variáveis:
    mensagem -- objeto recebido pelo socket

    O processo de decodificação realizado por essa função é sempre compatível
    com o processo de codificação fornecido em uma mesma versão do FlexA.
    Desta forma:
    codifica(decodifica(msg)) == msg

    """

    return pickle.loads(mensagem)


class RecebeHandler(socketserver.BaseRequestHandler):
    """Classe que executada para cada requisição"""

    def handle(self):
        """Função a ser executada para cada requisição"""

        data = decodifica(self.request.recv(1024))

        if sys.flags.debug:
            print("Dados recebidos: {}".format(data))

        # Primeiro membro da tupla é sempre o tipo de mensagem
        if data[0] == Tipos.ENVIA_ARQUIVO:
            resp_tipo = Tipos.ERRO
            resp_dados = Erros.NIMPL
        elif data[0] == Tipos.LISTA_ARQUIVOS:
            resp_tipo = data[0]
            resp_dados = ",".join(
                [f for f in os.listdir('.') if os.path.isfile(f)])
        elif data[0] == Tipos.REQUISITA_ARQUIVO:
            resp_tipo = Tipos.ERRO
            resp_dados = Erros.NIMPL
        elif data[0] == Tipos.EXCECAO:
            resp_tipo = Tipos.ERRO
            resp_dados = Erros.NIMPL
        elif data[0] == Tipos.ERRO:
            resp_tipo = Tipos.ERRO
            resp_dados = Erros.NIMPL
        else:
            # Caso o tipo não esteja presente, retorna erro
            resp_tipo = Tipos.ERRO
            resp_dados = Erros.EDESC

        resposta = codifica(resp_tipo, resp_dados)
        self.request.sendall(resposta)

class Servidor(socketserver.ThreadingMixIn,
               socketserver.TCPServer):
    """Classe que determinar o tipo do servidor"""
    pass

class Recebe:
    """Classe para recebimento de mensagens e arquivos entre nós da rede

    Variáveis da classe:
    host -- endereço ip ou hostname para escuta
    port_escuta -- porta de escuta para recebimento de conexões

    """

    def __init__(self, host=None, porta_escuta=5500):
        if not host:
            host = socket.gethostname()

        servidor = Servidor((host, porta_escuta),
                            RecebeHandler)
        ip, porta = servidor.server_address
        if sys.flags.debug:
            print("Escutando em {}:{}".format(ip, porta))
        # thread do servidor
        t_servidor = Thread(target=servidor.serve_forever)
        t_servidor.daemon = True
        t_servidor.start()

class Envia:
    """Classe para envio de mensagens entre nós da rede"""

    def __init__ (self, ip_destino=None, porta_destino=5500):
        """Construtor da classe Envia

        Variáveis:
        ip_destino -- IP destino da mensagem
        porta_destino -- porta destino da mensagem

        """

        if not ip_destino:
            ip_destino = socket.gethostname()

        try:
            self.sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            dest = (ip_destino, porta_destino)
            self.sock.connect(dest)
        except IOError:
            err = ("Falha ao criar o socket para o IP " +
                   ip_destino +
                   " na porta " + porta_destino)
            sys.exit(err)

    def envia(self, tipo, dados):
        self.sock.sendall(codifica(tipo, dados))
        resposta = decodifica(self.sock.recv(1024))

        if sys.flags.debug:
            print(resposta)

        if resposta[0] == Tipos.ERRO:
            print(Erros.strerro(resposta[1]))

    def close(self):
        self.sock.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
