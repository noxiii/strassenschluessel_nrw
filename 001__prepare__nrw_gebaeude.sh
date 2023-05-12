#!/bin/bash

# Download Data
# Die Datei mit den Gebäudereferenzen enthält ca. 4 Millionen Adressen für NRW
# Seit 2020-03-01 stehen dies Daten unter der Datenlizenz Deutschland - Zero - Version 2.0 

# Quelle:
# https://www.opengeodata.nrw.de/produkte/geobasis/lk/akt/gebref_txt/gebref_EPSG25832_ASCII.zip
# Zur Zeit ist das Datum der Erfassung 2023-01-01
# Die Datei ist ca. 92 MB groß.


echo Download NRW Data Hausumrisse

mkdir -p ../raw/raw_nrw
mkdir -p ../work
mkdir -p ../output

cd ../raw/raw_nrw

wget -q -c https://www.opengeodata.nrw.de/produkte/geobasis/lk/akt/gebref_txt/gebref_EPSG25832_ASCII.zip

wget -q -c https://www.bezreg-koeln.nrw.de/brk_internet/geobasis/liegenschaftskataster/aktuell/alkis-folgeprodukte/gebaeudereferenzen/datenformatbeschreibung.pdf

unzip -q gebref_EPSG25832_ASCII.zip

cp gebref.txt            ../../work/nrw__gebaeude__00.csv

cd -


#  Convert tu Unix

echo Convert to Unix

dos2unix -q -n  ../work/nrw__gebaeude__00.csv  ../work/nrw__gebaeude__01.csv


#  Normalize

echo  Normalize Str. to Straße and str. to straße

sed -e 's/Str\./Straße/' -e 's/str\./straße/'  ../work/nrw__gebaeude__01.csv  >  ../work/nrw__gebaeude__02.csv


echo  Sort complete file

sort  -t ";"  -k4,4 -k6,6  -k8,8 -k10,10  -k15,15  -k14,14  -k16,16n -k17,17  ../work/nrw__gebaeude__02.csv  >  ../work/nrw__gebaeude__03.csv



echo  Replace spaces with dummy  #x#x#x#

sed -r -e 's/[[:space:]]/#x#x#x#/g'   ../work/nrw__gebaeude__03.csv  > ../work/nrw__gebaeude__04.csv


# Prepare Coordinates

echo  Extract coordinates to front

awk  'BEGIN  {FS=";";  OFS=";"}  {print $19 " " $20  "###" $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21}'  ../work/nrw__gebaeude__04.csv  >  ../work/nrw__gebaeude__05.csv



# Compute  Coordinates

echo Compute coordinates

cs2cs -E +init=epsg:25832   +to +init=epsg:4326  -f "%.7f"  ../work/nrw__gebaeude__05.csv  >  ../work/nrw__gebaeude__06.csv


echo  Create new columns

sed -r -e 's/[[:space:]]+/;/g'    -e 's/###/;/g'  ../work/nrw__gebaeude__06.csv  >  ../work/nrw__gebaeude__07.csv


echo  Recreate spaces


sed -r -e 's/#x#x#x#/ /g'    ../work/nrw__gebaeude__07.csv  >  ../work/nrw__gebaeude__08.csv


echo Create final output as ../output/nrw__gebaeude.csv
echo   Original file, sorted, normalized, plus coordinates in WGS84 or OSM format


awk  'BEGIN  {FS=";";  OFS=";"}  {print  $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $3, $4}'  ../work/nrw__gebaeude__08.csv  >  ../work/nrw__gebaeude__09.csv

cp  ../work/nrw__gebaeude__09.csv  ../output/nrw__gebaeude.csv