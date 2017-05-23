var videoDownload = (function (Vue, extendAM){
        var videoDownload = {};
        videoDownload.vm = null;
        videoDownload.tasksData = {
                headPath: 'http://localhost:5000/',
                videoList: [],
                showModal: false,
                tablist: ['status', 'details', 'files', 'peers', 'options'],
                showTab: 'status',
                stateCounter: { all: 0, downloading: 0, finished: 0, paused: 0 },
                modalData: { url: '' }
        };
        videoDownload.updateVm = function(res) {
                var that = this;
                if(that.vm){
                        that.vm.updated();
                        return false;
                }
                that.vm = new Vue({
                        el: '#videoWrapper',
                        data: that.tasksData,
                        components:{
                              'modal': {template: '#modal-template'}
                        },
                        watch:{
                                stateCounter: function(){
                                        stateCounter.all = stateCounter.downloading + stateCounter.finished + stateCounter.paused;
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
                                }
                        }
                });
        };

        videoDownload.init = function() {
                var that = this;
                var url = that.tasksData.headPath + 'task/list';
                Vue.http.get(url).then(function(res){
                        var resData = JSON.parse(res.body);
                        that.tasksData.videoList = resData.detail;
                        that.tasksData.stateCounter = resData.state_counter;
                        that.updateVm(res);
                }, function(err){
                        console.log(err)
                });
        };

        return videoDownload;
})(Vue, {});


videoDownload.init();
