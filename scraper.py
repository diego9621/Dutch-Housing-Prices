import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import threading
import random
import time
import unicodedata

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36"
]

#open a csv file and write data to it
csv_file = 'funda_zeeland_output.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Street", "Price", "Zip Code", "City", "Size (m²)", "Perceel Size (m²)"])

# Lock to prevent multiple ChromeDriver initializations
driver_lock = threading.Lock()

# ChromeDriver initialization 
def init_driver():
    with driver_lock:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--incognito")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        
        driver = uc.Chrome(options=options, version_main=134)
        
        # Anti-detection script
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """
        })
        return driver

# Scrapes houses and appartments per provincie ( e.g Zeeland)
def scrape_page(page):
    base_url = "https://www.funda.nl/en/zoeken/koop?selected_area=%5B%22provincie-noord-holland%22%5D&object_type=%5B%22house%22,%22apartment%22%5D"
    driver = init_driver()

    url = f"{base_url}&page={page}"
    driver.get(url)

    # Scroll to the bottom to load all things making sure we don't miss data
    for i in range(3):  
        driver.execute_script(f"window.scrollBy(0, document.body.scrollHeight / 3 * {i});")
        time.sleep(0.5)

    print(f"Scraping page {page}...")

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "truncate"))
        )
    except:
        print(f"❗ Timeout on page {page}")
        driver.quit()
        return

    # Extract data from HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract street names
    street_names = [span.get_text(strip=True).replace('\u00a0', ' ') 
                    for span in soup.find_all('span', class_='truncate') 
                    if any(char.isdigit() for char in span.get_text())]

    # Extract prices
    prices = []
    for div in soup.find_all('div', class_='truncate'):
        text = div.get_text(strip=True).replace('\u00a0', ' ')
        if '€' in text and 'k.k.' in text:
            clean_price = ''.join([c for c in text if c.isdigit()])
            prices.append(clean_price)

    # Extract zip codes and cities
    zip_codes = []
    cities = []
    for div in soup.find_all('div', class_='truncate text-neutral-80'):
        text = div.get_text(strip=True)
        if any(char.isdigit() for char in text):
            parts = text.split()
            zip_code = parts[0]  # Zip code only
            city = parts[1] if len(parts) > 1 else "N/A"  # City if available
            zip_codes.append(zip_code)
            cities.append(city)

    # Extract m² sizes and perceel sizes
    house_sizes = []
    perceel_sizes = []

    # Logic for size data extraction
    size_blocks = soup.find_all('ul', class_='flex h-8 flex-wrap gap-4 overflow-hidden truncate py-1')
    for block in size_blocks:
        sizes = [li.get_text(strip=True) for li in block.find_all('li')]

        house_size, perceel_size = 'N/A', 'N/A'
        for size in sizes:
            if 'm²' in size:
                # Normalize, for example remove "²" from "m²"
                clean_size = unicodedata.normalize("NFKD", size).replace('m²', '').strip()
                clean_size = ''.join([c for c in clean_size if c.isdigit()])  # Keep digits only
                
                if clean_size.endswith('2'):
                    clean_size = clean_size[:-1]
                    
                if house_size == 'N/A':
                    house_size = clean_size
                else:
                    perceel_size = clean_size

        house_sizes.append(house_size)
        perceel_sizes.append(perceel_size)

    # Ensure data is correctly aligned
    max_length = max(len(street_names), len(prices), len(zip_codes), len(house_sizes), len(perceel_sizes))

    # Fill missing data with "N/A"
    street_names.extend(['N/A'] * (max_length - len(street_names)))
    prices.extend(['N/A'] * (max_length - len(prices)))
    zip_codes.extend(['N/A'] * (max_length - len(zip_codes)))
    cities.extend(['N/A'] * (max_length - len(cities)))
    house_sizes.extend(['N/A'] * (max_length - len(house_sizes)))
    perceel_sizes.extend(['N/A'] * (max_length - len(perceel_sizes)))

    # combine and store
    data = list(zip(street_names, prices, zip_codes, cities, house_sizes, perceel_sizes))

    # Append data to the CSV
    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

    print(f"✅ Data added for page {page}")
    driver.quit()

def scrape_funda():
    threads = []
    pages = 666 #number of pages for example 666

    for i in range(1, pages + 1, 5):
        for page in range(i, min(i + 5, pages + 1)):
            thread = threading.Thread(target=scrape_page, args=(page,))
            thread.start()
            threads.append(thread)

        # Wait for all 5 concurrent threads to finish before starting the next batch
        for thread in threads:
            thread.join()

    print(f"✅ All listings data successfully saved to '{csv_file}'")

if __name__ == "__main__":
    scrape_funda()