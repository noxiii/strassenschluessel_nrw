import xml.etree.ElementTree as ET
import json
import sqlite3
from pyproj import Transformer
from tqdm import tqdm



class streets_of_nrw:
    def __init__(self):
        self.gemeinden = []
        self.strassen = []
        self.gebaeuden = []

        self.con = sqlite3.connect("strassenschluessel_nrw.db")
        self.cur = self.con.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS gemeinden(schluessel TEXT PRIMARY KEY, name TEXT)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS strassen(schluessel TEXT PRIMARY KEY, gemeinde_id TEXT, name TEXT, FOREIGN KEY (gemeinde_id) REFERENCES gemeinden(id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS buildings(schluessel TEXT PRIMARY KEY, strasse_id TEXT, hausnummer TEXT, adressierungszusatz TEXT, lat TEXT, lon TEXT, FOREIGN KEY (strasse_id) REFERENCES strassen(id))')


    def close(self):
        self.con.close()

    def gemeinde(self):
        print('Start load gemeinde')
        tree = ET.parse('gemeinde.xml')
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

                    self.cur.execute('SELECT schluessel FROM gemeinden WHERE schluessel = ?', (gemeinde['schluessel'],))
                    schluessel_exist=self.cur.fetchall()
                    if len(schluessel_exist)==0:
                            self.cur.execute(f'INSERT INTO gemeinden VALUES(?, ?)', (gemeinde["schluessel"], gemeinde["name"],))
                            self.con.commit()
                    else:
                        self.cur.execute('UPDATE gemeinden SET name = ? WHERE schluessel = ?', (gemeinde['name'], schluessel_exist[0][0],))
                        self.con.commit()
    def strassennamen_repair(name):
        pass
    def strasse(self):
        tree = ET.parse('strassen.xml')
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
                            strasse['gemeindeverband_key'], # Gemeindeverband
                            strasse['gemeinde_key'],
                            ])
                        strasse['schluessel'] = ''.join([
                            strasse['land_key'],
                            strasse['rgbz_key'],
                            strasse['kreis_key'],
                            strasse['gemeindeverband_key'], # Gemeindeverband
                            strasse['gemeinde_key'],
                            strasse['lage_key'],
                            ])


                        self.cur.execute('SELECT * FROM strassen WHERE schluessel = ?', (strasse['schluessel'],))
                        schluessel_exist=self.cur.fetchall()
                        self.cur.execute('SELECT schluessel FROM gemeinden WHERE schluessel = ?', (strasse['schluessel_gemeinde'],))
                        gemeinde_schluessel=self.cur.fetchall()

                        if len(schluessel_exist)==0:

                            sql_values = (strasse["schluessel"], gemeinde_schluessel[0][0], strasse["name"],)
                            self.cur.execute(f'INSERT INTO strassen VALUES(?, ?, ?)', sql_values)
                            self.con.commit()
                        else:
                            if schluessel_exist[0][1] != schluessel_exist[0][0] and schluessel_exist[0][2] != strasse['name']:
                                sql_values = (strasse['name'], schluessel_exist[0][0],)
                                self.cur.execute("UPDATE strassen SET name = ? WHERE schluessel = ?", sql_values)
                                self.con.commit()
                    except Exception as e:
                        print("Error: Insert: ", e)
                        for data in member[0]:
                            print(data.tag, ': ', data.text)


    
    def gebaeude(self):
        tree = ET.parse('gebaeude.xml')
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
                                    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326")
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
    
                    self.cur.execute('SELECT * FROM buildings WHERE schluessel = ?', (gebaeude['schluessel'],))
                    building_exist=self.cur.fetchall()
                    self.cur.execute('SELECT schluessel FROM strassen WHERE schluessel = ?', (gebaeude['schluessel_strasse'],))
                    strasse_schluessel=self.cur.fetchall()
#   
                    if len(building_exist)==0:
                        #self.cur.execute('schluessel TEXT     strasse_id TEXT, hausnummer TEXT,  lat TEXT, lon TEXT, FOREIGN KEY (strasse_id) REFERENCES strassen(id))')
#   
                        sql_values = (gebaeude["schluessel"], strasse_schluessel[0][0], gebaeude["hausnummer_key"], gebaeude['adressierungszusatz_key'], gebaeude['lat'], gebaeude['lon'])
                        #print("test", sql_values)
                        self.cur.execute(f'INSERT INTO buildings VALUES(?, ?, ?, ?, ?, ?)', sql_values)
                        self.con.commit()
                    else:
                        if building_exist[0][2] != gebaeude["hausnummer_key"] and building_exist[0][3] != gebaeude['adressierungszusatz_key'] and building_exist[0][4] != gebaeude['lon'] and building_exist[0][5] != gebaeude['lat']:
                            sql_values = (gebaeude["hausnummer_key"], gebaeude['adressierungszusatz_key'], gebaeude['lat'], gebaeude['lon'], gebaeude["schluessel"])
                            self.cur.execute("UPDATE buildings SET hausnummer = ?, adressierungszusatz = ?, lat = ?, lon = ? WHERE schluessel = ?", sql_values)
                            self.con.commit()
                        
                except Exception as e:
                    print("Error: Insert: ", e)
                    for data in member:
                        print(data.tag, ': ', data.text)
                
                #print(gebaeude)
                #return
    def get_building_json(self):
        pass


   

if __name__ == '__main__':
    streets = streets_of_nrw()
    streets.gemeinde()
    streets.strasse()
    streets.gebaeude()
    streets.close()






