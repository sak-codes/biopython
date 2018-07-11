# Copyright 2018 by Ariel Aptekmann.
# All rights reserved.
#
# This file is part of the Biopython distribution and governed by your
# choice of the "Biopython License Agreement" or the "BSD 3-Clause License".
# Please see the LICENSE file that should have been included as part of this
# package.

from __future__ import print_function
from Bio.Alphabet import IUPAC
from Bio import Seq
from Bio import motifs
import math


def read(handle):
    """Parse the text output of the MEME program into a meme.Record object.

    Example:

    >>>from Bio.motifs import minimal
    >>>record = minimal.read(open("test_minimal.meme"))
    >>>for motif in record:
    ...    print(motif.name, motif.evalue)
    ...

    You can access individual motifs in the record by their index or find a motif
    by its name:

    Example:

    >>> from Bio import motifs
    >>> with open("test_minimal.meme") as f:
    ...     record = motifs.parse(f, 'minimal')
    >>> motif = record[0]
    >>> print(motif.name)
    LEXA
    >>> motif = record['LEXA']
    >>> print(motif.name)
    LEXA

    This function wont retrieve instances, as there are none in minimal meme format.
    """
    motif_number = 0
    record = Record()
    __read_version(record, handle)
    __read_alphabet(record, handle)
    __read_background(record, handle)

    while True:
        for line in handle:
            if line.startswith('MOTIF'):
                break
        else:
            return record
        name = line.split()[1]
        motif_number += 1
        length, num_occurrences, evalue = __read_motif_statistics(line, handle)
        counts = __read_lpm(line, handle)
        # {'A': 0.25, 'C': 0.25, 'T': 0.25, 'G': 0.25}
        motif = motifs.Motif(alphabet=record.alphabet, counts=counts)
        motif.background = record.background
        motif.length = length
        motif.num_occurrences = num_occurrences
        motif.evalue = evalue
        motif.name = name
        record.append(motif)
        assert len(record) == motif_number
    return record


class Record(list):
    """Class for holding the results of a minimal MEME run."""

    def __init__(self):
        """Initialize record class values."""
        self.version = ""
        self.datafile = ""
        self.command = ""
        self.alphabet = None
        self.background = {}
        self.sequences = []

    def __getitem__(self, key):
        if isinstance(key, str):
            for motif in self:
                if motif.name == key:
                    return motif
        else:
            return list.__getitem__(self, key)


# Everything below is private

def __read_background(record, handle):
    for line in handle:
        if line.startswith('Background letter frequencies'):
            break
    else:
        raise ValueError("Improper input file. File should contain a line starting background frequencies.")
    try:
        line = next(handle)
    except StopIteration:
        raise ValueError("Unexpected end of stream: Expected to find line starting background frequencies.")
    line = line.strip()
    ls = line.split()
    A, C, G, T = float(ls[1]), float(ls[3]), float(ls[5]), float(ls[7])
    record.background = {'A': A, 'C': C, 'G': G, 'T': T}


def __read_version(record, handle):
    for line in handle:
        if line.startswith('MEME version'):
            break
    else:
        raise ValueError("Improper input file. File should contain a line starting MEME version.")
    line = line.strip()
    ls = line.split()
    record.version = ls[2]


def __read_alphabet(record, handle):
    for line in handle:
        if line.startswith('ALPHABET'):
            break
    else:
        raise ValueError("Unexpected end of stream: Expected to find line starting with 'ALPHABET'")
    if not line.startswith('ALPHABET= '):
        raise ValueError("Line does not start with 'ALPHABET':\n%s" % line)
    line = line.strip().replace('ALPHABET= ', '')
    if line == 'ACGT':
        al = IUPAC.unambiguous_dna
    else:
        al = IUPAC.protein
    record.alphabet = al


def __read_lpm(line, handle):
    counts = [[], [], [], []]
    for line in handle:
        freqs = line.split()
        if len(freqs) != 4:
            break
        counts[0].append(int(float(freqs[0]) * 1000000))
        counts[1].append(int(float(freqs[1]) * 1000000))
        counts[2].append(int(float(freqs[2]) * 1000000))
        counts[3].append(int(float(freqs[3]) * 1000000))
    c = {}
    c['A'] = counts[0]
    c['C'] = counts[1]
    c['G'] = counts[2]
    c['T'] = counts[3]
    return c


def __read_motif_statistics(line, handle):
    # minimal :
    #      letter-probability matrix: alength= 4 w= 19 nsites= 17 E= 4.1e-009
    for line in handle:
        if line.startswith('letter-probability matrix:'):
            break
    num_occurrences = int(line.split("nsites=")[1].split()[0])
    length = int(line.split("w=")[1].split()[0])
    evalue = float(line.split("E=")[1].split()[0])
    return length, num_occurrences, evalue


def __read_motif_name(handle):
    for line in handle:
        if 'sorted by position p-value' in line:
            break
    else:
        raise ValueError('Unexpected end of stream: Failed to find motif name')
    line = line.strip()
    words = line.split()
    name = " ".join(words[0:2])
    return name