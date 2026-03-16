import os, time, re, datetime, gspread, json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google.oauth2.service_account import Credentials

def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=options)

def scrape_channel_views(driver, url):
    try:
        driver.get(url)
        time.sleep(30)
        src = driver.page_source
        patterns = [
            r'(?:Views|Video Views).*?>([\d,]+)<',
            r'id="youtube-stats-header-views"[^>]*>([\d,]+)',
            r'"video_views":"?([\d,]+)"?'
        ]
        for p in patterns:
            match = re.search(p, src, re.IGNORECASE | re.DOTALL)
            if match: return int(match.group(1).replace(',', ''))
        return None
    except Exception as e:
        print(f'Error on {url}: {e}')
        return None

def run_automation():
    creds_json = os.environ.get('GCP_CREDENTIALS')
    if not creds_json: raise ValueError('GCP_CREDENTIALS not set')
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
            try:
                print(f'Processing: {url}')
                views = scrape_channel_views(driver, url)
                if views:
                    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    worksheet.append_row([ts, url, views])
                    print(f'Success: {url}')
                else:
                    print(f'No data found for: {url}')
                time.sleep(10)
            except Exception as e:
                print(f'Failed inner loop for {url}: {e}')
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()