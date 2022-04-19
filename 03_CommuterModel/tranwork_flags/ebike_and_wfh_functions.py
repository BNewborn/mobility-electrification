'''
in this script there are two functions

ebike_flag_binary
wfh_flag_binary

Brian - April 18, 2022

'''

import pandas as pd

ipums_df = pd.read_csv("../ipums_data/disaggregated_cleaned_ipums_data.csv",index_col=0)


def ebike_flag_binary(max_age,max_distance,bike_friendly_origins,male_pct,female_pct,age_dist):
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
    
    
    age_hardcap = ipums_df['AGE']<=max_age
    dist_hardcap = ipums_df['DISTANCE_KM_TOCBD']<=max_distance
    bike_infra_locs = ipums_df['PUMA_NAME'].isin(bike_friendly_origins)
    
    ### Gender - 
    male_sex_flag = ipums_df['SEX'].apply(lambda x: True if random.random() <= male_pct/100 and x=='M' else False)
    female_sex_flag = ipums_df['SEX'].apply(lambda x: True if random.random() <= female_pct/100 and x=='F' else False)
    sex_flag = male_sex_flag|female_sex_flag

    
    ### Age - TBD if we use an age distribution or buckets
    final_series = age_hardcap&dist_hardcap&bike_infra_locs&sex_flag
    
    return final_series.astype(int)
    
    
    
    
def wfh_flag_binary(overall_wfh_pct):
    '''  
    Changable inputs:
    overall_wfh_pct
    
        
    output:
    series (0,1) indicating whether each line is a likely WFH candidate
    '''
    education_factor = 1.73 #3x more likely with bachelor degree or above (from constraints research)
    income_factor_150k=1.42 #2x more likely with 150K or more in income (from constraints research)
    # these are rough calculations - we can refine if we can figure out appropriate weights for each educ and income bucket
    
    
    education_mult = ipums_df['EDUC_LABEL'].apply(lambda x: education_factor if x in ['College_4Year','College_5PlusYears'] 
                                                      else 1/education_factor)
    income_mult = ipums_df['TOTAL_PERSONAL_INCOME'].apply(lambda x: income_factor_150k if x >=150000 
                                                      else 1/income_factor_150k)
    line_prob = overall_wfh_pct*education_mult*income_mult
    
    # grab a random number, if less than prob, WFH flag, else no flag
    line_prob.apply(lambda x: 1 if random.random() <= x else 0)

    
    final_series = line_prob.apply(lambda x: 1 if random.random() <= x else 0)
    
    return final_series.astype(int)
    
########################    
#### How to Run ########
########################
ipums_df['FLAG_EBIKE']=ebike_flag_binary(max_age=70
                                        ,max_distance = 24
                                        ,male_pct = 100
                                        ,female_pct = 100
                                        ,age_dist = None
                                        ,bike_friendly_origins=bike_friendly_origins
                                        )

ipums_df["FLAG_WFH"]=wfh_flag_binary(overall_wfh_pct=0.2)

######################    
###### CHECKS ########
######################

check_df = ipums_df[ipums_df['YEAR']==2019].copy() #just to make checks simpler
### population by ebike flag
check_df.groupby(by=['YEAR','FLAG_EBIKE']).agg({"PERWT":"sum"})

### population by wfh flag
check_df.groupby(by=['YEAR','FLAG_WFH']).agg({"PERWT":"sum"})

### education by wfh flag
wfh_by_edu = check_df.groupby(['YEAR',"FLAG_WFH",'EDUC_LABEL']).agg({"PERWT":"sum"}).reset_index()\
.pivot_table(index='EDUC_LABEL',columns='FLAG_WFH',values='PERWT')
wfh_by_edu.divide(wfh_by_edu.sum(axis=1),axis=0)
wfh_by_edu

### cross-tabs of the 2 flags
ct = check_df.groupby(['YEAR',"FLAG_WFH",'FLAG_EBIKE']).agg({"PERWT":"sum"})\
.reset_index().pivot_table(index='FLAG_EBIKE',columns='FLAG_WFH',values='PERWT')
ct / ct.sum().sum(), ct