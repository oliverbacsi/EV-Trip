#!/usr/bin/env python3

###############################
# EV Trip details calculator
#

import sys, re


#################### CLASS PART ####################


class TRIP :
    # Object to store whole trip properties

    def __init__(self, tName :str) :
        """Initialize the Trip object
        :param tName : Trip name as str"""
        self.Name :str = tName
        # Collection of days
        self.Days :list = list(())
        # Total Travelling Time
        self.TotTripTime :float =0.0
        # Total Charging Time
        self.TotChrgTime :float =0.0

        # Dynamic variables
        self.InitCharge :dict = dict(())
        self.DayName :dict = dict(())
        self.Events :dict = dict(())
        self.Alti :dict = dict(())

    def addTripTime(self, ti :float) :
        self.TotTripTime = self.TotTripTime + ti

    def addChrgTime(self, ti :float) :
        self.TotChrgTime = self.TotChrgTime + ti

    def addDay(self, da :str) :
        self.Days.append(da)
        self.InitCharge[ID] = "error"
        self.DayName[ID] = "error"
        self.Events[ID] = list(())
        self.Alti[ID] = "0"



class CAR :
    # Object to store default car properties

    def __init__(self, cName :str) :
        """Initialize the Car object
        :param cName : Car name as str"""
        self.Name :str =cName
        # Battery Pack Capacity in kWh
        self.BattCapacity :float =0.0
        # Average Consumption in kWh / 100km
        self.AvgConsumption :float =12.0
        # Default average motor power during driving in kW
        self.AvgMotPower :float =12.0
        # Default average charging power in kW
        self.AvgChgPower :float =3.6
        # Default average cruising speed in km/h
        self.AvgSpeed :float =80.0

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the car"""
        m1 = re.match("^([0-9]+\.?[0-9]*)kWh$",parStr)
        m2 = re.match("^([0-9]+\.?[0-9]*)kWh/100$",parStr)
        m3 = re.match("^([0-9]+\.?[0-9]*)/([0-9]+\.?[0-9]*)kW$",parStr)
        m4 = re.match("^([0-9]+\.?[0-9]*)km/h$",parStr)

        if m1 : self.BattCapacity = float(m1[1])
        if m2 : self.AvgConsumption = float(m2[1])
        if m4 : self.AvgSpeed = float(m4[1])
        if m3 :
            self.AvgMotPower = float(m3[1])
            self.AvgChgPower = float(m3[2])



class ETAP :
    # Object to store the properties of a trip etap

    def __init__(self, eName :str) :
        """Initialize the Etap object
        :param eName : The textual name of the etap as str"""
        self.Name :str  =eName
        # Etap Length in km
        self.Len :float =1.0
        # Average Motor Power (default)
        self.Pwr :float =c.AvgMotPower
        # Average Car Speed (default)
        self.Spd :float =c.AvgSpeed
        # Etap time in hours:
        self.Time :float =1.0
        # Consumed energy in kWh
        self.UsedEnergy =1.0
        # Consumed energy in percentage
        self.UsedPercent =1.0
        # Add to total Trip Time
        self.AddTotTripTime :float =0.0
        # Etap End Altitude (Sea Level in meters, integer)
        self.EndAltitude :int =0

        # Calculated data
        self.UsedPercent :float =0.0
        self.UsedEnergy  :float =0.0
        self.Time        :float =0.0

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the etap"""
        m1 = re.match("^([0-9]+\.?[0-9]*)km$",parStr)
        m2 = re.match("^([0-9]+\.?[0-9]*)kW$",parStr)
        m3 = re.match("^([0-9]+)km/h$",parStr)
        m4 = re.match("^([0-9]+)m$",parStr)

        if m1 : self.Len = float(m1[1])
        if m2 : self.Pwr = float(m2[1])
        if m3 : self.Spd = float(m3[1])
        if m4 : self.EndAltitude = int(m4[1])

    def recalc(self) :
        """Recalculate missing etap data based on the existing one"""
        # Etap Time in hrs
        self.Time = self.Len / self.Spd
        # Consumed Energy in kWh
        self.UsedEnergy = self.Pwr * self.Time
        # Consumed Energy in Battery Percentage
        self.UsedPercent = 100.00 * self.UsedEnergy / c.BattCapacity
        # This is to be added when displaying
        self.AddTotTripTime = self.Time

    def prettyPrint(self, CurrEnergy :float, DayDist :float, DayEnergy :float, DayTime :float, CumulDist :float, CumulEnergy :float, CumulTime :float) -> list :
        """Pretty print one row of data based on incoming information
        :param CurrEnergy : The Energy in the Battery in kWh at the beginning of the etap as float
        :param DayDist : The daily distance travelled at the beginning of the etap as float
        :param DayEnergy : The daily energy consumed at the beginning of the etap as float
        :param DayTime : The daily time spent at the beginning of the etap as float
        :param CumulDist : The cumulated distance travelled at the beginning of the etap as float
        :param CumulEnergy : The cumulated energy consumed at the beginning of the etap as float
        :param CumulTime : The cumulated time spent at the beginning of the etap as float
        :returns : List of total journey values (Distance, Energy, Time)
        """
        JournDist :float
        JournEngy :float
        JournTime :float
        DDist :float
        DEngy :float
        DTime :float
        print("\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185mE\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185m",end="")
        print(self.Name[0:25].ljust(25),end="")
        print("\x1b[0m| "+str(self.EndAltitude).rjust(4),end=" ")
        print("| \x1b[1;33m"+str(round(self.Len,1)).rjust(5),end="\x1b[0m | ")
        print(str(int(self.Spd)).rjust(3),end=" | ")
        print(str(round(self.Pwr,1)).rjust(4),end=" |")
        print("\x1b[1;38;5;131m -"+str(round(self.UsedPercent,1)).rjust(4),end=" \x1b[0m|")
        print("\x1b[1;38;5;131m -"+str(round(self.UsedEnergy,1)).rjust(4),end=" \x1b[0m| ")
        print(str(round(self.Time,2)).rjust(5),end=" || ")
        EndEnergy = CurrEnergy - self.UsedEnergy
        EndPercent = 100.00 * EndEnergy / c.BattCapacity
        EndRange = 100.00 * EndEnergy / c.AvgConsumption
        print(str(round(EndEnergy,1)).rjust(4),end=" |")
        print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
        print(str(round(EndRange,1)).rjust(5),end=" || ")
        JournDist = CumulDist + self.Len
        JournEngy = CumulEnergy + self.UsedEnergy
        JournTime = CumulTime + self.Time
        DDist = DayDist + self.Len
        DEngy = DayEnergy + self.UsedEnergy
        DTime = DayTime + self.Time
        print(str(round(DDist,1)).rjust(6),end=" | ")
        print(str(round(DEngy,1)).rjust(5),end=" | ")
        print(str(round(DTime,1)).rjust(4),end=" || ")
        print(str(round(JournDist,1)).rjust(6),end=" | ")
        print(str(round(JournEngy,1)).rjust(5),end=" | ")
        print(str(round(JournTime,1)).rjust(4)+" |")
        #prettyPrintSeparator()
        t.addTripTime(self.AddTotTripTime)

        return list((EndEnergy, DDist, DEngy, DTime, JournDist, JournEngy, JournTime))



