new Vue({
  el: '#videoWrapper',
  data: {
    videoList: [
        {name: 'video'},
        {name: 'video'},
        {name: 'video'},
        {name: 'video'},
        {name: 'video'},
        {name: 'video'}
    ],
    showModal: false,
    modalData: {
        'url': ''
    },
    showTab: 'status',
    tablist: [
            'status',
            'details',
            'files',
            'peers',
            'options'
    ],
    stateCounter: {
            all: 0,
            downloading: 0,
            finished: 0,
            paused: 0
    }
  },
  components:{
          'modal': {template: '#modal-template'}
  },
  methods:{
          addTask: function(){
                this.showModal = false;
                console.log('add Task');
          },
          deleteTask: function(taskID){
          }
  }
})

var getTaskList = function(){
        console.log('hello');
}
