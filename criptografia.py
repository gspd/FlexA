import os, struct
from Crypto.Cipher import AES
from Crypto import Random

""" Código adaptado de: http://goo.gl/jJuYe8

"""

__author__ = "Thiago Kenji Okada"

def encriptar(chave, arquivo_entrada, arquivo_saida=None,
		tam_porcao=64*1024):
    """Encripta o arquivo usando o AES (modo CBC) com determinada chave.

    Parâmetros de entrada:
    chave -- A chave de encriptação - uma string que deve ter 16, 24 ou 32
    bytes. Chaves longas são mais seguras

    arquivo_entrada -- Caminho para o arquivo que será encriptado

    arquivo_saida -- Caso não seja fornecido, '<arquivo_entrada>.enc' será
    usado.

    tam_porcao -- seta o tamanho da porção que a função usa para ler e
    encriptar o arquivo. Porções maiores podem ser mais rápidas.
    tam_porcao tem que ser divisível por 16.
    """
    if not arquivo_saida:
        arquivo_saida = arquivo_entrada + '.enc'

    iv = Random.new().read(AES.block_size)
    cipher = AES.new(chave, AES.MODE_CBC, iv)
    tam_arquivo = os.path.getsize(arquivo_entrada)

    with open(arquivo_entrada, 'rb') as infile:
        with open(arquivo_saida, 'wb') as outfile:
            outfile.write(struct.pack('<Q', tam_arquivo))
            outfile.write(iv)

            while True:
                porcao = infile.read(tam_porcao)
                if len(porcao) == 0:
                    break
                elif len(porcao) % 16 != 0:
                    porcao += b' ' * (16 - len(porcao) % 16)

                outfile.write(cipher.encrypt(porcao))

def decriptar(chave, arquivo_entrada, arquivo_saida=None,
		tam_porcao=24*1024):
    """ Decrypts a file using AES (CBC mode) with the
        given chave. Parameters are similar to encrypt_file,
        with one difference: arquivo_saida, if not supplied
        will be arquivo_entrada without its last extension
        (i.e. if arquivo_entrada is 'aaa.zip.enc' then
        arquivo_saida will be 'aaa.zip')
    """
    if not arquivo_saida:
        arquivo_saida = os.path.splitext(arquivo_entrada)[0]

    with open(arquivo_entrada, 'rb') as infile:
        tam_orig = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        cipher = AES.new(chave, AES.MODE_CBC, iv)

        with open(arquivo_saida, 'wb') as outfile:
            while True:
                porcao = infile.read(tam_porcao)
                if len(porcao) == 0:
                    break
                outfile.write(cipher.decrypt(porcao))

            outfile.truncate(tam_orig)
