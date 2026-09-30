# GrindingStation 1.1 — sviluppo

Baseline pubblicata: `v1.0.0` (`main`). Ramo di sviluppo: `development/1.1`.
Versione locale: `1.1.0-dev`; il collegamento desktop resta sulla 1.0.0.

## Completato

- Stati di pagina derivati da transizioni esplicite e cronologiche nel log; gli
  eventi incrementali continuano a funzionare quando la coda diagnostica ruota.
- Matcher normalizzato alla scala della finestra. Le prove sintetiche passano a
  1366×768 e 1920×1080 con Arena traslata sul desktop.
- Play a clic singolo con riscontro dello stato; Historic verifica di nuovo la
  schermata e riprende dalla pagina raggiunta senza forzare Home.
- Backoff breve per transizioni e backoff progressivo per problemi persistenti
  di navigazione/selezione mazzo.
- Snapshot quest isolato per account e revisione del log, comprese le liste
  vuote; i consumatori ricevono copie per non mutare i dati in cache.
- Coordinatore cancellabile post-game per sessione/partita, attesa stabile delle
  schermate, 10 secondi dopo Victory/Defeat e Claim condiviso Starter/Historic.
- Supervisione Reconnect indipendente dalla coda, serializzata con la
  navigazione e con input di gioco sospesi fino al nuovo stato della partita;
  riconosce anche Retry con etichetta diversa sullo stesso pulsante.
- Isolamento dei test da probe/click sul desktop e aggiornamento delle note di
  sviluppo e changelog.

## Verifica locale

- 171 test mirati: passati, inclusi quest, Historic, reward, reconnect/Retry,
  rotazione account e prove del matcher alle due dimensioni.
- Regressione Retry/Reconnect verificata a 1366×768 e 1920×1080.
- Suite completa prima del fix Retry: 961 test, 959 passati, 1 saltato e 1
  fallimento combat noto. Dopo il fix: 962 test, 959 passati, 1 saltato e 2
  fallimenti combat (`test_combat_blocks...time_budget...` e
  `test_combat_shadow...decision_is_recorded...`); nessuno riguarda Reconnect.
- Build di prova: `GrindingStation-1.1.0-dev.exe`; non è una release e non è
  collegata al desktop.
- `git diff --check` e compilazione Python dei moduli modificati.

## Prima della release 1.1

- [ ] Prova reale con Arena a 1366×768 e 1920×1080: ingresso in partita,
  ricompense, Claim, rotazione account e Reconnect.
- [ ] Verificare Stop/Start mentre sono attivi attesa Claim, timer post-game e
  monitor Reconnect.
- [ ] Confermare i tempi reali di transizione e matchmaking dai log della prova.

Queste prove richiedono una sessione reale di Arena; la verifica automatica usa
finestre e schermate sintetiche e non sostituisce il test interattivo.
Il fallimento del test combat è indipendente dai flussi 1.1 e resta registrato
come problema preesistente.
