import gspread
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Authenticate with Google Sheets using the JSON credentials file
gc = gspread.service_account(filename='credentials.json')

# Open the Google Sheet by its name
spreadsheet = gc.open("Daily YouTube Views")
worksheet = spreadsheet.sheet1

# Set up the headless browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

print("Starting scraper...")
try:
    url = "https://www.youtube.com/flipkart"
    driver.get(url)

    # Wait for the element with the stats to load
    wait = WebDriverWait(driver, 20)
    stats_element = wait.until(
        EC.presence_of_element_located((By.ID, "description-text"))
    )
    
    # Extract and parse the view count from the text
    full_stats_text = stats_element.text
    parts = full_stats_text.split('•')
    views_part = [part for part in parts if 'views' in part][0]
    view_count_str = ''.join(filter(str.isdigit, views_part))
    view_count = int(view_count_str)
    
    print(f"Successfully scraped view count: {view_count}")

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    
    # Append the data as a new row to the Google Sheet
    worksheet.append_row([today_date, view_count])
    
    print("✅ Data successfully appended to Google Sheet.")

except Exception as e:
    print(f"❌ An error occurred: {e}")
    
finally:
    driver.quit()
