curl 'https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_Gemeinde' > download/gemeinde.xml

curl 'https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_LagebezeichnungKatalogeintrag' > download/strassen.xml

curl 'https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_aaa-modell-basiert?service=WFS&version=2.0.0&request=getFeature&TYPENAMES=adv:AX_GeoreferenzierteGebaeudeadresse' > download/gebaeude.xml
