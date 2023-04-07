# twitter-summary-chatgpt

### 每天从twitter，总结当天 关注的 以及 热门的资讯

# 使用步骤

1. 安装所有的依赖，python版本 3.9
2. 复制 config.template.json 为 config.json
3. 确保有梯子
4. config.json 填写内容
   1. openai的key
   2. 邮箱的信息：发件人，密码，收件人
   3. 关注的领域
   4. 关注的账号
   5. 给chatgpt的prompt
5. 运行 python3 info_loader.py

### 代码简介

* 用 selenium 从 twitter 网页抓取信息（网页可能改版，导致抓取出错）
* 用 openai 的 token 包计算拆分要请求分析的数据
* 用 openai 的 3.5 的api，让 chatgpt 总结归纳
* 用 html 的形式展示所有的信息，以及 chatgpt 的总结归纳，并发送邮件

注意：总结归纳的好坏，取决于 prompt，要自己适当调整prompt
