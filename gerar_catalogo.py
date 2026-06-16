from pathlib import Path
import json
import re

# Execute este arquivo na mesma pasta do index.html.
# Estrutura:
# index.html
# catalogo.json
# gerar_catalogo.py
# img/
#   floral1.png
#   floral1verso.png
#   lisa1.png
#   lisa1verso.png
#
# Depois de adicionar/remover fotos, rode:
# python gerar_catalogo.py

PASTA_IMG = Path("img")
ARQUIVO_JSON = Path("catalogo.json")
ARQUIVO_INDEX = Path("index.html")

CATEGORIAS = {
    "floral": "Floral",
    "minimalista": "Minimalista",
    "estampado": "Estampado",
    "lisa": "Liso",
}

EXTENSOES = [".png", ".jpg", ".jpeg", ".webp", ".avif"]

PADRAO_FRENTE = re.compile(r"^(floral|minimalista|estampado|lisa)(\d*)$", re.IGNORECASE)


def encontrar_verso(base: str) -> str | None:
    for ext in EXTENSOES:
        candidato = PASTA_IMG / f"{base}verso{ext}"
        if candidato.exists():
            return f"img/{candidato.name}"
    return None


def gerar_catalogo() -> dict:
    catalogo = {categoria: [] for categoria in CATEGORIAS}

    if not PASTA_IMG.exists():
        print("Pasta img/ não encontrada.")
        return catalogo

    for arquivo in sorted(PASTA_IMG.iterdir(), key=lambda p: p.name.lower()):
        if not arquivo.is_file() or arquivo.suffix.lower() not in EXTENSOES:
            continue

        nome = arquivo.stem.lower()

        if nome.endswith("verso"):
            continue

        match = PADRAO_FRENTE.match(nome)
        if not match:
            continue

        categoria = match.group(1).lower()
        numero_txt = match.group(2)
        numero = int(numero_txt) if numero_txt else 1
        base = f"{categoria}{numero_txt}"

        verso = encontrar_verso(base)
        if not verso:
            print(f"IGNORADO: {arquivo.name} não tem verso correspondente ({base}verso.png, .jpg, .webp...)")
            continue

        catalogo[categoria].append({
            "id": base,
            "nome": base,
            "titulo": f"{CATEGORIAS[categoria]} {numero}",
            "categoria": categoria,
            "numero": numero,
            "frente": f"img/{arquivo.name}",
            "verso": verso
        })

    for categoria in catalogo:
        catalogo[categoria].sort(key=lambda x: x["numero"])

    return catalogo


def salvar_json(catalogo: dict) -> None:
    ARQUIVO_JSON.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK: catalogo.json atualizado.")


def atualizar_index(catalogo: dict) -> None:
    if not ARQUIVO_INDEX.exists():
        print("Aviso: index.html não encontrado; apenas catalogo.json foi gerado.")
        return

    html = ARQUIVO_INDEX.read_text(encoding="utf-8")
    inicio = '<script type="application/json" id="catalogoFallback">'
    fim = '</script>'

    pos_inicio = html.find(inicio)
    if pos_inicio == -1:
        print("Aviso: o index.html não tem o bloco catalogoFallback.")
        return

    pos_conteudo = pos_inicio + len(inicio)
    pos_fim = html.find(fim, pos_conteudo)

    if pos_fim == -1:
        print("Aviso: fechamento do catalogoFallback não encontrado.")
        return

    novo_json = "\n" + json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n  "
    html = html[:pos_conteudo] + novo_json + html[pos_fim:]
    ARQUIVO_INDEX.write_text(html, encoding="utf-8")
    print("OK: catálogo interno do index.html atualizado.")


if __name__ == "__main__":
    catalogo = gerar_catalogo()
    salvar_json(catalogo)
    atualizar_index(catalogo)

    total = sum(len(lista) for lista in catalogo.values())
    print(f"Total de colchas encontradas com frente e verso: {total}")
