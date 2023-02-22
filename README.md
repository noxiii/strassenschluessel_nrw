# Straßenschlüssel NRW Germany
This script is only usable for cities in North Rhine-Westphalia/Germany. 
For better understanding the script and the readme are written in German language.

The license for the script is `MIT`.
The license for the data in the folder `./strassenschluessel` is `Deutschland Lizens zero 2.0`.


## Einleitung

Mit diesem Skript ist es möglich alle Straßenschlüssel für Gemeinden in NRW zu generieren. Diese können mit dem Tag `de:strassenschluessel=` in osm an entsprechende Straßen ergänzt werden.

Das Script ist in der Form nur für NRW nutzbar. Um zu vermeiden das Fehlerhafte Daten in OSM eingetragen werden, bitte ich darum voher die Sclüssel für die entsprechende Gemeinde zu überprüfen und diese nicht automatisiert in OSM zu importieren.

Dieses Script wurde im zuge der erfassung von Straßenschlüssel beim OSM Stammtisch Düseldorf erstellt.

## Entschlüsselung der Daten
Das Land NRW stellt aktuelle Gebäudereferenz Daten über die OpenGeoData Portal als Gebäude referenz text Datei im CSV Format bereit. In dieser sind auch Daten enthalten über diese entsprechen die Straßenschlüssel ermittelt werden können.

[Gebäudereferenz GeoPortal NRW](https://www.opengeodata.nrw.de/produkte/geobasis/lk/akt/gebref_txt/)



Das CSV enthält keine Header Line welche Beschreibt was die einzelnen Spalten bedeuten. Diese werden jedoch in dem folgenden Dokument beschrieben, welche auf dem Kölner Open Data Portal öffentlich bereit gestellt wird.

https://www.bezreg-koeln.nrw.de/brk_internet/geobasis/liegenschaftskataster/aktuell/alkis-folgeprodukte/gebaeudereferenzen/datenformatbeschreibung.pdf

Folgener maßen sieht der Datensatz für ein Gebäude aus. 
```
NBA;OI;QUA;LAN;RBZ;KRS;GMD;OTT;SSS;HNR;ADZ;ZZEEEEEE,EEE;NNNNNNN,NNN;STN;JJJJ-MM-TT
N;DENW000002207504;A;05;1;58;028;0000;12741;6;;32349925,060;5685090,386;Minoritenstraße;2022-01-01
```

Folgendermaßen setz sich diese Zeile zusammen.
gebref.txt
| Kürzel | Beschreibung | Daten |
| ------ | ------------ | ----- |
| NBA | Kennung des Datensatzes | N |
| OI | Eindeutige Nummer des Datensatzes | DENW000002207504 |
| QUA |Qualität der georeferenzierten Gebäudeadresse | A |
| LAN | Schlüssel Land | 05|
| RBZ | Schlüssel Regierungsbezirk | 1|
| KRS | Schlüssel Kreis/kreisfreie Stadt | 58|
| GMD | Schlüssel Gemeinde | 028|
| OTT | Schlüssel des Orts- bzw. Gemeindeteils | 0000|
| SSS | Schlüssel der Straße | 12741|
| HNR | Hausnummer | 6|
| ADZ | Adressierungszusatz | a|
| ZZEEEEEE;EEE | 1. Koordinatenwer | 32349925,060|
| NNNNNNN,NNN | 2. Koordinatenwer | 5685090,386|
| STN| Straßenname | Minoritenstraße |
| JJJJ-MM-TT | Aktualitätsdatu | 2022-01-01|


In der gebref_schluessel.txt kann man den gemeinde Schlüssel entnehmen. Für die Straßenschlüssel wird der Schlüssel für die Gemeinde (G) benötigt. Hier ist zubeachten das z.B. Düsseldorf nicht nur als Gemeinde sondern auch als Kreis (K) und Regierungsbezierk (R) vorhanden ist. Diese werden nicht benötigt.
 

gebref_schluessel.txt
| Beschreibung     | Key | LAN | RBZ | KRS | GMD | Name     |
| ---------------- | --- | --- |  -- | --- | --- | -------- |
| (Bundes)Land     | L   | 05  |     |     |     |NRW       |
| Regierungsbezirk | R   | 05  | 1   |     |     |Düsseldorf|
| Kreis            | K   | 05  | 1   | 58  |     |Mettmann  |
| Gemeinde         | G   | 05  | 1   | 58  |028  |Ratingen  |
| Gemeinde         | G   | 05  | 1   | 11  |000  |Düsseldorf|
| Gemeinde         | G   | 05  | 3   | 15  |000  |Köln      |
| Gemeinde         | G   | 05  | 3   | 62  |008  |Bergheim  |



Der in OSM verwendete Straßenschlüssel ist eine Kombination aus den oben genannten Werten. Mehr dazu auf der Entsprechenden Wiki Seite: 
[DE:Key:de:strassenschluessel](https://wiki.openstreetmap.org/wiki/DE:Key:de:strassenschluessel)

In Nordrhein Westfahlen gibt anders als in manchen anderen Bundesländern keine Gemeindeverbände. Dieser Wert wird durch vier Nullen aufgefüllt, um einen OSM weiten Standart von 17 Ziffern zu haben.

Straßenschlüssel 

| LAN | RBZ | KRS | Gemeindeverbände | GMD | SSS   |
| ----| --- | --- | ----             | --- | ----- | 
| 05  | 1   |58   | 0000             | 028 | 12741 |


## Skript ausführen

Das Skript läd automatisch die Gebäudereferenzen vom geoportal nrw herunter und verarbeitet alle Daten.

Führe das script unter Linux aus.

```
bash ./strassenschlussel.sh
```


## Straßenschlüssel in Deutschland anzeigen

Wo bereits der Schlüssel eingesetzt wird kann über overpass turbo abgefragt werden.

https://overpass-turbo.eu/s/1i1m




## Lizenz und Danksagung

Um die Straßenschlüssel zu ermitteln, wird hierzu auf Gebäudereferenz Daten von NRW zurückgegriffen. Diese werden über das Open Geo Portal des Landes NRW unter der [Deutschland Lizens Zero 2.0](https://www.govdata.de/dl-de/zero-2-0) (stand Mai 2022) bereit gestellt.
Ich möchte mich an dieser Stelle bei den entsprechenden Behörden für die Bereistellung bedanken.

Die im Unterordner `./strassenschluessel` generierten Straßenschlüssel stehen allen unter der [Deutschland Lizens Zero 2.0](https://www.govdata.de/dl-de/zero-2-0) zur nutzung bereit.

Das Script zur generierung der Straßenschlüssel stelle ich unter der Lizens `MIT` bereit.
