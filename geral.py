#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções de uso geral para os diversos módulos do Novo FlexA."""

import os
import sys
import re
import string
import subprocess
import sqlite3
import uuid
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
    uuid = ''

    def __init__(self, nome_arquivo=None):
        """Construtor da classe ConfigDat

        Parâmetros de entrada:
        nome_arquivo -- nome/caminho do arquivo de configuração

        """
        if not nome_arquivo:
            self.__nome_arquivo = 'flexa.dat'
        else:
            self.__nome_arquivo = nome_arquivo

        if os.path.exists(self.__nome_arquivo):
            self.carregar()
        else:
            self.gerar_config_padrao()

    def carregar(self):
        """Recarrega o arquivo de configuração"""

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
        # Monta a lista de opcoes para ser salva no arquivo
        opcoes = [('interface', self.interface),
                  ('ip', self.ip),
                  ('porta', self.porta),
                  ('netmask', self.netmask),
                  ('faixa_varredura', self.faixa_varredura),
                  ('local_cache', self.local_cache),
                  ('uuid', self.uuid)]
        # Salva no arquivo
        with open(nome_arquivo, 'w') as arquivo:
            for i in opcoes:
                arquivo.write('{}: {}\n'.format(*i))

    def gerar_config_padrao(self):
        """Gera uma configuração padrão. Usada quando um arquivo de
        configuração não for especificado

        """

        # Por hora gerando um UUID completamente aleatório, depois pode
        # ser interessante usar algo como semente para geração dele
        self.uuid = str(uuid.uuid4())

class BancoDados__prototipo__:

    def __init__(self, nome_arquivo):
        novo_banco = True
        if os.path.exists(nome_arquivo): novo_banco = False

        self.__conn = sqlite3.connect(nome_arquivo)
        self.__db = self.__conn.cursor()

        if novo_banco:
            # TODO: colocando um banco simples aqui, provavelmente vai mudar
            query = ("CREATE TABLE arquivos_sad (hash_unica VARCHAR "
            "PRIMARY KEY, hash_arquivo VARCHAR, nome_arquivo VARCHAR "
            "diretorio VARCHAR, uuid VARCHAR, propridades VARCHAR, id_ver "
            "INTEGER, chunks VARCHAR)")
            self.__db.execute(query)

    def adicionar_arquivo(self, hash_unica, hash_arquivo, nome_arquivo,
            diretorio, uuid, propriedades, id_ver, chunks):
        query = ("INSERT INTO arquivos_sad VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        param = (hash_unica, hash_arquivo, nome_arquivo, diretorio, uuid,
                propriedades, id_ver, chunks)
        self.__db.execute(query, param)
        self.__conn.commit()

    def remover_arquivo(self, hash_arquivo):
        query = ("DELETE FROM arquivos_sad WHERE hash_arquivo = ?")
        param = (hash_unica,)
        self.__db.execute(query, param)
        self.__conn.commit()

    def info_arquivo(self, hash_arquivo):
        query = ("SELECT * from arquivos_sad WHERE hash_arquivo = ?")
        param = (hash_unica,)
        self.__db.execute(query, param)
        return self.__db.fetchone()

    def listar_arquivos(self, uuid):
        query = ("SELECT nome_arquivo from arquivos_sad WHERE uuid = ?")
        param = (uuid,)
        self.__db.execute(query, param)
        return self.__db.fetchall()

    def salvar(self):
        self.__conn.commit()

    def sair(self):
        self.salvar()
        self.__conn.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
