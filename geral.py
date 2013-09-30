#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções de uso geral para os diversos módulos do Novo FlexA."""

import os
import sys
import re
import string
import subprocess
import sqlite3
from threading import Thread

__authors__ = ["Thiago Kenji Okada", "Leandro Moreira Barbosa"]

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
        self.__host = host
        self.__numero = numero

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
            ["ping", "-c", str(self.__numero), self.__host],
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

    def __init__(self, nome_arquivo=None):
        """Construtor da classe ConfigDat

        Parâmetros de entrada:
        nome_arquivo -- nome/caminho do arquivo de configuração

        """
        if nome_arquivo:
            self.__nome_arquivo = nome_arquivo
            self.carregar()

    def carregar(self):
        """Recarrega o arquivo de configuração"""
        if os.path.exists(self.__nome_arquivo):
            # Usa expressão regular para pegar o que a gente quer
            regex = re.compile("\S+:.+$")
            # Abre o arquivo linha por linha
            lista = []
            for campo in open(self.__nome_arquivo):
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
            nome_arquivo = self.__nome_arquivo
        # Monta o texto que será salvo no arquivo
        texto = ('interface: ' + self.interface + '\nip: ' + self.ip +
                '\nporta:' + self.porta + '\nnetmask: ' + self.netmask +
                '\nfaixa_varredura: ' + self.faixa_varredura +
                '\nlocal_cache: ' + self.local_cache)
        # Salva no arquivo
        with open(nome_arquivo, 'w') as arquivo:
            arquivo.write(texto)

class BancoDados__prototipo__:

    def __init__(self, nome_arquivo):
        novo_banco = True
        if os.path.exists(nome_arquivo): novo_banco = False

        self.__conn = sqlite3.connect(nome_arquivo)
        self.__db = self.__conn.cursor()

        if novo_banco:
            # TODO: colocando um banco simples aqui, provavelmente vai mudar
            query = ("CREATE TABLE arquivos_sad (hash_arquivo VARCHAR "
            "PRIMARY KEY, nome_arquivo VARCHAR, diretorio VARCHAR, id_ver "
            "INTEGER)")
            self.__db.execute(query)

    def adicionar_arquivo(self, hash_arquivo, nome_arquivo, diretorio, id_ver):
        query = ("INSERT INTO arquivos_sad VALUES (?, ?, ?, ?)")
        param = (hash_arquivo, nome_arquivo, diretorio, id_ver)
        self.__db.execute(query, param)
        self.__conn.commit()

    def remover_arquivo(self, hash_arquivo):
        query = ("DELETE FROM arquivos_sad WHERE hash_arquivo = ?")
        self.__db.execute(query, (hash_arquivo,))
        self.__conn.commit()

    def info_arquivo(self, hash_arquivo):
        query = ("SELECT * from arquivos_sad WHERE hash_arquivo = ?")
        self.__db.execute(query, (hash_arquivo,))
        return self.__db.fetchone()

    def sair(self):
        self.__conn.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
