---
layout: post
title: 前端算法-冒泡排序
categories: 前端算法
description: 前端算法
keywords: 前端算法,排序
---
# 冒泡排序

冒泡排序时数组的数据会**像气泡一样从数组的一段漂浮到另一端**，因此才有了冒泡这个命名。

基本步骤如下：

1.依次两两比较相邻的元素，如果第一个比第二个大，则进行交换。

2.经过第一轮比较之后，最大的数已经出现在数组最后一个位置了。

3.然后再对除了最后一个元素外的所有数都重复一遍上述比较，结束后第二个的数会到达数组倒数第二个位置。

4.再依次对剩下的数进行重复，直到排序完毕。

下面看看代码描述：

```js
function bubbleSort(arr){
    for(var i=0; i<arr.length; i++){
        for(var j=0; j<arr.length-i; j++){
            //当第一个数大于第二个时，交换它们
            if(arr[j]>arr[j+1]){
                var temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
}
 //测试
 var testArr = [72，54，58，30，31，78，2，77，82，72];
 bubbleSort(testArr);
 console.log(testArr); //输出1,22,25,35,56,88
```

![](/assets/import.png)

其中每次的变化：

```
54,72,58,30,31,78,2,77,82,72
54,58,72,30,31,78,2,77,82,72
54,58,30,72,31,78,2,77,82,72
54,58,30,31,72,78,2,77,82,72
54,58,30,31,72,78,2,77,82,72
54,58,30,31,72,2,78,77,82,72
54,58,30,31,72,2,77,78,82,72
54,58,30,31,72,2,77,78,82,72
54,58,30,31,72,2,77,78,72,82
54,58,30,31,72,2,77,78,72,82
54,58,30,31,72,2,77,78,72,82
54,30,58,31,72,2,77,78,72,82
54,30,31,58,72,2,77,78,72,82
54,30,31,58,72,2,77,78,72,82
54,30,31,58,2,72,77,78,72,82
54,30,31,58,2,72,77,78,72,82
54,30,31,58,2,72,77,78,72,82
54,30,31,58,2,72,77,72,78,82
54,30,31,58,2,72,77,72,78,82
30,54,31,58,2,72,77,72,78,82
30,31,54,58,2,72,77,72,78,82
30,31,54,58,2,72,77,72,78,82
30,31,54,2,58,72,77,72,78,82
30,31,54,2,58,72,77,72,78,82
30,31,54,2,58,72,77,72,78,82
30,31,54,2,58,72,72,77,78,82
30,31,54,2,58,72,72,77,78,82
30,31,54,2,58,72,72,77,78,82
30,31,54,2,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,31,2,54,58,72,72,77,78,82
30,2,31,54,58,72,72,77,78,82
30,2,31,54,58,72,72,77,78,82
30,2,31,54,58,72,72,77,78,82
30,2,31,54,58,72,72,77,78,82
30,2,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
2,30,31,54,58,72,72,77,78,82
```


