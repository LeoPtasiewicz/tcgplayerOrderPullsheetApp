import pandas as pd
from collections import defaultdict

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

# Example usage
combine_and_merge_products()
