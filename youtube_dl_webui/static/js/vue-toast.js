(function (global, factory) {
	typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
	typeof define === 'function' && define.amd ? define(factory) :
	(global.vueToasts = factory());
}(this, (function () { 'use strict';

var defaultOptions$1 = {
  theme: 'default', // info warning error success
  timeLife: 5000,
  closeBtn: false,
};

var VueToast = {
render: function(){var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('transition',{attrs:{"name":"vue-toast-opacity"}},[_c('div',{staticClass:"vue-toast_container",class:[_vm.theme],style:(_vm.style),on:{"mouseover":_vm._stopTimer,"mouseleave":_vm._startTimer}},[_c('div',{staticClass:"vue-toast_message"},[_c('span',{domProps:{"innerHTML":_vm._s(_vm.message)}}),_vm._v(" "),(_vm.options.closeBtn)?_c('span',{staticClass:"vue-toast_close-btn",on:{"click":_vm.remove}}):_vm._e()])])])},
staticRenderFns: [],
  props: {
    message: {
      required: true
    },
    position: {
      type: Number,
      required: true
    },
    onDestroy: {
      required: true,
      type: Function
    },
    options: {
      type: Object
    }
  },
  data: function data() {
    return {
      isShow: false
    }
  },
  computed: {
    theme: function theme() {
      return '_' + this.options.theme
    },
    style: function style() {
      return ("transform: translateY(" + (this.options.directionOfJumping) + (this.position * 100) + "%)")
    },
    fullOptions: function fullOptions() {
      return Object.assign({}, defaultOptions$1, this.options)
    }
  },
  mounted: function mounted() {
    var this$1 = this;

    setTimeout(function () {
      this$1.isShow = true;
    }, 50);

    if (!this.fullOptions.closeBtn) {
      this._startLazyAutoDestroy();
    }
  },
  methods: {
    // Public
    remove: function remove() {
      this._clearTimer();
      this.onDestroy();
    },
    // Private
    _startLazyAutoDestroy: function _startLazyAutoDestroy() {
      var this$1 = this;

      this._clearTimer();
      this.timerDestroy = setTimeout(function () {
        this$1.remove();
      }, this.fullOptions.timeLife);
    },
    _clearTimer: function _clearTimer() {
      if (this.timerDestroy) {
        clearTimeout(this.timerDestroy);
      }
    },
    _startTimer: function _startTimer() {
      if (!this.fullOptions.closeBtn) {
        this._startLazyAutoDestroy();
      }
    },
    _stopTimer: function _stopTimer() {
      if (!this.options.closeBtn) {
        this._clearTimer();
      }
    }
  }
};

var defaultOptions = {
  maxToasts: 6,
  position: 'left bottom'
};

var manager$1 = {
render: function(){var _vm=this;var _h=_vm.$createElement;var _c=_vm._self._c||_h;return _c('transition-group',{staticClass:"vue-toast-manager_container",class:_vm.classesOfPosition,attrs:{"tag":"div","name":"vue-toast"}},_vm._l((_vm.toasts),function(toast,index){return _c('vue-toast',{key:toast.uid,attrs:{"message":toast.message,"options":toast.options,"onDestroy":toast.onDestroy,"position":index}})}))},
staticRenderFns: [],
  data: function data() {
    return {
      uid: 1,
      toasts: [],
      options: defaultOptions
    }
  },
  computed: {
    classesOfPosition: function classesOfPosition() {
      return this._updateClassesOfPosition(this.options.position)
    },
    directionOfJumping: function directionOfJumping() {
      return this._updateDirectionOfJumping(this.options.position)
    }
  },
  methods: {
    // Public
    showToast: function showToast(message, options) {
      this._addToast(message, options);
      this._moveToast();

      return this
    },
    setOptions: function setOptions(options) {
      this.options = Object.assign(this.options, options || {});

      return this
    },
    closeAll: function closeAll() {
      this.toasts = [];
    },
    // Private
    _addToast: function _addToast(message, options) {
      if ( options === void 0 ) options = {};

      if (!message) {
        return
      }

      options.directionOfJumping = this.directionOfJumping;

      var that = this;
      var uid = this.uid++;
      var toast = {
        uid: uid,
        message: message,
        options: options,
        onDestroy: function onDestroy() {
          var i = that.toasts.findIndex(function (item) { return item.uid === uid; });
          that.toasts.splice(i, 1);
        }
      };

      this.toasts.unshift(toast);
    },
    _moveToast: function _moveToast(toast) {
      var maxToasts = this.options.maxToasts > 0
        ? this.options.maxToasts
        : 9999;

      this.toasts = this.toasts.reduceRight(function (prev, toast, i) {
        if (i + 1 >= maxToasts) {
          return prev
        }

        return [toast].concat(prev)
      }, []);
    },
    _updateClassesOfPosition: function _updateClassesOfPosition(position) {
      return position.split(' ').reduce(function (prev, val) {
        prev[("__" + (val.toLowerCase()))] = true;

        return prev
      }, {})
    },
    _updateDirectionOfJumping: function _updateDirectionOfJumping(position) {
      return position.match(/top/i) ? '+' : '-'
    }
  },
  components: { VueToast: VueToast }
};

return manager$1;

})));
//# sourceMappingURL=vue-toast.js.map
