# Olivicoltura Digital Control

Dashboard interattiva in Python per monitorare le prestazioni di un'azienda olivicola: resa, costi e ricavi, meteo, fabbisogno irriguo, rischio parassiti e qualità, con KPI e grafici che si aggiornano in automatico.

Progetto sviluppato come **Project Work di laurea** in Informatica per le Aziende Digitali (L-31), Università Telematica Pegaso.
Tema: *La digitalizzazione dell'impresa*. Traccia: *Sviluppo di una dashboard in Python per l'analisi delle prestazioni aziendali nel settore primario*.


## Cosa fa

- Mostra **KPI e grafici interattivi** divisi in tre schede:
  - **Economia**: resa e olio per ettaro, ricavi, costi, profitto, prezzo di piazza.
  - **Cura e Qualità**: contesto meteo, fabbisogno irriguo, stress idrico, vigoria, indice di maturazione, interventi colturali, indice di qualità.
  - **Previsioni e Trattamenti**: pressione della mosca olearia (con semaforo), rischio di malattie fungine, alert sui trattamenti.
- Permette di filtrare per **cultivar** (Carolea, Sinopolese, Ottobratica, Coratina, Leccino), **finestra temporale** (da 7 giorni a 5 anni), **piazza di mercato** e **tipo di olio** (DOP, EVO, lampante).
- Si **aggiorna ogni 30 secondi** per simulare un flusso continuo di dati.
- Usa **dati meteo reali** (temperatura, umidità, precipitazioni) dall'API gratuita [Open-Meteo](https://open-meteo.com/) per le coordinate configurate. Se l'API non è raggiungibile, passa automaticamente a dati simulati.

## Come funziona

Il progetto ha un'architettura modulare che separa la generazione dei dati dalla loro visualizzazione, così il simulatore può essere sostituito in futuro da fonti di dati reali senza modificare la dashboard.

| File | Ruolo |
|---|---|
| `main.py` | Punto di ingresso: avvia il server Dash |
| `dashboard.py` | Layout, KPI, grafici e callback (Dash + Plotly) |
| `simulator.py` | Generazione dei dati agronomici ed economici con modelli semplificati |
| `data_sources.py` | Recupero del meteo reale da Open-Meteo, con cache e fallback |
| `config.py` | Coordinate dell'oliveto e opzioni sull'uso dei dati reali |
| `requirements.txt` | Dipendenze Python |

## Tecnologie

Python · Dash · Plotly · pandas · NumPy · requests

## Come avviarla

Requisiti: Python 3.9 o superiore.

```bash
# 1. Clona il repository
git clone https://github.com/FrancescoPentifallo/Tesi-di-Laurea-L-31-Olivicoltura-Digital-Control-Pentifallo-Francesco.git
cd Tesi-di-Laurea-L-31-Olivicoltura-Digital-Control-Pentifallo-Francesco

# 2. (Consigliato) crea un ambiente virtuale
python -m venv .venv
source .venv/bin/activate        # su Windows: .venv\Scripts\activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Avvia la dashboard
python main.py
```

Poi apri nel browser **http://127.0.0.1:8050**.

## Configurazione

In `config.py` puoi modificare:

- `LATITUDINE` e `LONGITUDINE`: posizione dell'oliveto (di default Gioia Tauro, Calabria).
- `USA_DATI_REALI`: imposta `False` per usare solo dati simulati, anche senza connessione internet.

## Limiti noti

- Quasi tutti i dati sono **simulati**: solo il meteo (temperatura, umidità, precipitazioni) viene da una fonte reale. Rese, costi, indici di rischio e qualità sono calcolati con formule semplificate a regole, non con modelli statistici o di machine learning, e vanno letti come **indicativi**.
- I prezzi di mercato per piazza e tipo di olio sono **valori fissi di esempio**, non quotazioni reali.
- Lo storico meteo reale è limitato agli ultimi 90 giorni; per periodi più lunghi i dati sono simulati.
- Lo storico viene rigenerato a ogni aggiornamento, quindi i valori cambiano da un ciclo all'altro.

## Possibili sviluppi

- Salvare i dati su un database o su file, per avere uno storico stabile.
- Collegare sensori, stazioni meteo o sistemi gestionali aziendali al posto del simulatore.
- Usare quotazioni di mercato reali per i prezzi.
- Aggiungere funzioni predittive con modelli statistici o di machine learning.
- Aggiungere test automatici e una gestione più completa degli errori.

## Autore

**Francesco Pentifallo**
[LinkedIn](https://www.linkedin.com/in/francesco-pentifallo-48348b329/) · [GitHub](https://github.com/FrancescoPentifallo)
