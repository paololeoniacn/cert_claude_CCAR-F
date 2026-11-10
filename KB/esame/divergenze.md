# Divergenze tra guida d'esame e documentazione attuale
> Dove la guida CCAR-F e la documentazione Anthropic attuale non coincidono, e quale risposta dare all'esame.
Aggiornato: 2026-11-10

Fonte di tutto il file: https://www.ccafpreparation.com/divergence-log (sito indipendente, docs consultate dal sito il 2026-07-30). Regola generale del sito: all'esame rispondi secondo la guida.

| Tema | Guida d'esame | Documentazione attuale | Risposta all'esame |
|---|---|---|---|
| Tool per i subagent | `Task`, in `allowedTools` | Rinominato `Agent` in Claude Code v2.1.63 | `Task` |
| `stop_reason` | Solo `tool_use` / `end_turn` | 7 valori, tra cui `pause_turn`, `max_tokens`, `refusal` | Il modello a 2 valori |
| Comunicazione tra subagent | Sempre tramite il coordinator | Claude Code ammette subagent annidati | Tramite il coordinator |
| Sessioni con nome | `--resume <session-name>` | `--resume` non assegna il nome: si usa `--name`/`-n` o `/rename` | `--resume <session-name>` |
| Scope MCP | 2 livelli: `.mcp.json`, `~/.claude.json` | 3 livelli: local, project, user | Modello a 2 livelli |
| `allowed-tools` nelle skill | Limita i tool | Pre-approva i tool senza permesso; per limitare si usa `disallowed-tools` | Limita i tool |
| `@import` | Nome della funzione | La sintassi reale è `@path/del/file` | Riconosci entrambe |
| Comandi vs skill | Due sistemi | Sistema unico; la skill vince in caso di nome uguale | Conosci entrambe le forme |

Il log contiene altre voci non ancora lette (da `start_index` 15000 in poi).
