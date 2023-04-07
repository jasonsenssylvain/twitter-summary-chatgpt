from datetime import datetime, timedelta
import csv
import json
import openai
import requests
import os
import re
import tiktoken

from scraper import Scraper
from email_sender import EmailSender


def read_config_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config

config_path = "config.json"
config_data = read_config_file(config_path)

# 设置 OpenAI API 认证信息
openai.api_key = config_data['openai_api_key']

today = datetime.now()  # 获取当前日期和时间
yesterday = today - timedelta(days=1)  # 从当前日期减去一天
yesterday_date = yesterday.strftime("%Y-%m-%d")
# yesterday_date = '2023-04-03'

print(config_data['tweet_accounts'])

date_tweets = []
top_tweets = []

scraper = Scraper()
headers = ["author", "tweet_url", "posted_time", "content", "external_link", "images"]

def get_tweet_2_csv(username, date, num_of_tweet):
  tweets = scraper.scrape_tweets(username, date, num_of_tweet)
  with open("./outputs/" + username + "_" + date + ".csv", "w", encoding="utf-8", newline="") as csvfile:
      csv_writer = csv.writer(csvfile)
      csv_writer.writerow(headers)
      csv_writer.writerows(tweets)
      
def get_tweet_popular_2_csv(file_location_name):
  tweets = scraper.search_popular_tweets(config_data['focus'])
  with open(file_location_name, "w", encoding="utf-8", newline="") as csvfile:
      csv_writer = csv.writer(csvfile)
      csv_writer.writerow(headers)
      csv_writer.writerows(tweets)
     
   
def read_info_from_csv(file_location_name):
  data = []
  # 读取CSV文件内容
  with open(file_location_name, "r", newline="", encoding='utf-8') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    csv_origin_rows = [row for row in csv_reader]
    for i in range(len(csv_origin_rows)):
      origin_row = csv_origin_rows[i]
      new_row = {
        "content": origin_row['content'],
        "author": origin_row['author'],
      }
      
      if len(new_row['content']) > 30:
        # data.append(row)
        json_data = json.dumps(new_row, ensure_ascii=False, indent=2)
        data_pack = {
          "json_data": json_data,
          "origin_row": origin_row
        }
        # print(data_pack)
        data.append(data_pack)
  return data



def get_user_tweets():
  data_list = []
  # 读取每个tweet account对应的csv文件，如果文件行数存在，则读取进来，并且按照key value的格式 转换为 json 字符串
  for username in config_data['tweet_accounts']:
    file_name = "./outputs/" + username + "_" + yesterday_date + ".csv"
    # 先判断文件存不存在 如果不存在，则抓取数据
    if os.path.exists(file_name) == False:
      get_tweet_2_csv(username, yesterday_date, 30)
    
    if os.path.exists(file_name):
      list = read_info_from_csv(file_name)
      data_list = data_list + list
  return data_list
  
def get_top_tweets():
  # 读取热门的tweet
  # 获取当前时间
  now = datetime.now()
  data_list = []

  # 格式化时间字符串
  time_string = now.strftime("%Y-%m-%d %H")
  file_name = "./outputs/top_" + time_string + ".csv"
  
  if os.path.exists(file_name) == False:
    get_tweet_popular_2_csv(file_name)

  if os.path.exists(file_name):
    list = read_info_from_csv(file_name)
    data_list = data_list + list
    
  return data_list

date_tweets = get_user_tweets()
top_tweets = get_top_tweets()

# print("date_tweets: \n\n\n\n", date_tweets)
# print("\n\n\n\n\n\n\n")
# print("top_tweets: \n\n\n\n", top_tweets)


enc = tiktoken.encoding_for_model("gpt-3.5-turbo-0301")
# 提炼重要的资讯
def get_summary(data_content):

  prompt = config_data['system_prompt'] + data_content
  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages = [
      {"role": "system", "content": config_data['sytem_role']},
      {"role": "user", "content": prompt}
    ]
  )
  
  print("prompt: \n")
  print(prompt)

  summary = response.choices[0].message.content
  return summary

