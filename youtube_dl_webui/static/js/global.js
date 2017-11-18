var videoDownload = (function (Vue, extendAM){
    var videoDownload = {};
    var VueToast = window.vueToasts ? window.vueToasts.default || window.vueToasts : window.vueToasts;
    videoDownload.vm = null;
    videoDownload.tasksData = {
        headPath: 'http://localhost:5000/',
        videoList: [],
        videoListCopy: [],
        showModal: false,
        modalType: 'addTask',
        // tablist: ['status', 'details', 'file24s', 'peers', 'options'],
        tablist: ['Status', 'Details', 'Log'],
        showTab: 'Status',
        stateCounter: { all: 0, downloading: 0, finished: 0, paused: 0, invalid: 0},
        modalData: {
            add: { url: '', ydl_opts: {} },
            remove: { removeFile: false },
            preference: {youtube_dl: {fomart: '', proxy: ''}, general: {download_dir: '', db_path: '', log_size: ''}},
        },
        currentSelected: null,
        taskDetails: {},
        taskInfoUrl: null,
        status: 'all',
        maxToasts: 4,
        position: 'bottom right',
        theme: 'error',
        timeLife: 3500,
        closeBtn: false
    };

    videoDownload.createVm = function(res) {
        var that = videoDownload;
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
                setInterval(videoDownload.timeOut, 3000);
            },
            methods: {
                showAddTaskModal: function(){
                    this.modalData.add.url = '';
                    this.showModal = true;
                    this.modalType = 'addTask';
                    console.log(this.modalData);
                    this.$nextTick(function(){
                        this.$refs.url.focus();
                    });
                },
                execFunction: function(){
                    switch(this.modalType) {
                        case 'addTask':
                            this.addTask();
                            break;
                        case 'removeTask':
                            this.removeTask();
                            break;
                        case 'updatePreference':
                            this.updatePreference();
                            break;
                    }
                },
                showRemoveTaskModal: function(){
                    this.modalData.remove.removeFile = false;
                    this.showModal = true;
                    this.modalType = 'removeTask';
                },
                addTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task';
                    for (var key in _self.modalData.add.ydl_opts) {
                        if (_self.modalData.add.ydl_opts[key].trim() == '')
                            delete _self.modalData.add.ydl_opts[key];
                    }
                    Vue.http.post(url, _self.modalData.add, {emulateJSON: false}).then(function(res){
                        _self.showModal = false;
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                updatePreference: function () {
                    var _self = this;
                    var url = _self.headPath + 'config';
                    Vue.http.post(url, _self.modalData.preference, {emulateJSON: false}).then(function(res){
                        console.log("Successfully");
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                removeTask: function(){
                    var _self = this;
                    var url = _self.headPath + 'task/tid/' + (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid);
                    if(_self.modalData.remove.removeFile){
                        url += '?del_file=true';
                    }
                    Vue.http.delete(url).then(function(res){
                        _self.showAlertToast('Task Delete', 'info');
                        _self.videoList.splice(_self.currentSelected, _self.currentSelected+1);
                        _self.showModal = false;
                        that.getTaskList();
                    }, function(err){
                        _self.showAlertToast(err, 'error');
                    });
                },
                removeData: function(){
                    this.modalData.remove.removeFile = true;
                    this.removeTask();
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
                about: function() {
                    this.showModal = true;
                    this.modalType = 'about';
                },
                preference: function() {
                    var _self = this;
                    var url = _self.headPath + 'config';

                    this.showModal = true;
                    this.modalType = 'updatePreference';
                    Vue.http.get(url).then(function(res) {
                        var responseJSON = JSON.parse(res.data);
                        if (responseJSON.status === 'error') {
                            return false;
                        } else {
                            config = responseJSON['config'];
                            _self.modalData.preference.general.download_dir = config.general.download_dir;
                            _self.modalData.preference.general.db_path = config.general.db_path;
                            _self.modalData.preference.general.log_size = config.general.log_size;
                            _self.modalData.preference.youtube_dl.format = config.youtube_dl.format;
                            _self.modalData.preference.youtube_dl.proxy = config.youtube_dl.proxy;
                        }
                    });
                },
                selected: function(index){
                    var _self = this;
                    this.currentSelected = index;
                    _self.taskInfoUrl = _self.headPath + 'task/tid/' +  (_self.videoList[_self.currentSelected] && _self.videoList[_self.currentSelected].tid) + '/status';
                    _self.getTaskInfoById();
                },
                getTaskInfoById: function(){
                    var _self = this;
                    if(!_self.taskInfoUrl) return false;
                    Vue.http.get(_self.taskInfoUrl).then(function(res){
                        var responseJSON = JSON.parse(res.data);
                        if(responseJSON.status === 'error'){
                            return false;
                        }
                        _self.taskDetails = responseJSON.detail;
                    }, function(err){
                        _self.showAlertToast('Network connection lost', 'error');
                    });
                },
                filterTasks: function(filterStatus) {
                    var _self = this;
                    _self.status = filterStatus;
                    that.getTaskList();
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
                    if(value > 1) {
                        tmp = parseInt(value % 60) + 'm' + tmp;
                        value = value / 60;
                        if(value > 1) {
                            tmp = parseInt(value % 60) + 'h' + tmp;
                            value = value / 24;
                            if(value > 1) {
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
        }, function(err){
            that.vm.showAlertToast('Network connection lost', 'error');
        });
    };

    videoDownload.timeOut = function(){
        var that = videoDownload;
        that.getTaskList();
        that.vm.getTaskInfoById();
    };

    videoDownload.init = function(){
        var that = this;
        that.tasksData.headPath = window.location.protocol + '//' + window.location.host + '/';
        that.createVm();
        that.getTaskList();
    }

    return videoDownload;
})(Vue, {});


videoDownload.init();
