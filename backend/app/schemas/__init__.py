"""
数据传输对象模块 (DTOs / Schemas)

本包定义 Pydantic 模型，用于:
- user.py   用户相关的请求/响应模型
- token.py  JWT Token 相关模型
- music.py  音乐相关模型 (预留)

设计原则:
1. 职责分离: 不同场景使用不同的 Schema
2. 验证优先: 利用 Pydantic 进行严格的数据验证
3. 文档友好: 每个字段都有描述，用于生成 API 文档
"""
