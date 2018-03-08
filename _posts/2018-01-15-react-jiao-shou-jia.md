---
layout: post
title: react 脚手架
categories: React
description: create-react-app
keywords: es6,React
---

## react 脚手架

**前言**

create-react-app 是一个全局的命令

行工具用来创建一个新的项目

react-scripts 是一个生成的项目所需要的开发依赖

**全局安装create-react-app脚手架**

```
npm install -g create-react-app
```

**新建一个项目my-app**

```
create-react-app my-app
```

**目录结构**

```
src          
├── App.css
├── App.js
├── App.test.js
├── index.css
├── index.js
├── logo.svg
└── registerServiceWorker.js
README.md 
node_modules
package.json
public
yarn.lock
```

**启动项目**

```
yarn start
```

**打包**

```
yarn build
```

**测试**

```
 yarn test
```

**添加依赖**

```
yarn eject
```

**视频演示**

![](https://camo.githubusercontent.com/ee7c8ab30f88d2e6cd287afa8bf2c69705465759/68747470733a2f2f63646e2e7261776769742e636f6d2f66616365626f6f6b696e63756261746f722f6372656174652d72656163742d6170702f366162363765366239363435373732306438343361613363353537666639353161343162616663322f73637265656e636173742e737667)

由于现在是package.json文件中,没做任何依赖,添加依赖。

此时看到package.json 依赖文件有了。

以上是脚手架简单应用，详细原理见：[http://blog.csdn.net/github\_squad/article/details/57452333](http://blog.csdn.net/github_squad/article/details/57452333)

