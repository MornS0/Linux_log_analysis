var boolPwd = false;
var boolIp = false;
var boolPort = false;

var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
// ip正则

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

    //判断ip地址格式是否正确
    var ip = $('#ip').val();
    if (ip != '') {
        if (reg.test(ip)) {
            $('#judgeIp').css("color", "#0000FF");
            $('#judgeIp').text("IP地址格式正确");
            boolIp = true;
        } else {
            $('#judgeIp').css("color", "#FF0000");
            $('#judgeIp').text("IP地址格式有误");
            boolIp = false;
        }
    }

    //判断端口号是否正确
    var port = $('#port').val();
    if (port != '') {
        if (parseInt(port) == Number(port) && parseInt(port) > 0 && parseInt(port) <= 65535) {
            $('#judgePort').css("color", "#FF000000");
            boolPort = true;
        } else {
            $('#judgePort').css("color", "#FF0000");
            boolPort = false;
        }
    }else{
        $('#judgePort').css("color", "#FF000000");
    }

    //判断是否可以点击提交表单
    if (boolPwd && boolIp && boolPort) {
        $('input[type="submit"]').removeAttr("disabled");
    } else {
        $('input[type="submit"]').attr("disabled", "disabled");
    }

}, 1000);