#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções de uso geral para os diversos módulos do Novo FlexA."""

import os
import sys
import re
import string
import subprocess
from threading import Thread

__author__ = "Thiago Kenji Okada"
__copyright__ = "Copyright 2013, Grupo de Sistemas Paralelos e Distribuídos"

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
