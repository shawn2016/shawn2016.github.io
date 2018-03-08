---
layout: post
title: git之学习
categories: Git
description:  git
keywords:  git
---
## 尝试

首先，你可以试着输入git，看看系统有没有安装Git：

```
$ git
The program 'git' is currently not installed. You can install it by typing:
sudo apt-get install git
```

### 安装

```
$ sudo apt-get install git
```

### 创建版本库

创建一个版本库非常简单，首先，选择一个合适的地方，创建一个空目录：

```
mkdir learngit
$ cd learngit
$ pwd
/Users/michael/learngit
```

通过`git init`命令把这个目录变成Git可以管理的仓库：

```
$ git init
Initialized empty Git repository in /Users/michael/learngit/.git/
```

### 查看文件中所有文件\(含隐藏文件\)

可以看到隐藏文件.git文件夹

```
ls -ah
```

### 新建一个文件

```
touch readme.txt
```

### 查看状态

`git status`命令可以让我们时刻掌握仓库当前的状态，上面的命令告诉我们，readme.txt被修改过了，但还没有准备提交的修改。

```
git status
```

虽然Git告诉我们readme.txt被修改了，但如果能看看具体修改了什么内容，自然是很好的。比如你休假两周从国外回来，第一天上班时，已经记不清上次怎么修改的readme.txt，所以，需要用`git diff`这个命令看看：

### git diff

```
$ git diff readme.txt 
diff --git a/readme.txt b/readme.txt
index 46d49bf..9247db6 100644
--- a/readme.txt
+++ b/readme.txt
@@ -1,2 +1,2 @@
-Git is a version control system.
+Git is a distributed version control system.
 Git is free software.
```

### 添加至暂存区

提交修改和提交新文件是一样的两步，第一步是`git add`

```
git add 文件名 // 添加单个文件
git add . // 添加所有文件
```

同样没有任何输出。在执行第二步`git commit`之前，我们再运行`git status`看看当前仓库的状态：

```
$ git status
# On branch master
# Changes to be committed:
#   (use "git reset HEAD <file>..." to unstage)
#
#       modified:   readme.txt
#
```

`git status`告诉我们，将要被提交的修改包括readme.txt，下一步，就可以放心地提交了：

```
$ git commit -m "add distributed"
[master ea34578] add distributed
 1 file changed, 1 insertion(+), 1 deletion(-)
```

提交后，我们再用`git status`命令看看仓库的当前状态：

```
$ git status
# On branch master
nothing to commit (working directory clean)
```

Git告诉我们当前没有需要提交的修改，而且，工作目录是干净（working directory clean）的。

