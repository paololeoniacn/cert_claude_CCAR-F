# Target: superare CCAR-F in 7 giorni

Approccio question-first: teoria solo quando sbagli. L'esame è scenario-based: richiede di scegliere il trade-off architetturale corretto, non di ricordare definizioni (fonte: Claude Certified Architect – Foundations Certification Exam Guide).

## Trainer interattivo adattivo

Una domanda alla volta, senza risposta visibile. L'utente sceglie A/B/C/D. Il sistema risponde con:
- ✅/❌ e risposta corretta
- perché è corretta e perché le altre sono sbagliate
- concetto Anthropic da ricordare
- punteggio aggiornato per dominio

Regole di ripetizione:
- Domanda sbagliata: ritorna dopo 5-10 domande.
- Sbagliata due volte: micro-lezione prima di riproporla.
- Punti deboli: frequenza aumentata automaticamente.
- Quando stabile: simulazione completa a tempo.

## Materiale (da verificare contro exam guide e documentazione Anthropic)

- Claude Certified Architect Foundations - 6 Practice Exams: 360 domande, 6 test da 60 (dichiarato).
- Claude Certified Architect Foundations (CCAR-F) Exam Prep: 408 domande, 30 lezioni, mock exam, gratuito, senza login (dichiarato).
- CCAR-F Study Resources: mappa il programma sulla documentazione Anthropic (Agent SDK, subagents, hooks, sessions, MCP, tool design, CLAUDE.md, Skills, plan mode).
- Le risposte dei siti terzi non sono affidabili senza verifica.

## Blueprint (da risorse di preparazione)

| Dominio | Peso |
|---|---|
| Agentic Architecture & Orchestration | 27% |
| Claude Code Configuration & Workflows | 20% |
| Prompt Engineering & Structured Output | 20% |
| Tool Design & MCP Integration | 18% |
| Context Management & Reliability | 15% |

## Piano 7 giorni

1. Baseline: 60 domande senza studiare.
2. Agentic Architecture: domanda → errore → micro-lezione → domanda simile.
3. MCP + Tool Design.
4. Claude Code.
5. Prompt / Context / Reliability.
6. 2 mock exam, solo scenario-based.
7. Errori ricorrenti + esame.

## Formato esame e soglia

- Fonte terza: 60 item in 120 minuti, soglia scaled 720/1000 (da verificare).
- Obiettivo di preparazione: prenotare quando i mock nuovi danno stabilmente ≥85%.

## Prossimo passo

Raccogliere un corpus di 300-400 practice questions, poi costruire la sessione interattiva con storico errori, streak e mastery per dominio.
