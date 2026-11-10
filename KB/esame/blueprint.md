# Blueprint: domini e task statement
> I 5 domini con i pesi e i 30 task statement della guida ufficiale, ognuno con la regola da ricordare.
Aggiornato: 2026-11-10

Fonte di tutto il file: fonti/ccar-f-exam-guide-v0.1.pdf, salvo dove indicato.

| Dominio | Peso | ≈ domande |
|---|---|---|
| 1 Agentic Architecture & Orchestration | 27% | 16 |
| 2 Tool Design & MCP Integration | 18% | 11 |
| 3 Claude Code Configuration & Workflows | 20% | 12 |
| 4 Prompt Engineering & Structured Output | 20% | 12 |
| 5 Context Management & Reliability | 15% | 9 |

## Dominio 1 — Agentic Architecture & Orchestration
- **1.1 Agentic loop**: continua se `stop_reason` è `"tool_use"`, termina se è `"end_turn"`. Aggiungi i tool result alla history. Anti-pattern: leggere segnali nel testo, cap di iterazioni come stop principale, testo dell'assistant come segnale di fine.
- **1.2 Coordinator-subagent**: hub-and-spoke. Tutta la comunicazione passa dal coordinator. I subagent hanno contesto isolato. Rischio: decomposizione troppo stretta → copertura incompleta. Il coordinator sceglie dinamicamente quali subagent invocare e ripete il ciclo finché la copertura basta.
- **1.3 Invocazione subagent**: si usa il tool `Task`; `allowedTools` deve includere `"Task"`. Il contesto va passato esplicitamente nel prompt. `AgentDefinition`: descrizione, system prompt, restrizioni tool. Parallelismo: più chiamate `Task` nella **stessa** risposta. Il prompt del coordinator dà obiettivi e criteri di qualità, non procedure passo-passo. Usa formati strutturati per separare contenuto e metadati (URL, pagine).
- **1.4 Enforcement e handoff**: per la compliance deterministica (es. verifica identità prima di un rimborso) usa gate programmatici, non il prompt: il prompt ha un tasso di errore non nullo. L'handoff all'umano include customer ID, root cause, importo, azione consigliata, perché l'umano non vede la trascrizione.
- **1.5 Hook**: `PostToolUse` normalizza i dati dei tool (timestamp Unix, ISO 8601, codici numerici) prima del modello. Un hook di intercettazione blocca le chiamate che violano la policy (es. rimborso > 500 $) e devia all'escalation. Hook = garanzia; prompt = probabilità.
- **1.6 Decomposizione**: prompt chaining (pipeline fissa) per review prevedibili; decomposizione dinamica per indagini aperte. Review grandi: un passo per file + un passo di integrazione cross-file.
- **1.7 Sessioni**: `--resume <session-name>` riprende una sessione con nome. `fork_session` crea rami indipendenti da una base comune. Se i tool result sono vecchi, meglio una sessione nuova con un riassunto strutturato. Alla ripresa, informa l'agente sui file cambiati.

## Dominio 2 — Tool Design & MCP Integration
- **2.1 Descrizioni dei tool**: sono il meccanismo principale di selezione. Includi formati di input, esempi, casi limite, confini rispetto ai tool simili. Rinomina o dividi i tool che si sovrappongono. Controlla che il system prompt non contenga parole chiave che spingono verso il tool sbagliato.
- **2.2 Errori strutturati MCP**: flag `isError`. Categorie: transient, validation, business, permission. Restituisci `errorCategory`, `isRetryable`, descrizione leggibile. Un errore generico ("Operation failed") impedisce il recupero. Distingui un errore di accesso da un risultato vuoto valido. Il subagent recupera localmente gli errori transienti e propaga solo quelli non risolvibili, con i risultati parziali.
- **2.3 Distribuzione dei tool**: troppi tool (18 invece di 4-5) peggiorano la selezione. Ogni agente riceve solo i tool del suo ruolo, più eventuali tool cross-role limitati (es. `verify_fact`). `tool_choice`: `"auto"`, `"any"` (deve chiamare un tool), forzato `{"type":"tool","name":"..."}`.
- **2.4 Server MCP**: `.mcp.json` (progetto, condiviso) vs `~/.claude.json` (utente, personale). Espansione delle variabili d'ambiente (`${GITHUB_TOKEN}`) per non committare segreti. I tool di tutti i server sono disponibili insieme. Le resource MCP espongono cataloghi (schemi DB, documentazione) e riducono le chiamate esplorative. Preferisci server community per integrazioni standard (es. Jira).
- **2.5 Tool built-in**: Grep cerca nel contenuto. Glob cerca per nome/percorso (es. `**/*.test.tsx`). Edit modifica con match univoco; se il match non è univoco usa Read + Write. Esplora in modo incrementale: Grep per i punti di ingresso, poi Read per seguire gli import.

