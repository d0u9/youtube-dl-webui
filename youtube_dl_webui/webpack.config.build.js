let path = require('path');
let webpack = require('webpack');
let htmlWebpackPlugin = require('html-webpack-plugin');
let ExtractTextWebpackPlugin = require('extract-text-webpack-plugin');
let OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin');
let CopyWebpackPlugin = require('copy-webpack-plugin');
let alias = require('./alias.config.js');

let srcPath = './src';
let outputPath = './';

module.exports = {
    devtool: 'eval-source-map',
    entry: {
        index: srcPath + '/index.js',
    },
    output: {
        path: path.resolve(outputPath),
        filename: './static/' + '[name].js?[hash]',
        publicPath: './'
    },
    module: {
        rules: [{
            test: /\.js$/,
            loader: 'babel-loader',
            exclude: /node_modules/
        },
            {
                test: /\.(less|css)$/,
                use: ExtractTextWebpackPlugin.extract({
                    use: ['css-loader', 'postcss-loader', 'less-loader'],
                    fallback: 'style-loader'
                }),
                // exclude: /node_modules/
            },
            {
                test: /\.(jpe|jpg|woff|woff2|eot|ttf|svg)(\?.*$|$)/,
                use: [{
                    loader: 'url-loader?limit=50000',
                    options: {
                        limit: '1024',
                        name: '[name].[ext]',
                        outputPath: '/imgs/'
                    }
                }]
            },
            {
                test: /\.vue/,
                use: [{
                    loader: 'vue-loader',
                    options: {
                        extractCSS: true
                    }
                }]
            },
            {
                test: /\.html$/,
                use: [{
                    loader: 'html-withimg-loader'
                }]
            }
        ]
    },
    plugins: [
        new webpack.DefinePlugin({
            __httpHost__: 9
        }),
        new htmlWebpackPlugin({
            template: srcPath + '/index.html',
            filename: './templates/index.html',
            minify: {
                // removeComments: true,
                // collapseWhitespace: true
            },
            chunks: ['index']
        }),
        new ExtractTextWebpackPlugin('./static/' + '[name].min.css?[hash]'),
        new OptimizeCssAssetsPlugin({
            assetNameRegExp: /\.min\.css/g,
            //cssProcessor: require('cssnano'),
            cssProcessorOptions: {discardComments: {removeAll: true}}
        })
    ],
    resolve: {
        alias: alias
    },
    devServer: {
        // contentBase: './unity/',
        // historyApiFallback: true,
        // hot: true,
        // inline: true,
        // progress: true,
    }
};