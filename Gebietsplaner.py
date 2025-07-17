# Gebietsplaner.py - Finale Version

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import numpy as np
# Stellen Sie sicher, dass die src-Struktur korrekt ist
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte
import matplotlib.colors as mcolors

# --- 2. SEITEN-KONFIGURATION ---
st.set_page_config(layout="wide", page_title="Gebietsplanung", page_icon="🗺️")

# --- 3. HELFER-FUNKTIONEN & INITIALISIERUNG ---

def initialisiere_app_zustand():
    """Initialisiert den Session State beim ersten Laden der App."""
    if 'app_initialisiert' not in st.session_state:
        st.session_state.df_basis = lade_basis_daten()
        # 'df_aktuell' hält den Zustand der Gebietsverteilung, die angezeigt und bearbeitet wird.
        st.session_state.df_aktuell = st.session_state.df_basis.copy()
        st.session_state.app_initialisiert = True
        # Initialisiert den Zustand für die Vertreter-Auswahl
        st.session_state.selected_vertreter = []


def optimierungs_algorithmus(dataframe_basis, weights, constraints):
    """Platzhalter für den komplexen Optimierungsalgorithmus."""
    df_opt = dataframe_basis.copy()
    # ... (Hier würde die Logik aus Phase 1 & 2 eingefügt werden) ...
    st.info(f"Optimierung mit folgenden Gewichten gestartet: {weights}")
    if constraints['top_kunden_sperren']:
        st.info("Constraint 'Top 10% Kunden sperren' ist aktiv.")
    return df_opt


# --- 4. LOGIN-LOGIK ---
# (Hier wäre Ihre st.login() Logik. Zur einfacheren Entwicklung überspringen wir sie hier.)
# Annahme: Nutzer ist eingeloggt und berechtigt.

# --- 5. HAUPTANWENDUNG ---
st.title("🗺️ Interaktive Gebietsplanung")

initialisiere_app_zustand()
df = st.session_state.get('df_aktuell', pd.DataFrame())

if not df.empty:
    # --- SEITENLEISTE ---
    with st.sidebar:
        st.header("Szenario Management")

        # SZENARIO LADEN
        szenarien_liste = lade_szenarien_liste()
        geladenes_szenario = st.selectbox("Szenario laden:", options=['Aktueller IST-Zustand'] + szenarien_liste)

        if st.button("Ausgewähltes Szenario laden"):
            if geladenes_szenario == 'Aktueller IST-Zustand':
                st.session_state.df_aktuell = st.session_state.df_basis.copy()
            else:
                neue_zuweisung = lade_szenario_zuweisung(geladenes_szenario)
                if neue_zuweisung is not None:
                    # Die Zuweisung im DataFrame aktualisieren
                    basis_copy = st.session_state.df_basis.copy().set_index('Kunden_Nr')
                    basis_copy.update(neue_zuweisung)
                    st.session_state.df_aktuell = basis_copy.reset_index()
            st.toast(f"Szenario '{geladenes_szenario}' geladen!")
            st.rerun()

        # SZENARIO SPEICHERN
        st.markdown("---")
        neuer_szenario_name = st.text_input("Neuen Szenario-Namen eingeben:")
        if st.button("Aktuelle Ansicht als Szenario speichern"):
            if neuer_szenario_name:
                zuweisung_zum_speichern = st.session_state.df_aktuell[['Kunden_Nr', 'Vertreter_Name']]
                if speichere_szenario(neuer_szenario_name, zuweisung_zum_speichern):
                    st.toast(f"Szenario '{neuer_szenario_name}' erfolgreich gespeichert!")
            else:
                st.warning("Bitte einen Namen für das Szenario eingeben.")
        
        # OPTIMIERUNGS-OPTIONEN
        st.markdown("---")
        st.header("Optimierungs-Optionen")
        st.subheader("1. Kriterien gewichten")
        
        # Slider für die Gewichtung
        w_arbeitslast = st.slider("Balance der Arbeitslast", 0, 100, 50)
        w_potenzial = st.slider("Balance des Potenzials", 0, 100, 30)
        w_effizienz = st.slider("Reise-Effizienz", 0, 100, 20)
        st.caption("Die Regler bestimmen das Verhältnis der Ziele zueinander.")

        weights = {'Arbeitslast': w_arbeitslast, 'Potenzial': w_potenzial, 'Effizienz': w_effizienz}

        st.subheader("2. Regeln (Constraints) festlegen")
        c_top_kunden_sperren = st.checkbox("Top 10% Kunden sperren", value=True)
        c_kontinuitaet_belohnen = st.checkbox("Kunden-Kontinuität belohnen", value=True)
        constraints = {'top_kunden_sperren': c_top_kunden_sperren, 'kontinuitaet_belohnen': c_kontinuitaet_belohnen}
        
        st.markdown("---")
        if st.button("Neue Gebietsverteilung berechnen", type="primary"):
            with st.spinner("Optimiere Gebiete..."):
                df_optimiert = optimierungs_algorithmus(st.session_state.df_basis, weights, constraints)
                st.session_state.df_aktuell = df_optimiert
                st.toast("Optimierung abgeschlossen!")
                st.rerun()

    # --- ANZEIGE-FILTER ---
    st.sidebar.markdown("---")
    st.sidebar.header("Anzeige-Filter")
    verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen, key='verlag_filter')

    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df[df['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    # Buttons zur Steuerung der Vertreter-Auswahl
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Alle auswählen"):
        st.session_state.selected_vertreter = verfuegbare_vertreter
    if col2.button("Auswahl aufheben"):
        st.session_state.selected_vertreter = []

    selected_vertreter = st.sidebar.multiselect(
        'Vertreter auswählen:',
        options=verfuegbare_vertreter,
        default=st.session_state.get('selected_vertreter', verfuegbare_vertreter)
    )
    st.session_state.selected_vertreter = selected_vertreter # Auswahl speichern

    # --- DATENFILTERUNG FÜR ANZEIGE ---
    df_filtered_display = df[df['Vertreter_Name'].isin(selected_vertreter)]
    if selected_verlag != 'Alle Verlage':
        df_filtered_display = df_filtered_display[df_filtered_display['Verlag'] == selected_verlag]

    # --- DASHBOARD-ANZEIGE ---
    st.subheader(f"Analyse für: {geladenes_szenario}")
    # ... (Rest der Metriken und Kartenlogik)
    zeichne_karte(df_filtered_display, {name: 'color' for name in df['Vertreter_Name'].unique()}) # Platzhalter für farb_map


else:
    st.warning("Daten konnten nicht geladen werden. Die Anwendung kann nicht angezeigt werden.")