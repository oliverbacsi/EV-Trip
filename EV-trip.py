#!/usr/bin/env python3

###############################
# EV Trip details calculator
#

import sys, re, os, math

SimpleMode  :bool =False ; # Whether the output should be a simplified table
ImportMode  :str ="trip" ; # The other possibility is "gpx"
VerboseMode :bool =False ; # Whether each GPX point should be displayed
LastSeenElev :float =0.0 ; # Last seen valid elevation, in case it is not specified for a point
LastSeenLati :float =-1000.0 ; # Last seen Latitude, useful for GPX mode so that the first GPX point of the file is already calculated
LastSeenLong :float =-1000.0 ; # Last seen Longitude, useful for GPX mode so that the first GPX point of the file is already calculated


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
        self.StartTime :dict =dict(())

        # Cumulative variables
        self.JOURNEYDISTANCE :float =0.00
        self.JOURNEYENERGY :float =0.00
        self.JOURNEYTIME :float =0.00
        self.DAYDISTANCE :float =0.00
        self.DAYENERGY :float =0.00
        self.DAYTIME :float =0.00
        self.REMAININGCHARGE :float =0.00

        # Last displayed cumulative variables (for non-verbose gpx mode)
        self.SHOWNJOURNEYDISTANCE :float =0.00
        self.SHOWNJOURNEYENERGY :float =0.00
        self.SHOWNJOURNEYTIME :float =0.00
        self.SHOWNDAYDISTANCE :float =0.00
        self.SHOWNDAYENERGY :float =0.00
        self.SHOWNDAYTIME :float =0.00
        self.SHOWNREMAININGCHARGE :float =0.00

        # For waypoint displaying purposes with multiplicant of 5%
        # List of lists. Each sub-list is Lat,Lon,Ele,Tag
        self.WayPointList :list = list(())
        # List of percentages already shown for one subsegment
        # Should be cleared with each charging (as same percentage can appear)
        # Or at each new day, as a new day can be a recharge
        # If no recharge at the day change, then no difference anyway
        self.WptedPercentages :set = set(())
        # This is to add a "charge segment" letter prefix before the percentage
        # to avoid appearing "35%" two times and not knowing which one is which,
        # this makes it to "A35%" and "B35%" so it is clear which charging
        # Any charging activity or a new day that is not "prev" will increase this.
        self.ChargeSegment :int =64 ; # 65 is letter 'A', but the very first day init will incr it by 1

        # [TEST MODE !!!] Feature : Mark all coordinates that are multiplicant of 0.1 degree
        self.LatSup :float = -1000.0
        self.LatInf :float = 1000.0
        self.LonSup :float = -1000.0
        self.LonInf :float = 1000.0

    def addTripTime(self, ti :float) :
        self.TotTripTime = self.TotTripTime + ti

    def addChrgTime(self, ti :float) :
        self.TotChrgTime = self.TotChrgTime + ti

    def syncShownValues(self) -> None :
        self.SHOWNJOURNEYDISTANCE = self.JOURNEYDISTANCE
        self.SHOWNJOURNEYENERGY   = self.JOURNEYENERGY
        self.SHOWNJOURNEYTIME     = self.JOURNEYTIME
        self.SHOWNDAYDISTANCE     = self.DAYDISTANCE
        self.SHOWNDAYENERGY       = self.DAYENERGY
        self.SHOWNDAYTIME         = self.DAYTIME
        self.SHOWNREMAININGCHARGE = self.REMAININGCHARGE

    def addDay(self, da :str) :
        self.Days.append(da)
        self.InitCharge[da] = "error"
        self.DayName[da] = "error"
        self.Events[da] = list(())
        self.Alti[da] = "-1000"
        self.StartTime[da] = 0



class CAR :
    # Object to store default car properties /trip mode/

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
        m1 = re.match("^([0-9]+[.]?[0-9]*)kWh$",parStr)
        m2 = re.match("^([0-9]+[.]?[0-9]*)kWh/100$",parStr)
        m3 = re.match("^([0-9]+[.]?[0-9]*)/([0-9]+[.]?[0-9]*)kW$",parStr)
        m4 = re.match("^([0-9]+[.]?[0-9]*)km/h$",parStr)

        if m1 : self.BattCapacity = float(m1[1])
        if m2 : self.AvgConsumption = float(m2[1])
        if m4 : self.AvgSpeed = float(m4[1])
        if m3 :
            self.AvgMotPower = float(m3[1])
            self.AvgChgPower = float(m3[2])



