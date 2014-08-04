#!/usr/bin/env python3

import os
import binascii
import hashlib
from array import array

from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Util import Counter

import misc

"""Functions to manipulate cryptography on FlexA

"""

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

    # generate 8 random bytes to be used uniquely
    nonce = Random.get_random_bytes(AES.block_size // 2)
    # create counter object
    ctr = Counter.new(AES.block_size * 4, prefix=nonce)
    # create cipher object
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    # number of chunks to be used such that the total size is chunksize
    bytes_left = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            # write the nonce
            outfile.write(nonce)

            while bytes_left > chunksize:
                # read a chunk
                plaintext = infile.read(chunksize)
                # update current chunk count
                bytes_left = bytes_left - chunksize
                # encrypt and write a chunk
                outfile.write(cipher.encrypt(plaintext))
            else:
                # read remaining bytes
                plaintext = infile.read(bytes_left)
                # encrypt and write
                outfile.write(cipher.encrypt(plaintext))

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

    nonce_size = AES.block_size // 2

    # number of chunks to be used such that the total size is chunksize
    bytes_left = (os.path.getsize(in_filename) - nonce_size)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            # read nonce from file
            nonce = infile.read(nonce_size)
            # create counter object
            ctr = Counter.new(AES.block_size * 4, prefix=nonce)
            # create cipher object
            cipher = AES.new(key, AES.MODE_CTR, counter=ctr)

            while bytes_left > chunksize:
                # read a chunk
                ciphertext = infile.read(chunksize)
                # update current chunk count
                bytes_left = bytes_left - chunksize
                # decrypt and write a chunk
                outfile.write(cipher.decrypt(ciphertext))
            else:
                # read remaining bytes
                ciphertext = infile.read(bytes_left)
                # decrypt and write
                outfile.write(cipher.decrypt(ciphertext))

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
        outfile.write(key.exportKey('PEM', passphrase))

    with open(out_filename + '.pub', 'wb') as outfile:
        outfile.write(key.publickey().exportKey('PEM', passphrase))

def open_rsa_key(in_filename, passphrase = None):
    """Open RSA private key and returns a RSA object

    Paramaters:

    out_filename -- name of the output file
    passphrase -- if used, the resulting file is encrypted

    """
    with open(in_filename, 'rb') as infile:
        return RSA.importKey(infile.read(), passphrase)

def generate_verify_key(salt, rsa):
    """generate a Verify Key with SHA512(RSA + Salt)
    """

    verify_key = hashlib.sha512()
    verify_key.update(rsa + salt)

    return verify_key.digest(), verify_key.hexdigest()

def generate_read_key(vk, rsa):
    """generate a Read Key with SHA256(Verify Key)
    """

    read_key = hashlib.sha256()
    read_key.update(vk + rsa)

    return read_key.digest(), read_key.hexdigest()

def generate_write_key(vk, rsa):
    """generate a Write Key with SHA384(Verify Key)
    """

    write_key= hashlib.sha512()
    write_key.update(vk + rsa)

    return write_key.hexdigest()

def generate_salt(length=16):
    """Generate a random salt in hexadecimal format.

    Parameters:

    length -- number of random bytes generated; the resulting hexadecimal is
    twice as long since each byte of data is converted into the corresponding
    2-digit hex representation

    """
    salt = os.urandom(length)
    salt = binascii.hexlify(salt)
    return salt

def keys_string(salt, rsa):
    """Generate keys (verify, write, read, salt) and return your strings
    Parameters:
    salt if exist file or 0 if doesn't
    rsa is object
    """

    if salt == 0:
        salt = generate_salt()
        salts = salt.decode("ascii")
    else:
        salts = salt
        salt = salt.encode("ascii")

    key_rsa = rsa.exportKey()
    #call generate hashs that return your binary and your string
    vk, vks = generate_verify_key(salt, key_rsa)
    rk, rks = generate_read_key(vk, key_rsa)
    wks = generate_write_key(rk, key_rsa)

    return (vks, rks, wks, salts)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4