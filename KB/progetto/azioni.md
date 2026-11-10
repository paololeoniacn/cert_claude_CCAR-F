# Azioni e checkpoint
> Stato del lavoro, punto di ripresa e azioni aperte del piano di 7 giorni.
Aggiornato: 2026-11-10

## Checkpoint 2026-11-10 (fine giornata)
- Struttura del progetto e KB pronte, con la guida ufficiale v0.1 elaborata.
- Banca di 408 domande scaricata in `fonti/ccafpreparation-bank-2026-11-10.json`. È esclusa da git con `.gitignore`.
- Trainer completo in `trainer/`: pratica adattiva, micro-lezione, mock da 60 domande con timer di 120 minuti, Review Screen, score report, elenco errori, modalità chat.
- Verifiche: 11 test unitari OK, test e2e delle API OK, test nel browser headless OK (nessun errore JS).
- Corretto un bug: il pulsante «Review» del mock apriva una Review Screen vuota.
- `trainer/state/` è vuota: l'utente non ha ancora risposto a nessuna domanda.

## Da fare (riprendi da qui)
| # | Azione | Stato |
|---|---|---|
| 1 | Tradurre in italiano le spiegazioni delle opzioni (circa 1.800 testi), in un file separato dalla banca, con MLX locale o con l'assistente. La UI deve mostrare l'italiano e tenere l'inglese come originale | aperta |
| 2 | Giorno 1: mock baseline da 60 domande senza studiare (`uv run trainer/ccar.py serve` → «Mock baseline») | aperta |
| 3 | Giorni 2–5: pratica per dominio secondo `target.md` | aperta |
| 4 | Giorno 6: 2 mock «final» (usano le domande riservate) | aperta |
| 5 | Prenotare l'esame quando i mock nuovi sono stabilmente ≥ 85% | aperta |
| 6 | Opzionale: scaricare la guida v1.0 dalla Partner Academy e aggiornare `KB/esame/divergenze.md` | aperta |
