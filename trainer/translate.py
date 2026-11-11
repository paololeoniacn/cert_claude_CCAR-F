"""Traduce in italiano le spiegazioni (rationale) della banca con un modello MLX locale.

Uscita: trainer/data/rationale_it.jsonl, una riga {"id", "rationale_it"} per domanda.
Ripartibile: salta le domande già tradotte. Solo locale (derivato dalla banca, escluso da git).

    uv run --with mlx-lm trainer/translate.py [--limit N] [--model ID]
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BANK_FILE = ROOT.parent / "fonti" / "ccafpreparation-bank-2026-11-10.json"
OUT_FILE = ROOT / "data" / "rationale_it.jsonl"
DEFAULT_MODEL = "mlx-community/Qwen3.5-9B-MLX-4bit"

SYSTEM = (
    "Sei un traduttore tecnico. Traduci dall'inglese all'italiano spiegazioni di un esame su Claude, "
    "Claude Code, Agent SDK e MCP. Regole: traduzione fedele e completa, nessun commento aggiunto. "
    "Non tradurre identificatori, nomi di prodotto e termini tecnici: Claude Code, Agent SDK, MCP, "
    "subagent, coordinator, tool, tool_use, tool_result, stop_reason, end_turn, hook, PreToolUse, "
    "PostToolUse, CLAUDE.md, skill, slash command, plan mode, prompt, system prompt, few-shot, "
    "JSON schema, context window, batch, Message Batches API, fork_session, --resume, allowedTools, "
    "nomi di file, codice e testo tra apici o backtick. Scrivi sempre 'subagent' (mai 'agente secondario' "
    "o 'sottoagente') e 'coordinator' (mai 'coordinatore'). Mantieni le lettere delle opzioni (A, B, C...). "
    "Rispondi solo con un oggetto JSON con le stesse chiavi dell'input."
)

log = logging.getLogger("translate")


def done_ids() -> set[str]:
    if not OUT_FILE.exists():
        return set()
    return {json.loads(line)["id"] for line in OUT_FILE.read_text(encoding="utf-8").splitlines() if line.strip()}


def parse_json(text: str, keys: set[str]) -> dict[str, str] | None:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or set(obj) != keys or not all(isinstance(v, str) and v.strip() for v in obj.values()):
        return None
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", nargs="*", help="traduci solo questi id (prova)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from mlx_lm import generate, load

    bank = json.loads(BANK_FILE.read_text(encoding="utf-8"))
    skip = done_ids()
    todo = [q for q in bank if q["id"] not in skip and (not args.ids or q["id"] in args.ids)]
    if args.limit:
        todo = todo[: args.limit]
    log.info("model=%s todo=%d already=%d", args.model, len(todo), len(skip))
    model, tok = load(args.model)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    failed = []
    t0 = time.time()
    for i, q in enumerate(todo, 1):
        src = q["rationale"] or {"explanation": q["explanation"]}
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(src, ensure_ascii=False)}]
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False)
        out = None
        for attempt in range(2):
            text = generate(model, tok, prompt=prompt, max_tokens=3000, verbose=False)
            out = parse_json(text, set(src))
            if out:
                break
            log.warning("id=%s attempt=%d invalid JSON output", q["id"], attempt + 1)
        if not out:
            failed.append(q["id"])
            continue
        with OUT_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"id": q["id"], "model": args.model, "rationale_it": out}, ensure_ascii=False) + "\n")
        if i % 10 == 0 or i == len(todo):
            el = time.time() - t0
            log.info("progress %d/%d elapsed=%.0fs eta=%.0fs", i, len(todo), el, el / i * (len(todo) - i))
    log.info("done ok=%d failed=%d %s", len(todo) - len(failed), len(failed), failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
