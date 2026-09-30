# GrindingStation 1.1 — sviluppo

Baseline pubblicata: `v1.0.0` (main). Ramo: `development/1.1`.
Versione applicazione: `1.1.0-dev`. Il collegamento desktop usa la 1.0.0.

## Primo incremento

- [x] Eliminare gli stati derivati da parole generiche nei payload.
- [x] Dare precedenza cronologica a MainNav, cambi scena, inizio e fine partita.
- [x] Elaborare solo il nuovo evento nel tracker, conservando lo stato durante la rotazione della coda diagnostica.
- [x] Saltare il tentativo a scala nativa quando Arena non è 1920×1080.
- [x] Aggiungere regressioni offline per transizioni e scelta del matcher.
- [x] Isolare i probe dei popup e il recupero input nei test di rotazione/acknowledgement.

Riscontro sul bundle locale del blocco 15:49:49: il parser nuovo ricava Home,
mentre lo stato registrato era Historic. I 17 test mirati di questo incremento
passano. Build locale separata: `GrindingStation-1.1.0-dev.exe`, non pubblicata
come release e non collegata al desktop.

Suite completa: 950 test eseguiti, 948 passati, 1 saltato e il solo fallimento
preesistente sul budget dei blocchi. Dopo l'isolamento finale del test di
acknowledgement, i 17 test mirati sono stati rieseguiti con successo.

Suite completa aggiornata: 956 test, 953 passati, 1 saltato e 2 fallimenti nei test combat (`test_combat_blocks...time_budget...` e `test_combat_shadow...decision_is_recorded...`). I due test statici legacy dei report e il nuovo controllo Historic passano. I 101 test mirati sui flussi post-game, Claim, Historic, reconnect e rotazione passano. Build locale aggiornata: `GrindingStation-1.1.0-dev.exe`; il desktop resta sulla 1.0.0.

## Incrementi successivi

- [x] Coordinatore unico dei timer post-game con cancellazione e identità sessione/match.
- [x] Clic Play singolo con conferma ingresso in matchmaking e verifica pagina anche con mazzo in cache.
- [x] Reconnect indipendente dalla coda, operativo anche durante il match.
- [x] Claim condiviso, conferma di scomparsa e retry distanziati.
- [x] Sostituire i 15 s post-game aggiuntivi con verifica della UI pronta, mantenendo i 10 s obbligatori dopo Victory/Defeat.
- [x] Ricontrollare a schermo la pagina Historic prima di riusare la selezione del mazzo memorizzata.
- [ ] Ripresa navigazione dalla pagina corrente e backoff distinto per tipo di errore.
- [ ] Snapshot quest per account/revisione e log meno ripetitivi.
- [ ] Prove complete a 1366×768 e 1920×1080, Stop/Start rapido e rotazione account.
- [ ] Build candidata e verifica reale prima della release 1.1.

Dettagli ed evidenze: [flow-optimization.md](flow-optimization.md).
Il fallimento preesistente del test sul budget dei blocchi resta registrato nelle note della 1.0; non riguarda questo primo incremento.
