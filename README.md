# Extreme-Programming
```
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

## 许可证
MIT
```
