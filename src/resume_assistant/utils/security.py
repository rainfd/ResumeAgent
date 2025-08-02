"""安全工具模块

提供加密存储、数据验证和隐私保护功能。
"""

import os
import base64
import hashlib
import secrets
import json
import re
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import logging

from . import get_logger

logger = get_logger(__name__)

@dataclass
class EncryptedData:
    """加密数据容器"""
    data: str  # Base64编码的加密数据
    salt: str  # Base64编码的盐值
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class SecurityManager:
    """安全管理器"""
    
    def __init__(self, master_key: Optional[str] = None):
        """初始化安全管理器
        
        Args:
            master_key: 主密钥，如果为None则自动生成
        """
        self.master_key = master_key or self._generate_master_key()
        self._encryption_key_cache: Dict[str, Fernet] = {}
        self._key_derivation_iterations = 100000  # PBKDF2迭代次数
        
    def _generate_master_key(self) -> str:
        """生成主密钥"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """使用PBKDF2派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self._key_derivation_iterations,
        )
        return kdf.derive(password.encode())
    
    def _get_encryption_key(self, context: str = "default") -> Fernet:
        """获取加密密钥"""
        if context not in self._encryption_key_cache:
            # 为特定上下文生成盐值
            salt = hashlib.sha256(f"{self.master_key}:{context}".encode()).digest()[:16]
            derived_key = self._derive_key(self.master_key, salt)
            fernet_key = base64.urlsafe_b64encode(derived_key)
            self._encryption_key_cache[context] = Fernet(fernet_key)
        
        return self._encryption_key_cache[context]
    
    def encrypt_data(
        self, 
        data: str, 
        context: str = "default",
        expires_hours: Optional[int] = None
    ) -> EncryptedData:
        """加密数据
        
        Args:
            data: 要加密的数据
            context: 加密上下文
            expires_hours: 过期时间（小时）
            
        Returns:
            加密数据对象
        """
        try:
            # 生成随机盐值
            salt = secrets.token_bytes(16)
            
            # 派生密钥
            derived_key = self._derive_key(f"{self.master_key}:{context}", salt)
            fernet_key = base64.urlsafe_b64encode(derived_key)
            fernet = Fernet(fernet_key)
            
            # 加密数据
            encrypted = fernet.encrypt(data.encode())
            
            # 计算过期时间
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            return EncryptedData(
                data=base64.b64encode(encrypted).decode(),
                salt=base64.b64encode(salt).decode(),
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata={"context": context}
            )
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise SecurityError(f"Encryption failed: {e}")
    
    def decrypt_data(self, encrypted_data: EncryptedData, context: str = "default") -> str:
        """解密数据
        
        Args:
            encrypted_data: 加密数据对象
            context: 加密上下文
            
        Returns:
            解密后的数据
        """
        try:
            # 检查是否过期
            if encrypted_data.expires_at and datetime.now() > encrypted_data.expires_at:
                raise SecurityError("Encrypted data has expired")
            
            # 解码盐值和数据
            salt = base64.b64decode(encrypted_data.salt)
            encrypted = base64.b64decode(encrypted_data.data)
            
            # 派生密钥
            derived_key = self._derive_key(f"{self.master_key}:{context}", salt)
            fernet_key = base64.urlsafe_b64encode(derived_key)
            fernet = Fernet(fernet_key)
            
            # 解密数据
            decrypted = fernet.decrypt(encrypted)
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise SecurityError(f"Decryption failed: {e}")
    
    def encrypt_file(self, file_path: Path, output_path: Optional[Path] = None) -> Path:
        """加密文件
        
        Args:
            file_path: 源文件路径
            output_path: 输出文件路径，如果为None则在源文件名后加.enc
            
        Returns:
            加密文件路径
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            output_path = output_path or file_path.with_suffix(file_path.suffix + '.enc')
            
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 加密文件内容
            fernet = self._get_encryption_key("file")
            encrypted_data = fernet.encrypt(file_data)
            
            # 写入加密文件
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to encrypt file: {e}")
            raise SecurityError(f"File encryption failed: {e}")
    
    def decrypt_file(self, encrypted_file_path: Path, output_path: Optional[Path] = None) -> Path:
        """解密文件
        
        Args:
            encrypted_file_path: 加密文件路径
            output_path: 输出文件路径
            
        Returns:
            解密文件路径
        """
        try:
            if not encrypted_file_path.exists():
                raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")
            
            if output_path is None:
                # 移除.enc后缀
                if encrypted_file_path.suffix == '.enc':
                    output_path = encrypted_file_path.with_suffix('')
                else:
                    output_path = encrypted_file_path.with_suffix('.dec')
            
            # 读取加密文件
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 解密文件内容
            fernet = self._get_encryption_key("file")
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # 写入解密文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            logger.info(f"File decrypted: {encrypted_file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to decrypt file: {e}")
            raise SecurityError(f"File decryption failed: {e}")

class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self, security_manager: SecurityManager, storage_path: Optional[Path] = None):
        """初始化API密钥管理器
        
        Args:
            security_manager: 安全管理器
            storage_path: 存储路径
        """
        self.security_manager = security_manager
        self.storage_path = storage_path or Path.home() / ".resume_assistant" / "keys.enc"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._keys_cache: Dict[str, str] = {}
    
    def store_api_key(self, service_name: str, api_key: str, expires_hours: Optional[int] = None):
        """存储API密钥
        
        Args:
            service_name: 服务名称
            api_key: API密钥
            expires_hours: 过期时间（小时）
        """
        try:
            # 加载现有密钥
            keys_data = self._load_keys()
            
            # 加密新密钥
            encrypted_key = self.security_manager.encrypt_data(
                api_key, 
                context=f"api:{service_name}",
                expires_hours=expires_hours
            )
            
            # 存储加密密钥
            keys_data[service_name] = {
                "data": encrypted_key.data,
                "salt": encrypted_key.salt,
                "created_at": encrypted_key.created_at.isoformat(),
                "expires_at": encrypted_key.expires_at.isoformat() if encrypted_key.expires_at else None,
                "metadata": encrypted_key.metadata
            }
            
            # 保存到文件
            self._save_keys(keys_data)
            
            # 更新缓存
            self._keys_cache[service_name] = api_key
            
            logger.info(f"API key stored for service: {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            raise SecurityError(f"API key storage failed: {e}")
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """获取API密钥
        
        Args:
            service_name: 服务名称
            
        Returns:
            API密钥，如果不存在则返回None
        """
        try:
            # 检查缓存
            if service_name in self._keys_cache:
                return self._keys_cache[service_name]
            
            # 加载密钥数据
            keys_data = self._load_keys()
            
            if service_name not in keys_data:
                return None
            
            key_info = keys_data[service_name]
            
            # 重建加密数据对象
            encrypted_data = EncryptedData(
                data=key_info["data"],
                salt=key_info["salt"],
                created_at=datetime.fromisoformat(key_info["created_at"]),
                expires_at=datetime.fromisoformat(key_info["expires_at"]) if key_info["expires_at"] else None,
                metadata=key_info.get("metadata", {})
            )
            
            # 解密密钥
            api_key = self.security_manager.decrypt_data(
                encrypted_data, 
                context=f"api:{service_name}"
            )
            
            # 更新缓存
            self._keys_cache[service_name] = api_key
            
            return api_key
            
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None
    
    def delete_api_key(self, service_name: str) -> bool:
        """删除API密钥
        
        Args:
            service_name: 服务名称
            
        Returns:
            是否成功删除
        """
        try:
            # 加载现有密钥
            keys_data = self._load_keys()
            
            if service_name in keys_data:
                del keys_data[service_name]
                self._save_keys(keys_data)
                
                # 清除缓存
                if service_name in self._keys_cache:
                    del self._keys_cache[service_name]
                
                logger.info(f"API key deleted for service: {service_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False
    
    def list_services(self) -> List[str]:
        """列出所有存储的服务
        
        Returns:
            服务名称列表
        """
        try:
            keys_data = self._load_keys()
            return list(keys_data.keys())
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    def rotate_api_key(self, service_name: str, new_api_key: str) -> bool:
        """轮换API密钥
        
        Args:
            service_name: 服务名称
            new_api_key: 新的API密钥
            
        Returns:
            是否成功轮换
        """
        try:
            # 检查旧密钥是否存在
            old_key = self.get_api_key(service_name)
            if not old_key:
                return False
            
            # 存储新密钥
            self.store_api_key(service_name, new_api_key)
            
            logger.info(f"API key rotated for service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate API key: {e}")
            return False
    
    def _load_keys(self) -> Dict[str, Any]:
        """加载密钥数据"""
        try:
            if not self.storage_path.exists():
                return {}
            
            with open(self.storage_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Failed to load keys data: {e}")
            return {}
    
    def _save_keys(self, keys_data: Dict[str, Any]):
        """保存密钥数据"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(keys_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save keys data: {e}")
            raise SecurityError(f"Keys data save failed: {e}")

