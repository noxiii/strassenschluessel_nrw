#!/bin/bash
## Variables
keydir="./strassenschluessel"
refdir="./gebref"

gebref_file="gebref_EPSG4647_ASCII.zip"
gebref_link="https://www.opengeodata.nrw.de/produkte/geobasis/lk/akt/gebref_txt/${gebref_file}"

gebref="${refdir}/gebref.txt"
gebref_schluessel="${refdir}/gebref_schluessel.txt"

# Download and unzip gebref
if [ ! -f ${gebref} ] && [ ! -f ${gebref_schluessel} ]
then
   echo "Download ${gebref_file}"
   mkdir -p ${refdir}

   wget ${gebref_link} -P ${refdir} 
   unzip ${refdir}/${gebref_file} -d ${refdir}
fi

mkdir -p ${keydir}

while read gemeinde
do 
  # Prüfe ob die Gemeinde einen Schlüssel mit der korrekten Formatierung besitzt.
  if $(echo ${gemeinde} | grep -q -E '^G;[0-9]{2};[0-9];[0-9]{2};[0-9]{3};*' )
  then
    ## Extrahiere den Gemeindenamen und bereinige den von: Leerzeichen, Zeilenumbrüche und Sonderzeichen
    gemeinde_name=$(echo $gemeinde | cut -d";" -f 6 | sed -e 's/\ /_/g' -e 's/.$//' -e 's/[\(\)\.\/\\]//g' -e 's/[Ää]/ae/g' -e 's/[Öö]/oe/g' -e 's/[Üü]/ue/g' -e 's/ß/ss/g')

    ## Extrahiere den Gemeindeschlüssel und setze diesen für anschließende Suche als pattern zusammen.
    gemeinde_pattern=$(echo $gemeinde |awk -F ";" '{ print $2";"$3";"$4";"$5 }')

    ## Definiere Variable für Gemeinde Datei
    file="${keydir}/${gemeinde_name}.csv"

    ## Suche nach dem Gemeindeschlüssel pattern und setze den Straßenschlüssel zusammen. 
    ## In NRW gibt es keine "Gemeindeverbände" daher wurden die Stellen 6. bis 9. durch 0000 aufgefüllt.
    grep -i ${gemeinde_pattern} ${gebref} | awk -F ";" '{ print $4$5$6"0000"$7$9";"$14 }' | sort | uniq > ${file}
    count=$(cat ${file} | wc -l)
    echo "Gefundene Straßenschlüssel für ${gemeinde_name}: ${count}"
  fi
done < ${gebref_schluessel}


