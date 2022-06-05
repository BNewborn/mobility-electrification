import pandas as pd
import numpy as np
import random
from pandas.api.types import CategoricalDtype


#### Helper Functions
#### These functions are used for transformations of our dataframes
def NumberOfEV(row):
    ### For each row, getting the number of EVs
    if row['TransMode'] in ['AutoOccupants','Escooter','Bicycle','Motorcycle','Taxicab']:
        return row['PERWT']
    elif row['TransMode']=='Bus':
        return row['PERWT']/20
    elif row['TransMode']=='Ferry':
        return row['PERWT']/100
    elif row['TransMode'] in ['Subway','CommuterRail']:
        return 1 


def TotalEnergyPerEV(row):
    ### For each row, getting the total energy for EACH EV
    if row['TransMode'] in ['AutoOccupants','Escooter','Bicycle','Motorcycle']:
        return row['DISTANCE_KM']*row['Multiplier']*2
    elif row['TransMode'] in ['Bus','Taxicab']:
        return row['DISTANCE_KM']*row['Multiplier']
    elif row['TransMode']=='Ferry':
        return row['Multiplier']
    elif row['TransMode'] in ['Subway','CommuterRail']:
        return row['PERWT']*row['Multiplier']


def HourEnergyPerEV(row,PEV_delay_hr,bus_ferry_cab_delay):
    ### For each row, getting the hourly energy for EACH EV
    ### output are rows with two new columns (type: list): Charge_Hour & Energy
    if row['TransMode'] in ['AutoOccupants','Escooter','Bicycle','Motorcycle','Taxicab','Bus','Ferry']:
        hour = list(range(0,24))*2
        atwork_hour_list = hour[row['HOUR'] : row['HOUR']+row['HRS_WK_DAILY']]
        charging_hr_roundup = np.ceil(row['TotalEnergyPerEV']/row['ChargingPower_kW'])
        duration_hr = int(min(charging_hr_roundup,row['HoursToFullyRecharge_hr'],row['HRS_WK_DAILY']))
        energy = int(row['TotalEnergyPerEV']//row['ChargingPower_kW'])*[row['ChargingPower_kW']] + [row['TotalEnergyPerEV']%row['ChargingPower_kW']]
        energy_list = energy[:duration_hr]

        if row['TransMode'] in ['AutoOccupants','Escooter','Bicycle','Motorcycle']:
            
            max_delay = row['HRS_WK_DAILY'] - duration_hr
            random_delay = random.randint(0,max_delay)
            PEV_delay_hr = int(min(PEV_delay_hr, max_delay))
            row['Charge_Hour_ER'] = atwork_hour_list[:duration_hr]
            row['Charge_Hour_LT'] = atwork_hour_list[-duration_hr:]
            row['Charge_Hour_RND'] = atwork_hour_list[random_delay:duration_hr+random_delay]
            row['Charge_Hour_CM'] = atwork_hour_list[PEV_delay_hr:duration_hr+PEV_delay_hr]     
            row['Energy'] = energy_list

            return row 
        elif row['TransMode'] in ['Bus','Ferry','Taxicab']:
            hour_list = hour[row['HOUR']+bus_ferry_cab_delay : row['HOUR']+bus_ferry_cab_delay+duration_hr]
            row['Charge_Hour_ER'] = hour_list
            row['Charge_Hour_LT'] = hour_list
            row['Charge_Hour_RND'] = hour_list
            row['Charge_Hour_CM'] = hour_list
            row['Energy'] = energy_list
            return row 
        
    elif row['TransMode'] in ['Subway','CommuterRail']:
        hour_list = [row['HOUR']]
        row['Charge_Hour_ER'] = hour_list
        row['Charge_Hour_LT'] = hour_list
        row['Charge_Hour_RND'] = hour_list
        row['Charge_Hour_CM'] = hour_list
        row['Energy'] = [row['TotalEnergyPerEV']]
        return row 

class ElectricModel:
    def __init__(self,commuter_df,ev_reference_table_loc,PEV_delay_hr,bus_ferry_cab_delay):
        '''
        variables needed to create electricmodel

        commuter_df: output of commutermodel class
        ev_reference_table_loc: location of electric reference information (static csv)
        PEV_delay_hr: parameter to adjust when charging occurs for PEV (cars)
        bus_ferry_cab_delay: delay from  use that will bus/ferry/cab will charge
        '''

        self.commuter_df = commuter_df
        self.ev_reference_table_loc = ev_reference_table_loc
        self.PEV_delay_hr=PEV_delay_hr
        self.bus_ferry_cab_delay=bus_ferry_cab_delay

             


    def HourEnergyByMode(self,df):
        '''
        [Input] df: the inbound or outbound flow dataframe
        [Output] A dataframe shows the agg energy at hour-mode level, data structures: Charge_Hour, TransMode, Energy
        This function wraps up the above four functions: NumberOfEV, TotalEnergyPerEV, HourEnergyPerEV, floor
        '''
        
        df = df.merge(right=self.ev_reference_table[['TransMode','Multiplier','ChargingPower_kW','HoursToFullyRecharge_hr']], on=["TransMode"], how='inner')

        df['NumberOfEV'] = df.apply(lambda row: NumberOfEV(row), axis=1)
        df['TotalEnergyPerEV'] = df.apply(lambda row: TotalEnergyPerEV(row), axis=1)
        
        df = df.apply(HourEnergyPerEV
        ,PEV_delay_hr=self.PEV_delay_hr
        ,bus_ferry_cab_delay=self.bus_ferry_cab_delay
        , axis=1) ### this step is a little slow

        df = df.explode(['Charge_Hour_ER','Charge_Hour_LT','Charge_Hour_RND','Charge_Hour_CM','Energy'])
        df['Energy'] = df['Energy']*df['NumberOfEV'] ### energy per EV --> energy all EV
        
        ###new steps
        value_vars = [c for c in df if c.startswith('Charge_Hour_')]
        df_melt = pd.melt(df, id_vars=["TransMode","FLOW_DIR","Energy"], value_vars=value_vars, var_name='PEV_DELAY', value_name='Charge_Hour')
        df_agg = df_melt.groupby(by=["Charge_Hour","TransMode","PEV_DELAY","FLOW_DIR"]).agg({"Energy":"sum"}).reset_index()
        
        delay_dict = {'Charge_Hour_ER':'Earliest',
                    'Charge_Hour_LT':'Latest',
                    'Charge_Hour_RND':'Random',
                    'Charge_Hour_CM':'Custom'}
        df_agg["PEV_DELAY"] = df_agg["PEV_DELAY"].replace(delay_dict)

        df_agg["Energy_Floor"] = df_agg["TransMode"].map(self.energy_floor_dict).fillna(0)
        df_agg['Energy'] = df_agg['Energy'] + df_agg["Energy_Floor"]
        df_agg.drop(["Energy_Floor"],inplace=True,axis=1)

        

        # ### old steps
        # df_agg = df.groupby(by=["Charge_Hour","TransMode","FLOW_DIR"]).agg({"Energy":"sum"}).reset_index()

        # df_agg["Energy_Floor"] = df_agg["TransMode"].map(self.energy_floor_dict).fillna(0)

        # # print(df_agg["Energy_Floor"].value_counts())

        # df_agg['Energy'] = df_agg['Energy'] + df_agg["Energy_Floor"]
        # df_agg.drop(["Energy_Floor"],inplace=True,axis=1)

        # # df_agg['Energy'] = df_agg.apply(lambda row: floor(row), axis=1)


        #### from old steps
        all_dir = df_agg.groupby(by=["Charge_Hour","TransMode"]).agg({"Energy":"sum"}).reset_index()
        all_dir['FLOW_DIR'] = 'ALL'
        df_agg = pd.concat([df_agg, all_dir]).reset_index(drop=True)
        return df_agg

    def excludingfromMNY(self,df,pct_escooter_N,pct_bicycle_N):
        '''
        [Input]
        df: the input dataframe should be the output df of the commuter model, for now, operations such as adding new columns (MNY_RES) are performed outside/before
        pct_escooter_N: % of Escooter no need to charge in MNY, we can interpret this number as (MNY_RES not EV + non_MNY_RES prefer charge at home)
        pct_bicycle_N: % of E-Bicycle no need to charge in MNY, we can interpret this number as (MNY_RES not EV + non_MNY_RES prefer charge at home)
        ### future: taxi narrow to MNY
        
        [Output]
        series (0,1) indicating whether each line should be exclude from the electric model or not
        excluding: True/1; keep: False/0
        '''
        
        autos_motorcycle_hardcap = (df['HOMEOWNER_LABEL']=='Own') & (df['MNY_RES']==0) & (df['TransMode'].isin(['AutoOccupants','Motorcycle']))
        bus_hardcap = (df['MNY_RES']==0) & (df['TransMode'].isin(['Bus']))

        escooter_flag = df['TransMode'].apply(lambda x: True if random.random() <= pct_escooter_N/100 and x=='Escooter' else False)
        bicycle_flag = df['TransMode'].apply(lambda x: True if random.random() <= pct_bicycle_N/100 and x=='Bicycle' else False)
        final_series = autos_motorcycle_hardcap | bus_hardcap | escooter_flag | bicycle_flag
        
        return final_series.astype(int)

        
    ##### Process Methods     
    def read_electric_info_in(self):
        '''read in electric reference table. also create subway floor and commuter rail floor variables'''
        self.ev_reference_table = pd.read_csv(self.ev_reference_table_loc)
        self.subway_floor = int(self.ev_reference_table[self.ev_reference_table['TransMode']=='Subway']['Floor_kWh'])
        self.commuterRail_floor = int(self.ev_reference_table[self.ev_reference_table['TransMode']=='CommuterRail']['Floor_kWh'])

        self.energy_floor_dict = {"Subway":self.subway_floor
                            ,"CommuterRail":self.commuterRail_floor
                            }

        print(f"ev reference table read in. subway floor and commuter rail floor extracted from table")

    
    def clean_commuter_df(self):
        '''steps that clean commuter_df for our purposes. some lines may be removed if we adjust commutermodel pipeline'''

        ### the next four lines can be deleted if the previous pipeline already fix it
        ### tag those that live in Manhattan
        self.commuter_df['MNY_RES'] = self.commuter_df['PUMAKEY_HOME'].apply(lambda x: 1 if x.startswith('36_038') else 0)

        ### this will be adjusted - TransMode should be the column name for final assignment from CommuterModel
        self.commuter_df = self.commuter_df.rename({'Rand Assignment':'TransMode'},axis=1)

        ### Create leave work hour from arrives and HRS_WK_DAILY 
        self.commuter_df['LEAVE_WORK_HOUR'] = (self.commuter_df['ARRIVES_AT_WORK_HOUR'] + self.commuter_df['HRS_WK_DAILY'])%24
        self.commuter_df['LEAVE_WORK_HOUR'] = self.commuter_df['LEAVE_WORK_HOUR'].astype(int)
        self.commuter_df['HRS_WK_DAILY'] = np.ceil(self.commuter_df['HRS_WK_DAILY']).astype(int)
        
        ## for easier coding, only take Manhattan workers (dir==in)
        self.commuter_df = self.commuter_df[self.commuter_df['COMMUTE_DIRECTION_MANHATTAN']=='in'].reset_index(drop=True)

        ##############################   
        ####   excludingfromMNY   ####
        ##############################
        self.commuter_df['excludingfromMNY'] = self.excludingfromMNY(df=self.commuter_df,pct_escooter_N=20,pct_bicycle_N=20)
        self.commuter_df = self.commuter_df[self.commuter_df['excludingfromMNY']==0].reset_index(drop=True)


    def create_in_out_flow_dfs(self):
        ### in_flow is all transit modes
        self.in_flow = self.commuter_df[["ARRIVES_AT_WORK_HOUR","HRS_WK_DAILY",'TransMode',"DISTANCE_KM",'PERWT']].rename({'ARRIVES_AT_WORK_HOUR':'HOUR'},axis=1)
        self.in_flow['FLOW_DIR'] = 'IN'

        ### out_flow is only those that will use electricity eventually or immediately drawn from manhattan
        self.out_flow = self.commuter_df[["LEAVE_WORK_HOUR","HRS_WK_DAILY",'TransMode',"DISTANCE_KM",'PERWT']].rename({'LEAVE_WORK_HOUR':'HOUR'},axis=1)
        self.out_flow_filter = self.out_flow[self.out_flow['TransMode'].isin(['Bus','Subway','CommuterRail','Taxicab'])].reset_index(drop=True)
        self.out_flow_filter['FLOW_DIR'] = 'OUT'

        ### flow_df will have IN and OUT info tagged separately
        self.flow_df = pd.concat([self.in_flow, self.out_flow_filter]).reset_index(drop=True)
        self.flow_df

    def aggregate_data(self):
        self.df_aggregate = self.HourEnergyByMode(self.flow_df)

        mode_order = CategoricalDtype(['AutoOccupants','Bus','Ferry','Escooter', 'Bicycle','Motorcycle','Taxicab','Subway','CommuterRail'],ordered=True)

        self.df_aggregate['TransMode'] = self.df_aggregate['TransMode'].astype(mode_order)




