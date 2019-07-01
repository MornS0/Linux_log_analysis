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
                zoom: 1,
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