class CAR2 :
    # Object to store default car properties /GPX mode/

    def __init__(self, cName :str) :
        """Initialize the Car object
        :param cName : Car name as str"""
        self.Name :str =cName
        # Battery Pack Capacity in kWh
        self.BattCapacity :float =0.0
        # Default average charging power in kW
        self.AvgChgPower :float =3.6
        # Motor powers at -20%,-10%,0,+10%,+20%
        self.Power :list = [4.0, 5.0, 6.0, 8.0, 10.0]
        # Cruising speeds at -20%,-10%,0,+10%,+20%
        self.Speed :list = [80, 70, 60, 45, 30]
        # For compatibility reasons, but recalculated anyway:
        self.AvgMotPower :float =6.0
        self.AvgSpeed :float =60.0
        self.AvgConsumption :float =0.0

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the car"""
        m1 = re.match("^([0-9]+[.]?[0-9]*)kWh$",parStr)
        m3 = re.match("^([0-9/.]+)kW$",parStr)
        m4 = re.match("^([0-9/.]+)km/h$",parStr)

        if m1 : self.BattCapacity = float(m1[1])
        if m4 :
            parList = parStr.strip()[:-4].split("/")
            if len(parList) == 5 :
                self.Speed = []
                for spd in parList : self.Speed.append(float(spd))
            self.calcAvgCons()
        if m3 :
            parList = parStr.strip()[:-2].split("/")
            if len(parList) == 5 :
                self.Power = []
                for pwr in parList : self.Power.append(float(pwr))
            elif len(parList) == 1 :
                self.AvgChgPower = float(parList[0])
            self.calcAvgCons()

    def calcAvgCons(self) -> None :
        """Recalculate average consumption if new power or speed received"""
        self.AvgSpeed = float(self.Speed[2])
        self.AvgMotPower = float(self.Power[2])
        self.AvgConsumption = 100.0 * self.AvgMotPower / self.AvgSpeed



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
        # Am I the last member of a track segment? (helps to determine if print or not)
        self.LastMember :bool =False
        # Store Lat-Lon-Ele for the purpose to be able to create a waypoint
        # in case this etap has an end energy of multiplicant of 5%
        # Theoretically should be unused if not in GPX mode
        self.WptCoords :list = list(())

        # Calculated data
        self.UsedPercent :float =0.0
        self.UsedEnergy  :float =0.0
        self.Time        :float =0.0

    def youAreLast(self) :
        self.LastMember = True

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the etap"""
        m1 = re.match("^([0-9]+[.]?[0-9]*)km$",parStr)
        m2 = re.match("^([0-9]+[.]?[0-9]*)kW$",parStr)
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

    def prettyPrint(self, fh) -> None :
        """Pretty print one row of data based on incoming information,
        as well as if VerboseMode and whether we are the last point
        """
        global SimpleMode, LastSeenElev, VerboseMode, LastSeenLati, LastSeenLong, ImportMode

        JournDist :float = t.JOURNEYDISTANCE + self.Len
        JournEngy :float = t.JOURNEYENERGY + self.UsedEnergy
        JournTime :float = t.JOURNEYTIME + self.Time
        DDist     :float = t.DAYDISTANCE + self.Len
        DEngy     :float = t.DAYENERGY + self.UsedEnergy
        DTime     :float = t.DAYTIME + self.Time

        EndEnergy  :float = t.REMAININGCHARGE - self.UsedEnergy
        EndPercent :float = 100.00 * EndEnergy / c.BattCapacity
        EndRange   :float = 100.00 * EndEnergy / c.AvgConsumption

        # Theoretically these two variables are only used during GPX import,
        # so touching them won't fuck up anything.
        # So during prettyprint we can use them to memorize last coord
        # to use them to generate a new wpt upon charging...
        if ImportMode == "gpx" :
            LastSeenLati = self.WptCoords[0]
            LastSeenLong = self.WptCoords[1]

        # If it's a new 5%-rounded percentage, store the coords of a waypoint
        By5Perc :int = 5 * math.ceil(EndPercent/5.0)
        if By5Perc not in t.WptedPercentages :
            t.WptedPercentages.add(By5Perc)
            wpt :list = self.WptCoords
            wpt.append(chr(t.ChargeSegment)+str(By5Perc)+"%")
            t.WayPointList.append(wpt)

        Inclination :float = 0.0
        if LastSeenElev > -999.0 :
            try :
                Inclination = 0.1 * (self.EndAltitude-LastSeenElev) / self.Len
            except ZeroDivisionError :
                Inclination = 0.0
        if abs(Inclination) > 30.0 : Inclination = 0.0

        # Only print anything on the screen if either verbose mode or I am the last member
        if VerboseMode :
            print("\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185mE\x1b[0m|",end="")
            if re.match("^R:.*",self.Name,re.I) :
                print("\x1b[1;33;41mR:",end="")
                print(f"\x1b[1;48;5;58m\x1b[1;38;5;185m{self.Name[2:25].ljust(23)}",end="")
            else :
                print(f"\x1b[1;48;5;58m\x1b[1;38;5;185m{self.Name[0:25].ljust(25)}",end="")
            print("\x1b[0m|"+HEI2ANS(self.EndAltitude)+" "+str(self.EndAltitude).rjust(4),end=" \x1b[0m")
            IncStr :str = "-" if Inclination < 0.0 else "+"
            IncStr += str(round(abs(Inclination),1)).rjust(4)
            IncStr += "%"
            print("\x1b[0m|"+INC2ANS(Inclination)+IncStr,end="\x1b[0m")
            if SimpleMode :
                print("| "+str(round(DDist, 1)).rjust(6), end=" | ")
                print(str(round(DTime, 1)).rjust(4), end=" |")
                print(SOC2ANS(EndPercent) +" "+ str(round(EndPercent, 1)).rjust(5), end=" \x1b[0m|\n")
            else :
                print("| \x1b[1;33m"+str(round(self.Len,1)).rjust(5),end="\x1b[0m | ")
                print(str(int(self.Spd)).rjust(3),end=" |-")
                print(str(round(self.Pwr,1)).rjust(4),end=" |")
                print("\x1b[1;38;5;131m -"+str(round(self.UsedPercent,1)).rjust(4),end=" \x1b[0m|")
                print("\x1b[1;38;5;131m -"+str(round(self.UsedEnergy,1)).rjust(4),end=" \x1b[0m| ")
                print(str(round(self.Time,2)).rjust(5),end=" || ")
                print(str(round(EndEnergy,1)).rjust(4),end=" |")
                print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
                print(str(round(EndRange,1)).rjust(5),end=" || ")
                print(str(round(DDist,1)).rjust(6),end=" | ")
                print(str(round(DEngy,1)).rjust(5),end=" | ")
                print(str(round(DTime,1)).rjust(4),end=" || ")
                print(str(round(JournDist,1)).rjust(6),end=" | ")
                print(str(round(JournEngy,1)).rjust(5),end=" | ")
                print(str(round(JournTime,1)).rjust(4)+" |")
        elif self.LastMember :
            print("\x1b[0m|\x1b[1;48;5;58m\x1b[1;38;5;185mE\x1b[0m|",end="")
            _snm = self.Name
            _sid = _snm.rfind("-")
            if _sid > -1 : _snm = _snm[0:_sid]
            if re.match("^R:.*",_snm,re.I) :
                print("\x1b[1;33;41mR:",end="")
                print(f"\x1b[1;48;5;58m\x1b[1;38;5;185m{_snm[2:25].ljust(23)}",end="")
            else :
                print(f"\x1b[1;48;5;58m\x1b[1;38;5;185m{_snm[0:25].ljust(25)}",end="")
            print("\x1b[0m|"+HEI2ANS(self.EndAltitude)+" "+str(self.EndAltitude).rjust(4),end=" \x1b[0m|      ")
            if SimpleMode :
                print("| "+str(round(DDist, 1)).rjust(6), end=" | ")
                print(str(round(DTime, 1)).rjust(4), end=" |")
                print(SOC2ANS(EndPercent) +" "+ str(round(EndPercent, 1)).rjust(5), end=" \x1b[0m|\n")
            else :
                print("| \x1b[1;33m"+str(round(DDist-t.SHOWNDAYDISTANCE,1)).rjust(5),end="\x1b[0m | ")
                print(str(int((DDist-t.SHOWNDAYDISTANCE)/(DTime-t.SHOWNDAYTIME))).rjust(3),end=" |-")
                print(str(round((t.SHOWNREMAININGCHARGE-EndEnergy)/(DTime-t.SHOWNDAYTIME),1)).rjust(4),end=" |")
                print("\x1b[1;38;5;131m -"+str(round(100.0*(t.SHOWNREMAININGCHARGE-EndEnergy)/c.BattCapacity,1)).rjust(4),end=" \x1b[0m|")
                print("\x1b[1;38;5;131m -"+str(round(t.SHOWNREMAININGCHARGE-EndEnergy,1)).rjust(4),end=" \x1b[0m| ")
                print(str(round(DTime-t.SHOWNDAYTIME,2)).rjust(5),end=" || ")
                print(str(round(EndEnergy,1)).rjust(4),end=" |")
                print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
                print(str(round(EndRange,1)).rjust(5),end=" || ")
                print(str(round(DDist,1)).rjust(6),end=" | ")
                print(str(round(DEngy,1)).rjust(5),end=" | ")
                print(str(round(DTime,1)).rjust(4),end=" || ")
                print(str(round(JournDist,1)).rjust(6),end=" | ")
                print(str(round(JournEngy,1)).rjust(5),end=" | ")
                print(str(round(JournTime,1)).rjust(4)+" |")
            fh.write(f"\t\t\t\t<TR><TD bgcolor=\"lemonchiffon\">etap</TD><TD bgcolor=\"lemonchiffon\">{_snm}</TD><TD>{self.EndAltitude}</TD><TD>{round(JournDist,1)}</TD><TD>{round(JournTime,1)}</TD><TD>{round(EndPercent,1)}</TD>"+"<TD>&nbsp;</TD>"*5+"</TR>\n")

        t.JOURNEYDISTANCE = JournDist
        t.JOURNEYENERGY   = JournEngy
        t.JOURNEYTIME     = JournTime
        t.DAYDISTANCE     = DDist
        t.DAYENERGY       = DEngy
        t.DAYTIME         = DTime
        t.REMAININGCHARGE = EndEnergy
        if self.LastMember : t.syncShownValues()

        t.addTripTime(self.AddTotTripTime)
        LastSeenElev = self.EndAltitude



