#!/usr/bin/env python

from click import echo, style, secho
from pandas import DataFrame, Series, read_pickle, concat, merge, isnull
from geopy.geocoders import GoogleV3
from IPython import embed

locations_cache = 'data/locations.pickle'

segments = DataFrame.from_csv('data/segments.tsv', index_col=None, sep='\t')
segments.columns = segments.columns.str.strip().str.lower()
# Process segments
segments["people"] = segments["people"].str.split(',').tolist()
segments["n_people"] = segments['people'].apply(lambda r: len(r))

# Get all locations
def get_locations(row):
    if not isnull(row.via):
        via = row.via.split(';')
    else:
        via = []
    return [row.start]+via+[row.end]

segments['locations'] = segments.apply(get_locations, axis=1)
locations = Series(segments['locations'].sum())
locations.name = "Location"
locations = locations.drop_duplicates()
locations = DataFrame(index=locations)

try:
    # Get locations from cache
    cached_locations = read_pickle(locations_cache)
    locations = concat((locations,cached_locations), axis=1)
except FileNotFoundError:
    locations["geocode"] = None

# Geolocate new locations
geolocator = GoogleV3()

def geolocate(row):
    if isnull(row.geocode):
        _ = style(row.name, fg='magenta')
        echo("Geolocating "+_+"...",nl=False)
        loc = geolocator.geocode(row.name)
        row.geocode = (loc.longitude,loc.latitude)
        secho("done", fg='green')
    return row

locations = locations.apply(geolocate, axis=1)
# Save to cache
locations.to_pickle(locations_cache)

def apply_geocode(val):
    return [locations.ix[i].geocode for i in val]

segments['waypoints'] = segments['locations'].apply(apply_geocode)

def properties(row):
    fields = ('mode','n_people','date','people','start','end','miles')
    return {k:row[k] for k in fields}

props = segments.apply(properties, axis=1)
props.name = 'properties'
df = DataFrame(props)
df['geometry'] = segments['waypoints'].apply(lambda x: dict(
    coordinates=x,type='LineString'))
df['type'] = 'Feature'

s = df.to_json(orient='records')
s = '{"type":"FeatureCollection","features":'+s+'}'

with open('data/segments.json','w') as f:
    f.write(s)

