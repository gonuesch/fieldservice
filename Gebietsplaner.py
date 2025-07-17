# Gebietsplaner.py - Version mit interaktiver Optimierung

import streamlit as st
import pandas as pd
import numpy as np
from src.daten import lade_basis_daten
from src.karten import zeichne_karte
import matplotlib.colors as mcolors
import random

# --- SEITEN-KONFIGURATION ---
st.set_page_config(layout="wide", page_title="Gebietsplanung", page_icon="🗺️")

# --- 1. FUNKTIONEN ---

def initialisiere_app_zustand():
    """
    Initialisiert den Zustand der App beim ersten Laden oder nach einem Refresh.
    Lädt die Basisdaten und speichert eine veränderbare Kopie im Session State.
    """
    if 'app_initialisiert' not in st.session_state:
        # Lade die unveränderlichen Basisdaten (Koordinaten, Umsätze etc.)
        st.session_state.df_basis = lade_basis_daten()
        # Erstelle eine Kopie der Zuweisungen, die wir verändern und optimieren können
        st.session_state.df_aktuell = st.session_state.df_basis.copy()
        st.session_state.app_initialisiert = True

def optimierungs_algorithmus(dataframe_basis, weights, constraints):
    """
    Führt den Optimierungsalgorithmus aus.
    Nimmt die Basisdaten und die Nutzereingaben als Input.
    Gibt einen neuen DataFrame mit der optimierten Zuweisung zurück.
    """
    df_opt = dataframe_basis.copy()
    vertreter_df = df_opt[['Vertreter_Name', 'Wohnort_Lat', 'Wohnort_Lon']].drop_duplicates().reset_index(drop=True)

    # --- PHASE 1: GEOGRAFISCHE INITIALZUWEISUNG ---
    # Dieser Schritt ist die Grundlage für die Optimierung.
    st.info("Phase 1: Erstelle eine geografisch kompakte Start-Zuweisung...")
    kunden_coords = df_opt[['Latitude', 'Longitude']].values
    vertreter_coords = vertreter_df[['Wohnort_Lat', 'Wohnort_Lon']].values
    dist_matrix = np.linalg.norm(kunden_coords[:, np.newaxis, :] - vertreter_coords, axis=2)
    naechster_vertreter_idx = np.argmin(dist_matrix, axis=1)
    # Die Spalte 'Vertreter_Name' wird mit der neuen Zuweisung überschrieben
    df_opt['Vertreter_Name'] = vertreter_df['Vertreter_Name'].iloc[naechster_vertreter_idx].values
    
    # --- PHASE 2: ITERATIVE VERBESSERUNG (Platzhalter) ---
    # Hier würde der komplexe Tausch-Algorithmus folgen, der die Kostenfunktion
    # und die Constraints (weights, constraints) berücksichtigt.
    st.info(f"Phase 2: Führe Optimierung mit folgenden Gewichten aus: {weights}")
    if constraints['top_kunden_sperren']:
        st.info("Constraint 'Top 10% Kunden sperren' ist aktiv.")
    
    # Zur Demonstration geben wir hier das Ergebnis der geografischen Optimierung zurück.
    # In einem weiteren Schritt würden wir hier die Tausch-Logik implementieren.
    
    return df_opt


# --- 2. LOGIN-LOGIK UND APP-STEUERUNG ---
if not st.user.is_logged_in:
    st.title("Willkommen beim Gebietsplanungs-Tool")
    st.info("Bitte melden Sie sich mit Ihrem Google-Konto an, um fortzufahren.")
    st.button("Mit Google einloggen", on_click=st.login, args=("google",))
