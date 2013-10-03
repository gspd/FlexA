#!/usr/bin/env python3

import os, struct
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto import Random

"""Functions to manipulate files on FlexA

"""

__author__ = "Thiago Kenji Okada"

def encrypt_file(key, in_filename, out_filename=None, chunksize=64*1024):
    """Encrypts a file using AES (CBC mode) with the given key.

    Parameters:

    key -- the encryption key - a string that must be either 16, 24 or 32
    bytes long. Longer keys are more secure.

    in_filename -- name of the input file

    out_filename -- if None, '<in_filename>.enc' will be used.

    chunksize -- sets the size of the chunk which the function uses to read
    and encrypt the file. Larger chunk sizes can be faster for some files
    and machines.
    chunksize must be divisible by 16.

    Based on: http://goo.gl/jJuYe8

    """
    if not out_filename:
        out_filename = in_filename + '.enc'

    iv = Random.new().read(AES.block_size)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    filesize = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(struct.pack('<Q', filesize))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))

def decrypt_file(key, in_filename, out_filename=None, chunksize=24*1024):
    """Decrypts a file using AES (CBC mode) with the given key.

    Parameters:

    key -- the encryption key - a string that must be either 16, 24 or 32
    bytes long. Longer keys are more secure.

    in_filename -- name of the input file

    out_filename -- if None, it will be in_filename without its last
    extension; i.e. if in_filename is 'aaa.zip.enc' then out_filename will
    be 'aaa.zip'.

    chunksize -- sets the size of the chunk which the function uses to read
    and encrypt the file. Larger chunk sizes can be faster for some files
    and machines.
    chunksize must be divisible by 16.

    Based on: http://goo.gl/jJuYe8

    """
    if not out_filename:
        out_filename = os.path.splitext(in_filename)[0]

    with open(in_filename, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(origsize)

def generate_rsa_key(out_filename, passphrase = None, bits = 2048):
    """Generate RSA private and public key

    Paramaters:

    out_filename -- name of the output file; the public key will be named
    <in_filename>.pub
    passphrase -- if used, the resulting file is encrypted
    bits -- number of bits used by RSA

    """

    key = RSA.generate(bits)

    with open(out_filename, 'wb') as outfile:
        infile.write(key.exportKey('PEM', passphrase))

    with open(out_filename + '.pub', 'wb') as outfile:
        infile.write(key.publickey().exportKey('PEM', passphrase))

def open_rsa_key(in_filename, passphrase = None):
    """Open RSA private key and returns a RSA object

    Paramaters:

    out_filename -- name of the output file
    passphrase -- if used, the resulting file is encrypted

    """
    with open(in_filename, 'rb') as infile:
        return RSA.importKey(infile.read(), passphrase)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
