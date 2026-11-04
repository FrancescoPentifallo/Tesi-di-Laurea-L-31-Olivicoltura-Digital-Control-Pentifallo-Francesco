"""
Modulo principale per la dashboard Dash con KPIs e grafici interattivi.
"""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import simulator

# Opzioni mercati e tipologie olio
MERCATI = ["Gioia Tauro", "Bari", "Palermo", "Roma", "Milano"]
TIPI_OLIO = ["Olio DOP", "Olio EVO", "Olio Lampante"]

# Prezzi indicativi (€ / kg) per mercato e tipologia
PREZZI_MERCATO = {
    "Gioia Tauro": {"Olio DOP": 8.2, "Olio EVO": 7.0, "Olio Lampante": 3.0},
    "Bari": {"Olio DOP": 7.8, "Olio EVO": 6.6, "Olio Lampante": 2.8},
    "Palermo": {"Olio DOP": 8.0, "Olio EVO": 6.9, "Olio Lampante": 2.9},
    "Roma": {"Olio DOP": 8.5, "Olio EVO": 7.2, "Olio Lampante": 3.2},
    "Milano": {"Olio DOP": 8.8, "Olio EVO": 7.5, "Olio Lampante": 3.3},
}


def normalizza_colonne(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantisce la presenza delle colonne usate nei grafici/KPI, riempiendo con default se mancanti.
    Utile per evitare KeyError quando si caricano dati privi dei nuovi campi.
    """
    default_cols = {
        'yield_ha': 0.0,
        'oil_yield_ha': 0.0,
        'yield_prevista_ha': 0.0,
        'irrigation_need_mm': 0.0,
        'olive_fly_pressure': 0.0,
        'olive_fly_light': 'verde',
        'fungal_risk': 0.0,
        'water_stress_model': 0.0,
        'vigor_index': 1.0,
        'leaf_area_index': 0.0,
        'maturity_index': 0.0,
        'quality_kpi': 0.0,
        'quality_pred': 0.0,
        'concimazioni': 0,
        'potature': 0,
        'irrigazioni': 0,
        'trattamenti': 0,
        'phenological_stage': 'N/D',
        'profitto': 0.0,
        'ricavi': 0.0,
    }
    for col, default in default_cols.items():
        if col not in df:
            df[col] = default
    return df


def aggrega_mensile(df: pd.DataFrame, campo_data: str = 'timestamp') -> pd.DataFrame:
    """
    Aggrega i dati su base mensile per rendere i grafici leggibili su intervalli lunghi.
    """
    if df.empty:
        return df
    df = df.set_index(campo_data)
    agg = {
        'yield_ha': 'mean',
        'oil_yield_ha': 'mean',
        'ricavi': 'sum',
        'costi': 'sum',
        'profitto': 'sum',
        'temperatura': 'mean',
        'umidita': 'mean',
        'precipitazioni': 'sum',
        'irrigation_need_mm': 'mean',
        'olive_fly_pressure': 'mean',
        'maturity_index': 'mean',
    }
    # Mantieni anche il primo stadio fenologico del mese (indicativo)
    agg_data = {k: v for k, v in agg.items() if k in df.columns}
    res = df.resample('MS').agg(agg_data)
    if 'phenological_stage' in df.columns:
        res['phenological_stage'] = df['phenological_stage'].resample('MS').last()
    res = res.reset_index()
    return res


def aggrega_settimanale(df: pd.DataFrame, campo_data: str = 'timestamp') -> pd.DataFrame:
    """
    Aggrega i dati su base settimanale per ridurre la densità nei grafici medi/lunghi.
    """
    if df.empty:
        return df
    df = df.set_index(campo_data)
    agg = {
        'yield_ha': 'mean',
        'oil_yield_ha': 'mean',
        'ricavi': 'sum',
        'costi': 'sum',
        'profitto': 'sum',
        'temperatura': 'mean',
        'umidita': 'mean',
        'precipitazioni': 'sum',
        'irrigation_need_mm': 'mean',
        'olive_fly_pressure': 'mean',
        'maturity_index': 'mean',
    }
    agg_data = {k: v for k, v in agg.items() if k in df.columns}
    res = df.resample('W-MON').agg(agg_data)
    if 'phenological_stage' in df.columns:
        res['phenological_stage'] = df['phenological_stage'].resample('W-MON').last()
    res = res.reset_index()
    return res

# Inizializza l'app Dash
app = dash.Dash(__name__)

# Stile CSS semplice e moderno
ESTERNO_STILE = {
    'fontFamily': 'Arial, sans-serif',
    'backgroundColor': '#f5f5f5',
    'padding': '20px',
}

CONTENITORE_STILE = {
    'maxWidth': '1400px',
    'margin': '0 auto',
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '10px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
}

KPI_STILE = {
    'backgroundColor': '#f8f9fa',
    'padding': '15px',
    'borderRadius': '8px',
    'textAlign': 'center',
    'margin': '10px',
    'border': '1px solid #dee2e6',
}

TITOLO_STILE = {
    'color': '#2c3e50',
    'marginBottom': '30px',
    'textAlign': 'center',
}

# Gruppi KPI per tab
ECON_KEYS = ['yield_medio', 'yield_prevista', 'olio_medio', 'ricavi_totali', 'profitto_totale', 'prezzo_piazza']
AGRO_QUAL_KEYS = [
    'fabbisogno_idrico', 'stress_idrico_modello', 'vigoria', 'leaf_area_index',
    'irrigazioni', 'concimazioni', 'potature', 'trattamenti',
    'stadio_corrente', 'maturazione', 'quality_kpi', 'quality_pred', 'qualita_vs_data',
]
PREV_TRATT_KEYS = [
    'pressione_mosca', 'semaforo_mosca', 'rischio_fungini', 'alert_trattamenti',
    'fabbisogno_idrico', 'yield_prevista', 'quality_pred',
]


# Crea il layout della dashboard
def crea_layout():
    """
    Crea e restituisce il layout completo della dashboard.
    Include controlli, KPIs e grafici.
    """
    return html.Div(style=ESTERNO_STILE, children=[
        html.Div(style=CONTENITORE_STILE, children=[
            # Titolo principale
            html.H1("Dashboard Olivicoltura", style=TITOLO_STILE),
            
            # Sezione controlli
            html.Div([
                html.Label("Seleziona Coltura:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='dropdown-coltura',
                    options=[{'label': c, 'value': c} for c in ['Tutte'] + simulator.COLTURE],
                    value='Tutte',
                    style={'width': '200px', 'display': 'inline-block'}
                ),
                html.Label("Finestra Temporale (giorni):", 
                         style={'fontWeight': 'bold', 'marginLeft': '30px', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='dropdown-giorni',
                    options=[
                        {'label': '7 giorni', 'value': 7},
                        {'label': '14 giorni', 'value': 14},
                        {'label': '30 giorni', 'value': 30},
                        {'label': '60 giorni', 'value': 60},
                        {'label': '1 anno', 'value': 365},
                        {'label': '2 anni', 'value': 730},
                        {'label': '5 anni', 'value': 1825},
                    ],
                    value=30,
                    style={'width': '150px', 'display': 'inline-block'}
                ),
                html.Label("Piazza:", style={'fontWeight': 'bold', 'marginLeft': '30px', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='dropdown-mercato',
                    options=[{'label': m, 'value': m} for m in MERCATI],
                    value=MERCATI[0],
                    style={'width': '180px', 'display': 'inline-block'}
                ),
                html.Label("Tipo olio:", style={'fontWeight': 'bold', 'marginLeft': '30px', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='dropdown-olio',
                    options=[{'label': t, 'value': t} for t in TIPI_OLIO],
                    value=TIPI_OLIO[0],
                    style={'width': '160px', 'display': 'inline-block'}
                ),
            ], style={'marginBottom': '30px', 'padding': '15px', 'backgroundColor': '#e9ecef', 'borderRadius': '5px'}),
            
            # Sezione KPIs (Metriche Chiave) - cambia in base al tab selezionato
            html.Div(id='kpi-container', style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '30px'}),

            # Tabs per sezioni
            dcc.Tabs(
                id='tabs',
                value='tab-economia',
                children=[
                    dcc.Tab(label='Economia (KPI Economici + Produttivi)', value='tab-economia', children=[
                        html.Div([
                            html.H3("Resa e Olio per Ettaro", style={'marginBottom': '15px', 'color': '#34495e'}),
                            dcc.Graph(id='grafico-efficienza'),
                        ], style={'marginBottom': '30px'}),
                        html.Div([
                            html.H3("Performance Finanziaria", style={'marginBottom': '15px', 'color': '#34495e'}),
                            dcc.Graph(id='grafico-finanziario'),
                        ], style={'marginBottom': '30px'}),
                    ]),
                    dcc.Tab(label='Cura e Qualità (KPI Agronomici + KPI Qualità)', value='tab-cura', children=[
                        html.Div([
                            html.H3("Contesto Meteorologico", style={'marginBottom': '15px', 'color': '#34495e'}),
                            dcc.Graph(id='grafico-meteo'),
                        ], style={'marginBottom': '30px'}),
                    ]),
                    dcc.Tab(label='Previsioni e Trattamenti (Monitoraggio parassiti + Trattamenti)', value='tab-previsioni', children=[
                        html.Div([
                            html.H3("Gestione Oliveto (Irrigazione, Mosca, Maturazione)", style={'marginBottom': '15px', 'color': '#34495e'}),
                            dcc.Graph(id='grafico-gestione'),
                        ], style={'marginBottom': '30px'}),
                    ]),
                ]
            ),
            
            # Intervallo per aggiornamento automatico dei dati
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Aggiorna ogni 30 secondi
                n_intervals=0
            ),
            
            # Storage nascosto per i dati
            dcc.Store(id='store-dati'),
        ])
    ])


def calcola_kpi(df):
    """
    Calcola le metriche chiave (KPIs) dal dataframe dei dati.
    
    Args:
        df: DataFrame con i dati
    
    Returns:
        dict: Dizionario con i valori dei KPIs
    """
    if df.empty:
        return {
        'profitto_totale': 0,
        'ricavi_totali': 0,
        'yield_medio': 0,
        'yield_prevista': 0,
        'olio_medio': 0,
        'fabbisogno_idrico': 0,
        'pressione_mosca': 0,
        'maturazione': 0,
        'stadio_corrente': 'N/D',
        'prezzo_piazza': 0,
        'rischio_fungini': 0,
        'stress_idrico_modello': 0,
        'vigoria': 0,
        'lai': 0,
        'concimazioni': 0,
        'potature': 0,
        'irrigazioni': 0,
        'trattamenti': 0,
        'quality_kpi': 0,
        'quality_pred': 0,
        'semaforo_mosca': 'verde',
        'alert_trattamenti': 'Nessun rischio',
        'qualita_vs_data': 'N/D',
        }
    
    profitto_totale = df['profitto'].sum()
    ricavi_totali = df['ricavi'].sum()
    yield_medio = df['yield_ha'].mean()
    yield_prevista = df['yield_prevista_ha'].mean()
    olio_medio = df['oil_yield_ha'].mean()
    fabbisogno_idrico = df['irrigation_need_mm'].mean()
    pressione_mosca = df['olive_fly_pressure'].mean()
    semaforo_mosca = df['olive_fly_light'].mode().iat[0] if not df['olive_fly_light'].empty else 'verde'
    rischio_fungini = df['fungal_risk'].mean()
    stress_idrico_modello = df['water_stress_model'].mean()
    vigoria = df['vigor_index'].mean()
    lai = df['leaf_area_index'].mean()
    concimazioni = df['concimazioni'].sum()
    potature = df['potature'].sum()
    irrigazioni = df['irrigazioni'].sum()
    trattamenti = df['trattamenti'].sum()
    quality_kpi = df['quality_kpi'].mean()
    quality_pred = df['quality_pred'].mean()
    alert_trattamenti = "Consigliato" if (rischio_fungini > 50 or pressione_mosca > 60) else "Non necessario"
    qualita_vs_data = "Raccogli presto" if df['maturity_index'].mean() < 6 else "Finestra ottimale" if df['maturity_index'].mean() <= 8 else "Qualità in calo"
    maturazione = df['maturity_index'].mean()
    # stadio più recente
    stadio_corrente = df.sort_values('timestamp')['phenological_stage'].iloc[-1]
    
    return {
        'profitto_totale': round(profitto_totale, 2),
        'ricavi_totali': round(ricavi_totali, 2),
        'yield_medio': round(yield_medio, 1),
        'yield_prevista': round(yield_prevista, 1),
        'olio_medio': round(olio_medio, 1),
        'fabbisogno_idrico': round(fabbisogno_idrico, 1),
        'pressione_mosca': round(pressione_mosca, 1),
        'maturazione': round(maturazione, 2),
        'stadio_corrente': stadio_corrente,
        'prezzo_piazza': 0,  # valorizzato nel callback con selezione utente
        'rischio_fungini': round(rischio_fungini, 1),
        'stress_idrico_modello': round(stress_idrico_modello, 1),
        'vigoria': round(vigoria, 2),
        'lai': round(lai, 2),
        'concimazioni': int(concimazioni),
        'potature': int(potature),
        'irrigazioni': int(irrigazioni),
        'trattamenti': int(trattamenti),
        'quality_kpi': round(quality_kpi, 2),
        'quality_pred': round(quality_pred, 2),
        'semaforo_mosca': semaforo_mosca,
        'alert_trattamenti': alert_trattamenti,
        'qualita_vs_data': qualita_vs_data,
    }


def aggiorna_kpi_visivi(kpi_values, keys=None):
    """
    Crea i componenti visuali per mostrare i KPIs. Permette di filtrare le card via lista keys.
    """
    cards = []

    def add(key, content):
        if keys is None or key in keys:
            cards.append(content)

    add('yield_medio', html.Div([
        html.H4(f"{kpi_values['yield_medio']:,.1f} kg/ha", style={'color': '#27ae60', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Resa media per ettaro", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('yield_prevista', html.Div([
        html.H4(f"{kpi_values.get('yield_prevista',0):,.1f} kg/ha", style={'color': '#1abc9c', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Previsione resa", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('olio_medio', html.Div([
        html.H4(f"{kpi_values['olio_medio']:,.1f} kg/ha", style={'color': '#16a085', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Olio stimato per ettaro", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('ricavi_totali', html.Div([
        html.H4(f"€{kpi_values['ricavi_totali']:,.2f}", style={'color': '#3498db', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Ricavi totali", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('profitto_totale', html.Div([
        html.H4(f"€{kpi_values['profitto_totale']:,.2f}", style={'color': '#27ae60', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Profitto totale", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('prezzo_piazza', html.Div([
        html.H4(f"€{kpi_values.get('prezzo_piazza', 0):,.2f}/kg", style={'color': '#34495e', 'fontSize': '26px', 'margin': '5px'}),
        html.P(f"Prezzo {kpi_values.get('tipo_olio','')} - {kpi_values.get('piazza','')}", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('fabbisogno_idrico', html.Div([
        html.H4(f"{kpi_values['fabbisogno_idrico']:,.1f} mm", style={'color': '#3498db', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Fabbisogno irriguo medio", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('stress_idrico_modello', html.Div([
        html.H4(f"{kpi_values.get('stress_idrico_modello',0):,.1f}", style={'color': '#8e44ad', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Livello stress idrico (modello)", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('pressione_mosca', html.Div([
        html.H4(f"{kpi_values['pressione_mosca']:,.1f}", style={'color': '#e67e22', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Pressione mosca (0-100)", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('semaforo_mosca', html.Div([
        html.H4(kpi_values.get('semaforo_mosca','verde').upper(), style={'color': '#e67e22', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Semaforo rischio mosca", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('rischio_fungini', html.Div([
        html.H4(f"{kpi_values.get('rischio_fungini',0):,.1f}", style={'color': '#c0392b', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Rischio malattie fungine (0-100)", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('maturazione', html.Div([
        html.H4(f"{kpi_values['maturazione']:.2f} /10", style={'color': '#9b59b6', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Indice maturazione medio", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('stadio_corrente', html.Div([
        html.H4(kpi_values['stadio_corrente'], style={'color': '#2c3e50', 'fontSize': '24px', 'margin': '5px'}),
        html.P("Stadio fenologico attuale", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('vigoria', html.Div([
        html.H4(f"{kpi_values.get('vigoria',0):,.2f}", style={'color': '#2ecc71', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Vigoria", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('leaf_area_index', html.Div([
        html.H4(f"{kpi_values.get('leaf_area_index',0):,.2f}", style={'color': '#16a085', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Superficie fogliare stimata (LAI)", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('concimazioni', html.Div([
        html.H4(f"{kpi_values.get('concimazioni',0)}", style={'color': '#7f8c8d', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Concimazioni effettuate", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('potature', html.Div([
        html.H4(f"{kpi_values.get('potature',0)}", style={'color': '#7f8c8d', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Potature", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('irrigazioni', html.Div([
        html.H4(f"{kpi_values.get('irrigazioni',0)}", style={'color': '#7f8c8d', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Irrigazioni", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('trattamenti', html.Div([
        html.H4(f"{kpi_values.get('trattamenti',0)}", style={'color': '#7f8c8d', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Trattamenti fitosanitari", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('alert_trattamenti', html.Div([
        html.H4(kpi_values.get('alert_trattamenti',''), style={'color': '#c0392b', 'fontSize': '24px', 'margin': '5px'}),
        html.P("Alert trattamenti", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('quality_kpi', html.Div([
        html.H4(f"{kpi_values.get('quality_kpi',0):,.2f} /10", style={'color': '#2980b9', 'fontSize': '26px', 'margin': '5px'}),
        html.P("KPI qualità attuale", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('quality_pred', html.Div([
        html.H4(f"{kpi_values.get('quality_pred',0):,.2f} /10", style={'color': '#1abc9c', 'fontSize': '26px', 'margin': '5px'}),
        html.P("Previsione qualità futura", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    add('qualita_vs_data', html.Div([
        html.H4(kpi_values.get('qualita_vs_data',''), style={'color': '#2c3e50', 'fontSize': '22px', 'margin': '5px'}),
        html.P("Relazione qualità ↔ data raccolta", style={'color': '#7f8c8d', 'margin': '0'}),
    ], style=KPI_STILE))

    return cards


# Callback per aggiornare i dati
@app.callback(
    Output('store-dati', 'data'),
    [Input('interval-component', 'n_intervals')],
    prevent_initial_call=False
)
def aggiorna_dati(n):
    """
    Aggiorna i dati aggiungendo una nuova riga ogni volta che viene chiamato.
    All'avvio genera anche uno storico iniziale.
    """
    # Alla prima chiamata, genera storico
    if n == 0:
        # Genera storico ampio per supportare finestre fino a 5 anni
        df = simulator.genera_storico_giorni(1825)
    else:
        df = simulator.genera_storico_giorni(1825)
        nuovo_dato = simulator.genera_dati_giornata()
        df = pd.concat([df, pd.DataFrame([nuovo_dato])], ignore_index=True)
        # Mantieni uno storico ragionevole (circa 5 anni + buffer)
        df = df.tail(2000)
    
    return df.to_dict('records')


# Callback per filtrare i dati in base ai controlli
def prezzo_piazza(mercato: str, tipo_olio: str) -> float:
    """Restituisce il prezzo €/kg per la piazza e tipologia selezionata."""
    return PREZZI_MERCATO.get(mercato, {}).get(tipo_olio, 0.0)


@app.callback(
    Output('kpi-container', 'children'),
    [Input('store-dati', 'data'),
     Input('dropdown-coltura', 'value'),
     Input('dropdown-giorni', 'value'),
     Input('dropdown-mercato', 'value'),
     Input('dropdown-olio', 'value'),
     Input('tabs', 'value')]
)
def aggiorna_kpi(dati, coltura_selezionata, giorni, mercato, tipo_olio, tab):
    """
    Aggiorna i KPIs visualizzati in base ai filtri selezionati.
    """
    if not dati:
        return []
    
    df = normalizza_colonne(pd.DataFrame(dati))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filtra per coltura
    if coltura_selezionata != 'Tutte':
        df = df[df['coltura'] == coltura_selezionata]
    
    # Filtra per giorni
    data_limite = datetime.now() - timedelta(days=giorni)
    df = df[df['timestamp'] >= data_limite]
    
    kpi_values = calcola_kpi(df)
    kpi_values['prezzo_piazza'] = prezzo_piazza(mercato, tipo_olio)
    kpi_values['piazza'] = mercato
    kpi_values['tipo_olio'] = tipo_olio
    if tab == 'tab-economia':
        keys = ECON_KEYS
    elif tab == 'tab-cura':
        keys = AGRO_QUAL_KEYS
    else:
        keys = PREV_TRATT_KEYS
    return aggiorna_kpi_visivi(kpi_values, keys)


# Callback per il grafico efficienza raccolto
@app.callback(
    Output('grafico-efficienza', 'figure'),
    [Input('store-dati', 'data'),
     Input('dropdown-coltura', 'value'),
     Input('dropdown-giorni', 'value')]
)
def aggiorna_grafico_efficienza(dati, coltura_selezionata, giorni):
    """
    Grafico di resa e resa olio per ettaro nel tempo.
    """
    if not dati:
        return go.Figure()
    
    df = normalizza_colonne(pd.DataFrame(dati))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    if coltura_selezionata != 'Tutte':
        df = df[df['coltura'] == coltura_selezionata]
    
    data_limite = datetime.now() - timedelta(days=giorni)
    df = df[df['timestamp'] >= data_limite].copy()
    
    if df.empty:
        return go.Figure()
    
    # Aggregazione mensile per finestre >= 1 anno
    if giorni >= 365:
        df = aggrega_mensile(df)

    if giorni >= 365:
        df = aggrega_mensile(df)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['yield_ha'],
        mode='lines+markers',
        name='Resa olive (kg/ha)',
        line=dict(color='#2c82c9', width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['oil_yield_ha'],
        mode='lines+markers',
        name='Resa olio (kg/ha)',
        line=dict(color='#16a085', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Rese per Ettaro",
        xaxis_title="Data",
        yaxis_title="Kg per ettaro",
        hovermode='x unified',
        template='plotly_white',
        height=400,
        xaxis=dict(tickformat='%b %Y' if giorni >= 365 else None),
    )
    
    return fig


# Callback per il grafico finanziario
@app.callback(
    Output('grafico-finanziario', 'figure'),
    [Input('store-dati', 'data'),
     Input('dropdown-coltura', 'value'),
     Input('dropdown-giorni', 'value')]
)
def aggiorna_grafico_finanziario(dati, coltura_selezionata, giorni):
    """
    Aggiorna il grafico che mostra ricavi, costi e profitti nel tempo.
    """
    if not dati:
        return go.Figure()
    
    df = normalizza_colonne(pd.DataFrame(dati))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filtra per coltura
    if coltura_selezionata != 'Tutte':
        df = df[df['coltura'] == coltura_selezionata]
    
    # Filtra per giorni
    data_limite = datetime.now() - timedelta(days=giorni)
    df = df[df['timestamp'] >= data_limite].copy()
    
    if df.empty:
        return go.Figure()
    
    if giorni >= 365:
        df = aggrega_mensile(df)

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['ricavi'],
        mode='lines+markers',
        name='Ricavi (€)',
        line=dict(color='#27ae60', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['costi'],
        mode='lines+markers',
        name='Costi (€)',
        line=dict(color='#e74c3c', width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['profitto'],
        mode='lines+markers',
        name='Profitto (€)',
        line=dict(color='#9b59b6', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Performance Finanziaria nel Tempo",
        xaxis_title="Data",
        yaxis_title="Euro (€)",
        hovermode='x unified',
        template='plotly_white',
        height=400,
        xaxis=dict(tickformat='%b %Y' if giorni >= 365 else None),
    )
    
    return fig


# Callback per il grafico meteo
@app.callback(
    Output('grafico-meteo', 'figure'),
    [Input('store-dati', 'data'),
     Input('dropdown-coltura', 'value'),
     Input('dropdown-giorni', 'value')]
)
def aggiorna_grafico_meteo(dati, coltura_selezionata, giorni):
    """
    Aggiorna il grafico che mostra temperatura, umidità e precipitazioni.
    """
    if not dati:
        return go.Figure()
    
    df = normalizza_colonne(pd.DataFrame(dati))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filtra per coltura
    if coltura_selezionata != 'Tutte':
        df = df[df['coltura'] == coltura_selezionata]
    
    # Filtra per giorni
    data_limite = datetime.now() - timedelta(days=giorni)
    df = df[df['timestamp'] >= data_limite].copy()
    
    if df.empty:
        return go.Figure()
    
    if giorni >= 365:
        df = aggrega_mensile(df)

    fig = go.Figure()
    
    # Grafico temperatura (asse Y sinistra)
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['temperatura'],
        mode='lines+markers',
        name='Temperatura (°C)',
        line=dict(color='#e67e22', width=2),
        marker=dict(size=6),
        yaxis='y'
    ))
    
    # Grafico umidità (asse Y sinistra)
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['umidita'],
        mode='lines+markers',
        name='Umidità (%)',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6),
        yaxis='y'
    ))
    
    # Grafico precipitazioni (asse Y destra)
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['precipitazioni'],
        name='Precipitazioni (mm)',
        marker_color='#16a085',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Contesto Meteorologico",
        xaxis_title="Data",
        hovermode='x unified',
        template='plotly_white',
        height=400,
        yaxis=dict(title="Temperatura (°C) / Umidità (%)", side='left'),
        yaxis2=dict(title="Precipitazioni (mm)", overlaying='y', side='right'),
        xaxis=dict(tickformat='%b %Y' if giorni >= 365 else None),
    )
    
    return fig


@app.callback(
    Output('grafico-gestione', 'figure'),
    [Input('store-dati', 'data'),
     Input('dropdown-coltura', 'value'),
     Input('dropdown-giorni', 'value')]
)
def aggiorna_grafico_gestione(dati, coltura_selezionata, giorni):
    """
    Mostra fabbisogno irriguo, pressione mosca e indice di maturazione.
    """
    if not dati:
        return go.Figure()

    df = normalizza_colonne(pd.DataFrame(dati))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if coltura_selezionata != 'Tutte':
        df = df[df['coltura'] == coltura_selezionata]

    data_limite = datetime.now() - timedelta(days=giorni)
    df = df[df['timestamp'] >= data_limite].copy()

    if df.empty:
        return go.Figure()

    tickformat = None
    line_mode = 'lines+markers'
    marker_cfg = dict(size=6)

    if giorni >= 365:
        df = aggrega_mensile(df)
        tickformat = '%b %Y'
        line_mode = 'lines'
        marker_cfg = dict(size=4)
    elif giorni >= 60:
        df = aggrega_settimanale(df)
        tickformat = '%d %b %Y'
        line_mode = 'lines'
        marker_cfg = dict(size=4)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['irrigation_need_mm'],
        name='Fabbisogno irriguo (mm)',
        marker_color='#3498db',
        yaxis='y'
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['olive_fly_pressure'],
        mode=line_mode,
        name='Pressione mosca (0-100)',
        line=dict(color='#e67e22', width=2),
        marker=marker_cfg,
        yaxis='y2'
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['maturity_index'],
        mode=line_mode,
        name='Indice maturazione (0-10)',
        line=dict(color='#9b59b6', width=2),
        marker=marker_cfg,
        yaxis='y3'
    ))

    fig.update_layout(
        title="Gestione colturale",
        xaxis_title="Data",
        hovermode='x unified',
        template='plotly_white',
        height=420,
        yaxis=dict(title="Irrigazione (mm)"),
        yaxis2=dict(title="Mosca (0-100)", overlaying='y', side='right'),
        # Position must be in [0,1]; keep a slight offset to separate labels
        yaxis3=dict(title="Maturazione (0-10)", overlaying='y', side='right', position=0.99),
        xaxis=dict(tickformat=tickformat),
    )

    return fig


# Inizializza il layout
app.layout = crea_layout()

