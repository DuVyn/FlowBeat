"""
FlowBeat 后端应用主包

本包是 FlowBeat 音乐推荐系统后端的主模块，采用分层架构设计:

包结构:
- api/         API 层，处理 HTTP 请求/响应和路由
- core/        核心模块，包含配置、安全和异常定义
- models/      数据模型层，SQLAlchemy ORM 实体
- repositories/ 仓储层，封装数据访问逻辑
- schemas/     数据传输对象层，Pydantic 模型
- services/    业务服务层，封装业务逻辑
- workers/     后台任务模块，Celery 异步任务

架构原则:
1. 分层解耦: 每层只依赖下层，禁止跨层调用
2. 依赖注入: 使用 FastAPI 的依赖注入管理资源
3. 领域驱动: 以业务领域为中心组织代码
"""