class CHARGE :
    # Object to store the properties of a charge

    def __init__(self, cName :str) :
        """Initialize the Charge object
        :param cName : The textual name of the charging as str"""
        self.Name :str = cName
        # This informs the recalc() method what to calculate the missing parameters from:
        #   "hrs" means that the charging time was specified last, so percentage comes from it
        #   "perc" means that percentage was specified last, so the time comes from it
        #   "full" means to charge up to 100%, and calculate what it takes
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
        m1 = re.match("^([0-9]+[.]?[0-9]*)hrs?$",parStr)
        m2 = re.match("^([0-9]+[.]?[0-9]*)kW$",parStr)
        m3 = re.match("^([0-9]+)[%]$",parStr)
        m4 = re.match("full",parStr,re.I)

        if m1 :
            self.Time = float(m1[1])
            self.CalcFrom = "hrs"
        if m2 : self.Pwr = float(m2[1])
        if m3 :
            self.ChargedPercent = float(m3[1])
            self.CalcFrom = "perc"
        if m4 :
            self.ChargedPercent = 0.0
            self.CalcFrom = "full"

    def recalc(self) :
        """Recalculate the required parameters"""
        if self.CalcFrom == "full" :
            self.ChargedEnergy = 0.0
        elif self.CalcFrom == "perc" :
            self.ChargedEnergy = 0.01 * self.ChargedPercent * c.BattCapacity
            self.Time = self.ChargedEnergy / self.Pwr
        else :
            self.ChargedEnergy = 1.00 * self.Pwr * self.Time
            self.ChargedPercent = 100.00 * self.ChargedEnergy / c.BattCapacity
        self.ChargedRange = 100.00 * self.ChargedEnergy / c.AvgConsumption
        self.ChargingSpeed = 100.00 * self.Pwr / c.AvgConsumption
        # Now we have the time to be added
        self.AddTotChrgTime = self.Time

    def prettyPrint(self, fh) -> None :
        """Pretty print one row of data based on incoming information"""
        global SimpleMode, LastSeenElev, LastSeenLati, LastSeenLong

        EndEnergy :float = t.REMAININGCHARGE
        EndRange  :float = 100.00 * EndEnergy / c.AvgConsumption
        # This is the only point where we know how much energy is exactly needed
        # if we want to charge until full, so let's invoke the recalculation once more.
        if self.CalcFrom == "full" :
            self.CalcFrom = "perc"
            self.ChargedPercent = (c.BattCapacity - EndEnergy) *100.0 / c.BattCapacity
            self.recalc()
            self.CalcFrom = "full"
            EndEnergy = c.BattCapacity
            EndPercent :float = 100.00
        else :
            EndEnergy += self.ChargedEnergy
            EndPercent :float = 100.00 * EndEnergy / c.BattCapacity
        # End conditional recalculation
        EndRange = 100.00 * EndEnergy / c.AvgConsumption
        t.JOURNEYTIME += self.Time
        t.DAYTIME     += self.Time
        t.WptedPercentages = set(())
        prettyPrintSeparator()
        print("\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44mC\x1b[0m|\x1b[1;48;5;23m\x1b[1;38;5;44m"+self.Name[0:25].ljust(25),end="\x1b[0m|")
        print(HEI2ANS(LastSeenElev)+" "+str(LastSeenElev).rjust(4),end=" \x1b[0m|")
        print(" "*6,end="|")
        if SimpleMode :
            print(" "+str(round(t.DAYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.DAYTIME,1)).rjust(4),end=" |")
            print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m|\n")
        else :
            print("\""+str(round(self.ChargedRange,1)).rjust(5),end="\x1b[0m\"|\"")
            print(str(int(self.ChargingSpeed)).rjust(3),end="\"|+")
            print(str(round(self.Pwr,1)).rjust(4),end=" |")
            print("\x1b[1;38;5;47m +"+str(round(self.ChargedPercent,1)).rjust(4),end=" \x1b[0m|")
            print("\x1b[1;38;5;47m +"+str(round(self.ChargedEnergy,1)).rjust(4),end=" \x1b[0m| \x1b[1;33m")
            print(str(round(self.Time,2)).rjust(5),end="\x1b[0m || ")
            print(str(round(EndEnergy,1)).rjust(4),end=" |")
            print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
            print(str(round(EndRange,1)).rjust(5),end=" || ")
            print(str(round(t.DAYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.DAYENERGY,1)).rjust(5),end=" | ")
            print(str(round(t.DAYTIME,1)).rjust(4),end=" || ")
            print(str(round(t.JOURNEYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.JOURNEYENERGY,1)).rjust(5),end=" | ")
            print(str(round(t.JOURNEYTIME,1)).rjust(4)+" |")

        fh.write(f"\t\t\t\t<TR><TD bgcolor=\"lightcyan\">chrg</TD><TD bgcolor=\"lightcyan\">{self.Name}</TD><TD>{LastSeenElev}</TD><TD>{round(t.JOURNEYDISTANCE,1)}</TD><TD>{round(t.JOURNEYTIME,1)}</TD><TD>{round(EndPercent,1)}</TD>"+"<TD>&nbsp;</TD>"*5+"</TR>\n")

        t.REMAININGCHARGE = EndEnergy
        t.syncShownValues()
        t.addChrgTime(self.AddTotChrgTime)
        t.ChargeSegment += 1
        if t.ChargeSegment > 90 : t.ChargeSegment = 65
        By5Perc :int = math.ceil(EndPercent)
        t.WptedPercentages.add(By5Perc)
        # Right after charging we show the exact percentage, rather than the
        # rounded up one to 5%, but as at the next waypoint the rounded up will be
        # calculated, so let's disable the display of that point by adding the
        # rounded percentage also to the 'shown' list.
        # It would look stupid that at the charger there is a '83%' waypoint
        # and at the next coordinate 10m further there is a '85%' waypoint
        t.WptedPercentages.add(5 * math.ceil(EndPercent/5.0))
        wpt :list = getRecentCoords()
        wpt.append(chr(t.ChargeSegment)+str(By5Perc)+"%")
        t.WayPointList.append(wpt)



