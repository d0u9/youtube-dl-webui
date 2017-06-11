var videoDownload = (function (Vue, extendAM){
        var videoDownload = {};
        videoDownload.vm = null;
        videoDownload.tasksData = {
                headPath: 'http://localhost:5000/',
                videoList: [],
                videoListCopy: [],
                showModal: false,
                tablist: ['status', 'details', 'files', 'peers', 'options'],
                showTab: 'status',
                stateCounter: { all: 0, downloading: 0, finished: 0, paused: 0, invalid: 0},
                modalData: { url: '' },
                currentSelected: null,
                status: 'all'
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
                              'modal': {template: '#modal-template'}
                        },
                        watch:{
                                stateCounter: function(val){
                                        val.all = val.downloading + val.finished + val.paused + val.invalid;
                                }
                        },
                        methods: {
                                addTask: function(){
                                        var _self = this;
                                        var url = _self.headPath + 'task';
                                        Vue.http.post(url, _self.modalData, {emulateJSON: true}).then(function(res){
                                                _self.showModal = false;
                                                that.init();
                                        }, function(err){
                                                console.log(err);
                                        });
                                },
                                removeTask: function(){
                                        var _self = this;
                                        var url = _self.headPath + 'task/tid/' + _self.videoList[_self.currentSelected].tid;
                                        Vue.http.delete(url).then(function(res){
                                            alert('deleted');
                                            _self.videoList.splice(_self.currentSelected, _self.currentSelected+1);
                                        }, function(err){
                                            alert('delete failed');
                                        });
                                },
                                pauseTask: function(){
                                    var _self = this;
                                    var url = _self.headPath + 'task/tid/' + _self.videoList[_self.currentSelected].tid + '?act=pause';
                                    Vue.http.put(url).then(function(res){
                                        alert('paused');
                                    }, function(err){
                                        alert(err);
                                    });
                                },
                                resumeTask: function(){
                                    var _self = this;
                                    var url = _self.headPath + 'task/tid/' + _self.videoList[_self.currentSelected].tid + '?act=resume';
                                    Vue.http.put(url).then(function(res){
                                        alert('resumed');
                                    }, function(err){
                                        alert(err);
                                    });
                                },
                                selected: function(index){
                                       var _self = this;
                                       this.currentSelected = index;
                                       console.log(this.currentSelected === index ? 'selected' : '');
                                       var url = _self.headPath + 'task/tid/' + _self.videoList[_self.currentSelected].tid + '/status';
                                       Vue.http.get(url).then(function(res){
                                           console.log(res);
                                       }, function(err){
                                           alert(err);
                                       });
                                },
                                filterTasks: function(filterStatus){
                                    var _self = this;
                                    _self.status = filterStatus;
                                    videoDownload.getTaskList();
                                },
                                bitesToHuman: function(value){
                                    return (value/1048576).toFixed(2);
                                }
                        }
                });
        };

        videoDownload.getTaskList = function() {
                var that = videoDownload;
                that.tasksData.headPath = window.location.protocol + '//' + window.location.host + '/';
                console.log(that.tasksData.headPath);
                var url = that.tasksData.headPath + 'task/list';
                url = url + '?state=' + that.tasksData.status;
                Vue.http.get(url).then(function(res){
                        var resData = JSON.parse(res.body);
                        that.tasksData.videoList = resData.detail;
                        that.tasksData.stateCounter = resData.state_counter;
                        that.tasksData.stateCounter.all = that.tasksData.stateCounter.downloading + that.tasksData.stateCounter.finished + that.tasksData.stateCounter.paused + that.tasksData.stateCounter.invalid;
                        that.updateVm();
                }, function(err){
                        console.log(err)
                });
        };

        videoDownload.init = function(){
            var that = this;
            setInterval(videoDownload.getTaskList, 3000);
        }

        return videoDownload;
})(Vue, {});


videoDownload.init();
