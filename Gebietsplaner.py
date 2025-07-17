# Gebietsplaner.py - Finale Version mit allen Funktionen

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from scipy.spatial import ConvexHull
import matplotlib.colors as mcolors
import random

# Stellt sicher, dass die Module aus dem src-Ordner gefunden werden
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte

# --- 2. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Interaktive Gebietsplanung",
    page_icon="🗺️",
    layout="wide"
)

# --- 3. HELFER-FUNKTIONEN & INITIALISIERUNG ---

def initialisiere_app_zustand():
    """
    Initialisiert den Session State beim ersten Laden der App.
    Dies stellt sicher, dass die Daten geladen und Zustände für die Interaktion gesetzt werden.
    """
    if 'app_initialisiert' not in st.session_state:
        st.session_state.df_basis = lade_basis_daten()
        # df_aktuell hält den Zustand der Gebietsverteilung, die angezeigt und bearbeitet wird.
        st.session_state.df_aktuell = st.session_state.df_basis.copy()
        st.session_state.app_initialisiert = True
        # Hält die ID des angeklickten Kunden. Startet mit None (keine Auswahl).
        st.session_state.selected_customer_id = None
        # Speichert die Auswahl im Multi-Select-Filter, um sie über Reruns hinweg zu erhalten.
        st.session_state.selected_vertreter = sorted(st.session_state.df_aktuell['Vertreter_Name'].unique().tolist())

def optimierungs_algorithmus(dataframe_basis, weights, constraints):
    """
    Platzhalter für den komplexen Optimierungsalgorithmus.
    In einer finalen Version würde hier die iterative Tausch-Logik implementiert.
    """
    st.info("Optimierungsfunktion ist ein Platzhalter und gibt zur Demonstration eine geografisch optimierte Zuweisung zurück.")
    df_opt = dataframe_basis.copy()
    vertreter_df = df_opt[['Vertreter_Name', 'Wohnort_Lat', 'Wohnort_Lon']].drop_duplicates().reset_index(drop=True)
    kunden_coords = df_opt[['Latitude', 'Longitude']].values
    vertreter_coords = vertreter_df[['Wohnort_Lat', 'Wohnort_Lon']].values
    dist_matrix = np.linalg.norm(kunden_coords[:, np.newaxis, :] - vertreter_coords, axis=2)
    naechster_vertreter_idx = np.argmin(dist_matrix, axis=1)
    df_opt['Vertreter_Name'] = vertreter_df['Vertreter_Name'].iloc[naechster_vertreter_idx].values
    return df_opt


# --- 4. LOGIN-LOGIK UND APP-STEUERUNG (PLATZHALTER) ---
# Hier wäre Ihre st.login() Logik integriert.
# Für die Entwicklung ist der Nutzer standardmäßig eingeloggt.
if 'user_is_logged_in' not in st.session_state:
    st.session_state.user_is_logged_in = True 