## Dominio 3 — Claude Code Configuration & Workflows
- **3.1 CLAUDE.md**: gerarchia utente (`~/.claude/CLAUDE.md`, non condiviso), progetto (`.claude/CLAUDE.md` o root), directory. `@import` per moduli. `.claude/rules/` per regole per argomento. `/memory` mostra quali file sono caricati.
- **3.2 Comandi e skill**: `.claude/commands/` (progetto, versionato) vs `~/.claude/commands/` (personale). Skill in `.claude/skills/<nome>/SKILL.md` con frontmatter `context: fork` (contesto isolato), `allowed-tools`, `argument-hint`. Skill = on demand; CLAUDE.md = sempre caricato.
- **3.3 Regole per percorso**: `.claude/rules/*.md` con frontmatter `paths:` e glob. Si caricano solo quando modifichi file corrispondenti. Meglio delle CLAUDE.md di directory per convenzioni sparse (es. test in tutto il codice).
- **3.4 Plan mode vs esecuzione diretta**: plan mode per cambi grandi, più approcci validi, decisioni architetturali, molti file. Esecuzione diretta per cambi semplici e chiari. Explore subagent isola l'output verboso. Combina: pianifica, poi esegui.
- **3.5 Raffinamento iterativo**: 2-3 esempi concreti input/output quando la prosa è ambigua. Test prima, poi itera sui fallimenti. Interview pattern: fai porre domande a Claude. Problemi che interagiscono: un solo messaggio; problemi indipendenti: in sequenza.
- **3.6 CI/CD**: `-p`/`--print` per la modalità non interattiva. `--output-format json` + `--json-schema` per output strutturato. CLAUDE.md fornisce il contesto in CI. Una review indipendente è migliore della review nella stessa sessione che ha generato il codice. Nelle nuove esecuzioni passa i finding precedenti e chiedi solo quelli nuovi o aperti.

## Dominio 4 — Prompt Engineering & Structured Output
- **4.1 Criteri espliciti**: criteri categoriali specifici battono "sii conservativo" o "solo alta confidenza". Troppi falsi positivi distruggono la fiducia: disattiva temporaneamente le categorie rumorose. Definisci la severità con esempi di codice.
- **4.2 Few-shot**: la tecnica più efficace per formato coerente e casi ambigui. 2-4 esempi mirati che mostrano il ragionamento. Riduce le allucinazioni nell'estrazione da documenti vari.
- **4.3 Output strutturato**: `tool_use` + JSON schema elimina gli errori di sintassi, non quelli semantici. `"any"` se ci sono più schemi e il tipo di documento è ignoto. Forza un tool specifico per farlo eseguire per primo. Campi nullable per evitare valori inventati. Enum con `"unclear"` e `"other"` + campo di dettaglio.
- **4.4 Validazione e retry**: il retry include documento, estrazione fallita, errore specifico. Il retry non serve se l'informazione manca nella fonte. Campo `detected_pattern` per analizzare i falsi positivi. `calculated_total` accanto a `stated_total`; `conflict_detected`.
- **4.5 Batch**: Message Batches API: -50% di costo, fino a 24 h, nessuno SLA di latenza, niente tool calling multi-turn, `custom_id` per correlare. Adatto a job notturni, non a controlli bloccanti pre-merge. Reinvia solo i falliti per `custom_id`. Affina il prompt su un campione prima del volume.
- **4.6 Review multi-istanza**: l'auto-review nella stessa sessione è debole. Un'istanza indipendente trova più problemi. Review multi-pass: per file + integrazione. Confidenza per finding per instradare la review.

## Dominio 5 — Context Management & Reliability
- **5.1 Contesto lungo**: i riassunti progressivi perdono numeri, date, aspettative. "Lost in the middle": metti i punti chiave all'inizio, usa intestazioni. Blocco persistente "case facts" fuori dalla history riassunta. Taglia i tool result ai campi rilevanti. Gli agenti a monte restituiscono dati strutturati, non testo verboso.
- **5.2 Escalation**: escala se il cliente chiede un umano (subito), se la policy è ambigua o non copre il caso, se non fai progressi. Sentiment e confidenza auto-dichiarata non sono indicatori affidabili. Con più clienti corrispondenti chiedi altri identificativi. Se il caso è semplice e il cliente è frustrato, offri la soluzione; escala se insiste.
- **5.3 Propagazione errori**: contesto strutturato (tipo di errore, query, risultati parziali, alternative). Anti-pattern: errore nascosto come successo vuoto; terminare tutto per un solo errore; stato generico. Annota nella sintesi le lacune di copertura.
- **5.4 Esplorazione di codebase grandi**: il contesto degrada nelle sessioni lunghe. Usa file scratchpad, subagent per l'esplorazione verbosa, riassunti tra le fasi, manifest per il crash recovery, `/compact`.
- **5.5 Review umana e calibrazione**: l'accuratezza aggregata (97%) può nascondere segmenti deboli. Campionamento casuale stratificato anche sugli high-confidence. Confidenza per campo calibrata su set etichettati. Instrada a revisione umana i casi a bassa confidenza o contraddittori.
- **5.6 Provenienza**: mappa claim → fonte preservata fino alla sintesi. Dati in conflitto: riporta entrambi con la fonte. Richiedi date di pubblicazione per non scambiare differenze temporali per contraddizioni. Formato adatto al contenuto (tabelle per dati finanziari, prosa per news).
