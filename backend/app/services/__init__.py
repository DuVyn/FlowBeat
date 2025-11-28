"""
业务服务层模块

本包实现业务逻辑层 (Service Layer):
- auth_service.py          认证服务
- music_service.py         音乐服务 (预留)
- recommendation_service.py 推荐服务 (预留)
- minio_client.py          对象存储客户端 (预留)

设计原则:
1. 领域逻辑: 封装复杂的业务规则
2. 事务边界: 服务方法通常是事务边界
3. 无状态: 服务实例可以安全地共享
"""
