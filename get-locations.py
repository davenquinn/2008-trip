#!/usr/bin/env python

from click import echo, style, secho
from pandas import DataFrame, Series, read_pickle, concat, merge, isnull
from geopy.geocoders import GoogleV3
from directions import Google, Mapbox
from time import sleep
from IPython import embed

from config import MAPBOX_TOKEN

locations_cache = 'data/locations.pickle'
routes_cache = 'data/routes.pickle'

magenta = lambda x: style(x, fg='magenta')
cyan = lambda x: style(x, fg='cyan')

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
        _ = magenta(row.name)
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

def hash_geocode(val):
    return hash(tuple(val))

segments['geocode'] = segments['locations'].apply(apply_geocode)
segments['hash'] = segments['geocode'].apply(hash_geocode)
segments.set_index('hash', inplace=True)

try:
    # Get locations from cache
    cached_routes = read_pickle(routes_cache)
except FileNotFoundError:
    cached_routes = DataFrame({'directions': []}, index=[])

segments = segments.join(cached_routes,rsuffix='_cached')

#google = Google(rate_limit_dt=2)
mapbox = Mapbox(MAPBOX_TOKEN, rate_limit_dt=2)
def get_route(row):
    mode = row['mode']

    if mode == 'fly':
        return row
    elif mode == 'bicycle':
        kwargs = dict(mode='cycling')
    elif mode == 'drive':
        kwargs = dict()

    if str(row.directions) == 'nan':
        a = magenta(row['start'])
        b = magenta(row['end'])
        echo("Getting directions from "+a+" to "+b+".")
        try:
            route = mapbox.route(row.geocode)[0]
            row['directions'] = route.coords
            row['geocode'] = row['directions']
        except IndexError:
            echo("Server not responding")
            return row
    row['geocode'] = row['directions']
    return row

segments = segments.apply(get_route, axis=1)

# Create segments cache
cached_routes = DataFrame({
    'directions': segments['directions']},
    index=segments.index)
cached_routes.to_pickle(routes_cache)

def write_geojson(dataframe, fn):
    def properties(row):
        fields = ('mode','n_people','date','people','start','end','miles')
        return {k:row[k] for k in fields}

    props = dataframe.apply(properties, axis=1)
    props.name = 'properties'
    df = DataFrame(props)
    df['geometry'] = segments['geocode'].apply(lambda x: dict(
        coordinates=x,type='LineString'))
    df['type'] = 'Feature'

    s = df.to_json(orient='records')
    s = '{"type":"FeatureCollection","features":'+s+'}'

    with open(fn,'w') as f:
        f.write(s)

write_geojson(segments[segments['mode'] == 'bicycle'], 'data/bicycle.json')
write_geojson(segments, 'data/segments.json')
