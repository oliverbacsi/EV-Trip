#!/usr/bin/env python3
#
# Take a GPX file with one single whole track inside and create internal split track segments
# based on the provided command line arguments

import sys, re

# This will store the user's requested breakpoints in the track
BRKPT1 :list = list(())
BRKPT2 :dict = dict(())
CurrPoint :int = 0
InFName :str = ""
LastPnt :str = ""
LastEle :str = ""


# Check command line arguments
if len(sys.argv) < 4 :
    print("*** Usage: _split-inside-file.py <inputfile> <name1> <endnode1> [<name2> <endnode2>] [<name3> <endnode3>] ...")
    exit(-1)

# Interpret the waypoint list and set up BREAKPOINTS list
WPLIST = sys.argv
WPLIST.pop(0)
InFName = WPLIST.pop(0)

while len(WPLIST) >1 :
    nStr = WPLIST.pop(0)
    pStr = WPLIST.pop(0)
    if not pStr.isdecimal() : continue
    pInt = int(pStr)
    BRKPT1.append([pInt, nStr])
BRKPT1.sort(key=lambda point: point[0])
# This is now the endpoint:name list.
# It's time to create the startpoint:name dict, as this will be handy during file processing
for i in BRKPT1 :
    BRKPT2[str(CurrPoint)] = i[1]
    CurrPoint = i[0]
del(BRKPT1)
CurrPoint = 0

# Open input and output files
try :
    fin = open(InFName,'r')
except :
    print(f"*** The specified input file ({InFName}) does not exist")
    exit(-2)
fout = open(InFName[:-4]+"-split.gpx",'w')

# Now go through and process
InitialPiece :bool =True
for sor in fin :
    if re.match(".*<trkpt.*",sor,re.I) :
        CurrPoint += 1
        LastPnt = sor
    if re.match(".*<ele.*",sor,re.I) :
        LastEle = sor
    fout.write(sor)
    if InitialPiece and re.match(".*<trkseg>.*",sor,re.I) :
        InitialPiece = False
        fout.write(f"\t\t\t<name>{BRKPT2['0']}</name>\n")
    if re.match(".*</trkpt>.*",sor,re.I) :
        if str(CurrPoint) in BRKPT2.keys() :
            fout.write("\t\t</trkseg>\n\t\t<trkseg>\n\t\t\t<name>"+BRKPT2[str(CurrPoint)]+"</name>\n")
            fout.write(LastPnt+LastEle+"\t\t\t</trkpt>\n")

fin.close()
fout.close()
