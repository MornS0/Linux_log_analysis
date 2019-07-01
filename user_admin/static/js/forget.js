var boolPwd = true;

setInterval(function() {


    //判断密码是否重复
    var pwd1 = $('#password').val();
    var pwd2 = $('#password2').val();
    if (pwd1 != '' && pwd2 != '' && pwd1 != pwd2) {
        $('#judgePwd').css("color", "#FF0000");
        boolPwd = false;
    } else {
        $('#judgePwd').css("color", "#FF000000");
        boolPwd = true;
    }

    //判断是否可以点击提交表单
    if (boolPwd) {
        $('input[type="submit"]').removeAttr("disabled");
    } else {
        $('input[type="submit"]').attr("disabled", "disabled");
    }

}, 1000);