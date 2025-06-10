#!/usr/bin/env python3
"""
Hamming (31, 26) – 1 erro corrigido, 2 erros detectados.

Uso:
    python hamming3126.py encode meu_arquivo.txt
    python hamming3126.py decode meu_arquivo.txt.hamming
"""

import argparse
from pathlib import Path

PARITY_POS = [1, 2, 4, 8, 16]                # posições (1-based) dos bits de paridade
DATA_POS   = [i for i in range(1, 32) if i not in PARITY_POS]

def bits_from_int(value: int, length: int) -> list[int]:
    return [(value >> i) & 1 for i in reversed(range(length))]

def int_from_bits(bits: list[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v

# ----------------------------------------------------------------------
# ENCODE
# ----------------------------------------------------------------------
def encode_file(path: Path) -> Path:
    raw = path.read_bytes()
    length_bits = bits_from_int(len(raw), 32)            # cabeçalho: 32 bits com tamanho original
    payload_bits = length_bits + bits_from_int(int.from_bytes(raw, 'big'), len(raw)*8)

    codewords = []
    while payload_bits:
        data_block = payload_bits[:26]
        payload_bits = payload_bits[26:]
        data_block += [0]*(26-len(data_block))           # padding final

        word = [0]*32                                    # índice 1-based … usando word[1]
        for bit, pos in zip(data_block, DATA_POS):
            word[pos] = bit

        # calcular paridades de ordem 0-4
        for i, p in enumerate(PARITY_POS):
            xor_sum = 0
            for pos in range(1, 32):
                if pos & p and pos != p:
                    xor_sum ^= word[pos]
            word[p] = xor_sum

        codewords.append(''.join(str(b) for b in word[1:]))

    out_path = path.with_suffix(path.suffix + '.hamming')
    out_path.write_text(' '.join(codewords))
    return out_path

# ----------------------------------------------------------------------
# DECODE
# ----------------------------------------------------------------------
def decode_file(path: Path) -> Path:
    codewords = path.read_text().split()
    bitstream: list[int] = []

    for w in codewords:
        if len(w) != 31:
            raise ValueError(f"Palavra-código de tamanho inesperado: {w!r}")

        word = [0] + [int(c) for c in w]                 # 1-based outra vez
        syndrome = 0
        for i, p in enumerate(PARITY_POS):
            xor_sum = 0
            for pos in range(1, 32):
                if pos & p:
                    xor_sum ^= word[pos]
            if xor_sum:
                syndrome |= p

        if syndrome:                                     # corrige 1 bit
            if 1 <= syndrome <= 31:
                word[syndrome] ^= 1
            else:
                raise ValueError("Síndrome fora de alcance – possivelmente >1 erro")

        bitstream.extend(word[pos] for pos in DATA_POS)

    # Extrai tamanho original (32 bits) + bytes
    original_len = int_from_bits(bitstream[:32])
    data_bits = bitstream[32:32+original_len*8]
    data_int = int_from_bits(data_bits)
    decoded = data_int.to_bytes(original_len, 'big')

    out_path = path.with_suffix('.dec')
    out_path.write_bytes(decoded)
    return out_path

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Hamming (31, 26) encoder/decoder")
    ap.add_argument('mode', choices=('encode', 'decode'))
    ap.add_argument('file', help='arquivo de entrada')
    args = ap.parse_args()

    p = Path(args.file)
    if args.mode == 'encode':
        out = encode_file(p)
        print(f"[OK] Arquivo codificado em: {out}")
    else:
        out = decode_file(p)
        print(f"[OK] Arquivo decodificado em: {out}")

if __name__ == '__main__':
    main()
