import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import tempfile
import pandas as pd
import xlwings as xw
from datetime import datetime
import logging
import time
import psutil
import shutil
import os
from seleniumbase import Driver

# Constants
WEBSITE = 'https://www.jegs.com/v/Omix-ADA/440?storeId=10001&catalogId=10002&langId=-1&Tab=SKU&csrc=brand'
CAPTCHA_WAIT_TIME = 500
ELEMENT_WAIT_TIME = 50
PAGE_LOAD_WAIT_TIME = 50
MAX_PAGES = 200

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('jegs_scraper.log'),
        logging.StreamHandler()
    ]
)

def setup_driver():
    try:
        user_data_dir = tempfile.mkdtemp()
        driver = Driver(uc=True)
        driver.user_data_dir = user_data_dir
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
       print(f"Driver setup failed: {e}")
       raise

def wait_for_captcha(driver):
    print("Please solve the CAPTCHA manually.")
    input("Press Enter after solving the CAPTCHA...")

def scrape_part_links(driver):
    part_links = []
    page_number = 113
    
    while page_number <= MAX_PAGES:
        try:
            print(f"Scraping page {page_number}...")
            
            # Update URL with current page number
            driver.get(f'https://www.jegs.com/v/Omix-ADA/440?pageSize=30&Tab=SKU&storeId=10001&catalogId=10002&langId=-1&csrc=brand&pageNumber={page_number}')
            time.sleep(5)

            # Wait for product container
            WebDriverWait(driver, ELEMENT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#SKU-description-container'))
            )

            # Retry logic for stale elements
            for _ in range(3): 
                try:
                    elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, 'div#product-details a[href^="/i/Omix-ADA/440/"]')
                        )
                    )
                    break
                except StaleElementReferenceException:
                    continue

            new_links = [
                element.get_attribute('href') 
                for element in elements if element.get_attribute('href') not in part_links
            ]
            part_links.extend(new_links)
            print(f"Found {len(new_links)} new links on page {page_number}")

            # Check for next page link
            try:
                pagination_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div#pagination'))
                )
                next_page_link = pagination_div.find_element(
                    By.CSS_SELECTOR, f'a[href*="pageNumber={page_number + 1}"]'
                )
                page_number += 1

            except (NoSuchElementException, TimeoutException):
                print("No more pages to scrape or 'Next' link not found.")
                break

        except Exception as e:
            print(f"Error on page {page_number}: {str(e)}")
            break

    part_links = list(dict.fromkeys(part_links))
    print(f"Total unique links found: {len(part_links)}")
    return part_links



def parse_vehicle_info(vehicle_info):
    """
    Split vehicle information into Year, Make, and Model
    
    Args:
        vehicle_info (str): Full vehicle information string
    
    Returns:
        dict: Dictionary with parsed Year, Make, and Model
    """
    # Split the vehicle info into parts
    parts = vehicle_info.split()
    
    # Assume the first part is the year (if it's a 4-digit number)
    if len(parts[0]) == 4 and parts[0].isdigit():
        year = parts[0]
        # The make is typically the next word
        make = parts[1]
        # The rest of the parts are the model
        model = ' '.join(parts[2:])
    else:
        # If no year is found, set year to None or an empty string
        year = ''
        make = parts[0]
        model = ' '.join(parts[1:])
    
    return {
        'Year': year,
        'Make': make,
        'Model': model
    }

def scrape_part_details(driver, part_links):
    part_data = []
    total_links = len(part_links)
    
    for index, part_link in enumerate(part_links, 1):
        try:
            print(f"Processing part {index}/{total_links}: {part_link}")
            driver.get(part_link)
            
            # Extract the part number from the part_link
            part_segments = part_link.split('/') 
            
            # Debug print to check the segments of the part_link
            print(f"Part segments: {part_segments}")

            # Ensure there are enough segments before accessing
            if len(part_segments) >= 6:
                part_number = f"{part_segments[-4]}-{part_segments[-3]}"
            else:
                print("Error: Part link does not contain enough segments.")
                continue
            
            # Click on the Vehicle Fitment tab
            try:
                vehicle_fitment_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.tab-label[onclick*="ajaxLoadFirstProductFitment"]'))
                )
                vehicle_fitment_tab.click()
                time.sleep(5)  # Allow time for the fitment data to load
            except NoSuchElementException:
                print("Vehicle Fitment tab not found.")
                continue
            
            # Check if there's a "No Fitment record found" message
            if "No Fitment record found for current selection" in driver.page_source:
                print(f"No fitment data found for part {index} ({part_link})")
                continue
            
            page_number = 1  # Start with page 1
            while True:
                try:
                    # Wait for the fitment data to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "fitment-data"))
                    )
                    
                    # Extract data from all fitment-data elements on the current page
                    fitment_elements = driver.find_elements(By.CSS_SELECTOR, 'div.fitment-data.col-4.desk-6.phone-12')
                    for fitment_element in fitment_elements:
                        part_detail = {}
                        try:
                            vehicle_info_element = fitment_element.find_element(By.CSS_SELECTOR, 'h3')
                            vehicle_info = vehicle_info_element.text.strip()
                            
                            # Parse vehicle information
                            vehicle_parsed = parse_vehicle_info(vehicle_info)
                            
                            # Add parsed vehicle info and part number to part_detail
                            part_detail['Vehicle'] = vehicle_info
                            part_detail['Year'] = vehicle_parsed['Year']
                            part_detail['Make'] = vehicle_parsed['Make']
                            part_detail['Model'] = vehicle_parsed['Model']
                            part_detail['Part Number'] = part_number
                        
                        except NoSuchElementException:
                            print("Vehicle information not found.")
                            continue
                        
                        detail_elements = fitment_element.find_elements(By.CSS_SELECTOR, 'ul li')
                        for detail_element in detail_elements:
                            detail_text = detail_element.text.strip()
                            if detail_text and ':' in detail_text:
                                key, value = detail_text.split(':', 1)
                                part_detail[key.strip()] = value.strip()
                        
                        if part_detail:
                            part_data.append(part_detail)
                            print(f"Scraped details for part {index}: {part_detail}")
                    
                    # Handle pagination
                    try:
                        next_page_link = driver.find_element(By.CSS_SELECTOR, f'a[onclick*="pageNumber={page_number + 1}"]')
                        if next_page_link:
                            driver.execute_script("arguments[0].click();", next_page_link)
                            page_number += 1
                            time.sleep(5)  # Allow page transition
                        else:
                            print("Next page link not found. Ending pagination.")
                            break  # Exit pagination loop
                    except (NoSuchElementException, TimeoutException):
                        print("No more pages to scrape or 'Next' link not found.")
                        break  # Exit pagination loop
                
                except TimeoutException:
                    print("Pagination data did not load in time.")
                    break
        
        except Exception as e:
            print(f"Error processing part {index} ({part_link}): {str(e)}")
            continue
    
    return part_data


