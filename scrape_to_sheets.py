import os, time, re, datetime, gspread, json
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
    driver_path = ChromeDriverManager().install()
    return webdriver.Chrome(service=Service(driver_path), options=options)

def scrape_youtube_views(driver, url):
    try:
        driver.get(url)
        time.sleep(25)
        src = driver.page_source
        # Pattern 1: JSON metadata (Most accurate for total views)
        match = re.search(r'"viewCount":"(\\d+)"', src)
        if match: return int(match.group(1))
        
        # Pattern 2: JSON escaped metadata
        match = re.search(r'viewCount\\\":\\\"(\\d+)\\\"', src)
        if match: return int(match.group(1))
        
        # Pattern 3: Human readable text fallback
        match = re.search(r'>([\\d,]+) views<', src)
        if match: return int(match.group(1).replace(',', ''))
        
        return None
    except Exception as e:
        print(f'Error on {url}: {e}')
        return None

# Main Automation Logic
creds_json = os.environ.get('GCP_CREDENTIALS')
if creds_json:
    creds_dict = json.loads(creds_json)
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open('Social Blade Scrape Results')
    worksheet = sh.get_worksheet(0)

    target_urls = [
        'https://www.youtube.com/@flipkart/about',
        'https://www.youtube.com/@Meesho/about',
        'https://www.youtube.com/@myntra/about',
        'https://www.youtube.com/@AmazonInOfficial/about',
        'https://www.youtube.com/@Blinkit_official/about'
    ]

    driver = get_driver()
    for url in target_urls:
        views = scrape_youtube_views(driver, url)
        if views:
            ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            worksheet.append_row([ts, url, views])
            print(f'Updated {url}: {views}')
    driver.quit()
