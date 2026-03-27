#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp[cli]>=1.2.0",
# ]
# ///
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP
# Importação do script core
from combine_docs import combine_docs, collect_md_files, DEFAULT_OUTPUT_NAME

# Inicializa o servidor FastMCP
mcp = FastMCP("notebooklm-docs")

# ---------------------------------------------------------------------------
# Helpers (Adaptadores de Resposta)
# ---------------------------------------------------------------------------

def handle_combine(root_str: str, output_str: str | None) -> dict:
    """Invoca o core de consolidação e retorna os metadados da execução."""
    root = Path(root_str).resolve()
    if not root.is_dir():
        return {"error": f"❌ Erro: '{root}' não é um diretório válido."}

    output = Path(output_str).resolve() if output_str else root / DEFAULT_OUTPUT_NAME
    
    from combine_docs import combine_docs
    total = combine_docs(root, output, verbose=False)

    if total == 0:
        return {"error": f"⚠️ Nenhum arquivo .md encontrado em: {root}"}

    size_kb = output.stat().st_size / 1024
    
    return {
        "msg": "✅ Consolidação concluída",
        "root": str(root.resolve()),
        "total_files": total,
        "output_path": str(output),
        "size_kb": round(size_kb, 1)
    }


def handle_list(root_str: str) -> dict:
    """Lista arquivos .md encontrados e retorna como objeto estruturado."""
    root = Path(root_str).resolve()

    if not root.is_dir():
        return {"error": f"❌ Erro: '{root}' não é um diretório válido."}

    # Coleta arquivos sem escrever a saída
    files = collect_md_files(root, root / "__placeholder__")
    relative_paths = [str(f.relative_to(root)) for f in files]

    return {
        "root": str(root.resolve()),
        "total": len(files),
        "files": relative_paths
    }

# ---------------------------------------------------------------------------
# Definição das Tools (Interface MCP)
# ---------------------------------------------------------------------------

@mcp.tool()
async def combine_markdown_docs(root: str, output: str = None) -> dict:
    """
    Varre recursivamente um diretório, coleta arquivos .md e os consolida em um único arquivo.
    Ignora automaticamente node_modules, .git e outras pastas de sistema.

    Args:
        root: Caminho absoluto ou relativo do diretório raiz a varrer.
        output: Caminho de saída. Padrão: <root>/combined.md.
    """
    return handle_combine(root, output)


@mcp.tool()
async def list_markdown_files(root: str) -> dict:
    """
    Lista todos os arquivos .md encontrados em um diretório, seguindo as regras de exclusão.
    Use esta ferramenta para verificar o que será incluído antes de consolidar.

    Args:
        root: Caminho absoluto ou relativo do diretório a listar.
    """
    return handle_list(root)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # O FastMCP gerencia o transporte stdio por padrão se chamado sem argumentos
    mcp.run()
