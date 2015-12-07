window.d3 = require 'd3'
window.topojson = require 'topojson'
datamaps = require 'datamaps-all-browserify'

el = document.getElementById 'container'
d3.select(el).style height: '100vh'

map = new Datamap
  element: el
  scope: 'usa'
  responsive: true

d3.select window
  .on 'resize', -> map.resize()

