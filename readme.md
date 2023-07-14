# fastapi 开发框架
在django框架下开发了较长时间，习惯了drf，因此在开发fastapi时，也直接想要基于同样的思维进行开发，参考了<a href="https://github.com/dmontagu/fastapi-utils">fastapi_utils</a>，其中大量参考了cbv部分的源码，并利用metaclass进行改造，从而实现了可继承，可声明Depends类属性的CBV，基本满足了日常开发需求。
## 特性
- 基于app的代码组织，可方便的进行移植和业务逻辑的拆分
- 基于类的视图ViewSet
  - 视图装饰器register 可直接将类中实现的endpoint注册到router中
  - endpoint装饰器action，用于声明一个函数为一个endpoint
  - 并注入AsyncSession 到db属性
  - 翻页插件，pagination_class,可扩展
- 集成SQLalchemy + asyncpg
- 异步查询的高效可扩展权限系统，源码参考了ory keto(Zanzibar的一个go的实现)，
- 
## 缺点
- 目前CTE仅支持了postgresql后端

## TODO
基于keto实现内置的权限管理系统基类，方便实现权限管理
集成fastapi-filter
后续把核心的功能单独抽出去，成为一个单独的包，方便管理


## 思路
账户体系
### 公网
支持账号密码，微信小程序等登录方式，但最后均需要绑定到手机号账户中来，确保账户体系统一

### 内网
支持账号密码，管理员账号可修改其他账号密码，进行重置