$.get('/get_code/');
$('.code').attr("src", "/static/img/code.png/?new=" + Math.random());
$('.code').click(function(){
	$.get('/get_code/');
	$('.code').attr("src", "/static/img/code.png/?new=" + Math.random());
})