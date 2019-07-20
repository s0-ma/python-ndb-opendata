#!/usr/bin/env python
# coding: utf-8

# # NDBオープンデータのダウンロード

# In[1]:


import requests
from bs4 import BeautifulSoup
import re
import os
import tqdm
from pathlib import Path
from retrying import retry


# In[2]:


sources = [
    {'name': '第1回NDBオープンデータ', 'link': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000139390.html'},
    {'name': '第2回NDBオープンデータ', 'link': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177221.html'},
    {'name': '第3回NDBオープンデータ', 'link': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000177221_00002.html'},
]


# In[3]:


def download_ndb_data(source):
    res = requests.get(source['link'])
    assert res.ok
    soup = BeautifulSoup(res.text)

    def criteria(tag):
        return (tag.name in ('h3', 'h4') or 
                (tag.has_attr('href') and re.compile('\.(pdf|xlsx)$').search(tag['href'])))

    targets = soup.find_all(criteria)

    pwd = Path('.')
      
    保存先ディレクトリ名 = source['name']
    if not os.path.exists(pwd/保存先ディレクトリ名): 
        os.mkdir(pwd/保存先ディレクトリ名)
    
    @retry(stop_max_attempt_number=4, wait_exponential_multiplier=1000)
    def download_file(url, filename):
        r = requests.get(url, stream=True)
        assert r.ok
        with open(filename, 'wb') as f:
            f.write(r.content)

    h3, h4 = '',''
    for i in tqdm.tqdm_notebook(targets):
        if i.name == 'h3':
            h3 = i.text + '_'
            h4 = ''
        elif i.name == 'h4':
            h4 = i.text + '_'
        else:
            link = 'https://www.mhlw.go.jp'+i['href']
            original_filename = Path(i['href'])
            name = i.text
            save_filename = pwd / 保存先ディレクトリ名 / (original_filename.stem+'_'+h3+h4+name+original_filename.suffix)
            download_file(link, save_filename)
        


# In[4]:


for source in sources: download_ndb_data(source)

