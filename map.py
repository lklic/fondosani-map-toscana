import pandas as pd
import folium
import requests

# Load the dataset
df = pd.read_csv('STRUTTURE-TOSCANA.csv')

# Clean postal code format by converting float to string and handling missing values
df['Cap'] = df['Cap'].fillna('').apply(lambda x: str(int(x)) if x != '' else '')

# Ensure phone numbers are treated as strings without modification
df['Telefono'] = df['Telefono'].astype(str)

# Concatenate address fields to form a complete address
df['full_address'] = df['Indirizzo'] + ', ' + df['comune'] + ', ' + df['prov_estesa'] + ', ' + df['Cap']

# Set up Google Geocoding API
API_KEY = 'myapikeyhere'
base_url = 'https://maps.googleapis.com/maps/api/geocode/json'

# Assign colors to different structure types based on the updated list
structure_colors = {
    'CASA DI CURA': 'blue',
    'CENTRO DIAGNOSTICO': 'green',
    'CENTRO FISIOTERAPICO': 'purple',
    'CENTRO POLISPECIALISTICO': 'orange',
    'COOPERATIVA': 'darkblue',
    'LABORATORIO ANALISI': 'red',
    'PSICOLOGI': 'pink',
    'SOCIETA\' DI SERVIZI': 'darkgreen',
    'STUDIO ODONTOIATRICO': 'lightblue'
}

# Create a map centered around Florence
map_center = [43.7696, 11.2558]  # Florence coordinates
mymap = folium.Map(location=map_center, zoom_start=12)

# Create a dictionary to hold the feature groups for each structure type
feature_groups = {}

# Create FeatureGroups for each structure type
for structure_type, color in structure_colors.items():
    feature_groups[structure_type] = folium.FeatureGroup(
        name=f'<i class="fa fa-map-marker fa-2x" style="color:{color}"></i> {structure_type}', show=True
    )
    mymap.add_child(feature_groups[structure_type])

def geocode(address, index):
    try:
        print(f"Geocoding {index + 1}/{len(df)}: {address}...", end="")
        params = {
            'address': address,
            'key': API_KEY
        }
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            print(" Success!")
            return (location['lat'], location['lng'])
        else:
            print(f" Failed ({data['status']}).")
            return (None, None)
    except Exception as e:
        print(f" Failed with error: {e}")
        return (None, None)

# Apply geocoding with progress display
df['coordinates'] = [geocode(addr, idx) for idx, addr in enumerate(df['full_address'])]
df[['latitude', 'longitude']] = pd.DataFrame(df['coordinates'].tolist(), index=df.index)

# Add markers for each medical facility, categorized by structure type
for idx, row in df.iterrows():
    if pd.notnull(row['latitude']) and pd.notnull(row['longitude']):
        # Choose the color based on the structure type
        structure_type = row['DescrizioneTipoStruttura']
        color = structure_colors.get(structure_type, 'gray')
        
        # Create a Google Places link
        google_maps_link = f"https://www.google.com/maps/search/?api=1&query=Google+Places+for+{row['Nominativo']}"
        
        # Format the popup content with better HTML structure
        popup_content = (f"<div style='font-size:14px;'><b style='font-size:16px;'>{row['Nominativo']}</b><br>"
                         f"<b>Type:</b> {row['DescrizioneTipoStruttura']}<br>"
                         f"<b>Address:</b> {row['Indirizzo']}, {row['comune']}<br>"
                         f"<b>Phone:</b> {row['Telefono']}<br>"
                         f"<a href='{google_maps_link}' target='_blank'>View on Google Places</a></div>")
        
        # Add the marker to the appropriate feature group
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.Icon(color=color)
        ).add_to(feature_groups[structure_type])

# Add a layer control to allow toggling of different structure types (without OSM selector)
layer_control = folium.LayerControl(collapsed=False, autoZIndex=False)
mymap.add_child(layer_control)

# Save the map to an HTML file
output_file = 'index.html'
mymap.save(output_file)
print(f"\nMap saved to {output_file}")