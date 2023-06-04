#!/usr/bin/env python3

###############################
# EV Trip details calculator
#

import sys, re

# Battery Pack capacity in kWh as float
BATTCAPACITY :float = 1.00
# Average energy consumption on 100kms
AVGCONSUMPTION :float = 10.00
# Textual name of the trip
TRIPNAME :str ="ERROR"
# Textual name of the Car
CARNAME :str =""
# DataBase representing the whole trip
TRIPDB :dict = dict(())
TRIPDB["days"] = list(())
# Total times calculation
TOTTRIPTIME :float =0.0
TOTCHRGTIME :float =0.0

#################### CLASS PART ####################

class ETAP :
    # Object to store the properties of a trip etap

    def __init__(self, eLen :float, ePwr :float, eSpd :float, eName :str) :
        """Initialize the Etap object
        :param eLen : Length of Etap in kilometers as float
        :param ePwr : Average momentary Power the car is travelling with in kW as float
        :param eSpd : Average speed the car will perform in km/h as float
        :param eName : The textual name of the etap as str"""

        global AVGCONSUMPTION, BATTCAPACITY, TOTTRIPTIME
        self.Len :float = 1.00 * eLen
        self.Pwr :float = 1.00 * ePwr
        self.Spd :float = 1.00 * eSpd
        self.Name :str  = eName
        #Etap time in hours:
        self.Time :float = self.Len / self.Spd
        #Consumed energy in kWh
        self.UsedEnergy = self.Pwr * self.Time
        #Consumed energy in percentage
        self.UsedPercent = 100.00 * self.UsedEnergy / BATTCAPACITY
        TOTTRIPTIME += self.Time

    def prettyPrint(self, CurrEnergy :float, CumulDist :float, CumulEnergy :float, CumulTime :float) -> list :
        """Pretty print one row of data based on incoming information
        :param CurrEnergy : The Energy in the Battery in kWh at the beginning of the etap as float
        :param CumulDist : The cumulated distance travelled at the beginning of the etap as float
        :param CumulEnergy : The cumulated energy consumed at the beginning of the etap as float
        :param CumulTime : The cumulated time spent at the beginning of the etap as float
        :returns : List of total journey values (Distance, Energy, Time)
        """
        global BATTCAPACITY, AVGCONSUMPTION
        JournDist :float
        JournEngy :float
        JournTime :float
        print("\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185mE\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185m",end="")
        print(self.Name[0:25].ljust(25),end="")
        print("\x1b[0m| \x1b[1;33m"+str(round(self.Len,1)).rjust(5),end="\x1b[0m | ")
        print(str(int(self.Spd)).rjust(3),end=" | ")
        print(str(round(self.Pwr,1)).rjust(4),end=" |")
        print("\x1b[1;38;5;131m -"+str(round(self.UsedPercent,1)).rjust(4),end=" \x1b[0m|")
        print("\x1b[1;38;5;131m -"+str(round(self.UsedEnergy,1)).rjust(4),end=" \x1b[0m| ")
        print(str(round(self.Time,2)).rjust(5),end=" || ")
        EndEnergy = CurrEnergy - self.UsedEnergy
        EndPercent = 100.00 * EndEnergy / BATTCAPACITY
        EndRange = 100.00 * EndEnergy / AVGCONSUMPTION
        print(str(round(EndEnergy,1)).rjust(4),end=" |")
        print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
        print(str(round(EndRange,1)).rjust(5),end=" || ")
        JournDist = CumulDist + self.Len
        JournEngy = CumulEnergy + self.UsedEnergy
        JournTime = CumulTime + self.Time
        print(str(round(JournDist,1)).rjust(6),end=" | ")
        print(str(round(JournEngy,1)).rjust(5),end=" | ")
        print(str(round(JournTime,1)).rjust(4)+" |")
        prettyPrintSeparator()

        return list((EndEnergy, JournDist, JournEngy, JournTime))