class PASSIVE :
    # Object to store passively spent time
    # To be able to track sightseeing into the daily spent time

    def __init__(self, pName :str) :
        """Initialize the Passive object
        :param pName : The textual name of the passively spent time as str"""
        self.Name :str = pName
        # Passively spent Time
        self.Time :float =0.0

    def interpretParm(self, parStr :str) :
        """Try to interpret a parameter for the passive object"""
        m1 = re.match("^([0-9]+[.]?[0-9]*)hrs?$",parStr)

        if m1 :
            self.Time = float(m1[1])

    def prettyPrint(self, fh) -> None :
        """Pretty print one row of data based on incoming information"""
        global SimpleMode, LastSeenElev
        t.JOURNEYTIME += self.Time
        t.DAYTIME     += self.Time
        EndEnergy :float = t.REMAININGCHARGE
        EndPercent = 100.00 * EndEnergy / c.BattCapacity
        EndRange = 100.00 * EndEnergy / c.AvgConsumption
        PTime = str(round(self.Time,2))
        if PTime.find('.') == -1 :
            PTime = PTime+".00"
        elif PTime[-2] == "." :
            PTime = PTime+"0"
        print("\x1b[0m|\x1b[1;48;5;236m\x1b[1;38;5;252mP\x1b[0m|\x1b[1;48;5;236m\x1b[1;38;5;252m"+self.Name[0:25].ljust(25),end="\x1b[0m|")
        print(HEI2ANS(LastSeenElev)+" "+str(LastSeenElev).rjust(4),end=" \x1b[0m|")
        print(" "*6,end="|")
        if SimpleMode :
            print(" "+str(round(t.DAYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.DAYTIME,1)).rjust(4),end=" |")
            print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m|\n")
        else :
            print("   0   |   0 |  0   |   0   |   0   |",end=" \x1b[1;33m")
            print(PTime.rjust(5),end="\x1b[0m || ")
            print(str(round(EndEnergy,1)).rjust(4),end=" |")
            print(SOC2ANS(EndPercent)+" "+str(round(EndPercent,1)).rjust(5),end=" \x1b[0m| ")
            print(str(round(EndRange,1)).rjust(5),end=" || ")
            print(str(round(t.DAYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.DAYENERGY,1)).rjust(5),end=" | ")
            print(str(round(t.DAYTIME,1)).rjust(4),end=" || ")
            print(str(round(t.JOURNEYDISTANCE,1)).rjust(6),end=" | ")
            print(str(round(t.JOURNEYENERGY,1)).rjust(5),end=" | ")
            print(str(round(t.JOURNEYTIME,1)).rjust(4)+" |")

        fh.write(f"\t\t\t\t<TR><TD bgcolor=\"lightgray\">pass</TD><TD bgcolor=\"lightgray\">{self.Name}</TD><TD>{LastSeenElev}</TD><TD>{round(t.JOURNEYDISTANCE,1)}</TD><TD>{round(t.JOURNEYTIME,1)}</TD><TD>{round(EndPercent,1)}</TD>"+"<TD>&nbsp;</TD>"*5+"</TR>\n")

        t.syncShownValues()



#################### PROC PART ####################


def geo_distance(Lat1 :float, Lon1 :float, Lat2 :float, Lon2 :float) -> float :
    """Give the approx geographical distance between two coordinates.
    This is a simplified formla of the FCC calculation method.
    Formula taken from the Wikipedia page.
    Parameters:
    :param Lat1,Lon1 : First point coordinates in degrees, Positive is North and East
    :param Lat2,Lon3 : Second point coordinates in degrees
    :returns: Distance in kilometers as float"""

    # Medium Latitude in Radians
    Latm_Rad :float = (Lat1+Lat2)*math.pi/360.0
    # FCC Formula parameters, providing an approx ratio between Degrees and Kilometers, considering Earth's curvature
    K1 :float = 111.13209                    - 0.56605*math.cos(2.0*Latm_Rad) + 0.00120*math.cos(4.0*Latm_Rad)
    K2 :float = 111.41513*math.cos(Latm_Rad) - 0.09455*math.cos(3.0*Latm_Rad) + 0.00012*math.cos(5.0*Latm_Rad)

    # The differences in degrees are simply multiplied by these ratio numbers for an approx value
    # then the distance comes out from the Pythagorean formula.
    return math.sqrt(  (K1*(Lat2-Lat1))**2  +  (K2*(Lon2-Lon1))**2  )


def get_extrapol(_p :float, _v :list) -> float :
    """Get extrapolated (interpolated) value for a given slope percentage,
    considering a value vector for variables.
    Parameters:
    :param _p : actual slope percentage as float, negative is down
    :param _v : value vector at -20,-10,0,+10,+20 percent
    :returns : Extrapol/Interpol value as float"""
    if _p <= -10 :
        return 0.10*(_v[1]-_v[0]) * (_p+20.00) + _v[0]
    elif _p <= 0 :
        return 0.10*(_v[2]-_v[1]) * (_p+10.00) + _v[1]
    elif _p <= 10 :
        return 0.10*(_v[3]-_v[2]) * _p + _v[2]
    else :
        return 0.10*(_v[4]-_v[3]) * (_p-10.00) + _v[3]


