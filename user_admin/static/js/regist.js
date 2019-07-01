function judgeFun(value, type) {

    $.post('/regist_judge/', {
        'type': type,
        'value': value
    }).done(function(data) {
        var judge = JSON.parse(data);
        if (judge.type == "name") {
            if (judge.status == 0) {
                $('#judgeName').css("color", "#FF0000");
                $('#judgeName').text("用户名已存在");
                boolName = false;
            } else {
                $('#judgeName').css("color", "#0000FF");
                $('#judgeName').text("可以使用的用户名");
                boolName = true;
            }
        } else if (judge.type == "email") {
            if (judge.status == 0) {
                $('#judgeEmail').css("color", "#FF0000");
                $('#judgeEmail').text("邮箱已注册");
                boolEmail = false;
            } else {
                $('#judgeEmail').css("color", "#0000FF");
                $('#judgeEmail').text("可以使用的邮箱");
                boolEmail = true;
            }
        }

    })
}

var boolName = true;
var boolEmail = true;
var boolPwd = true;
var reg = /^([a-zA-Z]|[0-9])(\w|\-)+@[a-zA-Z0-9]+\.([a-zA-Z]{2,4})$/;
// 邮箱正则

setInterval(function() {

    //判断用户名邮箱是否可用
    var name = $('#name').val();
    if (name != '') {
        judgeFun(name, 'name');
    }
    var email = $('#email').val();
    if (email != '') {
        if (reg.test(email)) {
            judgeFun(email, 'email');
        } else {
            $('#judgeEmail').css("color", "#FF0000");
            $('#judgeEmail').text("邮箱格式不正确");
            boolEmail = false;
        }
    }

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
    if (boolName && boolEmail && boolPwd) {
        $('input[type="submit"]').removeAttr("disabled");
    } else {
        $('input[type="submit"]').attr("disabled", "disabled");
    }

}, 1000);