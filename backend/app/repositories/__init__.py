"""
仓储层模块

本包实现数据访问层 (Repository Pattern):
- base.py              通用 CRUD 仓储基类
- user_repository.py   用户仓储
- music_repository.py  音乐仓储 (预留)
- interaction_repository.py 交互仓储 (预留)

设计原则:
1. 抽象数据访问: 上层无需关心具体的数据库操作
2. 统一接口: 所有仓储继承相同的基类
3. 可测试性: 便于在测试中 mock 数据访问
"""