def loadGPXFile(_fld :str, _fnm :str, _rev :bool, _efh) -> list :
    """Load a GPX file and convert elements into a list of lists"""
    global LastSeenElev, LastSeenLati, LastSeenLong

    try :
        fg = open(os.path.join(_fld,_fnm),"r")
    except :
        print(f"*** referred GPX file not found: {_fld}/{_fnm} : Output will be corrupted")
        return list(())

    _currElev :float = LastSeenElev
    _currLat  :float =-1000.0
    _currLon  :float =-1000.0
    _lastName :str ="error! no name in gpx file!"
    _segIdx   :int =0
    _pntIdx   :int =0
    _eleValid :bool =False
    _pntValid :bool =False
    _retList  :list =list(())
    _tempList :list =list(())
    # To be able to determine the first elevation of the day,
    # both sides to be remembered and one end to be returned,
    # based on whether it is reversed or not
    _veryFirstElev :float =-1000.0
    _veryLastElev  :float =-1000.0

    for gsor in fg :
        gsor = gsor.strip()
        if not len(gsor) : continue
        ma = re.match("^.*<name>(.*)</name>.*$", gsor, re.I)
        mb = re.match("^.*<trkseg>.*$", gsor, re.I)
        mc = re.match('.*<trkpt lat="([0-9.]+)" lon="([0-9.]+)">.*', gsor, re.I)
        md = re.match('.*<ele>([0-9.]+)</ele>.*', gsor, re.I)
        me = re.match('.*</trkpt>.*', gsor, re.I)
        if ma : _lastName = ma[1]
        if mb : _segIdx += 1
        if mc :
            _pntIdx += 1
            _currLat = float(mc[1])
            _currLon = float(mc[2])
            _pntValid = True
            _eleValid = False
        if md :
            if _pntValid :
                _currElev = float(md[1])
                _eleValid = True
                if _veryFirstElev < -999.0 : _veryFirstElev = _currElev
                _veryLastElev = _currElev
            else :
                _eleValid = False
        if me :
            if _eleValid :
                _itm = list((_currLat,_currLon,_currElev,_lastName+f"-{_segIdx}-{_pntIdx}"))
            else :
                _itm = list((_currLat,_currLon,-1000.0,_lastName+f"-{_segIdx}-{_pntIdx}"))
            _tempList.append(_itm)
            _pntValid = False
            _eleValid = False
            # Collecting the Supremum/Infimum coordinates
            t.LatSup = max(t.LatSup,_currLat)
            t.LatInf = min(t.LatInf,_currLat)
            t.LonSup = max(t.LonSup,_currLon)
            t.LonInf = min(t.LonInf,_currLon)

    fg.close()
    if _rev : _tempList.reverse()

    for _itm in _tempList :
        _currLat = _itm[0]
        _currLon = _itm[1]
        _currElev = _itm[2] if _itm[2] > -999.0 else LastSeenElev
        _lastName = _itm[3]

        # This is a good point to export the merged GPX file
        _efh.write(f'\t\t\t<trkpt lat="{_currLat}" lon="{_currLon}">\n')
        _efh.write(f'\t\t\t\t<ele>{_currElev}</ele>\n')
        _efh.write('\t\t\t</trkpt>\n')

        if LastSeenLati > -999.0 :
            __len = geo_distance(LastSeenLati, LastSeenLong, _currLat, _currLon)
            if __len < 0.001 : continue
            __prc = 0.1 * (_currElev-LastSeenElev)/__len
            __pwr = get_extrapol(__prc, c.Power)
            __spd = get_extrapol(__prc, c.Speed)
            _ita = list((__len, _currElev, __pwr, __spd, _lastName, _currLat, _currLon, _currElev))
            _retList.append(_ita)

        LastSeenLati = _currLat
        LastSeenLong = _currLon
        LastSeenElev = _currElev

    if _rev : return [_veryLastElev] + _retList
    return [_veryFirstElev] + _retList


def prettyPrintSeparator() -> None :
    """Print a separator line in the output table"""
    global SimpleMode
    print("+",end="")
    if SimpleMode :
        for i in [1, 25, 6, 6, 8, 6, 7]: print("-" * i, end="+")
    else :
        for i in [1, 25, 6, 6, 7, 5, 6, 7, 7, 7, 0, 6, 7, 7, 0, 8, 7, 6, 0, 8, 7, 6] : print("-"*i, end="+")
    print("")


def SOC2ANS(_perc :float ="-1.0") -> str:
    """Return the ANSI color of a Battery State of Charge
    :param _perc : State of charge in percentage as float
    :return : Perfectly formatted ANSI escape sequence string"""

    if _perc >= 100.0: return '\x1b[1;48;5;75m\x1b[1;38;5;195m'
    if _perc >= 95.0 : return '\x1b[1;48;5;68m\x1b[1;38;5;152m'
    if _perc >= 90.0 : return '\x1b[1;48;5;32m\x1b[1;38;5;117m'
    if _perc >= 85.0 : return '\x1b[1;48;5;25m\x1b[1;38;5;75m'
    if _perc >= 80.0 : return '\x1b[1;48;5;21m\x1b[1;38;5;39m'
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


def HEI2ANS(_alti :float ="-1.0") -> str:
    """Return the ANSI color of an Elevation Above Sea Level
    :param _alti : Elevation above sea level in meters as float
    :return : Perfectly formatted ANSI escape sequence string"""

    if _alti >= 1500.0 : return '\x1b[0;48;5;200m\x1b[1;38;5;16m'
    if _alti >= 1000.0 : return '\x1b[0;48;5;162m\x1b[1;38;5;16m'
    if _alti >=  800.0 : return '\x1b[0;48;5;160m\x1b[1;38;5;16m'
    if _alti >=  600.0 : return '\x1b[0;48;5;166m\x1b[1;38;5;16m'
    if _alti >=  500.0 : return '\x1b[0;48;5;172m\x1b[1;38;5;16m'
    if _alti >=  400.0 : return '\x1b[0;48;5;178m\x1b[1;38;5;16m'
    if _alti >=  350.0 : return '\x1b[0;48;5;142m\x1b[1;38;5;16m'
    if _alti >=  300.0 : return '\x1b[0;48;5;106m\x1b[1;38;5;16m'
    if _alti >=  250.0 : return '\x1b[0;48;5;70m\x1b[1;38;5;16m'
    if _alti >=  200.0 : return '\x1b[0;48;5;34m\x1b[1;38;5;16m'
    if _alti >=  150.0 : return '\x1b[0;48;5;28m\x1b[1;38;5;16m'
    if _alti >=  100.0 : return '\x1b[0;48;5;22m\x1b[1;38;5;16m'
    if _alti >=   50.0 : return '\x1b[0;48;5;23m\x1b[1;38;5;16m'
    if _alti >=    0.0 : return '\x1b[0;48;5;17m\x1b[37m'
    return '\x1b[0;48;5;53m\x1b[37m'


