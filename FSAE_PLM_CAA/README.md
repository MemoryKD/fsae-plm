# FSAE-PLM CAA V5 Add-in

CATIA V5 原生插件，通过 CAA V5 框架将 PLM 功能嵌入 CATIA 工具栏。

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| CATIA V5 | V5-6R 2018 或更高 |
| CAA RADE | 与 CATIA 版本匹配 |
| Visual Studio | VS 2015/2017/2019（取决于 CAA 版本） |
| 操作系统 | Windows 10/11 (64 位，CATIA 32 位兼容) |

## 项目结构

```
FSAE_PLM_CAA/
├── CATFSAEPLM/                  # CAA Framework
│   ├── IdentityCard/            # Framework identity
│   ├── PublicInterfaces/        # Public headers
│   │   ├── PlmBridge.h          # HTTP API client
│   │   ├── PlmCommands.h        # Toolbar button commands
│   │   ├── PlmToolbar.h         # Workbench + toolbar definition
│   │   └── PlmDialogs.h         # Login/Parts/Detail/Create dialogs
│   ├── ProtectedInterfaces/     # Protected headers
│   ├── LocalInterfaces/         # Local headers
│   ├── src/                     # Implementation
│   │   ├── PlmBridge.cpp        # WinHTTP communication + registry config
│   │   ├── PlmCommands.cpp      # Command Activate() handlers
│   │   ├── PlmToolbar.cpp       # Workbench creation
│   │   └── PlmDialogs.cpp       # CATDlgDialog implementations
│   └── resources/               # Icons, NLS resources
├── CATFSAEPLMMod/               # CAA Module
├── deploy.bat                   # Build + deploy script
└── README.md                    # This file
```

## 功能列表

| 工具栏按钮 | 功能 | 实现状态 |
|-----------|------|---------|
| Login | 登录 PLM 系统 | 骨架完成 |
| Search | 搜索/浏览零件列表 | 骨架完成 |
| Checkout | 检出零件并下载文件到 CATIA | 骨架完成 |
| Checkin | 检入当前 CATIA 文档到 PLM | 骨架完成 |
| Publish | 发布零件（更改生命周期状态） | 骨架完成 |
| Sync Props | 同步 PLM 属性到 CATIA 文档 | 骨架完成 |
| Create Part | 新建零件（模板自动编号） | 骨架完成 |

## 开发指南

### 1. 安装 CAA RADE

```batch
REM 1. 安装 Visual Studio（C++ 工作负载）
REM 2. 安装 CAA RADE（版本匹配 CATIA）
REM 3. 运行 cnext.exe 配置环境
set CATNextPath=C:\Program Files\Dassault Systemes\CAA V5-6R 2020\CAADoc
call "%CATNextPath%\cnext.exe"
```

### 2. 打开项目

在 Visual Studio 中打开 `FSAE_PLM_CAA.sln`，确保 CAA 工具栏已加载。

### 3. 构建

```
Build > Build Solution (F7)
```

### 4. 部署

```batch
deploy.bat
```

或手动将编译后的 DLL 复制到 CATIA startup 目录。

## 技术栈

| 组件 | 技术 |
|------|------|
| 框架 | CAA V5 (C++) |
| HTTP 通信 | Windows WinHTTP API |
| JSON 解析 | nlohmann/json (header-only) |
| UI | CATDlgDialog (CAA 原生对话框) |
| 配置存储 | Windows Registry (HKCU\SOFTWARE\FSAE_PLM) |
| CATIA 接口 | CATIProduct, CATIDocument, CATIProperties |

## 后端 API

所有 API 调用指向 FSAE-PLM 后端 `http://localhost/api`，详见 [API 文档](../README.md#api-端点)。
