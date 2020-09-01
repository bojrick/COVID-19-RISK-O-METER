# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import pandas as pd
import numpy as np
from urllib.request import urlopen
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

def rt_cal(row):
  if row['increase in cases']>=median_max:
    return np.float64(1.8)
  elif row['increase in cases']>0 and row['increase in cases']<median_max:
    return np.float64(1.2)
  elif row['increase in cases']==0:
    return np.float64(1)
  elif row['increase in cases']<0:
    return np.float64(0.565)
  #elif row['increase in cases']<=-mean_min:
    #return np.float64(0.33)

@sched.scheduled_job('interval',hour=24)
def pre_process():
    url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    cases = pd.read_csv(url,infer_datetime_format=True)
    lat_lon = pd.read_csv('lat_lon_counties.csv',thousands=',')
    masks = pd.read_csv('mask-use-by-county.csv')
    cases.dropna(inplace=True)

    lat_lon.set_index('FIPS ',inplace=True,drop=False)
    masks.set_index('COUNTYFP',inplace=True,drop=False)
    lat_lon.drop(index=[2270,46113,51515],inplace=True)
    for i in lat_lon.index:
        lat_lon.loc[i,'NEVER MASK'] = masks.loc[i,'NEVER']

    lat_lon['NEVER MASK'] = lat_lon['NEVER MASK']*100
    lat_lon['NEVER MASK'] = lat_lon['NEVER MASK'].astype(str)
    lat_lon['Hover'] = lat_lon['Hover'].str.cat(lat_lon['NEVER MASK'],sep='<br>% Population Never Use Mask')



    cases['fips'] = cases['fips'].astype(int)
#cases['fips'] = cases['fips'].apply(lambda x: int(str(int(x)).zfill(5)))
#cases = cases[cases['fips'].isin(lat_lon['FIPS '].astype(int).unique())]
    cases['date'] = pd.to_datetime(cases['date'])
    cases = cases.sort_values(by='date')
    grp_obj = cases.groupby(['fips'])
#cases['cases'].replace(0,np.nan,inplace=True)
#cases.dropna(how='all',inplace=True)



    county_df = dict()
    for i in cases['fips'].unique():
        county_df[i] = grp_obj.get_group(i).sort_values(by='date')
        county_df[i] = grp_obj.get_group(i).set_index('date',drop=False)
        county_df[i]['daily_cases'] = county_df[i]['cases'].diff()
        county_df[i]['increase in cases'] = county_df[i]['cases'].pct_change(14,freq='D')
        county_df[i].fillna(0)
    #county_df[i].replace(np.inf,np.nan,inplace=True)
    #county_df[i].dropna(inplace=True)

    final_df = pd.concat([county_df[k] for k in county_df.keys()])

#final_df = final_df[~(final_df['daily_cases'] < 0)]
    final_df['daily_cases'] = final_df['daily_cases']+final_df['daily_cases']*0.4*0.75
    grp_obj_new = final_df.groupby('fips')
    median_max = grp_obj_new.max()['increase in cases'].median()

    final_df['rt'] = final_df.apply(rt_cal,axis=1)
    final_df['max_people_at_risk'] = round(final_df['daily_cases']*final_df['rt'])

    final_df = final_df[final_df['date']=='2020-08-27'].fillna(0)
    final_df['max_people_at_risk'] = final_df['max_people_at_risk'].abs()

    final_df = final_df[final_df['fips'].isin(lat_lon['FIPS '].astype(int).unique())]

    final_df.set_index('fips',inplace=True,drop=False)

    masks.set_index('COUNTYFP',inplace=True,drop=False)

#lat_lon.drop(index=[2105,2230,2270,46113,51515],inplace=True)
    for i in lat_lon['FIPS '].unique():
        if i in masks['COUNTYFP'].unique():
            lat_lon.loc[i,'NEVER MASK'] = masks.loc[i,'NEVER']
        else:
            lat_lon.loc[i,'NEVER MASK'] = 0.0

    for i in lat_lon['FIPS '].unique():
        if i in final_df['fips'].unique():
            lat_lon.loc[i,'max_risk'] = final_df.loc[i,'max_people_at_risk']
        else:
            lat_lon.loc[i,'max_risk'] = 0.0

    lat_lon['NEVER MASK'] = lat_lon['NEVER MASK']*100
    lat_lon['NEVER MASK'] = round(lat_lon['NEVER MASK'].astype(float))
    lat_lon['NEVER MASK'] = lat_lon['NEVER MASK'].astype(int)
    lat_lon['max_risk'] = round(lat_lon['max_risk'])
    lat_lon['max_risk'] = lat_lon['max_risk'].astype(int)

#lat_lon['Hover'] = lat_lon['Hover'].str.cat(lat_lon['NEVER MASK'],sep='<br>% Population Never Use Mask')

    lat_lon['Hover'] = lat_lon['Hover']+'<br>'+'Every 100 People '+lat_lon['NEVER MASK'].astype(str)+' never uses mask'+'<br>'+'Max of '+lat_lon['max_risk'].astype(str)+' People can get Infected today'

    lat_lon['FIPS '] = lat_lon['FIPS '].apply(lambda x: str(x).zfill(5))

    lat_lon.to_csv('final.csv')
    
sched.start()

