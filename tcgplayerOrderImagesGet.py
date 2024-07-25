import undetected_chromedriver as uc
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
from collections import defaultdict
import pandas as pd
import time
import csv
import requests
from bs4 import BeautifulSoup
import re

# Initialize the Chrome WebDriver
driver = uc.Chrome()

# Locator definitions
all_open_orders_button_locator = (By.XPATH, "//button[contains(@class, 'button is-secondary') and text()=' All Open Orders ']")
items_per_page_dropdown_locator = (By.CSS_SELECTOR, "select.input-per-page")
order_number_url_locator = (By.XPATH, "//a[contains(@href, '/admin/orders')]")
order_status_locator = (By.CLASS_NAME, "widget")
product_rows_locator = (By.XPATH, "//table[@data-testid='Order_Products']//tbody//tr")
product_link_locator = (By.XPATH, ".//td[1]//a")
product_condition_locator = (By.XPATH, ".//td[1]")
product_quantity_locator = (By.XPATH, ".//td[3]")

# Open the login page
driver.get('https://store.tcgplayer.com/login')

# Wait until the login page is loaded
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'Email')))

# Find the username and password fields and the login button
username_field = driver.find_element(By.NAME, 'Email')
password_field = driver.find_element(By.NAME, 'Password')
login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')

# Enter your credentials
load_dotenv()

username = os.getenv('MY_APP_USERNAME')
password = os.getenv('MY_APP_PASSWORD')

print(f"Username from .env: {username}")
print(f"Password from .env: {password}")
time.sleep(0.5)
username_field.send_keys(username)
time.sleep(2)
password_field.send_keys(password)

print("Clicked login button")

# Wait for you to log in manually if any additional verification is needed
print("Please complete any additional verification if prompted. Type 'ok' in the terminal to continue.")
while input().strip().lower() != 'ok':
    print("Please type 'ok' to continue after logging in.")

def switch_to_iframe_containing_element(driver, element_locator):
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for iframe in iframes:
        driver.switch_to.frame(iframe)
        try:
            if WebDriverWait(driver, 5).until(EC.presence_of_element_located(element_locator)):
                print(f"Element found in iframe {iframe.get_attribute('id')}")
                return True
        except TimeoutException:
            pass
        driver.switch_to.default_content()
    return False

def click_all_open_orders_button(driver):
    try:
        print("Looking for the 'All Open Orders' button...")
        # Locate the button
        button = driver.find_element(*all_open_orders_button_locator)
        print("Button found, now checking visibility and scroll into view")

        # Scroll the button into view
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        
        # Print the outer HTML of the button to verify it's the correct element
        print("Button HTML:", button.get_attribute('outerHTML'))

        # Click the button
        button.click()
        print("Clicked the 'All Open Orders' button successfully.")
    except TimeoutException:
        print("The 'All Open Orders' button was not found or not clickable.")
    except Exception as e:
        print(f"An error occurred while clicking the button: {e}")

def select_items_per_page(driver, value='500'):
    try:
        print(f"Selecting {value} items per page...")
        # Wait for the dropdown to be present
        dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(items_per_page_dropdown_locator)
        )
        # Use Select class to interact with the dropdown
        select = Select(dropdown)
        select.select_by_value(value)
        print(f"Selected {value} items per page successfully.")
    except TimeoutException:
        print("The items per page dropdown was not found or not selectable.")
    except Exception as e:
        print(f"An error occurred while selecting items per page: {e}")

def combine_products(order_details):
    combined_orders = []

    for order in order_details:
        combined_products = defaultdict(lambda: {"Quantity": 0, "Product URL": "", "Condition": "", "Image URL": ""})

        for product in order["Products"]:
            product_name = product["Product Name"]
            product_condition = product["Condition"]
            key = (product_name, product_condition)  # Use a tuple of product name and condition as the key
            if key in combined_products:
                combined_products[key]["Quantity"] += int(product["Quantity"])
            else:
                combined_products[key] = product

        order["Products"] = list(combined_products.values())
        combined_orders.append(order)

    return combined_orders

def wait_for_non_empty_text(driver, locator):
    element = WebDriverWait(driver, 10).until(
        lambda d: d.find_element(*locator).text.strip() != '' and d.find_element(*locator)
    )
    return element.text

