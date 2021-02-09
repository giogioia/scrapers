#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 15:36:04 2021

@author: giovanni.scognamiglio
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

df_prods = pd.DataFrame(columns=['category_name','subcategory_name','product_name','product_brand','full_name','product_description','product_thumbnail','product_price'])


url = 'https://api.everli.com/sm/api/v3/locations/11303/stores/3231/categories/tree'
headers ={
    'Authorization': 'Bearer 6d6546714d534e6e74624c345569305076505555', 
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
r = requests.get(url, headers = headers)
r
r.content
r.json()
tree = r.json()['data']['menu'][1]['items']
tree[0]['branch'][0]["link"]

for main_branch in tree:
    for branch in main_branch['branch']:
        url = f'https://api.everli.com/sm/api/v3/{branch["link"][2:]}?skip=0&take=40'
        r = requests.get(url, headers = headers)
        products_list = r.json()['data']['body'][1]['list']
        for product in products_list:
            try: 
                df_prods.loc[0 if pd.isnull(df_prods.index.max()) else df_prods.index.max() + 1] =  [main_branch['name'],branch['name'],product['tracking'][0]['data']['product_name'],product['tracking'][0]['data']['product_brand'], product['name'],product['description'], product['thumbnail'],product['price']]
            except KeyError: 
                print(product,'\n not added')
                pass
df_prods.to_excel('everly_products.xlsx')

