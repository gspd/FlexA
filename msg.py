#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Provê funções para comunicação entre as partes do sistema"""

# Compatibility between python2 and python3
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

class Erros:
    EDESC = 0x0001

    strerro_dict = {EDESC: "Tipo de mensagem desconhecida."}

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
    dados -- dicionário contendo os dados a serem enviados na mensagem. Os dados
    serão convertidos da maneira corretas para uso no sistema.

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

