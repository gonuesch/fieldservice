# daten.py

import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

# Diese Funktion bleibt, um die Basisdaten zu laden
@st.cache_data(ttl=600)
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
        for col in ['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon', 'Umsatz_2024', 'Kunden_Nr']:
            df_merged[col] = pd.to_numeric(df_merged[col].replace('', np.nan), errors='coerce')
        
        df_merged.dropna(subset=['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon'], inplace=True)
        return df_merged
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Basisdaten aus Google Sheets: {e}")
        return pd.DataFrame()

# --- NEUE FUNKTIONEN FÜR SZENARIEN ---

def hole_szenarien_sheet():
    """Stellt die Verbindung zur Szenarien-Tabelle her."""
    creds_info = st.secrets["gcp_service_account"]
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open("gebietsplaner_szenarien").sheet1

@st.cache_data(ttl=60) # Kürzerer Cache, da sich die Liste ändern kann
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