# Gebietsplaner.py - Finale Version mit allen Funktionen

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import numpy as np
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte
import matplotlib.colors as mcolors
import random
from tqdm import tqdm # Import für einen Fortschrittsbalken im Terminal/Log

# --- 2. SEITEN-KONFIGURATION ---
st.set_page_config(layout="wide", page_title="Gebietsplanung", page_icon="🗺️")

# --- 3. HELFER-FUNKTIONEN & INITIALISIERUNG ---

def initialisiere_app_zustand():
    """Initialisiert den Session State beim ersten Laden der App."""
    if 'app_initialisiert' not in st.session_state:
        st.session_state.df_basis = lade_basis_daten()
        st.session_state.df_aktuell = st.session_state.df_basis.copy()
        st.session_state.app_initialisiert = True
        st.session_state.selected_vertreter = sorted(st.session_state.df_aktuell['Vertreter_Name'].unique().tolist())

def optimierungs_algorithmus(dataframe_basis, weights, constraints):
    """Führt den vollständigen, iterativen Optimierungsalgorithmus aus."""
    st.info("Beginne Optimierung...")
    df_opt = dataframe_basis.copy()

    # Referenz-Daten für die Berechnung
    vertreter_df = df_opt[['Vertreter_Name', 'Wohnort_Lat', 'Wohnort_Lon']].drop_duplicates().reset_index(drop=True)
    global_avg_kunden = len(df_opt) / len(vertreter_df)
    global_avg_umsatz = df_opt['Umsatz_2024'].sum() / len(vertreter_df)

    # --- PHASE 1: GEOGRAFISCHE INITIALZUWEISUNG ---
    st.info("Phase 1: Erstelle eine geografisch kompakte Start-Zuweisung...")
    kunden_coords = df_opt[['Latitude', 'Longitude']].values
    vertreter_coords = vertreter_df[['Wohnort_Lat', 'Wohnort_Lon']].values
    dist_matrix = np.linalg.norm(kunden_coords[:, np.newaxis, :] - vertreter_coords, axis=2)
    naechster_vertreter_idx = np.argmin(dist_matrix, axis=1)
    df_opt['Vertreter_Name'] = vertreter_df['Vertreter_Name'].iloc[naechster_vertreter_idx].values

    # --- KOSTEN- & CONSTRAINT-FUNKTIONEN (INTERN) ---
    def ueberpruefe_constraints(df_check, betroffene_vertreter):
        # Funktion zur Überprüfung der harten Regeln
        summary = df_check[df_check['Vertreter_Name'].isin(betroffene_vertreter)].groupby('Vertreter_Name').agg(Anzahl_Kunden=('Kunden_Nr', 'count'), Gesamtumsatz=('Umsatz_2024', 'sum'))
        # Prüft, ob einer der betroffenen Vertreter die 20%-Kunden- oder 25%-Umsatz-Regel verletzt
        if (abs(summary['Anzahl_Kunden'] - global_avg_kunden) / global_avg_kunden > 0.20).any(): return False
        if (abs(summary['Gesamtumsatz'] - global_avg_umsatz) / global_avg_umsatz > 0.25).any(): return False
        return True

    def berechne_kosten(df_check, weights):
        # Funktion zur Berechnung der Gesamtkosten
        summary = df_check.groupby('Vertreter_Name').agg(Anzahl_Kunden=('Kunden_Nr', 'count'), Gesamtumsatz=('Umsatz_2024', 'sum'))
        # Kosten durch Ungleichheit (Standardabweichung als Maß)
        kosten_arbeitslast_norm = summary['Anzahl_Kunden'].std() / global_avg_kunden
        kosten_potenzial_norm = summary['Gesamtumsatz'].std() / global_avg_umsatz
        return (weights['Arbeitslast'] * kosten_arbeitslast_norm + weights['Potenzial'] * kosten_potenzial_norm)

    # --- PHASE 2: ITERATIVER TAUSCH-ALGORITHMUS ---
    st.info("Phase 2: Führe iterativen Tausch-Algorithmus zur Verbesserung aus...")
    
    # Top-Kunden sperren, falls die Regel aktiv ist
    if constraints['top_kunden_sperren']:
        umsatz_schwelle_top_10 = df_opt['Umsatz_2024'].quantile(0.90)
        tauschbare_kunden_indices = df_opt[df_opt['Umsatz_2024'] < umsatz_schwelle_top_10].index
    else:
        tauschbare_kunden_indices = df_opt.index

    aktuelle_kosten = berechne_kosten(df_opt, weights)
    
    # Der Algorithmus macht 5000 Tauschversuche
    progress_bar = st.progress(0, text="Optimierungsfortschritt...")
    for i in range(5000):
        # Wähle einen zufälligen (tauschbaren) Kunden
        kunde_idx = random.choice(tauschbare_kunden_indices)
        original_vertreter = df_opt.loc[kunde_idx, 'Vertreter_Name']
        
        # Wähle den zweitnächsten Vertreter als Tausch-Kandidat
        zweitnaechster_idx = np.argsort(dist_matrix[kunde_idx])[1]
        neuer_vertreter = vertreter_df['Vertreter_Name'].iloc[zweitnaechster_idx]

        if original_vertreter == neuer_vertreter: continue

        # Simuliere den Tausch
        df_opt.loc[kunde_idx, 'Vertreter_Name'] = neuer_vertreter
        
        # Prüfe, ob die harten Regeln verletzt werden
        if not ueberpruefe_constraints(df_opt, [original_vertreter, neuer_vertreter]):
            df_opt.loc[kunde_idx, 'Vertreter_Name'] = original_vertreter # Tausch rückgängig
            continue

        # Wenn Regeln ok sind, prüfe, ob die Kosten sinken
        neue_kosten = berechne_kosten(df_opt, weights)
        if neue_kosten >= aktuelle_kosten:
            df_opt.loc[kunde_idx, 'Vertreter_Name'] = original_vertreter # Tausch rückgängig
        else:
            aktuelle_kosten = neue_kosten # Tausch beibehalten

        if (i + 1) % 100 == 0:
            progress_bar.progress((i + 1) / 5000, text=f"Iteration {i+1}/5000")
    
    progress_bar.empty()
    return df_opt


