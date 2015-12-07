#!/usr/bin/env python

from click import echo, style, secho
from pandas import DataFrame, Series, read_pickle, concat, merge
from geopy.geocoders import GoogleV3
from IPython import embed

locations_cache = 'data/locations.pickle'

segments = DataFrame.from_csv('data/segments.tsv', sep='\t')
segments.columns = segments.columns.str.strip()
# Process segments
segments["people"] = segments.pop("People").str.split(',').tolist()
segments["n_people"] = segments['people'].apply(lambda r: len(r))

# Get all locations
def get_locations(row):
    return [row['Start'],row['End']]

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
    if row.geocode is None:
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

segments['geocode'] = segments['locations'].apply(apply_geocode)

embed()
