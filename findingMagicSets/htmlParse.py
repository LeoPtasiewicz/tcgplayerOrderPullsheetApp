from bs4 import BeautifulSoup
import pandas as pd
import re

def parse_html_for_mtg_sets(file_path):
    # Load the saved HTML file
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

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
        data = {'Release Date': release_dates, 'Name': names, 'Code': codes}
        df = pd.DataFrame(data)
        
        # Optionally, save the DataFrame to a CSV file
        df.to_csv('mtg_sets.csv', index=False)
    else:
        print("Failed to find the correct table with the specified content")

def join_order_details_with_mtg_sets(order_details_path, mtg_sets_path):
    # Load order details CSV
    order_details = pd.read_csv(order_details_path)

    # Function to extract the set code from the product name
    def extract_set_code(product_name):
        match = re.search(r'\((\w{3})\)', product_name)
        return match.group(1) if match else None

    # Extract the set code from the product name
    order_details['Set Code'] = order_details['Product Name'].apply(extract_set_code)

    # Load the mtg_sets.csv
    mtg_sets = pd.read_csv(mtg_sets_path)

    # Merge order details with mtg sets on the set code
    merged_df = pd.merge(order_details, mtg_sets, left_on='Set Code', right_on='Code', how='left')

    # Optionally, save the merged DataFrame to a CSV file
    merged_df.to_csv('merged_order_details.csv', index=False)

if __name__ == "__main__":
    parse_html_for_mtg_sets('page_source.html')
    join_order_details_with_mtg_sets('order_details.csv', 'mtg_sets.csv')
