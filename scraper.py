from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from typing import Union
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dateutil.parser import parse
import time
import re

logger = logging.getLogger(__name__)
format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(format)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

class Scraper:
  def __init__(self) -> None:
    self.driver = Scraper.prepare_driver()
    
  def find_all_tweets(self, driver) -> list:
    """finds all tweets from the page"""
    try:
      return driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
    except Exception as ex:
      logger.exception(
        "Error at method fetch_all_tweets : {}".format(ex))
      return []
    
  def find_status(self, tweet) -> str:
    """finds status and link from the tweet"""
    try:
      anchor = tweet.find_element(
        By.CSS_SELECTOR, "a[aria-label][dir]")
      return anchor.get_attribute("href")
    except Exception as ex:
      logger.exception("Error at method find_status : {}".format(ex))
      return ""
    
  def find_timestamp(self, tweet) -> Union[str, None]:
    """finds timestamp from the tweet"""
    try:
      timestamp = tweet.find_element(By.TAG_NAME,
          "time").get_attribute("datetime")
      posted_time = parse(timestamp).isoformat()
      return posted_time
    except Exception as ex:
      logger.exception("Error at method find_timestamp : {}".format(ex))
      return ""
      
  def find_content(self, tweet) -> Union[str, None]:
    try:
      #content_element = tweet.find_element('.//*[@dir="auto"]')[4]
      content_element = tweet.find_element(By.CSS_SELECTOR, 'div[lang]')
      return content_element.text
    except NoSuchElementException:
      return ""
    except Exception as ex:
      logger.exception("Error at method find_content : {}".format(ex))
    
  def find_external_link(self, tweet) -> Union[str, None]:
    """finds external link from the tweet"""
    try:
      card = tweet.find_element(
          By.CSS_SELECTOR, '[data-testid="card.wrapper"]')
      href = card.find_element(By.TAG_NAME, 'a')
      return href.get_attribute("href")
    except NoSuchElementException:
      return ""
    except Exception as ex:
      logger.exception(
          "Error at method find_external_link : {}".format(ex))
            
  def find_images(self, tweet) -> Union[list, None]:
    """finds all images of the tweet"""
    try:
      image_element = tweet.find_elements(By.CSS_SELECTOR,
                                          'div[data-testid="tweetPhoto"]')
      images = []
      for image_div in image_element:
        href = image_div.find_element(By.TAG_NAME,
                                      "img").get_attribute("src")
        images.append(href)
      return images
    except Exception as ex:
      logger.exception("Error at method find_images : {}".format(ex))
      return []
    
  def find_username(self, tweet) -> Union[str, None]:
    try:
      content_elements = tweet.find_elements(By.CSS_SELECTOR,
                                          'div[data-testid="User-Name"]')
      # author = tweet.find_element_by_xpath('.//span[@class="css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"]')
      for content_element in content_elements:
        inner_span = content_element.find_element(By.XPATH, './/span[not(./*)]')
        span_text = inner_span.text
        return span_text
      return ""
    except NoSuchElementException:
      return ""
    except Exception as ex:
      logger.exception(
          "Error at method find_element_by_xpath : {}".format(ex))
    
  def scrape_tweets(self, username: str, match_date: str, num_tweets: int = 20) -> list:
    url = f"https://twitter.com/{username}"
    logger.info(f"URL {url}")
    
    self.driver.get(url)
    
    logger.info(f"URL {url} loading........")
    wait = WebDriverWait(self.driver, 10)
    
    list = self.find_currpage_tweets(self.driver, username, match_date)
    
    # 定义要滚动的次数
    scroll_times = 1

    # 滚动页面
    for _ in range(scroll_times):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # 暂停几秒，等待页面加载新的推文
        list1 = self.find_currpage_tweets(self.driver, username, match_date)
        list = list + list1
    return list

  def tweet_2_dict(self, tweet):
    tweet_url = self.find_status(tweet)
    posted_time = self.find_timestamp(tweet)
    content = self.find_content(tweet)
    external_link = self.find_external_link(tweet)
    images = self.find_images(tweet)
    author = self.find_username(tweet)
    
    if posted_time == "":
      return None
    
    tweet_date = posted_time.split("T")[0]
    
    data = {
        "author": author,
        "tweet_url": tweet_url,
        "posted_time": posted_time,
        "content": content,
        "external_link": external_link,
        "images": images,
        "tweet_date": tweet_date
      }
    # logger.info(f"Tweet data: {data}")
    return data
  
  def find_currpage_tweets(self, driver, username, match_date) -> list:
    tweets = self.find_all_tweets(self.driver)
    # logger.info(f"Found {len(tweets)} tweets, tweets: {tweets}")
    
    list = []
    #遍历取得tweet的所有详细信息
    for tweet in tweets:
      data = self.tweet_2_dict(tweet)
      if data is None:
        continue
      
      # 过滤非指定日期的tweet
      tweet_date = data['tweet_date']
      if tweet_date.strip() != match_date.strip():
        continue
      
      list.append((data['author'], data['tweet_url'], data['posted_time'], data['content'], data['external_link'], data['images']))
      
    logger.info(f"Found {len(list)} tweets match the date {match_date}")
    return list
  
  def search_popular_tweets(self, focus) -> list:
    query = f"{focus}%20lang%3Aen&f=top"
    url = "https://twitter.com/search?q="
    self.driver.get(url + query)

    print("URL {} loading........".format(url + query))
    wait = WebDriverWait(self.driver, 15)

    # 定义要滚动的次数
    scroll_times = 5
    
    list = []
    # 这里不过滤日期，因为是搜索热门的，所以应该是当天的
    tweets = self.find_all_tweets(self.driver)
    print("Found {} tweets".format(len(tweets)))
    
    list1 = self._get_top_ai_tweet()
    list = list + list1
    
    # 滚动页面
    for _ in range(scroll_times):
      self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      time.sleep(5)  # 暂停几秒，等待页面加载新的推文
        
      list1 = self._get_top_ai_tweet()
      list = list + list1
    return list
  
  def _get_top_ai_tweet(self) -> list:
    # 这里不过滤日期，因为是搜索热门的，所以应该是当天的
    list = []
    tweets = self.find_all_tweets(self.driver)
    for tweet in tweets:
      data = self.tweet_2_dict(tweet)
      if data is None:
        continue
      content = data['content']
      # top_tweets 可能被污染，存在奇奇怪怪的信息
      pattern = r"(^#|.+#)[\u4e00-\u9fff]+.*资源"
      if re.match(pattern, content):
        continue
      
      # 匹配中文字符的范围：\u4e00-\u9fff
      # 匹配日语假名字符的范围：\u3040-\u309f（平假名）和\u30a0-\u30ff（片假名）
      # 匹配韩语字符的范围：\uac00-\ud7a3
      pattern2 = re.compile("[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7a3]")
      match2 = pattern2.search(content)
      if match2:
        continue
      
      # print("Found content: {}\n\n".format(content))
      list.append((data['author'], data['tweet_url'], data['posted_time'], data['content'], data['external_link'], data['images']))
    return list
      
  
  @staticmethod
  def prepare_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36' 
    
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--allow-insecure-localhost')
  
    
    driver = webdriver.Chrome(options=chrome_options)
    # driver.scopes = [r'.*twitter[.]com.*']
    return driver