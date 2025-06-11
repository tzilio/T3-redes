#!/usr/bin/env python3
"""
Codificador/decodificador Hamming (31, 26).

Uso:
    python hamming3126.py codificar  arquivo.txt
    python hamming3126.py decodificar arquivo.txt.hamming
"""

import argparse
from pathlib import Path

# Constantes
TAMANHO_PALAVRA = 31
POS_PARIDADE = [1, 2, 4, 8, 16] # posições (1‑based) reservadas à paridade
POS_DADOS = [i for i in range(1, 32) if i not in POS_PARIDADE]

# Utilidades de conversão

def inteiro_para_bits(valor: int, tamanho: int) -> list[int]:
    return [(valor >> i) & 1 for i in reversed(range(tamanho))]


def bits_para_inteiro(bits: list[int]) -> int:
    resultado = 0
    for bit in bits:
        resultado = (resultado << 1) | bit
    return resultado

# Cálculo de paridade

def calcular_paridades(palavra_bits: list[int]) -> None:
    # Calcula os bits de paridade e os insere nas posições 1, 2, 4, 8 e 16 da lista 1-based 'palavra'.
    # Cada paridade em 'pos_paridade' verifica as posições cujo índice tem esse bit ativado.
    # O valor da paridade é o XOR de todos os bits das posições verificadas.
    for pos_paridade in POS_PARIDADE:
        xor_acumulado = 0
        for indice in range(1, TAMANHO_PALAVRA + 1):
            if indice != pos_paridade and indice & pos_paridade:
                xor_acumulado ^= palavra_bits[indice]
        palavra_bits[pos_paridade] = xor_acumulado

# Codificação

def codificar_arquivo(caminho: Path) -> Path:
    dados_bytes = caminho.read_bytes()

    # Cabeçalho de 32 bits indicando o tamanho original do arquivo em bytes.
    bits_cabecalho = inteiro_para_bits(len(dados_bytes), 32)

    # Converte todos os bytes do arquivo em bits e concatena com o cabeçalho,
    # formando uma lista única que será dividida em blocos de 26 bits na decodificação.
    bits_conteudo = inteiro_para_bits(int.from_bytes(dados_bytes, 'big'), len(dados_bytes) * 8)
    bitstream = bits_cabecalho + bits_conteudo

    palavras_codificadas: list[str] = []
    while bitstream:
        bloco_dados = bitstream[:26]
        bitstream = bitstream[26:]
        bloco_dados += [0] * (26 - len(bloco_dados))  # padding no bloco final para garantir 26 bits.

        palavra_bits = [0] * 32  # índice 0 é descartado; usamos 1..31
        for bit, pos in zip(bloco_dados, POS_DADOS):
            palavra_bits[pos] = bit

        calcular_paridades(palavra_bits)
        palavras_codificadas.append(''.join(str(b) for b in palavra_bits[1:]))

    destino = caminho.with_suffix(caminho.suffix + '.hamming')
    destino.write_text(' '.join(palavras_codificadas))
    return destino

# Decodificação

def descobrir_pos_erro(palavra_bits: list[int]) -> int:
    # Retorna a posição do bit errado (0 se nenhum erro, não trata mais de 1 erro).
    pos_erro = 0
    for pos_paridade in POS_PARIDADE:
        xor_acumulado = 0
        for indice in range(1, TAMANHO_PALAVRA + 1):
            if indice & pos_paridade:
                xor_acumulado ^= palavra_bits[indice]
        if xor_acumulado:
            pos_erro |= pos_paridade
    return pos_erro


def decodificar_arquivo(caminho: Path) -> Path:
    palavras = caminho.read_text().split()
    bitstream: list[int] = []

    for str_palavra in palavras:
        if len(str_palavra) != TAMANHO_PALAVRA:
            raise ValueError(f'Palavra de tamanho inválido: {str_palavra!r}')

        palavra = [0] + [int(c) for c in str_palavra]  # 1‑based
        pos_erro = descobrir_pos_erro(palavra)

        if 1 <= pos_erro <= TAMANHO_PALAVRA:
            palavra[pos_erro] ^= 1
            
        bitstream.extend(palavra[pos] for pos in POS_DADOS)

    tamanho_original = bits_para_inteiro(bitstream[:32]) # 32 primeiros bits = cabeçalho com o número de bytes originais do arquivo.
    bits_dados = bitstream[32:32 + tamanho_original * 8] # ignora os 32 bits iniciais
    dados_recuperados = bits_para_inteiro(bits_dados).to_bytes(tamanho_original, 'big') # recupera conteúdo original do arquivo em bytes

    destino = caminho.with_suffix('.dec')
    destino.write_bytes(dados_recuperados)
    return destino

# CLI
def main() -> None:
    parser = argparse.ArgumentParser(description='Codifica ou decodifica arquivos usando Hamming (31, 26).')
    parser.add_argument('modo', choices=('codificar', 'decodificar'))
    parser.add_argument('arquivo', help='caminho do arquivo de entrada')
    args = parser.parse_args()

    caminho = Path(args.arquivo)
    if args.modo == 'codificar':
        saida = codificar_arquivo(caminho)
        print(f'[OK] Arquivo codificado: {saida}')
    else:
        saida = decodificar_arquivo(caminho)
        print(f'[OK] Arquivo decodificado: {saida}')


if __name__ == '__main__':
    main()
