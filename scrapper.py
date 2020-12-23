#!/usr/bin/env python
# coding: utf-8

# In[2]:


import argparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd 
import requests
from alpha_vantage.timeseries import TimeSeries
import datetime as datetime
import time
import sys

def scrape_data():
    #BEGINNING OF STOCK SCRAPPING
    
    #use requests to parse through top 100 stocks on RobinHood
    content = requests.get('https://robinhood.com/collections/100-most-popular')
    soup = BeautifulSoup(content.content, 'html.parser')
    #find where the stock symbols of top 100 stocks are in the html
    stock_name = (soup.find_all('span', class_= '_2fMBL180hIqVoxOuNVJgST'))
    symbol = soup.find_all('span')
    list_symbol = []

    #loop through all tags with span in it, skip over the Nones
    for i in symbol:
        if i.string != None:
            list_symbol.append(i.string)
    
    global updated_symbol
    updated_symbol=[]

    #all symbols are uppercase with 3-5 in length and no & in the character for stock symbols 
    #loop through since there are some extra information in the same html tag under span
    #setting the if statement removes strings that are not stock symbols
    for i in range(len(list_symbol)):
        if list_symbol[i].isupper() == True and len(list_symbol[i])<= 5 and '&' not in list_symbol[i]:
            updated_symbol.append(list_symbol[i])
    #some duplicates embedded within the website that need to be removed
    #sort list of stock symbols to be alphabetically 
    updated_symbol = set(updated_symbol)
    updated_symbol = sorted(list(updated_symbol))
   

    #start with the first stock that was pulled from the top 100 stocks on RobinHood
    stock_symbol = updated_symbol[0]
    #use api key through alpha_vantage to access stock information
    app = TimeSeries(key = 'RNUBTSADYXXGZCUI', output_format='pandas')
    #get daily data of the first stock alphabetically in the top 100 stocks 
    data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
    #set start data and end data of what range of dates of information I want
    start_date = datetime.datetime(2020,9,30)
    end_date = datetime.datetime(2020,11,13)
    data_oct = data[(data.index > start_date) & (data.index <= end_date)]
    data_oct = data_oct.sort_index(ascending=True)
    #drop columns of stock information unneeded, only want open and close prices of stocks that day
    stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
    #rename column names so that each column also has the stock symbol included 
    stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
    #set new information to dataframe called total_stocks
    total_stocks = stock_price
    #calculate the percent change that day for the stock from opening to close
    total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100

    #set count = 1, only 5 requests per minute and there are 100 requests since there are 100 stocks, we set a timer in the code
    #that makes code stall for 61 seconds every 5 api calls 
    counter = 1

    #loop through the top 100 robinhood stock list created earlier, starting at index 1, since index 0 was just taken care of
    for i in range(1,len(updated_symbol)):
    #add one to counter each time we loop
        counter = counter + 1
        #if counter greater than 5 we go through the 61 second hold
        if counter > 5:
            #reset counter 
            counter = 1
            #make code stop for 61 seconds
            time.sleep(61)
            #set stock symbol to the one we are currently calling and pulling information for
            stock_symbol = updated_symbol[i]
            #get daily stock data for that stock symbol in the top 100 list
            data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
            start_date = datetime.datetime(2020,9,30)
            end_date = datetime.datetime(2020,11,13)
            data_oct = data[(data.index > start_date) & (data.index <= end_date)]
            data_oct = data_oct.sort_index(ascending=True)
            stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
            stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
            #add data of new stock to the overall stock dataframe
            total_stocks = pd.concat([total_stocks,stock_price],axis = 1)
            total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100
        #if counter not at 5, don't make code wait for 61 seconds but below code same as above otherwise
        else:
            stock_symbol = updated_symbol[i]
            data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
            start_date = datetime.datetime(2020,9,30)
            end_date = datetime.datetime(2020,11,13)
            data_oct = data[(data.index > start_date) & (data.index <= end_date)]
            data_oct = data_oct.sort_index(ascending=True)
            stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
            stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
            total_stocks = pd.concat([total_stocks,stock_price],axis = 1)
            total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100
    #if you want to save this dataset
    total_stocks.to_csv('stock_info.csv')
    
    #END OF STOCK SCRAPPER
    
    #BEGINNING OF REDDIT SCRAPPER
    #setting up the webdriver below, need to have chromedriver installed and set executable path to where it's located
    option = Options()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    #options=option prevents the link being opened and parsed through actively
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)


    #link for oct 1 below
    link = "https://www.reddit.com/r/wallstreetbets/comments/j35to3/daily_discussion_thread_for_october_01_2020/?sort=top"
    #give driver the link
    driver.get(link)
    #click button using xpath of the button to load more comments
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    #xpath to click on the load more comments after the first button
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[358]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    #identified html class where comments are in
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    #loop through comment list and append each comment in the discussion post within the intial page + 2 load comments worth
    #of pages
    for comment in comments:
        comment_list.append(comment.string)
    #remove first three comments since they are standard discussion guidelines 
    comment_list = comment_list[3:]
    #turn list of comments into a pd dataframe with date as column name
    df = pd.DataFrame(comment_list,columns=['Oct 01'])
    #set the first dataframe equal to a new name that where following lists of comments will be concat to
    reddit_comments_oct = df

    #get rid of comments that are empty (deleted or people input empty in comments)
    #we are now creating a second pandas dataframe which logs if a top 100 stock from RH is mentioned that day
    comment_list_1 = [i for i in comment_list if i]
    #intialize lists 
    stocks_day = []
    #alt stock name is just stock symbol with a $ in front of it, people mention stock symbols with/without the dollar time
    #all the time
    alt_stock_name = []
    #create alternate top 100 stock symbol with dollar in front
    for i in range(0,len(updated_symbol)):
        alt_stock_name.append('$'+updated_symbol[i])
    #loop through comments
    try:
        for i in range(0,len(comment_list_1)):
            #set all the comments to upper incase someone mentioned a stock symbol in lowercase
            comment_list_1[i] = comment_list_1[i].upper()
            #split comment sowe can iterate over each word
            string_holder = comment_list_1[i].split(' ')
            #if within that comment, a stock symbol from top 100 is mentioned, add it to the stocks_day list
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            #if within that comment, a stock symbol with a $ in front of it from top 100 is mentioned, add it to the stocks_day list
            x = [value for value in string_holder if value in alt_stock_name]
            #take out the dollar sign in front before adding it back to stocks_day
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    #comments have alot of extra info such as emojis and deletions causing errors, ignore emojis 
    except AttributeError:
        pass
    #use set to get rid of duplicates
    stocks_day = list(set(stocks_day))

    #initialize dataframe of whether top 100 stocks are mentioned each day
    keyword_count = pd.DataFrame()
    #append so each stock it's own row
    keyword_count = keyword_count.append(updated_symbol, ignore_index=True)
    #set day as a column equal to 0
    keyword_count['2020-10-01'] = 0
    #if stock mentioned that day, set equal to 1, else leave it as a 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-01'] = 1


    #code below is the same as above, except each link is unique to that day's discussion 
    #xpath of each button per day is also unique hence why each day has it's own segment of code

    #oct 2 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j3rz7r/daily_discussion_thread_for_october_02_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[363]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 02'])
    #concat this day's dataframe to the overall one 
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)


    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-02'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-02'] = 1


    #oct 5 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j5guae/daily_discussion_thread_for_october_05_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[334]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 05'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)

    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-05'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-05'] = 1

    #oct 6 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j62ihd/daily_discussion_thread_for_october_06_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[355]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 06'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-06'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-06'] = 1

    #oct 7 discussion    
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j6o9s8/daily_discussion_thread_for_october_07_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[360]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 07'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-07'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-07'] = 1

    #oct 8 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j7agfu/daily_discussion_thread_for_october_08_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[363]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 08'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-08'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-08'] = 1

    #oct 9 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j7wdaz/daily_discussion_thread_for_october_09_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[362]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 09'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-09'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-09'] = 1

    #oct 12 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j9obtn/daily_discussion_thread_for_october_12_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[333]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 12'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-12'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-12'] = 1

    #oct 13 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jaaj59/daily_discussion_thread_for_october_13_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[348]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 13'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-13'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-13'] = 1

    #oct 14 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jaxxuj/daily_discussion_thread_for_october_14_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[349]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 14'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-14'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-14'] = 1

    #oct 15 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jbktdv/daily_discussion_thread_for_october_15_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[349]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 15'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-15'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-15'] = 1

    #oct 16 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jc7ao5/daily_discussion_thread_for_october_16_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[347]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 16'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-16'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-16'] = 1

    #oct 22 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jfwwhm/daily_discussion_thread_for_october_22_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[354]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 22'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-22'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-22'] = 1

    #oct 23 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jgkeqo/daily_discussion_thread_for_october_23_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[333]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 23'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-23'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-23'] = 1

    #oct 26 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jibzmg/daily_discussion_thread_for_october_26_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[350]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 26'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-26'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-26'] = 1

    #oct 27 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jiyfu2/daily_discussion_thread_for_october_27_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[325]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 27'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-27'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-27'] = 1

    #oct 28 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jjl2qm/daily_discussion_thread_for_october_28_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[348]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 28'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-28'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-28'] = 1

    #oct 29 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jk7d6g/daily_discussion_thread_for_october_29_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[342]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 29'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-29'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-29'] = 1

    #oct 30 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jku4jx/daily_discussion_thread_for_october_30_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[359]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 30'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-30'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-30'] = 1

    #nov 2 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jmkz1s/daily_discussion_thread_for_november_02_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[339]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 02'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-02'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-02'] = 1

    #nov 3 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jn7ua1/daily_discussion_thread_for_november_03_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[358]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 03'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-03'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-03'] = 1

    #nov 4 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jnu8gl/daily_discussion_thread_for_november_04_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[359]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 04'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-04'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-04'] = 1

    #nov 5 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jogc2m/daily_discussion_thread_for_november_05_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[348]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 05'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-05'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-05'] = 1

    #nov 6 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jp2nvp/daily_discussion_thread_for_november_06_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[332]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 06'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-06'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-06'] = 1

    #nov 9 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jqv478/daily_discussion_thread_for_november_09_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[341]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 09'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-09'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-09'] = 1

    #nov 10 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jriieh/daily_discussion_thread_for_november_10_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[347]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 10'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-10'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-10'] = 1

    #nov 11 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/js5m7m/daily_discussion_thread_for_november_11_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[337]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 11'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-11'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-11'] = 1

    #nov 12 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jssu2g/daily_discussion_thread_for_november_12_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[337]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 12'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-12'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-12'] = 1

    #nov 13 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/jtf81v/daily_discussion_thread_for_november_13_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[353]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Nov 13'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)
    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-11-13'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-11-13'] = 1
    #transpose dataframe
    keyword_count = keyword_count.T
    #set headers to the stock symbols
    headers = keyword_count.iloc[0]
    #get rid of first row since that is index, want to have stock symbol as the first row
    keyword_count = keyword_count[1:]
    #set stock symbols as the column names
    keyword_count.columns = headers
    #if you want to save: below code
    #reddit_comments_oct.to_csv('reddit_comments.csv')
    keyword_count.to_csv('reddit_keyword_count.csv')
    
    #END OF REDDIT SCRAPPER
    
    #BEGINNING OF COVID SCRAPPER
    
    
    #start up the webdriver
    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)
    #link equal to daily covid data 
    link = "https://covid.cdc.gov/covid-data-tracker/#trends_dailytrendscases"
    driver.get(link)
    #let driver get link, takes time to load everything in
    time.sleep(10)
    #parse through the html
    source = driver.page_source 
    #information needed is embedded within several tags so we go through each tag to get the info we want
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    #loop through to remove the aria-label in front of each piece of data we want
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    date = []
    daily_case = []
    #once list of data we want is input, split since there is a date associated with each number to just pull the date first
    for i in range(0,len(info_3),3):
        holder = info_3[i].split(' ')
        date.append(holder[1]+' ' + holder[2]+ ' '+ holder[3])
    #find the daily cases now, need to skip every 3 since data goes (date, daily information, 7-day trend)
    for i in range(1, len(info_3),3):
        holder = info_3[i].split(' ')
        daily_case.append(holder[-1])

    ##below is same approach but for the daily death data

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)  
    link = "https://covid.cdc.gov/covid-data-tracker/#trends_dailytrendsdeaths"
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    daily_death = []
    for i in range(1, len(info_3),3):
        holder = info_3[i].split(' ')
        daily_death.append(holder[-1])

    start_index = date.index('Nov 13 2020')
    end_index = date.index('Oct 1 2020')
    date = date[start_index:end_index+1]
    daily_case = daily_case[start_index:end_index+1]
    daily_death = daily_death[start_index:end_index+1]
    daily_case.reverse()
    daily_death.reverse()

    #now that daily cases and deaths have been pulled, a different part of the site also has cases/deaths 
    #by population factors(metro vs non-metro) which we also pull

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    #driver = webdriver.Chrome(executable_path ='C:/Users/anson/Desktop/chromedriver.exe', options = option)
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)
    link = "https://covid.cdc.gov/covid-data-tracker/#pop-factors_7daynewcases"
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    factor_date = []
    metro_case = []
    non_metro_case = []
    #same approach as before but here we have date, metro case, non metro case, county case which is why we skip every 4 in
    #the list to append the necessary information
    for i in range(0, len(info_3),4):
        holder = info_3[i].split(' ')
        factor_date.append(holder[-1])
    for i in range(1,len(info_3),4):
        holder = info_3[i].split(' ')
        metro_case.append(holder[-1])
    for i in range(2,len(info_3),4):
        holder = info_3[i].split(' ')
        non_metro_case.append(holder[-1])

    #find the start and end date range for the information we want
    start_index = factor_date.index('2020-10-01')
    end_index = factor_date.index('2020-11-13')
    #index the three lists with date, metro cases, non-metro cases to get the time segment of interest
    factor_date = factor_date[start_index:end_index+1]
    metro_case = metro_case[start_index:end_index+1]
    non_metro_case = non_metro_case[start_index:end_index+1]

    #below code is the same but just for deaths in metro and non metro areas

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)    
    link = 'https://covid.cdc.gov/covid-data-tracker/#pop-factors_7daynewdeaths'
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    factor_date = []
    metro_death = []
    non_metro_death = []
    for i in range(0, len(info_3),4):
        holder = info_3[i].split(' ')
        factor_date.append(holder[-1])
    for i in range(1,len(info_3),4):
        holder = info_3[i].split(' ')
        metro_death.append(holder[-1])
    for i in range(2,len(info_3),4):
        holder = info_3[i].split(' ')
        non_metro_death.append(holder[-1])

    start_index = factor_date.index('2020-10-01')
    end_index = factor_date.index('2020-11-13')
    factor_date = factor_date[start_index:end_index+1]
    metro_death = metro_death[start_index:end_index+1]
    non_metro_death = non_metro_death[start_index:end_index+1]

    covid_data = list(zip(factor_date, daily_case, daily_death, metro_case, non_metro_case, metro_death, non_metro_death))
    covid_data = pd.DataFrame(covid_data, columns = ['Date', 'Daily Case Count', 'Daily Death Count','Metro 7-Day Case Rate per 100,000', 'Non-Metro 7-Day Case Rate per 100,000', 'Metro 7-Day Death Rate per 100,000','Non-Metro 7-Day Death Rate per 100,000'])
    #if you want to save this dataset
    covid_data.to_csv('covid_data.csv')
    
    #END OF COVID SCRAPPER
    merge_data = keyword_count
    merge_data['Date'] = merge_data.index
    merge_data['Date'] = merge_data['Date'].astype(str)
    total_stocks['Date'] = total_stocks.index
    total_stocks['Date'] = total_stocks['Date'].astype(str)
    merge_data = pd.merge(merge_data,total_stocks, on= 'Date',how='left')
    merge_data = pd.merge(merge_data,covid_data, on= 'Date',how='left')
    merge_data.to_csv('merged_data.csv')
    return merge_data

