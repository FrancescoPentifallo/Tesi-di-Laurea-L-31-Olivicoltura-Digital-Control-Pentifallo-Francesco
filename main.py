"""
Punto di ingresso principale per l'applicazione Dashboard Agricola.
Questo file avvia il server Dash.
"""
from dashboard import app

if __name__ == '__main__':
    # Avvia il server Dash
    # debug=True permette di vedere errori in tempo reale durante lo sviluppo
    app.run(debug=True, host='127.0.0.1', port=8050)

