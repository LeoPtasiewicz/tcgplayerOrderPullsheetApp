import pandas as pd
import re
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

def scrape_and_merge(url, order_details_file_path, output_file_path):
    # Set up the undetected_chromedriver
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
            # Check if the table contains the desired content
            if table.find('td', text='1993-08'):
                correct_table = table
                break

        # Check if the correct table was found
        if correct_table is not None:
            # Lists to hold the scraped data
            release_dates = []
            names = []
            codes = []

            # Iterate through each row in the correct table
            for row in correct_table.find_all('tr')[1:]:  # Skip the header row
                columns = row.find_all('td')
                if len(columns) > 0:
                    release_date = columns[0].get_text(strip=True) if len(columns) > 0 else 'N/A'
                    name = columns[1].get_text(strip=True) if len(columns) > 1 else 'N/A'
                    code = columns[3].get_text(strip=True) if len(columns) > 3 else 'N/A'

                    # Ensure the code is exactly 3 letters
                    if ' ' in code:
                        code = code.split()[0]
                    if '(' in code:
                        code = code.split('(')[0].strip()

                    release_dates.append(release_date)
                    names.append(name)
                    codes.append(code)

            # Create a DataFrame from the lists
            mtg_sets = pd.DataFrame({'Release Date': release_dates, 'Name': names, 'Code': codes})

            # Drop duplicate codes, keeping the first occurrence
            mtg_sets = mtg_sets.drop_duplicates(subset='Code', keep='first')

            # Save the DataFrame to a CSV file
            mtg_sets.to_csv('mtg_sets.csv', index=False)
        else:
            print("Failed to find the correct table with the specified content")
            return
    finally:
        driver.quit()

    # Load order details CSV
    order_details = pd.read_csv(order_details_file_path)

    # Function to extract the set code from the product name
    def extract_set_code(product_name):
        match = re.search(r'\((\w{3})\)', product_name)
        return match.group(1) if match else None

    # Extract the set code from the product name
    order_details['Set Code'] = order_details['Product Name'].apply(extract_set_code)

    # Load the mtg_sets.csv
    mtg_sets = pd.read_csv('mtg_sets.csv')

    # Merge order details with mtg sets on the set code
    merged_df = pd.merge(order_details, mtg_sets, left_on='Set Code', right_on='Code', how='left')

    # Save the merged DataFrame to a CSV file
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

if __name__ == "__main__":
    # URL to scrape
    url = "https://mtg.fandom.com/wiki/Set"
    
    # File paths
    order_details_file_path = 'order_details.csv'
    merged_output_file_path = 'merged_order_details.csv'
    reordered_output_file_path = 'reordered_merged_order_details.csv'

    # Execute the functions
    scrape_and_merge(url, order_details_file_path, merged_output_file_path)
    reorder_merged_order_details(merged_output_file_path, reordered_output_file_path)
