# Gebietsplaner.py

import streamlit as st
import matplotlib.colors as mcolors
from daten import lade_daten  # Import aus unserer neuen Datei
from karten import zeichne_karte # Import aus unserer neuen Datei

# --- SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Interaktive Gebietsplanung",
    page_icon="🗺️",
    layout="wide"
)

# --- HAUPTANWENDUNG ---
st.title("🗺️ Interaktive Gebietsplanung")
st.markdown("IST-Zustand basierend auf der Planung für 03/2025")

# Daten über das separate Modul laden
df = lade_daten()

# Die App wird nur angezeigt, wenn die Daten erfolgreich geladen wurden
if not df.empty:
    # --- SEITENLEISTE MIT FILTERN ---
    st.sidebar.header("Filter-Optionen")
    
    verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df[df['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    selected_vertreter = st.sidebar.multiselect(
        'Vertreter auswählen:',
        options=verfuegbare_vertreter,
        default=verfuegbare_vertreter
    )

    # --- DATENFILTERUNG ---
    if selected_verlag == 'Alle Verlage':
        df_filtered = df[df['Vertreter_Name'].isin(selected_vertreter)]
    else:
        df_filtered = df[(df['Verlag'] == selected_verlag) & (df['Vertreter_Name'].isin(selected_vertreter))]

    # --- DASHBOARD-ANZEIGE ---
    st.subheader("Analyse der Auswahl")
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Vertreter", f"{len(selected_vertreter)}")
    col2.metric("Anzahl Kunden", f"{len(df_filtered):,}".replace(',', '.'))
    col3.metric("Jahresumsatz 2024", f"{int(df_filtered['Umsatz_2024'].sum()):,} €".replace(',', '.'))

    st.subheader("Gebietskarte")
    
    # Farbpalette für eine konsistente Darstellung erstellen
    vertreter_liste = sorted(df['Vertreter_Name'].unique())
    # Eine große Palette, um Farb-Kollisionen zu vermeiden
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
    
    # Die Karte über die importierte Funktion zeichnen lassen
    zeichne_karte(df_filtered, farb_map)

    # Optional: Anzeige der Rohdaten-Tabelle
    if st.checkbox("Gefilterte Rohdaten anzeigen"):
        st.dataframe(df_filtered)
else:
    st.warning("Daten konnten nicht geladen werden. Die Anwendung kann nicht angezeigt werden.")