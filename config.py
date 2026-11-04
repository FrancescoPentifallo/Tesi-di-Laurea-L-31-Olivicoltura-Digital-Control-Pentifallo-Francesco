"""
File di configurazione per l'integrazione con API esterne.
Modifica questi valori secondo le tue esigenze.
"""
# Coordinate dell'oliveto (default: Gioia Tauro, Calabria)
# Trova le coordinate del tuo oliveto su Google Maps o OpenStreetMap
LATITUDINE = 38.43
LONGITUDINE = 15.90

# Abilita/disabilita uso dati reali
# Imposta a False per usare solo dati simulati
USA_DATI_REALI = True

# API Key OpenWeatherMap (opzionale)
# Ottieni una chiave gratuita su https://openweathermap.org/api
# Lascia None per usare solo Open-Meteo (gratuita, senza API key)
OPENWEATHER_API_KEY = None  # Esempio: "your_api_key_here"

# Preferenza API meteo
# True = preferisce Open-Meteo (gratuita, senza API key)
# False = preferisce OpenWeatherMap se API key disponibile
PREFER_OPENMETEO = True

