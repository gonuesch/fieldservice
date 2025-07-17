# Gebietsplaner.py - Finale Version mit interaktiver Kartenzuweisung

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import matplotlib.colors as mcolors
# Stellt sicher, dass die Module aus dem src-Ordner gefunden werden
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte
# Wichtig für die Karten-Interaktion
from streamlit_folium import st_folium

# --- 2. SEITEN-KONFIGURATION ---
st.set_page_config(
    page_title="Interaktive Gebietsplanung",
    page_icon="🗺️",
    layout="wide"
)

# --- 3. HELFER-FUNKTIONEN & INITIALISIERUNG ---
def initialisiere_app_zustand():
    """Initialisiert den Session State beim ersten Laden der App."""
    if 'app_initialisiert' not in st.session_state:
        st.session_state.df_basis = lade_basis_daten()
        # df_aktuell hält den Zustand der Gebietsverteilung, die angezeigt und bearbeitet wird.
        st.session_state.df_aktuell = st.session_state.df_basis.copy()
        st.session_state.app_initialisiert = True
        # Hält die ID des angeklickten Kunden. Startet mit None (keine Auswahl).
        st.session_state.selected_customer_id = None
        # Speichert die Auswahl im Multi-Select-Filter
        st.session_state.selected_vertreter = sorted(st.session_state.df_aktuell['Vertreter_Name'].unique().tolist())

def optimierungs_algorithmus(dataframe_basis, weights, constraints):
    """Platzhalter für den komplexen Optimierungsalgorithmus."""
    st.info("Optimierungsfunktion ist ein Platzhalter.")
    # In einer finalen Version würde hier der komplexe Tausch-Algorithmus stehen.
    return dataframe_basis.copy()


# --- 4. LOGIN-LOGIK UND APP-STEUERUNG (PLATZHALTER) ---
# Hier wäre Ihre st.login() Logik integriert.
# Für die Entwicklung ist der Nutzer standardmäßig eingeloggt.
if 'user_is_logged_in' not in st.session_state:
    st.session_state.user_is_logged_in = True 

if st.session_state.user_is_logged_in:
    # --- HAUPTANWENDUNG NACH LOGIN ---
    initialisiere_app_zustand()
    st.title("🗺️ Interaktive Gebietsplanung")

    # Wir arbeiten immer auf der Kopie im Session State
    df = st.session_state.df_aktuell
    
    # --- SEITENLEISTE (Sidebar) ---
    with st.sidebar:
        # --- Manuelle Zuweisung per Klick (NEUE SEKTION) ---
        st.header("Manuelle Zuweisung")
        
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

        # --- SZENARIO MANAGEMENT & OPTIMIERUNG ---
        st.markdown("---")
        st.header("Szenarien & Optimierung")
        # (Der Code für Laden/Speichern und die Optimierungs-Slider bleibt hier, gekürzt zur Übersicht)

    # --- DATENFILTERUNG FÜR DIE ANZEIGE ---
    st.sidebar.markdown("---")
    st.sidebar.header("Anzeige-Filter")
    # (Der Code für die Anzeige-Filter bleibt hier, gekürzt zur Übersicht)
    
    df_filtered_display = df # Platzhalter, hier wäre Ihre Filterlogik

    # --- DASHBOARD-ANZEIGE ---
    st.subheader("Analyse der aktuellen Gebietsverteilung")
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Vertreter", df_filtered_display['Vertreter_Name'].nunique())
    col2.metric("Anzahl Kunden", f"{len(df_filtered_display):,}".replace(',', '.'))
    col3.metric("Jahresumsatz 2024", f"{int(df_filtered_display['Umsatz_2024'].sum()):,} €".replace(',', '.'))
    
    st.subheader("Gebietskarte")
    
    # Farbpalette erstellen
    vertreter_liste = sorted(df['Vertreter_Name'].unique())
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
    
    # Karte als Objekt erstellen
    karte_obj = zeichne_karte(df_filtered_display, farb_map)

    # Karte mit st_folium anzeigen und auf Klicks lauschen
    map_data = st_folium(karte_obj, width='100%', height=700, returned_objects=['last_object_clicked_popup'])

    # Überprüfen, ob auf einen Kunden geklickt wurde
    if map_data and map_data.get("last_object_clicked_popup"):
        popup_text = map_data["last_object_clicked_popup"]
        
        # Extrahieren der Kunden-ID aus dem Popup-Text
        if popup_text.startswith("ID:"):
            try:
                clicked_id = int(popup_text.split("<br>")[0].replace("ID:", ""))
                # Wenn ein neuer Kunde geklickt wurde, speichere seine ID und lade die App neu
                if st.session_state.selected_customer_id != clicked_id:
                    st.session_state.selected_customer_id = clicked_id
                    st.rerun()
            except (ValueError, IndexError):
                # Ignoriere Klicks, die keine gültige ID enthalten (z.B. auf Polygone)
                pass
else:
    st.error("Bitte einloggen, um die Anwendung zu nutzen.")