# --- LOGIN-LOGIK UND APP-STEUERUNG (PLATZHALTER) ---
# Hier wäre Ihre st.login() Logik integriert
if 'user_is_logged_in' not in st.session_state:
    st.session_state.user_is_logged_in = True # Für die Entwicklung auf True gesetzt

if st.session_state.user_is_logged_in:
    # --- HAUPTANWENDUNG NACH LOGIN ---
    initialisiere_app_zustand()
    df_angezeigt = st.session_state.df_aktuell
    
    st.title("🗺️ Interaktive Gebietsplanung")

    # --- SEITENLEISTE ---
    with st.sidebar:
        st.header("Szenario Management")

        # SZENARIO LADEN
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
        
        w_arbeitslast = st.slider("Balance der Arbeitslast", 0, 100, 50)
        w_potenzial = st.slider("Balance des Potenzials", 0, 100, 30)
        w_effizienz = st.slider("Reise-Effizienz", 0, 100, 20)
        weights = {'Arbeitslast': w_arbeitslast, 'Potenzial': w_potenzial, 'Effizienz': w_effizienz}

        st.subheader("2. Regeln (Constraints) festlegen")
        c_top_kunden_sperren = st.checkbox("Top 10% Kunden sperren", value=True)
        constraints = {'top_kunden_sperren': c_top_kunden_sperren}
        
        st.markdown("---")
        if st.button("Neue Gebietsverteilung berechnen", type="primary"):
            df_optimiert = optimierungs_algorithmus(st.session_state.df_basis, weights, constraints)
            st.session_state.df_aktuell = df_optimiert
            st.toast("Optimierung abgeschlossen!")
            st.rerun()

    # --- ANZEIGE-FILTER ---
    st.sidebar.markdown("---")
    st.sidebar.header("Anzeige-Filter")
    verlag_optionen = ['Alle Verlage'] + sorted(df_angezeigt['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df_angezeigt['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df_angezeigt[df_angezeigt['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Alle auswählen", key="select_all"):
        st.session_state.selected_vertreter = verfuegbare_vertreter
        st.rerun()
    if col2.button("Auswahl aufheben", key="deselect_all"):
        st.session_state.selected_vertreter = []
        st.rerun()

    selected_vertreter = st.sidebar.multiselect(
        'Vertreter auswählen:',
        options=verfuegbare_vertreter,
        default=st.session_state.get('selected_vertreter', verfuegbare_vertreter)
    )
    st.session_state.selected_vertreter = selected_vertreter

    # --- DATENFILTERUNG FÜR ANZEIGE ---
    df_filtered_display = df_angezeigt[df_angezeigt['Vertreter_Name'].isin(selected_vertreter)]
    if selected_verlag != 'Alle Verlage':
        df_filtered_display = df_filtered_display[df_filtered_display['Verlag'] == selected_verlag]

    # --- DASHBOARD-ANZEIGE ---
    st.subheader(f"Analyse für: {geladenes_szenario}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Vertreter", df_filtered_display['Vertreter_Name'].nunique())
    col2.metric("Anzahl Kunden", f"{len(df_filtered_display):,}".replace(',', '.'))
    col3.metric("Jahresumsatz 2024", f"{int(df_filtered_display['Umsatz_2024'].sum()):,} €".replace(',', '.'))
    
    st.subheader("Gebietskarte")
    
    vertreter_liste = sorted(df_angezeigt['Vertreter_Name'].unique())
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
    
    zeichne_karte(df_filtered_display, farb_map)