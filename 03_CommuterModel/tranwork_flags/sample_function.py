import pandas as pd

ipums_df = pd.read_csv("disaggregated_cleaned_ipums_data.csv",index_col=0)

def ebike_flag_binary(max_age,max_distance,max_income,min_income):
    
    '''
    soft inputs:
    age - can go above 70
    
    hard inputs:
    distance -- cannot go above 25 KM
    
    outputs:
    series
    
    '''
    #create filters
    age_filter = ipums_df['AGE']<=max_age
    dist_filter = ipums_df['DISTANCE_KM_TOCBD']<=max_distance

    # use booleans to filter as necessary
    flag_ebike_series = age_filter&dist_filter

    # returns series with 0's and 1's (0=False, 1=True)
    return flag_ebike_series.astype(int)



#### If you want to see how many people fall in your series - do it by year and sum PERWT
### Income not used here, 5&5 are placeholders
ipums_df['FLAG_EBIKE']=ebike_flag_binary(70,25,5,5)
ipums_df.groupby(by=['YEAR','FLAG_EBIKE']).agg({"PERWT":"sum"})