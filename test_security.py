#!/usr/bin/env python3
"""测试安全模块功能"""

import sys
import os
from pathlib import Path

# 添加src路径到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from resume_assistant.utils.security import (
    SecurityManager, APIKeyManager, DataValidator, PrivacyProtector,
    get_security_manager, get_api_key_manager, SecurityError
)

def test_encryption():
    """测试加密解密功能"""
    print("=== 测试加密解密功能 ===")
    
    try:
        # 创建安全管理器
        security_manager = SecurityManager()
        
        # 测试数据
        test_data = "这是一个测试数据，包含敏感信息：13812345678"
        print(f"原始数据: {test_data}")
        
        # 加密
        encrypted = security_manager.encrypt_data(test_data, "test_context")
        print(f"加密成功，数据长度: {len(encrypted.data)}")
        print(f"盐值长度: {len(encrypted.salt)}")
        print(f"创建时间: {encrypted.created_at}")
        
        # 解密
        decrypted = security_manager.decrypt_data(encrypted, "test_context")
        print(f"解密结果: {decrypted}")
        
        # 验证
        if decrypted == test_data:
            print("✅ 加密解密测试通过")
            return True
        else:
            print("❌ 加密解密测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 加密测试异常: {e}")
        return False

def test_api_key_management():
    """测试API密钥管理"""
    print("\n=== 测试API密钥管理 ===")
    
    try:
        # 创建API密钥管理器
        security_manager = SecurityManager()
        api_key_manager = APIKeyManager(security_manager)
        
        # 测试存储API密钥
        test_service = "test_service"
        test_key = "sk-test-1234567890abcdef"
        
        print(f"存储API密钥: {test_service}")
        api_key_manager.store_api_key(test_service, test_key)
        
        # 测试获取API密钥
        retrieved_key = api_key_manager.get_api_key(test_service)
        print(f"获取的密钥: {retrieved_key}")
        
        # 验证
        if retrieved_key == test_key:
            print("✅ API密钥存储和获取测试通过")
        else:
            print("❌ API密钥不匹配")
            return False
        
        # 测试列出服务
        services = api_key_manager.list_services()
        print(f"存储的服务: {services}")
        
        # 测试删除密钥
        success = api_key_manager.delete_api_key(test_service)
        if success:
            print("✅ API密钥删除成功")
        else:
            print("❌ API密钥删除失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API密钥管理测试异常: {e}")
        return False

def test_data_validation():
    """测试数据验证"""
    print("\n=== 测试数据验证 ===")
    
    try:
        # 测试URL验证
        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://api.openai.com/v1/chat"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert(1)"
        ]
        
        print("测试有效URL:")
        for url in valid_urls:
            result = DataValidator.validate_url(url)
            print(f"  {url}: {'✅' if result else '❌'}")
        
        print("测试无效URL:")
        for url in invalid_urls:
            result = DataValidator.validate_url(url)
            print(f"  {url}: {'❌' if not result else '✅ (意外通过)'}")
        
        # 测试文件类型验证
        print("\n测试文件类型验证:")
        test_files = [
            ("resume.pdf", True),
            ("document.docx", True),
            ("script.exe", False),
            ("virus.bat", False)
        ]
        
        for filename, expected in test_files:
            result = DataValidator.validate_file_type(filename)
            status = "✅" if result == expected else "❌"
            print(f"  {filename}: {status} (期望: {expected}, 实际: {result})")
        
        # 测试输入清理
        print("\n测试输入清理:")
        dirty_input = "正常文本\x00控制字符\x1f更多内容" + "长" * 100
        cleaned = DataValidator.sanitize_input(dirty_input, 50)
        print(f"  原始长度: {len(dirty_input)}")
        print(f"  清理后长度: {len(cleaned)}")
        print(f"  清理结果: {repr(cleaned)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据验证测试异常: {e}")
        return False

def test_privacy_protection():
    """测试隐私保护"""
    print("\n=== 测试隐私保护 ===")
    
    try:
        # 测试敏感信息遮蔽
        test_text = "我的手机号是13812345678，邮箱是zhang.san@example.com，身份证号是110101199001011234"
        print(f"原始文本: {test_text}")
        
        masked_text = PrivacyProtector.mask_sensitive_data(test_text)
        print(f"遮蔽后: {masked_text}")
        
        # 检查是否成功遮蔽
        if "13812345678" not in masked_text and "zhang.san@example.com" not in masked_text:
            print("✅ 敏感信息遮蔽测试通过")
        else:
            print("❌ 敏感信息遮蔽失败")
            return False
        
        # 测试简历匿名化
        resume_content = """
        姓名：张三
        年龄：25
        性别：男
        手机：13912345678
        邮箱：zhangsan@company.com
        """
        
        print(f"\n原始简历:\n{resume_content}")
        
        anonymized = PrivacyProtector.anonymize_resume_data(resume_content)
        print(f"匿名化后:\n{anonymized}")
        
        # 检查匿名化效果
        if "张三" not in anonymized and "13912345678" not in anonymized:
            print("✅ 简历匿名化测试通过")
        else:
            print("❌ 简历匿名化失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 隐私保护测试异常: {e}")
        return False

def test_global_managers():
    """测试全局管理器"""
    print("\n=== 测试全局管理器 ===")
    
    try:
        # 测试全局安全管理器
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        
        if manager1 is manager2:
            print("✅ 全局安全管理器单例测试通过")
        else:
            print("❌ 全局安全管理器不是单例")
            return False
        
        # 测试全局API密钥管理器
        api_manager1 = get_api_key_manager()
        api_manager2 = get_api_key_manager()
        
        if api_manager1 is api_manager2:
            print("✅ 全局API密钥管理器单例测试通过")
        else:
            print("❌ 全局API密钥管理器不是单例")
            return False
        
        # 测试存储和获取
        test_service = "global_test"
        test_key = "sk-global-test-key"
        
        api_manager1.store_api_key(test_service, test_key)
        retrieved = api_manager2.get_api_key(test_service)
        
        if retrieved == test_key:
            print("✅ 全局管理器数据共享测试通过")
            # 清理
            api_manager1.delete_api_key(test_service)
        else:
            print("❌ 全局管理器数据共享失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 全局管理器测试异常: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🔒 Resume Assistant 安全模块测试")
    print("=" * 50)
    
    tests = [
        ("加密解密", test_encryption),
        ("API密钥管理", test_api_key_management),
        ("数据验证", test_data_validation),
        ("隐私保护", test_privacy_protection),
        ("全局管理器", test_global_managers)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} 测试通过")
            else:
                print(f"\n❌ {test_name} 测试失败")
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有安全功能测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)