# Analisi dei flussi pre-game e post-game

Data: 30 settembre 2026. Analisi statica della versione homeflow e riscontro sul log locale 15:37–15:50 e sulla schermata diagnostica 15:49:49. Il log precede l'ultima build: dimostra i problemi osservati, non il comportamento della homeflow dopo il rilascio. Nessuna modifica al comportamento applicativo in questa analisi.

## Flussi attuali

- Avvio: caricamento dati carte → lettura quest fresca (fino a 30 s dopo la navigazione) → reroll → eventuale verifica cambio account → navigazione della modalità → selezione mazzo → Play.
- Historic: Home → Play → Find Match → Play subtab → Historic → My Decks → scelta mazzo → verifica schermata → doppio clic di coda. Se fallisce riparte da Home dopo 5/15/30/60 s. Una chiave memorizza account e obiettivo quest per riutilizzare la selezione.
- Starter: ricerca Claim → recupero eventuale risultato → Play → Events → In Progress → evento → scelta mazzo → Play. La pagina evento è riconosciuta anche come recupero quando i passi iniziali non trovano i pulsanti.
- Fine partita: evento MatchCompleted → timer di 6 s → dismiss risultato → attesa di 10 s dopo ogni clic → attesa post-game di 15 s → coda → ricerca ricompense. Game programma inoltre un riavvio dopo 10 s, in parallelo al timer post-game, con guardie per differirlo.
- Cambio account: decisione quest/vittorie/tempo → logout/login → aggiornamento identità e quest → navigazione → attesa di circa 5 s → riavvio coda.

## Evidenza temporale

Nel log del 30 settembre:

| Evento | Ora |
|---|---|
| Inizio dismiss risultato | 15:41:15.852 |
| MainNav caricata | 15:41:18.240 |
| Dismiss confermato | 15:41:26.331 |
| Ripresa coda | 15:41:41.384 |
| Clic Claim Historic | 15:41:41.786 |

Sono circa 26 s dall'inizio dismiss al Claim. I 15 s aggiuntivi sono un margine separato dai 10 s richiesti dopo Victory/Defeat. MainNav caricata non prova, da sola, che il popup sia già cliccabile.

Nello stesso log, i tentativi di Play fra 15:38:22 e 15:39:13 distano circa 7,27 s: il ciclo non costa solo i 3 s del suo sleep; include ricerca immagini e doppio clic. I fallimenti Historic arrivano a un tentativo al minuto, mentre vengono ripetute lettura quest e righe di log ogni circa 3,3 s.

## Priorità 1: correttezza e continuità

1. **Stato UI unico con evidenze recenti.** `state/state_machine.py:get_state_from_playerlog` usa anche parole generiche come “historic” presenti nella coda del log. Uno stato può sopravvivere alla schermata che lo aveva generato. Gli override visivi in `actions/actions.py` risolvono alcuni passaggi, ma altre guardie continuano a consultare il solo log. Separare stato di partita, pagina e popup; associare timestamp/account/match alle evidenze. Le pagine devono essere riconosciute visivamente, mentre gli eventi recenti governano ingresso e uscita dal match.

2. **Un coordinatore per post-game, coda e cambio account.** `dismiss_end_screen`, `_maybe_post_match_action`, `_handle_main_nav_loaded` e `Game._restart_game` possono programmare o richiamare il seguito. Esistono lock utili contro doppie code, ma i timer post-game non hanno un identificatore di sessione/match e ogni chiamata anticipata può crearne un altro. Il log mostra due richieste di ripresa nello stesso decimo di secondo. Usare un solo avanzamento pianificato, cancellabile, con identificatore della sessione: i callback vecchi devono diventare inerti dopo Stop, nuovo match o cambio account.

3. **Reconnect disponibile anche durante il match.** `_handle_disconnect_overlay` è chiamato soltanto da `_queue_spam_loop`, fermato all'arrivo dello stato di gioco. Collegarlo a una supervisione UI periodica indipendente dalla coda, con precedenza sugli altri input. Dopo il clic verificare la scomparsa del popup e distinguere ripresa della partita da ritorno ai menu. Conservare un intervallo fra tentativi e un limite, evitando clic concorrenti.

4. **Conferma della transizione dopo Play.** `start_game_from_home_screen` esegue due pressioni separate da 1 s senza verificare il risultato fra loro. Passare a un clic e attesa di evidenza di matchmaking; ritentare soltanto se il pulsante iniziale è ancora visibile e nessuna coda è iniziata. La cache del mazzo deve autorizzare il riuso della scelta, non certificare che la schermata corrente sia pronta: `_ensure_historic_selection` restituisce subito True se la chiave coincide. Richiedere una verifica leggera della pagina prima del clic finale.

