# daten.py

import streamlit as st
import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=600)  # Cache für 10 Minuten, um Daten frisch zu halten
def lade_daten():
    """
    Stellt eine sichere Verbindung zu Google Sheets über den Service Account her
    (Anmeldedaten werden aus den Streamlit Secrets geladen) und liest die Daten ein.
    """
    try:
        # Anmeldedaten aus Streamlit Secrets beziehen
        creds_info = st.secrets["gcp_service_account"]
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        # Google Sheets über ihre exakten Namen öffnen
        kunden_sheet = gc.open("Kunden_mit_Koordinaten_Stand_2025-03").sheet1
        vertreter_sheet = gc.open("vertreter_stammdaten_robust").sheet1
        
        # Daten in pandas DataFrames umwandeln
        kunden_df = pd.DataFrame(kunden_sheet.get_all_records())
        vertreter_df = pd.DataFrame(vertreter_sheet.get_all_records())

        # Daten zusammenführen und bereinigen
        df_merged = pd.merge(kunden_df, vertreter_df, on='Vertreter_Name', how='left')
        
        # Leere Strings zu NaN konvertieren und Datentypen sicherstellen
        for col in ['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon', 'Umsatz_2024']:
            df_merged[col] = pd.to_numeric(df_merged[col].replace('', np.nan), errors='coerce')
        
        df_merged.dropna(subset=['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon'], inplace=True)
        return df_merged
        
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten aus Google Sheets: {e}")
        st.error("Bitte überprüfen Sie: 1) Die Namen der Google Sheets sind exakt. 2) Die Sheets sind für die Service-Account-E-Mail freigegeben. 3) Die Secrets in Streamlit sind korrekt formatiert.")
        return pd.DataFrame()