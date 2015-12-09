d3 = require 'd3'
queue = require 'queue-async'
topojson = require 'topojson'

el = d3.select '#container'
  .style height: '100vh'
sz = el.node().getBoundingClientRect()

#Map projection
projection = d3.geo.albersUsa()
  .scale sz.width*1.2
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
    lower48 = usa.features.filter (d)->
      ['Alaska','Hawaii'].indexOf(d.properties.NAME) == -1

    map = mapLayer.selectAll 'path'
      .data lower48

    map.enter()
      .append 'path'
      .attr
        d: path
        'stroke-width': 1
        stroke: '#fff'
        fill: '#f0f0f0'

    dataLayer = svg.append 'g'

    # Put flights on top
    data = geodata.features.sort (a,b)->
      return 1 if a.properties.mode == 'fly'
      return -1

    sel = dataLayer.selectAll 'path'
      .data data

    colors =
      drive: "#e6550d"
      fly: "#aaa"
      bicycle: "#4CB963"

    sel.enter()
      .append 'path'
      .attr
        d: path
        stroke: (d)->
          colors[d.properties.mode]
        'stroke-width': (d)->1.5+0.5*(d.properties.n_people-1)
        'stroke-linecap': 'round'
        'stroke-dasharray': (d)->
          return null if d.properties.mode != 'fly'
          return '5, 4'
        'stroke-dashadjust': 'compress'
        fill: 'none'

