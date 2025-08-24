EV Trip calculator
------------------

> Help to plan EV trips.
> * Calculate Battery SOC% and Trip Times based on Trip paramterers.
> * Create multi-day trip plans.

###EV-trip

This is the main program.
It supports two different input file types:

* **Trip mode**
	* This is the original one, all data is specified manually, and some pre-calculation is needed.
	* The user specifies the trip segments with length, average speed and typical power consumption, line by line.
	* It is the user's responsibility to take geographical elevations into consideration and specify a higher consumption and lower speed to have accurate calculation results.
	* In the 'trips' folder there should be regular plain text files with the extension `.trip`
	* The grammar itself is specified within the text file in the commented lines (Starting with `#`)
		* **`CAR`** _`name`_            / or /
		* **`CAR`** _`name`_ **|** _`packCapacity`_ _`defConsumption`_ _`defMotPower/defChrgPower`_ _`defSpeed`_
			* Defines the properties of the vehicle that is being used
			* _`name`_ : The single-word name of the vehicle
			* _`packCapacity`_ : Battery Pack Capacity in kWh
			* _`defConsumption`_ : Experienced default consumption in kWh/100
			* _`defMotPower/defChrgPower`_ : Default Motor Power and Default Charging Power in kW
			* _`defSpeed`_ : Default cruising speed
			* If only _`name`_ is specified, then all vehicle details must exist in the vehicle database file `Vehicles.cfg`
		* **`TRIP`** _`name`_
			* Identifies the whole road trip. A trip can contain multiple days.
			* _`name`_ : The name of the whole trip
		* **`DAY`** _`ID`_ _`startSOC`_ _`startElev`_ **|** _`descr`_
			* Specifies the start of a new day and its properties. A day can contain multiple trip etaps and chargings.
			* Any Etap or Charge or Trip segment might be only specified within a certain day, they can not be outside of day spec.
			* _`ID`_ : Any short identifier like '#1','#2',... or 'Fri','Sat','Sun',...
			* _`startSOC`_ : The starting State of Charge. Can be a percentage, like '85%' or '100%' , or if there is no charging possibility overnight , then specifying 'prev' will take the closing SoC of the previous day.
			* _`startElev`_ : The starting geographical elevation of the day. It is needed for the elevation delta of the first segment of the day.
			* _`descr`_ : Textual description of the daily trip
		* **`ETAP`** _`dist`_ _`anything...`_ **|** _`descr`_
			* Specifies an etap of the whole trip when the vehicle is in motion (distance growing, geo elevation changing, time passing, battery charge going down)
			* _`dist`_ : Distance. Length of the etap. Number, ending with 'km'
			* _`anything...`_ : Any parameter that is different from the default values. Values will be distinguished by the Unit of Measure used: ##.#km = Etap length, ##.#kW = Motor Power , ##.#km/h = Average speed, ###m = Geographical elevation at the end of the segment.
			* _`descr`_ : Textual description of the etap
		* **`CHRG`** _`SoC or Time`_ _`anything...`_ **|**  _`descr`_
			* Specifies a charging session for the battery (trip distance unchanged, geo elevation unchanged, time passing, battery charge going up)
			* _`Batt% or Time`_ : Charged energy can be defined either by Battery percentage, like '30%' means: 30% battery capacity charged (time will be calculated), OR : charging time is specified, like '1.5hrs' means charging for 1.5hrs long, (Battery percentage will be calculated). Values will be distinguished by the Unit of Measure used.
			* _`anything...`_ : Any parameter that is different from the default values. Values will be distinguished by the Unit of Measure used: ##% = Charged Batttery percentage, ##.#hrs = Charging time , ##.#kW = Charging power.
			* _`descr`_ : Textual description of the charging location
		* **`PASS`** _`time`_ **|** _`descr`_
			* Specifies passively spent time (when there is a stop in the trip but no charging possibility) (trip distance unchanged, geo elevation unchanged, time passing, battery charge unchanged)
			* _`time`_ : The passively spent time in hours.
			* _`descr`_ : Textual description of the activity performed without charging. (like 'visit castle')
