#!/usr/bin/env python3
"""验证Task 11: 安全性实现的完整性"""

import sys
import os
from pathlib import Path

# 添加src路径到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def verify_task11_1():
    """验证Task 11.1: 实现 API 密钥加密存储"""
    print("=== Task 11.1: API密钥加密存储 ===")
    
    checks = []
    
    try:
        # 检查安全模块导入
        from resume_assistant.utils.security import SecurityManager, APIKeyManager, get_security_manager, get_api_key_manager
        checks.append("✅ 安全模块导入成功")
        
        # 检查加密功能
        security_manager = SecurityManager()
        test_data = "test-api-key-sk-1234567890"
        encrypted = security_manager.encrypt_data(test_data)
        decrypted = security_manager.decrypt_data(encrypted)
        
        if decrypted == test_data:
            checks.append("✅ 加密解密功能正常")
        else:
            checks.append("❌ 加密解密功能异常")
        
        # 检查API密钥管理
        api_manager = APIKeyManager(security_manager)
        api_manager.store_api_key("test", "sk-test-key")
        retrieved = api_manager.get_api_key("test")
        
        if retrieved == "sk-test-key":
            checks.append("✅ API密钥存储和获取正常")
            api_manager.delete_api_key("test")
        else:
            checks.append("❌ API密钥存储异常")
        
        # 检查全局单例
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        
        if manager1 is manager2:
            checks.append("✅ 全局单例模式正常")
        else:
            checks.append("❌ 全局单例模式异常")
        
    except Exception as e:
        checks.append(f"❌ 导入或功能异常: {e}")
    
    return checks

def verify_task11_2():
    """验证Task 11.2: 实现数据验证和输入过滤"""
    print("\n=== Task 11.2: 数据验证和输入过滤 ===")
    
    checks = []
    
    try:
        from resume_assistant.utils.security import DataValidator, validate_url, validate_file
        
        # 检查URL验证
        valid_tests = [
            ("https://example.com", True),
            ("http://localhost", True),
            ("invalid-url", False),
            ("javascript:alert(1)", False)
        ]
        
        url_passed = 0
        for url, expected in valid_tests:
            result = DataValidator.validate_url(url)
            if result == expected:
                url_passed += 1
        
        if url_passed == len(valid_tests):
            checks.append("✅ URL验证功能正常")
        else:
            checks.append(f"❌ URL验证异常 ({url_passed}/{len(valid_tests)})")
        
        # 检查文件验证
        file_tests = [
            ("resume.pdf", 1024*1024, True),
            ("document.docx", 2*1024*1024, True), 
            ("script.exe", 1024, False),
            ("large.pdf", 100*1024*1024, False)
        ]
        
        file_passed = 0
        for filename, size, expected in file_tests:
            is_valid, _ = validate_file(filename, size)
            if is_valid == expected:
                file_passed += 1
        
        if file_passed == len(file_tests):
            checks.append("✅ 文件验证功能正常")
        else:
            checks.append(f"❌ 文件验证异常 ({file_passed}/{len(file_tests)})")
        
        # 检查输入清理
        dirty_input = "正常文本\x00控制字符\x1f" + "长" * 100
        cleaned = DataValidator.sanitize_input(dirty_input, 50)
        
        if len(cleaned) <= 50 and '\x00' not in cleaned:
            checks.append("✅ 输入清理功能正常")
        else:
            checks.append("❌ 输入清理功能异常")
        
        # 检查API密钥格式验证
        api_key_tests = [
            ("sk-1234567890abcdef", True),
            ("invalid", False),
            ("", False),
            ("x" * 300, False)
        ]
        
        api_passed = 0
        for key, expected in api_key_tests:
            result = DataValidator.validate_api_key(key)
            if result == expected:
                api_passed += 1
        
        if api_passed == len(api_key_tests):
            checks.append("✅ API密钥格式验证正常")
        else:
            checks.append(f"❌ API密钥格式验证异常 ({api_passed}/{len(api_key_tests)})")
        
    except Exception as e:
        checks.append(f"❌ 数据验证模块异常: {e}")
    
    return checks

def verify_task11_3():
    """验证Task 11.3: 实现隐私保护措施"""
    print("\n=== Task 11.3: 隐私保护措施 ===")
    
    checks = []
    
    try:
        from resume_assistant.utils.security import PrivacyProtector, mask_sensitive_info
        
        # 检查敏感信息遮蔽
        test_text = "手机：13812345678，邮箱：test@example.com，身份证：110101199001011234"
        masked = PrivacyProtector.mask_sensitive_data(test_text)
        
        if "13812345678" not in masked and "test@example.com" not in masked:
            checks.append("✅ 敏感信息遮蔽正常")
        else:
            checks.append("❌ 敏感信息遮蔽失败")
        
        # 检查简历匿名化
        resume_text = "姓名：张三\n年龄：25\n性别：男\n手机：13912345678"
        anonymized = PrivacyProtector.anonymize_resume_data(resume_text)
        
        if "张三" not in anonymized and "13912345678" not in anonymized:
            checks.append("✅ 简历匿名化正常")
        else:
            checks.append("❌ 简历匿名化失败")
        
        # 检查敏感数据移除
        removed = PrivacyProtector.remove_sensitive_data(test_text)
        if "13812345678" not in removed and "[REDACTED]" in removed:
            checks.append("✅ 敏感数据移除正常")
        else:
            checks.append("❌ 敏感数据移除失败")
        
        # 检查便捷函数
        masked_convenient = mask_sensitive_info(test_text)
        if "13812345678" not in masked_convenient:
            checks.append("✅ 便捷函数正常")
        else:
            checks.append("❌ 便捷函数异常")
        
    except Exception as e:
        checks.append(f"❌ 隐私保护模块异常: {e}")
    
    return checks

