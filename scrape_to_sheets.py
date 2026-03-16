import os
import time
import re
import datetime
import gspread
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2.service_account import Credentials

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    # Use the driver path established in the environment
    service = Service(executable_path='/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=options)

def scrape_youtube_views(driver, url):
    try:
        print(f'Scraping: {url}')
        driver.get(url)
        time.sleep(25)  # Wait for dynamic content to load
        src = driver.page_source
        # Verified regex pattern for viewCount
        pattern = r'"viewCount":"(\d+)"'
        match = re.search(pattern, src)
        if match:
            return int(match.group(1))
        # Fallback pattern
        fallback = re.search(r'>([\d,]+) views<', src)
        if fallback:
            return int(fallback.group(1).replace(',', ''))
        return None
    except Exception as e:
        print(f'Error on {url}: {e}')
        return None

def run_automation():
    # 1. Target URLs
    target_urls = [
        'https://www.youtube.com/@flipkart/about',
        'https://www.youtube.com/@Meesho/about',
        'https://www.youtube.com/@myntra/about',
        'https://www.youtube.com/@AmazonInOfficial/about',
        'https://www.youtube.com/@Blinkit_official/about'
    ]

    # 2. Google Sheets Authentication
    creds_json = os.environ.get('GCP_CREDENTIALS')
    if not creds_json:
        raise ValueError('GCP_CREDENTIALS environment variable not set')

    creds_dict = json.loads(creds_json)
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    # 3. Open Spreadsheet
    sh = gc.open('Social Blade Scrape Results')
    worksheet = sh.get_worksheet(0)

    # 4. Execute Scrape
    driver = get_driver()
    try:
        for url in target_urls:
            views = scrape_youtube_views(driver, url)
            if views:
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                worksheet.append_row([timestamp, url, views])
                print(f'Successfully updated {url}: {views:,} views')
            time.sleep(5)  # Delay between requests
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()