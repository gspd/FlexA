#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções de uso geral para os diversos módulos do Novo FlexA."""

import os
import sys
import socket
import re
import string
import subprocess
from threading import Thread

__author__ = "Thiago Kenji Okada"
__copyright__ = "Copyright 2013, Grupo de Sistemas Paralelos e Distribuídos"

class EnviaMensagem(Thread):
    """Classe para envio de mensagens e arquivos entre nós da rede"""

    def __init__ (self, ip_destino, porta_destino, estacao, opcao, nome_arquivo,
            *cabecalho):
        """Construtor da classe EnviaMensagem

        Parâmetros de entrada:
        ip_destino -- IP destino da mensagem
        porta_destino -- porta destino da mensagem
        estacao -- tipo de estação destino ('servidor', 'replica', 'cliente')
        opcao -- tipo de operação a ser realizada
        nome_arquivo -- nome/caminho do arquivo a ser transferido, ou False caso
        não tenha arquivo a ser transferido
        cabecalho (opcional) -- resto do cabeçalho da mensagem, um parâmetro
        para cada campo adicional

        """
        # Inicia a classe thread
        Thread.__init__(self)
        # Criando cabeçalho padrão
        header = '<div>' + str(estacao) + '#' +  str(opcao) + '#'

        # Adicionando o resto do cabeçalho excluindo o último elemento
        for campo in cabecalho[:-1]:
            header = header + campo + '#'

        # Último item da lista não adiciona '#', só o '<div>'
        try:
            header = header + cabecalho[-1] + '<div>'
        except IndexError:
            header = header + '<div>'

        # Inicializando variáveis da classe
        self.nome_arquivo = nome_arquivo
        self.header = header
        self.tamanho_header = str(len(header)).zfill(3)
        try:
            self.ip_destino = str(ip_destino)
            self.porta_destino = str(porta_destino)
        except ValueError:
            sys.exit("Valor de entrada inválida")

    def run(self):
        """Envia a mensagem e o arquivo.

        Retorna 0 em caso de sucesso, -1 caso falhe.

        """
        # Cria o socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dest = (self.ip_destino, int(self.porta_destino))
            sock.connect(dest)
        except IOError:
            err = ("Falha ao criar o socket para o IP " + self.ip_destino +
            " na porta " + self.porta_destino)
            sys.exit(err)

        # Envia o cabeçalho e seu tamanho
        try:
            sock.send(self.tamanho_header)
            sock.send(self.header)
        except:
            err = "Falha ao enviar o cabeçalho da mensagem: " + self.header
            sys.exit(err)

        # Abre o arquivo caso ele exista
        if self.nome_arquivo:
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
                        err = "Não conseguiu enviar o arquivo"
                        sys.exit(err)
                    totalsent = totalsent + sent
            # Caso o arquivo não exista, ignora
            except IOError:
                err = "Arquivo " + nome_arquivo + " não encontrado"
                sys.exit(err)

        # Fecha o socket e retorna que tudo deu certo
        sock.close()
        return 0

class Ping(Thread):
    """Classe para envio de pings entre nós da rede

    Variáveis da classe:
    status -- número de pacotes recebidos de volta com sucesso
    minimo -- menor RTT retornado
    media -- média dos RTTs retornados
    maxima -- maior RTT retornado
    jitter -- variação entre os RTTs retornados

    """
    status = None
    minimo = None
    media = None
    maximo = None
    jitter = None

    def __init__(self, host, numero=4):
        """Construtor da classe Ping

        Parâmetros de entrada:
        host -- endereço de IP do host destino do ping
        numero -- número de pings a serem feitos; padrão é 4

        """
        Thread.__init__(self)
        self.host = host
        self.numero = numero

    def run(self):
        """Verifica se o ping retorna resposta. Se não retornar o método é
        encerrado.

        """
        # Por enquanto só funciona no Linux com o ping do iputils, não sei se a
        # gente irá suportar outra plataforma
        if sys.platform == 'linux' or sys.platform == 'linux2':
            lifeline = r'(\d) received'
            ping_regex = r'(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)'

        ping = subprocess.Popen(
            ["ping", "-c", str(self.numero), self.host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        while True:
            try:
                saida, erro = ping.communicate()
            except ValueError:
                break
            # Pega o número de pacotes que foram retornados
            matcher = re.compile(lifeline)
            self.status = re.findall(lifeline, str(saida))
            # Pega as informações geradas pelo ping
            matcher = re.compile(ping_regex)
            self.minimo, self.media, self.maximo, self.jitter = \
            matcher.search(str(saida)).groups()

class ConfigDat:
    """Classe para gerenciar o arquivo de configuração do sistema

    Variáveis da classe:
    interface -- interface de rede da máquina
    ip -- IP da máquina
    netmask -- máscara de rede da máquina
    faixa_varredura -- faixa de varredura de IPs na busca
    local_cache -- diretório de localização da cache
    caminho -- caminho do arquivo de configuração

    """
    interface = ''
    ip = ''
    porta = ''
    netmask = ''
    faixa_varredura = ''
    local_cache = ''
    caminho = ''

    def __init__(self, nome_arquivo=None):
        """Construtor da classe ConfigDat

        Parâmetros de entrada:
        nome_arquivo -- nome/caminho do arquivo de configuração

        """
        if nome_arquivo:
            self.caminho = os.path.abspath(nome_arquivo)
            self.carregar()

    def carregar(self):
        """Recarrega o arquivo de configuração"""
        if os.path.exists(self.caminho):
            # Usa expressão regular para pegar o que a gente quer
            regex = re.compile("\S+:.+$")
            # Abre o arquivo linha por linha
            lista = []
            for campo in open(self.caminho):
                aux = regex.match(campo)
                # Se existir configuração, guarda na lista
                if aux:
                    lista.append(aux.group(0).split(":"))
            # Armazena nas variáveis
            for attr, valor in lista:
                setattr(self, attr.strip(), valor.strip())

    def salvar(self, nome_arquivo=None):
        """Salva o arquivo de configuração

        Parâmetros de entrada:
        nome_arquivo -- salva o arquivo de configuração em outro lugar

        """
        # Se nome_arquivo não for passado, usa o caminho original
        if not nome_arquivo:
            nome_arquivo = self.caminho
        # Monta o texto que será salvo no arquivo
        texto = ('interface: ' + self.interface + '\nip: ' + self.ip +
                '\nporta:' + self.porta + '\nnetmask: ' + self.netmask +
                '\nfaixa_varredura: ' + self.faixa_varredura +
                '\nlocal_cache: ' + self.local_cache)
        # Salva no arquivo
        with open(nome_arquivo, 'w') as arquivo:
            arquivo.write(texto)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
