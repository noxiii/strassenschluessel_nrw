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
from owslib.wfs import WebFeatureService
from owslib.ogcapi.features import Features
import os
from shapely.geometry import shape, Point
from shapely.ops import nearest_points

from requests import Request
from urllib.parse import unquote

#pd.set_option('display.max_columns', None)


class streets_of_nrw:
    def __init__(self):
        self.gemeinden = []
        self.strassen = {}
        self.gebaeuden = []

    def close(self):
        self.con.close()

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

    def get_wfs_nrw(self, type, gemeinde=None):
        # URL des WFS-Dienstes
        # https://www.bezreg-koeln.nrw.de/system/files/media/document/file/geobasis_webdienste_anleitung_wfs.pdf

        # https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_Gemeinde
        # https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_LagebezeichnungKatalogeintrag
        # https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_GeoreferenzierteGebaeudeadresse

        typenames = {
            'gemeinden': 'adv:AX_Gemeinde',
            'gebaeude': 'adv:AX_GeoreferenzierteGebaeudeadresse',
            'strassen': 'adv:AX_LagebezeichnungKatalogeintrag',
        }

        wfs_url = 'https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert'

        # Specify the parameters for fetching the data
        # Count: specificies amount of rows to return (e.g. 10000 or 100)
        # startIndex: specifies at which offset to start returning rows
        params = {
            'service': 'WFS',
            'version': "2.0.0",
            'request': 'GetFeature',
            'TYPENAMES': typenames[type],
            'startIndex': 0,
            'count': 10000,
        }
        start_index = 0

        gdf_total = gpd.GeoDataFrame()
        while True:
            params['startIndex'] = start_index
            start_index += params['count']
            print(start_index)
            wfs_request_url = Request(
                'GET', wfs_url, params=params).prepare().url
            print(wfs_request_url)
            gdf_part = gpd.read_file(unquote(wfs_request_url))
            gdf_total = gpd.GeoDataFrame(
                pd.concat([gdf_total, gdf_part], ignore_index=True), crs=gdf_part.crs)
            gdf_count = len(gdf_part)
            print(f'collect {gdf_count} lines')
            print(gdf_total)
            #gdf_count = 1
            if gdf_count < params['count']:
                print("last round")
                break

        return gdf_total

    def get_nrw_api(self, collection_name):
        url = 'https://ogc-api.nrw.de/lika/v1/'
        w = Features(url)
        collections = w.collections()
        # for collect in collections:
        #    print(collect)
        collection = w.collection(collection_name)
        id = collection['id']


 
    def gebref(self):
        dtype_mapping = {13: str, 15: str}
        print('Load gebref file')
        df = pd.read_csv('gebref/gebref.txt', delimiter=';',
                         header=None, dtype=dtype_mapping)

        column_names = [
            'nba',  #
            'oid',  # ?
            'qua',  # Qualität
            'land',  # Landesschlüssel
            'land_name',  # Land
            'regierungsbezirk',  # Regierungsbezirksschlüssel
            'regbez_name',  # Regierungsbezirk
            'kreis',  # Kreisschlüssel
            'kreis_name',  # Kreis
            'gemeinde',  # Gemeindeschlüssel
            'addr:city',  # Gemeinde (entsprechend OSM addr:city)
            'ottschl',  # Ortschlüssel
            'ott',  # Ort
            'lage',  # Straßenschlüssel
            'addr:street',  # Straße (entsprechend OSM addr:street)
            'hausnummer',  # Hausnummer (entsprechend OSM addr:housenumber)
            'zusatz',  # Adresszusatz (entsprechend OSM addr:unit)
            'zone',  # Zone
            'UTM_East',  # UTM-Ost
            'UTM_North',  # UTM-Nord
            'JJJJ-MM-TT'  # Datum
        ]

        # Weise die manuell festgelegten Spaltennamen zu
        print('name column')
        df.columns = column_names

        # UTM-Konvertierung in Längen- und Breitengrad direkt im DataFrame
        print('transform coordinate system')
        utm_proj = Proj(init='epsg:32632')  # Beispiel für UTM-Zone 32
        latlon_proj = Proj(init='epsg:4326')  # WGS84 Längen- und Breitengrad

        transformer = Transformer.from_proj(utm_proj, latlon_proj)

        # Wende die Transformation auf alle Zeilen im DataFrame an
        lon, lat = transformer.transform(
            df['UTM_East'].to_list(), df['UTM_North'].to_list())
        df['lon'], df['lat'] = lon, lat

        # Erstelle eine GeoDataFrame
        geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
        # 'EPSG:4326' ist der Code für WGS84
        gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

        # Gruppiere nach Stadt und erstelle separate GeoJSON-Dateien

        print('fix streetnames')

        gdf['addr:housenumber'] = gdf['hausnummer'] + \
            gdf['zusatz'].fillna('').astype(str)
        gdf['addr:street'] = gdf['addr:street'].str.replace(
            r'Str.', 'Straße', case=False)
        gdf['addr:street'] = gdf['addr:street'].str.replace(
            r'Pl.', 'Platz', case=False)

        def create_schluessel(row):
            land = str(row['land']).zfill(2)
            rgbz = str(int(row['regierungsbezirk'])).zfill(1)
            kreis = str(row['kreis']).zfill(2)
            gmd_verband = "0000"
            gemeinde = str(row['gemeinde']).zfill(3)
            lage = str(row['lage']).zfill(5)
            return f"{land}{rgbz}{kreis}{gmd_verband}{gemeinde}{lage}"
        # Neues Feld "schlüssel" erstellen
        gdf['strassenschluessel'] = gdf.apply(create_schluessel, axis=1)

        return gdf
            
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

    def get_overpass_housenumbers(self, gemeinde_schluessel):
        api = overpass.API()
        query = f"""
        area["boundary"="administrative"]
	        ["de:amtlicher_gemeindeschluessel"="{gemeinde_schluessel}"]
            ->.searchArea;
        #area["name"="{stadt}"]->.a;
        (
            nwr(area.a)
                ["addr:housenumber"]
                ["addr:street"];
        );
        """

        print("load overpass data")
        overpass_result = api.get(query, verbosity='geom')
        print("overpass to geopandas")
        overpass_gdf = gpd.GeoDataFrame.from_features(overpass_result['features'])
        # Erstelle eine separate Zeile für jede Hausnummer in 'overpass_gdf'
        # separate Komma-separierten
        print("split multi housenumbers commaseparate")
        comma_mask = overpass_gdf['addr:housenumber'].str.contains(',')
        split_overpass_gdf = overpass_gdf[comma_mask].copy()
        split_overpass_gdf['addr:housenumber'] = split_overpass_gdf['addr:housenumber'].str.split(',')
        split_overpass_gdf = split_overpass_gdf.explode('addr:housenumber')
        overpass_gdf = pd.concat([overpass_gdf[~comma_mask], split_overpass_gdf], ignore_index=True)

        print('split multi housenumbers -')
        range_mask = overpass_gdf['addr:housenumber'].str.contains('-')
        range_overpass_gdf = overpass_gdf[range_mask].copy()
        range_overpass_gdf['addr:housenumber'] = range_overpass_gdf['addr:housenumber'].apply(
            lambda x: list(range(int(x.split('-')[0]), int(x.split('-')[1])+1)))
        range_overpass_gdf = range_overpass_gdf.explode('addr:housenumber')
        overpass_gdf = pd.concat(
            [overpass_gdf[~range_mask], range_overpass_gdf], ignore_index=True)    
        print('done')
        return overpass_gdf[['addr:street', 'addr:housenumber', 'geometry']]

    def get_diff_hausnumbers(self, data1, data2):
        # Überprüfen, ob die erforderlichen Spalten vorhanden sind
        if 'addr:street' not in data1.columns or 'addr:housenumber' not in data1.columns:
            raise ValueError("data1 fehlen erforderliche Spalten 'addr:street' oder 'addr:housenumber'")
        if 'addr:street' not in data2.columns or 'addr:housenumber' not in data2.columns:
            raise ValueError("data2 fehlen erforderliche Spalten 'addr:street' oder 'addr:housenumber'")

        data1['geometry'] = data1.geometry.centroid
        data2['geometry'] = data2.geometry.centroid

        gdf1 = gpd.GeoDataFrame(data1)
        gdf2 = gpd.GeoDataFrame(data2)

        # Merge der GeoDataFrames basierend auf 'addr:street' und 'addr:housenumber'
        merged = pd.merge(gdf1, gdf2, on=['addr:street', 'addr:housenumber'], how='outer', suffixes=('_gdf1', '_gdf2'), indicator=True)
        merged['geometry'] = merged['geometry_gdf1'].combine_first(merged['geometry_gdf2'])

        # Filtern nach Zeilen, die nur in einem der beiden DataFrames vorhanden sind
        only_in_gdf1 = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])
        only_in_gdf2 = merged[merged['_merge'] == 'right_only'].drop(columns=['_merge'])
        only_in_gdf1['comment'] = 'only in alkis'
        only_in_gdf2['comment'] = 'only in osm'

        # Ergebnis-GeoDataFrames
        result = gpd.GeoDataFrame(pd.concat([only_in_gdf1, only_in_gdf2], ignore_index=True))

        print(result)
        return result



