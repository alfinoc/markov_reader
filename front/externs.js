window.positionCache = {};

window.positionCache_get = function(src, term) {
   return positionCache[src] && positionCache[src][term];
}

window.positionCache_set = function(src, term, positions) {
   if (!(src in window.positionCache))
      window.positionCache[src] = {}
   window.positionCache[src][term] = positions;
}

window.AJAX_HOST_PREFIX = 'http://104.236.145.31/markov/'

