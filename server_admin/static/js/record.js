function getLocation(id) {
    var ip = $('#' + id + ' .ip').text();
    var sign = $.md5("ip=" + ip + "&token=" + "输入你ip138接口的token");
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
                'type': -1,
            }).done(function(data) {
                if (data == "wrong") {
                    $('.connect').text("未知错误，点击重试！");
                    return;
                }
                var judge = JSON.parse(data);
                // console.log(data);
                row = judge.row;
                records = judge.data;
                name = $('.name').text();
                for (i = 0; i < records.length; i++) {
                    // 包括日期、登录时间、登出时间、总用时、用户名、IP、端口、登录类型
                    id = i + row;
                    date = records[i][0];
                    logon_time = records[i][1];
                    logout_time = records[i][2];
                    use_time = records[i][3];
                    user = records[i][4];
                    ip = records[i][5];
                    port = records[i][6];
                    type = records[i][7];

                    trAddHtml = "<tr id=\"" + id + "\">" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + date + "</td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + logon_time + "</td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + logout_time + "</td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + use_time + "</td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + user + "</td>" +
                        "<td class=\"ip\" width=\"150px\" height=\"30px\" align=\"center\">" + ip + "</td>" +
                        "<td class=\"location\" width=\"150px\" height=\"30px\" align=\"center\"><button onclick=\"getLocation('" + id + "')\">查询</button></td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + port + "</td>" +
                        "<td width=\"150px\" height=\"30px\" align=\"center\">" + type + "</td>"

                    // console.log(trAddHtml);
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