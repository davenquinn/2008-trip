#!/usr/bin/env python

from click import echo, style, secho
from pandas import DataFrame, read_pickle, concat, merge
from geopy.geocoders import GoogleV3
from IPython import embed

locations_cache = 'data/locations.pickle'

df = DataFrame.from_csv('data/test.tsv', sep='\t')
df.columns = df.columns.str.strip()

# Get all locations
_ = df.ix[:,'Start'],df.ix[:,'End']
_ = concat(_,axis=0).reset_index()[0]
_.name = "Location"
series = _.drop_duplicates()
locations = DataFrame(index=series)

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

embed()


