# daten.py

import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
import sqlite3
import tempfile
import os

# Diese Funktion bleibt, um die Basisdaten zu laden
@st.cache_data(ttl=7200)  # 2 Stunden Cache für bessere Performance
def lade_basis_daten():
    """Lädt die initialen Kunden- und Vertreterdaten."""
    try:
        creds_info = st.secrets["gcp_service_account"]
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        kunden_sheet = gc.open("Kunden_mit_Koordinaten_Stand_2025-03").sheet1
        vertreter_sheet = gc.open("vertreter_stammdaten_robust").sheet1
        
        kunden_df = pd.DataFrame(kunden_sheet.get_all_records())
        vertreter_df = pd.DataFrame(vertreter_sheet.get_all_records())

        df_merged = pd.merge(kunden_df, vertreter_df, on='Vertreter_Name', how='left')
        
        # Optimierte Datenverarbeitung
        numeric_columns = ['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon', 'Umsatz_2024', 'Kunden_Nr']
        for col in numeric_columns:
            if col in df_merged.columns:
                df_merged[col] = pd.to_numeric(df_merged[col].replace('', np.nan), errors='coerce')
        
        # Entferne Zeilen ohne Koordinaten
        df_merged.dropna(subset=['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon'], inplace=True)
        
        # Sortiere für bessere Performance
        df_merged.sort_values('Kunden_Nr', inplace=True)
        df_merged.reset_index(drop=True, inplace=True)
        
        # Erstelle In-Memory SQLite für bessere Performance
        create_in_memory_db(df_merged)
        
        return df_merged
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Basisdaten aus Google Sheets: {e}")
        return pd.DataFrame()

def create_in_memory_db(df):
    """Erstellt eine In-Memory SQLite Datenbank für bessere Performance."""
    try:
        # Erstelle temporäre SQLite-Datei
        temp_db_path = tempfile.mktemp(suffix='.db')
        
        # Verbinde zur SQLite-Datenbank
        conn = sqlite3.connect(temp_db_path)
        
        # Speichere DataFrame in SQLite
        df.to_sql('kunden', conn, if_exists='replace', index=False)
        
        # Erstelle Indizes für bessere Performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_kunden_nr ON kunden(Kunden_Nr)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_vertreter ON kunden(Vertreter_Name)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_verlag ON kunden(Verlag)')
        
        # Speichere DB-Pfad im Session State
        st.session_state.db_path = temp_db_path
        st.session_state.db_conn = conn
        
        st.success("✅ In-Memory Datenbank erstellt für bessere Performance")
        
    except Exception as e:
        st.warning(f"⚠️ In-Memory DB konnte nicht erstellt werden: {e}")

@st.cache_data(ttl=3600)  # 1 Stunde Cache für Datenbankabfragen
def query_kunden_db(query, params=None):
    """Führt eine SQL-Abfrage auf der In-Memory Datenbank aus."""
    try:
        if 'db_conn' not in st.session_state:
            return pd.DataFrame()
        
        if params:
            return pd.read_sql_query(query, st.session_state.db_conn, params=params)
        else:
            return pd.read_sql_query(query, st.session_state.db_conn)
            
    except Exception as e:
        st.warning(f"⚠️ Datenbankabfrage fehlgeschlagen: {e}")
        return pd.DataFrame()

# --- NEUE FUNKTIONEN FÜR SZENARIEN ---

def hole_szenarien_sheet():
    """Stellt die Verbindung zur Szenarien-Tabelle her."""
    creds_info = st.secrets["gcp_service_account"]
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open("gebietsplaner_szenarien").sheet1

@st.cache_data(ttl=600) # 10 Minuten Cache für Szenarien-Liste
def lade_szenarien_liste():
    """Lädt die Liste aller einzigartigen Szenario-Namen."""
    try:
        szenarien_sheet = hole_szenarien_sheet()
        szenarien_namen = szenarien_sheet.col_values(1)[1:] # Erste Spalte ohne Header
        return sorted(list(set(szenarien_namen)))
    except Exception as e:
        st.warning(f"Konnte keine gespeicherten Szenarien laden: {e}")
        return []

def lade_szenario_zuweisung(szenario_name):
    """Lädt die Kundenzuordnung für ein spezifisches Szenario."""
    try:
        szenarien_sheet = hole_szenarien_sheet()
        alle_szenarien_df = pd.DataFrame(szenarien_sheet.get_all_records())
        szenario_df = alle_szenarien_df[alle_szenarien_df['szenario_name'] == szenario_name]
        # Wir brauchen nur die Zuordnung von Kunden-Nr zu Vertreter
        zuweisung = szenario_df[['Kunden_Nr', 'Vertreter_Name']]
        zuweisung['Kunden_Nr'] = pd.to_numeric(zuweisung['Kunden_Nr'], errors='coerce')
        return zuweisung.set_index('Kunden_Nr')
    except Exception as e:
        st.error(f"Fehler beim Laden des Szenarios '{szenario_name}': {e}")
        return None

def speichere_szenario(szenario_name, dataframe_aktuell):
    """Speichert die aktuelle Gebietsverteilung als neues Szenario."""
    try:
        szenarien_sheet = hole_szenarien_sheet()
        
        # Daten für das Speichern vorbereiten
        zu_speichern_df = dataframe_aktuell[['Kunden_Nr', 'Vertreter_Name']].copy()
        zu_speichern_df.insert(0, 'szenario_name', szenario_name)
        
        # Daten als Liste von Listen anhängen (effizienter als einzelne API-Calls)
        daten_zum_anhaengen = zu_speichern_df.values.tolist()
        szenarien_sheet.append_rows(daten_zum_anhaengen, value_input_option='USER_ENTERED')
        
        # Cache für die Szenarienliste leeren, damit die neue Liste geladen wird
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern des Szenarios '{szenario_name}': {e}")
        return False