import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

companies = ["bloombergbusiness"]

def login(page):
  username = os.getenv("INSTAGRAM_USERNAME")
  username_input = page.locator("//input[@name='username']")
  username_input.type(username)

  password = os.getenv("INSTAGRAM_PASSWORD")
  password_input = page.locator("//input[@name='password']")
  password_input.type(password)

  login_button = page.locator("//div[text()='Log in']")
  login_button.click()

  try:
    not_now_button = page.locator("//div[text()='Not Now']")
    not_now_button.click()
  except:
    pass

  try:
    turn_off_notifications_button = page.locator("//button[text()='Not Now']")
    turn_off_notifications_button.click()
  except:
    pass

def search_company(page, company):
  search_input = page.locator("//input[@placeholder='Search']")
  search_input.type(company)

  try:
    result = page.locator(f"//a[@href='/{company}/']")
    result.click()
  except:
    page.goto(f"https://www.instagram.com/{company}/")

def scrape_post(page):
  soup = BeautifulSoup(page.content(), "lxml")

  post = dict()

  description = soup.select_one("h1._aad7")
  post["description"] = description.text

  media = soup.select_one("div._aatk  img")
  is_image = True
  if media == None:
    media = soup.select_one("div._aatk  video")
    is_image = False
  post["media"] = media["src"]
  post["media_alt"] = ""
  if is_image:
    post["media_alt"] = media["alt"]
  
  num_likes = soup.select_one("span.x10wh9bi span.html-span")
  post["likes"] = format_count(num_likes.text)
  
  return post

def format_count(val):
  val = val.replace(",", "")
  try:
    index1 = -1
    if "K" in val:
      index1 = val.index("K")
    
    int_val = val
    if index1 > -1:
      main = val[ : index1]
      int_val = float(main) * 1000
    
    return int(int_val)
  except:
    return val


p = sync_playwright().start()
chromium = p.chromium # or "firefox" or "webkit".
browser = chromium.launch(headless=False, slow_mo=500)
page = browser.new_page()
page.goto("https://www.instagram.com")
login(page)

search_button = page.locator("//a[@href='#']").nth(0)
search_button.click()

posts = []
for company in companies:
  search_company(page, company)

  n = 12000
  rows = n // 3
  flag = False

  for i in range(rows):
    # if i < 2339:
    #   if i > 5:
    #     page.mouse.wheel(0, 266)
    #     continue

    row_locator = f"//div[contains(@class,'_ac7v')]"
    if i > 10:
      row_locator += "[11]"
    else:
      row_locator += f"[{i + 1}]"
    try:
      for j in range(3):
        try:
          next_post_locator = f"{row_locator}/div[contains(@class,'_aabd')][{j + 1}]"
          print(len(posts) + 1, next_post_locator)
          next_post = page.locator(next_post_locator)
          next_post.scroll_into_view_if_needed()
          next_post.click()
          if flag:
            page.evaluate(f'document.querySelector(".x1n2onr6.xzkaem6").style.display = "block";')
            flag = False
          post = scrape_post(page)

          try:
            close_button = page.locator("//div[contains(@class,'x160vmok')]")
            close_button.click(force=True)
          except:
            page.evaluate(f'document.querySelector(".x1n2onr6.xzkaem6").style.display = "none";')
            flag = True
          next_post.hover()
          
          soup = BeautifulSoup(page.content(), "lxml")

          engagement = soup.select("div._ac2d li")
          # post["likes"] = format_count(engagement[0].text)
          post["comments"] = format_count(engagement[1].text)

          posts.append(post)

          # df = pd.DataFrame([post])
        except Exception as e:
          print("error", e)            
          continue
    except:
      if i == 0:
        page.mouse.wheel(0, 500)
      else:
        page.mouse.wheel(0, 266)
      continue

# if i == 0 and j == 0:
#           df.to_csv("instagram_posts.csv", mode="a", index=False)
#         else:                
#           df.to_csv("instagram_posts.csv", mode="a", index=False, header=False)

df = pd.DataFrame(posts)
df.to_csv("instagram_posts2.csv", mode="a", index=False)




    
