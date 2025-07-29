# 二维码生成器系统

一个基于Flask的专业二维码生成器系统，专为试块信息管理设计，支持文件上传、在线预览、管理员后台等完整功能。

## 🚀 功能特性

### 核心功能
- 📝 **试块信息管理** - 支持试块编号、材质、反射体类型、存放区域等信息录入
- 📄 **文件上传与管理** - 支持任意格式文件上传（不限于PDF），自动重命名防冲突
- 📱 **二维码生成** - 自动生成包含试块信息的二维码，支持下载
- 👀 **在线预览** - 扫码或直接访问查看试块详情，支持PDF在线预览
- 🔐 **管理员后台** - 完整的后台管理系统，支持数据管理和系统配置
- 📊 **操作日志** - 详细记录所有管理员操作，确保数据安全

### 管理员功能
- 🔑 **安全登录** - MD5加密密码，会话管理，1小时自动超时
- 📋 **记录管理** - 查看、编辑、删除所有试块记录
- ⚙️ **配置管理** - 管理下拉列表选项（材质、反射体类型、存放区域）
- 🔒 **密码管理** - 在线修改管理员密码
- 📋 **操作审计** - 查看所有操作日志（只读）
- 🚪 **安全登出** - 手动登出和自动超时保护

### PDF预览功能
- 📖 **在线预览** - 支持PDF文件在线查看，无需下载
- 🔍 **缩放控制** - 支持放大、缩小、适应页面、适应宽度
- 📄 **页面导航** - 支持多页PDF的页面切换
- 📱 **响应式设计** - 适配不同设备屏幕尺寸

## 🛠 技术架构

- **后端框架**: Python Flask + Flask-CORS
- **前端技术**: HTML5 + CSS3 + JavaScript (原生)
- **数据存储**: JSON文件系统（轻量级，易备份）
- **二维码生成**: qrcode + Pillow
- **文件处理**: Werkzeug (安全文件上传)
- **PDF预览**: PDF.js (浏览器原生支持)
- **会话管理**: Flask Session (服务器端会话)

## 📦 安装部署

### 环境要求
- Python 3.7+
- pip包管理器
- 现代浏览器（支持PDF.js）

### 快速开始

1. **克隆项目**
```bash
git clone https://github.com/bbyas22/QRcode.git
cd QRcode
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python app.py
```

4. **访问应用**
- 主页面: http://127.0.0.1:8000
- 管理员后台: http://127.0.0.1:8000/admin
- 初始管理员密码: `123456`

### 生产环境部署

#### 1. 修改配置

编辑 `data/app_config.json`：
```json
{
  "baseUrl": "https://your-domain.com",
  "appName": "二维码生成系统",
  "version": "1.0.0",
  "description": "用于生成和管理试块二维码的系统",
  "server": {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": false
  }
}
```

#### 2. Nginx反向代理配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 100M;  # 支持大文件上传
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://127.0.0.1:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**注意，baseUrl 是指最后可以用于访问项目的url，比如用Nginx反代到https://your-domain.com/QRcode，那么baseUrl就填写https://your-domain.com/QRcode，不能填写http://127.0.0.1:8000**

## 📁 项目结构

```
QRcode2/
├── app.py                    # Flask主应用文件
├── requirements.txt          # Python依赖包列表
├── README.md                # 项目说明文档
├── templates/               # HTML模板目录
│   ├── index.html           # 主页面（试块信息录入）
│   ├── admin_login.html     # 管理员登录页面
│   ├── admin.html           # 管理员后台面板
│   ├── view.html            # 试块信息查看页面
│   └── pdf_viewer.html      # PDF在线预览页面
├── uploads/                 # 用户上传文件存储目录
├── qrcodes/                 # 生成的二维码图片存储目录
├── data/                    # 系统数据文件目录
│   ├── admin.json           # 管理员密码（MD5加密）
│   ├── app_config.json      # 应用配置文件
│   ├── dropdown_config.json # 下拉列表配置
│   └── *.json              # 试块记录数据文件（UUID命名）
└── logs/                    # 系统日志目录
    └── admin_operations.json # 管理员操作日志
```

## 📖 使用指南

### 普通用户操作

1. **录入试块信息**
   - 访问主页面
   - 填写试块编号（必填，仅支持字母、数字、连字符、下划线）
   - 选择或输入材质、反射体类型、存放区域
   - 可选择上传检验证书文件

2. **生成二维码**
   - 点击"生成二维码"按钮
   - 系统自动生成唯一二维码
   - 可直接下载二维码图片

3. **查看试块信息**
   - 扫描二维码或直接访问链接
   - 查看完整试块信息
   - 在线预览或下载证书文件

### 管理员操作

1. **登录管理**
   - 访问 `/admin` 进入登录页面
   - 输入管理员密码（初始密码：123456）
   - 系统自动管理会话，1小时后自动登出

2. **记录管理**
   - 查看所有试块记录列表
   - 编辑试块信息（除文件外的所有字段）
   - 删除试块记录（同时删除关联文件）
   - 直接跳转查看试块详情

3. **配置管理**
   - 管理材质选项列表
   - 管理反射体类型选项
   - 管理存放区域选项
   - 配置应用基础URL和服务器参数

