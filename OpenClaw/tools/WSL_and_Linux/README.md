# OpenClaw WSL/Ubuntu 安装管理器

[![Version](https://img.shields.io/badge/version-1.1-blue.svg)]()
[![Platform](https://img.shields.io/badge/platform-WSL2%20%7C%20Ubuntu-orange.svg)]()
[![Node](https://img.shields.io/badge/node-%3E%3D22.0.0-green.svg)]()

一个专为 WSL2 (Windows Subsystem for Linux) 和原生 Ubuntu 设计的 OpenClaw 管理脚本，支持一键安装、更新和卸载，自动处理 Windows 与 WSL 环境混用问题。

---

## 📋 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [使用方法](#使用方法)
- [故障排除](#故障排除)
- [技术细节](#技术细节)
- [许可证](#许可证)

---

## ✨ 功能特性


| 特性                    | 说明                                                |
| ----------------------- | --------------------------------------------------- |
| **🖥️ 跨平台支持**     | 专为 WSL2 + Ubuntu 优化，同时支持原生 Ubuntu        |
| **🔧 自动环境修复**     | 智能检测并修复 Windows 与 WSL 环境混用问题          |
| **📦 Node.js 自动安装** | 通过 nvm 自动安装 Node.js v22.14.0，无需手动配置    |
| **🚀 双模式安装**       | 优先尝试官方安装脚本，失败时自动回退到 npm 全局安装 |
| **⚡ 镜像加速**         | 默认使用 npmmirror 镜像源，国内访问更快             |
| **🔄 完整生命周期**     | 支持 install / uninstall / update 全生命周期管理    |
| **🛡️ 冲突检测**       | 自动检测并处理 Windows 版本 OpenClaw 的冲突         |

---

## 🖥️ 环境要求

### 必需条件

- **操作系统**: Windows 10/11  with WSL2 + Ubuntu，或原生 Ubuntu 20.04+
- **网络连接**: 用于下载 Node.js 和 OpenClaw
- **磁盘空间**: 建议预留 500MB 以上空间

### 可选条件

- **sudo 权限**: 用于安装系统依赖（curl、git、build-essential）

---

## 🚀 快速开始

### 1. 下载脚本

```bash
# 克隆或下载脚本到本地
curl -fsSL https://your-repo-url/openclaw-installer.sh -o openclaw-installer.sh

# 或者手动创建文件并粘贴脚本内容
nano openclaw-installer.sh
```

### 2. 添加执行权限

```bash
chmod +x openclaw-installer.sh
```

### 3. 运行安装

```bash
./openclaw-installer.sh install
```

---

## 📖 使用方法

### 命令概览


| 命令        | 说明                      |
| ----------- | ------------------------- |
| `install`   | 安装 OpenClaw（默认命令） |
| `update`    | 更新到最新版本            |
| `uninstall` | 完全卸载并清理配置        |
| `help`      | 显示帮助信息              |

### 详细用法

#### 安装 OpenClaw

```bash
# 默认安装（推荐）
./openclaw-installer.sh

# 或显式指定 install
./openclaw-installer.sh install
```

**安装流程：**

1. 检查并安装系统依赖（curl、git、build-essential）
2. 检测并卸载 Windows 版本的 OpenClaw（如果存在）
3. 修复 PATH 优先级，确保 WSL 环境优先
4. 通过 nvm 安装 Node.js v22.14.0（如果未安装）
5. 配置 npm 使用国内镜像源
6. 尝试官方安装脚本安装 OpenClaw
7. 官方脚本失败时，自动回退到 npm 全局安装

#### 更新 OpenClaw

```bash
./openclaw-installer.sh update
```

**更新流程：**

1. 检查当前版本
2. 尝试 `npm update -g openclaw`
3. 版本未变化时，强制安装最新版
4. 清理 npm 缓存

#### 卸载 OpenClaw

```bash
./openclaw-installer.sh uninstall
```

**卸载流程：**

1. 检测并卸载 Windows 版本（如果存在）
2. 卸载 WSL 版本
3. 清理 npm 缓存
4. 删除配置文件（`~/.openclaw`、`~/.config/openclaw` 等）

---

## 🔧 故障排除

### 问题 1: "exec: node: not found"

**现象：**

```bash
$ openclaw --version
/mnt/c/Users/.../openclaw: 15: exec: node: not found
```

**原因：**
Windows 版本的 OpenClaw 无法在 WSL 中找到 Windows 的 Node.js 运行时。

**解决：**
脚本已自动处理此问题。运行 `./openclaw-installer.sh install` 即可：

- 自动卸载 Windows 版本
- 安装 WSL 版本的 Node.js 和 OpenClaw
- 修复 PATH 优先级

### 问题 2: 命令未找到 (command not found)

**现象：**

```bash
$ openclaw --version
bash: openclaw: command not found
```

**解决：**

```bash
# 刷新 hash 表
hash -r

# 或重新加载 shell
source ~/.bashrc

# 检查安装路径
which openclaw
```

### 问题 3: npm 权限错误

**现象：**

```bash
npm ERR! Error: EACCES: permission denied
```

**解决：**
脚本使用 nvm 管理 Node.js，避免使用 `sudo npm`。如需修复权限：

```bash
# 更改 npm 全局目录所有权
sudo chown -R $(whoami) ~/.npm

# 或使用 nvm 重新安装 Node.js
nvm reinstall-packages
```

### 问题 4: 网络连接超时

**现象：**
下载 Node.js 或 OpenClaw 时超时。

**解决：**
脚本已配置 npmmirror 镜像源。如需更换镜像：

```bash
# 临时更换为官方源
npm config set registry https://registry.npmjs.org/

# 或更换为淘宝镜像
npm config set registry https://registry.npmmirror.com/
```

---

## 🔍 技术细节

### 环境检测机制

脚本通过以下方式区分 Windows 和 WSL 环境：

```bash
# 检测 WSL
if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    echo "Running in WSL"
fi

# 检测 Windows 路径
if [[ "$(command -v node)" == /mnt/* ]]; then
    echo "Using Windows Node.js"
fi
```

### PATH 优先级修复

当检测到 Windows 环境冲突时，脚本自动：

1. **重新排序 PATH**：将 WSL 路径（`/usr/local/bin`、`/usr/bin` 等）移到 Windows 路径（`/mnt/...`）之前
2. **持久化配置**：将修复后的 PATH 写入 `~/.bashrc`

```bash
# 修复后的 PATH 示例
export PATH="/usr/local/bin:/usr/bin:/bin:/home/user/.nvm/versions/node/v22.14.0/bin:...:$PATH"
```

### 安装路径


| 组件       | WSL 路径                                         |
| ---------- | ------------------------------------------------ |
| Node.js    | `~/.nvm/versions/node/v22.14.0/bin/node`         |
| npm        | `~/.nvm/versions/node/v22.14.0/bin/npm`          |
| OpenClaw   | `~/.nvm/versions/node/v22.14.0/bin/openclaw`     |
| npm 全局包 | `~/.nvm/versions/node/v22.14.0/lib/node_modules` |
| 配置文件   | `~/.openclaw`、`~/.config/openclaw`              |

---

## 📝 版本历史


| 版本 | 日期       | 变更                                    |
| ---- | ---------- | --------------------------------------- |
| v1.1 | 2026-03-14 | 添加 Windows 环境冲突检测与自动修复     |
| v1.0 | 2026-03-14 | 初始版本，支持 install/uninstall/update |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🔗 相关链接

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [Node.js 官方网站](https://nodejs.org/)
- [nvm 项目](https://github.com/nvm-sh/nvm)
- [WSL 官方文档](https://docs.microsoft.com/zh-cn/windows/wsl/)

---

**Made with ❤️ for WSL Users**
