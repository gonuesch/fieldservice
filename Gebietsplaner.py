# Gebietsplaner.py

import streamlit as st
import matplotlib.colors as mcolors
import pandas as pd

# Wir stellen sicher, dass die Module gefunden werden
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import der ausgelagerten Funktionen
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte

# --- SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Interaktive Gebietsplanung",
    page_icon="🗺️",
    layout="wide"
)

# --- LOGIN-LOGIK UND APP-STEUERUNG ---
if not st.user.is_logged_in:
    # Zeige den Login-Button, wenn der Nutzer nicht eingeloggt ist.
    st.title("Willkommen beim Gebietsplanungs-Tool")
    st.info("Bitte melden Sie sich mit Ihrem Google-Konto an, um fortzufahren.")
    st.button("Mit Google einloggen", on_click=st.login, args=("google",))
else:
    # Wenn der Nutzer eingeloggt ist, prüfe seine E-Mail-Adresse
    user_email = st.user.email
    allowed_emails = [
        "gordon.nuesch@rowohlt.de"
        # Fügen Sie hier weitere berechtigte E-Mail-Adressen hinzu
    ]

    if user_email in allowed_emails:
        # ---- ERLAUBTER ZUGRIFF: Die eigentliche App anzeigen ----
        st.sidebar.success(f"Eingeloggt als {user_email}")
        st.sidebar.button("Logout", on_click=st.logout)
        
        st.title("🗺️ Interaktive Gebietsplanung")

        # Basisdaten (Koordinaten, Umsätze etc.) laden
        basis_df = lade_basis_daten()

        if not basis_df.empty:
            # Den aktuellen Zustand der Gebietszuweisung im Session State speichern.
            # Dies ermöglicht es uns, Änderungen vorzunehmen, ohne die Basisdaten zu verändern.
            if 'aktuelle_zuweisung' not in st.session_state:
                st.session_state.aktuelle_zuweisung = basis_df[['Kunden_Nr', 'Vertreter_Name']].copy()

            # --- SEITENLEISTE: SZENARIO MANAGEMENT ---
            st.sidebar.header("Szenario Management")

            # SZENARIO LADEN
            szenarien_liste = lade_szenarien_liste()
            # "IST-Zustand" als Standard-Option hinzufügen, um zur ursprünglichen Planung zurückzukehren
            geladenes_szenario = st.sidebar.selectbox(
                "Szenario laden:",
                options=['IST-Zustand 03/2025'] + szenarien_liste
            )
            
            if st.sidebar.button("Ausgewähltes Szenario laden"):
                if geladenes_szenario == 'IST-Zustand 03/2025':
                    # Lade die ursprüngliche Zuweisung aus den Basisdaten
                    st.session_state.aktuelle_zuweisung = basis_df[['Kunden_Nr', 'Vertreter_Name']].copy()
                else:
                    # Lade eine gespeicherte Zuweisung aus der Google-Tabelle
                    neue_zuweisung = lade_szenario_zuweisung(geladenes_szenario)
                    if neue_zuweisung is not None:
                        st.session_state.aktuelle_zuweisung = neue_zuweisung.reset_index()
                st.toast(f"Szenario '{geladenes_szenario}' geladen!")
            
            # SZENARIO SPEICHERN
            st.sidebar.markdown("---")
            neuer_szenario_name = st.sidebar.text_input("Neuen Szenario-Namen eingeben:")
            if st.sidebar.button("Aktuelle Ansicht als Szenario speichern"):
                if neuer_szenario_name:
                    # Übergebe die aktuelle Zuweisung aus dem Session State an die Speicherfunktion
                    if speichere_szenario(neuer_szenario_name, st.session_state.aktuelle_zuweisung):
                        st.toast(f"Szenario '{neuer_szenario_name}' erfolgreich gespeichert!")
                else:
                    st.sidebar.warning("Bitte einen Namen für das Szenario eingeben.")

            # Erstelle den finalen Arbeits-DataFrame, indem die Basisdaten mit der *aktuellen* Zuweisung verknüpft werden
            df = basis_df.drop(columns=['Vertreter_Name']).merge(
                st.session_state.aktuelle_zuweisung, on='Kunden_Nr', how='left'
            )

            # --- UI-FILTER UND DARSTELLUNG ---
            st.sidebar.header("Filter-Optionen")
            verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
            selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)
            
            if selected_verlag == 'Alle Verlage':
                verfuegbare_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
            else:
                verfuegbare_vertreter = sorted(df[df['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
            
            selected_vertreter = st.sidebar.multiselect('Vertreter auswählen:', options=verfuegbare_vertreter, default=verfuegbare_vertreter)

            if selected_verlag == 'Alle Verlage':
                df_filtered = df[df['Vertreter_Name'].isin(selected_vertreter)]
            else:
                df_filtered = df[(df['Verlag'] == selected_verlag) & (df['Vertreter_Name'].isin(selected_vertreter))]

            st.subheader("Analyse der Auswahl")
            col1, col2, col3 = st.columns(3)
            col1.metric("Anzahl Vertreter", f"{len(selected_vertreter)}")
            col2.metric("Anzahl Kunden", f"{len(df_filtered):,}".replace(',', '.'))
            col3.metric("Jahresumsatz 2024", f"{int(df_filtered['Umsatz_2024'].sum()):,} €".replace(',', '.'))

            st.subheader("Gebietskarte")
            
            vertreter_liste = sorted(df['Vertreter_Name'].unique())
            palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
            farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
            
            zeichne_karte(df_filtered, farb_map)
    else:
        # ---- UNERLAUBTER ZUGRIFF ----
        st.error("Zugriff verweigert.")
        st.warning(f"Ihre E-Mail-Adresse ({user_email}) ist für diese Anwendung nicht freigeschaltet.")
        st.button("Logout", on_click=st.logout)