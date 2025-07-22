import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import matplotlib.colors as mcolors

# Mock-Daten für lokale Entwicklung
def lade_basis_daten():
    """Mock-Daten für lokale Entwicklung ohne Google Sheets."""
    st.info("🔄 Lade Mock-Daten für lokale Entwicklung...")
    
    # Erstelle Testdaten
    np.random.seed(42)
    n_kunden = 50
    
    # Deutsche Städte mit Koordinaten
    staedte = [
        ("Berlin", 52.5200, 13.4050),
        ("Hamburg", 53.5511, 9.9937),
        ("München", 48.1351, 11.5820),
        ("Köln", 50.9375, 6.9603),
        ("Frankfurt", 50.1109, 8.6821),
        ("Stuttgart", 48.7758, 9.1829),
        ("Düsseldorf", 51.2277, 6.7735),
        ("Dortmund", 51.5136, 7.4653),
        ("Essen", 51.4556, 7.0116),
        ("Leipzig", 51.3397, 12.3731)
    ]
    
    # Vertreter
    vertreter = ["Müller", "Schmidt", "Weber", "Fischer", "Meyer", "Wagner", "Becker", "Schulz"]
    
    # Erstelle Kunden-Daten
    kunden_data = []
    for i in range(n_kunden):
        stadt = staedte[i % len(staedte)]
        # Füge etwas Zufall zu den Koordinaten hinzu
        lat = stadt[1] + np.random.normal(0, 0.01)
        lon = stadt[2] + np.random.normal(0, 0.01)
        
        kunden_data.append({
            'Kunden_Nr': 100000 + i,
            'Kunde_ID_Name': f"Kunde {100000 + i} - {stadt[0]}",
            'Vertreter_Name': vertreter[i % len(vertreter)],
            'Latitude': lat,
            'Longitude': lon,
            'Wohnort_Lat': stadt[1],
            'Wohnort_Lon': stadt[2],
            'Umsatz_2024': np.random.randint(10000, 100000),
            'Verlag': f"Verlag {chr(65 + (i % 5))}"
        })
    
    df = pd.DataFrame(kunden_data)
    st.success(f"✅ {len(df)} Mock-Kunden geladen")
    return df

# Importiere die Karten-Funktion
from src.karten import zeichne_karte

# Initialisiere Session State
if 'app_initialisiert' not in st.session_state:
    st.session_state.df_basis = lade_basis_daten()
    st.session_state.df_aktuell = st.session_state.df_basis.copy()
    st.session_state.app_initialisiert = True
    st.session_state.selected_customer_id = None
    st.session_state.selected_vertreter = sorted(st.session_state.df_aktuell['Vertreter_Name'].unique().tolist())
    st.session_state.zuweisung_history = []

# Haupt-App
st.title("🗺️ Interaktive Gebietsplanung (Lokale Testversion)")

# Der angezeigte DataFrame
df = st.session_state.df_aktuell

# Sidebar
with st.sidebar:
    st.header("🗺️ Manuelle Zuweisung per Klick")
    
    # Undo-Funktion
    if st.session_state.zuweisung_history:
        col1, col2 = st.columns([1, 1])
        if col1.button("↶ Rückgängig", help="Macht die letzte Zuweisung rückgängig"):
            if len(st.session_state.zuweisung_history) > 0:
                letzte_aenderung = st.session_state.zuweisung_history.pop()
                st.session_state.df_aktuell.loc[
                    st.session_state.df_aktuell['Kunden_Nr'] == letzte_aenderung['kunden_id'],
                    'Vertreter_Name'
                ] = letzte_aenderung['alter_vertreter']
                st.toast("Letzte Zuweisung rückgängig gemacht!")
                st.rerun()
        
        if col2.button("🗑️ Auswahl löschen"):
            st.session_state.selected_customer_id = None
            st.rerun()
    
    st.info("👆 **Anleitung:** Klicken Sie auf einen Kundenpunkt auf der Karte, um ihn einem neuen Vertreter zuzuweisen.")
    
    # Zeige letzte Änderungen
    if st.session_state.zuweisung_history:
        st.markdown("---")
        st.markdown("**📋 Letzte Änderungen:**")
        for i, aenderung in enumerate(reversed(st.session_state.zuweisung_history[-3:]), 1):
            st.markdown(f"{i}. Kunde {aenderung['kunden_id']}: {aenderung['alter_vertreter']} → {aenderung['neuer_vertreter']}")

# Datenfilterung
st.sidebar.markdown("---")
st.sidebar.header("Anzeige-Filter")
verlag_optionen = ['Alle Verlage'] + sorted(df['Verlag'].unique().tolist())
selected_verlag = st.sidebar.selectbox('Verlag auswählen:', verlag_optionen)

# Filtere Daten basierend auf Auswahl
if selected_verlag == 'Alle Verlage':
    df_filtered_display = df.copy()
else:
    df_filtered_display = df[df['Verlag'] == selected_verlag].copy()

# Vertreter-Filter
if st.sidebar.checkbox("Vertreter-Filter aktivieren"):
    selected_vertreter_filter = st.sidebar.multiselect(
        "Vertreter auswählen:",
        options=sorted(df['Vertreter_Name'].unique()),
        default=st.session_state.selected_vertreter
    )
    if selected_vertreter_filter:
        df_filtered_display = df_filtered_display[df_filtered_display['Vertreter_Name'].isin(selected_vertreter_filter)]
        st.session_state.selected_vertreter = selected_vertreter_filter

