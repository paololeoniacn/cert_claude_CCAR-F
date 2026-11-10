# Formato dell'esame CCAR-F
> Struttura, punteggio, scenari e regole di iscrizione dell'esame Claude Certified Architect – Foundations.
Aggiornato: 2026-11-10

## Formato
- 60 domande in 120 minuti. Calcola circa 135 minuti in sede (check-in e survey). (fonte: https://claude.termidy.com/ccar-f/)
- Guida v0.1: tutte le domande sono a scelta multipla, con 1 risposta corretta e 3 distrattori. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
- Guida v1.0 (luglio 2026): domande multiple choice **e** multiple response. Ogni domanda dice quante risposte scegliere. (fonte: https://www.ccafpreparation.com/ ; https://claude.termidy.com/ccar-f/) ⚠️ contrasto con la v0.1: vale la v1.0, che è più recente.
- Una risposta mancante conta come errata. Non ci sono penalità per i tentativi. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
- Esame closed book, sorvegliato, online con webcam o in un centro Pearson VUE. Solo in inglese. (fonte: https://claude.termidy.com/ccar-f/)
- Costo: 125 USD. (fonte: https://www.ccafpreparation.com/) — da confermare su fonte ufficiale.

## Punteggio
- Punteggio scalato da 100 a 1.000. La soglia è 720. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
- La scala compensa la difficoltà della singola forma d'esame: 720 non è il 72% di risposte corrette. (fonte: https://www.ccafpreparation.com/)
- Il report mostra anche la percentuale corretta per dominio. (fonte: https://claude.termidy.com/ccar-f/)

## Scenari
L'esame presenta 4 scenari scelti a caso tra 6, circa 15 domande ciascuno. Prepara tutti e 6. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)

| # | Scenario | Domini principali |
|---|---|---|
| 1 | Customer Support Resolution Agent (Agent SDK, tool MCP `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`, obiettivo 80%+ first-contact resolution) | 1, 2, 5 |
| 2 | Code Generation with Claude Code (slash command, CLAUDE.md, plan mode vs esecuzione diretta) | 3, 5 |
| 3 | Multi-Agent Research System (coordinator + subagent search, analysis, synthesis, report) | 1, 2, 5 |
| 4 | Developer Productivity with Claude (tool built-in Read, Write, Bash, Grep, Glob + server MCP) | 2, 3, 1 |
| 5 | Claude Code for Continuous Integration (review automatica, test, feedback PR, pochi falsi positivi) | 3, 4 |
| 6 | Structured Data Extraction (JSON schema, validazione, casi limite) | 4, 5 |

## Validità e ripetizioni
- La certificazione vale 12 mesi. (fonte: https://claude.termidy.com/ccar-f/)
- Dopo un esame fallito: attesa di 14 giorni, poi 30, poi 90. Massimo 4 tentativi in 12 mesi. (fonte: https://claude.termidy.com/ccar-f/)
- L'iscrizione avviene sulla Anthropic Partner Academy (Skilljar) con un'email aziendale di un dominio partner. (fonte: https://claude.termidy.com/ccar-f/)

## Fuori programma
Fine-tuning, autenticazione/billing API, hosting di server MCP, architettura interna di Claude, Constitutional AI/RLHF, embedding e vector DB, computer use, vision, streaming/SSE, rate limit e prezzi, OAuth, configurazioni cloud specifiche, benchmark, dettagli del prompt caching, tokenizzazione. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
