from pathlib import Path
import json
import re

IMG_DIR = Path('img')
MARTELASSE_DIR = IMG_DIR / 'martelasse'
POLIESTER_DIR = IMG_DIR / 'poliester'
OUT_FILE = Path('catalogo.json')
VALID_EXTS = {'.png'}


def titulo_bonito(nome: str) -> str:
    nome = re.sub(r'(?i)verso$', '', nome)
    nome = re.sub(r'[-_]+', ' ', nome)
    nome = re.sub(r'([A-Za-zÀ-ÿ])([0-9]+)', r'\1 \2', nome)
    nome = ' '.join(nome.split())
    return nome.title() or 'Acolchoado'


def extrair_listas_catalogo(data):
    """Aceita {catalogo:[...]}, formatos antigos por categorias ou lista direta."""
    if isinstance(data, dict) and isinstance(data.get('catalogo'), list):
        return [data.get('catalogo', [])]
    if isinstance(data, dict):
        return [v for v in data.values() if isinstance(v, list)]
    if isinstance(data, list):
        return [data]
    return []


def carregar_itens_existentes():
    """
    Lê o catalogo.json atual e guarda o item inteiro.
    Assim, quando rodar o GCO.py de novo, as colchas já existentes
    permanecem exatamente com as mesmas variáveis/campos.
    """
    existentes = {}

    if not OUT_FILE.exists():
        return existentes

    try:
        data = json.loads(OUT_FILE.read_text(encoding='utf-8'))
    except Exception as err:
        print(f'Aviso: não consegui ler o catálogo antigo para preservar dados: {err}')
        return existentes

    for lista in extrair_listas_catalogo(data):
        for item in lista:
            if not isinstance(item, dict):
                continue

            chaves = [
                item.get('id'),
                item.get('nome'),
                Path(str(item.get('frente', ''))).stem if item.get('frente') else None,
            ]

            for chave in chaves:
                if chave:
                    existentes[str(chave).lower()] = dict(item)

    return existentes


def item_existente_ou_novo(existentes, stem, novo_item):
    """Se já existir, devolve o item antigo sem mexer em nada."""
    antigo = existentes.get(stem.lower())
    if antigo:
        return antigo
    return novo_item


def gerar_martelasse(existentes):
    itens = []

    if not MARTELASSE_DIR.exists():
        MARTELASSE_DIR.mkdir(parents=True, exist_ok=True)
        print('Pasta img/martelasse/ criada.')

    arquivos = sorted([
        p for p in MARTELASSE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTS
    ])

    for frente in arquivos:
        stem = frente.stem
        if stem.lower().endswith('verso'):
            continue

        verso = frente.with_name(f'{stem}verso{frente.suffix}')
        if not verso.exists():
            print(f'Ignorado em martelasse: {frente.name} não tem verso correspondente: {stem}verso{frente.suffix}')
            continue

        novo_item = {
            'id': stem,
            'nome': stem,
            'titulo': titulo_bonito(stem),
            'frente': f'img/martelasse/{frente.name}',
            'verso': f'img/martelasse/{verso.name}',
            'poliester': False,
            'martelasse': True,
            'esgotado': False,
        }
        itens.append(item_existente_ou_novo(existentes, stem, novo_item))

    return itens


def gerar_poliester(existentes):
    itens = []

    if not POLIESTER_DIR.exists():
        POLIESTER_DIR.mkdir(parents=True, exist_ok=True)
        print('Pasta img/poliester/ criada.')

    arquivos = sorted([
        p for p in POLIESTER_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTS
    ])

    for frente in arquivos:
        stem = frente.stem
        if stem.lower().endswith('verso'):
            print(f'Ignorado em poliester: {frente.name} parece ser verso, mas poliéster não é dupla face.')
            continue

        novo_item = {
            'id': stem,
            'nome': stem,
            'titulo': titulo_bonito(stem),
            'frente': f'img/poliester/{frente.name}',
            'poliester': True,
            'martelasse': False,
            'esgotado': False,
        }
        itens.append(item_existente_ou_novo(existentes, stem, novo_item))

    return itens


def main():
    if not IMG_DIR.exists():
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        print('Pasta img/ criada.')

    existentes = carregar_itens_existentes()

    itens = []
    itens.extend(gerar_martelasse(existentes))
    itens.extend(gerar_poliester(existentes))

    OUT_FILE.write_text(
        json.dumps({'catalogo': itens}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(f'Catálogo gerado: {OUT_FILE} ({len(itens)} modelos)')
    print('Use:')
    print('  img/martelasse/nome.png + img/martelasse/nomeverso.png')
    print('  img/poliester/nome.png')


if __name__ == '__main__':
    main()
