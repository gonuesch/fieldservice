# ==============================================================================
#  app.py - Interaktives Tool zur Gebietsplanung
#  Für die lokale Ausführung mit Anaconda / Streamlit
# ==============================================================================

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import matplotlib.colors as mcolors
from streamlit_folium import st_folium # Spezielle Komponente für Folium-Karten
from scipy.spatial import ConvexHull
import os

# --- 2. SEITEN-KONFIGURATION ---
# Dies muss der erste Streamlit-Befehl auf der Seite sein.
st.set_page_config(
    page_title="Interaktive Gebietsplanung",
    page_icon="🗺️",
    layout="wide"  # Nutzt die volle Breite des Bildschirms
)

# --- 3. DATEN LADEN (VOM LOKALEN RECHNER) ---
# Die @st.cache_data Dekoration sorgt dafür, dass die Daten nur einmal geladen
# und im Speicher gehalten werden. Das macht die App extrem schnell.
@st.cache_data
def lade_daten():
    """
    Lädt die Kunden- und Vertreterdaten aus den lokalen CSV-Dateien
    und führt sie zu einer einzigen Arbeitstabelle zusammen.
    """
    kunden_pfad = 'Kunden_mit_Koordinaten_Stand_2025-03.csv'
    vertreter_pfad = 'vertreter_stammdaten_robust.csv'

    # Überprüfen, ob die Dateien existieren
    if not os.path.exists(kunden_pfad) or not os.path.exists(vertreter_pfad):
        st.error(
            f"FEHLER: Eine der Datendateien wurde nicht gefunden. "
            f"Bitte stellen Sie sicher, dass '{kunden_pfad}' und '{vertreter_pfad}' "
            f"im selben Ordner wie die app.py liegen."
        )
        return pd.DataFrame()

    # Daten einlesen
    kunden_df = pd.read_csv(kunden_pfad, sep=';')
    vertreter_df = pd.read_csv(vertreter_pfad, sep=';')

    # Daten zusammenführen
    df_merged = pd.merge(kunden_df, vertreter_df, on='Vertreter_Name', how='left')

    # Datentypen sicherstellen und leere Werte für die Analyse entfernen
    for col in ['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon', 'Umsatz_2024']:
        df_merged[col] = pd.to_numeric(df_merged[col], errors='coerce')
    df_merged.dropna(subset=['Latitude', 'Longitude', 'Wohnort_Lat', 'Wohnort_Lon'], inplace=True)
    
    return df_merged

# Haupt-DataFrame laden
df = lade_daten()

# --- 4. HAUPTANWENDUNG ---
# Die App wird nur angezeigt, wenn die Daten erfolgreich geladen wurden.
if not df.empty:
    st.title("🗺️ Interaktive Gebietsplanung (IST-Zustand 3/2025)")

    # --- SEITENLEISTE MIT FILTERN ---
    st.sidebar.header("Filter-Optionen")

    # a) Verlags-Filter
    verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

    # b) Vertreter-Filter (wird dynamisch basierend auf dem Verlag gefüllt)
    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df[df['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    selected_vertreter = st.sidebar.multiselect(
        'Vertreter auswählen:',
        options=verfuegbare_vertreter,
        default=verfuegbare_vertreter  # Standardmäßig sind alle ausgewählt
    )

    # --- DATENFILTERUNG BASIEREND AUF DER AUSWAHL ---
    if selected_verlag == 'Alle Verlage':
        df_filtered = df[df['Vertreter_Name'].isin(selected_vertreter)]
    else:
        df_filtered = df[(df['Verlag'] == selected_verlag) & (df['Vertreter_Name'].isin(selected_vertreter))]

    # --- DASHBOARD-METRIKEN (KPIs) ---
    st.subheader("Analyse der Auswahl")
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Vertreter", f"{len(selected_vertreter)}")
    col2.metric("Anzahl Kunden", f"{len(df_filtered):,}".replace(',', '.'))
    col3.metric("Jahresumsatz 2024", f"{int(df_filtered['Umsatz_2024'].sum()):,} €".replace(',', '.'))

    # --- INTERAKTIVE KARTE ---
    st.subheader("Gebietskarte")

    # Stabile Farbpalette für die Vertreter erstellen
    vertreter_liste = sorted(df['Vertreter_Name'].unique())
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}

    # Karte initialisieren
    karte = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="cartodbpositron")

    # Für jeden ausgewählten Vertreter die Gebietsfläche und die Punkte zeichnen
    for vertreter_name in df_filtered['Vertreter_Name'].unique():
        vertreter_daten = df_filtered[df_filtered['Vertreter_Name'] == vertreter_name]
        kunden_punkte = vertreter_daten[['Latitude', 'Longitude']].values
        
        # Gebietsfläche (Convex Hull)
        if len(kunden_punkte) >= 3:
            try:
                hull = ConvexHull(kunden_punkte)
                hull_punkte = [list(p) for p in kunden_punkte[hull.vertices]]
                folium.Polygon(
                    locations=hull_punkte,
                    color=farb_map.get(vertreter_name, 'gray'),
                    fill=True,
                    fill_color=farb_map.get(vertreter_name, 'gray'),
                    fill_opacity=0.2,
                    popup=vertreter_name
                ).add_to(karte)
            except Exception:
                # Fehler ignorieren, wenn Hülle nicht erstellt werden kann (z.B. alle Punkte auf einer Linie)
                pass
            
        # Wohnort als Stern-Marker
        wohnort_lat = vertreter_daten['Wohnort_Lat'].iloc[0]
        wohnort_lon = vertreter_daten['Wohnort_Lon'].iloc[0]
        if pd.notna(wohnort_lat):
            folium.Marker(
                [wohnort_lat, wohnort_lon],
                popup=f"Zentrum: {vertreter_name}",
                icon=folium.Icon(color='black', icon_color='white', icon='star')
            ).add_to(karte)

    # Kundenpunkte hinzufügen
    for _, row in df_filtered.iterrows():
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=4,
            popup=f"<b>{row['Kunde_ID_Name']}</b><br>Vertreter: {row['Vertreter_Name']}",
            color=farb_map.get(row['Vertreter_Name']),
            fill=True,
            fill_opacity=0.8
        ).add_to(karte)

    # Die fertige Karte in der Streamlit-App anzeigen
    st_folium(karte, width='100%', height=600, returned_objects=[])

    # Optional: Anzeige der Rohdaten-Tabelle
    if st.checkbox("Gefilterte Rohdaten anzeigen"):
        st.dataframe(df_filtered)