else:
    user_email = st.user.email
    allowed_emails = ["gordon.nuesch@rowohlt.de"]

    if user_email in allowed_emails:
        # --- HAUPTANWENDUNG NACH LOGIN ---
        initialisiere_app_zustand()
        
        # Der angezeigte DataFrame ist immer der, der im session_state gespeichert ist
        df_angezeigt = st.session_state.df_aktuell
        
        st.title("🗺️ Interaktive Gebietsplanung")

        # --- SEITENLEISTE ---
        st.sidebar.success(f"Eingeloggt als {user_email}")
        st.sidebar.button("Logout", on_click=st.logout)
        
        # ANZEIGE-FILTER
        st.sidebar.header("Filter- & Anzeigeoptionen")
        verlag_optionen = ['Alle Verlage'] + sorted(df_angezeigt['Verlag'].unique().tolist())
        selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

        if selected_verlag == 'Alle Verlage':
            verfuegbare_vertreter = sorted(df_angezeigt['Vertreter_Name'].unique().tolist())
        else:
            verfuegbare_vertreter = sorted(df_angezeigt[df_angezeigt['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
        
        selected_vertreter = st.sidebar.multiselect(
            'Angezeigte Vertreter:', options=verfuegbare_vertreter, default=verfuegbare_vertreter
        )
        
        # OPTIMIERUNGS-OPTIONEN
        st.sidebar.markdown("---")
        st.sidebar.header("Optimierungs-Optionen")

        st.sidebar.subheader("1. Kriterien gewichten")
        w_arbeitslast = st.sidebar.slider("Balance der Arbeitslast (Kundenzahl)", 0, 100, 50, key="w_workload")
        w_potenzial = st.sidebar.slider("Balance des Potenzials (Umsatz)", 0, 100, 30, key="w_potential")
        w_effizienz = st.sidebar.slider("Reise-Effizienz (Kompaktheit)", 0, 100, 20, key="w_efficiency")

        # Normiere die Gewichte, damit ihre Summe 1 ergibt
        total_weight = w_arbeitslast + w_potenzial + w_effizienz
        # Sicherstellen, dass nicht durch Null geteilt wird
        if total_weight == 0: total_weight = 1 
        weights = {
            'Arbeitslast': w_arbeitslast / total_weight,
            'Potenzial': w_potenzial / total_weight,
            'Effizienz': w_effizienz / total_weight,
        }

        st.sidebar.subheader("2. Regeln (Constraints) festlegen")
        c_top_kunden_sperren = st.sidebar.checkbox("Top 10% Kunden beim alten Vertreter belassen", value=True, key="c_top_customers")
        c_kontinuitaet_belohnen = st.sidebar.checkbox("Kunden-Kontinuität als Ziel berücksichtigen", value=True, key="c_continuity")

        constraints = {
            'top_kunden_sperren': c_top_kunden_sperren,
            'kontinuitaet_belohnen': c_kontinuitaet_belohnen
        }
        
        st.sidebar.markdown("---")
        if st.sidebar.button("Neue Gebietsverteilung berechnen", type="primary"):
            with st.spinner("Optimiere Gebiete... Dieser Vorgang kann einige Minuten dauern."):
                # Die Optimierung wird immer auf den originalen Basisdaten ausgeführt
                df_optimiert = optimierungs_algorithmus(st.session_state.df_basis, weights, constraints)
                # Das Ergebnis der Optimierung wird zum neuen "aktuellen" Zustand
                st.session_state.df_aktuell = df_optimiert
                st.toast("Optimierung abgeschlossen! Die Ansicht wurde aktualisiert.")
                st.rerun() # Lädt die App neu, um die Änderungen anzuzeigen

        # --- DASHBOARD-ANZEIGE ---
        if not df_angezeigt.empty:
            # Filtere die angezeigten Daten basierend auf den Sidebar-Widgets
            if selected_verlag == 'Alle Verlage':
                df_filtered = df_angezeigt[df_angezeigt['Vertreter_Name'].isin(selected_vertreter)]
            else:
                df_filtered = df_angezeigt[(df_angezeigt['Verlag'] == selected_verlag) & (df_angezeigt['Vertreter_Name'].isin(selected_vertreter))]

            # Metriken
            st.subheader("Analyse der aktuellen Ansicht")
            col1, col2, col3 = st.columns(3)
            col1.metric("Anzahl Vertreter", df_filtered['Vertreter_Name'].nunique())
            col2.metric("Anzahl Kunden", f"{len(df_filtered):,}".replace(',', '.'))
            col3.metric("Jahresumsatz 2024", f"{int(df_filtered['Umsatz_2024'].sum()):,} €".replace(',', '.'))
            
            # Karte
            st.subheader("Gebietskarte")
            vertreter_liste = sorted(df_angezeigt['Vertreter_Name'].unique())
            palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
            farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
            
            zeichne_karte(df_filtered, farb_map)

    else:
        # User ist eingeloggt, aber nicht berechtigt
        st.error("Zugriff verweigert.")
        st.warning(f"Ihre E-Mail-Adresse ({user_email}) ist für diese Anwendung nicht freigeschaltet.")
        st.button("Logout", on_click=st.logout)