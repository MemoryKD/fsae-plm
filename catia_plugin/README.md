# CATIA PLM 插件安装说明

## 安装步骤

1. 打开 CATIA V5
2. 菜单：工具 → 宏 → 宏...
3. 点击「宏文件...」，选择 `FSAE_PLM_Macro.catvba`
4. 选择 `SaveToPLM` 宏，点击「运行」

## 配置

修改宏代码中的 `PLM_SERVER` 常量为你的 PLM 服务器地址：
```vba
Const PLM_SERVER As String = "http://your-server:8000"
```

## 添加到工具栏

1. 菜单：工具 → 自定义
2. 选择「命令」标签页，类别选择「宏」
3. 将 `SaveToPLM`、`CheckNaming` 拖到工具栏

## 功能

- **保存到 PLM**：读取 CATIA 文件属性，上传到 PLM 服务器
- **检查命名**：验证当前文件是否符合编号规则
