#!/usr/bin/env python3
###################################################################
# GPX file merger
# to generate larger trips from previously defined smaller segments
#
# TODO: If two segments end-and-start on the same geographical point,
# there is no check for that and there is a point duplication at the welding point


import sys,re
from glob import glob

# This is to store if all track segments should be treated separately in the export file
# Currently only used if collecting all the available includes.
# Otherwise all merged tracks will be one single segment.
MultiSegment :bool =False

# Stores if next piece of file should be imported in reverse direction or not
Reverse :bool =False

# Stores the directory name of the next piece of import file
Dirname :str  ="gpxincludes/"

# Check if command line argument is specified:
if len(sys.argv) < 2 :
    print(f"*** Usage: {sys.argv[0]} <trip_name>\n***   a file named <trip_name>.cfg must exist in the 'trips' folder")
    exit(-1)

# Store the name of the whole trip
# (this is the trip config file name as well as the export file name)
TRIPNAME :str =sys.argv[1]

# Special command line argument is __SHOW__INCLUDES__ :
# It means that a coverage map of all include file pieces should be generated
if TRIPNAME.strip().upper() == "__SHOW__INCLUDES__" :
    MultiSegment =True
    fout = open("trips/__SHOW__INCLUDES__.cfg","w")
    IL :list = glob("gpxincludes/*.gpx")
    for FName in IL :
        fout.write("include-fwd "+FName[12:-4]+"\n")
    fout.close()

# Temporarily stores the list of geo points for an imported file
# Just to be able to reverse their sequence easily
PointList :list =list(())

# Temporarily stores if a geo point is valid when receiving the '</trkpt>' closing tag
TrkPtValid :bool =False

# Temporary store of geo point coordinates while reading the import file
Lat :str =""
Lon :str =""
Ele :str =""

# Temporarily store if we have received valid elevation for a certain geo point
EleValid :bool =False


# NOW try to import the config file and interpret its lines
try :
    fin = open("trips/"+TRIPNAME+".cfg","r")
except Exception :
    print(f"*** A file named '{TRIPNAME}.cfg' must exist in the 'trips' folder!")
    exit(-2)


fout = open("gpxexport/"+TRIPNAME+".gpx","w")
fout.write('<?xml version="1.0" encoding="UTF-8"?>\n')
fout.write('<gpx version="1.1" creator="TripGenerator.py"\n')
fout.write(' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
fout.write(' xmlns="http://www.topografix.com/GPX/1/1"\n')
fout.write(' xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"\n>\n')
fout.write(f'\t<metadata>\n\t\t<name>{TRIPNAME}</name>\n\t\t<desc>{TRIPNAME}</desc>\n\t</metadata>\n')
fout.write(f'\t<trk>\n\t\t<name>{TRIPNAME}</name>\n\t\t<number>1</number>\n\t\t<trkseg>\n')


for sor in fin :
    sList = sor.strip().split(" ")
    if len(sList) < 2 : continue
    if re.match("^include-fwd.*",sList[0],re.I) :
        Reverse = False
        Dirname = "gpxincludes/"
        print("\x1b[1;32m[>>FWD>>]\x1b[0;32m : "+sList[1]+"\x1b[0m")
    elif re.match("^include-rev.*",sList[0],re.I) :
        Reverse = True
        Dirname = "gpxincludes/"
        print("\x1b[1;35m[<<REV<<]\x1b[0;35m : "+sList[1]+"\x1b[0m")
    elif re.match("^segment.*",sList[0],re.I) :
        Reverse = False
        Dirname = "gpxsegments/"
        print("\x1b[1;33m[==SEG==]\x1b[0m : "+sList[1]+"\x1b[0m")
    else :
        print(f"\x1b[1;31m???\x1b[0;31m Line not understood : {sor.strip()}\x1b[0m")
        continue
    try :
        fin2 = open(Dirname+sList[1]+".gpx","r")
    except Exception :
        print(f"\x1b[0;31m*** \x1b[1mERROR!\x1b[0;31m : Missing element: {Dirname}{sList[1]}.gpx\x1b[0m")
        continue
    PointList = []
    for sor2 in fin2 :
        m1 = re.match('.*<trkpt lat="([0-9.]+)" lon="([0-9.]+)">.*',sor2,re.I)
        m2 = re.match('.*<ele>([0-9.]+)</ele>.*',sor2,re.I)
        m3 = re.match('.*</trkpt>.*',sor2,re.I)
        m4 = re.match('.*<name>(.*)</name>.*',sor2,re.I)
        m5 = re.match('.*<desc>(.*)</desc>.*',sor2,re.I)
        if m1 :
            Lat = m1[1] ; Lon = m1[2]
            TrkPtValid = True
            EleValid = False
        elif m2 :
            if TrkPtValid :
                Ele = m2[1]
                EleValid = True
            else :
                EleValid = False
        elif m3 :
            if TrkPtValid :
                if EleValid :
                    Item = [Lat,Lon,Ele]
                else :
                    Item = [Lat,Lon]
                PointList.append(Item)
                TrkPtValid = False
                EleValid = False
        if m4 :
            if m4[1] != sList[1] :
                print(f"-note- : File Name \x1b[1m{sList[1]}\x1b[0m mismatch with <name> tag \x1b[1m{m4[1]}\x1b[0m")
        if m5 :
            if m5[1] != sList[1] :
                print(f"-note- : File Name \x1b[1m{sList[1]}\x1b[0m mismatch with <desc> tag \x1b[1m{m5[1]}\x1b[0m")
    fin2.close()
    if Reverse : PointList.reverse()
    for E in PointList :
        fout.write(f'\t\t\t<trkpt lat="{E[0]}" lon="{E[1]}">\n')
        if len(E) > 2 : fout.write(f'\t\t\t\t<ele>{E[2]}</ele>\n')
        fout.write('\t\t\t</trkpt>\n')
    if MultiSegment :
        fout.write('\t\t</trkseg>\n\t\t<trkseg>\n')


fout.write('\t\t</trkseg>\n\t</trk>\n</gpx>\n')
fin.close()
fout.close()
