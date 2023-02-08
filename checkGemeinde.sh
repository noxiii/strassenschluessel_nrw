#!/bin/bash

city=$1

name_filtered=$(echo $city | sed -e 's/\ /_/g' -e 's/[Ää]/ae/g' -e 's/[Öö]/oe/g' -e 's/[Üü]/ue/g' -e 's/ß/ss/g')
path='./strassenschluessel/'
file="./strassenschluessel/${name_filtered}.csv"

if [ -z "${city}" ]
then
   echo "Gebe einen Gemeindenamen mit"
   echo "${0##*/} Düsseldorf"
   exit 1
fi

if [ ! -f "${file}" ]
then
	echo "\"$city\" not exist: $file"
	exit 1
fi


query='
[out:csv("de:strassenschluessel",::id,name;false;";")];
(
  area[name="Ratingen"];
  way["highway"]
     [!"de:strassenschluessel_exists"]
  	  ["highway"!="platform"]
     ["service"!="parking_aisle"]
     ["name"](area);
); 
out;
'

overpass=$(mktemp)

curl -d "${query}" -X POST http://overpass-api.de/api/interpreter > $overpass

pat="[0-9]+\;[0-9]+\;.*"
if [[ ! $(head -n1 $overpass) =~ $pat ]]; then
	echo "Downloaded file not ok"
	head -n10 $overpass 
   exit 1
fi

dataDir="data/$name_filtered"
missedFile="$dataDir/missed.csv"
failureFile="$dataDir/failure.csv"
noKeyFile="$dataDir/failure.csv"
mkdir -p $dataDir
echo -n "" > $missedFile
echo -n "" > $failureFile
echo -n "" > $noKeyFile

echo "Check entries"
while read entry; do
	streetKey=$(echo $entry | cut -d";" -f1)
   osmID=$(echo $entry | cut -d";" -f2)
   streetName=$(echo $entry | cut -d";" -f3)

   if [ -z $streetKey ]
   then
      streetkeyEntry=$(grep "$streetName" $file)
      echo "$osmID;$streetName" >> "$missedFile"
      continue
   fi

   if ! grep "$streetKey" "$file" | grep -q "$streetName"
   then
      streetkeyEntry=$(grep "$streetName" $file)
      if [ -z "$streetkeyEntry" ]
      then
      	echo "$entry" > $noKeyFile}
      else
         echo "$osmID;$streetkeyEntry" >> "${failureFile}"
      fi
   fi

   if ! grep "$streetName" "$file" | grep -q "$streetKey"
   then
      streetkeyEntry=$(grep "$streetName" $file)
      if [ -z "$streetkeyEntry" ]
      then
      	echo "$entry" > $noKeyFile}
      else
         echo "$osmID;$streetkeyEntry" >> "${failureFile}"
      fi 
   fi
done < $overpass

echo "Found keys: $(cat $overpass | wc -l)"
echo "Found missed: $(cat $missedFile | wc -l) in $missedFile"
echo "Found failure: $(cat $failureFile | wc -l) in $failureFile"
echo "Found missed keys: $(cat $noKeyFile | wc -l) in $noKeyFile"

rm $overpass

