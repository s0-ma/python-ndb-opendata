#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas
from read_ndb_opendata import get_dataframe


# In[2]:


df = get_dataframe('第1回NDBオープンデータ', ['入院基本料等加算', '都道府県'])
df


# In[3]:


幼児加算算定回数 = df[df['診療行為'].str.contains('幼児加算')].groupby('都道府県').sum()['算定回数']
都道府県別幼児加算算定回数 = pandas.merge(df[[ '都道府県']].drop_duplicates(), 幼児加算算定回数, on='都道府県')


# In[4]:


都道府県別幼児加算算定回数


# In[ ]:




