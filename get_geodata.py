import xml.etree.ElementTree as ET
import json
import sqlite3
import re
from pyproj import Transformer
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from pyproj import Proj, Transformer
import overpass
import geopy.distance
import shapely.geometry as geom
import geojson


class streets_of_nrw:
    def __init__(self):
        self.gemeinden = []
        self.strassen = {}
        self.gebaeuden = []

    def close(self):
        self.con.close()

    def gemeinde(self):
        print('Start load gemeinde')
        tree = ET.parse('download/gemeinde.xml')
        root = tree.getroot()
        print('progress gemeinden')

        for featureCollection in tqdm(root):

            gemeinde = {}
            gemeinde['gemeindeverband_key'] = '0000'

            for member in featureCollection[0]:
                if member.tag.endswith('bezeichnung'):
                    gemeinde['name'] = member.text
                if member.tag.endswith('gemeindekennzeichen'):
                    for gkz in member[0]:
                        if gkz.tag.endswith('land'):
                            gemeinde['land_key'] = gkz.text
                        if gkz.tag.endswith('regierungsbezirk'):
                            gemeinde['rgbz_key'] = gkz.text
                        if gkz.tag.endswith('kreis'):
                            gemeinde['kreis_key'] = gkz.text
                        if gkz.tag.endswith('gemeinde'):
                            gemeinde['gemeinde_key'] = gkz.text

                    gemeinde['schluessel'] = ''.join([
                        gemeinde['land_key'],
                        gemeinde['rgbz_key'],
                        gemeinde['kreis_key'],
                        gemeinde['gemeindeverband_key'],
                        gemeinde['gemeinde_key'],
                    ])
                    if gemeinde['land_key'] != "05":
                        print(f"{gemeinde['name']} - ")
                        continue
                    self.gemeinden.append(gemeinde)
                    self.strassen[gemeinde['schluessel']] = []

    def strasse(self):
        tree = ET.parse('download/strassen.xml')
        root = tree.getroot()

        print('progress strassen')
        for featureCollection in tqdm(root):
            strasse = {}
            strasse['gemeindeverband_key'] = '0000'

            for member in featureCollection[0]:
                if member.tag.endswith('bezeichnung'):
                    strasse['name'] = member.text
                if member.tag.endswith('schluessel'):
                    try:
                        for schluessel in member[0]:
                            if schluessel.tag.endswith('land'):
                                strasse['land_key'] = schluessel.text
                            if schluessel.tag.endswith('regierungsbezirk'):
                                strasse['rgbz_key'] = schluessel.text
                            if schluessel.tag.endswith('kreis'):
                                strasse['kreis_key'] = schluessel.text
                            if schluessel.tag.endswith('gemeinde'):
                                strasse['gemeinde_key'] = schluessel.text
                            if schluessel.tag.endswith('lage'):
                                strasse['lage_key'] = schluessel.text
                        strasse['schluessel_gemeinde'] = ''.join([
                            strasse['land_key'],
                            strasse['rgbz_key'],
                            strasse['kreis_key'],
                            strasse['gemeindeverband_key'],  # Gemeindeverband
                            strasse['gemeinde_key'],
                        ])
                        strasse['schluessel'] = ''.join([
                            strasse['land_key'],
                            strasse['rgbz_key'],
                            strasse['kreis_key'],
                            strasse['gemeindeverband_key'],  # Gemeindeverband
                            strasse['gemeinde_key'],
                            strasse['lage_key'],
                        ])
                        
                        if strasse['land_key'] != "05":
                            print(f"{strasse['name']} - {strasse['land_key']}")
                            continue

                        if not re.match("^[0-9]+$", strasse['lage_key']):
                            print("keine zahl")
                            continue

                        if strasse['schluessel_gemeinde'] not in self.strassen:
                            self.strassen[strasse['schluessel_gemeinde']] = []

                        line = f"{strasse['schluessel']};{strasse['name']}"
                        self.strassen[strasse['schluessel_gemeinde']].append(line)

                    except Exception as e:
                        print("Error: Insert: ", e)
                        for data in member[0]:
                            print(data.tag, ': ', data.text)

    def speicher_strassen(self):
        print("Speicher Straßen")
        for gemeinde in self.gemeinden:

            name = self.cleanup_text(gemeinde['name'])
            gemeinde_schluessel = gemeinde['schluessel']
            strassen = sorted(set(self.strassen[gemeinde_schluessel]))
            print(f"Speicher {name} mit {len(strassen)} Straßen")
            with open(f"strassenschluessel/{name}.csv", "w") as file:
                for string in strassen:
                    file.write(f"{string}\n")

    def cleanup_text(self, text):
        # Leerzeichen durch Unterstriche ersetzen
        text = re.sub(r'\s', '_', text)

        # Klammern, Punkt, Schrägstrich und Backslash entfernen
        text = re.sub(r'[\(\).\/\\]', '', text)

        # Umlaute ersetzen
        text = re.sub(r'[Ää]', 'ae', text)
        text = re.sub(r'[Öö]', 'oe', text)
        text = re.sub(r'[Üü]', 'ue', text)

        # ß durch ss ersetzen
        text = re.sub(r'ß', 'ss', text)

        return text
   
