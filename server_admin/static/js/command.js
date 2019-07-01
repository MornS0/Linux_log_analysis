function judgeFun(value) {
    if (value != '') {
        $.post('/admin/command_judge/', {
            'server_name': value,
        }).done(function(data) {
            if (data == "wrong") {
                $('.connect').text("未知错误...");
                return;
            }
            var judge = JSON.parse(data);
            console.log(data)
            console.log(judge.connect_status)
            if (judge.connect_status == 1) {
                $('.connect').text("连接成功");
                $('.connect').css("color", "green");
                $('.send').removeAttr("disabled");
                clearInterval(timer);
                var myDate = new Date();
                if($('.type').text() == "单命令模式"){
                    $('.get').html(myDate.toLocaleString() + "&nbsp;&nbsp;&nbsp;" + server_user + ">>");
                }
            } else if (judge.connect_status == 0) {
                $('.connect').text("连接中...");
                $('.connect').css("color", "blue");
            } else if (judge.connect_status == -1) {
                $('.connect').text("连接失败...");
                $('.connect').css("color", "red");
                clearInterval(timer);
            }
        });
    }
}

function sendCmd() {
    var cmd = $('.cmd').val();
    $('.cmd').val("");
    if($('.type').text() == "交互模式"){
        var type = "invoke";
    }else{
        var type = "single";
    }

    if (cmd != '') {
        $.ajax('/admin/command_deal/', {
            method: 'post',
            data: {
                'command': cmd,
                'cmd_type': type
            },
            success: function(data) {
                var judge = JSON.parse(data);
                if (judge.msg == "已关闭连接") {
                    $('.connect').text("连接已关闭");
                    $('.send').attr("disabled", "disabled");
                }
                msg = judge.msg.replace(/\n/g, "<br>").replace(/ /g, "&nbsp;&nbsp;").replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;");
                var get = $('.get').html();
                if(type == "single"){
                    var myDate = new Date();
                    $('.get').html(get + cmd + "<br>" + msg + myDate.toLocaleString() + "&nbsp;&nbsp;&nbsp;" + server_user + ">>");
                }else{
                    $('.get').html(get + msg);
                }
                $('.get').scrollTop($('.get').get(0).scrollHeight);
                //滑轮固定到底端
            },
            error: function() {
                $('.connect').text("连接已关闭");
                $('.send').attr("disabled", "disabled");
            }
        });
    }

}

function emptyCmd() {
    $('.get').empty();
}

var server_name = $('.name').text();
var server_user = $('.name').attr("user");

$('.send').attr("disabled", "disabled");
$('input[type="text"]').eq(0).select();

// 循环检测是否成功
timer = setInterval(function() {
    judgeFun(server_name);
}, 1000);

$('input[type="text"]').eq(0).mouseenter(function() { $('input[type="text"]').eq(0).select(); });
$(document).keyup(function(event) {
    if (event.keyCode == 13) { //按下回车发送
        sendCmd();
    }
});