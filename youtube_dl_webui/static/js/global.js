var videoDownload = (function (Vue, extendAM){
    var videoDownload = {};
    var VueToast = window.vueToasts ? window.vueToasts.default || window.vueToasts : window.vueToasts;
    videoDownload.vm = null;
    videoDownload.tasksData = {
        headPath: 'http://localhost:5000/',
        videoList: [],
        videoListCopy: [],
        showModal: false,
        // tablist: ['status', 'details', 'file24s', 'peers', 'options'],
        tablist: ['Status', 'Details', 'Log'],
        showTab: 'Status',
        stateCounter: { all: 0, downloading: 0, finished: 0, paused: 0, invalid: 0},
        modalData: { url: '' },
        currentSelected: null,
        taskDetails: {},
        status: 'all',
        maxToasts: 4,
        position: 'bottom right',
        theme: 'error',
        timeLife: 3000,
        closeBtn: false
    };

    videoDownload.updateVm = function(res) {
        var that = videoDownload;
        if(that.vm){
            return false;
        }
        that.vm = new Vue({
            el: '#videoWrapper',
            data: that.tasksData,
            components:{
                'modal': {template: '#modal-template'},
                VueToast
            },
            watch:{
                stateCounter: function(val){
                    val.all = val.downloading + val.finished + val.paused + val.invalid;
                }
            },
            mounted: function () {
                this.resetOptions();
            },
            methods: {
                showAddTaskModal: function(){
                    this.modalData.url = '';
                    this.showModal = true;
                    this.$nextTick(function(){
                        this.$refs.url.focus();
                    });
                },
                addTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task';
                    Vue.http.post(url, _self.modalData, {emulateJSON: true}).then(function(res){ _self.showModal = false;
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                removeTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task/tid/' + (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid);
                    Vue.http.delete(url).then(function(res){
                        _self.showAlertToast('Task Delete', 'info');
                        _self.videoList.splice(_self.currentSelected, _self.currentSelected+1);
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                pauseTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task/tid/' +  (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid) + '?act=pause';
                    Vue.http.put(url).then(function(res){
                        _self.showAlertToast('Task Pause', 'info');
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                resumeTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task/tid/' + (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid) + '?act=resume';
                    Vue.http.put(url).then(function(res){
                        _self.showAlertToast('Task Resume', 'info');
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                selected: function(index){
                    var _self = this;
                    this.currentSelected = index;
                    console.log(this.currentSelected === index ? 'selected' : '');
                    var url = _self.headPath + 'task/tid/' +  (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid) + '/status';
                    console.log(url);
                    Vue.http.get(url).then(function(res){
                        console.log(res.data);
                        _self.taskDetails = JSON.parse(res.data).detail;
                        console.log(_self.taskDetails);
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                filterTasks: function(filterStatus) {
                    var _self = this;
                    _self.status = filterStatus;
                },
                speedConv: function(state, value) {
                    if (state == 'paused' || state == 'invalid')
                        return '0 B/s';
                    else if (state == 'finished')
                        return 'Done';
                    return this.bitsToHuman(value) + '/s';
                },
                etaConv: function(state, value) {
                    if (state == 'paused' || state == 'invalid' || state == 'finished')
                        return 'NaN';
                    return this.secondsToHuman(value);
                },
                progressConv: function(state, value) {
                    if (state == 'finished')
                        return 'Done';
                    return value;
                },
                bitsToHuman: function(value) {
                    var tmp = value, count = 0;
                    var metricList = [' B', ' KB', ' M', ' G', ' T',' P',' E',' Z'];

                    while(tmp/1024 > 1){
                        tmp = tmp/1024;
                        count++;
                    }
                    return tmp.toFixed(2) + metricList[count];
                },
                secondsToHuman: function(value) {
                    var tmp = '';
                    tmp = value % 60 + 's';
                    value = value/ 60;
                    if(value > 1){
                        tmp = parseInt(value % 60) + 'm' + tmp;
                        value = value / 60;
                        if(value > 1){
                            tmp = parseInt(value % 60) + 'h' + tmp;
                            value = value / 24;
                            if(value > 1){
                                tmp += parseInt(value % 24) + 'd' + tmp;
                            }
                        }
                    }
                    return tmp;
                },
                stateIcon: function(state) {
                    if (state == 'downloading')
                        return {'icon': 'fa-arrow-circle-o-down', 'color': 'blue'};
                    else if (state == 'paused')
                        return {'icon': 'fa-pause-circle-o', 'color': 'green'};
                    else if (state == 'finished')
                        return {'icon': 'fa-check-circle-o', 'color': 'grey'};
                    else
                        return {'icon': 'fa-times-circle-o', 'color': 'red'};
                },
                tsToLocal: function(timeStamp) {
                    if (typeof timeStamp == 'undefined' || Number(timeStamp) < 10)
                        return '';

                    var options = {
                        year: "numeric", month: "short", hour12: false,
                        day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit"
                    };
                    var d = new Date(0);
                    d.setUTCSeconds(timeStamp);
                    return d.toLocaleString('en-US', options);
                },
                resetOptions() {
                    this.$refs.toast.setOptions({
                        delayOfJumps: this.delayOfJumps,
                        maxToasts: this.maxToasts,
                        position: this.position
                    });
                },
                showAlertToast(msg, theme) {
                    this.$refs.toast.showToast(msg, {
                        theme: theme,
                        timeLife: this.timeLife,
                        closeBtn: this.closeBtn
                    });
                }
            }
        });
    };

    videoDownload.getTaskList = function() {
        var that = videoDownload;
        console.log(that.tasksData.headPath);
        var url = that.tasksData.headPath + 'task/list';
        url = url + '?state=' + that.tasksData.status;
        Vue.http.get(url).then(function(res){
            var resData = JSON.parse(res.body);
            that.tasksData.videoList = resData.detail;
            that.tasksData.stateCounter = resData.state_counter;
            that.tasksData.stateCounter.all = that.tasksData.stateCounter.downloading +
                                              that.tasksData.stateCounter.finished +
                                              that.tasksData.stateCounter.paused +
                                              that.tasksData.stateCounter.invalid;
            that.updateVm();
        }, function(err){
            console.log(err)
            that.vm.showAlertToast('Network connection lost', 'error');
        });
    };

    videoDownload.init = function(){
        var that = this;
        that.tasksData.headPath = window.location.protocol + '//' + window.location.host + '/';
        that.getTaskList();
        setInterval(videoDownload.getTaskList, 3000);
    }

    return videoDownload;
})(Vue, {});


videoDownload.init();