#    def convert_coordinates(self, utm_east, utm_north):
#        # Definiere die Projektionen für UTM und Längen- und Breitengrad
#        utm_proj = Proj(init='epsg:25832')  # 'EPSG:25832' ist der UTM-Zonen-Code
#        latlon_proj = Proj(init='epsg:4326')  # 'EPSG:4326' ist der Code für WGS84 Längen- und Breitengrad
#
#        # Führe die Umrechnung durch
#        lon, lat = transform(utm_proj, latlon_proj, utm_east, utm_north)
#        return lon, lat

    def gebref(self):
        dtype_mapping = {13: str, 15: str}
        df = pd.read_csv('gebref/gebref.txt', delimiter=';', header=None, dtype=dtype_mapping)

        column_names = [
            'nba',  #
            'oid',  # ?
            'qua',  # Qualität
            'landschl',  # Landesschlüssel
            'land',  # Land
            'regbezschl',  # Regierungsbezirksschlüssel
            'regbez',  # Regierungsbezirk
            'kreisschl',  # Kreisschlüssel
            'kreis',  # Kreis
            'gmdschl',  # Gemeindeschlüssel
            'addr:city',  # Gemeinde (entsprechend OSM addr:city)
            'ottschl',  # Ortschlüssel
            'ott',  # Ort
            'strschl',  # Straßenschlüssel
            'addr:street',  # Straße (entsprechend OSM addr:street)
            'hausnummer',  # Hausnummer (entsprechend OSM addr:housenumber)
            'zusatz',  # Adresszusatz (entsprechend OSM addr:unit)
            'zone',  # Zone
            'UTM_East',  # UTM-Ost
            'UTM_North',  # UTM-Nord
            'JJJJ-MM-TT'  # Datum
        ]

        # Weise die manuell festgelegten Spaltennamen zu
        df.columns = column_names
        
        # UTM-Konvertierung in Längen- und Breitengrad direkt im DataFrame
        utm_proj = Proj(init=f'epsg:32632')  # Beispiel für UTM-Zone 32
        latlon_proj = Proj(init='epsg:4326')  # WGS84 Längen- und Breitengrad
        
        transformer = Transformer.from_proj(utm_proj, latlon_proj)

        # Wende die Transformation auf alle Zeilen im DataFrame an
        lon, lat = transformer.transform(df['UTM_East'].to_list(), df['UTM_North'].to_list())
        df['lon'], df['lat'] = lon, lat

        # Erstelle eine GeoDataFrame
        geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')  # 'EPSG:4326' ist der Code für WGS84

        # Gruppiere nach Stadt und erstelle separate GeoJSON-Dateien
        for stadt, daten in gdf.groupby('addr:city'):
            print('start: ' + stadt)
            stadt_gdf = gpd.GeoDataFrame(daten)
            #  stadt_gdf["properties"]["source"] = "opengeodata.nrw.de (c) Deutschland Lizens zero"
            stadt_gdf['addr:housenumber'] = stadt_gdf['hausnummer'] + stadt_gdf['zusatz'].fillna('').astype(str)
            stadt_gdf['addr:street'] = stadt_gdf['addr:street'].str.replace(r'Str.', 'Straße', case=False)
            stadt_gdf['addr:street'] = stadt_gdf['addr:street'].str.replace(r'Pl.', 'Platz', case=False)

            stadt_clear = "".join(ch for ch in stadt if ch.isalnum())

            # Speichere als GeoJSON
            stadt_gdf.to_file(f'data/Hausnummern/{stadt_clear}_daten.geojson', driver='GeoJSON')

    def split_housenumbers(self, row):
        housenumbers = []
        # Wenn ',' vorhanden ist, teile nach ',' auf
        if ',' in str(row['addr:housenumber']):
            housenumbers.extend(str(row['addr:housenumber']).split(','))
            print(f"split {row['addr:housenumber']} to {housenumbers}")
        elif '-' in str(row['addr:housenumber']):
            # Wenn '-' vorhanden ist, teile nach '-' auf

            start, end = map(int, str(row['addr:housenumber']).split('-'))
            housenumbers.extend(map(str, range(start, end + 1)))
            print(f"split {row['addr:housenumber']} to {housenumbers}")

        else:
            # Andernfalls bleibt die Hausnummer unverändert
            housenumbers.append(str(row['addr:housenumber']))

        # Erstelle für jede Hausnummer eine eigene Zeile
        rows = []
        for hn in housenumbers:
            new_row = row.copy()
            new_row['addr:housenumber'] = hn
            rows.append(new_row)

        return rows
    
    def check_with_overpass(self, stadt):
        api = overpass.API()
        query = f'area["name"="{stadt}"]->.a; (node(area.a)["addr:housenumber"]; way(area.a)["addr:housenumber"]; relation(area.a)["addr:housenumber"];);'

        print("load overpass data")
        overpass_result = api.get(query, verbosity='geom')
        print("convert overpass data")
        overpass_gdf = gpd.read_file(geojson.dumps(overpass_result), driver='GeoJSON')
        overpass_gdf = overpass_gdf.rename(columns={'geometry': 'geometry_overpass'})
        overpass_gdf['geometry_overpass'] = overpass_gdf['geometry_overpass'].to_crs(epsg=4326).centroid
        # Wende die Funktion auf jede Zeile an und erstelle eine Liste von DataFrames
        print("split multi housenumbers")
        # Kombiniere die DataFrames in einer Liste zu einem einzigen DataFrame


        # Erstelle eine separate Zeile für jede Hausnummer in 'overpass_gdf' mit Komma-separierten Werten
        comma_mask = overpass_gdf['addr:housenumber'].str.contains(',')
        split_overpass_gdf = overpass_gdf[comma_mask].copy()
        split_overpass_gdf['addr:housenumber'] = split_overpass_gdf['addr:housenumber'].str.split(',')
        split_overpass_gdf = split_overpass_gdf.explode('addr:housenumber')
        overpass_gdf = pd.concat([overpass_gdf[~comma_mask], split_overpass_gdf], ignore_index=True)


        # Erstelle eine separate Zeile für jede Hausnummer im "von-bis"-Format
        range_mask = overpass_gdf['addr:housenumber'].str.contains('-')
        range_overpass_gdf = overpass_gdf[range_mask].copy()
        range_overpass_gdf['addr:housenumber'] = range_overpass_gdf['addr:housenumber'].apply(lambda x: list(range(int(x.split('-')[0]), int(x.split('-')[1])+1)))
        range_overpass_gdf = range_overpass_gdf.explode('addr:housenumber')
        overpass_gdf = pd.concat([overpass_gdf[~range_mask], range_overpass_gdf], ignore_index=True)


        # Lade das vorhandene GeoJSON
        print("load alkis data")
        alkis_gdf = gpd.read_file(f'data/Hausnummern/{stadt}_daten.geojson')
        alkis_gdf = alkis_gdf.rename(columns={'geometry': 'geometry_alkis'})




        # Merge die beiden GeoDataFrames
        merged_gdf = pd.merge(alkis_gdf, overpass_gdf, on=['addr:street', 'addr:housenumber'], how='outer', indicator=True)


        # Extrahiere Straßennamen und Hausnummern, sortiere nach addr:street
        missing_data = merged_gdf[merged_gdf['_merge'] == 'left_only'][['addr:street', 'addr:housenumber', 'geometry_alkis', '_merge']]

        missing_data_gdf = pd.merge(missing_data, overpass_gdf[['addr:street', 'addr:housenumber']], on=['addr:street', 'addr:housenumber'], how='left') 
        missing_data_gdf = missing_data_gdf.rename(columns={'geometry_alkis': 'geometry'})

        missing_data_gdf['source'] = ''
        missing_data_gdf.loc[merged_gdf['_merge'] == 'left_only', 'source'] = 'alkis'
        missing_data_gdf.loc[merged_gdf['_merge'] == 'right_only', 'source'] = 'overpass'

        print(f'Merged: {merged_gdf.columns}')
        print(f'Missing Merged: {missing_data_gdf.columns}')


        missing_clount = len(missing_data_gdf)
        print(f"Es wurden {missing_clount} Hausnummern gefunden")
        print("Columns in missing_data_gdf:", missing_data_gdf.columns)



        # Zeige die ersten 20 Einträge für 'overpass_gdf' an
        print("Overpass Data (Sorted):")
        overpass_gdf_sorted = overpass_gdf.sort_values(by='addr:street').head(20)
        print(overpass_gdf_sorted[['addr:street', 'addr:housenumber', 'geometry_overpass']])

        # Zeige die ersten 20 Einträge für 'alkis_gdf' an
        print("\nALKIS Data (Sorted):")
        alkis_gdf_sorted = alkis_gdf.sort_values(by='addr:street').head(20)
        print(alkis_gdf_sorted[['addr:street', 'addr:housenumber', 'geometry_alkis']])

        print("\nMissed Data (Sorted):")
        missing_gdf_sorted = missing_data_gdf.sort_values(by='addr:street').head(20)
        print(missing_gdf_sorted[['addr:street', 'addr:housenumber', 'geometry', 'source']])

        missing_data_gdf.to_file(f'data/Hausnummern_diff/{stadt}.geojson', driver='GeoJSON', na='drop')

        overpass_gdf = overpass_gdf.rename(columns={'geometry_overpass': 'geometry'})
        overpass_gdf_filtered = overpass_gdf[['addr:street', 'addr:housenumber', 'geometry' ]].copy()
        overpass_gdf_filtered.to_file(f'data/Hausnummern_diff/{stadt}_overpass.geojson', driver='GeoJSON', na='drop')

        alkis_gdf = alkis_gdf.rename(columns={'geometry_alkis': 'geometry'})
        alkis_gdf_filtered = alkis_gdf[['addr:street', 'addr:housenumber', 'geometry' ]].copy()
        alkis_gdf_filtered.to_file(f'data/Hausnummern_diff/{stadt}_alkis.geojson', driver='GeoJSON', na='drop')


    def gebaeude(self):
        # Die Gebäude aus alkis sind unvollständig, da der abruf limitiert ist. Für vorschläge bin ich offen :)
        tree = ET.parse('download/gebaeude.xml')
        root = tree.getroot()
        for featureCollection in tqdm(root):
            if featureCollection.tag.endswith('member'):

                gebaeude = {}
                gebaeude['gemeindeverband_key'] = '0000'
                gebaeude['adressierungszusatz_key'] = ''

                try:
                    for member in featureCollection[0]:
                        if member.tag.endswith('land'):
                            gebaeude['land_key'] = member.text
                        if member.tag.endswith('regierungsbezirk'):
                            gebaeude['rgbz_key'] = member.text
                        if member.tag.endswith('kreis'):
                            gebaeude['kreis_key'] = member.text
                        if member.tag.endswith('gemeinde'):
                            gebaeude['gemeinde_key'] = member.text
                        if member.tag.endswith('strassenschluessel'):
                            gebaeude['strassenschluessel_key'] = member.text
                        if member.tag.endswith('hausnummer'):
                            gebaeude['hausnummer_key'] = member.text
                        if member.tag.endswith('adressierungszusatz'):
                            gebaeude['adressierungszusatz_key'] = member.text

                        if member.tag.endswith('position'):
                            for position in member[0]:
                                if position.tag.endswith('pos'):
                                    gebaeude['EPSG:4326'] = position.text
                                    transformer = Transformer.from_crs(
                                        "EPSG:3857", "EPSG:4326")
                                    c1, c2 = position.text.split()

                                    lat, lon = transformer.transform(c1, c2)
                                    gebaeude['lat'] = lat
                                    gebaeude['lon'] = lon

                    gebaeude['schluessel_strasse'] = ''.join([
                        gebaeude['land_key'],
                        gebaeude['rgbz_key'],
                        gebaeude['kreis_key'],
                        gebaeude['gemeindeverband_key'],
                        gebaeude['gemeinde_key'],
                        gebaeude['strassenschluessel_key'],
                    ])
                    gebaeude['schluessel'] = ''.join([
                        gebaeude['land_key'],
                        gebaeude['rgbz_key'],
                        gebaeude['kreis_key'],
                        gebaeude['gemeindeverband_key'],
                        gebaeude['gemeinde_key'],
                        gebaeude['strassenschluessel_key'],
                        gebaeude['hausnummer_key'],
                        gebaeude['adressierungszusatz_key'],
                    ])

                except Exception as e:
                    print("Error: Insert: ", e)
                    for data in member:
                        print(data.tag, ': ', data.text)

                # print(gebaeude)
                # return
    def get_building_json(self):
        pass


if __name__ == '__main__':
    streets = streets_of_nrw()
    # streets.gemeinde()
    # streets.strasse()
    # streets.gebaeude()
    # streets.speicher_strassen()

    # streets.gebref()
    streets.check_with_overpass("Ratingen")
