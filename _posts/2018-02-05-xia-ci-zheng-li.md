---
layout: post
title: git之推送改动
categories: Git
description:  git
keywords:  git
---
## 推送改动

```
git push origin master // 推送改动至master分支中
```

### 本地推送远程仓库

```
git remote add origin 分支全地址
```

### 合并分支

```
git merge <branch>
```

### 检出仓库

```
git clone 项目地址
```

### 拉取最新代码

```
git pull
```

## 版本回退

### 单个文件撤回

```
git reset --hard 2f81c9c // 切到某个版本，2f81c9c是 2f81c9c44cf5b16ba0819ed5a2fb344cc830a293 某一段
```

```
git reset --hard HEAD // 切换到当前版本
git reset --hard HEAD^ // 切换到上一版本
git reset --hard HEAD^^ // 切换到上两个版本
git reset --hard HEAD~3 // 切换到上三个版本
git reset --hard HEAD~100 // 切换到上一百个版本
```

### 撤销未提交

```
git checkout --文件名 //
```

### 撤销已提交

```
git reset --hard 2f81c9c // 切到某个版本，2f81c9c是 2f81c9c44cf5b16ba0819ed5a2fb344cc830a293 某一段
```

### 查看分支

```
git branch
```

### 新建分支

```
git -b 分支名
```

### 切换分支

```
git checkout 分支名
```

### 新建分支+切换分支

```
git checkout -b 分支名
```

### 合并分支

```
git merge origin master
```

————————————————————————华丽分割—————————————————————

## 标签tag

### 查看tag

```
git tag
```

### 新增标签

```
git tag 标签名
```

### 给版本新增tag

```
git tag 标签名 commit 版本id
```

### 查看当前标签有哪些具体改动（单个提交）

```
git show 标签名
```

### 提交tag（不能是任何分支名同名）

```
git push origin 标签名
```

### 提交所有tag

```
git push origin —tags
```

### 删除单个tag

```
git tag -d tagname
```

### 删除远程tag

```
git push origin :refs/tags/tagname  ===   git push origin —delete tag tagname
```



