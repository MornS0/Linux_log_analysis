$(function() {
        /*
         smallimg   // 小图
         bigimg  //点击放大的图片
         mask   //黑色遮罩
         */
        var obj = new zoom('mask', 'bigimg', 'smallimg');
        obj.init();
    })
function zoom(mask, bigimg, smallimg) {
    this.bigimg = bigimg;
    this.smallimg = smallimg;
    this.mask = mask
}
zoom.prototype = {
    init: function() {
        var that = this;
        this.smallimgClick();
        this.maskClick();
        this.mouseWheel()
    },
    smallimgClick: function() {
        var that = this;
        $("." + that.smallimg).click(function() {
            $("." + that.bigimg).css({ height: $("." + that.smallimg).height() * 1.5, width: $("." + that.smallimg).width() * 1.5 });
            $("." + that.mask).fadeIn();
            $("." + that.bigimg).attr("src", $(this).attr("src")).fadeIn()
        })
    },
    maskClick: function() {
        var that = this;
        $("." + that.mask).click(function() {
            $("." + that.bigimg).fadeOut();
            $("." + that.mask).fadeOut()
        })
    },
    mouseWheel: function() {
        function mousewheel(obj, upfun, downfun) {
            if (document.attachEvent) { obj.attachEvent("onmousewheel", scrollFn) } else {
                if (document.addEventListener) {
                    obj.addEventListener("mousewheel", scrollFn, false);
                    obj.addEventListener("DOMMouseScroll", scrollFn, false)
                }
            }

            function scrollFn(e) { var ev = e || window.event; var dir = ev.wheelDelta || ev.detail; if (ev.preventDefault) { ev.preventDefault() } else { ev.returnValue = false } if (dir == -3 || dir == 120) { upfun() } else { downfun() } }
        }
        var that = this;
        mousewheel($("." + that.bigimg)[0], function() {
            if ($("." + that.bigimg).innerWidth() > $("body").width() - 20) { alert("不能再放大了"); return }
            if ($("." + that.bigimg).innerHeight() > $("body").height() - 50) { alert("不能再放大"); return }
            var zoomHeight = $("." + that.bigimg).innerHeight() * 1.03;
            var zoomWidth = $("." + that.bigimg).innerWidth() * 1.03;
            $("." + that.bigimg).css({ height: zoomHeight + "px", width: zoomWidth + "px" })
        }, function() {
            if ($("." + that.bigimg).innerWidth() < 100) { alert("不能再缩小了哦！"); return }
            if ($("." + that.bigimg).innerHeight() < 100) { alert("不能再缩小了哦！"); return }
            var zoomHeight = $("." + that.bigimg).innerHeight() / 1.03;
            var zoomWidth = $("." + that.bigimg).innerWidth() / 1.03;
            $("." + that.bigimg).css({ height: zoomHeight + "px", width: zoomWidth + "px" })
        })
    }
};


$.ajax('/admin/receive/geo_get/', {
        method: 'post',
        data: {
            'server_name': $('.name').text(),
        },
        success: function(data) {
            var result = JSON.parse(data);

            data = result.data;
            console.log(data);
            var map = Loca.create('container', {
                mapStyle: 'amap://styles/midnight',
                zoom: 4,
                center: [120.472973, 31.298494],
                features: ['bg', 'road'],
                viewMode: '3D'
            });

            var layer = Loca.visualLayer({
                eventSupport: true,
                container: map,
                type: 'point',
                shape: 'circle'
            });

            layer.on('mousemove', function(ev) {

                var rawData = ev.rawData;
                // 原始鼠标事件
                var originalEvent = ev.originalEvent;

                openInfoWin(map.getMap(), originalEvent, {
                    '地点': rawData.loc,
                    'IP': rawData.ip,
                    '位置': rawData.经纬度,
                    '总登录次数': rawData.times
                });

                $('td .label, td .content').css("color", "#ffffff");
                // 字体设置白色
            });

            layer.on('mouseleave', function(ev) {
                closeInfoWin();
            });

            layer.setData(data, {
                lnglat: '经纬度',
                type: 'csv'
            });

            layer.setOptions({
                style: {
                    // 圆形半径，单位像素
                    radius: 10,
                    // 填充颜色
                    color: '#f3ad6a',
                    // 描边颜色
                    borderColor: '#252e64',
                    // 描边宽度，单位像素
                    borderWidth: 1,
                    // 透明度 [0-1]
                    opacity: 0.9,
                },
                selectStyle: {
                radius: 15,
                color: '#ffe30a'
            }
            });

            layer.render();
        }
    });