def get_product_image_info(driver, product_url):
    driver.get(product_url)
    try:
        # Wait for the card name to be present
        card_name = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-details__name[data-testid="lblProductDetailsProductName"]'))
        ).text
        print(f"Card Name: {card_name}")

        # Wait for the images to be present and filter by the required URL pattern
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, 'img'))
        )
        image_elements = driver.find_elements(By.TAG_NAME, 'img')
        print(f"Found {len(image_elements)} image elements")

        # Filter the image elements to find the correct one
        card_image_url = next(
            (img.get_attribute('src') for img in image_elements if 'https://tcgplayer-cdn.tcgplayer.com' in img.get_attribute('src')), None
        )
        if card_image_url:
            # Change the dimensions to 1000x1000.jpg
            card_image_url = card_image_url.replace('_200x200.jpg', '_1000x1000.jpg')
        
        print(f"Card Image URL: {card_image_url}")
        return card_name, card_image_url
    except TimeoutException:
        print(f"Failed to retrieve image or name for {product_url}")
        return None, None
    except Exception as e:
        print(f"An error occurred while retrieving image or name for {product_url}: {e}")
        return None, None


def extract_order_number_urls(driver):
    try:
        print("Extracting order number URLs...")
        # Use a set to store unique URLs
        order_urls = set()
        
        # Locate all <a> elements with the specific href pattern
        order_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/admin/orders/manageorder')]")
        
        for link in order_links:
            href = link.get_attribute('href')
            if href:
                order_urls.add(href)
        
        if order_urls:
            for url in order_urls:
                print("Order URL:", url)
        else:
            print("No order URLs found.")
        
        return list(order_urls)
    except Exception as e:
        print(f"An error occurred while extracting order number URLs: {e}")
        return []

def extract_order_details(driver, order_url):
    driver.get(order_url)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(order_status_locator)
        )
        print(f"Order page loaded: {order_url}")

        # Extracting product details
        product_rows = driver.find_elements(*product_rows_locator)
        products = []
        
        for row in product_rows:
            product_link = row.find_element(*product_link_locator).get_attribute('href')
            product_name = row.find_element(*product_link_locator).text.strip()
            product_condition = row.find_element(*product_condition_locator).text.split('-')[-1].strip()
            product_quantity = row.find_element(*product_quantity_locator).text
            products.append({
                "Product URL": product_link,
                "Product Name": product_name,
                "Condition": product_condition,
                "Quantity": product_quantity
            })
        
        return {
            "Order URL": order_url,
            "Products": products
        }
    except TimeoutException:
        print(f"Failed to load order page: {order_url}")
        return None

def save_order_details_to_csv(order_details, filename="order_details.csv"):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(["Order URL", "Product Name", "Product URL", "Condition", "Quantity", "Image URL"])

            # Write order details
            for order in order_details:
                for product in order["Products"]:
                    writer.writerow([
                        order["Order URL"],
                        product["Product Name"],
                        product["Product URL"],
                        product["Condition"],
                        product["Quantity"],
                        product.get("Image URL", "")  # Image URL may be empty initially
                    ])
        print(f"Order details saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving the order details to CSV: {e}")

def update_image_urls_in_csv(driver, filename="order_details.csv"):
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
        
        header = rows[0]
        data_rows = rows[1:]

        updated_rows = []
        for row in data_rows:
            product_url = row[2]  # Adjusted to match the correct column for Product URL
            card_name, image_url = get_product_image_info(driver, product_url)
            row[5] = image_url if image_url else row[5]  # Adjusted to match the correct column for Image URL
            row[1] = card_name if card_name else row[1]  # Adjusted to match the correct column for Card Name
            updated_rows.append(row)

        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(updated_rows)

        print(f"Image URLs and Card Names updated in {filename}")
    except Exception as e:
        print(f"An error occurred while updating image URLs and Card Names in CSV: {e}")

