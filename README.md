FlexA-ng: A new Flexible and Adaptable Distributed Filesystem
==============================================================

Introduction
----------
FlexA-ng is a from scratch FlexA [1] implementation. A flexible and adaptable
filesystem developed in Grupo de Sistemas Paralelos e Distribuídos (Parallel
and Distributed Systems Group, GSPD) [2] located in UNESP, São José do Rio
Preto, SP, Brazil.

The original FlexA version was written by:

1. Silas Evandro Nachif Fernandes
2. Danilo Costa Marim Segura
3. Matheus Della Croce Oliveira
4. Leandro Moreira Barbosa
5. Lúcio Rodrigo de Carvalho
6. Thiago Kenji Okada

Original FlexA is a distributed filesystem written in Python 2 that runs in
userspace. For more details about the general idea about the system please see
[1] as well as other publications [3].

Unfortunately, the original codebase has become a chaos and continuously
getting worse as time goes by. This is why a major rewrite is ongoing.

Objectives
---------
The main goal of this rewrite is to have an organized and mature codebase thus
making the code understandable as well as making it easy to add funcionality.

Please read and follow PEP 8 [4] and PEP 257 [5] guidelines to write code and
documentation unless otherwise stated.

Requirements
------------
- The officially supported version is the latest version of Python 3.x. The
  code should work on Python 3.2 and forward, but it's not guarantee.

- PyCrypto

- SQLAlchemy and Elixir

[1]: http://www.dcce.ibilce.unesp.br/spd
[2]: http://www.dcce.ibilce.unesp.br/spd/pubs/FlexA_PDPTA.pdf
[3]: http://www.dcce.ibilce.unesp.br/spd/publication.php
[4]: http://www.python.org/dev/peps/pep-0008
[5]: http://www.python.org/dev/peps/pep-0257