* **GPX mode**
	* This is a later development, to be able to import GPX tracks or routes, read length and elevation values from the tracks.
	* A trip config file is still needed to specify vehicle basic data, list up which GPX files to import, as well as specify chargings somehow.
	* In the 'trips' folder there should be a regular plain text file with the extension `.cfg`
	* The first valid row should be the vehicle specification
		* **`CAR`** _`name`_            / or /
		* **`CAR`** _`name`_ **|** _`battCapacity`_ _`speeds-20/-10/0/+10/+20`_ _`powers-20/-10/0/+10/+20`_ _`chargingPower`_
			* Defines the properties of the vehicle
			* _`name`_ : The single-word name of the vehicle
			* _`battCapacity`_ : Battery Capacity in kWh
			* _`speeds-20/-10/0/+10/+20`_ : Travelling speeds at 20%+ slope down / 10% slope down / flat surface / 10% slope up / 20%+ slope up , ending with 'km/h' . Example: 80/60/50/40/25km/h . Intermediate values will be calculated with interpolation . 20%+ slopes are very seldom, the value for 20% will be used.
			* _`powers-20/-10/0/+10/+20`_ : Typical motor powers at 20%+ slope down / 10% slope down / flat surface / 10% slope up / 20%+ slope up , ending with 'kW' . Example: 0.2/3.0/5.0/10.0/30.0kW . Intermediate values will be calculated with interpolation . 20%+ slopes are very seldom, the value for 20% will be used.
			* _`chargingPower`_ : As the name says, the charging power of the vehicle in kW.
			* If only _`name`_ is specified, then all vehicle details must exist in the vehicle database file `Vehicles.cfg`
	* Trip name itself is taken from the file name, underscores converted to spaces
	* The day specification was also inherited from 'trip' mode as the GPX data does not contain this information, although elevation is not specified as it comes from the GPX data:
		* **`DAY`** _`ID`_ _`startSOC`_ **|** _`descr`_
			* Specifies the start of a new day and its properties. A day can contain multiple trip etaps and chargings.
			* Any Etap or Charge or Trip segment might be only specified within a certain day, they can not be outside of day spec.
			* _`ID`_ : Any short identifier like '#1','#2',... or 'Fri','Sat','Sun',...
			* _`startSOC`_ : The starting State of Charge. Can be a percentage, like '85%' or '100%' , or if there is no charging possibility overnight , then specifying 'prev' will take the closing SoC of the previous day.
			* _`descr`_ : Textual description of the daily trip
	* The GPX import rows can be either to import a frequently used standard 'include' track from the 'gpxinclude' folder. As You might want to travel either direction, so there might be a need to include it in Your trip in reverse direction as it was originally drawn.
		* **`include-fwd`** _`filename-no-extension`_ : Include a frequently used GPX track segment from the 'gpxinclude' folder into Your track. The drawing direction of the included GPX file is matching Your desired traveling direction, so import it 'forward'.
		* **`include-rev`** _`filename-no-extension`_ : Include a frequently used GPX track segment from the 'gpxinclude' folder into Your track. The drawing direction of the included GPX file is the opposite of Your planned trip, so import it 'in reverse'.
	* Then there might be such GPX tracks that You've specifically drawn for this trip, these segments can be imported from the 'gpxsegments' folder.
		* **`segment`** _`filename-no-extension`_ : Import a previously drawn trip segment in GPX format from the 'gpxsegments' folder. As these segments are drawn for this trip, so direction is always matching.
	* Charging times and passive times can be added between two GPX segment imports
		* **`charge`** _`Batt%-or-Time`_ **|** _`descr`_ : Specify a charging either by charged percentage or by charging time (Unit of Measure specifies which), and have a description for this charging location.
		* **`passive`** _`Time`_ **|** _`descr`_ : Spend time passively without charging. Specify the time spent and the activity in the description.
	* All GPX segments referred in the config files must exist as '.gpx' files. Everything is calculated automatically using the vehicle parameters and the GPX data.
	* If there are track segments within the GPX file, they are treated as separate etaps by the program, automatically labeled as '-1', '-2', ...
	* In case of verbose mode each point of the GPX file will be a separate etap...
	* If the GPX file is segmented, there can be a _name_ tag specified for each piece, that will also appear in the output to make it more clear



**Command line arguments:**

* `-g` : *Full Grid* : Show all 0.1degree confluence points in the whole coverage area, not just the ones next to the track points
* `-n` : *No separator* : Do not put an additional separator line before each charging session. Useful if trip plan is vague (etap-charge-etap-charge), because the day does not break up to small pieces. Don't use this if the trip is detailed, as then the small segments that need to be ridden with one charge will appear grouped.
* `-s` : *Simple mode* : By default the program gives all possible technical details for each etap or charge. Simple mode reduces it to the essential columns: distance, time, battery SoC
* `-v` : *Verbose mode* : In case of GPX mode the default is that there is one data row for each GPX segment. Verbose mode will output 1 row for each GPX point. This is only useful for debugging. For trip planning it is too much data flow.

### GPXGenerator

> Utility to create larger GPX trip files from smaller, previously drawn segments.
> This program is able to sew parts together, very similarly to the EV-trip program.

It is using the same '.cfg' config files from the 'trips' folder as EV-trip does, but is only able to understand the 'include-fwd', 'include-rev' and 'segment' elements, and generate one single large GPX file in the 'gpxexport' folder to display the whole trip at once.
