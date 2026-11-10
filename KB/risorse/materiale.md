# Materiale di preparazione
> Risorse ufficiali e di terze parti per CCAR-F, con cosa contengono e quanto sono affidabili.
Aggiornato: 2026-11-10

## Ufficiale
- Exam Guide v0.1 (10 feb 2025): 30 task statement, 12 domande di esempio con spiegazioni, 4 esercizi pratici. Archiviata in `fonti/ccar-f-exam-guide-v0.1.pdf`. Il PDF porta la dicitura «Confidential Need to Know (NTK)», ma è pubblicato su S3 di Skilljar. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
- Exam Guide v1.0 (luglio 2026): esiste sulla Partner Academy; non l'ho ancora scaricata. (fonte: https://claude.termidy.com/ccar-f/)
- La guida rimanda a un **practice exam ufficiale** con spiegazioni dopo ogni risposta; il link viene fornito separatamente. (fonte: fonti/ccar-f-exam-guide-v0.1.pdf)
- Corsi ufficiali sulla Partner Academy: Claude Code in Action, Claude with the Anthropic API, Introduction to Model Context Protocol. (fonte: https://claude.termidy.com/ccar-f/)

## Terze parti (gratuite, non affiliate ad Anthropic)
| Sito | Contenuto | Note |
|---|---|---|
| https://www.ccafpreparation.com/ | 408 domande con spiegazione per ogni opzione (incluse le 12 ufficiali), mock da 60 a tempo o per scenario, drill degli errori, 385 flashcard con ripetizione spaziata, 5 cheat sheet, glossario, divergence log | Senza login. Basato su guida v1.0. La home in un altro punto dice 318 domande: numero da confermare |
| https://claude.termidy.com/ccar-f/ | 360 domande scritte da zero, lezioni per dominio | Senza login |
| https://claudearchitectcertification.com/exam-guide | Guida PDF 14 pagine, checklist, piano di 2 settimane | Senza email |

## Affidabilità
- Le risposte dei siti terzi vanno verificate contro la guida ufficiale e la documentazione Anthropic.
- Il corpus dei siti terzi è protetto da copyright.
- Banca ccafpreparation (408 domande): scaricata il 2026-11-10 in `fonti/ccafpreparation-bank-2026-11-10.json`. L'utente dichiara un permesso da accordo diretto. La banca resta solo in locale: niente remote e niente push. (fonte: richiesta utente in sessione 2026-11-10)
- Composizione della banca: 240 `enrichment`, 156 `lesson`, 12 `official-sample`. 28 domande sono a risposta multipla («Select two»). Le spiegazioni sono in inglese. (fonte: fonti/ccafpreparation-bank-2026-11-10.json)
- termidy: non scaricato. Il `robots.txt` vieta `/question_banks/` e non c'è accesso guest a CCAR-F.
