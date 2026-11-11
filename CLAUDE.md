# cert_claude_CCAR-F

<!-- new-prj: struttura creata il 2026-11-10. Queste regole valgono in ogni sessione; non serve richiamare la skill. -->

## Contesto

Obiettivo: superare l'esame Claude Certified Architect – Foundations (CCAR-F) in 7 giorni, con un trainer interattivo adattivo (domande scenario-based, ripetizione degli errori, mastery per dominio). Piano, blueprint e materiale: `target.md`. Stato: banca di 408 domande in `fonti/`, trainer pronto in `trainer/`. Punto di ripresa: `KB/progetto/azioni.md`.

**Trainer** (`trainer/ccar.py`, solo stdlib):
- Web (simula l'esame): `uv run trainer/ccar.py serve` → http://127.0.0.1:8765
- Chat: `uv run trainer/ccar.py next [--domain N]`, poi `answer <QID> <LETTERE>`; `stats`, `missed`. Output JSON. In chat mostra la domanda in inglese senza la soluzione e spiega in italiano dopo la risposta.
- Test: `cd trainer && uv run --quiet python -m unittest -v test_ccar`
- Traduzione IT delle spiegazioni: `uv run --with mlx-lm trainer/translate.py --model <percorso snapshot Qwen3.5-9B>` (ripartibile). Uscita in `trainer/data/` (solo locale).
- Stato utente: `trainer/state/` (`attempts.jsonl` append-only). Le regole italiane vengono da `KB/esame/blueprint.md`: non cambiarne il formato delle righe `- **N.N Titolo**: regola`.
- La banca in `fonti/` è solo locale: non fare push.

## Struttura

| Percorso | Contenuto | Chi scrive |
|---|---|---|
| `_input/` | Casella di ingresso: materiale grezzo da elaborare. Dopo l'elaborazione resta **vuota** | Utente, chief-of-staff |
| `minute/AAAA.MM.GG/` | Una cartella per giorno di riunione: trascrizioni `.md`, foto, screenshot | Utente |
| `fonti/` | Archivio dei file di `_input/` da conservare in originale | Assistente |
| `KB/<tema>/<argomento>.md` | Conoscenza distillata, un argomento per file | Assistente |
| `KB/fonti.md` | Journal di tutte le fonti elaborate e del loro esito | Assistente |
| `KB/prossimi-incontri.md` | Agenda: prossimi incontri e scadenze. Generato, non modificarlo | chief-of-staff |
| `inbound-rule.md` | Regole per la posta in arrivo, elaborata in automatico | Utente |
| `CLAUDE.md` | Questo file: contesto, regole, indice della KB | Assistente |
| `trainer/` | Trainer adattivo: motore, CLI, UI web, test; `state/` = risultati dell'utente | Assistente |

## Regole

### Istruzioni globali (richiamo)
Valgono le istruzioni globali (`~/.claude/CLAUDE.md`, `~/.copilot/copilot-instructions.md`). In particolare:
- **Protocollo Cerniera**: con `.protocolloCerniera` presente la produzione si usa solo in lettura, con il controllo del revisore prima di ogni accesso esterno.
- **Segreti di sistemi esterni**: non leggerli mai da solo. Mostra il comando e lascia decidere l'utente.
- **Git**: nessun riferimento a strumenti AI nei commit.

### Fonti
- **`_input/`** è una casella di ingresso: ogni file presente è da elaborare. Dopo l'elaborazione va sempre svuotata (vedi passo 7).
- **`minute/`** e **`fonti/`** sono memoria storica: non modificare, rinominare, spostare o cancellare i file. Una minuta è nuova se il suo percorso non è in `KB/fonti.md`.
- All'inizio di una sessione, o quando l'utente lo chiede, controlla se ci sono fonti nuove: se ci sono, elencale e proponi di elaborarle.
- La posta in arrivo segue anche [inbound-rule.md](inbound-rule.md).

### Elaborazione di una fonte nuova
1. Leggila tutta. Guarda anche foto e screenshot e trascrivi il testo rilevante che contengono.
2. Estrai **ogni dettaglio rilevante**: fatti, numeri, date, nomi e ruoli, requisiti, vincoli, decisioni (chi, quando), azioni (chi, cosa, entro quando), punti aperti, rischi, termini e sigle.
3. Assegna ogni dettaglio a un tema. Aggiorna il file KB esistente sull'argomento, oppure creane uno nuovo se non c'è. Se il tema di una fonte non è chiaro, non indovinare: lascia la fonte in `_input/` e indicala in «Cosa manca».
4. Accanto a ogni dettaglio indica la fonte con il percorso definitivo: `(fonte: minute/2026.11.03/call-cliente.md)`, `(fonte: fonti/contratto.pdf)`, oppure, per un file di `_input/` eliminato, `(fonte: offerta.docx, eliminato — vedi KB/fonti.md)`.
5. Se un'informazione contraddice la KB, non sovrascrivere in silenzio: tieni entrambe le versioni con data e fonte e marcale `⚠️ contrasto`.
6. Registra la fonte nel journal `KB/fonti.md`: nome del file, data, sintesi in una riga, file KB aggiornati, esito (`minute`, `archiviato in fonti/<nome>` oppure `eliminato`).
7. Solo per i file di `_input/`, dopo aver scritto KB e journal, svuota la cartella (tranne `.gitkeep`) senza chiedere conferma:
   - **archivia in `fonti/`** i file da conservare in originale perché la KB da sola non basta: contratti, offerte, specifiche e documenti ufficiali, diagrammi, fogli di calcolo con dati, testi troppo ampi da distillare per intero, file che andranno ricondivisi. In caso di nome già presente, anteponi la data `AAAA-MM-GG_`;
   - **elimina** tutti gli altri, compreso il rumore (loghi, firme, immagini inline): il loro contenuto rilevante è già nella KB;
   - lascia in `_input/` solo i file che non si riescono a leggere (formato non supportato, protetto da password) e quelli con tema non chiaro (passo 3).
8. Aggiorna l'[Indice KB](#indice-kb) e il [Contesto](#contesto): se è ancora il testo segnaposto, sostituiscilo con quanto emerso dalla fonte. Le scadenze trovate nelle fonti vanno in `KB/progetto/azioni.md`, non in `KB/prossimi-incontri.md`.
9. Chiudi con il recap del progetto, non con un diario. Il recap ha due blocchi:
   - **Cosa è cambiato**: i fatti nuovi entrati in KB, con fonte, e i contrasti ⚠️;
   - **Cosa manca**: domande aperte, segreti trovati, fonti lasciate in `_input/` e il motivo.

   Il resoconto di cosa hai letto, aggiornato o spostato sta solo in `KB/fonti.md`.

Le minute restano nella loro cartella del giorno; nella KB finisce il contenuto, organizzato per tema, non il resoconto della riunione.

### Flusso automatico
Nelle sessioni interattive le domande all'utente sono ammesse. In un flusso automatico (posta in arrivo, batch) non chiedere conferme: applica queste regole e metti nel recap tutto ciò che richiede l'utente.

### Organizzazione della KB
- Cartelle per tema e file per argomento, con nomi in kebab-case (es. `KB/architettura/integrazione-sap.md`).
- Temi trasversali da creare solo quando serve: `KB/progetto/persone.md`, `decisioni.md`, `azioni.md` (aperte e chiuse), `glossario.md`.
- Ogni file KB inizia così:
  ```markdown
  # <Argomento>
  > <sintesi in 1–2 righe: è la stessa che compare nell'indice>
  Aggiornato: AAAA-MM-GG
  ```
- Se un file supera circa 300 righe, dividilo in sotto-argomenti e aggiorna l'indice.
- Scrivi la KB in stile ASD-STE100 all'80%: un fatto per frase, frasi brevi in forma attiva, un solo termine per ogni concetto (registralo in `glossario.md`). Copia esatti nomi, cifre, date e codici. Mantieni condizioni e incertezze: «forse» resta «forse», «da confermare» resta «da confermare».

### Consultazione (contesto leggero)
- Per rispondere a domande sul progetto parti dall'[Indice KB](#indice-kb) e apri **solo** i file KB pertinenti.
- Per date di incontri e scadenze leggi `KB/prossimi-incontri.md` e `KB/progetto/azioni.md`.
- Non leggere `minute/` o `fonti/` per intero: torna a una fonte solo per verificare un dettaglio o se la KB non lo copre.
- Nelle risposte cita il file KB o la fonte da cui viene l'informazione.
- Se la risposta non è nella KB, dillo invece di dedurla.

### Manutenzione di questo file
- Tienilo breve: qui stanno solo contesto, regole e indice, i dettagli stanno nella KB.
- Se l'indice supera circa 40 righe, qui lascia una riga per tema e sposta l'elenco dei file in `KB/<tema>/_indice.md`.

### Riservatezza
- Non copiare nella KB segreti (password, token, chiavi): scrivi solo «segreto presente in `<fonte>`» e segnalalo nel recap.
- Non creare remote git e non fare push senza una richiesta esplicita.

## Indice KB

<!-- Mantenuto dall'assistente: un file (o un tema) per riga, con una sintesi sufficiente a capire quando aprirlo. -->

| File | Contiene |
|---|---|
| `KB/fonti.md` | Journal delle fonti elaborate e del loro esito (archiviate o eliminate) |
| `KB/prossimi-incontri.md` | Prossimi incontri e scadenze (generato dal chief-of-staff) |
| `KB/esame/formato.md` | Formato esame: 60 domande, 120 min, soglia 720, 6 scenari, retake, fuori programma |
| `KB/esame/blueprint.md` | 5 domini con pesi e 30 task statement con la regola da ricordare |
| `KB/esame/divergenze.md` | Guida d'esame vs documentazione attuale: quale risposta dare |
| `KB/progetto/azioni.md` | Checkpoint e punto di ripresa, azioni aperte del piano di 7 giorni |
| `KB/risorse/materiale.md` | Risorse ufficiali e gratuite di terze parti, affidabilità, copyright |