def INC2ANS(_prc :float =0.0) -> str:
    """Return the ANSI color of an Inclination percentage
    :param _prc : Inclination value in percentage (meters per 100m)
    :return : Perfectly formatted ANSI escape sequence string"""
    if _prc >=20.0 : return '\x1b[0;38;5;213m'
    if _prc >=18.0 : return '\x1b[0;38;5;207m'
    if _prc >=16.0 : return '\x1b[0;38;5;200m'
    if _prc >=14.0 : return '\x1b[0;38;5;199m'
    if _prc >=12.0 : return '\x1b[0;38;5;198m'
    if _prc >=10.0 : return '\x1b[0;38;5;197m'
    if _prc >= 8.0 : return '\x1b[0;38;5;196m'
    if _prc >= 6.0 : return '\x1b[0;38;5;160m'
    if _prc >= 4.0 : return '\x1b[0;38;5;167m'
    if _prc >= 2.0 : return '\x1b[0;38;5;174m'
    if _prc > 0.01 : return '\x1b[0;38;5;181m'

    if _prc <=-20.0 : return '\x1b[0;38;5;33m'
    if _prc <=-18.0 : return '\x1b[0;38;5;38m'
    if _prc <=-16.0 : return '\x1b[0;38;5;43m'
    if _prc <=-14.0 : return '\x1b[0;38;5;49m'
    if _prc <=-12.0 : return '\x1b[0;38;5;48m'
    if _prc <=-10.0 : return '\x1b[0;38;5;47m'
    if _prc <= -8.0 : return '\x1b[0;38;5;46m'
    if _prc <= -6.0 : return '\x1b[0;38;5;40m'
    if _prc <= -4.0 : return '\x1b[0;38;5;77m'
    if _prc <= -2.0 : return '\x1b[0;38;5;114m'
    if _prc < -0.01 : return '\x1b[0;38;5;151m'

    return "\x1b[0;38;5;250m"


def getRecentCoords() -> list :
    global LastSeenLati, LastSeenLong, LastSeenElev
    ret :list = [LastSeenLati, LastSeenLong, LastSeenElev]
    return ret


#################### MAIN PART ####################


# Interpret command line arguments:
if len(sys.argv) < 2 :
    print(f"Usage : {sys.argv[0]} [-v] [-s] <Trip file name>")
    print("  -s : Simple mode : Only a few essential columns are displayed in the output.")
    print("  -v : Verbose mode : In case of GPX mode: each point is displayed, not just track segments.")
    print("  <Trip file name> : Input file name to read, the extension will determine the input mode.")
    exit(-1)

ParamList = sys.argv[1:]
while re.match("^-.*",ParamList[0]) :
    if ParamList[0].lower() == "-v" :
        VerboseMode = True
        ParamList.pop(0)
    elif ParamList[0].lower() == "-s" :
        SimpleMode = True
        ParamList.pop(0)

InFName :str = ParamList[0]
if not re.match("(\\./)?trips/.*",InFName) : InFName = os.path.join("trips",InFName)

try :
    fin = open(InFName, "r")
except :
    print(f"Could not open input file: {InFName}")
    exit(-2)

# Import the trip file
if os.path.splitext(InFName)[1].lower() == ".cfg" : ImportMode = "gpx"
LineNumber :int =0
DayIsActive :bool =False
ID :str ="error"

if ImportMode == "trip" :

    VerboseMode = True ; # If not gpx, then each point counts !
    for sor in fin :
        LineNumber += 1

        sor = sor.strip()
        if not len(sor) : continue
        if re.match("^#.*$", sor) : continue

        m0 = re.match("^TRIP +(.*)$", sor, re.I)
        if m0 :
            t = TRIP(str(m0[1]).strip())
            continue

        m1 = re.match("^CAR +(.*) +[|] (.*)$", sor, re.I)
        if m1 :
            c = CAR(m1[1].strip())
            for _par in m1[2].split(" ") : c.interpretParm(_par)
            continue

        m2 = re.match("^DAY +(.+) +([0-9]+)[%] +([0-9]+)m +[|] +(.*)$", sor, re.I)
        m3 = re.match("^DAY +(.+) +(prev) +([0-9]+)m +[|] +(.*)$", sor, re.I)
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

        m1 = re.match("^ETAP +(.*) +[|] +(.*)$", sor, re.I)
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

        m1 = re.match("^CHRG +(.*) +[|] +(.*)$", sor, re.I)
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

        m1 = re.match("^PASS +(.*) +[|] +(.*)$", sor, re.I)
        if m1 :
            if not DayIsActive :
                fin.close()
                print(f"Line #{LineNumber}: PASS specified without valid DAY first")
                exit(-3)
            PaObj = PASSIVE(str(m1[2]).strip())
            for _par in m1[1].split(" ") : PaObj.interpretParm(_par)
            t.Events[ID].append(PaObj)
            continue

        print(f"Line #{LineNumber}: Not understood: <{sor}>")