class DataValidator:
    """数据验证器"""
    
    # URL验证正则表达式
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    # 邮箱验证正则表达式
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # 危险文件扩展名
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', 
        '.jar', '.sh', '.ps1', '.php', '.asp', '.jsp'
    }
    
    # 允许的简历文件类型
    ALLOWED_RESUME_TYPES = {'.pdf', '.txt', '.md', '.docx', '.doc'}
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """验证URL格式
        
        Args:
            url: 要验证的URL
            
        Returns:
            是否为有效URL
        """
        if not url or not isinstance(url, str):
            return False
        
        return bool(cls.URL_PATTERN.match(url.strip()))
    
    @classmethod
    def validate_email(cls, email: str) -> bool:
        """验证邮箱格式
        
        Args:
            email: 要验证的邮箱
            
        Returns:
            是否为有效邮箱
        """
        if not email or not isinstance(email, str):
            return False
        
        return bool(cls.EMAIL_PATTERN.match(email.strip()))
    
    @classmethod
    def validate_file_type(cls, filename: str, allowed_types: Optional[set] = None) -> bool:
        """验证文件类型
        
        Args:
            filename: 文件名
            allowed_types: 允许的文件类型集合
            
        Returns:
            是否为允许的文件类型
        """
        if not filename or not isinstance(filename, str):
            return False
        
        file_ext = Path(filename).suffix.lower()
        
        # 检查是否为危险文件类型
        if file_ext in cls.DANGEROUS_EXTENSIONS:
            return False
        
        # 检查是否在允许列表中
        allowed = allowed_types or cls.ALLOWED_RESUME_TYPES
        return file_ext in allowed
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size_mb: int = 50) -> bool:
        """验证文件大小
        
        Args:
            file_size: 文件大小（字节）
            max_size_mb: 最大文件大小（MB）
            
        Returns:
            是否在允许的大小范围内
        """
        if file_size < 0:
            return False
        
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    @classmethod
    def sanitize_input(cls, text: str, max_length: int = 1000) -> str:
        """清理输入文本
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            清理后的文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        # 移除控制字符
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # 限制长度
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # 移除首尾空白
        return sanitized.strip()
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> bool:
        """验证API密钥格式
        
        Args:
            api_key: API密钥
            
        Returns:
            是否为有效的API密钥格式
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        # 基本长度检查
        if len(api_key) < 10 or len(api_key) > 200:
            return False
        
        # 检查是否只包含合法字符
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
        if not set(api_key).issubset(allowed_chars):
            return False
        
        return True

