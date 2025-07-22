import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import time

st.title("🔍 Google Sheets API Debug")

# Debug-Funktion für Google Sheets
def debug_google_sheets():
    st.info("🔄 Starte Google Sheets API Debug...")
    
    try:
        # 1. Prüfe Secrets
        st.write("### 1. Secrets prüfen")
        if "gcp_service_account" not in st.secrets:
            st.error("❌ gcp_service_account nicht in st.secrets gefunden")
            return
        
        st.success("✅ gcp_service_account in st.secrets gefunden")
        creds_info = st.secrets["gcp_service_account"]
        st.write("🔍 Secrets Keys:", list(creds_info.keys()))
        
        # 2. Credentials erstellen
        st.write("### 2. Credentials erstellen")
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        st.success("✅ Credentials erstellt")
        
        # 3. gspread autorisieren
        st.write("### 3. gspread autorisieren")
        gc = gspread.authorize(creds)
        st.success("✅ gspread autorisiert")
        
        # 4. Verfügbare Sheets auflisten
        st.write("### 4. Verfügbare Sheets auflisten")
        try:
            st.info("🔄 Rufe verfügbare Sheets ab...")
            available_sheets = gc.openall()
            sheet_names = [sheet.title for sheet in available_sheets]
            st.success(f"✅ {len(sheet_names)} Sheets gefunden")
            st.write("📋 Verfügbare Sheets:")
            for i, name in enumerate(sheet_names, 1):
                st.write(f"  {i}. {name}")
        except Exception as e:
            st.error(f"❌ Fehler beim Auflisten der Sheets: {e}")
            st.write(f"🔍 Vollständiger Fehler: {str(e)}")
            st.warning("⚠️ Versuche direkten Zugriff auf bekannte Sheets...")
            
            # Versuche direkten Zugriff auf bekannte Sheets
            known_sheets = [
                "Kunden_mit_Koordinaten_Stand_2025-03",
                "vertreter_stammdaten_robust",
                "gebietsplaner_szenarien"
            ]
            
            for sheet_name in known_sheets:
                try:
                    st.write(f"🔍 Teste direkten Zugriff auf: '{sheet_name}'")
                    sheet = gc.open(sheet_name)
                    st.success(f"✅ Zugriff auf '{sheet_name}' erfolgreich!")
                    st.write(f"  - ID: {sheet.id}")
                    st.write(f"  - URL: {sheet.url}")
                except Exception as sheet_error:
                    st.error(f"❌ Kein Zugriff auf '{sheet_name}': {sheet_error}")
            
            return
        
        # 5. Kunden-Sheet öffnen
        st.write("### 5. Kunden-Sheet öffnen")
        try:
            st.info("🔄 Öffne Kunden-Sheet...")
            kunden_sheet = gc.open("Kunden_mit_Koordinaten_Stand_2025-03")
            st.success("✅ Kunden-Sheet geöffnet")
            
            # Sheet-Info anzeigen
            st.write("📊 Sheet-Info:")
            st.write(f"  - Titel: {kunden_sheet.title}")
            st.write(f"  - ID: {kunden_sheet.id}")
            st.write(f"  - URL: {kunden_sheet.url}")
            
            # Worksheet-Info
            worksheet = kunden_sheet.sheet1
            st.write(f"  - Worksheet: {worksheet.title}")
            st.write(f"  - Zeilen: {worksheet.row_count}")
            st.write(f"  - Spalten: {worksheet.col_count}")
            
        except Exception as e:
            st.error(f"❌ Fehler beim Öffnen des Kunden-Sheets: {e}")
            st.write(f"🔍 Vollständiger Fehler: {str(e)}")
            return
        
        # 6. Daten laden
        st.write("### 6. Daten laden")
        try:
            st.info("🔄 Lade Daten vom Kunden-Sheet...")
            start_time = time.time()
            
            # Erste 5 Zeilen laden für Test
            st.write("📋 Lade erste 5 Zeilen...")
            first_rows = worksheet.get_all_values()[:5]
            st.success(f"✅ Erste 5 Zeilen geladen in {time.time() - start_time:.2f}s")
            
            st.write("📊 Erste 5 Zeilen:")
            for i, row in enumerate(first_rows, 1):
                st.write(f"  Zeile {i}: {row}")
            
            # Header extrahieren
            if first_rows:
                headers = first_rows[0]
                st.write("📋 Headers:", headers)
            
            # Vollständige Daten laden
            st.write("📋 Lade alle Daten...")
            start_time = time.time()
            all_data = worksheet.get_all_records()
            load_time = time.time() - start_time
            st.success(f"✅ {len(all_data)} Datensätze geladen in {load_time:.2f}s")
            
            # DataFrame erstellen
            df = pd.DataFrame(all_data)
            st.write("📊 DataFrame Info:")
            st.write(f"  - Shape: {df.shape}")
            st.write(f"  - Spalten: {list(df.columns)}")
            st.write(f"  - Erste 3 Zeilen:")
            st.dataframe(df.head(3))
            
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Daten: {e}")
            st.write(f"🔍 Vollständiger Fehler: {str(e)}")
            return
        
        # 7. Vertreter-Sheet testen
        st.write("### 7. Vertreter-Sheet testen")
        try:
            st.info("🔄 Öffne Vertreter-Sheet...")
            vertreter_sheet = gc.open("vertreter_stammdaten_robust")
            st.success("✅ Vertreter-Sheet geöffnet")
            
            vertreter_data = vertreter_sheet.sheet1.get_all_records()
            vertreter_df = pd.DataFrame(vertreter_data)
            st.write(f"📊 Vertreter-Daten: {len(vertreter_df)} Vertreter")
            st.write(f"📋 Vertreter-Spalten: {list(vertreter_df.columns)}")
            
        except Exception as e:
            st.error(f"❌ Fehler beim Vertreter-Sheet: {e}")
            st.write(f"🔍 Vollständiger Fehler: {str(e)}")
            return
        
        st.success("🎉 Alle API-Tests erfolgreich!")
        
    except Exception as e:
        st.error(f"❌ Allgemeiner Fehler: {e}")
        st.write(f"🔍 Vollständiger Fehler: {str(e)}")
        st.write("🔍 Fehler-Typ:", type(e).__name__)

