# Gebietsplaner.py

import streamlit as st
import matplotlib.colors as mcolors

# Wir stellen sicher, dass die Module gefunden werden
# (Diese Methode ist die robusteste für Cloud-Umgebungen)
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daten import lade_daten
from karten import zeichne_karte

# --- SEITEN-KONFIGURATION ---
st.set_page_config(layout="wide", page_title="Gebietsplanung", page_icon="🗺️")

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
        st.markdown("IST-Zustand basierend auf der Planung für 03/2025")

        df = lade_daten()

        if not df.empty:
            # Hier folgt der gesamte restliche Dashboard-Code...
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