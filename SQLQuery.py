from dotenv import load_dotenv
import os
import psycopg2
import pandas as pd

# Load environment variables from the .env file
load_dotenv()

# Retrieve database credentials from environment variables
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Connect to the PostgreSQL database
connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# Define the SQL query
query = """
select a.*
from "Asset" a
join "Prize" p on a."id" = p."assetId"
join "GameVersion" gv on gv."gameId" = p."gameId" and gv."version" = p."gameVersionVersion"
join "Game" g on g."id" = gv."gameId"
where exists (
    select 1
    from unnest(a.tags) as tag
    where tag in ('POKEMON', 'MTG')
)
and gv."currentVersionOfId" is not null
and g.status = 'AVAILABLE';
"""

# Execute the query and fetch the results
try:
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()

        # Fetch column names
        column_names = [desc[0] for desc in cursor.description]

        # Convert the results to a DataFrame
        df = pd.DataFrame(results, columns=column_names)

        # Save the DataFrame to a CSV file
        df.to_csv('query_results.csv', index=False)

        print("Query executed and results saved to 'query_results.csv'")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    connection.close()
