import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import gc


#   FETCHING 

calendar =  pd.read_csv('calendar.csv')                           
sales =  pd.read_csv('sales_train_evaluation.csv')
prices =  pd.read_csv('sell_prices.csv')
sample_submission_df =  pd.read_csv('sample_submission.csv')


##########################################################################################################
#   DOWNCASTING 



def downcast(df):
    column = df.dtypes.index.tolist()
    types = df.dtypes.values.tolist()
    for i in range(len(types)):
        if 'int' in str(types[i]):
            if df[column[i]].min() > -128 and df[column[i]].max() < 128:
                df[column[i]] = df[column[i]].astype('int8')
            elif df[column[i]].min() > -32768 and df[column[i]].max() < 32767:
                df[column[i]] = df[column[i]].astype('int16')
            elif df[column[i]].min() > -2147483648 and df[column[i]].max() < 2147483647:
                df[column[i]] = df[column[i]].astype('int32')
            else:
                df[column[i]] = df[column[i]].astype(np.int64)
        elif 'float' in str(types[i]):
            if df[column[i]].min() > np.finfo('float16').min and df[column[i]].max() < np.finfo('float16').max:
                df[column[i]] = df[column[i]].astype('float16')
            elif df[column[i]].min() > np.finfo('float32').min and df[column[i]].max() < np.finfo('float32').max:
                df[column[i]] = df[column[i]].astype('float32')
            else:
                df[column[i]] = df[column[i]].astype('float64')
        elif types[i] == np.object:
            if column[i] == 'date':
                df[column[i]] = pd.to_datetime(df[column[i]], format='%Y-%m-%d')
            else:
                df[column[i]] = df[column[i]].astype('category')
    return df 

sales = downcast(sales)
prices = downcast(prices)
calendar = downcast(calendar)


##########################################################################################################
#   RESIZING AND MERGING 

df = pd.melt(sales, id_vars=['id', 'item_id', 'dept_id', 'cat_id', 'store_id','state_id'], var_name='d', value_name='sold').dropna()
df = pd.merge(df, calendar, on='d', how='left')
df = pd.merge(df, prices, on=['store_id','item_id','wm_yr_wk'], how='left') 


##########################################################################################################
#   EXPLORATORY DATA ANALYSIS (Don't run this section)


#   Below line of code will write our dataframe into a csv file which have a size of about 7 GB


#
#df.d = df['d'].apply(lambda x: x.split('_')[1]).astype(np.int16) 
#df.to_csv (r'C:\Users\Asus\Desktop\m5-forecasting-accuracy\all_states.csv', index = False, header=True)
#



#It takes about 20 min* to write on local disk and load on tableau 
#But as the data is reshaped and sorted most of the graphs required to investigate hypothesis 







##########################################################################################################
#   STATE WISE APPROACH AND CLEANING OF DATAFRAME 

df_CA = df.loc[df.state_id == 'CA']
df_TX = df.loc[df.state_id == 'TX']
df_WI = df.loc[df.state_id == 'WI']


df_CA.drop(['state_id'],axis=1,inplace=True)
df_CA.drop(['snap_TX','snap_WI'],axis=1,inplace=True)
df_CA = df_CA.rename(columns={'snap_CA':'snap'})
df_CA.snap = df_CA.snap.astype('bool')


df_TX.drop(['state_id'],axis=1,inplace=True)
df_TX.drop(['snap_CA','snap_WI'],axis=1,inplace=True)
df_TX = df_TX.rename(columns={'snap_TX':'snap'})
df_TX.snap = df_TX.snap.astype('bool')


df_WI.drop(['state_id'],axis=1,inplace=True)
df_WI.drop(['snap_CA','snap_TX'],axis=1,inplace=True)
df_WI = df_WI.rename(columns={'snap_WI':'snap'})
df_WI.snap = df_WI.snap.astype('bool')



del sales,prices,calendar,df
gc.collect()












##########################################################################################################
#   NaN values of selling prices 

df = df_CA[df_CA['sell_price'].notna()]


##########################################################################################################
#   NUMERICAL ENCODING  

df.d = df['d'].apply(lambda x: x.split('_')[1]).astype(np.int16)  #In column 'd' this line will split the str from d_1 to 1 and change datatype to int16 

