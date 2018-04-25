<template>
    <transition name="modal">
        <div class="modal-mask">
            <div class="modal-wrapper">
                <div class="modal-container">
                    <div class="modal-header">
                        <slot name="header">
                            default header
                        </slot>
                    </div>

                    <div class="modal-body">
                        <slot name="body">
                            default body
                        </slot>
                    </div>

                    <div class="modal-footer">
                        <slot name="footer">
                            <button class="modal-default-button" @click="$emit('confirm')">
                                ok
                            </button>
                            <button class="modal-default-button" @click="$emit('close')">
                                cancel
                            </button>
                        </slot>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>
<script>
    export default {
        mounted: function (){
            console.log('hello');
        }
    }
</script>
<style lang="less">
    .modal-mask {
        position: fixed;
        z-index: 9998;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, .5);
        display: table;
        transition: opacity .3s ease;
    }

    .modal-wrapper {
        display: table-cell;
        vertical-align: middle;
    }

    .modal-container {
        width: 500px;
        margin: 0px auto;
        padding: 20px;
        background-color: #fff;
        border-radius: 6px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, .4);
        transition: all .3s ease;
        font-family: Helvetica, Arial, sans-serif;
    }

    .modal-header div {
        font-weight: bold;
        font-size: 20px;
        margin-top: 0;
        color: #020202;
    }

    .modal-body div {
        margin: 20px 0;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .modal-body label {
        min-width: 80px;
        max-width: 100px;
    }

    .modal-body input {
        font-size: 15px;
        display: block;
        width: 100%;
        height: 12px;
        padding: 5px;
    }

    .modal-body hr {
        border: 0;
        height: 1px;
        margin-left:auto;
        margin-right:auto;
        width: 40%;
    }

    .modal-body .left-hr {
        float: left;
        background-image: linear-gradient(left, #f0f0f0, #000000, #000000);
    }

    .modal-body .right-hr {
        float: right;
        background-image: linear-gradient(left, #000000, #000000, #f0f0f0);
    }

    .modal-body .caption {
        width: 80px;
        font-weight: bold;
    }

    .modal-footer {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .modal-default-button {
        float: right;
        width: 100px;
        height: 30px;
        font-size: 15px;
        margin: 0 10px;
    }

    /*
     * The following styles are auto-applied to elements with
     * transition="modal" when their visibility is toggled
     * by Vue.js.
     *
     * You can easily play with the modal transition by editing
     * these styles.
     */

    .modal-enter {
        opacity: 0;
    }

    .modal-leave-active {
        opacity: 0;
    }

    .modal-enter .modal-container,
    .modal-leave-active .modal-container {
        -webkit-transform: scale(1.1);
        transform: scale(1.1);
    }
</style>
