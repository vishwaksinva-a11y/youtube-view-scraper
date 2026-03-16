import os
import time
import re
import datetime
import gspread
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google.oauth2.service_account import Credentials

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_channel_views(driver, url):
    try:
        # Randomized delay before loading to mimic human behavior
        wait_time = random.randint(30, 60)
        print(f'Waiting {wait_time}s before loading {url}...')
        time.sleep(wait_time)
        
        driver.get(url)
        time.sleep(15) # Wait for dynamic JS
        page_source = driver.page_source

        patterns = [
            r'(?:Views|Video Views).*?>([\d,]+)<',
            r'id="youtube-stats-header-views"[^>]*>([\d,]+)',
            r'"video_views":"?([\d,]+)"?',
            r'<span>([\d,]+)</span>.*?Video Views'
        ]

        for pattern in patterns:
            match = re.search(pattern, page_source, re.IGNORECASE | re.DOTALL)
            if match:
                return int(match.group(1).replace(',', ''))
        return None
    except Exception as e:
        print(f'Error scraping {url}: {e}')
        return None

def run_automation():
    creds_json = os.environ.get('GCP_CREDENTIALS')
    if not creds_json: 
        raise ValueError('GCP_CREDENTIALS not set')
    
    creds_dict = json.loads(creds_json)
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)

    sh = gc.open('Social Blade Scrape Results')
    worksheet = sh.get_worksheet(0)

    target_urls = [
        'https://socialblade.com/youtube/handle/flipkart',
        'https://socialblade.com/youtube/channel/UCaGHIRKYUYlaI_ZAt2hxpjw',
        'https://socialblade.com/youtube/channel/UCMlJjMRSKaUQhXQ_9XjCGpg',
        'https://socialblade.com/youtube/channel/UC2cZjd8SBxVvZFGC5FEXn2Q'
    ]

    driver = get_driver()
    try:
        for url in target_urls:
            print(f'Processing: {url}')
            views = scrape_channel_views(driver, url)
            if views:
                timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                worksheet.append_row([timestamp, url, views])
                print(f'Successfully updated: {url}')
            else:
                print(f'Could not find data for: {url}')
            time.sleep(10) # Cooling period between channels
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
