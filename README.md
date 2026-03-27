# 📚 combine_docs — Consolidador de Documentação Markdown

> Une todos os arquivos `.md` de um projeto em um único `combined.md`, ideal para uso com **NotebookLM** e integrações **MCP**.

---

## 📁 Estrutura do Projeto

```
mcp-notebooklm-doc-projects/
├── combine_docs.py   ← Script principal (sem dependências externas)
├── mcp_server.py     ← Servidor MCP (requer: pip install mcp)
├── watch_docs.py     ← Modo watch automático (requer: pip install watchdog)
└── README.md
```

---

## ⚡ Instalação Rápida

```bash
# Apenas para o script principal — sem dependências externas!
python combine_docs.py

# Para MCP e watch:
pip install mcp watchdog
```

---

## 🛠️ Uso do Script Principal

### Sintaxe

```bash
python combine_docs.py [--root DIR] [--output FILE] [--quiet]
```

### Exemplos

```bash
# Varra o diretório atual
python combine_docs.py

# Varra um projeto externo
python combine_docs.py --root ~/Documentos/meu-projeto

# Saída personalizada
python combine_docs.py --root ./docs --output ./combined.md

# Silencioso (para CI/CD)
python combine_docs.py --root . --quiet
```

### O que o script produz

O `combined.md` gerado contém:
- **Cabeçalho** com data, raiz e total de arquivos
- **Índice clicável** com todos os arquivos encontrados
- **Seções separadas** por `---`, cada uma com path relativo e absoluto
- **Ordenação** alfabética por caminho relativo

### Diretórios ignorados automaticamente

```
node_modules  .git  .venv  venv  __pycache__
dist  build  .next  .nuxt  coverage  .pytest_cache
.mypy_cache  .ruff_cache  htmlcov  env  .env
```

---

## 🔄 Modo Watch Automático

Regenera o `combined.md` sempre que um `.md` é alterado:

```bash
pip install watchdog
python watch_docs.py

# Com opções
python watch_docs.py --root ./docs --output ./combined.md
```

---

## 🤖 Integração com MCP

### Ferramentas expostas pelo mcp_server.py

| Tool | Descrição |
|------|-----------|
| `combine_markdown_docs` | Gera/atualiza o `combined.md` |
| `list_markdown_files` | Lista todos os `.md` encontrados |

### Configuração no Claude Desktop

Arquivo: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notebooklm-docs": {
      "command": "python",
      "args": [
        "/caminho/para/seu/projeto/mcp_server.py"
      ]
    }
  }
}
```

Reinicie o Claude Desktop. Na conversa, use:

> *"Consolide todos os .md do projeto /caminho/do/meu-projeto"*

### Configuração no Cursor AI

Arquivo: `.cursor/mcp.json` (na raiz do projeto)

```json
{
  "mcpServers": {
    "notebooklm-docs": {
      "command": "python",
      "args": ["./mcp_server.py"]
    }
  }
}
```

### Configuração no Antigravity (Gemini)

```json
{
  "name": "notebooklm-docs",
  "command": "python",
  "args": ["/caminho/para/seu/projeto/mcp_server.py"],
  "description": "Consolida documentação .md para NotebookLM"
}
```

---

## 📓 Fluxo Completo com NotebookLM

```
Projeto (vários .md dispersos)
            │
            ▼
    python combine_docs.py          ← Passo 1
            │
            ▼
        combined.md                  ← Passo 2: arquivo consolidado
            │
            ▼
    Upload no NotebookLM             ← Passo 3: adicionar como fonte
   (notebooklm.google.com)
            │
            ▼
  Perguntas em linguagem natural     ← Passo 4: consulte sua documentação
```

### Com MCP (fluxo automatizado)

```
Você pede ao agente de IA          ← "Atualize a doc do projeto X"
            │
            ▼
    mcp_server.py                   ← Agente chama a tool via MCP
            │
            ▼
        combined.md atualizado       ← Pronto para upload no NotebookLM
```

---

## 🔧 Personalização

### Adicionar mais diretórios ao blacklist

Em `combine_docs.py`, edite `IGNORED_DIRS`:

```python
IGNORED_DIRS: set[str] = {
    "node_modules",
    ".git",
    "minha_pasta_extra",   # ← adicione aqui
    ...
}
```

### Integrar ao Makefile

```makefile
docs:
	python combine_docs.py --root . --output combined.md

watch-docs:
	python watch_docs.py
```

### Automação com GitHub Actions

```yaml
- name: Consolidar documentação
  run: python combine_docs.py --root . --quiet

- name: Commit combined.md
  run: |
    git add combined.md
    git diff --staged --quiet || git commit -m "docs: atualiza combined.md [skip ci]"
    git push
```

---

## 💡 Melhorias Futuras

| Melhoria | Complexidade | Benefício |
|----------|-------------|-----------|
| `--format html` para exportar como HTML | Baixa | Compartilhar no browser |
| `--since <data>` para arquivos recentes | Média | Performance em projetos grandes |
| Upload automático via API do NotebookLM | Alta | Fluxo 100% automático |
| Busca semântica local com embeddings | Alta | Alternativa ao NotebookLM |
| Suporte a `.rst` e `.txt` | Baixa | Projetos Python/Sphinx |
| Dashboard web com preview | Média | Visibilidade do processo |

---

## 📦 Dependências

| Pacote | Obrigatório | Uso |
|--------|-------------|-----|
| Python 3.10+ | ✅ | Runtime |
| `mcp` | Só para MCP | `pip install mcp` |
| `watchdog` | Só para watch | `pip install watchdog` |

> O `combine_docs.py` usa **apenas stdlib** — zero dependências externas.
