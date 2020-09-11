$(document).ready(function() {
  $("#validateLoading").hide();
  $("#verifyLoading").hide();
  $('.toast').toast('show');
  $('#verifyBtn').click(function(){
    $("#verifyBtn").hide();
    $("#verifyLoading").show();
  });
});