class CHARGE :
    # Object to store the properties of a charge

    def __init__(self, cPwr :float, cVal :float, cUnit :str, cName :str) :
        """Initialize the Charge object
        :param cPwr : Power of the charger in kW as float
        :param cVal : Charged value (percent or time) as float
        :param cUnit : Either '%' or 'h', specifying unit of cVal
        :param cName : The textual name of the charging as str"""

        global AVGCONSUMPTION, BATTCAPACITY, TOTCHRGTIME
        self.Pwr :float = 1.00 * cPwr
        if cUnit == "%" :
            self.ChargedPercent = 1.00 * cVal
            self.ChargedEnergy = 0.01 * cVal * BATTCAPACITY
            self.Time = self.ChargedEnergy / self.Pwr
        else :
            self.Time = 1.00 * cVal
            self.ChargedEnergy = 1.00 * self.Pwr * self.Time
            self.ChargedPercent = 100.00 * self.ChargedEnergy / BATTCAPACITY
        self.ChargedRange = 100.00 * self.ChargedEnergy / AVGCONSUMPTION
        self.ChargingSpeed = 100.00 * self.Pwr / AVGCONSUMPTION
        self.Name :str  = cName
        TOTCHRGTIME += self.Time

    def prettyPrint(self, CurrEnergy :float, CumulDist :float, CumulEnergy :float, CumulTime :float) -> list :
        """Pretty print one row of data based on incoming information
        :param CurrEnergy : The Energy in the Battery in kWh at the beginning of the etap as float
        :param CumulDist : The cumulated distance travelled at the beginning of the etap as float
        :param CumulEnergy : The cumulated energy consumed at the beginning of the etap as float
        :param CumulTime : The cumulated time spent at the beginning of the etap as float
        :returns : List of total journey values (Distance, Energy, Time)
        """
        global BATTCAPACITY, AVGCONSUMPTION
        JournDist :float
        JournEngy :float
        JournTime :float
        print("\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44mC\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44m",end="")
        print(self.Name[0:25].ljust(25),end="\x1b[0m| ")
        print(str(round(self.ChargedRange,1)).rjust(5),end="\x1b[0m | ")
        print(str(int(self.ChargingSpeed)).rjust(3),end=" | ")
        print(str(round(self.Pwr,1)).rjust(4),end=" |")
        print("\x1b[1;38;5;47m +"+str(round(self.ChargedPercent,1)).rjust(4),end=" \x1b[0m|")
        print("\x1b[1;38;5;47m +"+str(round(self.ChargedEnergy,1)).rjust(4),end=" \x1b[0m| \x1b[1;33m")
        print(str(round(self.Time,2)).rjust(5),end="\x1b[0m || ")
        EndEnergy = CurrEnergy + self.ChargedEnergy
        EndPercent = 100.00 * EndEnergy / BATTCAPACITY
        EndRange = 100.00 * EndEnergy / AVGCONSUMPTION
        print(str(round(EndEnergy,1)).rjust(4),end=" |")
        print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
        print(str(round(EndRange,1)).rjust(5),end=" || ")
        JournDist = CumulDist
        JournEngy = CumulEnergy
        JournTime = CumulTime + self.Time
        print(str(round(JournDist,1)).rjust(6),end=" | ")
        print(str(round(JournEngy,1)).rjust(5),end=" | ")
        print(str(round(JournTime,1)).rjust(4)+" |")
        prettyPrintSeparator()

        return list((EndEnergy, JournDist, JournEngy, JournTime))


#################### PROC PART ####################

def prettyPrintSeparator() -> None :
    """Print a separator line in the output table"""
    print("+",end="")
    for i in [1, 25, 7, 5, 6, 7, 7, 7, 0, 6, 7, 7, 0, 8, 7, 6] :
        print("-"*i, end="+")
    print("")

