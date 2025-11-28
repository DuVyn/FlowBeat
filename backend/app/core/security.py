"""
安全与加密工具模块

本模块提供应用核心的安全功能:
1. 密码哈希与验证 (Password Hashing)
2. JWT Token 生成与管理 (Token Management)

设计原则:
1. 防御深度: 使用业界最强的密码哈希算法 (Argon2id)。
2. 时间安全: 所有时间戳使用 UTC，避免时区问题。
3. 异常隐藏: 安全相关的错误不暴露具体原因，防止信息泄露。

安全等级:
- Argon2id: 2019 年 Password Hashing Competition 冠军算法。
- HS256 JWT: 适用于单体应用的对称签名算法。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# =============================================================================
# 密码哈希配置
# =============================================================================
# 为什么选择 Argon2:
# 1. 算法强度: Argon2id 结合了 Argon2i (防侧信道攻击) 和 Argon2d (防 GPU 暴力破解) 的优点。
# 2. 内存硬度: 需要消耗大量内存，使 GPU/ASIC 暴力破解的成本极高。
# 3. 标准认可: OWASP、NIST 等安全组织推荐的首选算法。
#
# deprecated="auto" 的作用:
# 这是一个平滑迁移策略。如果数据库中遗留了旧算法 (如 bcrypt) 的哈希值，
# 系统仍能验证通过，但在验证成功后，passlib 会自动标记其为"过时"。
# 业务层检测到此标记后，可自动将其重哈希为 Argon2 并更新数据库 (Auto-Rehash)。
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希摘要是否匹配

    为什么封装此函数:
    1. 解耦: 上层业务代码无需关心具体使用哪个加密库。
    2. 安全: 统一处理异常，防止错误信息泄露。
    3. 可测: 便于在单元测试中 mock 此函数。

    安全注意事项:
    - 此函数不应抛出任何异常，所有错误都返回 False。
    - 不应在日志中记录密码相关的任何信息。

    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的哈希字符串 (通常以 $argon2id$ 开头)

    Returns:
        bool: 匹配返回 True，否则返回 False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 安全处理: 捕获所有异常并返回 False
        #
        # 为什么不记录异常详情:
        # 密码验证是安全敏感操作，异常信息可能包含:
        # 1. 哈希算法版本信息 (可被用于针对性攻击)
        # 2. 输入长度信息 (可被用于侧信道攻击)
        #
        # 生产环境中，此处应记录结构化安全日志 (Security Audit Log)，
        # 但日志内容应仅包含"验证失败"事件，不包含具体原因。
        return False


def get_password_hash(password: str) -> str:
    """
    生成高强度的密码哈希摘要

    算法原理:
    Argon2id 会根据预设的参数生成哈希:
    - t_cost (时间成本): 迭代次数，增加暴力破解时间
    - m_cost (内存成本): 需要的内存量，防止 GPU 并行攻击
    - p_cost (并行度): 使用的线程数

    输出格式示例:
    $argon2id$v=19$m=65536,t=3,p=4$salt$hash...

    格式解读:
    - $argon2id$: 算法标识
    - v=19: Argon2 版本
    - m=65536,t=3,p=4: 参数 (内存 64MB，迭代 3 次，4 线程)
    - salt: 随机盐值 (Base64 编码)
    - hash: 哈希结果 (Base64 编码)

    Args:
        password: 明文密码

    Returns:
        str: 安全的哈希字符串，可直接存入数据库
    """
    # passlib 会自动生成高熵随机盐，无需手动干预
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    签发 JWT (JSON Web Token) 访问令牌

    为什么使用 JWT:
    1. 无状态: 服务端无需存储 Session，便于水平扩展。
    2. 自包含: Token 中包含用户标识，减少数据库查询。
    3. 标准化: 跨语言、跨平台通用，便于前后端分离。

    安全设计:
    1. 使用 UTC 时间计算过期时间，避免时区问题。
    2. 载荷中仅存储用户 ID，不存储敏感信息。
    3. 使用 HS256 签名，防止 Token 被篡改。

    Args:
        subject: 令牌主体，通常为 User ID (会被转为字符串)
        expires_delta: 自定义过期时间增量，若为 None 则使用全局配置

    Returns:
        str: 编码并签名后的 JWT 字符串
    """
    # 计算过期时间
    # 为什么强制使用 UTC: 防止跨服务器/跨时区部署时的时间偏差导致 Token 提前失效
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 构建载荷 (Payload)
    # 为什么只存储 sub 和 exp:
    # 1. 减小 Token 体积，降低网络传输开销
    # 2. 遵循最小信息原则，敏感数据 (如角色) 应从数据库实时查询
    to_encode = {
        "exp": expire,
        "sub": str(subject),
    }

    # 签名生成
    # 为什么使用 settings.SECRET_KEY: 确保生产环境使用强随机密钥
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
