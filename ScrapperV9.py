import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import json
import re
import os
from urllib.parse import urlparse, unquote

def setup_driver():
    """Set up and return a Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_restaurant_info(driver):
    """Extract restaurant information from the page."""
    
    restaurant_info = {}
    
    try:
        time.sleep(3)
        try:
            restaurant_name = driver.find_element(By.XPATH, "//h1[contains(@class, 'sc-')]").text
            restaurant_info["name"] = restaurant_name
        except NoSuchElementException:
            restaurant_info["name"] = "Unknown"
            
        # Extract restaurant location 
        try:
            
            location_element = driver.find_element(By.CLASS_NAME, "sc-clNaTc.ckqoPM")
            location = location_element.text
            
            
            if not location:
                location_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'sc-clNaTc')]")
                if location_elements:
                    location = location_elements[0].text
            
            restaurant_info["location"] = location if location else "Not available"
        except NoSuchElementException:
            pass
        
        # Extract  rating 
        try:
            delivery_rating_elements = driver.find_elements(By.CLASS_NAME,"sc-1q7bklc-1.cILgox")
            delivery_rating_element=delivery_rating_elements[1]
            restaurant_info["rating"] = delivery_rating_element.text
        except (NoSuchElementException, IndexError):
            restaurant_info["rating"] = "Not available"
        
        # Extract  rating count 
        try:
            delivery_count_element = driver.find_element(By.XPATH, "//div[contains(@class, 'sc-1q7bklc-8') and following-sibling::div[contains(text(), 'Delivery')]]")
            restaurant_info["rating_count"] = delivery_count_element.text
        except NoSuchElementException:
            restaurant_info["rating_count"] = "0"
        
        # Extract restaurant cuisine types
        try:
            cuisine_elements = driver.find_elements(By.CLASS_NAME, "sc-eXNvrr")
            cuisines = [element.text for element in cuisine_elements]
            restaurant_info["cuisines"] = ", ".join(cuisines) if cuisines else "Not available"
        except NoSuchElementException:
            restaurant_info["cuisines"] = "Not available"
        
        # Set default timing as per requirement
        restaurant_info["timing"] = "10:00 AM to 11:00 PM"
        print(f"Default Timing: {restaurant_info['timing']}")
        
        # Extract phone number if available
        try:
            phone_element = driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]")
            restaurant_info["phone"] = phone_element.text
        except NoSuchElementException:
            restaurant_info["phone"] = "Not available" 
            
    except Exception as e:
        print(f"Error extracting restaurant information: {str(e)}")
    
    return restaurant_info

def extract_restaurant_name_from_url(url):
    """Extract restaurant name from URL for naming files."""
    try:
        # Parse URL and get the path
        path = urlparse(url).path
        
        path_parts = path.split('/')
        
        restaurant_name = path_parts[2] if len(path_parts) > 2 else "unknown"
        # Clean up the name 
        restaurant_name = restaurant_name.replace('-', ' ').title()
        return restaurant_name
    except Exception:
        return "unknown"

def scrape_zomato_menu(url):
    """Scrape the Zomato menu page for restaurant information and menu items."""
    driver = setup_driver()
    
    try:
        driver.get(url)
        
        
        time.sleep(5)
        
        
        restaurant_info = get_restaurant_info(driver)
        
        categories = driver.find_elements(By.CLASS_NAME, "sc-bZVNgQ.iGYweR")
        
        all_items = []
        
        for category in categories:
            # Extract category name
            try:
                category_name = category.find_element(By.CLASS_NAME, "sc-1hp8d8a-0.sc-liPmeQ.iZwYBC").text
            except NoSuchElementException:
                category_name = "Unknown Category"
            
            # Find all subcategory elements
            subcategories = category.find_elements(By.CLASS_NAME, "sc-eWRdud.iPlSrI")
            
            for subcategory in subcategories:
                # Extract subcategory name
                try:
                    subcategory_name = subcategory.find_element(By.CLASS_NAME, "sc-lljKfs.hQcSnF").text
                except NoSuchElementException:
                    subcategory_name = ""  # Leave blank if unknown subcategory
                
                # Find all food items in this subcategory
                food_items = subcategory.find_elements(By.CLASS_NAME, "sc-jhLVlY.cFNHph")
                
                for item in food_items:
                    try:
                        # Extract item name
                        item_name = item.find_element(By.CLASS_NAME, "sc-cGCqpu.chKhYc").text
                        
                        price_text = item.find_element(By.CLASS_NAME, "sc-17hyc2s-1.cCiQWA").text
                       
                        item_price = re.sub(r'[^\d.]', '', price_text)
                        
                        if item_price.count('.') > 1:
                            dots = [i for i, char in enumerate(item_price) if char == '.']
                            item_price = item_price[:dots[1]].replace('.', '') + '.' + item_price[dots[1]+1:].replace('.', '')
                        try:
                            item_price = float(item_price) if '.' in item_price else int(item_price)
                            print("Price: ", item_price)
                        except ValueError:
                            item_price = 0 
                        
                        # Extract tags
                        tags = []
                        try:
                            tag_containers = item.find_elements(By.XPATH, ".//*[contains(@class, 'sc-2gamf4-0')]")
                            for tag in tag_containers:
                                tags.append(tag.text)
                        except NoSuchElementException:
                            pass  
                        
                        # Check if item is veg or non-veg
                        try:
                            veg_element = item.find_element(By.CLASS_NAME, "sc-gcpVEs.cKFVkH")
                            veg_status = "Non-Veg" if "non-veg-icon" in veg_element.find_element(By.TAG_NAME, "use").get_attribute("href") else "Veg"                         
                        except NoSuchElementException:
                            veg_status = "Unknown"
                        
                        # Extract description
                        try:
                            description_element = item.find_element(By.CLASS_NAME, "sc-gsxalj.jqiNmO")
                            description = description_element.text
                            
                            # if there's a "read more" button and click it
                            try:
                                read_more = description_element.find_element(By.CLASS_NAME, "sc-VuRhl.RXkrv")
                                if "read more" in read_more.text.lower():
                                    read_more.click()
                                    time.sleep(1)  
                                    description = description_element.text.replace(" read less", "")
                            except NoSuchElementException:
                                pass  
                        except NoSuchElementException:
                            description = ""
                        
                        
                        description = description.replace(" read more", "").replace(" read less", "")
                        
                        
                        item_data = {
                            "category": category_name,
                            "subcategory": subcategory_name,
                            "name": item_name,
                            "price": item_price,
                            "veg_status": veg_status,
                            "tags": ", ".join(tags) if tags else "",
                            "description": description
                        }
                        
                        all_items.append(item_data)
                        
                    except Exception as e:
                        print(f"Error extracting item details: {str(e)}")
                        continue
        
        return restaurant_info, all_items
    
    finally:
        
        driver.quit()

def save_to_csv(restaurant_info, menu_data, restaurant_name="unknown"):
    """Save the scraped data to CSV files."""
    clean_name = re.sub(r'[^\w\s]', '', restaurant_name).replace(' ', '_').lower()
    
    # Save restaurant info
    restaurant_csv_filename = f"restaurant_info_{clean_name}.csv"
    pd.DataFrame([restaurant_info]).to_csv(restaurant_csv_filename, index=False, encoding='utf-8')
    print(f"Restaurant information saved to {restaurant_csv_filename}")

    
    for item in menu_data:
        item["restaurant_name"] = restaurant_info.get("name", restaurant_name)
    
    # Save menu data
    menu_csv_filename = f"menu_data_{clean_name}.csv"
    df = pd.DataFrame(menu_data)
    df.to_csv(menu_csv_filename, index=False, encoding='utf-8')
    print(f"Menu data saved to {menu_csv_filename}")

def save_to_json(restaurant_info, menu_data, restaurant_name="unknown"):
    """Save the scraped data to JSON files."""
    
    clean_name = re.sub(r'[^\w\s]', '', restaurant_name).replace(' ', '_').lower()
    
    
    combined_data = {
        "restaurant_info": restaurant_info,
        "menu_items": menu_data
    }
    
    # Save combined data
    json_filename = f"data_{clean_name}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
    print(f"All data saved to {json_filename}")

def scrape_multiple_restaurants(urls):
    """Scrape multiple restaurant URLs."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs("data", exist_ok=True)
    

    original_dir = os.getcwd()
    os.chdir(data_dir)
    
    results = []
    
    for url in urls:
        try:
            print(f"\n{'='*50}")
            print(f"Processing URL: {url}")
            print(f"{'='*50}\n")
            
            restaurant_info, menu_data = scrape_zomato_menu(url)
            
            if restaurant_info and menu_data:
                restaurant_name = restaurant_info.get("name", extract_restaurant_name_from_url(url))
                
                save_to_csv(restaurant_info, menu_data, restaurant_name)
                save_to_json(restaurant_info, menu_data, restaurant_name)
                
                results.append({
                    "url": url,
                    "restaurant_name": restaurant_name,
                    "status": "Success",
                    "items_scraped": len(menu_data)
                })

            else:
                results.append({
                    "url": url,
                    "restaurant_name": extract_restaurant_name_from_url(url),
                    "status": "Failed",
                    "items_scraped": 0
                })

                
            # Add a delay between requests to be nice to the server
            time.sleep(3)
                
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            results.append({
                "url": url,
                "restaurant_name": extract_restaurant_name_from_url(url),
                "status": f"Error: {str(e)}",
                "items_scraped": 0
            })
    

    pd.DataFrame(results).to_csv("scraping_results_summary.csv", index=False)
    print("\nScraping summary report saved to scraping_results_summary.csv")

    os.chdir(original_dir)
    
    return results

if __name__ == "__main__":
    urls = [
        "https://www.zomato.com/ncr/daryaganj-by-the-inventors-of-butter-chicken-and-dal-makhani-aerocity-new-delhi/order",
        "https://www.zomato.com/ncr/xero-courtyard-janpath-new-delhi/order",
        "https://www.zomato.com/ncr/mamagoto-saket-new-delhi/order",
        "https://www.zomato.com/ncr/cafe-delhi-heights-dlf-phase-4/order",
        "https://www.zomato.com/ncr/kfc-1-connaught-place-new-delhi/order",
        "https://www.zomato.com/ncr/burger-king-connaught-place-new-delhi/order",
        "https://www.zomato.com/ncr/taco-bell-connaught-place-new-delhi/order"
    ]
    

    results = scrape_multiple_restaurants(urls)

    print("\ncompleted!")