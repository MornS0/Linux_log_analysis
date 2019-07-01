// 开启/关闭自动更新
function switchFun(num, value) {
    if (value != '') {
        $.post('/admin/switch/', {
            'server_name': value
        }).done(function(data) {
            if (data == "wrong") {
                return;
            }
            var judge = JSON.parse(data);
            console.log(judge);
            if (judge.switch == 1) {
                $('.switch_result img').eq(num).attr("src", "/static/img/c11.png");
                $('.switch').eq(num).text("关闭");
            } else if (judge.switch == 0) {
                $('.switch_result img').eq(num).attr("src", "/static/img/9.png");
                $('.switch').eq(num).text("打开");
            }
        });
    }
}

// 更新服务器
function upgradeFun(num, value) {
    if (value != '') {
        $.post('/admin/receive/connect_get/', {
            'server_name': value
        }).done(function(data) {
            console.log(data);
            var judge = JSON.parse(data);
            if (judge.status == 1) {
                $('.upgrade').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/loading.gif" height="20px">');
                upgradeJudgeFun(num, value);
            } else if (judge.status == 0) {
                $('.upgrade').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/9.png" height="20px">');
            }
        });
    }
}

// 定时发送请求查看更新是否成功
function upgradeJudgeFun(num, value) {
    timer = setInterval(function() {
        $.post('/admin/receive/connect_get_judge/', {
            'server_name': value
        }).done(function(data) {
            console.log(data);
            var judge = JSON.parse(data);
            if (judge.status == 1) {
                $('.upgrade').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/c11.png" height="20px">');
                clearInterval(timer);
            } else if (judge.status == -1) {
                $('.upgrade').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/9.png" height="20px">');
                clearInterval(timer);
            } else {
            }
        });
    }, 1000);
}

// 测试是否能够连接远程服务器
function connectTestFun(num, value) {
    $('.connect').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/loading.gif" height="20px">');

    $.ajax('/admin/connect_test/', {
        method: 'post',
        data: {
            'server_name': value
        },
        success: function(data) {
            console.log(data);
            var judge = JSON.parse(data);
            if (judge.status == 1) {
                $('.connect').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/c11.png" height="20px">');
                $('.upgrade button').eq(num).removeAttr("disabled");
                $('.switch').eq(num).removeAttr("disabled");
            } else if (judge.status == 0) {
                $('.connect').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/9.png" height="20px">');
                $('.upgrade button').eq(num).attr("disabled", "disabled");
                console.log("sda");
                $('.switch').eq(num).attr("disabled", "disabled");
            } else {
                $('.connect').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/18.png" height="20px">');
                $('.upgrade button').eq(num).css("disabled", "disabled");
                $('.switch').eq(num).css("disabled", "disabled");
            }
        },
        error: function() {
            $('.connect').eq(num).html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/18.png" height="20px">');
            $('.upgrade button').eq(num).css("disabled", "disabled");
            $('.switch').eq(num).css("disabled", "disabled");
        }
    });
}