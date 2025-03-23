import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import numpy as np  

geojson_file = 'zipcodes.geojson'
gdf = gpd.read_file(geojson_file)

price_data = pd.read_csv('combined_data.csv')
gdf['pc4_code'] = gdf['pc4_code'].astype(str)
price_data['pc4_code'] = price_data['pc4_code'].astype(str)

gdf = gdf.merge(price_data, on='pc4_code', how='left')

# Apply log scaling for skewed data
gdf['Price_per_m2_log'] = np.log1p(gdf['Price_per_m2'])

m = folium.Map(location=[52.1236, 5.2913], zoom_start=8, tiles='cartodbpositron')
m.get_root().header.add_child(folium.Element(
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>'
))

bins = list(np.linspace(gdf['Price_per_m2_log'].min(), gdf['Price_per_m2_log'].max(), 8))
folium.Choropleth(
    geo_data=gdf,
    name='choropleth',
    data=gdf,
    columns=['pc4_code', 'Price_per_m2_log'],
    key_on='feature.properties.pc4_code',
    fill_color='RdYlGn_r',  
    fill_opacity=0.8,
    line_opacity=0.2,
    bins=bins,  
    legend_name='Log-Scaled Average Price per m² (€)'
).add_to(m)

# Marker Cluster for Price Display
market_cluster = MarkerCluster().add_to(m)

for _, row in gdf.iterrows():
    if pd.notnull(row['Price_per_m2']):
        folium.Marker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            popup=(
                f"Zip Code: {row['pc4_code']}<br>"
                f"Avg. Price/m²: €{round(row['Price_per_m2'], 2)}<br>"
                f"City: {row.get('gem_name', 'Unknown')}"  
            ),
        ).add_to(market_cluster)

folium.LayerControl().add_to(m)
m.save('map.html')
print("✅ Map created!")