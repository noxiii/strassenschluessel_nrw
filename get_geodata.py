import xml.etree.ElementTree as ET
import re
from pyproj import Transformer

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Proj, Transformer
import overpass
from owslib.ogcapi.features import Features
import os
from shapely.geometry import Point

from requests import Request
from urllib.parse import unquote

#pd.set_option('display.max_columns', None)


class streets_of_nrw:
    def __init__(self):
        self.gemeinden = []
        self.strassen = {}
        self.gebaeuden = []

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


if __name__ == '__main__':
    streets = streets_of_nrw()

    # prepair data

    # Download from alkis nrw
    # add 'gebaeude_bauwerk' if it is possible to download city based

    keys = ['gemeinden', 'strassen']
    file_paths = {}

    alkis_download_dir = 'download/alkis'
    if not os.path.exists(alkis_download_dir):
        os.makedirs(alkis_download_dir) 
    
    for key in keys:
        print(f'start import {key}')
        file_paths[key] = f'{alkis_download_dir}/{key}.xml'
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

    #gemeinde_list = sorted(gpd_gemeinden['bezeichnung'].tolist())
    #gemeinde_name_list = ['Düsseldorf', 'Köln', 'Mönchengladbach', 'Essen', 'Duisburg', 'Ratingen']
    gemeinde_name_list = ['Ratingen']
    gemeinde_list = gpd_gemeinden[gpd_gemeinden['bezeichnung'].isin(gemeinde_name_list)]
    print(gemeinde_list)

    export_strassenschluessel_csv = './export/strassenschluessel_csv'
    if not os.path.exists(export_strassenschluessel_csv):
        os.makedirs(export_strassenschluessel_csv)

    export_strassenschluessel_json = './export/strassenschluessel_json'
    if not os.path.exists(export_strassenschluessel_json):
        os.makedirs(export_strassenschluessel_json)

    #gpd_gemeinde = gpd_gemeinden[gpd_gemeinden.bezeichnung == gemeinde]
    for index, gmd_row in gemeinde_list.iterrows():
        gemeinde = gmd_row['bezeichnung']
        print(f'progress {gemeinde}')
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
            return str.strip(f"{land}{rgbz}{kreis}{gmd_verband}{gemeinde}{lage}")

        # Neues Feld "schlüssel" erstellen
        gpd_strasse['strassenschluessel'] = gpd_strasse.apply(create_schluessel, axis=1)

        # Füge die ersten Koordinaten den Straßendaten hinzu
        gpd_gebaeude['mittelpunkt'] = gpd_gebaeude.geometry.centroid
        gebaeude_erste_koordinaten = gpd_gebaeude.groupby('strassenschluessel').first()
        gpd_strasse['geometry'] = gpd_strasse['strassenschluessel'].map(gebaeude_erste_koordinaten['mittelpunkt'])

        filtered_strasse = gpd_strasse[['strassenschluessel', 'bezeichnung', 'geometry']].sort_values(by='strassenschluessel')
        print(gpd_gebaeude)
        print(gpd_strasse)
        print(filtered_strasse)
            
        # save as csv 
        gemeinde_clean = streets.cleanup_text(gemeinde)

        csv_file = f'{export_strassenschluessel_csv}/{gemeinde_clean}.csv'
        print(f'save file {csv_file}')
        #print(filtered_strasse)
        filtered_strasse.to_csv(csv_file, sep=';', index=False)

        # export as json
        json_file = f'{export_strassenschluessel_json}/{gemeinde_clean}.json'
        print(f'save file {json_file}')
        gpd_strasse.sort_values(by='strassenschluessel').to_file(json_file)
            
        ####################
        # Housenumbers
        gpd_overpass = gpd.GeoDataFrame(streets.get_overpass_housenumbers(gmd_row['schluesselGesamt']))
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
        missing_buildings[['addr:street', 'addr:housenumber', 'comment', 'geometry']].sort_values(by='addr:street').to_file(hausnummer_json_file)
        print('done')
        