d_id = dict(zip(df.id.cat.codes, df.id))
d_item_id = dict(zip(df.item_id.cat.codes, df.item_id))
d_dept_id = dict(zip(df.dept_id.cat.codes, df.dept_id))
d_cat_id = dict(zip(df.cat_id.cat.codes, df.cat_id))
d_store_id = dict(zip(df.store_id.cat.codes, df.store_id))
d_event_name_1 = dict(zip(df.event_name_1.cat.codes, df.event_name_1))
d_event_name_2 = dict(zip(df.event_name_2.cat.codes, df.event_name_2))
d_event_type_1 = dict(zip(df.event_type_1.cat.codes, df.event_type_1))
d_event_type_2 = dict(zip(df.event_type_2.cat.codes, df.event_type_2))




def cat_encoding(df):
    column = df.dtypes.index.tolist()
    types = df.dtypes.values.tolist()
    for i in range(len(types)):
        if types[i].name == "category":
            df[column[i]] = df[column[i]].cat.codes
    return df
            
df = cat_encoding(df)      








##########################################################################################################
#   FEATURE ENGINEERING 

#   LEVEL ID from the table in doc file of M5, omitted state including labels as we are analyzing state wise 

#df['item_sold_avg'] = df.groupby('item_id')['sold'].mean()  not working and assigning NaN values 
        