def SOC2ANS(_perc :float ="-1.0") -> str:
    """Return the ANSI color of a Battery State of Charge
    :param _perc : State of charge in percentage as float
    :return : Perfectly formatted ANSI escape sequence string"""

    if _perc >= 100.0: return '\x1b[1;48;5;75m\x1b[1;38;5;195m'
    if _perc >= 95.0 : return '\x1b[1;48;5;68m\x1b[1;38;5;152m'
    if _perc >= 90.0 : return '\x1b[1;48;5;32m\x1b[1;38;5;117m'
    if _perc >= 85.0 : return '\x1b[1;48;5;25m\x1b[1;38;5;75m'
    if _perc >= 80.0 : return '\x1b[1;48;5;21m\x1b[1;38;5;33m'
    if _perc >= 75.0 : return '\x1b[1;48;5;19m\x1b[1;38;5;38m'
    if _perc >= 70.0 : return '\x1b[1;48;5;24m\x1b[1;38;5;43m'
    if _perc >= 65.0 : return '\x1b[1;48;5;23m\x1b[1;38;5;48m'
    if _perc >= 60.0 : return '\x1b[1;48;5;22m\x1b[1;38;5;46m'
    if _perc >= 55.0 : return '\x1b[1;48;5;58m\x1b[1;38;5;82m'
    if _perc >= 50.0 : return '\x1b[1;48;5;94m\x1b[1;38;5;118m'
    if _perc >= 45.0 : return '\x1b[1;48;5;130m\x1b[1;38;5;154m'
    if _perc >= 40.0 : return '\x1b[1;48;5;166m\x1b[1;38;5;190m'
    if _perc >= 35.0 : return '\x1b[1;48;5;202m\x1b[1;38;5;226m'
    if _perc >= 30.0 : return '\x1b[1;48;5;160m\x1b[1;38;5;221m'
    if _perc >= 25.0 : return '\x1b[1;48;5;124m\x1b[1;38;5;215m'
    if _perc >= 20.0 : return '\x1b[1;48;5;88m\x1b[1;38;5;208m'
    if _perc >= 15.0 : return '\x1b[1;48;5;52m\x1b[1;38;5;202m'
    if _perc >= 10.0 : return '\x1b[1;48;5;53m\x1b[1;38;5;197m'
    if _perc >=  5.0 : return '\x1b[1;48;5;54m\x1b[1;38;5;199m'
    if _perc >=  0.0 : return '\x1b[1;48;5;55m\x1b[1;38;5;201m'
    return '\x1b[1;48;5;213m\x1b[1;38;5;232m'


#################### MAIN PART ####################

if len(sys.argv) < 2 :
    print(f"Usage : {sys.argv[0]} <TRIP file name>")
    exit(-1)

try :
    fin = open(sys.argv[1], "r")
except :
    print(f"Could not open input file: {sys.argv[1]}")
    exit(-2)
LineNumber :int =0
DayIsActive :bool =False
ID :str ="error"

for sor in fin :
    LineNumber += 1
    m1 = re.match("CAPA ([0-9.]+)kWh", sor, re.I)
    if m1 :
        BATTCAPACITY = float(m1[1])
        continue
    m1 = re.match("CNSM ([0-9.]+)kWh.*", sor, re.I)
    if m1 :
        AVGCONSUMPTION = float(m1[1])
        continue
    m1 = re.match("TRIP +(.+)", sor, re.I)
    if m1 :
        TRIPNAME = m1[1].strip()
        continue
    m1 = re.match("CAR +(.+)", sor, re.I)
    if m1 :
        CARNAME = m1[1].strip()
        continue

    m1 = re.match("DAY +(.+) +(.+) +(.*)", sor, re.I)
    if m1 :
        ID = str(m1[1]).strip()
        Name = str(m1[3]).strip()
        Chrg1 = str(m1[2]).strip()
        if Chrg1.isdecimal() :
            Chrg = int(Chrg1)
            if Chrg > 100 : Chrg = 100
            if Chrg < 1 : Chrg = 1
        else :
            if re.match("prev", Chrg1, re.I) :
                Chrg = "prev"
            else :
                fin.close()
                print(f"Line #{LineNumber}: Initial Charge specification error at day {ID} : Must be either 'prev' or an integer between 1-100")
                exit(-3)
        TRIPDB["days"].append(ID)
        TRIPDB[ID+":InitChg"] = str(Chrg)
        TRIPDB[ID+":Name"] = Name
        TRIPDB[ID+":Events"] = list(())
        DayIsActive = True
        continue

    m1 = re.match("ETAP +([0-9.]+)km +([0-9.]+)kW +([0-9.]+)km/h +\| +(.*)", sor, re.I)
    if m1 :
        if not DayIsActive :
            fin.close()
            print(f"Line #{LineNumber}: ETAP specified without valid DAY first")
            exit(-3)
        EtLen = float(str(m1[1]).strip())
        EtPwr = float(str(m1[2]).strip())
        EtSpd = float(str(m1[3]).strip())
        EtNam = str(m1[4]).strip()
        EtObj = ETAP(EtLen, EtPwr, EtSpd, EtNam)
        TRIPDB[ID+":Events"].append(EtObj)
        continue

    m1 = re.match("CHRG +([0-9.]+)kW +([0-9.]+)([%h]r?s?) +\| +(.*)", sor, re.I)
    if m1 :
        if not DayIsActive :
            fin.close()
            print(f"Line #{LineNumber}: CHRG specified without valid DAY first")
            exit(-3)
        ChPwr = float(str(m1[1]).strip())
        ChVal = float(str(m1[2]).strip())
        ChUoM = str(m1[3]).strip()
        ChNam = str(m1[4]).strip()
        ChObj = CHARGE(ChPwr, ChVal, ChUoM, ChNam)
        TRIPDB[ID+":Events"].append(ChObj)
        continue

    # To avoid getting a warning message for empty lines:
    if not len(sor.strip()) : continue

    print(f"Line #{LineNumber}: Not understood: <{sor}>")

