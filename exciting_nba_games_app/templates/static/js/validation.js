$(document).ready(function() {
  $("#validateLoading").hide();
  $("#verifyLoading").hide();
  $('.toast').toast('show');

  $('#validateBtn').click(function(){
    $("#validateBtn").hide();
    $("#validateLoading").show();
  });

  $('#verifyBtn').click(function(){
    $("#verifyBtn").hide();
    $("#verifyLoading").show();
  });
});
