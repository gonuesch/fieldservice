# Gebietsplaner.py - Finale Version mit manueller Kundenzuweisung

# --- 1. BIBLIOTHEKEN IMPORTIEREN ---
import streamlit as st
import pandas as pd
import numpy as np
from src.daten import lade_basis_daten, lade_szenarien_liste, lade_szenario_zuweisung, speichere_szenario
from src.karten import zeichne_karte
import matplotlib.colors as mcolors
import random

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
    """Platzhalter für den komplexen Optimierungsalgorithmus."""
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
    df_angezeigt = st.session_state.df_aktuell
    
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
        st.header("Automatische Optimierung")
        st.subheader("1. Kriterien gewichten")
        
        w_arbeitslast = st.slider("Balance der Arbeitslast", 0, 100, 50)
        w_potenzial = st.slider("Balance des Potenzials", 0, 100, 30)
        w_effizienz = st.slider("Reise-Effizienz", 0, 100, 20)
        weights = {'Arbeitslast': w_arbeitslast, 'Potenzial': w_potenzial, 'Effizienz': w_effizienz}

        st.subheader("2. Regeln festlegen")
        c_top_kunden_sperren = st.checkbox("Top 10% Kunden sperren", value=True)
        constraints = {'top_kunden_sperren': c_top_kunden_sperren}
        
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
    verlag_optionen = ['Alle Verlage'] + sorted(df_angezeigt['Verlag'].unique().tolist())
    selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

    if selected_verlag == 'Alle Verlage':
        verfuegbare_vertreter = sorted(df_angezeigt['Vertreter_Name'].unique().tolist())
    else:
        verfuegbare_vertreter = sorted(df_angezeigt[df_angezeigt['Verlag'] == selected_verlag]['Vertreter_Name'].unique().tolist())
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Alle auswählen"):
        st.session_state.selected_vertreter = verfuegbare_vertreter
        st.rerun()
    if col2.button("Auswahl aufheben"):
        st.session_state.selected_vertreter = []
        st.rerun()

    selected_vertreter = st.sidebar.multiselect(
        'Angezeigte Vertreter:',
        options=verfuegbare_vertreter,
        default=st.session_state.get('selected_vertreter', verfuegbare_vertreter)
    )
    st.session_state.selected_vertreter = selected_vertreter

    # --- DATENFILTERUNG FÜR DIE ANZEIGE ---
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

    # --- MANUELLE KUNDEN-ZUWEISUNG (NEUE SEKTION) ---
    st.markdown("---")
    with st.expander("Manuelle Kunden-Zuweisung"):
        st.info("Hier können Sie einzelne Kunden von einem Vertreter zu einem anderen verschieben. Änderungen werden sofort wirksam und können als neues Szenario gespeichert werden.")

        # 1. Auswahl des zu bearbeitenden Vertreters
        alle_vertreter = sorted(df_angezeigt['Vertreter_Name'].unique().tolist())
        quell_vertreter = st.selectbox(
            "Kunden anzeigen von Vertreter:",
            options=alle_vertreter,
            key="quell_vertreter_select"
        )

        # 2. Tabelle der Kunden dieses Vertreters anzeigen
        if quell_vertreter:
            kunden_des_vertreters = df_angezeigt[df_angezeigt['Vertreter_Name'] == quell_vertreter].sort_values(by="Umsatz_2024", ascending=False)
            
            st.write(f"Kunden von **{quell_vertreter}**:")

            # Für jeden Kunden eine Zeile mit einer Auswahlbox erstellen
            for _, kunde in kunden_des_vertreters.iterrows():
                # Wir verwenden die Kunden_Nr, um einen stabilen Index zu haben
                kunden_index = kunde.name 
                
                cols = st.columns([3, 2, 2])
                cols[0].write(f"{kunde['Kunde_ID_Name']} ({kunde['Kunden_PLZ']} {kunde['Kunden_Ort']})")
                cols[1].metric("Umsatz 2024", f"{int(kunde['Umsatz_2024']):,} €")
                
                # Dropdown zur Neuzuweisung
                neuer_vertreter = cols[2].selectbox(
                    "Neuer Vertreter",
                    options=alle_vertreter,
                    index=alle_vertreter.index(kunde['Vertreter_Name']),
                    key=f"select_{kunde['Kunden_Nr']}" # Eindeutiger Schlüssel für jedes Widget
                )

                # Wenn eine Änderung vorgenommen wurde, aktualisiere den DataFrame im Session State
                if neuer_vertreter != kunde['Vertreter_Name']:
                    # Wir ändern den Wert im DataFrame des Session States
                    st.session_state.df_aktuell.loc[st.session_state.df_aktuell['Kunden_Nr'] == kunde['Kunden_Nr'], 'Vertreter_Name'] = neuer_vertreter
                    st.toast(f"Kunde zu {neuer_vertreter} verschoben!")
                    # Seite neu laden, damit alle KPIs und die Karte die Änderung reflektieren
                    st.rerun()

else:
    st.error("Keine Daten geladen. Die Anwendung kann nicht gestartet werden.")