def download_data():
    covid_data = pd.read_csv('covid_data.csv', index_col=[0])
    total_stocks = pd.read_csv('stock_info.csv', index_col=[0])
    keyword_count = pd.read_csv('reddit_keyword_count.csv', index_col=[0])
    merge_data = keyword_count
    merge_data['Date'] = merge_data.index
    total_stocks['Date'] = total_stocks.index
    merge_data = pd.merge(merge_data,total_stocks, on= 'Date',how='left')
    merge_data = pd.merge(merge_data,covid_data, on= 'Date',how='left')
    dates = keyword_count.index
    merge_data = merge_data.set_index(dates)
    return merge_data


def scrape_data_short():
    #BEGINNING OF STOCK SCRAPPING
    
    #use requests to parse through top 100 stocks on RobinHood
    content = requests.get('https://robinhood.com/collections/100-most-popular')
    soup = BeautifulSoup(content.content, 'html.parser')
    #find where the stock symbols of top 100 stocks are in the html
    stock_name = (soup.find_all('span', class_= '_2fMBL180hIqVoxOuNVJgST'))
    symbol = soup.find_all('span')
    list_symbol = []

    #loop through all tags with span in it, skip over the Nones
    for i in symbol:
        if i.string != None:
            list_symbol.append(i.string)
    
    global updated_symbol
    updated_symbol=[]

    #all symbols are uppercase with 3-5 in length and no & in the character for stock symbols 
    #loop through since there are some extra information in the same html tag under span
    #setting the if statement removes strings that are not stock symbols
    for i in range(len(list_symbol)):
        if list_symbol[i].isupper() == True and len(list_symbol[i])<= 5 and '&' not in list_symbol[i]:
            updated_symbol.append(list_symbol[i])
    #some duplicates embedded within the website that need to be removed
    #sort list of stock symbols to be alphabetically 
    updated_symbol = set(updated_symbol)
    updated_symbol = sorted(list(updated_symbol))
   

    #start with the first stock that was pulled from the top 100 stocks on RobinHood
    stock_symbol = updated_symbol[0]
    #use api key through alpha_vantage to access stock information
    app = TimeSeries(key = 'RNUBTSADYXXGZCUI', output_format='pandas')
    #get daily data of the first stock alphabetically in the top 100 stocks 
    data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
    #set start data and end data of what range of dates of information I want
    start_date = datetime.datetime(2020,9,30)
    end_date = datetime.datetime(2020,11,13)
    data_oct = data[(data.index > start_date) & (data.index <= end_date)]
    data_oct = data_oct.sort_index(ascending=True)
    #drop columns of stock information unneeded, only want open and close prices of stocks that day
    stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
    #rename column names so that each column also has the stock symbol included 
    stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
    #set new information to dataframe called total_stocks
    total_stocks = stock_price
    #calculate the percent change that day for the stock from opening to close
    total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100

    #set count = 1, only 5 requests per minute and there are 100 requests since there are 100 stocks, we set a timer in the code
    #that makes code stall for 61 seconds every 5 api calls 
    counter = 1

    #loop through the top 100 robinhood stock list created earlier, starting at index 1, since index 0 was just taken care of
    
    #get only the first 3 stocks' information 
    for i in range(1,3):
    #add one to counter each time we loop
        counter = counter + 1
        #if counter greater than 5 we go through the 61 second hold
        if counter > 5:
            #reset counter 
            counter = 1
            #make code stop for 61 seconds
            time.sleep(61)
            #set stock symbol to the one we are currently calling and pulling information for
            stock_symbol = updated_symbol[i]
            #get daily stock data for that stock symbol in the top 100 list
            data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
            start_date = datetime.datetime(2020,9,30)
            end_date = datetime.datetime(2020,11,13)
            data_oct = data[(data.index > start_date) & (data.index <= end_date)]
            data_oct = data_oct.sort_index(ascending=True)
            stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
            stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
            #add data of new stock to the overall stock dataframe
            total_stocks = pd.concat([total_stocks,stock_price],axis = 1)
            total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100
        #if counter not at 5, don't make code wait for 61 seconds but below code same as above otherwise
        else:
            stock_symbol = updated_symbol[i]
            data, metadata = app.get_daily_adjusted(stock_symbol, outputsize = 'full')
            start_date = datetime.datetime(2020,9,30)
            end_date = datetime.datetime(2020,11,13)
            data_oct = data[(data.index > start_date) & (data.index <= end_date)]
            data_oct = data_oct.sort_index(ascending=True)
            stock_price = data_oct.drop(data_oct.columns[[1,2,4,5,6,7]],axis = 1)
            stock_price.rename(columns = {'1. open': stock_symbol + ' open', '4. close': stock_symbol + ' close'},inplace = True)
            total_stocks = pd.concat([total_stocks,stock_price],axis = 1)
            total_stocks[stock_symbol + ' percent day change'] = ((total_stocks[stock_symbol + ' close'] - total_stocks[stock_symbol + ' open'])/abs(total_stocks[stock_symbol + ' open']))*100
    #if you want to save this dataset
    total_stocks.to_csv('stock_info_short.csv')
    
    #END OF STOCK SCRAPPER
    
    #BEGINNING OF REDDIT SCRAPPER
    #setting up the webdriver below, need to have chromedriver installed and set executable path to where it's located
    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    #options=option prevents the link being opened and parsed through actively
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)


    #link for oct 1 below
    link = "https://www.reddit.com/r/wallstreetbets/comments/j35to3/daily_discussion_thread_for_october_01_2020/?sort=top"
    #give driver the link
    driver.get(link)
    #click button using xpath of the button to load more comments
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    #xpath to click on the load more comments after the first button
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[358]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    #identified html class where comments are in
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    #loop through comment list and append each comment in the discussion post within the intial page + 2 load comments worth
    #of pages
    for comment in comments:
        comment_list.append(comment.string)
    #remove first three comments since they are standard discussion guidelines 
    comment_list = comment_list[3:]
    #turn list of comments into a pd dataframe with date as column name
    df = pd.DataFrame(comment_list,columns=['Oct 01'])
    #set the first dataframe equal to a new name that where following lists of comments will be concat to
    reddit_comments_oct = df

    #get rid of comments that are empty (deleted or people input empty in comments)
    #we are now creating a second pandas dataframe which logs if a top 100 stock from RH is mentioned that day
    comment_list_1 = [i for i in comment_list if i]
    #intialize lists 
    stocks_day = []
    #alt stock name is just stock symbol with a $ in front of it, people mention stock symbols with/without the dollar time
    #all the time
    alt_stock_name = []
    #create alternate top 100 stock symbol with dollar in front
    for i in range(0,len(updated_symbol)):
        alt_stock_name.append('$'+updated_symbol[i])
    #loop through comments
    try:
        for i in range(0,len(comment_list_1)):
            #set all the comments to upper incase someone mentioned a stock symbol in lowercase
            comment_list_1[i] = comment_list_1[i].upper()
            #split comment sowe can iterate over each word
            string_holder = comment_list_1[i].split(' ')
            #if within that comment, a stock symbol from top 100 is mentioned, add it to the stocks_day list
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            #if within that comment, a stock symbol with a $ in front of it from top 100 is mentioned, add it to the stocks_day list
            x = [value for value in string_holder if value in alt_stock_name]
            #take out the dollar sign in front before adding it back to stocks_day
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    #comments have alot of extra info such as emojis and deletions causing errors, ignore emojis 
    except AttributeError:
        pass
    #use set to get rid of duplicates
    stocks_day = list(set(stocks_day))

    #initialize dataframe of whether top 100 stocks are mentioned each day
    keyword_count = pd.DataFrame()
    #append so each stock it's own row
    keyword_count = keyword_count.append(updated_symbol, ignore_index=True)
    #set day as a column equal to 0
    keyword_count['2020-10-01'] = 0
    #if stock mentioned that day, set equal to 1, else leave it as a 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-01'] = 1


    #code below is the same as above, except each link is unique to that day's discussion 
    #xpath of each button per day is also unique hence why each day has it's own segment of code

    #oct 2 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j3rz7r/daily_discussion_thread_for_october_02_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[363]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 02'])
    #concat this day's dataframe to the overall one 
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)


    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-02'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-02'] = 1


    #oct 5 discussion
    link = 'https://www.reddit.com/r/wallstreetbets/comments/j5guae/daily_discussion_thread_for_october_05_2020/?sort=top'
    driver.get(link)
    driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/button").click()
    WebDriverWait(driver, 500).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div/div[2]/div[2]/div/div[3]/div[1]/div[2]/div[4]/div/div/div/div[334]/div/div/div[2]/p'))).click()
    html_source = driver.page_source 
    source_data = html_source.encode('utf-8')
    soup = BeautifulSoup(source_data, "lxml")
    comments = soup.find_all("p",{"class":"_1qeIAgB0cPwnLhDF9XSiJM"} )
    comment_list = []
    for comment in comments:
        comment_list.append(comment.string)
    comment_list = comment_list[3:]
    df = pd.DataFrame(comment_list,columns=['Oct 05'])
    reddit_comments_oct = pd.concat([reddit_comments_oct,df], axis=1)

    comment_list_1 = [i for i in comment_list if i]
    stocks_day = []

    try:
        for i in range(0,len(comment_list_1)):
            comment_list_1[i] = comment_list_1[i].upper()
            string_holder = comment_list_1[i].split(' ')
            x = [value for value in string_holder if value in updated_symbol]
            stocks_day.extend(x)
            x = [value for value in string_holder if value in alt_stock_name]
            for i in range(0,len(x)):
                x[i] = x[i][1:]
            stocks_day.extend(x)
    except AttributeError:
        pass
    stocks_day = list(set(stocks_day))

    keyword_count['2020-10-05'] = 0
    for stock in stocks_day:
        keyword_count.loc[keyword_count[0] == stock, '2020-10-05'] = 1
    #transpose dataframe
    keyword_count = keyword_count.T
    #set headers to the stock symbols
    headers = keyword_count.iloc[0]
    #get rid of first row since that is index, want to have stock symbol as the first row
    keyword_count = keyword_count[1:]
    #set stock symbols as the column names
    keyword_count.columns = headers
    #if you want to save: below code
    #reddit_comments_oct.to_csv('reddit_comments.csv')
    keyword_count.to_csv('reddit_keyword_count_short.csv')
    
    #END OF REDDIT SCRAPPER
    
    #BEGINNING OF COVID SCRAPPER
    
    #start up the webdriver
    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)
    #link equal to daily covid data 
    link = "https://covid.cdc.gov/covid-data-tracker/#trends_dailytrendscases"
    driver.get(link)
    #let driver get link, takes time to load everything in
    time.sleep(10)
    #parse through the html
    source = driver.page_source 
    #information needed is embedded within several tags so we go through each tag to get the info we want
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    #loop through to remove the aria-label in front of each piece of data we want
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    date = []
    daily_case = []
    #once list of data we want is input, split since there is a date associated with each number to just pull the date first
    for i in range(0,len(info_3),3):
        holder = info_3[i].split(' ')
        date.append(holder[1]+' ' + holder[2]+ ' '+ holder[3])
    #find the daily cases now, need to skip every 3 since data goes (date, daily information, 7-day trend)
    for i in range(1, len(info_3),3):
        holder = info_3[i].split(' ')
        daily_case.append(holder[-1])

    ##below is same approach but for the daily death data

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)  
    link = "https://covid.cdc.gov/covid-data-tracker/#trends_dailytrendsdeaths"
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    daily_death = []
    for i in range(1, len(info_3),3):
        holder = info_3[i].split(' ')
        daily_death.append(holder[-1])

    start_index = date.index('Nov 13 2020')
    end_index = date.index('Oct 1 2020')
    date = date[start_index:end_index+1]
    daily_case = daily_case[start_index:end_index+1]
    daily_death = daily_death[start_index:end_index+1]
    daily_case.reverse()
    daily_death.reverse()

    #now that daily cases and deaths have been pulled, a different part of the site also has cases/deaths 
    #by population factors(metro vs non-metro) which we also pull

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    #driver = webdriver.Chrome(executable_path ='C:/Users/anson/Desktop/chromedriver.exe', options = option)
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)
    link = "https://covid.cdc.gov/covid-data-tracker/#pop-factors_7daynewcases"
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    factor_date = []
    metro_case = []
    non_metro_case = []
    #same approach as before but here we have date, metro case, non metro case, county case which is why we skip every 4 in
    #the list to append the necessary information
    for i in range(0, len(info_3),4):
        holder = info_3[i].split(' ')
        factor_date.append(holder[-1])
    for i in range(1,len(info_3),4):
        holder = info_3[i].split(' ')
        metro_case.append(holder[-1])
    for i in range(2,len(info_3),4):
        holder = info_3[i].split(' ')
        non_metro_case.append(holder[-1])

    #find the start and end date range for the information we want
    start_index = factor_date.index('2020-10-01')
    end_index = factor_date.index('2020-11-13')
    #index the three lists with date, metro cases, non-metro cases to get the time segment of interest
    factor_date = factor_date[start_index:end_index+1]
    metro_case = metro_case[start_index:end_index+1]
    non_metro_case = non_metro_case[start_index:end_index+1]

    #below code is the same but just for deaths in metro and non metro areas

    option = Options()
    option.add_argument('--no-sandbox')
    option.add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(),options = option)    
    link = 'https://covid.cdc.gov/covid-data-tracker/#pop-factors_7daynewdeaths'
    driver.get(link)
    time.sleep(10)
    source = driver.page_source 
    soup = BeautifulSoup(source, 'html.parser')
    info = soup.find_all('table', class_= 'expanded-data-table')
    info_2 = soup.find_all('tr')
    info_3 = soup.find_all('td')
    info_3 = list(info_3)
    for i in range(0,len(info_3)):
        info_3[i] = info_3[i]['aria-label']
    factor_date = []
    metro_death = []
    non_metro_death = []
    for i in range(0, len(info_3),4):
        holder = info_3[i].split(' ')
        factor_date.append(holder[-1])
    for i in range(1,len(info_3),4):
        holder = info_3[i].split(' ')
        metro_death.append(holder[-1])
    for i in range(2,len(info_3),4):
        holder = info_3[i].split(' ')
        non_metro_death.append(holder[-1])

    start_index = factor_date.index('2020-10-01')
    end_index = factor_date.index('2020-11-13')
    factor_date = factor_date[start_index:end_index+1]
    metro_death = metro_death[start_index:end_index+1]
    non_metro_death = non_metro_death[start_index:end_index+1]

    covid_data = list(zip(factor_date, daily_case, daily_death, metro_case, non_metro_case, metro_death, non_metro_death))
    covid_data = pd.DataFrame(covid_data, columns = ['Date', 'Daily Case Count', 'Daily Death Count','Metro 7-Day Case Rate per 100,000', 'Non-Metro 7-Day Case Rate per 100,000', 'Metro 7-Day Death Rate per 100,000','Non-Metro 7-Day Death Rate per 100,000'])
    #if you want to save this dataset
    covid_data.to_csv('covid_data_short.csv')
    
    #END OF COVID SCRAPPER
    merge_data = keyword_count
    merge_data['Date'] = merge_data.index
    merge_data['Date'] = merge_data['Date'].astype(str)
    total_stocks['Date'] = total_stocks.index
    total_stocks['Date'] = total_stocks['Date'].astype(str)
    merge_data = pd.merge(merge_data,total_stocks, on= 'Date',how='left')
    merge_data = pd.merge(merge_data,covid_data, on= 'Date',how='left')
    merge_data.to_csv('merged_data_short.csv')
    return merge_data

