"""
Modulo per simulare dati agricoli (temperatura, umidità, precipitazioni,
quantità raccolto, tempi di crescita, costi e prezzi).
Supporta integrazione con dati meteorologici reali da API esterne.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# Import per dati reali
try:
    from data_sources import ottieni_meteo_reale, ottieni_storico_meteo_openmeteo
    DATI_REALI_DISPONIBILI = True
except ImportError:
    DATI_REALI_DISPONIBILI = False
    print("data_sources.py non trovato, usando solo dati simulati")

# Configurazione uso dati reali (può essere sovrascritta da config.py)
try:
    from config import LATITUDINE, LONGITUDINE, USA_DATI_REALI, OPENWEATHER_API_KEY, PREFER_OPENMETEO
    # Aggiorna anche data_sources se possibile
    try:
        import data_sources
        data_sources.LATITUDINE = LATITUDINE
        data_sources.LONGITUDINE = LONGITUDINE
    except:
        pass
except ImportError:
    # Valori di default se config.py non esiste
    USA_DATI_REALI = True
    OPENWEATHER_API_KEY = None
    PREFER_OPENMETEO = True

# Lista delle colture di olivo disponibili
COLTURE = [
    "Carolea",
    "Sinopolese",
    "Ottobratica",
    "Coratina",
    "Leccino",
]

# Parametri di simulazione configurabili
PARAMETRI_SIMULAZIONE = {
    "temperatura_base": 20.0,       # Temperatura base in gradi Celsius
    "umidita_base": 60.0,           # Umidità base in percentuale
    "variazione_temperatura": 5.0,  # Variazione massima temperatura
    "variazione_umidita": 15.0,     # Variazione massima umidità
}

# Parametri specifici per culture di olivo
CULTIVAR_PARAM = {
    "Carolea": {
        "temp_ottimale": 23,
        "umidita_ottimale": 60,
        "produzione_base_kg_ha": 5500,
        "densita_alberi_ha": 280,
        "estrazione_olio": 0.19,
    },
    "Sinopolese": {
        "temp_ottimale": 22,
        "umidita_ottimale": 62,
        "produzione_base_kg_ha": 5200,
        "densita_alberi_ha": 300,
        "estrazione_olio": 0.18,
    },
    "Ottobratica": {
        "temp_ottimale": 21,
        "umidita_ottimale": 65,
        "produzione_base_kg_ha": 5000,
        "densita_alberi_ha": 260,
        "estrazione_olio": 0.20,
    },
    "Coratina": {
        "temp_ottimale": 22,
        "umidita_ottimale": 58,
        "produzione_base_kg_ha": 6000,
        "densita_alberi_ha": 320,
        "estrazione_olio": 0.21,
    },
    "Leccino": {
        "temp_ottimale": 21,
        "umidita_ottimale": 60,
        "produzione_base_kg_ha": 4800,
        "densita_alberi_ha": 250,
        "estrazione_olio": 0.17,
    },
}


def genera_temperatura(temperatura_base=None):
    """
    Genera una temperatura simulata con variazioni giornaliere realistiche.
    
    Returns:
        float: Temperatura in gradi Celsius
    """
    if temperatura_base is None:
        temperatura_base = PARAMETRI_SIMULAZIONE["temperatura_base"]
    
    # Simula variazioni giornaliere + stagionali + casualità
    ora_corrente = datetime.now().hour
    variazioni_giorno = 3 * np.sin(2 * np.pi * ora_corrente / 24)  # Variazione durante il giorno
    variazione_casuale = np.random.normal(0, PARAMETRI_SIMULAZIONE["variazione_temperatura"] / 3)
    
    temperatura = temperatura_base + variazioni_giorno + variazione_casuale
    return round(temperatura, 1)


def genera_umidita(umidita_base=None):
    """
    Genera un valore di umidità simulato con variazioni realistiche.
    
    Returns:
        float: Umidità in percentuale (0-100)
    """
    if umidita_base is None:
        umidita_base = PARAMETRI_SIMULAZIONE["umidita_base"]
    
    # Umidità varia in modo più lento rispetto alla temperatura
    variazione_casuale = np.random.normal(0, PARAMETRI_SIMULAZIONE["variazione_umidita"] / 3)
    umidita = umidita_base + variazione_casuale
    
    # Limita tra 0 e 100
    umidita = max(0, min(100, umidita))
    return round(umidita, 1)


def genera_precipitazioni():
    """
    Genera un valore di precipitazioni simulato (pioggia).
    La maggior parte dei giorni non piove, occasionalmente piove molto.
    
    Returns:
        float: Precipitazioni in mm
    """
    # 70% probabilità di non piovere
    if random.random() < 0.7:
        return 0.0
    
    # Quando piove, varia tra 0.5 e 25 mm
    precipitazioni = np.random.exponential(5.0)
    return round(min(precipitazioni, 25.0), 1)


def calcola_efficienza_colturale(coltura, temperatura, umidita, precipitazioni):
    """Restituisce un coefficiente di efficienza 0-1 rispetto alle condizioni ottimali del cultivar."""
    param = CULTIVAR_PARAM.get(coltura, CULTIVAR_PARAM["Carolea"])
    temp_opt = param["temp_ottimale"]
    umidita_opt = param["umidita_ottimale"]

    efficienza_temp = 1 - abs(temperatura - temp_opt) / 18
    efficienza_umidita = 1 - abs(umidita - umidita_opt) / 35
    effetto_pioggia = 1.0 if precipitazioni < 12 else max(0.5, 1 - (precipitazioni - 12) / 35)

    return max(0.25, min(1.0, (efficienza_temp + efficienza_umidita) / 2 * effetto_pioggia))


def calcola_tempo_crescita(coltura, temperatura):
    """
    Calcola il tempo di crescita basato sulla temperatura.
    Temperature troppo basse o alte aumentano i tempi.
    
    Args:
        coltura: Nome della coltura
        temperatura: Temperatura corrente
    
    Returns:
        int: Giorni di crescita rimanenti
    """
    tempo_base = 240  # giorni medi da fioritura a raccolta per olivo
    temp_ottimale = 22
    moltiplicatore = 1 + max(0, abs(temperatura - temp_ottimale) - 5) / 60
    tempo = int(tempo_base * moltiplicatore)
    return max(120, tempo)


def calcola_costi(coltura, quantita_raccolto):
    """
    Calcola i costi di produzione basati sulla coltura e quantità.
    
    Args:
        coltura: Nome della coltura
        quantita_raccolto: Quantità raccolta in kg
    
    Returns:
        float: Costi totali in euro
    """
    costo_per_kg = 0.65  # euro/kg olive raccolte
    variabilita = np.random.normal(1.0, 0.08)
    costi_totali = quantita_raccolto * costo_per_kg * variabilita
    return round(max(0, costi_totali), 2)


def calcola_prezzo_vendita(coltura):
    """
    Calcola il prezzo di vendita per kg della coltura.
    
    Args:
        coltura: Nome della coltura
    
    Returns:
        float: Prezzo per kg in euro
    """
    param = CULTIVAR_PARAM.get(coltura, CULTIVAR_PARAM["Carolea"])
    prezzo_kg = 0.95  # prezzo medio olive frangitura
    premium = (param["estrazione_olio"] - 0.18) * 10  # piccoli premi per resa in olio
    variazione_mercato = np.random.normal(1.0, 0.05)
    prezzo_finale = prezzo_kg * (1 + premium) * variazione_mercato
    return round(max(0.45, prezzo_finale), 2)


def stadio_fenologico(temperatura, mese):
    """Stima semplice dello stadio fenologico in base a temperatura media e periodo."""
    if mese in (2, 3):
        return "Germogliamento"
    if mese in (4, 5):
        return "Fioritura"
    if mese in (6, 7):
        return "Allegagione"
    if mese in (8, 9):
        return "Invaiatura"
    if mese in (10, 11):
        return "Maturazione"
    return "Riposo vegetativo"


def calcola_fabbisogno_idrico(temperatura, umidita, stadio):
    """Calcola fabbisogno irriguo giornaliero semplificato (mm)."""
    base = 2.5 if stadio in ("Riposo vegetativo", "Germogliamento") else 4.0
    if stadio in ("Allegagione", "Invaiatura", "Maturazione"):
        base = 5.5
    stress_termico = max(0, temperatura - 28) * 0.25
    deficit_umidita = max(0, 65 - umidita) * 0.05
    return round(base + stress_termico + deficit_umidita, 1)


def pressione_mosca(temperatura, umidita):
    """Indice 0-100 della pressione della mosca olearia."""
    score = 0
    if 18 <= temperatura <= 28:
        score += 50
    elif 15 <= temperatura < 18 or 28 < temperatura <= 32:
        score += 30
    score += max(0, (umidita - 55) * 0.8)
    return round(min(100, score), 1)


def calcola_maturazione_indice(stadio, temperatura):
    """Indice 0-10 di maturazione (maturity index semplificato)."""
    base = {
        "Riposo vegetativo": 0.5,
        "Germogliamento": 1.5,
        "Fioritura": 2.5,
        "Allegagione": 4.0,
        "Invaiatura": 6.0,
        "Maturazione": 8.5,
    }.get(stadio, 3.0)
    aggiustamento = max(0, temperatura - 25) * 0.05
    return round(min(10, base + aggiustamento), 2)


def calcola_resa_ha(coltura, efficienza):
    """Calcola resa fresca e olio per ettaro in base all'efficienza colturale."""
    param = CULTIVAR_PARAM.get(coltura, CULTIVAR_PARAM["Carolea"])
    resa_fresca = param["produzione_base_kg_ha"] * efficienza * np.random.normal(1.0, 0.05)
    resa_olio = resa_fresca * param["estrazione_olio"]
    return round(resa_fresca, 1), round(resa_olio, 1)