fin.close()


JOURNEYDISTANCE :float =0.00
JOURNEYENERGY :float =0.00
JOURNEYTIME :float =0.00
REMAININGCHARGE :float =0.00
JOURNEYTITLE = f"{TRIPNAME}   with  {CARNAME}  /{BATTCAPACITY} kWh/"
print("\n\x1b[0;48;5;240m\x1b[1;37m" + "#"*123+"\x1b[0m")
print("\x1b[0;48;5;240m\x1b[1;37m#" + JOURNEYTITLE.center(121) + "#\x1b[0m")
print("\x1b[0;48;5;240m\x1b[1;37m"+"#"*123+"\x1b[0m")

for ID in TRIPDB["days"] :
    print("|" + " "*121 + "|")
    print(f'|\x1b[0;36;44m Day \x1b[1m[{ID}] \x1b[1;32;44m {TRIPDB[ID+":Name"]} \x1b[0;36;44m',end="")
    print(" "*(111-len(ID)-len(TRIPDB[ID+":Name"])) +"\x1b[0m|")
    print("|                             TRIP                                       ||       BATTERY        ||         JOURNEY       |")
    print("\x1b[1m|T|Trip Item                |  km   | spd |  kW  |   %   |  kWh  |   h   ||  kWh |   %   |   km  ||   km   |  kWh  |   h  |\x1b[0m")
    if TRIPDB[ID+":InitChg"].isdecimal() :
        REMAININGCHARGE = 0.01 * int(TRIPDB[ID+":InitChg"]) * BATTCAPACITY
        PRINTPERC = float(TRIPDB[ID+":InitChg"])
    else :
        PRINTPERC = 100.0 * REMAININGCHARGE / BATTCAPACITY
    PRINTDIST = 100.0 * REMAININGCHARGE / AVGCONSUMPTION
    prettyPrintSeparator()
    print("\x1b[0;36m|S|--- START ---            |       |     |      |       |       |       || ",end="")
    print(str(round(REMAININGCHARGE,1)).rjust(4), end=" |")
    print(SOC2ANS(PRINTPERC)+" "+str(round(PRINTPERC,1)).rjust(5), end=" \x1b[0m\x1b[0;36m| ")
    print(str(round(PRINTDIST,1)).rjust(5), end=" || ")
    print(str(round(JOURNEYDISTANCE,1)).rjust(6), end=" | ")
    print(str(round(JOURNEYENERGY,1)).rjust(5), end=" | ")
    print(str(round(JOURNEYTIME,1)).rjust(4), end=" |\x1b[0m\n")
    prettyPrintSeparator()

    for xx in TRIPDB[ID+":Events"] :
        REMAININGCHARGE, JOURNEYDISTANCE, JOURNEYENERGY, JOURNEYTIME = xx.prettyPrint(REMAININGCHARGE, JOURNEYDISTANCE, JOURNEYENERGY, JOURNEYTIME)

print(f"\n * TOTAL TRAVELLING TIME : {str(round(TOTTRIPTIME,2)).rjust(5)} hrs  ({round(100.0*TOTTRIPTIME/JOURNEYTIME,1)}%)")
print(f" * TOTAL CHARGING TIME   : {str(round(TOTCHRGTIME,2)).rjust(5)} hrs  ({round(100.0*TOTCHRGTIME/JOURNEYTIME,1)}%)")
print(f" * AVERAGE SPEED         : {str(round(JOURNEYDISTANCE/JOURNEYTIME,1)).rjust(5)} km/h")
print(f" * AVERAGE CONSUMPTION   : {round(100.0*JOURNEYENERGY/JOURNEYDISTANCE,2)} kWh/100km\n")



# Battery SOC color test :
#_test1 :float =100.5
#while _test1 > -5.0 :
#    print(SOC2ANS(_test1)+str(_test1).rjust(8)+"\x1b[0m")
#    _test1 -= 1.0
