import pandas as pd
import glob 

all_files = glob.glob('output/*.csv')

#combine all files in the 'output' folder
df_list = [pd.read_csv(file) for file in all_files]
df = pd.concat(df_list, ignore_index=True)

# Data Cleaning and Processing
df['pc4_code'] = df['Zip Code'].str[:4]  # Extract 4-digit zip code
df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
df['size m²'] = pd.to_numeric(df['Size (m²)'], errors='coerce')

# Drop invalid data
df = df.dropna(subset=['Price', 'size m²'])
df = df[df['size m²'] > 0]

# Calculate Price per m²
df['Price_per_m2'] = df['Price'] / df['size m²']

#Group by zipcode and calculate Average
avg_price_per_m2 = df.groupby('pc4_code')['Price_per_m2'].mean().reset_index()

# Save the Results
avg_price_per_m2.to_csv('combined_data.csv', index=False)
print("✅ Done!")