def download_data_short():
    covid_data = pd.read_csv('covid_data_short.csv', index_col=[0])
    total_stocks = pd.read_csv('stock_info_short.csv', index_col=[0])
    keyword_count = pd.read_csv('reddit_keyword_count_short.csv', index_col=[0])
    merge_data = keyword_count
    merge_data['Date'] = merge_data.index
    total_stocks['Date'] = total_stocks.index
    merge_data = pd.merge(merge_data,total_stocks, on= 'Date',how='left')
    merge_data = pd.merge(merge_data,covid_data, on= 'Date',how='left')
    dates = keyword_count.index
    merge_data = merge_data.set_index(dates)
    return merge_data

def main():
    parser = argparse.ArgumentParser(description="Three commands here to obtain data. --source local to download all the data, --source remote to scrape all the data which takes up to 50 minutes, and --source remote --short to just scrape first 3 entries of the dataset")
    parser.add_argument("--source", choices=["local", "remote"])
    args, unknown = parser.parse_known_args()
    location = args.source
    entry = sys.argv
    if location == "local":
        output_data = download_data()
        print('Data read in locally from saved files')
    elif location == "remote" and len(entry) < 2:
        output_data = scrape_data()
        print('All data scrapped remotely')
    elif location == "remote" and entry[3] == "--short":
        output_data = scrape_data_short()
        print('First 3 entries of dataset scrapped')
    else:
        print("Please input one of the three lines of code in the command prompt: python scrapper.py --source local, python scrapper.py --source remote, or python scrapper.py --source remote --short")
if __name__ == "__main__":
    main()

# %%
