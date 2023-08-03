# fastapi 开发框架
在django框架下开发了较长时间，习惯了drf，因此在开发fastapi时，也直接想要基于同样的思维进行开发，参考了<a href="https://github.com/dmontagu/fastapi-utils">fastapi_utils</a>，其中大量参考了cbv部分的源码，并利用metaclass进行改造，从而实现了可继承，可声明Depends类属性的CBV，基本满足了日常开发需求。
## 特性
- 基于app的代码组织，可方便的进行移植和业务逻辑的拆分
- 基于类的视图ViewSet
  - 视图装饰器register 可直接将类中实现的endpoint注册到router中
  - endpoint装饰器action，用于声明一个函数为一个endpoint
  - 并注入AsyncSession 到db属性
  - 默认集成了翻页功能
  - 在user部分实现了用户登录功能，后续在此基础上可扩展添加权限相关功能
- 集成SQLalchemy + asyncpg
- 异步查询的高效可扩展权限系统，源码参考了ory keto(Zanzibar的一个go的实现)，
- 
## 缺点
- 目前CTE仅支持了postgresql后端

## TODO
基于keto实现内置的权限管理系统基类，方便实现权限管理
集成fastapi-filter
抽出配置函数，实现单例，从而实现配置的注入


## 思路
账户体系
### 公网
支持账号密码，微信小程序等登录方式，但最后均需要绑定到手机号账户中来，确保账户体系统一

### 内网
支持账号密码，管理员账号可修改其他账号密码，进行重置
更新日志
# 2023年7月31日
核心重构，通过元类参数，增加忽略子类参数功能，并且mixin重构，去掉重要属性的下划线
增加sqlalchemy_to_pydantic方法（https://github.com/tiangolo/pydantic-sqlalchemy）
增加筛选中间件,参考了他人工作（https://github.com/arthurio/fastapi-filter），并剥离了排序搜索功能，后面做成单独的中间件
# 2023年8月3日
筛选功能增强，sqlalchemy to pydantic功能增强，创建增加混入参数的方法，增加reference