def process_data(part_data):
    if not part_data:
        raise ValueError("No part data to process")
        
    # Create DataFrame
    df = pd.DataFrame(part_data)

    # Clean the data
    for column in df.columns:
        if df[column].dtype == 'object':
            df[column] = df[column].str.strip()
    
    # Drop the 'Vehicle' column
    df = df.drop('Vehicle', axis=1)

    # Determine the desired column order
    desired_columns = ['Part Number', 'Year', 'Make', 'Model']
    
    # Rearrange the columns to match the desired order
    # First, get the columns that are in the desired_columns list
    reordered_columns = [col for col in desired_columns if col in df.columns]
    # Then, get the remaining columns that are not in the desired_columns list
    other_columns = [col for col in df.columns if col not in desired_columns]
    # Combine the reordered columns and other columns in the desired order
    df = df[reordered_columns + other_columns]
            
    return df


def save_to_excel(df):
    try:
        current_datetime = datetime.now().strftime("%Y-%m-%d")
        output_file_name = f"Omix-ADA_Application_{current_datetime}.xlsx"
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop_path, output_file_name)
        
        # Save with pandas first
        df.to_excel(file_path, index=False, freeze_panes=(1, 0))
        
        # Format with xlwings
        with xw.App(visible=False) as app:
            wb = xw.Book(file_path)
            ws = wb.sheets[0]
            
            # Format header
            header_range = ws.range('1:1')
            header_range.color = (200, 200, 200)
            header_range.api.Font.Bold = True
            
            # Autofit columns
            ws.autofit('c')
            
            # Set minimum and maximum column widths
            for column in ws.api.UsedRange.Columns:
                if column.ColumnWidth < 8:
                    column.ColumnWidth = 8
                elif column.ColumnWidth > 50:
                    column.ColumnWidth = 50
            wb.save()
            wb.close()
        
        print(f'Data successfully saved to: {file_path}')
        
    except Exception as e:
        print(f"Error saving to Excel: {str(e)}")
        raise

def cleanup(driver):
    """Helper function to handle driver cleanup and temp data directory deletion."""
    try:
        # Attempt to close all windows
        for _ in range(5):
            try:
                driver.quit()
                
                # Wait a bit before cleanup to ensure all processes are closed
                time.sleep(2)

                # Forcefully close any remaining chrome processes
                for proc in psutil.process_iter(attrs=['pid', 'name']):
                    if 'chrome' in proc.info['name'].lower():
                        proc.kill()

                # Remove temporary user data directory
                if hasattr(driver, 'user_data_dir') and os.path.exists(driver.user_data_dir):
                    shutil.rmtree(driver.user_data_dir, ignore_errors=False)
                
                # Short sleep to allow proper cleanup
                time.sleep(0.1)
                break
            except FileNotFoundError:
                break
            except (RuntimeError, OSError, PermissionError) as e:
                print(f"Cleanup error: {e}")
                # Wait a bit before retrying
                time.sleep(0.1)
    except Exception as close_error:
        print(f"Error during driver closure: {close_error}")


def main():
    driver = None
    try:
        print("Starting scraping process...")
        driver = setup_driver()
        driver.get(WEBSITE)
        
        wait_for_captcha(driver)
        
        print("Collecting part links...")
        part_links = scrape_part_links(driver)
        print(f"Scraping details for {len(part_links)} parts...")
        part_data = scrape_part_details(driver, part_links)
        
        print("Processing part data...")
        df = process_data(part_data)
        
        print("Saving data to Excel...")
        save_to_excel(df)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        if driver:
            cleanup(driver)

if __name__ == "__main__":
    main()







