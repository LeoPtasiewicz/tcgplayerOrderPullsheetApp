import csv
import re

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

if __name__ == "__main__":
    order_details_file = 'order_details.csv'
    sets_file = 'magic_the_gathering_sets.csv'
    output_file = 'joined_orders.csv'
    
    join_csv_files(order_details_file, sets_file, output_file)
    print(f'Joined data has been saved to {output_file}')
