# 懂的都懂🤗

获取页面 URL：
- 运行 getpageurl.py 收集目标网站上的页面 URL。
- data文件夹中已有2017-2014年的指南页面URL及其标题 csv文件。

提取下载链接：
- request.txt文件 用于放置搜索关键词列表
- 运行 getdownloadurl.py 匹配标题并返回带有下载链接的jsonl文件
- 调整脚本以根据需求提取下载链接。

登录与下载：
- 使用 loginanddownload.py，输入用户名、密码以及 getdownloadurl.py 提取的下载链接jsonl文件
- 执行脚本以登录网站并下载文件。