if __name__ == '__main__':
    streets = streets_of_nrw()

    # prepair data

    # Download from alkis nrw
    # add 'gebaeude_bauwerk' if it is possible to download city based

    keys = ['gemeinden', 'strassen']
    file_paths = {}
    for key in keys:
        print(f'start import {key}')
        file_paths[key] = f'download/alkis/{key}.xml'
        if not os.path.exists(file_paths[key]):
            gdf_streets = streets.get_wfs_nrw(key, gemeinde='Ratingen')
            filter_list = {
                'gemeinden': ['identifier', 'beginnt', 'schluesselGesamt',
                              'bezeichnung', 'land', 'regierungsbezirk',
                              'kreis', 'gemeinde', 'geometry'],
                'strassen': ['identifier', 'beginnt', 'schluesselGesamt',
                             'bezeichnung', 'land', 'regierungsbezirk',
                             'kreis', 'gemeinde', 'lage', 'geometry'],
            }
            filter = filter_list.get(key, [])
            if filter:
                gdf_streets = gpd.GeoDataFrame(gdf_streets[filter])
            gdf_streets.to_file(file_paths[key])
        else:
            print(f'use existing file: {file_paths[key]}')

    # Better load Data City based this take alot of time and create high memory usage
    print('Load data')
    gpd_gemeinden = gpd.read_file(file_paths['gemeinden']).query("land == 5")
    gpd_strassen = gpd.read_file(file_paths['strassen'])
    gpd_gebaeude = streets.gebref()

    gemeinde_list = sorted(gpd_gemeinden['bezeichnung'].tolist())
    for gemeinde in gemeinde_list:
        print(f'progress {gemeinde}')
        gpd_gemeinde = gpd_gemeinden[gpd_gemeinden.bezeichnung == gemeinde]
        for index, gmd_row in gpd_gemeinde.iterrows():
            gpd_strasse = gpd_strassen[
                (gpd_strassen.land == gmd_row['land'])
                & (gpd_strassen.regierungsbezirk == gmd_row['regierungsbezirk'])
                & (gpd_strassen.kreis == gmd_row['kreis'])
                & (gpd_strassen.gemeinde == gmd_row['gemeinde'])
            ].copy()

            def create_schluessel(row):
                land = str(row['land']).zfill(2)
                rgbz = str(int(row['regierungsbezirk'])).zfill(1)
                kreis = str(row['kreis']).zfill(2)
                gmd_verband = "0000"
                gemeinde = str(row['gemeinde']).zfill(3)
                lage = str(row['lage']).zfill(5)
                return f"{land}{rgbz}{kreis}{gmd_verband}{gemeinde}{lage}"

            # Neues Feld "schlüssel" erstellen
            gpd_strasse['strassenschluessel'] = gpd_strasse.apply(create_schluessel, axis=1)
            filtered_strasse = gpd_strasse[['strassenschluessel', 'bezeichnung']].sort_values(by='strassenschluessel')
            
            # save as csv 
            gemeinde_clean = streets.cleanup_text(gemeinde)
            csv_file = f'./export/strassenschluessel_csv/{gemeinde_clean}.csv'
            print(f'save file {csv_file}')
            print(filtered_strasse)
            filtered_strasse.to_csv(csv_file, sep=';', index=False)

            # export as json#
            json_file = f'./export/strassenschluessel_json/{gemeinde_clean}.json'
            print(f'save file {json_file}')
            gpd_strasse.sort_values(by='strassenschluessel').to_file(json_file)

            ####################
            # Housenumbers
            gpd_overpass = gpd.GeoDataFrame(streets.get_overpass_housenumbers(gemeinde))
            #print(gpd_overpass[['addr:street', 'addr:housenumber', 'geometry']])

            alkis_gebaeude_gemeinde_gdf = gpd_gebaeude[
                (gpd_gebaeude.land == gmd_row['land'])
                & (gpd_gebaeude.regierungsbezirk == gmd_row['regierungsbezirk'])
                & (gpd_gebaeude.kreis == gmd_row['kreis'])
                & (gpd_gebaeude.gemeinde == gmd_row['gemeinde'])
            ].copy()
            missing_buildings = streets.get_diff_hausnumbers(alkis_gebaeude_gemeinde_gdf, gpd_overpass)
            hausnummer_json_file = f'./export/hausnummern_json/{gemeinde_clean}.json'
            print(f'save file {json_file}')
            print(missing_buildings)
            missing_buildings.sort_values(by='addr:street').to_file(hausnummer_json_file)
            print('done')
            

