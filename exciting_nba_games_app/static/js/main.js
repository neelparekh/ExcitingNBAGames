$(document).ready(function() {
  $("#verifyPhone").submit(() => {
    $.ajax({
    	type : "POST",
    	url : '/verify_phone',
    	dataType: "json",
    	data: JSON.stringify($("#phone").value()),
    	contentType: 'application/json;charset=UTF-8',
    	success: function (data) {
    		console.log(data);
    		}
      error: function (err) {
        console.log(err);
      }
    });
  });

});
