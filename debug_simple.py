import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

st.title("🔍 Einfacher Google Sheets Debug")

def test_sheets_directly():
    st.info("🔄 Teste direkten Zugriff auf bekannte Sheets...")
    
    try:
        # 1. Secrets prüfen
        if "gcp_service_account" not in st.secrets:
            st.error("❌ gcp_service_account nicht in st.secrets gefunden")
            return
        
        creds_info = st.secrets["gcp_service_account"]
        st.success("✅ Secrets gefunden")
        
        # 2. Credentials erstellen
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(creds)
        st.success("✅ gspread autorisiert")
        
        # 3. Service Account Info anzeigen
        st.write("### Service Account Details:")
        st.write(f"**Email:** {creds.service_account_email}")
        st.write(f"**Project:** {creds.project_id}")
        
        # 4. Direkte Sheet-Tests
        st.write("### Direkte Sheet-Tests:")
        
        known_sheets = [
            "Kunden_mit_Koordinaten_Stand_2025-03",
            "vertreter_stammdaten_robust", 
            "gebietsplaner_szenarien"
        ]
        
        for sheet_name in known_sheets:
            st.write(f"---")
            st.write(f"**Teste: {sheet_name}**")
            
            try:
                start_time = time.time()
                sheet = gc.open(sheet_name)
                load_time = time.time() - start_time
                
                st.success(f"✅ Zugriff erfolgreich ({load_time:.2f}s)")
                st.write(f"  - ID: {sheet.id}")
                st.write(f"  - URL: {sheet.url}")
                
                # Teste Daten-Laden
                try:
                    worksheet = sheet.sheet1
                    st.write(f"  - Worksheet: {worksheet.title}")
                    st.write(f"  - Zeilen: {worksheet.row_count}")
                    st.write(f"  - Spalten: {worksheet.col_count}")
                    
                    # Lade erste Zeile (Header)
                    first_row = worksheet.row_values(1)
                    st.write(f"  - Header: {first_row[:5]}...")  # Erste 5 Spalten
                    
                    # Lade erste 3 Datensätze
                    if worksheet.row_count > 1:
                        sample_data = worksheet.get_all_records()[:3]
                        st.write(f"  - Erste 3 Datensätze geladen")
                        df_sample = pd.DataFrame(sample_data)
                        st.dataframe(df_sample)
                    
                except Exception as data_error:
                    st.error(f"❌ Daten-Laden Fehler: {data_error}")
                
            except Exception as e:
                st.error(f"❌ Zugriff fehlgeschlagen: {e}")
                st.write(f"  - Fehler-Typ: {type(e).__name__}")
        
        st.success("🎉 Alle Tests abgeschlossen!")
        
    except Exception as e:
        st.error(f"❌ Allgemeiner Fehler: {e}")
        st.write(f"Fehler-Typ: {type(e).__name__}")

# Test ausführen
if st.button("🚀 Starte direkte Sheet-Tests"):
    test_sheets_directly()

# Zusätzliche Tests
st.markdown("---")
st.write("### Zusätzliche Tests")

# Netzwerk-Test
if st.button("🌐 Teste Google API Erreichbarkeit"):
    import requests
    try:
        response = requests.get("https://sheets.googleapis.com", timeout=5)
        st.success(f"✅ Google Sheets API erreichbar (Status: {response.status_code})")
    except Exception as e:
        st.error(f"❌ Google Sheets API nicht erreichbar: {e}")

# Secrets-Details
if st.button("🔐 Zeige Secrets-Details"):
    if "gcp_service_account" in st.secrets:
        creds = st.secrets["gcp_service_account"]
        st.success("✅ Secrets verfügbar")
        
        # Zeige wichtige Felder
        important_fields = ["type", "project_id", "client_email", "private_key_id"]
        for field in important_fields:
            if field in creds:
                if field == "private_key_id":
                    st.write(f"**{field}:** {creds[field][:10]}...")
                else:
                    st.write(f"**{field}:** {creds[field]}")
        
        # Prüfe ob private_key vorhanden ist
        if "private_key" in creds:
            key_length = len(creds["private_key"])
            st.write(f"**private_key:** {key_length} Zeichen")
        else:
            st.error("❌ private_key fehlt")
    else:
        st.error("❌ Secrets nicht verfügbar")

# Berechtigungs-Hilfe
st.markdown("---")
st.write("### 🔧 Berechtigungs-Hilfe")

st.info("""
**Wenn die Tests fehlschlagen:**

1. **Service Account Email prüfen:** Die oben angezeigte Email muss Zugriff auf die Google Sheets haben
2. **Sheets teilen:** Gehe zu jedem Google Sheet und teile es mit der Service Account Email
3. **Berechtigungen:** Mindestens "Viewer" Berechtigung erforderlich
4. **Sheet-Namen:** Prüfe ob die Sheet-Namen exakt stimmen

**Service Account Email finden:**
- Wird oben unter "Service Account Details" angezeigt
- Format: `name@project-id.iam.gserviceaccount.com`
""") 