# Debug ausführen
if st.button("🚀 Starte API Debug"):
    debug_google_sheets()

# Zusätzliche Debug-Info
st.markdown("---")
st.write("### 🔧 Zusätzliche Debug-Informationen")

# Environment Info
st.write("**Environment:**")
st.write(f"- Python Version: {st.get_option('server.enableCORS')}")
st.write(f"- Streamlit Version: {st.__version__}")

# Network Test
if st.button("🌐 Teste Netzwerk-Verbindung"):
    import requests
    try:
        response = requests.get("https://sheets.googleapis.com", timeout=10)
        st.success(f"✅ Google Sheets API erreichbar (Status: {response.status_code})")
    except Exception as e:
        st.error(f"❌ Google Sheets API nicht erreichbar: {e}")

# Secrets Test (ohne sensible Daten)
if st.button("🔐 Teste Secrets"):
    if "gcp_service_account" in st.secrets:
        creds = st.secrets["gcp_service_account"]
        st.success("✅ Secrets verfügbar")
        st.write("🔍 Verfügbare Keys:", list(creds.keys()))
        if "type" in creds:
            st.write("🔍 Service Account Typ:", creds["type"])
        if "project_id" in creds:
            st.write("🔍 Project ID:", creds["project_id"])
        if "client_email" in creds:
            st.write("🔍 Service Account Email:", creds["client_email"])
    else:
        st.error("❌ Secrets nicht verfügbar")

# Berechtigungs-Test
if st.button("🔑 Teste Berechtigungen"):
    try:
        creds_info = st.secrets["gcp_service_account"]
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        st.info("🔍 Teste verschiedene Zugriffsmethoden...")
        
        # Test 1: Drive API
        try:
            drive_service = gc.auth.service
            st.success("✅ Drive API Service verfügbar")
        except Exception as e:
            st.error(f"❌ Drive API Service Fehler: {e}")
        
        # Test 2: Sheets API
        try:
            sheets_service = gc.auth.service
            st.success("✅ Sheets API Service verfügbar")
        except Exception as e:
            st.error(f"❌ Sheets API Service Fehler: {e}")
        
        # Test 3: Service Account Info
        st.write("🔍 Service Account Details:")
        st.write(f"  - Email: {creds.service_account_email}")
        st.write(f"  - Project: {creds.project_id}")
        st.write(f"  - Scopes: {creds.scopes}")
        
    except Exception as e:
        st.error(f"❌ Berechtigungs-Test Fehler: {e}") 