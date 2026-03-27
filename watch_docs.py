#!/usr/bin/env python3
"""
watch_docs.py
=============
Modo **watch**: monitora o diretório raiz e regera automaticamente o
combined.md sempre que um arquivo .md é criado, modificado ou deletado.

Dependência:
    pip install watchdog

Uso:
    python watch_docs.py
    python watch_docs.py --root ./docs --output ./combined.md
"""

import argparse
import sys
import time
from pathlib import Path

try:
    from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
    from watchdog.observers import Observer
except ImportError:
    print(
        "❌ Pacote 'watchdog' não encontrado.\n"
        "   Instale com: pip install watchdog",
        file=sys.stderr,
    )
    sys.exit(1)

from combine_docs import DEFAULT_OUTPUT_NAME, IGNORED_DIRS, combine_docs


class MarkdownHandler(PatternMatchingEventHandler):
    """Observa mudanças em arquivos .md e dispara a reconsolidação."""

    def __init__(self, root: Path, output: Path) -> None:
        super().__init__(
            patterns=["*.md"],
            ignore_patterns=[str(output)],
            ignore_directories=False,
            case_sensitive=False,
        )
        self.root = root
        self.output = output
        self._last_run: float = 0.0
        self._debounce_secs = 1.5  # evita múltiplos disparos simultâneos

    def _rebuild(self, event: FileSystemEvent) -> None:
        now = time.time()
        if now - self._last_run < self._debounce_secs:
            return
        self._last_run = now

        # Ignora arquivos dentro de diretórios excluídos
        path = Path(event.src_path)
        if any(part in IGNORED_DIRS for part in path.parts):
            return

        print(f"\n🔄 Mudança detectada: {event.src_path}")
        combine_docs(self.root, self.output, verbose=True)

    on_created = _rebuild
    on_modified = _rebuild
    on_deleted = _rebuild


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitora mudanças em .md e regenera combined.md automaticamente."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output = (args.output or root / DEFAULT_OUTPUT_NAME).resolve()

    print(f"👁️  Monitorando: {root}")
    print(f"📄 Saída:        {output}")
    print("   Pressione Ctrl+C para parar.\n")

    # Gera imediatamente ao iniciar
    combine_docs(root, output, verbose=True)

    handler = MarkdownHandler(root, output)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Monitoramento encerrado.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