# ImportMode == "gpx"
else :

    TripName = os.path.splitext(os.path.split(InFName)[-1])[0]
    fexp = open("gpxexport/"+TripName+".gpx","w")
    TripName = TripName.replace("_"," ")
    t = TRIP(TripName)
    fexp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    fexp.write('<gpx version="1.1" creator="EV-trip.py"\n')
    fexp.write(' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
    fexp.write(' xmlns="http://www.topografix.com/GPX/1/1"\n')
    fexp.write(' xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"\n>\n')
    fexp.write(f'\t<metadata>\n\t\t<name>{TripName}</name>\n\t\t<desc>{TripName}</desc>\n\t</metadata>\n')
    fexp.write(f'\t<trk>\n\t\t<name>{TripName}</name>\n\t\t<number>1</number>\n\t\t<trkseg>\n')

    for sor in fin :
        LineNumber += 1

        sor = sor.strip()
        if not len(sor) : continue
        if re.match("^#.*$", sor) : continue

        m1 = re.match("^CAR +(.*) +[|] (.*)$", sor, re.I)
        if m1 :
            c = CAR2(m1[1].strip())
            for _par in m1[2].split(" ") : c.interpretParm(_par)
            continue

        m2 = re.match("^DAY +(.+) +([0-9]+)[%] +[|] +(.*)$", sor, re.I)
        m3 = re.match("^DAY +(.+) +(prev) +[|] +(.*)$", sor, re.I)
        if m2 or m3 :
            if m2 :
                m1 = m2
            else :
                m1 = m3
            ID = str(m1[1]).strip()
            Chrg1 = str(m1[2]).strip()
            Name = str(m1[3]).strip()
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
            DayIsActive = True
            continue

        m2 = re.match("^include-fwd +(.*)$", sor, re.I)
        m3 = re.match("^include-rev +(.*)$", sor, re.I)
        m4 = re.match("^segment +(.*)$", sor, re.I)
        if m2 or m3 or m4 :
            if not DayIsActive :
                fin.close()
                print(f"Line #{LineNumber}: GPX file specified without valid DAY first")
                exit(-3)
            Reverse = True if m3 else False
            Folder = "gpxsegments" if m4 else "gpxincludes"
            if m2 :
                GpxFiName = m2[1].strip()
            elif m3 :
                GpxFiName = m3[1].strip()
            else :
                GpxFiName = m4[1].strip()
            EtList = loadGPXFile(Folder,GpxFiName+".gpx",Reverse,fexp)
            #+++ Day starting altimeter hack:
            # The 0th element of EtList is just a string containing the very first altitude data.
            # This is popped and checked if the day has already a valid altitude or not.
            # If not, this is used....
            FirstAlti = str(round(EtList.pop(0)))
            if t.Alti[ID] == "-1000" : t.Alti[ID] = FirstAlti
            #*** End Hack
            _lastName = ""
            for etap in EtList :
                if Reverse :
                    EtObj = ETAP("R:"+etap[4])
                else :
                    EtObj = ETAP(etap[4])
                EtObj.Len = etap[0]
                EtObj.EndAltitude = round(etap[1])
                EtObj.Pwr = etap[2]
                EtObj.Spd = etap[3]
                EtObj.WptCoords = etap[5:8]
                EtObj.recalc()
                # If not the first point of the whole list:
                if _lastName :
                    # Check if <trkseg> indices differ. If yes, it's a new segment,
                    # therefore the previously seen object needs to be marked as last.
                    mi1 = re.match("^.*-([0-9]+)-([0-9]+)$",_lastName)
                    mi2 = re.match("^.*-([0-9]+)-([0-9]+)$",etap[4])
                    if mi1 and mi2 :
                        if mi1[1] != mi2[1] :
                            t.Events[ID][-1].youAreLast()
                _lastName = etap[4]
                t.Events[ID].append(EtObj)
            t.Events[ID][-1].youAreLast()
            continue

        m1 = re.match("^charge +(.*) +[|] +(.*)$", sor, re.I)
        if m1 :
            if not DayIsActive :
                fin.close()
                print(f"Line #{LineNumber}: Charge specified without valid DAY first")
                exit(-3)
            ChObj = CHARGE(str(m1[2]).strip())
            for _par in m1[1].split(" ") : ChObj.interpretParm(_par)
            ChObj.recalc()
            t.Events[ID].append(ChObj)
            continue

        m1 = re.match("^passive +(.*) +[|] +(.*)$", sor, re.I)
        if m1 :
            if not DayIsActive :
                fin.close()
                print(f"Line #{LineNumber}: Passive time specified without valid DAY first")
                exit(-3)
            PaObj = PASSIVE(str(m1[2]).strip())
            for _par in m1[1].split(" ") : PaObj.interpretParm(_par)
            t.Events[ID].append(PaObj)
            continue

        print(f"Line #{LineNumber}: Not understood: <{sor}>")


fin.close()


if SimpleMode :
    Wid :int =67
    print("\n\x1b[0;48;5;240m\x1b[1;37m" + "#"*Wid+"\x1b[0m")
    print("\x1b[0;48;5;240m\x1b[1;37m#" + t.Name.center(Wid-2) + "#\x1b[0m")
    print("\x1b[0;48;5;240m\x1b[1;37m#" + f"{c.Name} /{c.BattCapacity}/".center(Wid-2) + "#\x1b[0m")
    print("\x1b[0;48;5;240m\x1b[1;37m"+"#"*Wid+"\x1b[0m")
else :
    Wid :int =162
    JOURNEYTITLE = f"{t.Name}   with  {c.Name}  /{c.BattCapacity} kWh/"
    print("\n\x1b[0;48;5;240m\x1b[1;37m" + "#"*Wid+"\x1b[0m")
    print("\x1b[0;48;5;240m\x1b[1;37m#" + JOURNEYTITLE.center(Wid-2) + "#\x1b[0m")
    print("\x1b[0;48;5;240m\x1b[1;37m"+"#"*Wid+"\x1b[0m")

# Support for HTML export for printing and parameter finetuning
HTMLName = os.path.splitext(os.path.split(InFName)[-1])[0]
fhtm = open("gpxexport/"+HTMLName+".html","w")
HTMLName = HTMLName.replace("_"," ")
fhtm.write(f"<HTML>\n\t<HEAD>\n\t\t<TITLE>{HTMLName}</TITLE>\n\t\t<META name=\"Generator\" value=\"EV-Trip\"></META>\n\t</HEAD>\n")
fhtm.write(f"\t<BODY>\n\t\t<P><H1><CENTER>{HTMLName}</CENTER></H1></P>\n\t\t<P>\n\t\t\t<TABLE border=\"1\" borderwidth=\"1\">\n")

for ID in t.Days :
    t.DAYDISTANCE =0.00
    t.DAYENERGY =0.00
    t.DAYTIME =0.00
    t.WptedPercentages = set(())
    print("|" + " "*(Wid-2) + "|")
    print(f'|\x1b[0;36;44m Day \x1b[1m[{ID}] \x1b[1;32;44m {t.DayName[ID]} \x1b[0;36;44m',end="")
    print(" "*(Wid-12-len(ID)-len(t.DayName[ID])) +"\x1b[0m|")
    fhtm.write(f"\t\t\t\t<TR><TH colspan=\"11\">[{ID}] : {t.DayName[ID]}</TH></TR>\n")
    fhtm.write("\t\t\t\t<TR>\n\t\t\t\t\t")
    for n,l in [["3","ETAP"],["3","PLAN"],["5","REAL"]] : fhtm.write(f"<TH colspan=\"{n}\">{l}</TH>")
    fhtm.write("\n\t\t\t\t</TR>\n\t\t\t\t<TR>\n\t\t\t\t\t")
    for l in ["type","NAME","alti","km","time","batt %","ODOMETER","DISTANCE","REALTIME","TIMEDIFF","BATT %"] : fhtm.write(f"<TH>{l}</TH>")
    fhtm.write("\n\t\t\t\t</TR>\n")
    if SimpleMode :
        print("\x1b[1m|T|Trip Item                | alti | incl |   km   |   h  |   %   |\x1b[0m")
    else :
        print("|                                       TRIP                                           ||       BATTERY        ||           DAY         ||         JOURNEY       |")
        print("\x1b[1m|T|Trip Item                | alti | incl |  km   | spd |  kW  |   %   |  kWh  |   h   ||  kWh |   %   |   km  ||   km   |  kWh  |   h  ||   km   |  kWh  |   h  |\x1b[0m")
    if t.InitCharge[ID].isdecimal() :
        t.REMAININGCHARGE = 0.01 * int(t.InitCharge[ID]) * c.BattCapacity
        PRINTPERC = float(t.InitCharge[ID])
        t.ChargeSegment += 1
        if t.ChargeSegment > 90 : t.ChargeSegment = 65
    else :
        PRINTPERC = 100.0 * t.REMAININGCHARGE / c.BattCapacity
    PRINTDIST = 100.0 * t.REMAININGCHARGE / c.AvgConsumption
    prettyPrintSeparator()
    if SimpleMode :
        print("\x1b[0;36m|S|--- START ---            |"+HEI2ANS(float(t.Alti[ID]))+" "+t.Alti[ID].rjust(4)+" \x1b[0m\x1b[0;36m|      | ",end="")
        print(str(round(t.DAYDISTANCE,1)).rjust(6), end=" | ")
        print(str(round(t.DAYTIME,1)).rjust(4), end=" |")
        print(SOC2ANS(PRINTPERC)+" "+str(round(PRINTPERC,1)).rjust(5), end=" \x1b[0m\x1b[0;36m|\x1b[0m\n")
    else :
        print("\x1b[0;36m|S|--- START ---            |"+HEI2ANS(float(t.Alti[ID]))+" "+t.Alti[ID].rjust(4)+" \x1b[0m\x1b[0;36m|      |       |     |      |       |       |       || ",end="")
        print(str(round(t.REMAININGCHARGE,1)).rjust(4), end=" |")
        print(SOC2ANS(PRINTPERC)+" "+str(round(PRINTPERC,1)).rjust(5), end=" \x1b[0m\x1b[0;36m| ")
        print(str(round(PRINTDIST,1)).rjust(5), end=" || ")
        print(str(round(t.DAYDISTANCE,1)).rjust(6), end=" | ")
        print(str(round(t.DAYENERGY,1)).rjust(5), end=" | ")
        print(str(round(t.DAYTIME,1)).rjust(4), end=" || ")
        print(str(round(t.JOURNEYDISTANCE,1)).rjust(6), end=" | ")
        print(str(round(t.JOURNEYENERGY,1)).rjust(5), end=" | ")
        print(str(round(t.JOURNEYTIME,1)).rjust(4), end=" |\x1b[0m\n")
    fhtm.write(f"\t\t\t\t<TR><TD bgcolor=\"beige\">strt</TD><TD bgcolor=\"beige\">--- START ---</TD><TD>{t.Alti[ID]}</TD><TD>{round(t.JOURNEYDISTANCE,1)}</TD><TD>{round(t.JOURNEYTIME,1)}</TD><TD>{str(round(PRINTPERC,1))}</TD>"+"<TD>&nbsp</TD>"*5+"</TR>\n")
    LastSeenElev = int(float(t.Alti[ID]))

    t.syncShownValues()

    for xx in t.Events[ID] : xx.prettyPrint(fhtm)
    prettyPrintSeparator()

print(f"\n * TOTAL TRAVELLING TIME   : {str(round(t.TotTripTime,2)).rjust(5)} hrs  ({round(100.0*t.TotTripTime/t.JOURNEYTIME,1)}%)")
print(f" * TOTAL CHARGING TIME     : {str(round(t.TotChrgTime,2)).rjust(5)} hrs  ({round(100.0*t.TotChrgTime/t.JOURNEYTIME,1)}%)")
print(f" * TOTAL PASSIVE TIME      : {str(round(t.JOURNEYTIME-t.TotChrgTime-t.TotTripTime,2)).rjust(5)} hrs  ({round(100.0*(t.JOURNEYTIME-t.TotChrgTime-t.TotTripTime)/t.JOURNEYTIME,1)}%)")
print(f" * AVERAGE SPEED (active)  : {str(round(t.JOURNEYDISTANCE/(t.TotChrgTime+t.TotTripTime),1)).rjust(5)} km/h")
print(f" * AVERAGE SPEED (overall) : {str(round(t.JOURNEYDISTANCE/t.JOURNEYTIME,1)).rjust(5)} km/h")
AvgCons :float = 100.0*t.JOURNEYENERGY/t.JOURNEYDISTANCE
print(f" * AVERAGE CONSUMPTION     : {str(round(AvgCons,2)).rjust(5)} kWh/100km")
print(f" * NOMINAL RANGE /JOURNEY/ : {str(round(100.0*c.BattCapacity/AvgCons,1)).rjust(5)} km\n")

# End HTML export
fhtm.write("\t\t\t</TABLE>\n\t\t</P>\n\t</BODY>\n</HTML>\n")
fhtm.close()

if ImportMode == "gpx" :
    fexp.write('\t\t</trkseg>\n\t</trk>\n')
    for wpt in t.WayPointList :
        fexp.write(f'\t<wpt lat="{wpt[0]}" lon="{wpt[1]}">\n')
        #+++ Currently try to skip to add elevation value to percentage marker waypoints
        #fexp.write(f'\t\t<ele>{wpt[2]}</ele>\n')
        #***
        fexp.write(f'\t\t<name>{wpt[3]}</name>\n\t</wpt>\n')

    # Expand the min-max coordinates to the multiplicant of 0.1
    x0 :int = math.floor(10.0*t.LonInf)
    x1 :int = math.ceil(10.0*t.LonSup)+1
    y0 :int = math.floor(10.0*t.LatInf)
    y1 :int = math.ceil(10.0*t.LatSup)+1
    # Generate all 0.1 degree coordinate intersections as waypoints
    for yy in range(y0,y1) :
        for xx in range(x0,x1) :
            fexp.write(f'\t<wpt lat="{round(yy*0.10,2)}" lon="{round(xx*0.10,2)}">\n')
            fexp.write(f'\t\t<name>{round(yy*0.1,1)}N  {round(xx*0.1,1)}E</name>\n\t</wpt>\n')

    fexp.write('</gpx>\n')
    fexp.close()
