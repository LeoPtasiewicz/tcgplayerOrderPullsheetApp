import pandas as pd

def reorder_merged_order_details(file_path):
    # Load the merged order details CSV
    df = pd.read_csv(file_path)

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
    output_file_path = 'merged_order_details.csv'
    df_sorted.to_csv(output_file_path, index=False)

    return output_file_path

if __name__ == "__main__":
    file_path = 'merged_order_details.csv'
    reordered_file = reorder_merged_order_details(file_path)
    print(f"Reordered file saved as: {reordered_file}")
