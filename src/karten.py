# karten.py

import streamlit as st
import folium
from scipy.spatial import ConvexHull
import pandas as pd

def zeichne_karte(dataframe, farb_map, selected_customer_id=None):
    """
    Erstellt ein interaktives Folium-Kartenobjekt, ohne es anzuzeigen.
    Gibt das Kartenobjekt zur weiteren Verwendung zurück.
    
    Args:
        dataframe: DataFrame mit Kundendaten
        farb_map: Dictionary mit Vertreter-Farben
        selected_customer_id: ID des aktuell ausgewählten Kunden (optional)
    """
    # Karte initialisieren
    karte = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="cartodbpositron")

    # Für jeden ausgewählten Vertreter die Gebietsfläche und die Punkte zeichnen
    for vertreter_name in dataframe['Vertreter_Name'].unique():
        vertreter_daten = dataframe[dataframe['Vertreter_Name'] == vertreter_name]
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
                    popup=f"<b>Gebiet: {vertreter_name}</b><br>Kunden: {len(vertreter_daten)}"
                ).add_to(karte)
            except Exception:
                pass
            
        # Wohnort als Stern-Marker
        wohnort_lat = vertreter_daten['Wohnort_Lat'].iloc[0]
        wohnort_lon = vertreter_daten['Wohnort_Lon'].iloc[0]
        if pd.notna(wohnort_lat):
            folium.Marker(
                [wohnort_lat, wohnort_lon],
                popup=f"<b>🏠 Zentrum: {vertreter_name}</b><br>Kunden: {len(vertreter_daten)}",
                icon=folium.Icon(color='black', icon_color='white', icon='star', prefix='fa')
            ).add_to(karte)

    # Kundenpunkte hinzufügen
    for _, row in dataframe.iterrows():
        is_selected = row['Kunden_Nr'] == selected_customer_id
        
        # Vereinfachte Popup-Informationen für bessere Klick-Erkennung
        popup_html = f"ID:{row['Kunden_Nr']}<br><b>{row['Kunde_ID_Name']}</b><br>Vertreter: {row['Vertreter_Name']}<br>Umsatz: {int(row['Umsatz_2024']):,} €<br><small>👆 Klicken zum Auswählen</small>"
        
        # Bestimme Größe und Farbe basierend auf Auswahl
        if is_selected:
            radius = 15  # Größer für ausgewählte Kunden
            color = 'red'
            weight = 4
            fill_opacity = 1.0
        else:
            radius = 10  # Größer für bessere Klickbarkeit
            color = farb_map.get(row['Vertreter_Name'], 'gray')
            weight = 2
            fill_opacity = 0.8
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            popup=popup_html,
            color=color,
            weight=weight,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            tooltip=f"Kunde {row['Kunden_Nr']}: {row['Kunde_ID_Name']}",
            # Füge data-Attribut für einfachere Extraktion hinzu
            popup_props={'data-customer-id': str(row['Kunden_Nr'])}
        ).add_to(karte)
        
    return karte