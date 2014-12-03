window.COLORS = ['#218693', '#C75646'];

window.getNextColor = function() {
   var next = window.COLORS.pop();
   window.COLORS.unshift(next);
   return next;
}
