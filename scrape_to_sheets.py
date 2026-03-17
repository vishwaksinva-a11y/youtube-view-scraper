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
        time.sleep(20) # Increased wait for full rendering
        yt_data = driver.execute_script("return JSON.stringify(window.ytInitialData);")
        src = driver.page_source
        
        # Try multiple patterns in both internal data and raw source
        patterns = [
            r'"viewCountText"\s*:\s*(?:\{"simpleText"\s*:\s*)?"([\d,]+)\s*views"', # Standard
            r'"viewCountText"\\s*:\\s*(?:\\{"simpleText"\\s*:\\s*)?"([\\d,]+)\\s*views"', # Escaped
            r'>([\d,]+)\s+views<', # HTML fallback
            r'viewCount\\\":\\\"(\d+)\\\"' # JSON Raw fallback
        ]

        all_found = []
        for p in patterns:
            for text_to_search in [yt_data, src]:
                if text_to_search:
                    matches = re.findall(p, text_to_search, re.IGNORECASE)
                    for m in matches:
                        try:
                            all_found.append(int(m.replace(',', '')))
                        except: pass
        
        if all_found:
            return max(all_found)
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
    
    sheet_id = "1SdheQ0MSi8n7mewLymk2CACIKzFJrI37gFo_Sm8_cHY"
    sh = gc.open_by_key(sheet_id)
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
                print(f'Successfully Updated {url}: {views}')
            else:
                print(f'FAILED to find data for {url}')
            time.sleep(5)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_automation()
