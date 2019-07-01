function sendCmd(name, id) {
    var ip_status_judge = $('#' + id + ' .ban').text();
    var ip = $('#' + id + ' .ip').text();
    if (ip_status_judge == "已封禁") {
        ip_status = 1
    } else if (ip_status_judge == "未封禁") {
        ip_status = 0
    }
    $('#' + id + ' .msg').html('&nbsp;&nbsp;<img style="vertical-align: middle;" src="/static/img/loading.gif" height="20px">');

    $.ajax('/admin/log_command/', {
        method: 'post',
        data: {
            'server_name': name,
            'ip': ip,
            'type': ip_status,
        },
        success: function(data) {
            var judge = JSON.parse(data);
            console.log(data);
            if (judge.ip_status == 1) {
                if (ip_status_judge == "已封禁") {
                    $('#' + id + ' .banBtn').text("封禁");
                    $('#' + id + ' .ban').text("未封禁");
                } else if (ip_status_judge == "未封禁") {
                    $('#' + id + ' .banBtn').text("解封");
                    $('#' + id + ' .ban').text("已封禁");
                }
                $('#' + id + ' .msg').css("color", "blue");
                $('#' + id + ' .msg').text("操作成功");
            } else {
                $('#' + id + ' .msg').text("操作失败");
                $('#' + id + ' .msg').css("color", "red");
            }
        }
    });
}

function getLocation(id) {
    var ip = $('#' + id + ' .ip').text();
    var sign = $.md5("ip=" + ip + "&token=" + "输入你ip138接口的token");
    // ip138接口
    $.ajax({
        url: "http://api.ip138.com/query/?ip=" + ip + "&callback=find&oid=" + "输入oid" + "&mid=" + "输入mid" + "&sign=" + sign,
        type: "get",
        dataType: "jsonp",
        jsonpCallback: "find",
        // jsonp格式： xxx(json)
        // 所以该参数对于外面是什么包着的，就是什么，比如这里是find
        success: function(data) {
            // 返回值：find({"ret":"ok","ip":"106.47.98.222","data":["中国","天津","天津","电信","",""]})
            // find({"ret":"ok","ip":"82.13.21.43","data":["英国","","","","",""]})
            var array_location = data.data;
            if (array_location[1] == "") {
                $('#' + id + ' .location').text(array_location[0]);
            } else if (array_location[2] == "") {
                $('#' + id + ' .location').text(array_location[1]);
            } else {
                $('#' + id + ' .location').text(array_location[2]);
            }
        },
        error: function(data) {
            console.log("wrong");
        }
    });

}

$(window).scroll(
    function() {
        var scrollTop = $(this).scrollTop();
        var scrollHeight = $(document).height();
        var windowHeight = $(this).height();
        // console.log("scrollTop:" + scrollTop);
        // console.log("scrollHeight:" + scrollHeight);
        // console.log("windowHeight:" + windowHeight);

        if (scrollHeight - (scrollTop + windowHeight) <= 1) {
            $.post('/admin/log_add/', {
                'server_name': $('.name').text(),
                'type': 1,
            }).done(function(data) {
                if (data == "wrong") {
                    $('.connect').text("未知错误，点击重试！");
                    return;
                }
                var judge = JSON.parse(data);
                console.log(data);
                row = judge.row;
                ips = judge.data;
                name = $('.name').text();
                for (i = 0; i < ips.length; i++) {
                    id = i + row;
                    date = ips[i][0];
                    ip = ips[i][1];
                    times = ips[i][2];
                    if (ips[i][3] == "1") {
                        ban = "已封禁";
                        ban_btn = "解封";
                    } else {
                        ban = "未封禁";
                        ban_btn = "封禁";
                    }
                    trAddHtml = "<tr id=\"" + id + "\">" + 
                    "<td width=\"150px\" height=\"30px\" align=\"center\">" + date + "</td>" + 
                    "<td class=\"ip\" width=\"150px\" height=\"30px\" align=\"center\">" + ip + "</td>" + 
                    "<td class=\"location\" width=\"150px\" height=\"30px\" align=\"center\"><button onclick=\"getLocation('" + id + "')\">查询</button></td>" + 
                    "<td width=\"150px\" height=\"30px\" align=\"center\">" + times + "</td>" + 
                    "<td class='ban' width=\"150px\" height=\"30px\" align=\"center\">" + ban + "</td>" + 
                    "<td width=\"70px\" height=\"30px\" align=\"center\"><button class=\"banBtn\" onclick=\"sendCmd('" + name + "', '" + id + "')\">" + ban_btn + "</button></td>" + 
                    "<td align=\"center\"><font class=\"msg\">无</font></td>" + 
                    "</tr>"

                    console.log(trAddHtml);
                    $(".table ").append(trAddHtml);
                }
            });

        }
    })

function sleep(numberMillis) {
    var now = new Date();
    var exitTime = now.getTime() + numberMillis;
    while (true) {
        now = new Date();
        if (now.getTime() > exitTime)
            return;
    }
}