class PrivacyProtector:
    """隐私保护器"""
    
    # 敏感信息模式
    SENSITIVE_PATTERNS = {
        'phone': re.compile(r'(?:\+?86)?1[3-9]\d{9}'),  # 中国手机号
        'id_card': re.compile(r'\d{17}[\dxX]'),  # 身份证号
        'email': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'),
        'credit_card': re.compile(r'\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}'),
        'api_key': re.compile(r'[A-Za-z0-9]{20,}'),  # 长字符串可能是API密钥
    }
    
    @classmethod
    def mask_sensitive_data(cls, text: str, mask_char: str = '*') -> str:
        """遮蔽敏感数据
        
        Args:
            text: 原始文本
            mask_char: 遮蔽字符
            
        Returns:
            遮蔽后的文本
        """
        if not text:
            return text
        
        masked_text = text
        
        for pattern_name, pattern in cls.SENSITIVE_PATTERNS.items():
            def mask_match(match):
                matched = match.group()
                if pattern_name == 'phone':
                    return matched[:3] + mask_char * 4 + matched[-4:]
                elif pattern_name == 'id_card':
                    return matched[:4] + mask_char * 10 + matched[-4:]
                elif pattern_name == 'email':
                    parts = matched.split('@')
                    if len(parts) == 2:
                        username = parts[0]
                        domain = parts[1]
                        if len(username) > 2:
                            masked_username = username[:2] + mask_char * (len(username) - 2)
                        else:
                            masked_username = mask_char * len(username)
                        return f"{masked_username}@{domain}"
                elif pattern_name == 'credit_card':
                    return mask_char * 4 + matched[-4:]
                elif pattern_name == 'api_key':
                    if len(matched) > 8:
                        return matched[:4] + mask_char * (len(matched) - 8) + matched[-4:]
                
                return mask_char * len(matched)
            
            masked_text = pattern.sub(mask_match, masked_text)
        
        return masked_text
    
    @classmethod
    def remove_sensitive_data(cls, text: str) -> str:
        """移除敏感数据
        
        Args:
            text: 原始文本
            
        Returns:
            移除敏感数据后的文本
        """
        if not text:
            return text
        
        cleaned_text = text
        
        for pattern in cls.SENSITIVE_PATTERNS.values():
            cleaned_text = pattern.sub('[REDACTED]', cleaned_text)
        
        return cleaned_text
    
    @classmethod
    def anonymize_resume_data(cls, resume_content: str) -> str:
        """匿名化简历数据
        
        Args:
            resume_content: 简历内容
            
        Returns:
            匿名化后的简历内容
        """
        if not resume_content:
            return resume_content
        
        # 遮蔽敏感信息
        anonymized = cls.mask_sensitive_data(resume_content)
        
        # 替换常见的个人信息标识
        anonymized = re.sub(r'姓名[:：]\s*\S+', '姓名：[匿名]', anonymized)
        anonymized = re.sub(r'年龄[:：]\s*\d+', '年龄：[隐藏]', anonymized)
        anonymized = re.sub(r'性别[:：]\s*[男女]', '性别：[隐藏]', anonymized)
        
        return anonymized