class CHARGE :
    # Object to store the properties of a charge

    def __init__(self, cName :str) :
        """Initialize the Charge object
        :param cName : The textual name of the charging as str"""
        self.Name :str = cName
        # This informs the recalc() method what to calculate the missing parameters from:
        #   "hrs" means that the charging time was specified last, so percentage comes from it
        #   "perc" means that percentage was specified last, so the time comes from it
        self.CalcFrom :str ="hrs"
        # Add to Total Charge Time
        self.AddTotChrgTime :float =0.0
        # Charging Power
        self.Pwr :float = c.AvgChgPower
        # Charging Time
        self.Time :float =0.0
        # Charged Energy in kWh and Percent
        self.ChargedEnergy :float =0.0
        self.ChargedPercent :float =0.0
        # Charged car range
        self.ChargedRange :float =0.0
        # Charging speed (charged range in km per hr time)
        self.ChargingSpeed :float =0.0

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the charge"""
        m1 = re.match("^([0-9]+\.?[0-9]*)hrs?$",parStr)
        m2 = re.match("^([0-9]+\.?[0-9]*)kW$",parStr)
        m3 = re.match("^([0-9]+)\%$",parStr)

        if m1 :
            self.Time = float(m1[1])
            self.CalcFrom = "hrs"
        if m2 : self.Pwr = float(m2[1])
        if m3 :
            self.ChargedPercent = float(m3[1])
            self.CalcFrom = "perc"

    def recalc(self) :
        """Recalculate the required parameters"""
        if self.CalcFrom == "perc" :
            self.ChargedEnergy = 0.01 * self.ChargedPercent * c.BattCapacity
            self.Time = self.ChargedEnergy / self.Pwr
        else :
            self.ChargedEnergy = 1.00 * self.Pwr * self.Time
            self.ChargedPercent = 100.00 * self.ChargedEnergy / c.BattCapacity
        self.ChargedRange = 100.00 * self.ChargedEnergy / c.AvgConsumption
        self.ChargingSpeed = 100.00 * self.Pwr / c.AvgConsumption
        # Now we have the time to be added
        self.AddTotChrgTime = self.Time

    def prettyPrint(self, CurrEnergy :float, DayDist :float, DayEnergy :float, DayTime :float, CumulDist :float, CumulEnergy :float, CumulTime :float) -> list :
        """Pretty print one row of data based on incoming information
        :param CurrEnergy : The Energy in the Battery in kWh at the beginning of the etap as float
        :param DayDist : The daily distance travelled at the beginning of the etap as float
        :param DayEnergy : The daily energy consumed at the beginning of the etap as float
        :param DayTime : The daily time spent at the beginning of the etap as float
        :param CumulDist : The cumulated distance travelled at the beginning of the etap as float
        :param CumulEnergy : The cumulated energy consumed at the beginning of the etap as float
        :param CumulTime : The cumulated time spent at the beginning of the etap as float
        :returns : List of total journey values (Distance, Energy, Time)
        """
        JTime :float  # Journey time (cumulated total)
        DTime :float  # Daily time (day summary)
        prettyPrintSeparator()
        print("\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44mC\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44m",end="")
        print(self.Name[0:25].ljust(25),end="\x1b[0m|      | ")
        print(str(round(self.ChargedRange,1)).rjust(5),end="\x1b[0m | ")
        print(str(int(self.ChargingSpeed)).rjust(3),end=" | ")
        print(str(round(self.Pwr,1)).rjust(4),end=" |")
        print("\x1b[1;38;5;47m +"+str(round(self.ChargedPercent,1)).rjust(4),end=" \x1b[0m|")
        print("\x1b[1;38;5;47m +"+str(round(self.ChargedEnergy,1)).rjust(4),end=" \x1b[0m| \x1b[1;33m")
        print(str(round(self.Time,2)).rjust(5),end="\x1b[0m || ")
        EndEnergy = CurrEnergy + self.ChargedEnergy
        EndPercent = 100.00 * EndEnergy / c.BattCapacity
        EndRange = 100.00 * EndEnergy / c.AvgConsumption
        print(str(round(EndEnergy,1)).rjust(4),end=" |")
        print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
        print(str(round(EndRange,1)).rjust(5),end=" || ")
        JTime = CumulTime + self.Time
        DTime = DayTime + self.Time
        print(str(round(DayDist,1)).rjust(6),end=" | ")
        print(str(round(DayEnergy,1)).rjust(5),end=" | ")
        print(str(round(DTime,1)).rjust(4),end=" || ")
        print(str(round(CumulDist,1)).rjust(6),end=" | ")
        print(str(round(CumulEnergy,1)).rjust(5),end=" | ")
        print(str(round(JTime,1)).rjust(4)+" |")
        #prettyPrintSeparator()
        t.addChrgTime(self.AddTotChrgTime)

        return list((EndEnergy, DayDist, DayEnergy, DTime, CumulDist, CumulEnergy, JTime))


#################### PROC PART ####################

def prettyPrintSeparator() -> None :
    """Print a separator line in the output table"""
    print("+",end="")
    for i in [1, 25, 6, 7, 5, 6, 7, 7, 7, 0, 6, 7, 7, 0, 8, 7, 6, 0, 8, 7, 6] :
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
    print(f"Usage : {sys.argv[0]} <Trip file name>")
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

    sor = sor.strip()
    if not len(sor) : continue
    if re.match("^#.*$", sor) : continue

    m0 = re.match("^TRIP +(.*)$", sor, re.I)
    if m0 :
        t = TRIP(str(m0[1]).strip())
        continue

    m1 = re.match("^CAR +(.*) +\| (.*)$", sor, re.I)
    if m1 :
        c = CAR(m1[1].strip())
        for _par in m1[2].split(" ") : c.interpretParm(_par)
        continue

    m2 = re.match("^DAY +(.+) +([0-9]+)\% +([0-9]+)m +\| +(.*)$", sor, re.I)
    m3 = re.match("^DAY +(.+) +(prev) +([0-9]+)m +\| +(.*)$", sor, re.I)
    if m2 or m3 :
        if m2 :
            m1 = m2
        else :
            m1 = m3
        ID = str(m1[1]).strip()
        Chrg1 = str(m1[2]).strip()
        Alti1 = str(m1[3]).strip()
        Name = str(m1[4]).strip()
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
        t.addDay(ID)
        t.InitCharge[ID] = str(Chrg)
        t.DayName[ID] = Name
        t.Alti[ID] = Alti1
        DayIsActive = True
        continue

    m1 = re.match("^ETAP +(.*) +\| +(.*)$", sor, re.I)
    if m1 :
        if not DayIsActive :
            fin.close()
            print(f"Line #{LineNumber}: ETAP specified without valid DAY first")
            exit(-3)
        EtObj = ETAP(str(m1[2]).strip())
        for _par in m1[1].split(" ") : EtObj.interpretParm(_par)
        EtObj.recalc()
        t.Events[ID].append(EtObj)
        continue

    m1 = re.match("^CHRG +(.*) +\| +(.*)$", sor, re.I)
    if m1 :
        if not DayIsActive :
            fin.close()
            print(f"Line #{LineNumber}: CHRG specified without valid DAY first")
            exit(-3)
        ChObj = CHARGE(str(m1[2]).strip())
        for _par in m1[1].split(" ") : ChObj.interpretParm(_par)
        ChObj.recalc()
        t.Events[ID].append(ChObj)
        continue

    print(f"Line #{LineNumber}: Not understood: <{sor}>")

fin.close()


JOURNEYDISTANCE :float =0.00
JOURNEYENERGY :float =0.00
JOURNEYTIME :float =0.00
DAYDISTANCE :float =0.00
DAYENERGY :float =0.00
DAYTIME :float =0.00
REMAININGCHARGE :float =0.00
JOURNEYTITLE = f"{t.Name}   with  {c.Name}  /{c.BattCapacity} kWh/"
print("\n\x1b[0;48;5;240m\x1b[1;37m" + "#"*155+"\x1b[0m")
print("\x1b[0;48;5;240m\x1b[1;37m#" + JOURNEYTITLE.center(153) + "#\x1b[0m")
print("\x1b[0;48;5;240m\x1b[1;37m"+"#"*155+"\x1b[0m")

for ID in t.Days :
    DAYDISTANCE =0.00
    DAYENERGY =0.00
    DAYTIME =0.00
    print("|" + " "*153 + "|")
    print(f'|\x1b[0;36;44m Day \x1b[1m[{ID}] \x1b[1;32;44m {t.DayName[ID]} \x1b[0;36;44m',end="")
    print(" "*(143-len(ID)-len(t.DayName[ID])) +"\x1b[0m|")
    print("|                                    TRIP                                       ||       BATTERY        ||           DAY         ||         JOURNEY       |")
    print("\x1b[1m|T|Trip Item                | alti |  km   | spd |  kW  |   %   |  kWh  |   h   ||  kWh |   %   |   km  ||   km   |  kWh  |   h  ||   km   |  kWh  |   h  |\x1b[0m")
    if t.InitCharge[ID].isdecimal() :
        REMAININGCHARGE = 0.01 * int(t.InitCharge[ID]) * c.BattCapacity
        PRINTPERC = float(t.InitCharge[ID])
    else :
        PRINTPERC = 100.0 * REMAININGCHARGE / c.BattCapacity
    PRINTDIST = 100.0 * REMAININGCHARGE / c.AvgConsumption
    prettyPrintSeparator()
    print(f"\x1b[0;36m|S|--- START ---            | {t.Alti[ID].rjust(4)} |       |     |      |       |       |       || ",end="")
    print(str(round(REMAININGCHARGE,1)).rjust(4), end=" |")
    print(SOC2ANS(PRINTPERC)+" "+str(round(PRINTPERC,1)).rjust(5), end=" \x1b[0m\x1b[0;36m| ")
    print(str(round(PRINTDIST,1)).rjust(5), end=" || ")
    print(str(round(DAYDISTANCE,1)).rjust(6), end=" | ")
    print(str(round(DAYENERGY,1)).rjust(5), end=" | ")
    print(str(round(DAYTIME,1)).rjust(4), end=" || ")
    print(str(round(JOURNEYDISTANCE,1)).rjust(6), end=" | ")
    print(str(round(JOURNEYENERGY,1)).rjust(5), end=" | ")
    print(str(round(JOURNEYTIME,1)).rjust(4), end=" |\x1b[0m\n")
    #prettyPrintSeparator()

    for xx in t.Events[ID] :
        REMAININGCHARGE, DAYDISTANCE, DAYENERGY, DAYTIME, JOURNEYDISTANCE, JOURNEYENERGY, JOURNEYTIME =xx.prettyPrint(REMAININGCHARGE, DAYDISTANCE, DAYENERGY, DAYTIME, JOURNEYDISTANCE, JOURNEYENERGY, JOURNEYTIME)
    prettyPrintSeparator()

print(f"\n * TOTAL TRAVELLING TIME : {str(round(t.TotTripTime,2)).rjust(5)} hrs  ({round(100.0*t.TotTripTime/JOURNEYTIME,1)}%)")
print(f" * TOTAL CHARGING TIME   : {str(round(t.TotChrgTime,2)).rjust(5)} hrs  ({round(100.0*t.TotChrgTime/JOURNEYTIME,1)}%)")
print(f" * AVERAGE SPEED         : {str(round(JOURNEYDISTANCE/JOURNEYTIME,1)).rjust(5)} km/h")
print(f" * AVERAGE CONSUMPTION   : {round(100.0*JOURNEYENERGY/JOURNEYDISTANCE,2)} kWh/100km\n")