def ask_openai(tweets):
  all_tweets = [] # 用来存储本次要发送的内容
  for user_data in tweets:
    json_data = user_data['json_data']
    origin_row = user_data['origin_row']
    
    if len(all_tweets) == 0:
      data = {
        "json_data": json_data,
        "origin_rows": [origin_row],
        "answer": ""
      }
      all_tweets.append(data)
    else:
      curr_tweet = all_tweets[-1]
      future_data = curr_tweet['json_data'] + "\n" + json_data
      
      dataList = enc.encode(future_data)
      
      if len(dataList) > 3800: # 一次最多3500个字符，超过了就要分开发送
        data = {
          "json_data": json_data,
          "origin_rows": [origin_row],
          "answer": ""
        }
        all_tweets.append(data)
      else:
        curr_tweet['json_data'] = future_data
        curr_tweet['origin_rows'].append(origin_row)
        all_tweets[-1] = curr_tweet
        
  # 打包完毕，可以一个一个发送出去了
  for all_tweet in all_tweets:
    summary = get_summary(all_tweet['json_data'])
    # print(summary)
    # print(all_tweet)
    # print("\n\n\n\n\n\n\n\n\n")
    all_tweet['answer'] = summary
  return all_tweets
  
date_tweets_answers = ask_openai(date_tweets)
top_tweets_answers = ask_openai(top_tweets)

# print("\n\n\n\n\n\n\n\n\n")
# print(date_tweets_answers)
# print("\n\n\n\n\n\n\n\n\n")
# print(top_tweets_answers)

def parse_rows_2_html(origin_rows):
  table = "<table border='1'>"
  # 添加表头
  table += "<tr>"
  for column in headers:
    table += f"<th>{column}</th>"
  table += "</tr>"
  # 添加数据
  for row in origin_rows:
    table += "<tr>"
    for key, value in row.items():
      table += f"<td>{value}</td>"
    table += "</tr>"
  table += "</table>"
  return table
  

# 用html邮件的形式，发送出去

html_content = f"<h1>{config_data['focus']}关注资讯汇总</h1><br/>"

if len(date_tweets_answers) == 1:
  html_content = html_content + date_tweets_answers[0]['answer'].replace('\n', '<br />') + "<br/>"
  html_content += parse_rows_2_html(date_tweets_answers[0]['origin_rows'])
elif len(date_tweets_answers) > 1:
  html_content = f"<h3>总共{len(date_tweets_answers)}份资讯</h3><br/>"
  for date_tweet in date_tweets_answers:
    html_content = html_content + date_tweet['answer'].replace('\n', '<br />') + "<br/>"
    html_content += parse_rows_2_html(date_tweet['origin_rows'])
    html_content += "<br/><br/>"
    
html_content += "<br/><br/>"
html_content += f"<h1>今日{config_data['focus']}热门资讯汇总</h1><br/>"

if len(top_tweets_answers) == 1:
  html_content = html_content + top_tweets_answers[0]['answer'].replace('\n', '<br />') + "<br/>"
  html_content += parse_rows_2_html(top_tweets_answers[0]['origin_rows'])
elif len(top_tweets_answers) > 1:
  html_content = f"<h3>总共{len(top_tweets_answers)}份资讯</h3><br/>"
  for top_tweet in top_tweets_answers:
    html_content = html_content + top_tweet['answer'].replace('\n', '<br />') + "<br/>"
    html_content += parse_rows_2_html(top_tweet['origin_rows'])
    html_content += "<br/><br/>"
    
  
emailSender = EmailSender(config_data['email_account'], config_data['email_password'], config_data['email_receiver'])

today = datetime.now()  # 获取当前日期和时间
today_date = today.strftime("%Y-%m-%d")

emailSender.send_email(f"{config_data['focus']}资讯汇总-{today_date}", html_content)
