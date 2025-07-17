# karten.py

import streamlit as st
import folium
from scipy.spatial import ConvexHull
import pandas as pd

def zeichne_karte(dataframe, farb_map):
    """
    Erstellt ein interaktives Folium-Kartenobjekt, ohne es anzuzeigen.
    Gibt das Kartenobjekt zur weiteren Verwendung zurück.
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
                    popup=vertreter_name
                ).add_to(karte)
            except Exception:
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
    for _, row in dataframe.iterrows():
        # WICHTIG: Wir fügen eine ID zum Popup hinzu, um den Kunden zu identifizieren
        popup_html = f"ID:{row['Kunden_Nr']}<br><b>{row['Kunde_ID_Name']}</b><br>Vertreter: {row['Vertreter_Name']}"
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=5, # Etwas größer für leichtere Klickbarkeit
            popup=popup_html,
            color=farb_map.get(row['Vertreter_Name']),
            fill=True,
            fill_opacity=0.9
        ).add_to(karte)
        
    return karte