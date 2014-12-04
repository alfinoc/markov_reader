window.COLORS = ['#C75646', '#218693', '#AA82B3']; // '#1565C0' '#00695C',  purp'#4527A0'
// 1:blue 2:green
window.getNextColor = function() {
   var next = window.COLORS.pop();
   window.COLORS.unshift(next);
   return next;
}