df['item_sold_avg'] = df.groupby('item_id')['sold'].transform('mean').astype(np.float16)
df['store_sold_avg'] = df.groupby('store_id')['sold'].transform('mean').astype(np.float16)
df['cat_sold_avg'] = df.groupby('cat_id')['sold'].transform('mean').astype(np.float16)
df['dept_sold_avg'] = df.groupby('dept_id')['sold'].transform('mean').astype(np.float16)
df['cat_dept_sold_avg'] = df.groupby(['cat_id','dept_id'])['sold'].transform('mean').astype(np.float16)
df['store_item_sold_avg'] = df.groupby(['store_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['cat_item_sold_avg'] = df.groupby(['cat_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['dept_item_sold_avg'] = df.groupby(['dept_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['store_cat_sold_avg'] = df.groupby(['store_id','cat_id'])['sold'].transform('mean').astype(np.float16)
df['store_cat_dept_sold_avg'] = df.groupby(['store_id','cat_id','dept_id'])['sold'].transform('mean').astype(np.float16)


#   LAG, ROLLING WINDOW and EXPANDING WINDOW 
#   will add more after exploring what features are required for diffrent models 

lags = [1,2,3,6,12,24,36]
for lag in lags:
    df['lag'+str(lag)] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id'],as_index=False)['sold'].shift(lag).astype(np.float16)


df['rolling_window_mean'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id'])['sold'].transform(lambda x: x.rolling(window=7).mean()).astype(np.float16)


df['expanding_window_mean'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id'])['sold'].transform(lambda x: x.expanding(2).mean()).astype(np.float16)



##########################################################################################################
#Considering the stocastic nature of ml algos I am writing the dataframe on disk and freeing the ram 

df.to_pickle('data.pkl')
del df
gc.collect();


##########################################################################################################
#   MAPE FUNCTION 


def mean_absolute_percentage_error(y_true, y_pred): 
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100



##########################################################################################################
#ENSEMBLE METHODS FOR MODELING 











x = df_CA.loc[df_CA.year == 2016]
count = x['sell_price'].isna().sum()
count









sales_CA = sales.loc[sales.state_id == 'CA']
sales_TX = sales.loc[sales.state_id == 'TX']
sales_WI = sales.loc[sales.state_id == 'WI']

sales_CA.drop(['state_id'],axis=1,inplace=True)
sales_TX.drop(['state_id'],axis=1,inplace=True)
sales_WI.drop(['state_id'],axis=1,inplace=True)


df1.drop(['snap_TX','snap_WI'],axis=1,inplace=True)
df1 = df1.rename(columns={'snap_CA':'snap'})
df1.snap = df1.snap.astype('bool')








df1.drop(['snap_TX','snap_WI'],axis=1,inplace=True)
df1 = df1.rename(columns={'snap_CA':'snap'})
df1.snap = df1.snap.astype('bool')



df2 = pd.melt(sales_TX, id_vars=['id', 'item_id', 'dept_id', 'cat_id', 'store_id'], var_name='d', value_name='sold').dropna()
df2 = pd.merge(df2, calendar, on='d', how='left')
df2 = pd.merge(df2, prices, on=['store_id','item_id','wm_yr_wk'], how='left') 
df2.drop(['snap_CA','snap_WI'],axis=1,inplace=True)
df2 = df2.rename(columns={'snap_TX':'snap'})
df2.snap = df2.snap.astype('bool')

df3 = pd.melt(sales_TX, id_vars=['id', 'item_id', 'dept_id', 'cat_id', 'store_id'], var_name='d', value_name='sold').dropna()
df3 = pd.merge(df3, calendar, on='d', how='left')
df3 = pd.merge(df3, prices, on=['store_id','item_id','wm_yr_wk'], how='left') 
df3.drop(['snap_CA','snap_TX'],axis=1,inplace=True)
df3 = df3.rename(columns={'snap_WI':'snap'})
df3.snap = df3.snap.astype('bool')

del sales, prices, calendar
gc.collect()



def basic_encoding(df):
    column_name = df.columns
    cat_dict = ()
    for i in range(len(column_name)):
        if df[column_name[i]] == 'category':
            s = 'd_'+str(column_name[i])
            s= dict(zip(df[column_name[i]].cat.codes, df[column_name[i]]))          
            df[column_name[i]] = df[column_name[i]].cat.codes
            cat_dict.append(s)
    return df,cat_dict

    

cols = df.dtypes.index.tolist()
types = df.dtypes.values.tolist()
for i,type in enumerate(types):
    if type.name == 'category':
        df[cols[i]] = df[cols[i]].cat.codes








df1.assign(weekend = 0)
df1.loc[(df1.weekday == 'Saturday') , 'weekend' ] = 1
df1.loc[(df1.weekday == 'Sunday') , 'weekend' ] = 1
df1.weekend = df1.weekend.astype('bool')






d_id = dict(zip(df.id.cat.codes, df.id))
d_item_id = dict(zip(df.item_id.cat.codes, df.item_id))
d_dept_id = dict(zip(df.dept_id.cat.codes, df.dept_id))
d_cat_id = dict(zip(df.cat_id.cat.codes, df.cat_id))
d_store_id = dict(zip(df.store_id.cat.codes, df.store_id))
#add event names in dict


df.d = df['d'].apply(lambda x: x.split('_')[1]).astype(np.int16)
cols = df.dtypes.index.tolist()
types = df.dtypes.values.tolist()
for i,type in enumerate(types):
    if type.name == 'category':
        df[cols[i]] = df[cols[i]].cat.codes
        
#3
df.drop('date',axis=1,inplace=True)

lags = [1,2,3,6,12,24,36]
for lag in lags:
    df['sold_lag_'+str(lag)] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id'],as_index=False)['sold'].shift(lag).astype(np.float16)

df['item_sold_avg'] = df.groupby('item_id')['sold'].transform('mean').astype(np.float16)
df['state_sold_avg'] = df.groupby('state_id')['sold'].transform('mean').astype(np.float16)
df['store_sold_avg'] = df.groupby('store_id')['sold'].transform('mean').astype(np.float16)
df['cat_sold_avg'] = df.groupby('cat_id')['sold'].transform('mean').astype(np.float16)
df['dept_sold_avg'] = df.groupby('dept_id')['sold'].transform('mean').astype(np.float16)
df['cat_dept_sold_avg'] = df.groupby(['cat_id','dept_id'])['sold'].transform('mean').astype(np.float16)
df['store_item_sold_avg'] = df.groupby(['store_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['cat_item_sold_avg'] = df.groupby(['cat_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['dept_item_sold_avg'] = df.groupby(['dept_id','item_id'])['sold'].transform('mean').astype(np.float16)
df['state_store_sold_avg'] = df.groupby(['state_id','store_id'])['sold'].transform('mean').astype(np.float16)
df['state_store_cat_sold_avg'] = df.groupby(['state_id','store_id','cat_id'])['sold'].transform('mean').astype(np.float16)
df['store_cat_dept_sold_avg'] = df.groupby(['store_id','cat_id','dept_id'])['sold'].transform('mean').astype(np.float16)


df['rolling_sold_mean'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id'])['sold'].transform(lambda x: x.rolling(window=7).mean()).astype(np.float16)

df['expanding_sold_mean'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id'])['sold'].transform(lambda x: x.expanding(2).mean()).astype(np.float16)

df['daily_avg_sold'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id','d'])['sold'].transform('mean').astype(np.float16)
df['avg_sold'] = df.groupby(['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id'])['sold'].transform('mean').astype(np.float16)
df['selling_trend'] = (df['daily_avg_sold'] - df['avg_sold']).astype(np.float16)
df.drop(['daily_avg_sold','avg_sold'],axis=1,inplace=True)



df = df[df['d']>=36]


