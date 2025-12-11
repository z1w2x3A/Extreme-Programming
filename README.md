# Extreme-Programming
```
Backend
# 联系人管理小程序（Flask + SQLite）
基于 Flask 的轻量级联系人管理后端，支持：
- 用户注册/登录（SHA256 密码）
- 联系人增删改查
- 多种联系方式（电话、邮箱、社交媒体、地址）
- 收藏功能
- Excel 导入/导出
- RESTful API，CORS 跨域

## 快速开始
1. 克隆仓库
2. 安装依赖
```bash
pip install flask flask-cors pandas openpyxl
```
3. 运行
```bash
python app.py
```
服务启动后，浏览器访问 http://127.0.0.1:5500 即可打开前端页面（contacts.html）。

## 数据库
首次启动自动创建 `db.sqlite`，含以下表：
- users：用户
- contacts：联系人（含 is_favorite）
- contact_methods：一对多联系方式

## API 概览
| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| POST | /register | 注册 |
| POST | /login | 登录 |
| POST | /contacts | 新增联系人 |
| GET | /contacts/{user_id} | 获取联系人列表 |
| PUT | /contacts/{contact_id} | 更新联系人 |
| DELETE | /contacts/{contact_id} | 删除联系人 |
| POST | /contacts/{contact_id}/favorite | 切换收藏 |
| GET | /contacts/export/{user_id} | 导出 Excel |
| POST | /contacts/import/{user_id} | 导入 Excel |

请求/响应格式详见代码注释。

## Excel 文件格式
导入/导出均要求包含“姓名”列，其余可选列：
- 收藏（填写“是”表示收藏）
- 电话/邮箱/社交媒体/地址  
多个值请用英文逗号分隔。

## 目录结构
```
project
├─ backend
│  └─ app.py
├─ frontend
│  └─ contacts.html
└─ db.sqlite
```

## 注意事项
- 默认端口 5500，调试模式已开启，生产环境请关闭 debug。
- 密码使用 SHA256 哈希存储，未加盐，如有更高安全需求请自行增强。
- 前端资源放在 `frontend` 目录，通过 `/frontend/<path>` 访问。


  Frontend

# 联系人管理前端 (Contact Manager Frontend)

## 项目简介
基于原生 HTML/CSS/JavaScript 的单页应用，提供完整的联系人管理 UI，支持登录/注册、增删改查、收藏、多联系方式、Excel 导入/导出、模糊搜索、收藏视图切换等功能。  
与后端 Flask API 配套使用，CORS 跨域开箱即用。

## 快速开始
1. 将 `contacts.html` 放入 `frontend` 目录（与后端 `app.py` 中的 `FRONTEND_DIR` 对应）。
2. 启动后端服务（`python app.py`）。
3. 浏览器访问 http://127.0.0.1:5500 即可。

## 功能一览
| 功能 | 说明 |
| ---- | ---- |
| 登录/注册 | 支持用户注册与 SHA256 密码登录 |
| 联系人列表 | 头像 + 名称 + 多联系方式（电话/邮箱/社交媒体/地址） |
| 收藏 | 点击星标快速切换，支持仅显示收藏 |
| 搜索 | 实时按名称模糊过滤（回车触发） |
| 新增 | 动态添加/删除多组联系方式 |
| 编辑 | 原位编辑名称与全部联系方式 |
| 删除 | 二次确认后删除 |
| Excel 导出 | 一键生成 `contacts.xlsx`（含收藏列） |
| Excel 导入 | 选择 `.xls/.xlsx` 文件批量导入（需“姓名”列） |
| 响应式 | 毛玻璃背景、卡片阴影、悬浮动画，适配 PC/移动 |

## 文件结构
```
project
├─ backend
│  └─ app.py
├─ frontend
│  ├─ contacts.html   ← 本文件
│  └─ xingkong.jpg    ← 登录页背景图（可选）
└─ db.sqlite
```

## 主要组件
- **登录/注册页**：全屏星空背景 + 毛玻璃面板
- **顶部栏**：标题 + 注销按钮
- **工具栏**：搜索框 + 收藏视图切换 + 导入/导出按钮
- **新增卡片**：名称输入 + 动态联系方式行
- **联系人列表**：卡片式展示，支持编辑/删除/收藏

## 浏览器兼容
- Chrome 80+ / Edge 80+ / Firefox 75+ / Safari 13+
- 依赖：原生 ES6+，无需额外构建

## 配置与自定义
- 后端地址默认 `http://localhost:5500`，可在 `<script>` 顶部修改 `API` 变量。
- 背景图路径 `/frontend/xingkong.jpg`，可替换任意图片。
- 主题色、圆角、阴影等均在 `<style>` 开头集中定义，方便一键换肤。

## 注意事项
- 所有数据通过后端 REST API 持久化，前端不缓存敏感信息。
- 导入 Excel 时，表头需包含“姓名”列，其余列（电话/邮箱/社交媒体/地址）可选，多值用英文逗号分隔。
- 若部署到生产环境，请将后端 `debug=False` 并启用 HTTPS，防止明文传输密码。


## 许可证
MIT
```
