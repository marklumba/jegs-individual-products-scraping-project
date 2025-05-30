
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import tempfile
import pandas as pd
import xlwings as xw
from datetime import datetime
from fake_useragent import UserAgent
import logging

import time
import psutil
import shutil
import os



# Constants
WEBSITE = 'https://www.jegs.com/v/King-Shocks/745?Tab=GROUP'
CAPTCHA_WAIT_TIME = 500
ELEMENT_WAIT_TIME = 30
PAGE_LOAD_WAIT_TIME = 30
MAX_PAGES = 500

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
        # Create a temporary directory for user data
        user_data_dir = tempfile.mkdtemp()
        
        user_agent = UserAgent().random
        options = uc.ChromeOptions()
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        driver = uc.Chrome(options=options)
        
        # Attach the temp directory path to the driver for later cleanup
        driver.user_data_dir = user_data_dir

        # Set page load timeout
        driver.set_page_load_timeout(30)

        return driver

    except Exception as e:
       print(f"Driver setup failed: {e}")
       raise


def wait_for_captcha(driver):
    print("Please solve the CAPTCHA manually.")
    input("Press Enter after solving the CAPTCHA...")  # Better than fixed time sleep


def navigate_to_individual_parts(driver):
    locators = [
        (By.CSS_SELECTOR, 'span#unselected-tab a[href*="?Tab=SKU"]'),
        (By.XPATH, '//span[@id="unselected-tab"]//a[contains(@href, "?Tab=SKU")]'),
        (By.CSS_SELECTOR, 'span#unselected-tab a')
    ]
    
    for locator in locators:
        try:
            element = WebDriverWait(driver, ELEMENT_WAIT_TIME).until(
                EC.element_to_be_clickable(locator)
            )
            
            element.click()
            time.sleep(2)
            return
        except Exception as e:
            print(f"Failed with locator {locator}: {e}")
    
    raise Exception("Could not navigate to Individual Products tab")


def scrape_part_links(driver):
    part_links = []
    page_number = 1  # Start from page 1
    
    while page_number <= MAX_PAGES:
        try:
            print(f"Scraping page {page_number}...")

            # Wait for product container
            WebDriverWait(driver, ELEMENT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div#SKU-description-container'))
            )

            # Retry logic for stale elements
            for _ in range(3): 
                try:
                    elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, 'div#product-details a[href^="/i/King-Shocks/745/"]')
                        )
                    )
                    break
                except StaleElementReferenceException:
                    continue

            # Extract unique links
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

                # Click the link to navigate to the next page
                driver.execute_script("arguments[0].click();", next_page_link)
                page_number += 1
                time.sleep(2)  # Allow page transition

            except (NoSuchElementException, TimeoutException):
                print("No more pages to scrape or 'Next' link not found.")
                break

        except Exception as e:
            print(f"Error on page {page_number}: {str(e)}")
            break

    # Drop duplicates and return unique links
    part_links = list(dict.fromkeys(part_links))
    print(f"Total unique links found: {len(part_links)}")
    return part_links




