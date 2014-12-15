/*
window.COLORS = ['#C75646', '#218693', '#AA82B3']; // '#1565C0' '#00695C',  purp'#4527A0'

window.getNextColor = function() {
   var next = window.COLORS.pop();
   window.COLORS.unshift(next);
   return next;
}
*/

window.TERMINATORS = '.?!'
window.BRIDGE = ',:;'

window.isTerminator = function(str) {
   return window.TERMINATORS.indexOf(str) != -1;
}

window.isBridge = function(str) {
   return window.BRIDGE.indexOf(str) != -1;
}

window.positionCache = {};

window.positionCache_get = function(src, term) {
   return positionCache[src] && positionCache[src][term];
}

window.positionCache_set = function(src, term, positions) {
   if (!(src in window.positionCache))
      window.positionCache[src] = {}
   window.positionCache[src][term] = positions;
}
