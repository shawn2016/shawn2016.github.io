---
layout: page
title: About
description: 打码改变世界
keywords: Zhuang Ma, 马壮
comments: true
menu: 关于
permalink: /about/
---

## 个人简历
- 姓名：戴志祥
- 昵称：shawn
- 职业：全干工程师
- 爱好：听音乐 撸代码
- 个人定位：全栈工程师（Full Stack Developer）
- 职业技能：JavaScript、Node.js、React、Vue、bootstrap、angularJs、Es6等


## 联系方式
- 邮箱：787990963@qq.com
- Github: [https://github.com/shawn2016](https://github.com/shawn2016 "https://github.com/shawn2016")
- 掘金：[https://juejin.im/user/58acd7348fd9c50067feb4f1](https://juejin.im/user/58acd7348fd9c50067feb4f1 "https://juejin.im/user/58acd7348fd9c50067feb4f1")
- 博客园：[https://home.cnblogs.com/u/dzx-shawn/](https://home.cnblogs.com/u/dzx-shawn/ "https://home.cnblogs.com/u/dzx-shawn/")
- 个人网站：[http://nodedai.com/](http://nodedai.com/ "http://nodedai.com/")
## 技能关键字

{% for category in site.data.skills %}
### {{ category.name }}
<div class="btn-inline">
{% for keyword in category.keywords %}
<button class="btn btn-outline" type="button">{{ keyword }}</button>
{% endfor %}
</div>
{% endfor %}