if st.session_state.user_is_logged_in:
    # --- HAUPTANWENDUNG NACH LOGIN ---
    initialisiere_app_zustand()
    st.title("🗺️ Interaktive Gebietsplanung")

    # Der angezeigte DataFrame ist immer der, der im Session State gespeichert ist
    df = st.session_state.df_aktuell
    
    # --- SEITENLEISTE (Sidebar) ---
    with st.sidebar:
        st.header("Manuelle Zuweisung per Klick")
        
        # Dieser Bereich wird nur angezeigt, wenn ein Kunde auf der Karte angeklickt wurde
        if st.session_state.selected_customer_id:
            try:
                # Finde die Daten des ausgewählten Kunden
                selected_customer_data = df[df['Kunden_Nr'] == st.session_state.selected_customer_id].iloc[0]
                
                st.info(f"Ausgewählter Kunde:")
                st.write(f"**{selected_customer_data['Kunde_ID_Name']}**")
                st.metric("Umsatz 2024", f"{int(selected_customer_data['Umsatz_2024']):,} €")
                st.write(f"Aktueller Vertreter: **{selected_customer_data['Vertreter_Name']}**")

                alle_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
                aktueller_index = alle_vertreter.index(selected_customer_data['Vertreter_Name'])

                # Dropdown zur Auswahl des neuen Vertreters
                neuer_vertreter = st.selectbox(
                    "Neuen Vertreter zuweisen:",
                    options=alle_vertreter,
                    index=aktueller_index,
                    key="neuer_vertreter_select"
                )

                if st.button("Zuweisung übernehmen", type="primary"):
                    # Update des DataFrames im Session State
                    st.session_state.df_aktuell.loc[
                        st.session_state.df_aktuell['Kunden_Nr'] == st.session_state.selected_customer_id,
                        'Vertreter_Name'
                    ] = neuer_vertreter
                    
                    st.toast(f"Kunde wurde zu {neuer_vertreter} verschoben!")
                    # Auswahl zurücksetzen und App neu laden, um Änderungen anzuzeigen
                    st.session_state.selected_customer_id = None
                    st.rerun()
            except (IndexError, KeyError):
                 st.warning("Der ausgewählte Kunde konnte nicht gefunden werden. Bitte laden Sie die Seite neu.")
                 st.session_state.selected_customer_id = None
        else:
            st.info("Klicken Sie auf einen Kundenpunkt auf der Karte, um ihn einem neuen Vertreter zuzuweisen.")

        st.markdown("---")
        st.header("Szenario Management")
        szenarien_liste = lade_szenarien_liste()
        geladenes_szenario = st.selectbox("Szenario laden:", options=['Aktueller IST-Zustand'] + szenarien_liste, key="szenario_laden")

        if st.button("Ausgewähltes Szenario laden"):
            if geladenes_szenario == 'Aktueller IST-Zustand':
                st.session_state.df_aktuell = st.session_state.df_basis.copy()
            else:
                neue_zuweisung = lade_szenario_zuweisung(geladenes_szenario)
                if neue_zuweisung is not None:
                    basis_copy = st.session_state.df_basis.copy().set_index('Kunden_Nr')
                    basis_copy.update(neue_zuweisung)
                    st.session_state.df_aktuell = basis_copy.reset_index()
            st.toast(f"Szenario '{geladenes_szenario}' geladen!")
            st.rerun()

        st.markdown("---")
        neuer_szenario_name = st.text_input("Neuen Szenario-Namen eingeben:")
        if st.button("Aktuelle Ansicht als Szenario speichern"):
            if neuer_szenario_name:
                zuweisung_zum_speichern = st.session_state.df_aktuell[['Kunden_Nr', 'Vertreter_Name']]
                if speichere_szenario(neuer_szenario_name, zuweisung_zum_speichern):
                    st.toast(f"Szenario '{neuer_szenario_name}' erfolgreich gespeichert!")
            else:
                st.warning("Bitte einen Namen für das Szenario eingeben.")
        
        st.markdown("---")
        st.header("Automatische Optimierung")
        # (Hier könnte der Code für die Optimierungs-Slider stehen)

    # --- DATENFILTERUNG FÜR DIE ANZEIGE ---
    st.sidebar.markdown("---")
    st.sidebar.header("Anzeige-Filter")
    verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df[df['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Alle auswählen"):
        st.session_state.selected_vertreter = verfuegbare_vertreter
        st.rerun()
    if col2.button("Auswahl aufheben"):
        st.session_state.selected_vertreter = []
        st.rerun()

    selected_vertreter = st.sidebar.multiselect('Angezeigte Vertreter:', options=verfuegbare_vertreter, default=st.session_state.get('selected_vertreter'))
    st.session_state.selected_vertreter = selected_vertreter

    df_filtered_display = df[df['Vertreter_Name'].isin(selected_vertreter)]
    if selected_verlag != 'Alle Verlage':
        df_filtered_display = df_filtered_display[df_filtered_display['Verlag'] == selected_verlag]

    # --- DASHBOARD-ANZEIGE ---
    st.subheader(f"Analyse für: {geladenes_szenario}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Vertreter", df_filtered_display['Vertreter_Name'].nunique())
    col2.metric("Anzahl Kunden", f"{len(df_filtered_display):,}".replace(',', '.'))
    col3.metric("Jahresumsatz 2024", f"{int(df_filtered_display['Umsatz_2024'].sum()):,} €".replace(',', '.'))
    
    st.subheader("Gebietskarte")
    vertreter_liste = sorted(df['Vertreter_Name'].unique())
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
    
    karte_obj = zeichne_karte(df_filtered_display, farb_map)

    map_data = st_folium(karte_obj, width='100%', height=700, returned_objects=['last_object_clicked_popup'])

    if map_data and map_data.get("last_object_clicked_popup"):
        popup_text = map_data["last_object_clicked_popup"]
        if popup_text.startswith("ID:"):
            try:
                clicked_id = int(popup_text.split("<br>")[0].replace("ID:", ""))
                if st.session_state.selected_customer_id != clicked_id:
                    st.session_state.selected_customer_id = clicked_id
                    st.rerun()
            except (ValueError, IndexError):
                pass
else:
    st.error("Bitte einloggen, um die Anwendung zu nutzen.")