# Kunden-Zuweisung Fenster
if st.session_state.selected_customer_id:
    st.success(f"🎯 **Kunde ausgewählt:** ID {st.session_state.selected_customer_id}")
    try:
        selected_customer_data = df[df['Kunden_Nr'] == st.session_state.selected_customer_id].iloc[0]
        st.markdown("""
        <div style="
            border: 2px solid #e0e0e0; 
            border-radius: 10px; 
            padding: 20px; 
            margin: 20px 0; 
            background-color: #f8f9fa;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        ">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Kunde:** {selected_customer_data['Kunde_ID_Name']}")
            st.markdown(f"**Aktueller Vertreter:** {selected_customer_data['Vertreter_Name']}")
            st.markdown(f"**Umsatz 2024:** {int(selected_customer_data['Umsatz_2024']):,} €")
            st.markdown(f"**Verlag:** {selected_customer_data['Verlag']}")
        
        with col2:
            st.markdown("**Neuen Vertreter zuweisen:**")
            neuer_vertreter = st.selectbox(
                "Vertreter auswählen:",
                options=sorted(df['Vertreter_Name'].unique()),
                index=sorted(df['Vertreter_Name'].unique()).index(selected_customer_data['Vertreter_Name']),
                key="neuer_vertreter_select"
            )
        
        # Zuweisungs-Buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("✅ Zuweisung bestätigen", key="confirm_assignment"):
                if neuer_vertreter != selected_customer_data['Vertreter_Name']:
                    # Aktuelle Zuweisung für Undo speichern
                    st.session_state.zuweisung_history.append({
                        'kunden_id': st.session_state.selected_customer_id,
                        'alter_vertreter': selected_customer_data['Vertreter_Name'],
                        'neuer_vertreter': neuer_vertreter,
                        'timestamp': pd.Timestamp.now()
                    })
                    
                    # Update des DataFrames
                    st.session_state.df_aktuell.loc[
                        st.session_state.df_aktuell['Kunden_Nr'] == st.session_state.selected_customer_id,
                        'Vertreter_Name'
                    ] = neuer_vertreter
                    
                    st.toast(f"✅ Kunde erfolgreich zu {neuer_vertreter} verschoben!")
                    st.session_state.selected_customer_id = None
                    st.rerun()
                else:
                    st.error("Die Zuweisung konnte nicht durchgeführt werden.")
        
        with col2:
            if st.button("❌ Abbrechen", key="cancel_assignment"):
                st.session_state.selected_customer_id = None
                st.rerun()
        
        with col3:
            if st.button("🔄 Anderen Kunden wählen", key="select_other"):
                st.session_state.selected_customer_id = None
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    except (IndexError, KeyError):
        st.error("❌ Der ausgewählte Kunde konnte nicht gefunden werden.")
        st.session_state.selected_customer_id = None

# Karte
st.subheader("Gebietskarte")
vertreter_liste = sorted(df['Vertreter_Name'].unique())
palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}

karte_obj = zeichne_karte(df_filtered_display, farb_map, st.session_state.selected_customer_id)

# Karten-Interaktion
map_data = st_folium(karte_obj, width='100%', height=700, returned_objects=['last_object_clicked_popup'])

# Kundenauswahl über Suchfeld
if len(df_filtered_display) > 0:
    search_term = st.text_input(
        "🔍 Kunde suchen (ID oder Name):",
        placeholder="z.B. 100000 oder Berlin",
        key="kunde_search"
    )
    
    if search_term:
        filtered_customers = df_filtered_display[
            (df_filtered_display['Kunden_Nr'].astype(str).str.contains(search_term, na=False)) |
            (df_filtered_display['Kunde_ID_Name'].str.contains(search_term, case=False, na=False))
        ]
    else:
        filtered_customers = df_filtered_display.head(10)
    
    filtered_customers = filtered_customers.drop_duplicates(subset=['Kunden_Nr']).reset_index(drop=True)
    
    if len(filtered_customers) > 0:
        cols = st.columns(min(5, len(filtered_customers)))
        for idx, (_, kunde) in enumerate(filtered_customers.iterrows()):
            col_idx = idx % 5
            with cols[col_idx]:
                if st.button(
                    f"Kunde {kunde['Kunden_Nr']}",
                    key=f"kunde_btn_{kunde['Kunden_Nr']}_{idx}_{col_idx}",
                    help=f"{kunde['Kunde_ID_Name'][:40]}..."
                ):
                    st.session_state.selected_customer_id = kunde['Kunden_Nr']
                    st.toast(f"✅ Kunde {kunde['Kunden_Nr']} ausgewählt!")
                    st.rerun()
    else:
        st.info("Keine Kunden gefunden.")
else:
    st.info("Keine Kunden zum Anzeigen verfügbar.")

# Karten-Klick-Interaktion
if map_data and map_data.get("last_object_clicked_popup"):
    popup_text = map_data["last_object_clicked_popup"]
    
    try:
        if "ID:" in popup_text:
            lines = popup_text.replace("<br>", "\n").split("\n")
            for line in lines:
                if "ID:" in line:
                    id_text = line.replace("ID:", "").strip()
                    clicked_id = int(id_text)
                    if st.session_state.selected_customer_id != clicked_id:
                        st.session_state.selected_customer_id = clicked_id
                        st.toast(f"✅ Kunde {clicked_id} ausgewählt!")
                        st.rerun()
                    break
    except (ValueError, IndexError, AttributeError):
        pass

# Footer
st.markdown("---")
st.info("🧪 **Lokale Testversion** - Verwendet Mock-Daten für Entwicklung") 