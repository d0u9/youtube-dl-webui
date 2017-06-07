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
                modalData: { url: '' },
                currentSelected: false
        };
        videoDownload.updateVm = function(res) {
                var that = this;
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
                                        val.all = val.downloading + val.finished + val.paused;
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
                                },
                                selected: function(index){
                                       this.currentSelected = index;
                                       console.log(this.currentSelected === index ? 'selected' : '');
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
                        that.tasksData.stateCounter.all = that.tasksData.stateCounter.downloading + that.tasksData.stateCounter.finished + that.tasksData.stateCounter.paused;
                        that.updateVm(res);
                }, function(err){
                        console.log(err)
                });
        };

        return videoDownload;
})(Vue, {});


videoDownload.init();