## Priorità 2: ridurre i ritardi senza anticipare i clic

5. **Post-game basato su avanzamenti osservati.** Mantenere i 10 s dopo un clic su Victory/Defeat, come richiesto. Terminati i 10 s, riconoscere risultato, ricompensa, Home, evento o caricamento. Sostituire i successivi 15 s incondizionati con attesa della schermata stabile, con scadenza di recupero. Il risparmio potenziale è fino a circa 15 s quando la UI è già pronta; va misurato, non garantito per ogni match.

6. **Claim condiviso fra modalità.** Oggi Starter usa Claim più esclusione della pagina evento e attende 1 s; Historic richiede titolo Reward più Claim e blocca i tentativi per 5 s, riprovando sul ciclo da 3 s. Entrambi dichiarano gestito il popup dopo il clic senza confermarne subito la scomparsa. Unificare riconoscimento, attesa di stabilità del pulsante, clic singolo, verifica di chiusura e retry distanziato. La scomparsa del popup deve liberare subito la navigazione; un Claim rimasto visibile deve mantenere il controllo degli input. Non assimilare la semplice presenza di MainNav alla chiusura delle ricompense.

7. **Ricerca immagini normalizzata subito.** `_locate_image_center_in_scaled_arena_region` prova prima un template non scalato fino a 1 s e solo dopo normalizza la regione. A 1366×768 il primo tentativo frequentemente non può trovare il template 1920×1080; il log mostra questo costo anche su Home. Scegliere il matcher dalla geometria, riutilizzare la cattura nello stesso ciclo e conservare la geometria finché la finestra non cambia. Verificare con immagini offline a entrambe le risoluzioni e finestre spostate.

8. **Riprendere dal punto raggiunto.** Historic riparte da Home a ogni errore; Starter tenta Play/Events prima di recuperare la pagina evento. Riconoscere prima la pagina corrente e saltare i passi già conclusi. Separare attesa di animazione, template assente, mazzo mancante e stato incoerente: solo gli errori persistenti meritano il backoff di 60 s. Una transizione in corso deve avere polling breve e una scadenza propria.

9. **Una lettura quest per revisione dei dati.** Startup, reroll, cambio account e navigazione hanno controlli sovrapposti. `_quest_deck_target` torna al parser anche durante il backoff Historic. Riutilizzare uno snapshot valido per account e offset del log, inclusa la lista vuota; invalidarlo su reroll, cambio account o nuovo blocco quest. Mantenere i confini di freschezza che impediscono di usare le quest dell'account precedente. Valutare la rotazione e il mazzo una sola volta sullo snapshot aggiornato.

## Sequenza proposta

Prima stato e coordinamento dei timer; poi Play con conferma, reconnect e Claim condiviso; infine riduzione attese, matcher e cache. Ridurre soltanto gli sleep adesso lascerebbe intatte le cause dei blocchi.

Flusso obiettivo: risultato → attesa obbligatoria dopo il clic → ricompense verificate → aggiornamento quest/rotazione → pagina corretta → mazzo verificato → Play singolo → matchmaking confermato → partita. Il reconnect può interrompere qualsiasi fase e riprende dal punto osservato dopo il recupero.

## Verifica richiesta prima del rilascio

- Test offline dell'intero percorso, non soltanto dei singoli passi: stato Historic obsoleto su Home/Recently Played; Starter e Historic con/senza ricompensa; Claim lento o ignorato; matchmaking lento; reconnect in coda e in partita; cambio account; Stop durante attese e riavvio rapido.
- Stesse prove a 1366×768 e 1920×1080, con origine finestra diversa.
- Timer simulati: nessun clic nei 10 s obbligatori; callback della sessione precedente senza effetti; un solo proprietario degli input.
- Misurare risultato→Claim, Claim→Play e Play→match separatamente: il matchmaking remoto non va contato come rallentamento del bot. Registrare stato prima/dopo, motivo dell'attesa e tentativo, limitando i messaggi identici.
- Breve prova reale dopo build: i test sintetici non dimostrano la durata delle animazioni o l'accettazione del clic da parte di Arena.

Questa analisi non include modifiche alle decisioni di gioco o al percorso di dichiarazione degli attaccanti.