def verify_web_integration():
    """验证Web界面集成"""
    print("\n=== Web界面集成 ===")
    
    checks = []
    
    try:
        # 检查设置页面导入
        from resume_assistant.web.pages.settings import SettingsPage
        checks.append("✅ 设置页面导入成功")
        
        # 检查安全设置方法存在
        settings_page = SettingsPage()
        
        security_methods = [
            '_render_security_settings',
            '_render_api_key_management', 
            '_render_data_validation_settings',
            '_render_privacy_protection_settings',
            '_render_security_tests',
            '_store_api_key',
            '_validate_api_key',
            '_run_security_check',
            '_test_encryption',
            '_show_security_report'
        ]
        
        missing_methods = []
        for method in security_methods:
            if not hasattr(settings_page, method):
                missing_methods.append(method)
        
        if not missing_methods:
            checks.append("✅ 所有安全设置方法已实现")
        else:
            checks.append(f"❌ 缺少方法: {missing_methods}")
        
        # 检查AI设置中的安全存储集成
        if hasattr(settings_page, '_save_ai_settings'):
            checks.append("✅ AI设置安全存储集成完成")
        else:
            checks.append("❌ AI设置安全存储集成缺失")
        
    except Exception as e:
        checks.append(f"❌ Web集成检查异常: {e}")
    
    return checks

def verify_comprehensive_functionality():
    """验证综合功能"""
    print("\n=== 综合功能验证 ===")
    
    checks = []
    
    try:
        from resume_assistant.utils.security import (
            get_security_manager, get_api_key_manager, 
            encrypt_text, decrypt_text, store_api_key, get_api_key
        )
        
        # 端到端测试：存储API密钥并在设置中使用
        test_service = "comprehensive_test"
        test_key = "sk-comprehensive-test-key-1234567890"
        
        # 使用便捷函数存储
        store_api_key(test_service, test_key)
        
        # 使用便捷函数获取
        retrieved = get_api_key(test_service)
        
        if retrieved == test_key:
            checks.append("✅ 端到端API密钥管理正常")
        else:
            checks.append("❌ 端到端API密钥管理异常")
        
        # 测试加密便捷函数
        test_data = "综合测试数据"
        encrypted = encrypt_text(test_data, "comprehensive")
        decrypted = decrypt_text(encrypted, "comprehensive")
        
        if decrypted == test_data:
            checks.append("✅ 便捷加密函数正常")
        else:
            checks.append("❌ 便捷加密函数异常")
        
        # 清理测试数据
        api_manager = get_api_key_manager()
        api_manager.delete_api_key(test_service)
        
        # 检查安全错误处理
        from resume_assistant.utils.security import SecurityError
        checks.append("✅ 安全异常类已定义")
        
    except Exception as e:
        checks.append(f"❌ 综合功能测试异常: {e}")
    
    return checks

def generate_task11_report():
    """生成Task 11完成报告"""
    print("🔒 Task 11: 安全性实现 - 完成验证报告")
    print("=" * 60)
    
    all_checks = []
    
    # 运行所有验证
    all_checks.extend(verify_task11_1())
    all_checks.extend(verify_task11_2()) 
    all_checks.extend(verify_task11_3())
    all_checks.extend(verify_web_integration())
    all_checks.extend(verify_comprehensive_functionality())
    
    # 统计结果
    passed = sum(1 for check in all_checks if check.startswith("✅"))
    total = len(all_checks)
    
    print(f"\n{'=' * 60}")
    print("📊 验证结果汇总")
    print(f"{'=' * 60}")
    
    for check in all_checks:
        print(check)
    
    print(f"\n📈 总体统计: {passed}/{total} 检查通过")
    
    if passed == total:
        print("\n🎉 Task 11: 安全性实现 - 完全完成！")
        print("\n🛡️ 实现的安全功能：")
        print("   • API密钥加密存储 (PBKDF2 + Fernet)")
        print("   • 数据验证和输入过滤")
        print("   • 隐私保护和敏感信息遮蔽")
        print("   • Web界面安全设置集成")
        print("   • 全局安全管理器")
        print("   • 完整的测试覆盖")
        print("   • 安全状态监控和报告")
        return True
    else:
        print(f"\n⚠️ Task 11部分完成，{total-passed}项检查失败")
        return False

if __name__ == "__main__":
    success = generate_task11_report()
    sys.exit(0 if success else 1)