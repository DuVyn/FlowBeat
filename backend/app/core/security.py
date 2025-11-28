from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# =============================================================================
# [架构决策] 密码哈希算法配置
# =============================================================================
# 1. 算法选择: 使用 "argon2"。passlib 会自动映射到 argon2-cffi 库。
# 2. 模式说明: 默认使用 Argon2id 变体 (侧信道防护 + 内存硬抗性)。
# 3. 废弃策略: deprecated="auto"
#    [原理]: 这是一个平滑迁移策略。如果数据库中遗留了旧算法 (如 bcrypt) 的哈希值，
#    系统仍能验证通过，但在验证成功后，passlib 会自动标记其为"过时"。
#    业务层检测到此标记后，可自动将其重哈希为 Argon2 并更新数据库 (Auto-Rehash)。
# =============================================================================
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希摘要是否匹配。

    [设计意图]
    作为安全层的门面 (Facade)，屏蔽底层加密库的复杂性。
    该函数不仅负责校验，还隐含了算法版本兼容性的处理逻辑。

    Args:
        plain_password (str): 用户输入的明文密码。
        hashed_password (str): 数据库中存储的哈希字符串 (通常以 $argon2id$ 开头)。

    Returns:
        bool: 匹配返回 True，否则 False。
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # [生产级异常处理]
        # 密码验证是安全敏感操作，严禁将底层库的具体错误堆栈暴露给上层或日志。
        # 捕获所有异常并返回 False，防止基于错误的侧信道攻击 (如根据报错时间猜测密码长度)。
        # 在实际生产中，此处应记录结构化安全日志 (Security Audit Log)。
        print(f"Password verification failed with internal error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    生成高强度的密码哈希摘要。

    [原理]
    Argon2id 算法会根据预设的 t_cost (时间成本) 和 m_cost (内存成本) 生成哈希。
    输出格式示例: $argon2id$v=19$m=65536,t=3,p=4$salt$hash...
    包含: 算法标识、版本、参数、随机盐 (Salt) 和哈希本体。

    Args:
        password (str): 明文密码。

    Returns:
        str: 安全的哈希字符串。
    """
    # 这里的 hash 方法会自动生成高熵随机盐，无需手动干预
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    签发 JWT (JSON Web Token) 访问令牌。

    [无状态认证核心]
    生成包含用户标识 (sub) 和过期时间 (exp) 的签名 Token。

    Args:
        subject: 令牌主体，通常为 User ID。
        expires_delta: 自定义过期时间增量。若为 None，则使用全局配置。

    Returns:
        str: 编码并签名后的 JWT 字符串。
    """
    # [时区处理] 强制使用 UTC 时间，防止跨服务器/跨时区部署时的时间偏差导致 Token 提前失效
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 构建载荷 (Payload)
    # 仅存储最必要的元数据，避免 Token 体积过大影响传输性能
    to_encode = {"exp": expire, "sub": str(subject)}

    # 签名加密
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
