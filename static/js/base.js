function moveFun() {
    if ($('.navControl').css("left") <= "0px") {
        $('.nav').animate({
            left: 0
        }, 300);
        $('.navControl').animate({
            left: document.body.clientWidth / 10
        }, 300);
        $('.navControl').html("<br>隐<br>藏")
    } else {
        $('.nav').animate({
            left: document.body.clientWidth / -10
        }, 300);
        $('.navControl').animate({
            left: 0,
        }, 300);
        $('.navControl').html("<br>显<br>示")
    }
}
if ($('.nav').attr("control") == "0"){
    console.log(1);
    $('.nav').animate({
        left: document.body.clientWidth / -10
    }, 300);
    $('.navControl').animate({
        left: 0,
    }, 300);
    $('.navControl').html("<br>显<br>示")
}

// 窗口大小改变时导航栏位置自适应
window.onresize = function(){
    if ($('.navControl').css("left") <= "0px") {
        $('.nav').animate({
            left: document.body.clientWidth / -10
        }, 100);
        $('.navControl').animate({
            left: 0,
        }, 0);
        $('.navControl').html("<br>显<br>示")
    } else {
                $('.nav').animate({
            left: 0
        }, 100);
        $('.navControl').animate({
            left: document.body.clientWidth / 10
        }, 0);
        $('.navControl').html("<br>隐<br>藏")

    }
}


// 用户信息栏默认不可见
$('.userInfo').css("visibility", "hidden");
// 用户栏长度
var userWidth = $('.user').css('width');

// 移入用户，显示信息框
$('.user').mouseenter(function() {
    $('.userInfo').removeAttr("style");
    // 设置用户信息栏和用户栏长度相等
    $('.userInfo').width(userWidth);
    // 移入用户又移出用户框，信息框消失
    $('.user').mouseleave(function() {
            $('.userInfo').css("visibility", "hidden");
    });
});

// 移出用户
$('.user').mouseleave(function() {
    // 移出用户且移出信息框，信息框消失
    $('.userInfo').mouseleave(function() {
        $('.user').mouseleave(function() {
            $('.userInfo').css("visibility", "hidden");
        });
    });
    // 移出用户但移入信息框，显示信息框
    $('.userInfo').mouseenter(function() {
        $('.userInfo').removeAttr("style");
        // 设置用户信息栏和用户栏长度相等
        $('.userInfo').width(userWidth);
    });

});

// 移出信息框，信息框消失
$('.userInfo').mouseleave(function() {
    $('.userInfo').css("visibility", "hidden");
});