def genera_dati_giornata(coltura=None, usa_reali=None):
    """
    Genera tutti i dati per una singola giornata simulata.
    Prova a usare dati meteorologici reali se disponibili.
    
    Args:
        coltura: Nome della coltura (se None, sceglie random)
        usa_reali: Se True, prova a usare dati reali (default: USA_DATI_REALI)
    
    Returns:
        dict: Dizionario con tutti i dati della giornata
    """
    if coltura is None:
        coltura = random.choice(COLTURE)
    
    if usa_reali is None:
        usa_reali = USA_DATI_REALI
    
    # Prova a ottenere dati meteorologici reali
    meteo_reale = None
    if usa_reali and DATI_REALI_DISPONIBILI:
        meteo_reale = ottieni_meteo_reale(OPENWEATHER_API_KEY, PREFER_OPENMETEO)
    
    if meteo_reale:
        temperatura = meteo_reale['temperatura']
        umidita = meteo_reale['umidita']
        precipitazioni = meteo_reale.get('precipitazioni', 0)
        fonte_meteo = meteo_reale.get('fonte', 'reale')
    else:
        # Fallback a dati simulati
        temperatura = genera_temperatura()
        umidita = genera_umidita()
        precipitazioni = genera_precipitazioni()
        fonte_meteo = 'simulato'
    
    stadio = stadio_fenologico(temperatura, datetime.now().month)
    efficienza = calcola_efficienza_colturale(coltura, temperatura, umidita, precipitazioni)
    fabbisogno_idrico = calcola_fabbisogno_idrico(temperatura, umidita, stadio)
    mosca = pressione_mosca(temperatura, umidita)
    maturazione_idx = calcola_maturazione_indice(stadio, temperatura)

    # Calcola rese
    resa_fresca_ha, resa_olio_ha = calcola_resa_ha(coltura, efficienza)
    resa_prevista_ha = resa_fresca_ha * np.random.normal(1.02, 0.05)
    # Distribuzione della raccolta giornaliera come quota della resa annuale
    quantita_raccolto = resa_fresca_ha / 200  # ipotesi: 200 giorni utili
    tempo_crescita = calcola_tempo_crescita(coltura, temperatura)
    costi = calcola_costi(coltura, quantita_raccolto)
    prezzo_vendita = calcola_prezzo_vendita(coltura)
    ricavi = quantita_raccolto * prezzo_vendita
    profitto = ricavi - costi

    # Rischi e qualità
    rischio_mosca = pressione_mosca(temperatura, umidita)
    semaforo_mosca = "rosso" if rischio_mosca >= 70 else "giallo" if rischio_mosca >= 40 else "verde"
    rischio_fungini = min(100, max(0, 0.6 * umidita + 1.2 * max(0, precipitazioni - 5)))
    stress_idrico_modello = max(0, fabbisogno_idrico - precipitazioni) * 2
    vigoria = round(max(0.4, min(1.2, np.random.normal(1.0, 0.1))) , 2)
    lai = round(vigoria * 3.2 + np.random.normal(0, 0.2), 2)  # superficie fogliare indicativa
    quality_kpi = round(max(0, min(10, 7.5 - stress_idrico_modello * 0.05 + maturazione_idx * 0.3 - rischio_fungini * 0.01)), 2)
    quality_pred = round(max(0, min(10, quality_kpi + np.random.normal(0.2, 0.2))), 2)

    # Eventi gestionali (conteggi giornalieri)
    concimazioni = 1 if random.random() < 0.01 else 0
    potature = 1 if random.random() < 0.005 else 0
    irrigazioni = 1 if fabbisogno_idrico > 4 and random.random() < 0.6 else 0
    trattamenti = 1 if (rischio_fungini > 50 or rischio_mosca > 60) and random.random() < 0.5 else 0
    
    return {
        "timestamp": datetime.now(),
        "coltura": coltura,
        "temperatura": temperatura,
        "umidita": umidita,
        "precipitazioni": precipitazioni,
        "quantita_raccolto": quantita_raccolto,
        "yield_ha": resa_fresca_ha,
        "oil_yield_ha": resa_olio_ha,
        "yield_prevista_ha": resa_prevista_ha,
        "tempo_crescita": tempo_crescita,
        "costi": costi,
        "prezzo_vendita": prezzo_vendita,
        "ricavi": ricavi,
        "profitto": profitto,
        "phenological_stage": stadio,
        "irrigation_need_mm": fabbisogno_idrico,
        "olive_fly_pressure": rischio_mosca,
        "olive_fly_light": semaforo_mosca,
        "fungal_risk": rischio_fungini,
        "water_stress_model": stress_idrico_modello,
        "vigor_index": vigoria,
        "leaf_area_index": lai,
        "maturity_index": maturazione_idx,
        "quality_kpi": quality_kpi,
        "quality_pred": quality_pred,
        "concimazioni": concimazioni,
        "potature": potature,
        "irrigazioni": irrigazioni,
        "trattamenti": trattamenti,
    }


