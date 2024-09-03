import pandas as pd
import numpy as np
import random

class CommuterModel:
    def __init__(self,ipums_df):
        self.ipums_df = ipums_df
        
        ### Create list of bike-friendly origin PUMAs for e-biking function
        self.bike_friendly_origins = self.ipums_df[(self.ipums_df['PUMA_NAME'].str.contains("NYC-Brook"))|
        (self.ipums_df['PUMA_NAME'].str.contains("NYC-Queen"))|
        (self.ipums_df['PUMA_NAME'].str.contains("NYC-Bronx"))|
        (self.ipums_df['PUMA_NAME'].str.contains("NYC-Manh"))|
        (self.ipums_df['PUMA_NAME'].str.contains("Hudson County"))|
        (self.ipums_df['PUMA_NAME'].str.contains("Bergen"))]['PUMA_NAME'].unique()
        
        ### Read in work-from-home conditional income&education probabilties
        self.wfh_probs = pd.read_csv("commuter_model/wfh_conditional_probs.csv",index_col=0).drop("WFH_TAG",axis=1)

        
        ### Read in required csv to get pumas for mass transit functions
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/bus_subway_rail_ferry_functions.ipynb
        self.reachable_puma_home = pd.read_csv("commuter_model/regional_transit_system/reachable_puma_home.csv")
        self.puma_home_Bus = self.reachable_puma_home[self.reachable_puma_home['Bus']==1]['PUMAKEY_HOME'].to_list()
        self.puma_home_Subway = self.reachable_puma_home[self.reachable_puma_home['Subway']==1]['PUMAKEY_HOME'].to_list()
        self.puma_home_CommuterRail = self.reachable_puma_home[self.reachable_puma_home['CommuterRail']==1]['PUMAKEY_HOME'].to_list()
        self.puma_home_Ferry = self.reachable_puma_home[self.reachable_puma_home['Ferry']==1]['PUMAKEY_HOME'].to_list()
        
        self.reachable_puma_work = pd.read_csv("commuter_model/regional_transit_system/reachable_puma_work.csv")
        self.puma_work_Bus = self.reachable_puma_work[self.reachable_puma_work['Bus']==1]['PUMAKEY_WORK'].to_list()
        self.puma_work_Subway = self.reachable_puma_work[self.reachable_puma_work['Subway']==1]['PUMAKEY_WORK'].to_list()
        self.puma_work_CommuterRail = self.reachable_puma_work[self.reachable_puma_work['CommuterRail']==1]['PUMAKEY_WORK'].to_list()
        self.puma_work_Ferry = self.reachable_puma_work[self.reachable_puma_work['Ferry']==1]['PUMAKEY_WORK'].to_list()
        
        self.time_Bus = list(range(6,22))
        self.time_Subway = list(range(0,24))
        self.time_CommuterRail = list(range(6,22))
        self.time_Ferry = list(range(7,21))
        
        
    def auto_flag_binary(self,max_age,min_distance,min_income,male_pct,female_pct,age_dist):
        '''
        Auto inputs
        Hard Caps:
        max_age - maximum age of drivers. Research from Kaiser Permanente and retirement age indicates 75 is a realistic cut-off
        min_distance - minimum distance traveled by drivers, does not make sense to drive for under 1 mile (2km)
        min_income - minimum income of drivers. Current cutoff is set at the NY poverty line
        cognitive_diff - if the individual has cognitive difficulties, they would not have a drivers license
        ambulatory_diff - if the individual has walking difficulties, they would not have a drivers license
        ind_living_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license
        selfcare_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license
        vision_diff - if the individual has vision difficulties, they would not have a drivers license
        vehicle_availabile - if the individual does not have a car, they cannot drive to work

        Changable inputs:
        male_pct & female_pct - how many, of each sex, will drive a car of eligible riders? 0-100 value
        age_dist - to be determined how we can use age distributions to determine ridership. 
            Ex) 35 year olds may be 2x more likely to ride than a 50 year old

        output:
            series (0,1) indicating whether each line is an eligible driver or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/Auto%2C%20motorcycle%2C%20taxicab%20flags.ipynb
        age_hardcap = self.ipums_df['AGE'] <= max_age
        dist_hardcap = self.ipums_df['DISTANCE_KM'] >= min_distance
        income_hardcap = self.ipums_df['TOTAL_PERSONAL_INCOME'] >= min_income #poverty line in NY 2019
        cog_diff_hardcap = self.ipums_df['COGNITIVE_DIFFICULTY'] <= 0
        amb_diff_hardcap = self.ipums_df['AMBULATORY_DIFFICULTY'] <= 0
        ind_living_diff_hardcap = self.ipums_df['IND_LIVING_DIFFICULTY'] <= 0
        selfcare_diff_hardcap = self.ipums_df['SELFCARE_DIFFICULTY'] <= 0
        vision_diff_hardcap = self.ipums_df['VISION_DIFFICULTY'] <= 0
        car_hardcap = self.ipums_df['VEHICLE_AVAILABLE'] == 1


        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag

        final_series = age_hardcap&dist_hardcap&income_hardcap&cog_diff_hardcap\
                        &amb_diff_hardcap&ind_living_diff_hardcap&selfcare_diff_hardcap\
                        &vision_diff_hardcap&car_hardcap&sex_flag
        return final_series.astype(int)
    
    def motorcycle_flag_binary(self,max_age,max_distance,min_income,male_pct,female_pct,age_dist):
        '''
        Motorcycle inputs
        Hard Caps:
        max_age - maximum age of drivers. Research from Kaiser Permanente and retirement age indicates 75 is a realistic cut-off
        max_distance - max distance traveled by drivers, avg motorcycle tank only holds 150 miles
        min_income - minimum income of drivers. Current cutoff is set at the NY poverty line
        cognitive_diff - if the individual has cognitive difficulties, they would not have a drivers license
        ambulatory_diff - if the individual has walking difficulties, they would not have a drivers license
        ind_living_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license
        selfcare_diff - if the individual has difficulties taking care of themselves, they would not have a drivers license
        vision_diff - if the individual has vision difficulties, they would not have a drivers license

        Changable inputs:
        male_pct & female_pct - how many, of each sex, will drive a car of eligible riders? 0-100 value
        age_dist - to be determined how we can use age distributions to determine ridership. 
            Ex) 35 year olds may be 2x more likely to ride than a 50 year old

        output:
            series (0,1) indicating whether each line is an eligible driver or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/Auto%2C%20motorcycle%2C%20taxicab%20flags.ipynb 
        age_hardcap = self.ipums_df['AGE'] <= max_age
        dist_hardcap = self.ipums_df['DISTANCE_KM'] <= max_distance
        income_hardcap = self.ipums_df['TOTAL_PERSONAL_INCOME'] >= 32626 #poverty line in NY 2019
        cog_diff_hardcap = self.ipums_df['COGNITIVE_DIFFICULTY'] <= 0
        amb_diff_hardcap = self.ipums_df['AMBULATORY_DIFFICULTY'] <= 0
        ind_living_diff_hardcap = self.ipums_df['IND_LIVING_DIFFICULTY'] <= 0
        selfcare_diff_hardcap = self.ipums_df['SELFCARE_DIFFICULTY'] <= 0
        vision_diff_hardcap = self.ipums_df['VISION_DIFFICULTY'] <= 0

        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag

        final_series = age_hardcap&dist_hardcap&income_hardcap&cog_diff_hardcap\
                        &amb_diff_hardcap&ind_living_diff_hardcap&selfcare_diff_hardcap\
                        &vision_diff_hardcap&sex_flag

        return final_series.astype(int)
    
    def taxicab_flag_binary(self,max_distance,min_income, male_pct,female_pct,age_dist):
        '''
        Taxicab inputs
        Hard Caps:
        max_distance - max distance of taxicab ride (~15 miles or 30 km)
        min_income - minimum income of drivers. Current cutoff is set at the NY poverty line

        Changable inputs:
        male_pct & female_pct - how many, of each sex, will take a taxi of eligible riders? 0-100 value
        age_dist - to be determined how we can use age distributions to determine ridership. 
            Ex) 35 year olds may be 2x more likely to ride than a 50 year old

        output:
            series (0,1) indicating whether each line is an eligible driver or not
        '''
        #https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/Auto%2C%20motorcycle%2C%20taxicab%20flags.ipynb
        
        dist_hardcap = self.ipums_df['DISTANCE_KM'] <= max_distance
        income_hardcap = self.ipums_df['TOTAL_PERSONAL_INCOME'] >= min_income #poverty line in NY 2019

        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag

        final_series = dist_hardcap&income_hardcap&sex_flag
        return final_series.astype(int)
    
    
    def bus_flag_binary(self,home_region,work_region,schedule,affordability,fixgaps):
        '''
        inputs
        Hard Caps:
            home_region (list): Bus-friendly Residential PUMAs, calculated based on current commuting data (% or count)
            work_region (list): Bus-friendly Place of Work PUMAs, calculated based on current commuting data (% or count)
            schedule (list): Operating hours of the buses

        Changable inputs:
            affordability (0-100, default 20): Commuting costs as % of income. Higher = more likely somebody can use this mode
            fixgaps (True/False, default False): Whether to fix gaps with current data

        output:
            series (0,1) indicating whether each line is an eligible eBuses commuter or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/bus_subway_rail_ferry_functions.ipynb

        dir_in = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']!='out'
        dir_out = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']=='out'
        home_region_hardcap = self.ipums_df[dir_in]['PUMAKEY_HOME'].isin(home_region)
        work_region_hardcap = self.ipums_df[dir_out]['PUMAKEY_WORK'].isin(work_region)
        region_hardcap = pd.concat([home_region_hardcap, work_region_hardcap])

        schedule_hardcap = self.ipums_df['DEPARTS_FOR_WORK_HOUR'].isin(schedule)    ## Using the current departure time as a reference

        affordability_changable = self.ipums_df['TOTAL_PERSONAL_INCOME']>=100*12*100/int(affordability)

        if fixgaps == True:
            fixgaps_changable = self.ipums_df['MODE_TRANSP_TO_WORK_HBDMATCH']=='Bus'
            final_series = region_hardcap & schedule_hardcap & affordability_changable | fixgaps_changable
        elif fixgaps == False:
            final_series = region_hardcap & schedule_hardcap & affordability_changable

        return final_series.astype(int)
    
    def subway_flag_binary(self,home_region,work_region,schedule,affordability,fixgaps):
        '''
        inputs
        Hard Caps:
            home_region (list): Subway-friendly Residential PUMAs, calculated based on current commuting data (% or count)
            work_region (list): Subway-friendly Place of Work PUMAs, calculated based on current commuting data (% or count)
            schedule (list): Operating hours of the subway

        Changable inputs:
            affordability (0-100, default 20): Commuting costs as % of income
            fixgaps (True/False, default False): Whether to fix gaps with current data

        output:
            series (0,1) indicating whether each line is an eligible subway commuter or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/bus_subway_rail_ferry_functions.ipynb

        dir_in = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']!='out'
        dir_out = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']=='out'
        home_region_hardcap = self.ipums_df[dir_in]['PUMAKEY_HOME'].isin(home_region)
        work_region_hardcap = self.ipums_df[dir_out]['PUMAKEY_WORK'].isin(work_region)
        region_hardcap = pd.concat([home_region_hardcap, work_region_hardcap])

        schedule_hardcap = self.ipums_df['DEPARTS_FOR_WORK_HOUR'].isin(schedule)    ## Using the current departure time as a reference

        affordability_changable = self.ipums_df['TOTAL_PERSONAL_INCOME']>=100*12*100/int(affordability)

        if fixgaps == True:
            fixgaps_changable = self.ipums_df['MODE_TRANSP_TO_WORK_HBDMATCH']=='Subway'
            final_series = region_hardcap & schedule_hardcap & affordability_changable | fixgaps_changable
        elif fixgaps == False:
            final_series = region_hardcap & schedule_hardcap & affordability_changable

        return final_series.astype(int)
    
    def commuterRail_flag_binary(self,home_region,work_region,schedule,affordability,fixgaps):
        '''
        inputs
        Hard Caps:
            home_region (list): CommuterRail-friendly Residential PUMAs, calculated based on current commuting data (% or count)
            work_region (list): CommuterRail-friendly Place of Work PUMAs, calculated based on current commuting data (% or count)
            schedule (list): Operating hours of the commuter rail

        Changable inputs:
            affordability (0-100, default 20): Commuting costs as % of income
            fixgaps (True/False, default False): Whether to fix gaps with current data

        output:
            series (0,1) indicating whether each line is an eligible Commuter Rail commuter or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/bus_subway_rail_ferry_functions.ipynb

        dir_in = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']!='out'
        dir_out = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']=='out'
        home_region_hardcap = self.ipums_df[dir_in]['PUMAKEY_HOME'].isin(home_region)
        work_region_hardcap = self.ipums_df[dir_out]['PUMAKEY_WORK'].isin(work_region)
        region_hardcap = pd.concat([home_region_hardcap, work_region_hardcap])

        schedule_hardcap = self.ipums_df['DEPARTS_FOR_WORK_HOUR'].isin(schedule)    ## Using the current departure time as a reference

        affordability_changable = self.ipums_df['TOTAL_PERSONAL_INCOME']>=100*12*100/int(affordability)

        if fixgaps == True:
            fixgaps_changable = self.ipums_df['MODE_TRANSP_TO_WORK_HBDMATCH']=='CommuterRail'
            final_series = region_hardcap & schedule_hardcap & affordability_changable | fixgaps_changable
        elif fixgaps == False:
            final_series = region_hardcap & schedule_hardcap & affordability_changable

        return final_series.astype(int)
    
    def ferry_flag_binary(self,home_region,work_region,schedule,affordability,fixgaps):
        '''
        inputs
        Hard Caps:
            home_region (list): Ferry-friendly Residential PUMAs, calculated based on current commuting data (% or count)
            work_region (list): Ferry-friendly Place of Work PUMAs, calculated based on current commuting data (% or count)
            schedule (list): Operating hours of the ferry

        Changable inputs:
            affordability (0-100, default 20): Commuting costs as % of income
            fixgaps (True/False, default False): Whether to fix gaps with current data

        output:
            series (0,1) indicating whether each line is an eligible ferry commuter or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/bus_subway_rail_ferry_functions.ipynb

        dir_in = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']!='out'
        dir_out = self.ipums_df['COMMUTE_DIRECTION_MANHATTAN']=='out'
        home_region_hardcap = self.ipums_df[dir_in]['PUMAKEY_HOME'].isin(home_region)
        work_region_hardcap = self.ipums_df[dir_out]['PUMAKEY_WORK'].isin(work_region)
        region_hardcap = pd.concat([home_region_hardcap, work_region_hardcap])

        schedule_hardcap = self.ipums_df['DEPARTS_FOR_WORK_HOUR'].isin(schedule)    ## Using the current departure time as a reference

        affordability_changable = self.ipums_df['TOTAL_PERSONAL_INCOME']>=100*12*100/int(affordability)

        if fixgaps == True:
            fixgaps_changable = self.ipums_df['MODE_TRANSP_TO_WORK_HBDMATCH']=='Ferry'
            final_series = region_hardcap & schedule_hardcap & affordability_changable | fixgaps_changable
        elif fixgaps == False:
            final_series = region_hardcap & schedule_hardcap & affordability_changable

        return final_series.astype(int)
    
    def escooter_flag_binary(self,max_age,max_distance,scooter_friendly_origins,male_pct,female_pct):
        '''
        inputs
        Hard Caps:
        max_age - maximum age of e-scooter riders: 60 is a realistic cut-off  
        max_distance - The average speed of electric scooters is around 15 mph (24 km/h),some can go up to 75mph
        scooter_friendly_origins - no specific esooter infrastructure, so use same bike lanes at this moment

        Changable inputs:
        male_pct & female_pct - how many, of each sex, will ride an e-scooter of eligible riders? 0-100 value

        output:
            series (0,1) indicating whether each line is an eligible e-scooter rider or not
        '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/e-scooter%2C%20walking%20flags.ipynb


        age_hardcap = self.ipums_df['AGE']<=max_age
        dist_hardcap = self.ipums_df['DISTANCE_KM']<=max_distance
        scooter_infra_locs = self.ipums_df['PUMA_NAME'].isin(scooter_friendly_origins)
        amb_diff_hardcap = self.ipums_df['AMBULATORY_DIFFICULTY'] <= 0
        ind_living_diff_hardcap = self.ipums_df['IND_LIVING_DIFFICULTY'] <= 0
        selfcare_diff_hardcap = self.ipums_df['SELFCARE_DIFFICULTY'] <= 0
        vision_diff_hardcap = self.ipums_df['VISION_DIFFICULTY'] <= 0

        ### Gender - 
        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag

        final_series = age_hardcap&dist_hardcap&scooter_infra_locs&amb_diff_hardcap&ind_living_diff_hardcap&selfcare_diff_hardcap&vision_diff_hardcap&sex_flag

        return final_series.astype(int)
    
    def walking_flag_binary(self,max_age,max_distance,male_pct,female_pct):
        '''
        Walking inputs
        Hard Caps:
        max_distance - max distance of a walk 2 miles (can up to 20 miles or 32 km)

        Changable inputs:
        male_pct & female_pct - how many, of each sex, will take a taxi of eligible riders? 0-100 value

        output:
            series (0,1) indicating whether each line is an eligible walker or not
            '''
        # https://github.com/BNewborn/mobility-electrification/blob/main/03_CommuterModel/tranwork_flags/e-scooter%2C%20walking%20flags.ipynb
        age_hardcap = self.ipums_df['AGE']<=max_age
        dist_hardcap = self.ipums_df['DISTANCE_KM']<=max_distance
        amb_diff_hardcap = self.ipums_df['AMBULATORY_DIFFICULTY'] <= 0
        selfcare_diff_hardcap = self.ipums_df['SELFCARE_DIFFICULTY'] <= 0
        vision_diff_hardcap = self.ipums_df['VISION_DIFFICULTY'] <= 0

        ### Gender
        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag

        final_series = age_hardcap&dist_hardcap&amb_diff_hardcap&sex_flag&selfcare_diff_hardcap&vision_diff_hardcap

        return final_series.astype(int)
    
    def ebike_flag_binary(self,max_age,max_distance,bike_friendly_origins,male_pct,female_pct,age_dist):
        '''
        inputs
        Hard Caps:
        max_age - maximum age of e-bikers. Early research indicates 70 is a realistic cut-off
        max_distance - maximum distance traveled by e-bikers. 15 miles (24 KM) to start.
        bike_friendly_origins - what origin points have bike infrastructure leading into Manhattan?
            ** Bronx, Queens, Brooklyn, Northern NJ


        Changable inputs:
        male_pct & female_pct - how many, of each sex, will ride an e-bike of eligible riders? 0-100 value
        age_dist - to be determined how we can use age distributions to determine ridership. 
            Ex) 35 year olds may be 2x more likely to ride than a 50 year old

        output:
            series (0,1) indicating whether each line is an eligible e-bike rider or not
        '''


        age_hardcap = self.ipums_df['AGE']<=max_age
        dist_hardcap = self.ipums_df['DISTANCE_KM']<=max_distance
        bike_infra_locs = self.ipums_df['PUMA_NAME'].isin(bike_friendly_origins)

        ### Gender - 
        male_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
        female_sex_flag = self.ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
        sex_flag = male_sex_flag|female_sex_flag


        ### Age - TBD if we use an age distribution or buckets
        final_series = age_hardcap&dist_hardcap&bike_infra_locs&sex_flag

        return final_series.astype(int)
    
    def wfh_flag_binary(self,wfh_dampener):
        '''  
        Changable inputs:
        wfh_dampener: decimal 0-1
            if 1, then just use probs as is.
            if <1, multiply probabilities by dampener to reduce WFH population
            if 0, nobody will WFH

        WFH taken as a conditional prob of income and education from Census Household Pulse Survey results last year

        output:
            series (0,1) indicating whether each line is a likely WFH candidate
        '''   

        assert wfh_dampener >= 0 and wfh_dampener <= 1

        def income_prob_label(inp_income):
            if inp_income >= 200000:
                return '7) 200K+'
            elif inp_income >= 150000:
                return '6) 150-200K'
            elif inp_income >= 100000:
                return '5) 100-150K'
            elif inp_income >= 75000:
                return '4) 75-100K'
            elif inp_income >= 50000:
                return '3) 50-75K'
            elif inp_income >= 35000:
                return '2) 35-50K'
            elif inp_income >= 25000:
                return '1) 25-35K'
            else:
                return '0) 0-25K'

        def educ_label(inp_educ):
            if inp_educ in ['College_4Year','College_5PlusYears']:
                return 1
            else:
                return 0

        self.ipums_df['INC_TAG'] = self.ipums_df["TOTAL_PERSONAL_INCOME"].apply(income_prob_label)
        self.ipums_df['EDUC_TAG'] = self.ipums_df["EDUC_LABEL"].apply(educ_label)


        industries_cannot_wfh = ["Educational Services, and Health Care and Social Assistance"\
                                ,"Arts, Entertainment, and Recreation, and Accommodation and Food Services"\
                                ,"Retail Trade", "Construction"\
                                ,"Other Services, Except Public Administration"\
                                ,"Transportation and Warehousing, and Utilities","Manufacturing"\
                                ,"Agriculture, Forestry, Fishing, and Hunting, and Mining"]



        industry_binary = self.ipums_df["IND_CAT"].apply(lambda x: 0 if x in industries_cannot_wfh else 1)
        wfh_probabilities = self.ipums_df.merge(right=self.wfh_probs,on=["INC_TAG","EDUC_TAG"])["PROB WFH | INC * EDUC"]
        wfh_binary = wfh_probabilities.apply(lambda x: 1 if random.random() <= x*wfh_dampener else 0)
        self.ipums_df.drop(["INC_TAG","EDUC_TAG"],axis=1,inplace=True)

        wfh_overall_binary = industry_binary&wfh_binary

        return wfh_overall_binary
    
    def AssignTransModesWaterfall(self,waterfall_order):
        '''
        This method, instead of randomly assigning a transmode from eligible riders, uses waterfall logic to assign.
        First in the list will always take priority, then 2nd, 3rd etc.
        waterfall_order should have the column names - easiest that way

        It returns a pandas series to be added to the end of ipums_df
        '''
        assignments_total = list()
        # flag_cols = [x for x in self.ipums_df if "FLAG" in x]
        # Dictionary to return clean transmode name used in downstream options
        match_dict = {"FLAG_AUTO":"AutoOccupants"
        ,"FLAG_ESCOOTER" :"Escooter"
        ,"FLAG_WALK" :"Walk"
        ,"FLAG_EBIKE" :"Bicycle"
        ,"FLAG_MOTORCYCLE":"Motorcycle"
        ,"FLAG_TAXICAB":"Taxicab"
        ,"FLAG_EBUSES":"Bus"
        ,"FLAG_SUBWAY":"Subway"
        ,"FLAG_COMMUTERRAIL":"CommuterRail"
        ,"FLAG_FERRY":"Ferry"
        ,"FLAG_WFH":"WFH"
        }

        ### Loop through every row, creating an ordered list of the options each is eligible for.
        for index, row in self.ipums_df.iterrows():
            # print(row)
            per_line_flags = list()
            for flag in waterfall_order:
                if row[flag] == 1:
                    per_line_flags.append(flag)

            ### At the end of the waterfall_order,
            # If per_line_flags has at least 1 entry, take the first. Otherwise, return "No Option"
            if len(per_line_flags) > 0 :
                assignments_total.append(match_dict[per_line_flags[0]])
            else:
                assignments_total.append("No Option")
            
        return assignments_total

    def RandAssignNoOption(self, FLAG_AUTO, FLAG_MOTORCYCLE, FLAG_TAXICAB, FLAG_EBUSES, FLAG_SUBWAY, FLAG_COMMUTERRAIL, FLAG_FERRY, FLAG_ESCOOTER, FLAG_WALK, FLAG_EBIKE, FLAG_WFH, NoOptionAssignment = "No Option"):
        '''
        This method looks at how many modes of transit an IPUMS line is eligible for and randomly selects one
        It returns a pandas series to be added to the end of ipums_df
        '''
        assignment = []
        modes = ['AutoOccupants','Motorcycle','Taxicab','Bus','Subway','CommuterRail','Ferry','Escooter','Walk','Bicycle','WFH']
        for index, rows in self.ipums_df.iterrows():
            available_indices = []
            if FLAG_AUTO[index] == 1:
                available_indices.append(0)
            if FLAG_MOTORCYCLE[index] == 1:
                available_indices.append(1)
            if FLAG_TAXICAB[index] == 1:
                available_indices.append(2)
            if FLAG_EBUSES[index] == 1:
                available_indices.append(3)
            if FLAG_SUBWAY[index] == 1:
                available_indices.append(4)
            if FLAG_COMMUTERRAIL[index] == 1:
                available_indices.append(5)
            if FLAG_FERRY[index] == 1:
                available_indices.append(6)
            if FLAG_ESCOOTER[index] == 1:
                available_indices.append(7)
            if FLAG_WALK[index] == 1:
                available_indices.append(8)
            if FLAG_EBIKE[index] == 1:
                available_indices.append(9)
            if FLAG_WFH[index] == 1:
                available_indices.append(10)
            if len(available_indices) == 0:
                assignment.append("No Option")
            else:
                RandAssignment = random.choice(available_indices)
                assignment.append(modes[RandAssignment])
        return assignment
    
    def RandAssignChosenOption(self, RandAssignment, CurrentAssignment, NoOptionAssignment = "Current"):
        '''
        This method takes in an assigned option for each ipums line. If there is no option assigned, it returns the line's existing mode from 2019 IPUMS data.
        It returns a pandas series to be added to the end of ipums_df
        '''
        assignment = []
        for i in range(len(RandAssignment)):
            if RandAssignment[i] == "No Option":
                if NoOptionAssignment == "Current":
                    assignment.append(CurrentAssignment[i])
                else:
                    assignment.append(NoOptionAssignment)
            else:
                assignment.append(RandAssignment[i])
        return assignment
    
    def GasCO2(self, OriginalMode, Distance):
        '''
        This method provides CO2 calculations for each mode of transit taken
        '''
        GasCO2lbs = []
        for i in range(len(OriginalMode)):
            if OriginalMode[i] in ["AutoOccupants" , "Taxicab"]:
                CO2 = Distance[i]*0.4346
            elif OriginalMode[i] == "Bus":
                CO2 = Distance[i]*0.14038
            elif OriginalMode[i] == "Ferry":
                CO2 = Distance[i]*2.4627
            elif OriginalMode[i] in ["Escooter" , "Bicycle"]:
                CO2 = 0
            elif OriginalMode[i] == "Motorcycle":
                CO2 = Distance[i]*0.18615
            elif OriginalMode[i] in ["Subway" , "CommuterRail"]:
                CO2 = 1 #placeholder
            GasCO2lbs.append(CO2)
        return GasCO2lbs
    
    def WeightedAssignNoOption(self, FLAG_AUTO, FLAG_MOTORCYCLE, FLAG_TAXICAB, FLAG_EBUSES, FLAG_SUBWAY, FLAG_COMMUTERRAIL, FLAG_FERRY, FLAG_ESCOOTER, FLAG_WALK, FLAG_EBIKE, FLAG_WFH, WEIGHTS, NoOptionAssignment = "No Option"):
        '''
        This method looks at how many modes of transit an IPUMS line is eligible for and randomly selects with a list of weights one
        It returns a pandas series to be added to the end of ipums_df
        '''
        assignment = []
        modes = ['AutoOccupants','Motorcycle','Taxicab','Bus','Subway','CommuterRail','Ferry','Escooter','Walk','Bicycle','WFH']
        for index, rows in self.ipums_df.iterrows():
            available_indices = []
            weights = []
            if FLAG_AUTO[index] == 1:
                available_indices.append(0)
                weights.append(WEIGHTS[0])
            if FLAG_MOTORCYCLE[index] == 1:
                available_indices.append(1)
                weights.append(WEIGHTS[1])
            if FLAG_TAXICAB[index] == 1:
                available_indices.append(2)
                weights.append(WEIGHTS[2])
            if FLAG_EBUSES[index] == 1:
                available_indices.append(3)
                weights.append(WEIGHTS[3])
            if FLAG_SUBWAY[index] == 1:
                available_indices.append(4)
                weights.append(WEIGHTS[4])
            if FLAG_COMMUTERRAIL[index] == 1:
                available_indices.append(5)
                weights.append(WEIGHTS[5])
            if FLAG_FERRY[index] == 1:
                available_indices.append(6)
                weights.append(WEIGHTS[6])
            if FLAG_ESCOOTER[index] == 1:
                available_indices.append(7)
                weights.append(WEIGHTS[7])
            if FLAG_WALK[index] == 1:
                available_indices.append(8)
                weights.append(WEIGHTS[8])
            if FLAG_EBIKE[index] == 1:
                available_indices.append(9)
                weights.append(WEIGHTS[9])
            if FLAG_WFH[index] == 1:
                available_indices.append(10)
                weights.append(WEIGHTS[10])
            if (len(available_indices) == 0) | (sum(weights) == 0):
                assignment.append("No Option")
            else:
                RandAssignment = random.choices(available_indices, tuple(weights),k=1)[0]
                assignment.append(modes[RandAssignment])
        return assignment