4. **系统维护**
   - 修改管理员密码
   - 查看操作日志（包含时间、操作类型、详细信息）
   - 监控系统使用情况

### PDF预览功能

1. **访问预览**
   - 在试块详情页面点击"在线预览"按钮
   - 或直接访问 `/pdf-viewer?file=filename`

2. **预览控制**
   - 🔍 放大/缩小：调整PDF显示比例
   - 📄 适应页面：PDF适应浏览器窗口大小
   - 📱 适应宽度：PDF适应设备屏幕宽度
   - ⬅️➡️ 页面导航：多页PDF的前后翻页
   - ⬇️ 下载：下载PDF文件到本地

## 🔒 安全特性

### 身份认证与授权
- 🔐 管理员密码MD5加密存储
- 🛡️ 基于Session的会话管理
- ⏰ 1小时会话超时自动清理
- 🔄 定期会话状态检查（每5分钟）
- 🚫 未授权访问自动重定向

### 数据安全
- 📝 所有管理员操作记录详细日志
- 🔒 操作日志只读，不可修改
- 🆔 UUID确保记录和文件唯一性
- 🧹 输入数据清理和验证
- 📁 文件上传安全检查（大小限制100MB）

### 系统安全
- 🔧 试块编号格式严格验证
- 🛡️ XSS攻击防护
- 📊 文件类型和大小限制
- 🔄 自动文件重命名防冲突
- 📋 详细错误日志记录

## ⚙️ 配置说明

### 应用配置 (app_config.json)

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| baseUrl | 应用基础URL，用于生成二维码链接 | `http://localhost:8000` |
| appName | 应用名称，显示在页面标题 | `二维码生成系统` |
| version | 应用版本号 | `1.0.0` |
| description | 应用描述信息 | `用于生成和管理试块二维码的系统` |
| server.host | 服务器监听地址 | `127.0.0.1` / `0.0.0.0` |
| server.port | 服务器端口号 | `8000` |
| server.debug | 调试模式开关 | `true` / `false` |

### 下拉列表配置 (dropdown_config.json)

管理员可以通过后台界面配置以下选项：
- **materials**: 材质选项（如：钢材、混凝土、铝合金等）
- **reflector_types**: 反射体类型（如：平底孔、横通孔、斜孔等）
- **storage_areas**: 存放区域（如：A区、B区、C区等）

### 文件存储配置

| 目录 | 用途 | 说明 |
|------|------|------|
| uploads/ | 用户上传文件 | 支持任意格式，自动UUID重命名 |
| qrcodes/ | 二维码图片 | PNG格式，与记录ID对应 |
| data/ | 系统数据文件 | JSON格式，包含配置和记录数据 |
| logs/ | 操作日志 | JSON格式，记录所有管理员操作 |

## 🔧 维护指南

### 日常维护

1. **数据备份**
```bash
# 备份重要数据目录
tar -czf backup_$(date +%Y%m%d).tar.gz data/ uploads/ logs/
```

2. **日志清理**
```bash
# 清理30天前的操作日志（可选）
find logs/ -name "*.json" -mtime +30 -delete
```

3. **文件清理**
```bash
# 清理孤立的文件（没有对应记录的文件）
python cleanup_orphaned_files.py
```

4. **密码安全**
- 定期通过管理员界面修改密码
- 生产环境建议使用强密码
- 定期检查登录日志

5. **性能监控**
- 监控磁盘使用情况
- 检查文件上传目录大小
- 监控系统内存和CPU使用率

### 故障排除

#### 常见问题

**1. 端口被占用**
```bash
# Windows
netstat -ano | findstr :8000
# Linux/Mac
lsof -i :8000

# 解决方案：修改配置文件中的端口号
```

**2. 文件上传失败**
- 检查uploads目录权限：`chmod 755 uploads/`
- 确认文件大小不超过100MB
- 检查磁盘空间是否充足

**3. 二维码无法访问**
- 检查baseUrl配置是否正确
- 确认防火墙设置允许对应端口
- 验证网络连接和DNS解析

**4. 管理员无法登录**
- 检查admin.json文件是否存在
- 重置密码：删除admin.json文件，重启应用
- 检查会话是否过期

**5. PDF预览无法正常工作**
- 确认浏览器支持PDF.js
- 检查文件是否存在于uploads目录
- 验证文件权限设置

**6. 配置无法保存**
- 检查data目录写权限
- 验证JSON格式是否正确
- 确认baseUrl格式（必须以http://或https://开头）

#### 错误日志

系统错误信息主要记录在：
- 控制台输出（应用启动日志）
- `logs/admin_operations.json`（管理员操作日志）
- 浏览器开发者工具（前端错误）


## ⚠️ 重要提醒

1. **首次部署后请立即修改管理员密码！**
2. **生产环境请关闭调试模式（debug: false）**
3. **定期备份数据目录和上传文件**
4. **建议使用HTTPS协议保护数据传输**
5. **定期更新系统和依赖包**

---

**项目开发**: 基于Flask框架开发的专业二维码生成系统  
**技术栈**: Python + Flask + JavaScript + PDF.js  
**许可证**: MIT License  
**版本**: v1.0.0