def genera_storico_giorni(num_giorni=30, usa_reali=None):
    """
    Genera uno storico di dati per un numero di giorni specificato.
    Prova a usare dati meteorologici reali se disponibili.
    Utile per popolare i grafici all'avvio.
    
    Args:
        num_giorni: Numero di giorni di storico da generare
        usa_reali: Se True, prova a usare dati reali per meteo (default: USA_DATI_REALI)
    
    Returns:
        pd.DataFrame: DataFrame con tutti i dati storici
    """
    if usa_reali is None:
        usa_reali = USA_DATI_REALI
    
    # Prova a ottenere storico meteo reale
    storico_meteo = None
    if usa_reali and DATI_REALI_DISPONIBILI:
        # Limita a 90 giorni per evitare chiamate troppo lunghe
        giorni_richiesti = min(num_giorni, 90)
        storico_meteo = ottieni_storico_meteo_openmeteo(giorni=giorni_richiesti)
    
    dati = []
    data_inizio = datetime.now() - timedelta(days=num_giorni)
    
    for i in range(num_giorni):
        # Simula una data passata
        data = data_inizio + timedelta(days=i)
        coltura = random.choice(COLTURE)
        
        # Usa dati meteo reali se disponibili per questa data
        if storico_meteo is not None and not storico_meteo.empty:
            # Cerca dati per questa data specifica
            giorno_meteo = storico_meteo[storico_meteo['timestamp'].dt.date == data.date()]
            if not giorno_meteo.empty:
                temperatura = giorno_meteo.iloc[0]['temperatura']
                umidita = giorno_meteo.iloc[0]['umidita']
                precipitazioni = giorno_meteo.iloc[0]['precipitazioni']
            else:
                # Fallback se data non trovata nello storico reale
                temperatura = PARAMETRI_SIMULAZIONE["temperatura_base"] + np.random.normal(0, 4)
                umidita = PARAMETRI_SIMULAZIONE["umidita_base"] + np.random.normal(0, 10)
                precipitazioni = genera_precipitazioni()
        else:
            # Dati simulati (fallback completo)
            temperatura = PARAMETRI_SIMULAZIONE["temperatura_base"] + np.random.normal(0, 4)
            umidita = PARAMETRI_SIMULAZIONE["umidita_base"] + np.random.normal(0, 10)
            precipitazioni = genera_precipitazioni()
        
        stadio = stadio_fenologico(temperatura, data.month)
        efficienza = calcola_efficienza_colturale(coltura, temperatura, umidita, precipitazioni)
        fabbisogno_idrico = calcola_fabbisogno_idrico(temperatura, umidita, stadio)
        mosca = pressione_mosca(temperatura, umidita)
        semaforo_mosca = "rosso" if mosca >= 70 else "giallo" if mosca >= 40 else "verde"
        maturazione_idx = calcola_maturazione_indice(stadio, temperatura)

        resa_fresca_ha, resa_olio_ha = calcola_resa_ha(coltura, efficienza)
        resa_prevista_ha = resa_fresca_ha * np.random.normal(1.02, 0.05)
        quantita_raccolto = resa_fresca_ha / 200
        tempo_crescita = calcola_tempo_crescita(coltura, temperatura)
        costi = calcola_costi(coltura, quantita_raccolto)
        prezzo_vendita = calcola_prezzo_vendita(coltura)
        ricavi = quantita_raccolto * prezzo_vendita
        profitto = ricavi - costi
        rischio_fungini = min(100, max(0, 0.6 * umidita + 1.2 * max(0, precipitazioni - 5)))
        stress_idrico_modello = max(0, fabbisogno_idrico - precipitazioni) * 2
        vigoria = round(max(0.4, min(1.2, np.random.normal(1.0, 0.1))) , 2)
        lai = round(vigoria * 3.2 + np.random.normal(0, 0.2), 2)
        quality_kpi = round(max(0, min(10, 7.5 - stress_idrico_modello * 0.05 + maturazione_idx * 0.3 - rischio_fungini * 0.01)), 2)
        quality_pred = round(max(0, min(10, quality_kpi + np.random.normal(0.2, 0.2))), 2)
        concimazioni = 1 if random.random() < 0.01 else 0
        potature = 1 if random.random() < 0.005 else 0
        irrigazioni = 1 if fabbisogno_idrico > 4 and random.random() < 0.6 else 0
        trattamenti = 1 if (rischio_fungini > 50 or mosca > 60) and random.random() < 0.5 else 0
        
        dati.append({
            "timestamp": data,
            "coltura": coltura,
            "temperatura": temperatura,
            "umidita": umidita,
            "precipitazioni": precipitazioni,
            "quantita_raccolto": quantita_raccolto,
            "yield_ha": resa_fresca_ha,
            "oil_yield_ha": resa_olio_ha,
            "yield_prevista_ha": resa_prevista_ha,
            "tempo_crescita": tempo_crescita,
            "costi": costi,
            "prezzo_vendita": prezzo_vendita,
            "ricavi": ricavi,
            "profitto": profitto,
            "phenological_stage": stadio,
            "irrigation_need_mm": fabbisogno_idrico,
            "olive_fly_pressure": mosca,
            "olive_fly_light": semaforo_mosca,
            "fungal_risk": rischio_fungini,
            "water_stress_model": stress_idrico_modello,
            "vigor_index": vigoria,
            "leaf_area_index": lai,
            "maturity_index": maturazione_idx,
            "quality_kpi": quality_kpi,
            "quality_pred": quality_pred,
            "concimazioni": concimazioni,
            "potature": potature,
            "irrigazioni": irrigazioni,
            "trattamenti": trattamenti,
        })
    
    return pd.DataFrame(dati)

