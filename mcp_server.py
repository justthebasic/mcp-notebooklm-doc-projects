#!/usr/bin/env python3
"""
mcp_server.py
=============
Servidor MCP (Model Context Protocol) que expõe `combine_docs` como
uma *tool* utilizável por qualquer cliente MCP compatível
(Claude Desktop, Cursor AI, Gemini, etc.).

Dependências:
    pip install mcp

Execução:
    python mcp_server.py          # stdio transport (padrão para Claude Desktop)
    python mcp_server.py --http   # HTTP transport na porta 8000

Configuração no claude_desktop_config.json:
    {
      "mcpServers": {
        "notebooklm-docs": {
          "command": "python",
          "args": ["/caminho/absoluto/para/mcp_server.py"]
        }
      }
    }
"""

import argparse
import json
import sys
from pathlib import Path

# Importação condicional — instale com: pip install mcp
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        ListToolsResult,
        TextContent,
        Tool,
    )
except ImportError:
    print(
        "❌ Pacote 'mcp' não encontrado.\n"
        "   Instale com: pip install mcp\n"
        "   Documentação: https://github.com/modelcontextprotocol/python-sdk",
        file=sys.stderr,
    )
    sys.exit(1)

from combine_docs import DEFAULT_OUTPUT_NAME, IGNORED_DIRS, combine_docs

# ---------------------------------------------------------------------------
# Definição das ferramentas MCP
# ---------------------------------------------------------------------------

TOOLS = [
    Tool(
        name="combine_markdown_docs",
        description=(
            "Varre recursivamente um diretório de projeto, coleta todos os arquivos "
            ".md e os consolida em um único arquivo combined.md. "
            "Ignora automaticamente node_modules, .git, __pycache__ e similares."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Caminho absoluto ou relativo do diretório raiz a varrer.",
                },
                "output": {
                    "type": "string",
                    "description": (
                        "Caminho absoluto ou relativo do arquivo de saída. "
                        f"Padrão: <root>/{DEFAULT_OUTPUT_NAME}"
                    ),
                },
            },
            "required": ["root"],
        },
    ),
    Tool(
        name="list_markdown_files",
        description=(
            "Lista todos os arquivos .md encontrados em um diretório, "
            "respeitando as mesmas regras de exclusão do combine_markdown_docs."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "root": {
                    "type": "string",
                    "description": "Caminho absoluto ou relativo do diretório a listar.",
                }
            },
            "required": ["root"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_combine(root_str: str, output_str: str | None) -> str:
    """Executa combine_docs e retorna um relatório em texto."""
    root = Path(root_str).resolve()
    output = (Path(output_str) if output_str else root / DEFAULT_OUTPUT_NAME).resolve()

    if not root.is_dir():
        return f"❌ Erro: '{root}' não é um diretório válido."

    total = combine_docs(root, output, verbose=False)

    if total == 0:
        return f"⚠️  Nenhum arquivo .md encontrado em: {root}"

    size_kb = output.stat().st_size / 1024
    return (
        f"✅ Consolidação concluída!\n"
        f"   📁 Raiz:    {root.resolve()}\n"
        f"   📄 Arquivos: {total}\n"
        f"   💾 Saída:   {output}\n"
        f"   📏 Tamanho: {size_kb:.1f} KB"
    )


def handle_list(root_str: str) -> str:
    """Lista arquivos .md encontrados e retorna como JSON."""
    root = Path(root_str).resolve()

    if not root.is_dir():
        return f"❌ Erro: '{root}' não é um diretório válido."

    from combine_docs import collect_md_files

    files = collect_md_files(root, root / "__placeholder__")
    relative_paths = [str(f.relative_to(root)) for f in files]

    return json.dumps(
        {"root": str(root.resolve()), "total": len(files), "files": relative_paths},
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Servidor MCP
# ---------------------------------------------------------------------------


async def run_server() -> None:
    server = Server("notebooklm-doc-combiner")

    @server.list_tools()
    async def list_tools(_: ListToolsRequest) -> ListToolsResult:
        return ListToolsResult(tools=TOOLS)

    @server.call_tool()
    async def call_tool(request: CallToolRequest) -> CallToolResult:
        args = request.params.arguments or {}
        name = request.params.name

        if name == "combine_markdown_docs":
            result = handle_combine(
                root_str=args.get("root", "."),
                output_str=args.get("output"),
            )
        elif name == "list_markdown_files":
            result = handle_list(root_str=args.get("root", "."))
        else:
            result = f"❌ Ferramenta desconhecida: '{name}'"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    # Inicia com stdio transport (compatível com Claude Desktop / Cursor)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
