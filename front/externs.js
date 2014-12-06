window.COLORS = ['#C75646', '#218693', '#AA82B3']; // '#1565C0' '#00695C',  purp'#4527A0'

window.getNextColor = function() {
   var next = window.COLORS.pop();
   window.COLORS.unshift(next);
   return next;
}

window.TERMINATORS = '.?!'
window.BRIDGE = ',:;'

window.isTerminator = function(str) {
   return window.TERMINATORS.indexOf(str) != -1;
}

window.isBridge = function(str) {
   return window.BRIDGE.indexOf(str) != -1;
}
