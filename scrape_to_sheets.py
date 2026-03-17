```python
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
        time.sleep(15)
        yt_data = driver.execute_script("return JSON.stringify(window.ytInitialData);")
        if not yt_data: return None
        pattern = r'"viewCountText"\\s*:\\s*(?:\\{"simpleText"\\s*:\\s*)?"([\\d,]+)\\s*views"'
        matches = re.findall(pattern, yt_data, re.IGNORECASE)
        if matches:
            return max([int(m.replace(',', '')) for m in matches])
        return None
    except Exception as e:
        print(f'Error on {url}: {e}')
        return None

def run_automation():
    creds_json = os.environ.get('GCP_CREDENTIALS')
    if not creds_json: raise ValueError('GCP_CREDENTIALS not set')
    creds_dict = json.loads(creds_json)
    
    print(f"DEBUG: Script is running as {creds_dict.get('client_email')}")

    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    
    sh = gc.open_by_key('1T0fc6EsGu_mQnKLucqNgb5wZkE0qDe2EQCrt1ZcxzcI')
    worksheet = sh.get_worksheet(0)
    
    urls = [
        'https://www.youtube.com/@flipkart/about',
        'https://www.youtube.com/@Meesho/about',
        'https://www.youtube.com/@myntra/about',
        'https://www.youtube.com/@AmazonInOfficial/about',
        'https://www.youtube.com/@letsblinkit/about'
    ]

    driver = get_driver()
    try:
        for url in urls:
            views = scrape_youtube_views(driver, url)
            if views:
                ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                worksheet.append_row([ts, url, str(views)])
                print(f'Updated {url}: {views}')
            time.sleep(5)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
```