def scrape_part_details(driver, part_links):
    part_data = []
    total_links = len(part_links)

    for index, part_link in enumerate(part_links, 1):
        try:
            print(f"Processing part {index}/{total_links}: {part_link}")
            driver.get(part_link)

            # Wait for specifications tab to ensure page has loaded
            try:
                WebDriverWait(driver, PAGE_LOAD_WAIT_TIME).until(
                    EC.presence_of_element_located((By.ID, "tab-item-specification"))
                )
            except TimeoutException:
                print(f"Page load timeout for part {index}")
                continue

            # Initialize empty part detail dictionary
            part_detail = {}

            # Extract Part Number
            try:
                part_number = driver.find_element(By.ID, "product_id").text.strip()
                part_detail['Part Number'] = part_number
            except NoSuchElementException:
                print(f"Part number not found for part {index}")

            # Extract Product Title
            try:
                name_elements = driver.find_elements(By.CSS_SELECTOR, '#pdpHeading .productItemName span')
                full_name = ' '.join([elem.text.strip() for elem in name_elements if elem.text.strip()])
                part_detail['Title'] = full_name
            except Exception as name_error:
                print(f"Error extracting product title for part {index}: {str(name_error)}")

            # Extract Product Category
            try:
                product_category = driver.find_element(By.ID, "shortDesc").text.strip()
                part_detail['Product Category'] = product_category
            except NoSuchElementException:
                print(f"Product category not found for part {index}")

            # Extract Bullet Points
            try:
                bullet_elements = driver.find_elements(By.CSS_SELECTOR, '#shortDesc li')
                for i, bullet in enumerate(bullet_elements, 1):
                    bullet_text = bullet.text.strip()
                    part_detail[f'Bullet {i}'] = bullet_text
            except NoSuchElementException:
                print(f"Bullet points not found for part {index}")

            # Add an empty 'Specs' column
            part_detail['Specs'] = ''

            # Extract Description (plain text and bullets)
            try:
                descriptions = []

                try:
                    # Short description (e.g., GM)
                    aux_description_element = driver.find_element(By.CSS_SELECTOR, '#tab-auxDescription1')
                    aux_description = aux_description_element.text.strip()

                    # Locate the long description element
                    long_description_element = driver.find_element(By.CSS_SELECTOR, '#tab-longDescription')
                    long_description = long_description_element.text.strip()  # Extract the plain text description

                    # Locate bullet points within the long description
                    bullet_elements = driver.find_elements(By.CSS_SELECTOR, '#tab-longDescription ul li')
                    #bullet_texts = [f"- {bullet.text.strip()}" for bullet in bullet_elements if bullet.text.strip()]
                    bullet_texts = [f". {li.text.strip()}" for li in bullet_elements if li.text.strip()]  # Add bullet markers
                    # Prepare bullet text separately
                    bullet_text_combined = "\n".join(bullet_texts)

                    # Combine plain text and bullets if both exist
                    if  aux_description and long_description:
                      descriptions.append(f"{aux_description}\n\n{long_description}\n")
                    elif long_description:  # Only plain text
                      descriptions.append(long_description)
                    elif bullet_texts:  # Only bullets
                      descriptions.append(bullet_text_combined)

                except NoSuchElementException:
                    pass  # Optional element

                # Combine descriptions
                part_detail['Description'] = "\n\n".join(descriptions) if descriptions else ""

            except Exception as e:
                print(f"Error extracting description for part {index}: {str(e)}")
                part_detail['Description'] = "No description available"

            # Extract Specifications
            try:
                detail_elements = driver.find_elements(By.CSS_SELECTOR, 'div#tab-item-specification div.cf')
                for detail_element in detail_elements:
                    try:
                        name_element = detail_element.find_element(By.CLASS_NAME, 'itemAttribName')
                        value_element = detail_element.find_element(By.CLASS_NAME, 'itemAttribValue')
                        
                        key = name_element.text.strip()
                        value = value_element.text.strip()
                        
                        if key and value:
                            part_detail[key] = value
                    except (NoSuchElementException, StaleElementReferenceException):
                        continue
            except Exception as e:
                print(f"Error extracting specifications for part {index}: {str(e)}")

            # Append part details to the data list
            if part_detail:
                part_data.append(part_detail)
                print(f"Successfully scraped details for part {index}")
            
            # Respectful delay between requests
            time.sleep(1)

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


    # Define the desired fixed order (excluding the dynamic "Bullet" columns)
    fixed_order = ['Part Number', 'Title', 'Product Category', 'Specs', 'Description']

    # Identify all "Bullet" columns dynamically
    bullet_columns = sorted([col for col in df.columns if 'Bullet' in col])

    # Combine the fixed order with the dynamically identified "Bullet" columns
    new_order = ['Part Number', 'Title', 'Product Category'] + bullet_columns + ['Specs', 'Description']

    # Dynamically extract the remaining columns that are not part of the desired order
    remaining_columns = [col for col in df.columns if col not in new_order]

    # Combine the new order with the remaining columns
    final_order = new_order + remaining_columns

    # Reorder the DataFrame
    df = df[final_order]

    print("Headers reordered and saved successfully.")
            
    return df


def save_to_excel(df):
    try:
        current_datetime = datetime.now().strftime("%Y-%m-%d")
        output_file_name = f"King_Shocks_Individual_Part_{current_datetime}.xlsx"
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
        print("Navigating to individual parts...")
        navigate_to_individual_parts(driver)
        
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