class SecurityError(Exception):
    """安全相关异常"""
    pass

# 全局安全管理器实例
_security_manager: Optional[SecurityManager] = None
_api_key_manager: Optional[APIKeyManager] = None

def get_security_manager() -> SecurityManager:
    """获取全局安全管理器"""
    global _security_manager
    if _security_manager is None:
        # 从环境变量或配置文件获取主密钥
        master_key = os.getenv('RESUME_ASSISTANT_MASTER_KEY')
        _security_manager = SecurityManager(master_key)
    return _security_manager

def get_api_key_manager() -> APIKeyManager:
    """获取全局API密钥管理器"""
    global _api_key_manager
    if _api_key_manager is None:
        security_manager = get_security_manager()
        _api_key_manager = APIKeyManager(security_manager)
    return _api_key_manager

# 便捷函数
def encrypt_text(text: str, context: str = "default") -> EncryptedData:
    """加密文本"""
    return get_security_manager().encrypt_data(text, context)

def decrypt_text(encrypted_data: EncryptedData, context: str = "default") -> str:
    """解密文本"""
    return get_security_manager().decrypt_data(encrypted_data, context)

def store_api_key(service: str, key: str):
    """存储API密钥"""
    get_api_key_manager().store_api_key(service, key)

def get_api_key(service: str) -> Optional[str]:
    """获取API密钥"""
    return get_api_key_manager().get_api_key(service)

def validate_url(url: str) -> bool:
    """验证URL"""
    return DataValidator.validate_url(url)

def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """验证文件
    
    Returns:
        (是否有效, 错误信息)
    """
    if not DataValidator.validate_file_type(filename):
        return False, "不支持的文件类型"
    
    if not DataValidator.validate_file_size(file_size):
        return False, "文件大小超出限制"
    
    return True, ""

def mask_sensitive_info(text: str) -> str:
    """遮蔽敏感信息"""
    return PrivacyProtector.mask_sensitive_data(text)