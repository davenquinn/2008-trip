d3 = require 'd3'
queue = require 'queue-async'
topojson = require 'topojson'

el = d3.select '#container'
  .style height: '100vh'
sz = el.node().getBoundingClientRect()

#Map projection
projection = d3.geo.albersUsa()
  .scale 1044.3916877314448
  .translate [sz.width / 2,sz.height / 2]
#translate to center the map in view
#Generate paths based on projection
path = d3.geo.path().projection(projection)
#Create an SVG
svg = el.append 'svg'
  .attr
    width: sz.width
    height: sz.height

queue()
  .defer d3.json, 'data/us-states.topojson'
  .defer d3.json, 'data/segments.json'
  .await (error, states, geodata) ->
    if error
      return console.log(error)

    mapLayer = svg.append 'g'
      .attr class: 'map-background'

    usa = topojson.feature(states,states.objects.collection)
    map = mapLayer.selectAll 'path'
      .data usa.features

    map.enter()
      .append 'path'
      .attr
        d: path
        'stroke-width': 0.5
        stroke: '#aaa'
        fill: 'white'

    dataLayer = svg.append 'g'

    sel = dataLayer.selectAll 'path'
      .data geodata.features

    colors =
      drive: "#e6550d"
      fly: "#ccc"
      bicycle: "#98df8a"

    sel.enter()
      .append 'path'
      .attr
        d: path
        stroke: (d)->
          colors[d.properties.mode]
        'stroke-width': (d)->1+0.3*(d.properties.n_people-1)
        'stroke-linecap': 'round'
        fill: 'none'

