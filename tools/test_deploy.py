#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试远程部署脚本的基本功能
"""

import sys
import os
import tempfile
import tarfile
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

try:
    from remote_deploy import RemoteDeployer, Logger, ProgressIndicator
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保已安装依赖: pip install paramiko scp")
    sys.exit(1)

def test_progress_indicator():
    """测试进度指示器"""
    print("🧪 测试进度指示器...")
    
    progress = ProgressIndicator("测试进度显示")
    progress.start()
    
    import time
    time.sleep(2)
    
    progress.stop()
    Logger.success("进度指示器测试完成")

def test_logger():
    """测试日志输出"""
    print("🧪 测试日志输出...")
    
    Logger.info("这是信息日志")
    Logger.warning("这是警告日志")
    Logger.error("这是错误日志")
    Logger.step("这是步骤日志")
    Logger.success("这是成功日志")

def test_source_package():
    """测试源码包创建"""
    print("🧪 测试源码包创建...")
    
    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建模拟的项目结构
        (temp_path / "cmd").mkdir()
        (temp_path / "cmd" / "test.go").write_text("package main")
        
        (temp_path / "internal").mkdir()
        (temp_path / "internal" / "test.go").write_text("package internal")
        
        (temp_path / "pkg").mkdir()
        (temp_path / "pkg" / "test.go").write_text("package pkg")
        
        (temp_path / "etc").mkdir()
        (temp_path / "etc" / "config.csv").write_text("test,config")
        
        (temp_path / "go.mod").write_text("module test")
        (temp_path / "go.sum").write_text("# test")
        (temp_path / "Makefile").write_text("all:")
        (temp_path / "LICENSE").write_text("MIT License")
        
        # 切换到临时目录
        original_cwd = os.getcwd()
        os.chdir(temp_path)
        
        try:
            # 创建部署器实例
            deployer = RemoteDeployer("test", "test", "test")
            
            # 测试源码包创建
            source_file = deployer.prepare_source_package()
            
            if source_file and os.path.exists(source_file):
                Logger.success(f"源码包创建成功: {source_file}")
                
                # 验证tar包内容
                with tarfile.open(source_file, "r:gz") as tar:
                    members = tar.getnames()
                    Logger.info(f"包含文件: {', '.join(members)}")
                
                # 清理
                os.remove(source_file)
                return True
            else:
                Logger.error("源码包创建失败")
                return False
                
        finally:
            os.chdir(original_cwd)

def test_deployer_init():
    """测试部署器初始化"""
    print("🧪 测试部署器初始化...")
    
    deployer = RemoteDeployer(
        host="192.168.1.100",
        username="testuser",
        password="testpass",
        remote_dir="/tmp/test"
    )
    
    assert deployer.host == "192.168.1.100"
    assert deployer.username == "testuser"
    assert deployer.password == "testpass"
    assert deployer.remote_dir == "/tmp/test"
    
    Logger.success("部署器初始化测试完成")

def main():
    """主测试函数"""
    print("🚀 开始测试远程部署脚本...")
    print("=" * 50)
    
    tests = [
        ("日志输出", test_logger),
        ("进度指示器", test_progress_indicator),
        ("部署器初始化", test_deployer_init),
        ("源码包创建", test_source_package),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 运行测试: {test_name}")
            result = test_func()
            if result is not False:
                Logger.success(f"✅ {test_name} - 通过")
                passed += 1
            else:
                Logger.error(f"❌ {test_name} - 失败")
                failed += 1
        except Exception as e:
            Logger.error(f"❌ {test_name} - 异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: 通过 {passed}, 失败 {failed}")
    
    if failed == 0:
        Logger.success("🎉 所有测试通过！")
        return 0
    else:
        Logger.error(f"💥 有 {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
