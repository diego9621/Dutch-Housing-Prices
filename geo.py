import geopandas as gpd

# Load the GeoJSON file
geojson_file = 'zipcodes.geojson'
gdf = gpd.read_file(geojson_file)

# Print column names
print(gdf['gem_name'].head())
