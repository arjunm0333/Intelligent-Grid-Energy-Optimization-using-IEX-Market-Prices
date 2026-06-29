def mcp():
    import time
    import sqlite3
    import logging
    import os
    import sys
    from datetime import datetime
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

    DB_NAME = 'iex_market_snapshot.db'
    TABLE_NAME = 'dam_price'
    URL = 'https://www.iexindia.com/market-data/day-ahead-market/market-snapshot?interval=ONE_FOURTH_HOUR&dp=TODAY&showGraph=false'

    log_folder = 'logs'
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, f'iex_scraper_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    def create_db():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_block TEXT,
                mcp_value REAL,
                date_captured TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(time_block, date_captured)
            )
        ''')
        conn.commit()
        conn.close()

    def init_driver():
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def scroll_to_load_all(driver, expected_blocks=96, max_attempts=15):
        soup = None
        last_count = 0
        for attempt in range(max_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all("tr")[1:]
            current_count = len(rows)
            if current_count >= expected_blocks:
                break
            if current_count == last_count and attempt > 3:
                break
            last_count = current_count
        return soup

    def extract_data():
        try:
            driver = init_driver()
            driver.get(URL)
            time.sleep(5)
            soup = scroll_to_load_all(driver)
            driver.quit()

            if not soup:
                return []

            table = soup.find("table")
            rows = table.find_all("tr")
            if len(rows) < 2:
                return []

            standard_time_blocks = []
            for hour in range(24):
                for minute in [0, 15, 30, 45]:
                    start_time = f"{hour:02d}:{minute:02d}"
                    end_minute = (minute + 15) % 60
                    end_hour = hour + 1 if minute == 45 else hour
                    end_time = f"{end_hour:02d}:{end_minute:02d}"
                    standard_time_blocks.append(f"{start_time} - {end_time}")

            mcp_values = []
            for row in rows[1:]:
                cols = row.find_all("td")
                if cols:
                    try:
                        mcp_str = cols[-1].get_text(strip=True).replace(",", "").replace("₹", "").strip()
                        mcp = float(mcp_str)
                        mcp_values.append(mcp)
                    except:
                        pass

            today_date = datetime.now().strftime("%Y-%m-%d")
            data = []
            for i in range(min(len(standard_time_blocks), len(mcp_values))):
                data.append((standard_time_blocks[i], mcp_values[i], today_date))

            return data
        except Exception as e:
            logging.error(f"Error extracting data: {e}")
            print(f"Error extracting data: {e}")
            return []

    def save_data(data):
        if not data:
            return False
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE date_captured = ?", (today,))
            for tb, mcp, date_captured in data:
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} (time_block, mcp_value, date_captured, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (tb, mcp, date_captured, datetime.now()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            print(f"Error saving data: {e}")
            return False

    def job():
        logging.info("====== Running IEX DAM scraping job ======")
        print(">> Starting IEX DAM data scraping job...")

        create_db()
        data = extract_data()

        if data:
            logging.info(f"Extracted {len(data)} time blocks.")
            print(f">> ✅ Extracted {len(data)} time blocks:\n")
            for tb, mcp, _ in data:
                print(f"{tb} -> ₹{mcp:.2f}")
            save_data(data)
            logging.info("✅ Data saved.")
            print("\n>> ✅ Data saved to database.")
        else:
            logging.warning("⚠️ No data extracted.")
            print(">> ⚠️ No data extracted.")

        logging.info("====== Job finished ======")
        print(">> ✅ Job completed.\n")

    # 💡 Call job() here when mcp() is invoked
    job()