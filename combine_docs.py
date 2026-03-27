#!/usr/bin/env python3
"""
combine_docs.py
================
Consolida todos os arquivos .md de um diretório de projeto em um único
arquivo `combined.md`, mantendo ordem consistente e separadores claros.

Uso básico:
    python combine_docs.py
    python combine_docs.py --root ./meu-projeto --output ./out/combined.md

Compatível com integração MCP (Model Context Protocol).
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Diretórios a ignorar durante a varredura
IGNORED_DIRS: set[str] = {
    "node_modules",
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
}

# Nome padrão do arquivo de saída (ignorado na varredura para evitar
# incluir o próprio combined.md caso já exista)
DEFAULT_OUTPUT_NAME = "combined.md"

# Separador visual entre arquivos
SEPARATOR = "\n\n---\n\n"


# ---------------------------------------------------------------------------
# Funções principais
# ---------------------------------------------------------------------------


def collect_md_files(root: Path, output_path: Path) -> list[Path]:
    """
    Varre recursivamente *root* e retorna todos os arquivos .md encontrados,
    excluindo diretórios ignorados e o próprio arquivo de saída.

    Args:
        root:        Diretório raiz da varredura.
        output_path: Caminho absoluto do arquivo de saída (será excluído).

    Returns:
        Lista de Path objects ordenada alfabeticamente pelo caminho relativo.
    """
    md_files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Filtrar diretórios ignorados in-place (afeta a recursão do os.walk)
        dirnames[:] = sorted(
            d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")
        )

        for filename in sorted(filenames):
            if filename.lower().endswith(".md"):
                full_path = Path(dirpath) / filename

                # Evita incluir o próprio arquivo de saída
                if full_path.resolve() == output_path.resolve():
                    continue

                md_files.append(full_path)

    return md_files


def build_header(root: Path, files: list[Path]) -> str:
    """
    Gera um cabeçalho com metadados da consolidação.

    Args:
        root:  Diretório raiz usado na varredura.
        files: Lista de arquivos que serão incluídos.

    Returns:
        String com o cabeçalho formatado em Markdown.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    toc_lines = [
        f"- [{f.relative_to(root)}](#{_anchor(str(f.relative_to(root)))})"
        for f in files
    ]
    toc = "\n".join(toc_lines)

    return (
        f"# 📚 Documentação Consolidada\n\n"
        f"> **Gerado automaticamente por `combine_docs.py`**  \n"
        f"> 🗂️ Raiz: `{root.resolve()}`  \n"
        f"> 📅 Data: `{timestamp}`  \n"
        f"> 📄 Total de arquivos: `{len(files)}`\n\n"
        f"---\n\n"
        f"## 📑 Índice\n\n"
        f"{toc}\n"
    )


def _anchor(text: str) -> str:
    """
    Converte um caminho de arquivo em um âncora Markdown compatível com
    GitHub/Obsidian (lowercase, espaços → hífens, remove caracteres especiais).
    """
    import re
    anchor = text.lower()
    anchor = re.sub(r"[/\\]", "-", anchor)          # separadores → hifén
    anchor = re.sub(r"[^\w\s-]", "", anchor)         # remove especiais
    anchor = re.sub(r"[\s]+", "-", anchor)            # espaços → hifén
    anchor = re.sub(r"-{2,}", "-", anchor)            # hifens duplos
    return anchor.strip("-")


def build_file_section(file_path: Path, root: Path) -> str:
    """
    Lê um arquivo .md e retorna seu conteúdo encapsulado com cabeçalho
    identificador e separador.

    Args:
        file_path: Caminho absoluto do arquivo.
        root:      Diretório raiz (para calcular o caminho relativo).

    Returns:
        String com o bloco formatado.
    """
    relative = file_path.relative_to(root)

    try:
        content = file_path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        content = file_path.read_text(encoding="latin-1").strip()
    except OSError as exc:
        content = f"⚠️ **Erro ao ler o arquivo:** `{exc}`"

    header = (
        f"## 📄 `{relative}`\n\n"
        f"> 📁 **Caminho:** `{file_path.resolve()}`\n"
    )

    return f"{header}\n{content}"


def combine_docs(
    root: Path,
    output_path: Path,
    *,
    verbose: bool = True,
) -> int:
    """
    Função principal: coleta, processa e grava o arquivo consolidado.

    Args:
        root:        Diretório raiz da varredura.
        output_path: Destino do arquivo consolidado.
        verbose:     Se True, imprime progresso no stdout.

    Returns:
        Número de arquivos processados.
    """
    # Garante que o diretório de saída existe
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"🔍 Varrendo: {root}")

    files = collect_md_files(root, output_path)

    if not files:
        print("⚠️  Nenhum arquivo .md encontrado. Abortando.")
        return 0

    if verbose:
        print(f"📄 {len(files)} arquivo(s) encontrado(s).\n")

    sections: list[str] = [build_header(root, files)]

    for i, file_path in enumerate(files, start=1):
        if verbose:
            relative = file_path.relative_to(root)
            print(f"  [{i:>3}/{len(files)}] {relative}")
        sections.append(build_file_section(file_path, root))

    combined = SEPARATOR.join(sections)
    output_path.write_text(combined, encoding="utf-8")

    if verbose:
        size_kb = output_path.stat().st_size / 1024
        print(f"\n✅ Arquivo gerado: {output_path}")
        print(f"   Tamanho: {size_kb:.1f} KB")

    return len(files)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolida arquivos .md de um projeto em um único combined.md.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python combine_docs.py
  python combine_docs.py --root ./docs --output ./combined.md
  python combine_docs.py --root /home/user/projeto --output /tmp/combined.md --quiet
        """,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Diretório raiz a varrer (padrão: diretório atual)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Caminho do arquivo de saída (padrão: <root>/{DEFAULT_OUTPUT_NAME})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suprime a saída de progresso",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    root = args.root
    if not root.is_dir():
        print(f"❌ Erro: '{root}' não é um diretório válido.", file=sys.stderr)
        sys.exit(1)

    output = (args.output or root / DEFAULT_OUTPUT_NAME).resolve()

    total = combine_docs(root, output, verbose=not args.quiet)

    if total == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
