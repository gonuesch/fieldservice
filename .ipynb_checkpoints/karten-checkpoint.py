# karten.py

import streamlit as st
import folium
from streamlit_folium import st_folium
from scipy.spatial import ConvexHull
import pandas as pd

def zeichne_karte(dataframe, farb_map):
    """
    Erstellt und zeigt eine interaktive Folium-Karte basierend auf den
    übergebenen Daten und der Farbzuordnung an.
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
                    color=farb_map.get(vertreter_name, 'gray'), # Nutzt die Farbe aus der Map
                    fill=True,
                    fill_color=farb_map.get(vertreter_name, 'gray'),
                    fill_opacity=0.2,
                    popup=vertreter_name
                ).add_to(karte)
            except Exception:
                # Fehler ignorieren, wenn Hülle nicht erstellt werden kann
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
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=4,
            popup=f"<b>{row['Kunde_ID_Name']}</b><br>Vertreter: {row['Vertreter_Name']}",
            color=farb_map.get(row['Vertreter_Name']), # Nutzt die Farbe aus der Map
            fill=True,
            fill_opacity=0.8
        ).add_to(karte)

    # Die fertige Karte in der Streamlit-App anzeigen
    st_folium(karte, width='100%', height=600, returned_objects=[])