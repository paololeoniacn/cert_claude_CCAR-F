# Azioni e checkpoint
> Stato del lavoro, punto di ripresa e azioni aperte del piano di 7 giorni.
Aggiornato: 2026-11-11

## Checkpoint 2026-11-10 (fine giornata)
- Struttura del progetto e KB pronte, con la guida ufficiale v0.1 elaborata.
- Banca di 408 domande scaricata in `fonti/ccafpreparation-bank-2026-11-10.json`. È esclusa da git con `.gitignore`.
- Trainer completo in `trainer/`: pratica adattiva, micro-lezione, mock da 60 domande con timer di 120 minuti, Review Screen, score report, elenco errori, modalità chat.
- Verifiche: 11 test unitari OK, test e2e delle API OK, test nel browser headless OK (nessun errore JS).
- Corretto un bug: il pulsante «Review» del mock apriva una Review Screen vuota.
- `trainer/state/` è vuota: l'utente non ha ancora risposto a nessuna domanda.

## Checkpoint 2026-11-11
- Corretto: le 12 domande ufficiali (`os-*`) hanno solo un campo `explanation`, e prima la UI mostrava spiegazioni vuote.
- Aggiunti `trainer/translate.py` (ripartibile: rilancialo per completare) e le spiegazioni in italiano nella UI. 12 test unitari OK.

## Da fare (riprendi da qui)
| # | Azione | Stato |
|---|---|---|
| 1 | Tradurre in italiano le spiegazioni (1.612 per opzione + 12 spiegazioni ufficiali) con Qwen3.5-9B MLX locale in `trainer/data/rationale_it.jsonl`. La UI mostra l'italiano e l'originale EN richiudibile. Traduzione automatica: in caso di dubbio vale l'originale | in corso (2026-11-11) |
| 2 | Giorno 1: mock baseline da 60 domande senza studiare (`uv run trainer/ccar.py serve` → «Mock baseline») | aperta |
| 3 | Giorni 2–5: pratica per dominio secondo `target.md` | aperta |
| 4 | Giorno 6: 2 mock «final» (usano le domande riservate) | aperta |
| 5 | Prenotare l'esame quando i mock nuovi sono stabilmente ≥ 85% | aperta |
| 6 | Opzionale: scaricare la guida v1.0 dalla Partner Academy e aggiornare `KB/esame/divergenze.md` | aperta |
