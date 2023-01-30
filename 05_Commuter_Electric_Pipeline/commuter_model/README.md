# Commuter Model
Each commute mode takes relevant individual parameters such as gender, health, and age, as well as contextual parameters, like the existence of safe biking infrastructure, to declare if an individual is eligible for each mode of transportation. These parameters apply different constraints on possible mode choices. The details and sources for this implementation are as follows.

**Autos**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_age - maximum age of drivers. Research from Kaiser Permanente and retirement age indicates 75 is a realistic cut-off |
| min_distance - minimum distance traveled by drivers, does not make sense to drive for under 1 mile (2km) |
| min_income - minimum income of drivers. Current cutoff is set at the NY poverty line |
| cognitive_diff - if the individual has cognitive difficulties, they would not have a drivers license |
| ambulatory_diff - if the individual has walking difficulties, they would not have a drivers license |
| ind_living_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license |
| selfcare_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license |
| vision_diff - if the individual has vision difficulties, they would not have a drivers license |
| vehicle_availabile - if the individual does not have a car, they cannot drive to work |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many, of each sex, will drive a car of eligible riders? 0-100 value |
| age_dist - to be determined how we can use age distributions to determine ridership. |
| Ex) 35 year olds may be 2x more likely to ride than a 50 year old |

**Motorcycle**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_age - maximum age of drivers.  Research from Kaiser Permanente and retirement age indicates 75 is a  realistic cut-off |
| max_distance  - max distance traveled by drivers, avg motorcycle tank only holds 150 miles |
| min_income - minimum income of  drivers. Current cutoff is set at the NY poverty line |
| cognitive_diff - if the individual has cognitive difficulties, they  would not have a drivers license |
| ambulatory_diff - if the individual  has walking difficulties, they would not have a drivers license |
| ind_living_diff  - if the individual has difficulties taking care of themselves, they would  not have a drivers license |
| selfcare_diff - if the individual has  difficulties taking care of themselves, they would not have a drivers license |
| vision_diff  - if the individual has vision difficulties, they would not have a drivers  license |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many,  of each sex, will drive a car of eligible riders? 0-100 value |
| age_dist -  to be determined how we can use age distributions to determine ridership. |
| Ex) 35 year olds may be 2x more  likely to ride than a 50 year old |

**Taxicab**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_distance - max distance of taxicab ride (~15 miles or 30 km) |
| min_income - minimum income of drivers. Current cutoff is set at the NY poverty line |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many, of each sex, will take a taxi of eligible riders? 0-100 value |
| age_dist - to be determined how we can use age distributions to determine ridership. |
| Ex) 35 year olds may be 2x more likely to ride than a 50 year old |

**Bus**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| home_region (list): Bus-friendly Residential PUMAs, calculated based on current commuting data (% or count) |
| work_region (list): Bus-friendly Place of Work PUMAs, calculated based on current commuting data (% or count) |
| schedule (list): Operating hours of the buses                |
| **Changable inputs**                                         |
| affordability (0-100, default 20): Commuting costs as % of income. Higher = more likely somebody can use this mode |
| fixgaps (True/False, default False): Whether to fix gaps with current data |

**Subway**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| home_region (list): Subway-friendly Residential PUMAs, calculated based on current commuting data (% or count) |
| work_region (list): Subway-friendly Place of Work PUMAs, calculated based on current commuting data (% or count) |
| schedule (list): Operating hours of the subway               |
| **Changable Inputs**                                         |
| affordability (0-100, default 20): Commuting costs as % of income |
| fixgaps (True/False, default False): Whether to fix gaps with current data |

**Commuter Rail**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| home_region (list): CommuterRail-friendly Residential PUMAs, calculated based on current commuting data (% or count) |
| work_region (list): CommuterRail-friendly Place of Work PUMAs, calculated based on current commuting data (% or count) |
| schedule (list): Operating hours of the commuter rail        |
| **Changable Inputs**                                         |
| affordability (0-100, default 20): Commuting costs as % of income |
| fixgaps (True/False, default False): Whether to fix gaps with current data |

**Ferry**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| home_region (list): Ferry-friendly Residential PUMAs, calculated based on current commuting data (% or count) |
| work_region (list): Ferry-friendly Place of Work PUMAs, calculated based on current commuting data (% or count) |
| schedule (list): Operating hours of the ferry                |
| **Changable Inputs**                                         |
| affordability (0-100, default 20): Commuting costs as % of income |
| fixgaps (True/False, default False): Whether to fix gaps with current data |

**Scooter**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_age - maximum age of e-scooter riders: 60 is a realistic cut-off |
| max_distance - The average speed of electric scooters is around 15 mph (24 km/h),some can go up to 75mph |
| scooter_friendly_origins - no specific esooter infrastructure, so use same bike lanes at this moment |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many, of each sex, will ride an e-scooter of eligible riders? 0-100 value |

**Walking**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_distance - max distance of a walk 2 miles (can up to 20 miles or 32 km) |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many, of each sex, will take a taxi of eligible riders? 0-100 value |

**Ebikes**

| Hard Caps                                                    |
| ------------------------------------------------------------ |
| max_age - maximum age of e-bikers. Early research indicates 70 is a realistic cut-off |
| max_distance - maximum distance traveled by e-bikers. 15 miles (24 KM) to start. |
| bike_friendly_origins - what origin points have bike infrastructure leading into Manhattan? |
| ** Bronx, Queens, Brooklyn, Northern NJ                      |
| **Changable Inputs**                                         |
| male_pct & female_pct - how many, of each sex, will ride an e-bike of eligible riders? 0-100 value |
| age_dist - to be determined how we can use age distributions to determine ridership. |
| Ex) 35 year olds may be 2x more likely to ride than a 50 year old |

**WFH**

| Changable Inputs                                             |
| ------------------------------------------------------------ |
| wfh_dampener: decimal 0-1                                    |
| if 1, then just use probs as is.                             |
| if <1, multiply probabilities by dampener to reduce WFH population |
| if 0, nobody will WFH                                        |
| WFH taken as a conditional prob of income and education from Census Household Pulse Survey results last year |



