#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 11:09:51 2021

@author: giovanni.scognamiglio
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import numpy as np

def init():
    global session, sub_soup, url_main, selection
    #get main page with categories tree
    session = requests.Session()
    session.headers.update({'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'})
    session.headers.update({'Connection': 'keep-alive'})
    selection = input('global or local?\t').lower().strip()
    if selection == 'local':
        print('local inventory scraping')
        code = input('postal code:\t')
        url_init = f'https://pamacasa.pampanorama.it/spesa-consegna-domicilio/{code}'
    else:
        print('Global inventory scraping')
        url_init = 'https://pamacasa.pampanorama.it'
    url_main = 'https://pamacasa.pampanorama.it'
    r = session.get(url_init)
    soup = BeautifulSoup(r.content, 'html.parser')
    sub_soup = soup.find('div', {'class':"main-navigation__site flex start"})
    
def load_more(loadmore_link, page, loadmore_id):
    time.sleep(1)
    url_pagination = f'{loadmore_link}?page_num={page}&page_container=1&category_id={loadmore_id}&featured_category_id=0&productsPerPage=42&params=&special_id='
    re = session.get(url_pagination)
    soup3 = BeautifulSoup(re.json()['html'], 'html.parser')
    new_soup = soup3.find('div', {'class':"product-list"})
    return new_soup
    
def is_last_page(fresh_soup):
    if fresh_soup['data-islastpage'] == 'true':
        print('last page == true')
        return True

def main():
    global df, last_page
    #create df
    df = pd.DataFrame(columns=['supercategory_name','category','subcategory_name','name','brand','icon_url','product_quantprice','price_old','price_new','price_eur'])
    mainnavigationwrap = sub_soup.find('div',{'class':"main-navigation__wrap"})
    supercat_list = list(mainnavigationwrap)
    scrape_all = input('Also scrape non-food products? [yes/no]\n')
    if scrape_all in ['yes','ye','y','si','s']:
        end = len(supercat_list)
    else:
        end = 31
    for _ in range(5,end, 2):
        supercat_name = supercat_list[_].find('span').text
        print(supercat_name)
        cat_list = list(supercat_list[_].find('div', {'class':"main-navigation__item--side-content"}))
        for o in range(1,len(cat_list),2):
            cat_name = list(list(cat_list[o])[1])[1]['title']
            cat_link = list(list(cat_list[o])[1])[1]['href']
            #url_cat = url+cat_link
            print('\t',cat_name)
            subcat_list = list(list(cat_list[o])[3])
            for p in range(1,len(subcat_list),2):
                subcat_name = list(list(subcat_list[p])[1])[1]['title']
                subcat_link = list(list(subcat_list[p])[1])[1]['href']   
                url_subcat = url_main+subcat_link
                print('\t\t',subcat_name)
                
                r2 = session.get(url_subcat)
                soup2 = BeautifulSoup(r2.content, 'html.parser')
                sub_soup2 = soup2.find('div', {'class':"product-list"})
                loadmore_link = url_main+sub_soup2['data-pagination-url']
                loadmore_id = sub_soup2['data-category-id']
                
                last_page = 'false'
                page = 1
                while True:
                    if page == 1:
                        products = sub_soup2.find_all('div', {'class':"list-item"})
                        for i in list(products):
                            prod_details = list(i.find('section', {'itemtype':"http://schema.org/Product"}).children)[1]
                            print(prod_details['data-name'],'- added')
                            df.loc[0 if pd.isnull(df.index.max()) else df.index.max() + 1]  = [ supercat_name, cat_name, subcat_name,prod_details['data-name'],prod_details['data-brand'],prod_details['data-img-src'], prod_details['data-meta'],prod_details['data-old-price'],prod_details['data-price'],prod_details['data-price-euro']]
                    else:
                        fresh_soup = load_more(loadmore_link, page, loadmore_id)
                        products = fresh_soup.find_all('div', {'class':"list-item"})
                        for i in list(products):
                            prod_details = list(i.find('section', {'itemtype':"http://schema.org/Product"}).children)[1]
                            print(prod_details['data-name'],'- added')
                            df.loc[0 if pd.isnull(df.index.max()) else df.index.max() + 1]  = [ supercat_name, cat_name, subcat_name,prod_details['data-name'],prod_details['data-brand'],prod_details['data-img-src'], prod_details['data-meta'],prod_details['data-old-price'],prod_details['data-price'],prod_details['data-price-euro']]
                        if is_last_page(fresh_soup):
                            print("last_page == 'true' : breaking loop")
                            break
                    page += 1
                    print('page:',page)
                    load_more(loadmore_link, page, loadmore_id)

def post_processing():
    global df
    df = df.join(df.product_quantprice.str.split('-',1,expand=True).rename(columns={0:'quantity', 1:'price/quantity'}))
    for i in df.index:
        if pd.isnull(df.loc[i,'price_old']) or df.loc[i,'price_old'] == '':
            df.loc[i,'price'] = float(df.loc[i,'price_new'].replace(',','.'))
        else: 
            df.loc[i,'price'] = float(df.loc[i,'price_old'][:-2].replace(',','.'))
    df.drop_duplicates(inplace = True, ignore_index = True)
    df.brand.fillna('PAM PANORAMA', inplace =True)
    df.brand.replace('','PAM PANORAMA', inplace =True)
    df.brand.replace('.','PAM PANORAMA', inplace =True)
    df.loc[:,'name'] = df.name.str.capitalize()
    df.loc[:,'brand'] = df.brand.str.upper()
    df.loc[:,['name','brand','quantity']] = df[['name','brand','quantity']].apply(lambda x: x.str.strip())
    df.loc[:,'identifier'] = [f"{str((df.loc[index_n,'name'])).lower()} - {str((df.loc[index_n,'brand'])).lower()} - {df.loc[index_n,'quantity']}" for index_n in df.index]
    date = datetime.datetime.now().strftime("%d_%m_%Y") 
    df.to_excel(f'pam_{selection}_{date}.xlsx', index=False)
    df.loc[:,['active','matchingName','priority']] = np.nan
    df_csv = df[['icon_url','name','brand','quantity','price','active','matchingName','priority','category','identifier']]
    df_csv.to_csv(f'pam_{selection}_{date}.csv', index=False)
    print('Data postprocessed')
    print('Total number of products:',len(df))

if __name__=='__main__':
    init()                              
    main()
    post_processing()
    
    
    
    
    
