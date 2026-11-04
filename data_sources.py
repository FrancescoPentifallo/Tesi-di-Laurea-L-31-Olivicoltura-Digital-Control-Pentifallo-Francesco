"""
Modulo per ottenere dati reali da API esterne.
Supporta fallback a dati simulati se le API non sono disponibili.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict
import time

# Configurazione coordinate (default: Gioia Tauro, Calabria)
LATITUDINE = 38.43
LONGITUDINE = 15.90

# Cache per evitare troppe chiamate API
_meteo_cache = {}
_cache_duration = 300  # 5 minuti


def ottieni_meteo_openmeteo(lat: float = LATITUDINE, lon: float = LONGITUDINE) -> Optional[Dict]:
    """
    Ottiene dati meteorologici reali da Open-Meteo API (gratuita, senza API key).
    
    Args:
        lat: Latitudine
        lon: Longitudine
    
    Returns:
        dict con temperatura, umidita, precipitazioni o None se errore
    """
    cache_key = f"{lat}_{lon}_{datetime.now().strftime('%Y%m%d%H')}"
    
    # Controlla cache
    if cache_key in _meteo_cache:
        cached_time, cached_data = _meteo_cache[cache_key]
        if (datetime.now() - cached_time).seconds < _cache_duration:
            return cached_data
    
    try:
        # API Open-Meteo per dati attuali
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"hourly=temperature_2m,relative_humidity_2m,precipitation&"
            f"timezone=Europe/Rome&forecast_days=1"
        )
        
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            hourly = data.get('hourly', {})
            
            if hourly and len(hourly.get('time', [])) > 0:
                # Prendi l'ultimo valore disponibile (più recente)
                idx = -1
                temperatura = hourly['temperature_2m'][idx]
                umidita = hourly['relative_humidity_2m'][idx]
                precipitazioni = hourly['precipitation'][idx] if hourly.get('precipitation') else 0
                
                result = {
                    'temperatura': round(temperatura, 1),
                    'umidita': round(umidita, 1),
                    'precipitazioni': round(max(0, precipitazioni), 1),
                    'fonte': 'openmeteo'
                }
                
                # Salva in cache
                _meteo_cache[cache_key] = (datetime.now(), result)
                return result
    except Exception as e:
        print(f"Errore Open-Meteo API: {e}")
    
    return None


def ottieni_storico_meteo_openmeteo(
    lat: float = LATITUDINE,
    lon: float = LONGITUDINE,
    giorni: int = 30
) -> Optional[pd.DataFrame]:
    """
    Ottiene storico meteorologico da Open-Meteo.
    
    Args:
        lat: Latitudine
        lon: Longitudine
        giorni: Numero di giorni di storico
    
    Returns:
        DataFrame con timestamp, temperatura, umidita, precipitazioni
    """
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=giorni)
        
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_max,precipitation_sum&"
            f"timezone=Europe/Rome&"
            f"start_date={start_date}&end_date={end_date}"
        )
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            daily = data.get('daily', {})
            
            if daily and len(daily.get('time', [])) > 0:
                times = [datetime.fromisoformat(t) for t in daily['time']]
                temp_max = daily.get('temperature_2m_max', [])
                temp_min = daily.get('temperature_2m_min', [])
                umidita_max = daily.get('relative_humidity_2m_max', [])
                precipitazioni = daily.get('precipitation_sum', [])
                
                # Calcola temperatura media
                temp_media = [(tmax + tmin) / 2 for tmax, tmin in zip(temp_max, temp_min)]
                
                df = pd.DataFrame({
                    'timestamp': times,
                    'temperatura': [round(t, 1) for t in temp_media],
                    'umidita': [round(u, 1) for u in umidita_max],
                    'precipitazioni': [round(max(0, p), 1) for p in precipitazioni]
                })
                
                return df
    except Exception as e:
        None
    
    return None



def ottieni_meteo_reale(api_key: Optional[str] = None, prefer_openmeteo: bool = True) -> Optional[Dict]:
    """
    Ottiene dati meteorologici reali, provando prima Open-Meteo
    
    Args:
        prefer_openmeteo: Se True, preferisce Open-Meteo 
    
    Returns:
        dict con dati meteo o None se tutte le API falliscono
    """
    if prefer_openmeteo:
        meteo = ottieni_meteo_openmeteo()
        if meteo:
            return meteo
    
    
    return None

