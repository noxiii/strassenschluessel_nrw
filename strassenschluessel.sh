#!/bin/bash
## Variables
keydir="./strassenschluessel"
refdir="./gebref"


gebref_file="gebref_EPSG25832_ASCII.zip"
gebref_link="https://www.opengeodata.nrw.de/produkte/geobasis/lk/akt/gebref_txt/${gebref_file}"

gebref="${refdir}/gebref.txt"

# Download and unzip gebref
if [ ! -f ${gebref} ]
then
   echo "Download ${gebref_file}"
   mkdir -p ${refdir}

   wget ${gebref_link} -P ${refdir} 
   unzip ${refdir}/${gebref_file} -d ${refdir}
fi

mkdir -p ${keydir}

# Schleife nur Zeilenweise durchgehen, da Gemeindenamen aus mehreren Wörtern bestehen kann (Siehe: Mülheim an der Ruhr)
IFS=$'\n'
for gemeinde in $(cat ${gebref} | cut -d";" -f11 | sort -u)
do 
  # Extrahiere den Gemeindenamen und bereinige den von: Leerzeichen, Zeilenumbrüche und Sonderzeichen
  gemeinde_name_clean=$(echo $gemeinde | cut -d";" -f 6 | sed -e 's/\ /_/g' -e 's/[\(\)\.\/\\]//g' -e 's/[Ää]/ae/g' -e 's/[Öö]/oe/g' -e 's/[Üü]/ue/g' -e 's/ß/ss/g')
  echo $gemeinde_name_clean
  # Definiere Variable für Gemeinde Datei
  file="${keydir}/${gemeinde_name_clean}.csv"

  # In NRW gibt es keine "Gemeindeverbände" daher wurden die Stellen 6. bis 9. durch 0000 aufgefüllt.
  grep $gemeinde ${gebref} | awk -v gemeinde=$gemeinde -F ";" '{ if($11==gemeinde) print $4$6$8"0000"$10$14";"$15 }' | sort | uniq > ${file}
  count=$(cat ${file} | wc -l)
  echo "Gefundene Straßenschlüssel für ${gemeinde}: ${count}"
done


