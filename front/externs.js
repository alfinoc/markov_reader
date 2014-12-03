window.COLORS = ['#1565C0', '#00695C',  '#4527A0']; // '#218693' '#C75646'
// 1:blue 2:green
window.getNextColor = function() {
   var next = window.COLORS.pop();
   window.COLORS.unshift(next);
   return next;
}