def combine_products_from_csv(input_filename="order_details.csv", output_filename="order_details.csv"):
    try:
        with open(input_filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        combined_products = defaultdict(lambda: {"Quantity": 0, "Product URL": "", "Condition": "", "Image URL": ""})

        for row in rows:
            product_name = row["Product Name"]
            product_condition = row["Condition"]
            key = (product_name, product_condition)
            if key in combined_products:
                combined_products[key]["Quantity"] += int(row["Quantity"])
            else:
                combined_products[key] = {
                    "Order URL": row["Order URL"],
                    "Product Name": product_name,
                    "Product URL": row["Product URL"],
                    "Condition": product_condition,
                    "Quantity": int(row["Quantity"]),
                    "Image URL": row["Image URL"]
                }

        combined_rows = []
        for key, product in combined_products.items():
            combined_rows.append({
                "Order URL": product["Order URL"],
                "Product Name": key[0],
                "Product URL": product["Product URL"],
                "Condition": key[1],
                "Quantity": product["Quantity"],
                "Image URL": product["Image URL"]
            })

        with open(output_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["Order URL", "Product Name", "Product URL", "Condition", "Quantity", "Image URL"])
            writer.writeheader()
            writer.writerows(combined_rows)

        print(f"Combined order details saved to {output_filename}")
    except Exception as e:
        print(f"An error occurred while combining products: {e}")


def scrape_and_merge(url, order_details_file_path, output_file_path):
    driver = uc.Chrome()

    try:
        # Open the webpage
        driver.get(url)
        
        # Get the page source after JavaScript has executed
        html_content = driver.page_source

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all tables on the page
        tables = soup.find_all('table', {'class': 'wikitable'})

        # Initialize variables to hold the correct table
        correct_table = None

        # Iterate through all tables to find the correct one
        for table in tables:
            if table.find('td', text='1993-08'):
                correct_table = table
                break

        if correct_table is not None:
            release_dates = []
            names = []
            codes = []

            for row in correct_table.find_all('tr')[1:]:  # Skip the header row
                columns = row.find_all('td')
                if len(columns) > 0:
                    release_date = columns[0].get_text(strip=True) if len(columns) > 0 else 'N/A'
                    name = columns[1].get_text(strip=True) if len(columns) > 1 else 'N/A'
                    code = columns[3].get_text(strip=True) if len(columns) > 3 else 'N/A'

                    if ' ' in code:
                        code = code.split()[0]
                    if '(' in code:
                        code = code.split('(')[0].strip()

                    release_dates.append(release_date)
                    names.append(name)
                    codes.append(code)

            mtg_sets = pd.DataFrame({'Release Date': release_dates, 'Name': names, 'Code': codes})
            mtg_sets = mtg_sets.drop_duplicates(subset='Code', keep='first')
            mtg_sets.to_csv('mtg_sets.csv', index=False)
        else:
            print("Failed to find the correct table with the specified content")
            return
    finally:
        driver.quit()

    order_details = pd.read_csv(order_details_file_path)

    def extract_set_code(product_name):
        match = re.search(r'\((\w{3})\)', product_name)
        return match.group(1) if match else None

    order_details['Set Code'] = order_details['Product Name'].apply(extract_set_code)
    mtg_sets = pd.read_csv('mtg_sets.csv')
    merged_df = pd.merge(order_details, mtg_sets, left_on='Set Code', right_on='Code', how='left')
    merged_df.to_csv(output_file_path, index=False)
    print(f"Merged file saved as: {output_file_path}")

def reorder_merged_order_details(input_file_path, output_file_path):
    # Load the merged order details CSV
    df = pd.read_csv(input_file_path)

    # Define the desired order for conditions
    condition_order = [
        'Near Mint', 'Lightly Played', 'Moderately Played', 'Heavily Played', 'Damaged',
        'Near Mint Foil', 'Lightly Played Foil', 'Moderately Played Foil', 'Heavily Played Foil', 'Damaged Foil'
    ]

    # Define a function to get the sorting key based on the condition
    def get_condition_key(condition):
        if condition in condition_order:
            return condition_order.index(condition)
        else:
            return len(condition_order)  # Place unmatched conditions at the end

    # Add a sorting key column based on condition
    df['Condition_Key'] = df['Condition'].apply(get_condition_key)

    # Sort the DataFrame by the condition key and then by release date (descending)
    df_sorted = df.sort_values(by=['Condition_Key', 'Release Date'], ascending=[True, False])

    # Drop the sorting key column
    df_sorted = df_sorted.drop(columns=['Condition_Key'])

    # Save the reordered DataFrame to a new CSV file
    df_sorted.to_csv(output_file_path, index=False)
    print(f"Reordered file saved as: {output_file_path}")

def extract_three_letter_name(product_name):
    # Use regex to find the three-letter name in the product name
    match = re.search(r'\((\w{3})\)', product_name)
    if match:
        return match.group(1)
    return None

def load_set_data(csv_file):
    set_data = {}
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            set_data[row['Three-Letter Name']] = {
                'Set Name': row['Set Name'],
                'Release Date': row['Release Date']
            }
    return set_data

def join_csv_files(order_file, set_data_file, output_file):
    set_data = load_set_data(set_data_file)

    with open(order_file, mode='r', newline='', encoding='utf-8') as order_csv, \
         open(output_file, mode='w', newline='', encoding='utf-8') as output_csv:
        
        order_reader = csv.DictReader(order_csv)
        fieldnames = order_reader.fieldnames + ['Set Name', 'Release Date']
        writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
        writer.writeheader()

        for row in order_reader:
            product_name = row['Product Name']
            three_letter_name = extract_three_letter_name(product_name)
            if three_letter_name and three_letter_name in set_data:
                row['Set Name'] = set_data[three_letter_name]['Set Name']
                row['Release Date'] = set_data[three_letter_name]['Release Date']
            else:
                row['Set Name'] = 'Unknown'
                row['Release Date'] = 'Unknown'
            writer.writerow(row)


def combine_and_merge_products(input_filename="reordered_merged_order_details.csv", output_filename="combined_order_details.csv"):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(input_filename)
        
        # Create a dictionary to hold combined products
        combined_products = defaultdict(lambda: {
            "Order URL": "", "Product URL": "", "Condition": "", "Quantity": 0,
            "Image URL": "", "Set Code": "", "Release Date": "", "Name": "", "Code": ""
        })

        # Iterate over each row to combine products
        for _, row in df.iterrows():
            key = (row["Product Name"], row["Condition"])
            if key in combined_products:
                combined_products[key]["Quantity"] += row["Quantity"]
            else:
                combined_products[key].update({
                    "Order URL": row["Order URL"],
                    "Product URL": row["Product URL"],
                    "Condition": row["Condition"],
                    "Quantity": row["Quantity"],
                    "Image URL": row["Image URL"],
                    "Set Code": row["Set Code"],
                    "Release Date": row["Release Date"],
                    "Name": row["Name"],
                    "Code": row["Code"]
                })
        
        # Convert the combined products dictionary back to a DataFrame
        combined_rows = []
        for key, product in combined_products.items():
            combined_rows.append({
                "Order URL": product["Order URL"],
                "Product Name": key[0],
                "Product URL": product["Product URL"],
                "Condition": key[1],
                "Quantity": product["Quantity"],
                "Image URL": product["Image URL"],
                "Set Code": product["Set Code"],
                "Release Date": product["Release Date"],
                "Name": product["Name"],
                "Code": product["Code"]
            })

        combined_df = pd.DataFrame(combined_rows)
        
        # Write the combined DataFrame to the output CSV file
        combined_df.to_csv(output_filename, index=False)

        print(f"Combined order details saved to {output_filename}")
    except Exception as e:
        print(f"An error occurred while combining products: {e}")


if __name__ == "__main__":
    try:
        driver.get('https://store.tcgplayer.com/admin/orders/orderlist')
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//h6[text()='Quick Filters']")))
        print("Order list page loaded")

        click_all_open_orders_button(driver)
        select_items_per_page(driver)

        time.sleep(5)

        order_urls = extract_order_number_urls(driver)
        time.sleep(2)

        order_details = []
        for order_url in order_urls:
            details = extract_order_details(driver, order_url)
            if details:
                order_details.append(details)

        save_order_details_to_csv(order_details)
        update_image_urls_in_csv(driver)

        print("Scraping MTG sets from live site...")
        mtg_url = "https://mtg.fandom.com/wiki/Set"
        order_details_file_path = 'order_details.csv'
        merged_output_file_path = 'merged_order_details.csv'
        reordered_output_file_path = 'reordered_merged_order_details.csv'

        scrape_and_merge(mtg_url, order_details_file_path, merged_output_file_path)

        print("Reordering merged order details...")
        reorder_merged_order_details(merged_output_file_path, reordered_output_file_path)
        combine_and_merge_products()
        
    finally:
        print("Script completed. Keeping the browser open for inspection.")
        time.sleep(5)
        try:
            driver.close()
            driver.quit()
            print("Chrome WebDriver has been quit successfully.")
        except Exception as e:
            print(f"An error occurred while quitting the driver: {e}")

        

