import xml.etree.ElementTree as ET
import json
import sqlite3
import re
from pyproj import Transformer
from tqdm import tqdm


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

    def gebaeude(self):
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
    streets.gemeinde()
    streets.strasse()
    streets.gebaeude()
    streets.close()
