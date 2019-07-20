#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
import os
import re
import pandas
import numpy as np


# In[2]:


'''メモ：次のようなデータがあります。'''
sources = ['dummy','第1回NDBオープンデータ', '第2回NDBオープンデータ', '第3回NDBオープンデータ']
大分類 = ['医科診療行為', '歯科傷病', '特定健診', '薬剤']
医科診療行為_中分類 = ['基本診療料', '医学管理等', '在宅医療', '検査', '画像診断', 'リハビリテーション', 
              '精神科専門療法', '処置', '手術', '麻酔', '放射線治療', '病理診断']


# In[3]:


def get_datafile(source, criteria):
    pwd = Path('.')
    assert (pwd / source).exists()
    
    criteria_re = re.compile('.*'.join(criteria))
    search_result = [x for x in (pwd/source).iterdir() if criteria_re.search(str(x))]
    
    if len(search_result) == 0:
        raise FileNotFoundError('No file found')
    elif len(search_result) >= 2:
        raise FileNotFoundError('Ambiguous criteria: {0} files found.\n{1}'.format(len(search_result), '\n'.join([str(x) for x in search_result])))
    else:
        return search_result[0]
    
    
    
# get_datafile('第1回NDBオープンデータ', ['医科', '基本診療料', '初', '都道府県'])


# In[4]:


# NDBオープンデータを "Tidy data" に変換して返す。
# Tidy data については次などを参照： http://dx.doi.org/10.18637/jss.v059.i10

def decide_value_name(datafile):
    check_list = ['算定回数', '傷病件数', '数量']
    for i in check_list:
        if i in str(datafile): return i
    raise KeyError

def get_dataframes(source, criteria):
    datafile = get_datafile(source, criteria)
    
    if '医科診療行為' in str(datafile) or '歯科傷病' in str(datafile) or '薬剤' in str(datafile):
        dict_of_df = pandas.read_excel(
            datafile,
            header=[2,3],
            sheet_name=None  # 全シートを Ordererd Dict の形で取得する。
        )
        if '都道府県別' in str(datafile):
            value_name = decide_value_name(datafile)
            for key in dict_of_df:
                dict_of_df[key] = dict_of_df[key].replace('-', 0).fillna(method='ffill')                 .rename(columns=lambda x: '' if 'Unnamed' in str(x) else x)
                dict_of_df[key] = dict_of_df[key]                 .melt(
                    id_vars=[x for x in dict_of_df[key].columns.tolist() if x[1] == ''] ,
                    value_vars=[x for x in dict_of_df[key].columns.tolist() if x[1] != ''] ,
                    var_name=[('都道府県コード',), ('都道府県',)],
                    value_name=value_name ) \
                .rename(columns=lambda x: (x[0].replace('\n','') if type(x) is tuple else x ))
            return dict_of_df
    
        elif '性年齢別' in str(datafile):
            value_name = decide_value_name(datafile)
            for key in dict_of_df:
                dict_of_df[key] = dict_of_df[key].replace('-', 0).fillna(method='ffill')                 .melt(
                    id_vars=[x for x in dict_of_df[key].columns.tolist() if x[0] not in ('男性', '女性')] ,
                    value_vars=[x for x in dict_of_df[key].columns.tolist() if x[0] in ('男性', '女性')],
                    var_name=['性別', '年齢'],
                    value_name= value_name) \
                    .rename(columns=lambda x: x[0] if 'Unnamed' in str(x[1]) else x) \
                    .rename(columns=lambda x: x.replace('\n', ''))
            return dict_of_df
        
    elif '特定健診' in str(datafile):
        if 'ヘモグロビン' in str(datafile):
            header = pandas.read_excel(
                datafile,
                nrows=4,
                sheet_name=None
            )
            dict_of_df = pandas.read_excel(
                datafile,
                header=4,
                sheet_name=None
            )
            dfs = []
            for key in header:
                for df_num in range(2):
                    hdr = np.split(header[key], [10], axis=1)[df_num].ffill(axis=1).iloc[[0,2]].applymap(lambda x: str(x).replace('\n','') if str(x) != 'nan' else '')
                    df = np.split(dict_of_df[key], [10], axis=1)[df_num].replace('-', 0).fillna(method='ffill')
                    df.columns = pandas.MultiIndex.from_arrays(hdr.to_numpy())
                    df = df.melt(                    
                        id_vars=[x for x in df.columns.tolist() if x[0] not in ('男', '女')],
                        value_vars=[x for x in df.columns.tolist() if x[0] in ('男', '女')],
                        var_name=['性別', '年齢'],
                        value_name= '人数')
                    df = df.rename(columns= lambda x: x[0] if type(x) is tuple else x)
                    dfs.append(df)
            return pandas.concat(dfs)
        
        else:
            dict_of_df = pandas.read_excel(
                datafile,
                header=[1,2,3,4],
                sheet_name=None  # 全シートを Ordererd Dict の形で取得する。
            )
            for key in dict_of_df:
                dict_of_df[key] = dict_of_df[key]                                                 .replace('-', 0).fillna(method='ffill')                     .melt(
                    id_vars=[x for x in dict_of_df[key].columns.tolist() if x[1] not in ('男', '女')],
                    value_vars=[x for x in dict_of_df[key].columns.tolist() if x[1] in ('男', '女')],
                    var_name=['範囲', '性別', '年齢', '単位'],
                    value_name= '人数') \
                    .rename(columns= lambda x: x[0] if type(x) is tuple else x) \
                    .rename(columns= lambda x: x.replace('\n', "")) \
                    .drop(['範囲', '単位'], axis=1)
                dict_of_df[key] = dict_of_df[key][~dict_of_df[key].loc[:, dict_of_df[key].columns.str.startswith('検査値階層')].iloc[:, 0].str.contains('再掲')] 
            return dict_of_df
            
        
    raise NotImplementedError('Sorry, that functionality is not implemented yet.')


# In[5]:


from collections import OrderedDict
def get_dataframe(source, criteria):
    dict_of_df = get_dataframes(source, criteria)
    if type(dict_of_df) is pandas.DataFrame:
        return dict_of_df
    elif type(dict_of_df) is OrderedDict:
        first = True
        for key in dict_of_df:
            if first:
                df = dict_of_df[key]
                df['Sheet'] = key
                first = False
            else:
                df2 = dict_of_df[key]
                df2['Sheet'] = key
                df = pandas.concat([df, df2])
        return df
        


# In[10]:


# get_dataframe('第1回NDBオープンデータ', ['特定健診', '受診時年齢', 'GPT'])


# In[ ]:




