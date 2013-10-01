#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções para comunicação entre as partes do sistema"""

import os
import sys
import socket
from threading import Thread, Condition

# Compatibilidade entre o Python 2.x e 3.x
try:
    import SocketServer as socketserver
except ImportError:
    import socketserver

try:
    import cPickle as pickle
except ImportError:
    import pickle

__authors__ = ["Thiago Kenji Okada", "Leandro Moreira Barbosa"]

class Tipos:
    ENVIA_ARQUIVO = 0x0001
    LISTA_ARQUIVOS = 0x0002
    REQUISITA_ARQUIVO = 0x0004
    EXCECAO = 0x0008
    ERRO = 0x0016
    CLOSE = 0x0032

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

    def setup(self):
        if sys.flags.debug:
            print('{}:{} conectado'.format(*self.client_address))

    def handle(self):
        """Função a ser executada para cada requisição"""

        while True:
            try:
                data = decodifica(self.request.recv(1024))
            except EOFError:
                break

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
                elif data[0] == Tipos.CLOSE:
                    break
                else:
                    # Caso o tipo não esteja presente, retorna erro
                    resp_tipo = Tipos.ERRO
                    resp_dados = Erros.EDESC

                resposta = codifica(resp_tipo, resp_dados)
                self.request.sendall(resposta)

    def finish(self):
        if sys.flags.debug:
            print('{}:{} desconectado'.format(*self.client_address))

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
            self.__sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            dest = (ip_destino, porta_destino)
            self.__sock.connect(dest)
        except IOError:
            err = ("Falha ao criar o socket para o IP " +
                   ip_destino +
                   " na porta " + porta_destino)
            sys.exit(err)

    def envia(self, tipo, dados):
        self.__sock.sendall(codifica(tipo, dados))
        try:
            resposta = decodifica(self.__sock.recv(1024))
        except EOFError:
            if sys.flags.debug:
                print('Conexão fechada pelo servidor remoto.')
            return

        if sys.flags.debug:
            print(resposta)

        if resposta[0] == Tipos.ERRO:
            print(Erros.strerro(resposta[1]))

    def close(self):
        self.__sock.close()

class Envia__versao_thread__(Thread):
    """Classe para envio de mensagens entre nós da rede"""

    def __init__ (self, ip_destino=None, porta_destino=5500):
        """Construtor da classe Envia

        Variáveis:
        ip_destino -- IP destino da mensagem
        porta_destino -- porta destino da mensagem

        """

        Thread.__init__(self)
        if not ip_destino:
            ip_destino = socket.gethostname()

        self.__dest = (ip_destino, porta_destino)
        self.__trava = Condition()
        self.__terminar = False
        self.__dados = None
        self.__tipo = None

    def run(self):
        # Inicia a conexão com o servidor
        try:
            self.__sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            self.__sock.connect(self.__dest)
        except IOError:
            err = ("Falha ao criar o socket para o IP " +
                   ip_destino +
                   " na porta " + porta_destino)
            sys.exit(err)

        while True:
            self.__trava.acquire()
            while not self.__dados:
                self.__trava.wait()

            if self.__terminar:
                self.__sock.close()
                break

            self.__sock.sendall(codifica(self.__tipo, self.__dados))
            resposta = decodifica(self.__sock.recv(1024))

            if sys.flags.debug:
                print(resposta)

            if resposta[0] == Tipos.ERRO:
                print(Erros.strerro(resposta[1]))

            self.__tipo = None
            self.__dados = None
            self.__trava.release()

    def envia(self, tipo, dados):
        self.__trava.acquire()

        if self.__terminar:
            if sys.flags.debug:
                print ("Thread desativada")
        if not self.__dados:
            self.__tipo = tipo
            self.__dados = dados
        else:
            if sys.flags.debug:
                print ("Mensagem anterior não enviada")

        self.__trava.notify()
        self.__trava.release()

    def close(self):
        self.__trava.acquire()
        self.__terminar = True
        self.__trava.notify()
        self.__trava.release()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
