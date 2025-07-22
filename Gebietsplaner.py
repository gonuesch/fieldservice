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

# CSS für modales Fenster
st.markdown("""
<style>
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0,0,0,0.5);
}

.modal-content {
    background-color: white;
    margin: 5% auto;
    padding: 20px;
    border-radius: 10px;
    width: 80%;
    max-width: 600px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}

.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
}

.close:hover {
    color: black;
}

.customer-details {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.assignment-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# --- 3. HELFER-FUNKTIONEN & INITIALISIERUNG ---

def initialisiere_app_zustand():
    """
    Initialisiert den Session State beim ersten Laden der App.
    Dies stellt sicher, dass die Daten geladen und Zustände für die Interaktion gesetzt werden.
    """
    if 'app_initialisiert' not in st.session_state:
        try:
            st.session_state.df_basis = lade_basis_daten()
            # Prüfe ob Daten erfolgreich geladen wurden
            if st.session_state.df_basis is None or st.session_state.df_basis.empty:
                st.error("❌ Keine Daten geladen. Bitte überprüfen Sie die Google Sheets API-Verbindung.")
                st.session_state.app_initialisiert = False
                return
            
            # df_aktuell hält den Zustand der Gebietsverteilung, die angezeigt und bearbeitet wird.
            st.session_state.df_aktuell = st.session_state.df_basis.copy()
            st.session_state.app_initialisiert = True
            # Hält die ID des angeklickten Kunden. Startet mit None (keine Auswahl).
            st.session_state.selected_customer_id = None
            # Speichert die Auswahl im Multi-Select-Filter, um sie über Reruns hinweg zu erhalten.
            # Initialisiere mit leeren Array, wird später basierend auf Filter gesetzt
            st.session_state.selected_vertreter = []
            # Für Undo-Funktionalität
            st.session_state.zuweisung_history = []
            
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Basisdaten: {str(e)}")
            st.info("💡 Mögliche Lösungen:")
            st.info("• Überprüfen Sie die Google Sheets API-Verbindung")
            st.info("• Stellen Sie sicher, dass die Berechtigungen korrekt sind")
            st.info("• Versuchen Sie es in einigen Minuten erneut")
            st.session_state.app_initialisiert = False
            return



def kunde_zuweisen(kunden_id, neuer_vertreter):
    """
    Weist einen Kunden einem neuen Vertreter zu und speichert die Änderung für Undo.
    """
    try:
        # Aktuelle Zuweisung für Undo speichern
        alter_vertreter = st.session_state.df_aktuell[
            st.session_state.df_aktuell['Kunden_Nr'] == kunden_id
        ]['Vertreter_Name'].iloc[0]
        
        # Änderung in History speichern
        st.session_state.zuweisung_history.append({
            'kunden_id': kunden_id,
            'alter_vertreter': alter_vertreter,
            'neuer_vertreter': neuer_vertreter,
            'timestamp': pd.Timestamp.now()
        })
        
        # Nur die letzten 10 Änderungen behalten
        if len(st.session_state.zuweisung_history) > 10:
            st.session_state.zuweisung_history = st.session_state.zuweisung_history[-10:]
        
        # Update des DataFrames im Session State
        st.session_state.df_aktuell.loc[
            st.session_state.df_aktuell['Kunden_Nr'] == kunden_id,
            'Vertreter_Name'
        ] = neuer_vertreter
        
        return True
    except Exception as e:
        st.error(f"Fehler bei der Zuweisung: {e}")
        return False

def undo_letzte_zuweisung():
    """
    Macht die letzte Kunden-Zuweisung rückgängig.
    """
    if st.session_state.zuweisung_history:
        letzte_aenderung = st.session_state.zuweisung_history.pop()
        
        st.session_state.df_aktuell.loc[
            st.session_state.df_aktuell['Kunden_Nr'] == letzte_aenderung['kunden_id'],
            'Vertreter_Name'
        ] = letzte_aenderung['alter_vertreter']
        
        return True
    return False


# --- 4. LOGIN-LOGIK UND APP-STEUERUNG (PLATZHALTER) ---
# Hier wäre Ihre st.login() Logik integriert.
# Für die Entwicklung ist der Nutzer standardmäßig eingeloggt.
if 'user_is_logged_in' not in st.session_state:
    st.session_state.user_is_logged_in = True 

if st.session_state.user_is_logged_in:
    # --- HAUPTANWENDUNG NACH LOGIN ---
    initialisiere_app_zustand()
    
    # Prüfe ob die App erfolgreich initialisiert wurde
    if not st.session_state.get('app_initialisiert', False):
        st.title("🗺️ Interaktive Gebietsplanung")
        st.error("❌ Die Anwendung konnte nicht initialisiert werden.")
        st.info("🔧 Bitte versuchen Sie es in einigen Minuten erneut oder kontaktieren Sie den Administrator.")
        
        # Reload-Button
        if st.button("🔄 Seite neu laden"):
            # Reset session state für neuen Versuch
            if 'app_initialisiert' in st.session_state:
                del st.session_state.app_initialisiert
            st.rerun()
        
        st.stop()  # Stoppe die Ausführung hier
    
    st.title("🗺️ Interaktive Gebietsplanung")

    # Der angezeigte DataFrame ist immer der, der im Session State gespeichert ist
    df = st.session_state.df_aktuell
    
    # --- SEITENLEISTE (Sidebar) ---
    with st.sidebar:
        st.header("🗺️ Manuelle Zuweisung per Klick")
        
        # Undo-Funktion
        if st.session_state.zuweisung_history:
            col1, col2 = st.columns([1, 1])
            if col1.button("↶ Rückgängig", help="Macht die letzte Zuweisung rückgängig"):
                if undo_letzte_zuweisung():
                    st.toast("Letzte Zuweisung rückgängig gemacht!")
                    st.rerun()
                else:
                    st.warning("Keine Änderung zum Rückgängigmachen verfügbar.")
            
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
        st.session_state.selected_vertreter = verfuegbare_vertreter.copy()
        st.rerun()
    if col2.button("Auswahl aufheben"):
        st.session_state.selected_vertreter = []
        st.rerun()

    # Stelle sicher, dass nur verfügbare Vertreter als Default gesetzt werden
    current_selected = st.session_state.get('selected_vertreter', [])
    valid_default = [v for v in current_selected if v in verfuegbare_vertreter]
    
    # Beim ersten Laden alle Vertreter auswählen, wenn keine Filter gesetzt sind
    if not valid_default and selected_verlag == 'Alle Verlage':
        valid_default = verfuegbare_vertreter
    
    selected_vertreter = st.sidebar.multiselect(
        'Angezeigte Vertreter:', 
        options=verfuegbare_vertreter, 
        default=valid_default
    )
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
    
    # --- KUNDEN-ZUWEISUNG FENSTER (über der Karte) ---
    if st.session_state.selected_customer_id:
        # Zeige ausgewählten Kunden an
        st.success(f"🎯 **Kunde ausgewählt:** ID {st.session_state.selected_customer_id}")
        
        try:
            # Finde die Daten des ausgewählten Kunden
            selected_customer_data = df[df['Kunden_Nr'] == st.session_state.selected_customer_id].iloc[0]
            

            
            # Schönes Fenster mit Container und Border
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
            
            # Header mit Schließen-Button
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown("### 🎯 Kunden-Zuweisung")
            with col2:
                if st.button("❌ Schließen", key="close_modal"):
                    st.session_state.selected_customer_id = None
                    st.rerun()  # Nur hier für UI-Update
            
            st.markdown("---")
            
            # Kunden-Details in zwei Spalten
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**👤 Kunde:** {selected_customer_data['Kunde_ID_Name']}")
                st.markdown(f"**🏢 Verlag:** {selected_customer_data['Verlag']}")
                st.markdown(f"**💰 Umsatz 2024:** {int(selected_customer_data['Umsatz_2024']):,} €")
            
            with col2:
                st.markdown(f"**👨‍💼 Aktueller Vertreter:** {selected_customer_data['Vertreter_Name']}")
                st.markdown(f"**📍 Koordinaten:** {selected_customer_data['Latitude']:.4f}, {selected_customer_data['Longitude']:.4f}")
            
            st.markdown("---")
            
            # Vertreter-Auswahl
            st.markdown("**🔄 Neuen Vertreter auswählen:**")
            alle_vertreter = sorted(df['Vertreter_Name'].unique().tolist())
            aktueller_index = alle_vertreter.index(selected_customer_data['Vertreter_Name'])
            
            neuer_vertreter = st.selectbox(
                "Vertreter:",
                options=alle_vertreter,
                index=aktueller_index,
                key="neuer_vertreter_select",
                label_visibility="collapsed"
            )
            
            # Zeige Unterschiede an
            if neuer_vertreter != selected_customer_data['Vertreter_Name']:
                st.warning(f"⚠️ **Änderung:** Kunde wird von **{selected_customer_data['Vertreter_Name']}** zu **{neuer_vertreter}** verschoben")
                
                # Bestätigungs-Buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("✅ Bestätigen", type="primary", key="confirm_assignment"):
                        if kunde_zuweisen(st.session_state.selected_customer_id, neuer_vertreter):
                            st.toast(f"✅ Kunde erfolgreich zu {neuer_vertreter} verschoben!")
                            st.session_state.selected_customer_id = None
                            st.rerun()  # Nur hier für Karten-Update nach Zuweisung
                        else:
                            st.error("Die Zuweisung konnte nicht durchgeführt werden.")
                with col2:
                    if st.button("❌ Abbrechen", key="cancel_assignment"):
                        st.session_state.selected_customer_id = None
                        st.rerun()  # Nur hier für UI-Update
                    
                with col3:
                    if st.button("🔄 Anderen Kunden wählen", key="select_other"):
                        st.session_state.selected_customer_id = None
                        st.rerun()  # Nur hier für UI-Update
            else:
                st.info("ℹ️ Wählen Sie einen anderen Vertreter aus, um die Zuweisung zu ändern.")
            
            st.markdown("</div>", unsafe_allow_html=True)
                
        except (IndexError, KeyError):
            st.error("❌ Der ausgewählte Kunde konnte nicht gefunden werden.")
            if st.button("Seite neu laden"):
                st.rerun()
            st.session_state.selected_customer_id = None
    
    st.subheader("Gebietskarte")
    

    
    # OPTIMIERT: Karte neu rendern wenn sich Daten oder Kundenauswahl geändert haben
    current_data_hash = hash(str(df_filtered_display[['Kunden_Nr', 'Vertreter_Name']].values.tobytes()))
    current_selection_hash = hash(str(st.session_state.selected_customer_id))
    combined_hash = hash(str(current_data_hash) + str(current_selection_hash))
    
    # Neu rendern wenn sich Daten oder Kundenauswahl geändert haben
    if ('last_karte_data_hash' not in st.session_state or 
        st.session_state.last_karte_data_hash != combined_hash):
        
        vertreter_liste = sorted(df['Vertreter_Name'].unique())
        palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
        farb_map = {name: palette[i % len(palette)] for i, name in enumerate(vertreter_liste)}
        
        karte_obj = zeichne_karte(df_filtered_display, farb_map, st.session_state.selected_customer_id)
        
        # Speichere aktuelle Daten für nächsten Vergleich
        st.session_state.last_karte_data_hash = combined_hash
        st.session_state.cached_karte = karte_obj
    else:
        # Verwende gecachte Karte
        karte_obj = st.session_state.cached_karte

    # Karten-Interaktion für Kundenauswahl
    map_data = st_folium(
        karte_obj, 
        width='100%', 
        height=700, 
        returned_objects=['last_object_clicked_popup'],
        key=f"map_{st.session_state.selected_customer_id}"  # Unique key für bessere Interaktion
    )

    # OPTIMIERT: Kundenauswahl über Suchfeld und Dropdown
    if len(df_filtered_display) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Suchfeld für Kunden
            search_term = st.text_input(
                "🔍 Kunde suchen (ID oder Name):",
                placeholder="z.B. 1037090 oder Scheller",
                key="kunde_search"
            )
        
        with col2:
            # Direkte Dropdown-Auswahl als Alternative
            kunden_options = [f"{row['Kunden_Nr']} - {row['Kunde_ID_Name'][:30]}..." 
                             for _, row in df_filtered_display.head(20).iterrows()]
            kunden_options.insert(0, "Kunde aus Dropdown auswählen...")
            
            selected_kunde_option = st.selectbox(
                "📋 Oder direkt auswählen:",
                options=kunden_options,
                key="kunde_dropdown"
            )
            
            if selected_kunde_option != "Kunde aus Dropdown auswählen...":
                try:
                    selected_id = int(selected_kunde_option.split(" - ")[0])
                    if st.session_state.selected_customer_id != selected_id:
                        st.session_state.selected_customer_id = selected_id
                        st.toast(f"✅ Kunde {selected_id} ausgewählt!")
                        st.rerun()
                except:
                    pass
        
        # Filtere Kunden basierend auf Suchbegriff
        if search_term:
            filtered_customers = df_filtered_display[
                (df_filtered_display['Kunden_Nr'].astype(str).str.contains(search_term, na=False)) |
                (df_filtered_display['Kunde_ID_Name'].str.contains(search_term, case=False, na=False))
            ]
        else:
            filtered_customers = df_filtered_display.head(10)  # Zeige die ersten 10 Kunden
        
        # Entferne Duplikate basierend auf Kunden_Nr
        filtered_customers = filtered_customers.drop_duplicates(subset=['Kunden_Nr']).reset_index(drop=True)
        
        # Zeige gefilterte Kunden als Buttons
        if len(filtered_customers) > 0:
            st.markdown("**🔍 Gefundene Kunden:**")
            cols = st.columns(min(5, len(filtered_customers)))
            for idx, (_, kunde) in enumerate(filtered_customers.iterrows()):
                col_idx = idx % 5
                with cols[col_idx]:
                    if st.button(
                        f"{kunde['Kunden_Nr']} - {kunde['Kunde_ID_Name'][:25]}",
                        key=f"kunde_btn_{kunde['Kunden_Nr']}_{idx}_{col_idx}",
                        help=f"{kunde['Kunde_ID_Name']}"
                    ):
                        st.session_state.selected_customer_id = kunde['Kunden_Nr']
                        st.toast(f"✅ Kunde {kunde['Kunden_Nr']} ausgewählt!")
                        st.rerun()  # Wichtig: Rerun für sofortige Anzeige des Dialogs
        else:
            st.info("Keine Kunden gefunden.")
    else:
        st.info("Keine Kunden zum Anzeigen verfügbar.")
    
    # OPTIMIERT: Karten-Klick-Interaktion
    if map_data and map_data.get("last_object_clicked_popup"):
        popup_text = map_data["last_object_clicked_popup"]
        
        # Extrahiere Kunden-ID aus dem Popup-Text
        try:
            if "ID:" in popup_text:
                # Behandle sowohl <br> als auch \n Zeilenumbrüche
                lines = popup_text.replace("<br>", "\n").split("\n")
                for line in lines:
                    if "ID:" in line:
                        id_text = line.replace("ID:", "").strip()
                        clicked_id = int(id_text)
                        if st.session_state.selected_customer_id != clicked_id:
                            st.session_state.selected_customer_id = clicked_id
                            st.toast(f"✅ Kunde {clicked_id} ausgewählt!")
                            st.rerun()  # Wichtig: Rerun für sofortige Anzeige des Dialogs
                        break
        except (ValueError, IndexError, AttributeError):
            pass
    


else:
    st.error("Bitte einloggen, um die Anwendung zu nutzen.")