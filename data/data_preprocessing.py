import pandas as pd
import numpy as np
from datetime import date

cases_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
mask_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/mask-use/mask-use-by-county.csv'

def cases_preprocess(raw_url):
    cases = pd.read_csv(raw_url,infer_datetime_format=True).dropna()
    cases['fips'] = cases['fips'].astype(int)
    cases['date'] = pd.to_datetime(cases['date'])
    cases = cases.sort_values(by='date')
    grp_obj = cases.groupby(['fips'])
    county_df = dict()
    for i in cases['fips'].unique():
        county_df[i] = grp_obj.get_group(i).sort_values(by='date')
        county_df[i] = grp_obj.get_group(i).set_index('date',drop=True)
        county_df[i]['daily_cases'] = county_df[i]['cases'].diff()
        county_df[i]['increase in cases'] = county_df[i]['cases'].pct_change(14,freq='D')
        county_df[i].fillna(0)

    cases_final_df = pd.concat([county_df[k].tail(1) for k in county_df.keys()])
    cases_final_df['total_infected'] = cases_final_df['daily_cases']+cases_final_df['daily_cases']*0.4*0.75
    print('cases_preprocessed')
    return cases_final_df

def rt_exc(df):
    grp_obj_new = df.groupby('fips')
    median_max = grp_obj_new.max()['increase in cases'].median()
    def rt_cal(row):
        if row['increase in cases']>=median_max:
            return np.float64(1.8)
        elif row['increase in cases']>0 and row['increase in cases']<median_max:
            return np.float64(1.2)
        elif row['increase in cases']==0:
            return np.float64(1)
        elif row['increase in cases']<0:
            return np.float64(0.565)

    df['rt'] = df.apply(rt_cal,axis=1)
    df['max_people_at_risk'] = round(df['total_infected']*df['rt']).abs()
    print('Rt Calculated')
    return df.fillna(0)

def final_func():
    lat_lon = pd.read_csv('lat_lon_counties.csv',thousands=',')
    masks = pd.read_csv(mask_url).dropna()
    df = rt_exc(cases_preprocess(cases_url))
    fips_list = lat_lon['FIPS '].astype(int).unique()
    df = df[df['fips'].isin(fips_list)]

    df['fips'] = df['fips'].apply(lambda x: int(str(int(x)).zfill(5)))
    lat_lon['FIPS '] = lat_lon['FIPS '].apply(lambda x: int(str(int(x)).zfill(5)))
    masks['COUNTYFP'] = masks['COUNTYFP'].apply(lambda x: int(str(int(x)).zfill(5)))

    masks_mapping = dict(masks[['COUNTYFP','NEVER']].values)
    risk_mapping = dict(df[['fips','max_people_at_risk']].values)
    lat_lon['NEVER MASK']=lat_lon['FIPS '].map(masks_mapping,na_action='ignore')
    lat_lon['max_risk']=lat_lon['FIPS '].map(risk_mapping,na_action='ignore')
    lat_lon.fillna(0)
    lat_lon['NEVER MASK'] = round(lat_lon['NEVER MASK']*10000)
    lat_lon['max_risk'] = round(lat_lon['max_risk'])
    #lat_lon['NEVER MASK'] = lat_lon['NEVER MASK'].astype(int)
    #lat_lon['max_risk'] = lat_lon['max_risk'].astype(int)
    lat_lon['Hover'] = lat_lon['County ']+'<br>'+'Every 10,000 People '+lat_lon['NEVER MASK'].astype(str)+' Not using Mask'+'<br>'+'Max of '+lat_lon['max_risk'].astype(str)+' People can get Infected'
    lat_lon['FIPS '] = lat_lon['FIPS '].apply(lambda x: str(x).zfill(5))
    print('As CSV saved')
    lat_lon.to_csv('final.csv')

final_func()


