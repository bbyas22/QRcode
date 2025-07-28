# -*- coding: utf-8 -*-
"""
二维码生成器后端服务
提供二维码生成、信息存储、文件管理等功能
"""

import os
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, session
from flask_cors import CORS
import qrcode
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.permanent_session_lifetime = timedelta(hours=1)
CORS(app)

# 配置
UPLOAD_FOLDER = 'uploads'
QRCODE_FOLDER = 'qrcodes'
DATA_FOLDER = 'data'
LOG_FOLDER = 'logs'
# 取消文件类型限制，允许所有文件类型
# ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}
ALLOWED_EXTENSIONS = set()  # 空集合表示不限制文件类型
# 应用配置文件路径
APP_CONFIG_FILE = os.path.join(DATA_FOLDER, 'app_config.json')

# 初始化应用配置文件
if not os.path.exists(APP_CONFIG_FILE):
    default_app_config = {
        'baseUrl': 'http://localhost:8000',
        'appName': '二维码生成系统',
        'version': '1.0.0',
        'description': '用于生成和管理试块二维码的系统',
        'server': {
            'host': '127.0.0.1',
            'port': 8000,
            'debug': True
        }
    }
    with open(APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_app_config, f, ensure_ascii=False, indent=2)

# 从配置文件读取baseUrl
def get_base_url():
    """从配置文件获取baseUrl"""
    try:
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('baseUrl', 'http://localhost:8000')
    except Exception as e:
        print(f'读取配置文件失败: {e}')
        return 'http://localhost:8000'  # 默认值

def get_server_config():
    """从配置文件获取服务器配置"""
    try:
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        server_config = config.get('server', {})
        return {
            'host': server_config.get('host', '127.0.0.1'),
            'port': server_config.get('port', 8000),
            'debug': server_config.get('debug', True)
        }
    except Exception as e:
        print(f'读取服务器配置失败: {e}')
        return {
            'host': '127.0.0.1',
            'port': 8000,
            'debug': True
        }

BASE_URL = get_base_url()

def update_html_templates_config():
    """更新HTML模板文件中的appConfig配置"""
    try:
        # 获取当前配置
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        base_url = config.get('baseUrl', 'http://localhost:8000')
        
        # 需要更新的HTML文件列表
        html_files = [
            os.path.join('templates', 'index.html'),
            os.path.join('templates', 'admin.html'),
            os.path.join('templates', 'admin_login.html'),
            os.path.join('templates', 'view.html'),
            os.path.join('templates', 'pdf_viewer.html')
        ]
        
        for html_file in html_files:
            if os.path.exists(html_file):
                # 读取文件内容
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换appConfig初始化代码
                # 匹配模式：let appConfig = { baseUrl: '' }; 或 let appConfig = { baseUrl: '任何内容' };
                pattern = r"let appConfig = \{ baseUrl: '[^']*' \};"
                replacement = f"let appConfig = {{ baseUrl: '{base_url}' }};"
                
                updated_content = re.sub(pattern, replacement, content)
                
                # 如果内容有变化，写回文件
                if updated_content != content:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f'已更新 {html_file} 中的appConfig配置')
        
        print(f'HTML模板配置更新完成，BASE_URL: {base_url}')
        
    except Exception as e:
        print(f'更新HTML模板配置失败: {e}')

# 创建必要的目录
for folder in [UPLOAD_FOLDER, QRCODE_FOLDER, DATA_FOLDER, LOG_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 初始化管理员密码文件
ADMIN_PASSWORD_FILE = os.path.join(DATA_FOLDER, 'admin.json')
if not os.path.exists(ADMIN_PASSWORD_FILE):
    # 初始密码: 123456
    initial_password = hashlib.md5('123456'.encode()).hexdigest()
    with open(ADMIN_PASSWORD_FILE, 'w', encoding='utf-8') as f:
        json.dump({'password': initial_password}, f)

# 初始化下拉列表配置文件
DROPDOWN_CONFIG_FILE = os.path.join(DATA_FOLDER, 'dropdown_config.json')
if not os.path.exists(DROPDOWN_CONFIG_FILE):
    default_config = {
        'materials': ['钢材', '混凝土', '铝合金', '其他'],
        'reflector_types': ['平底孔', '横通孔', '斜孔', '其他'],
        'storage_areas': ['A区', 'B区', 'C区', 'D区']
    }
    with open(DROPDOWN_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    # 如果ALLOWED_EXTENSIONS为空，则允许所有文件类型
    if not ALLOWED_EXTENSIONS:
        return '.' in filename  # 只要有扩展名就允许
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_input(text):
    """清理用户输入，进行基本验证"""
    if not text:
        return text
    
    # 移除潜在的脚本标签和事件处理器（但不进行HTML转义）
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    # 限制长度
    if len(text) > 200:
        text = text[:200]
    
    return text.strip()

def validate_specimen_number(specimen_number):
    """验证试块编号格式"""
    if not specimen_number:
        return False, "试块编号不能为空"
    
    # 只允许字母、数字、连字符和下划线
    if not re.match(r'^[a-zA-Z0-9_-]+$', specimen_number):
        return False, "试块编号只能包含字母、数字、连字符和下划线"
    
    if len(specimen_number) > 50:
        return False, "试块编号长度不能超过50个字符"
    
    return True, ""

def validate_file_security(file):
    """验证文件安全性"""
    if not file:
        return True, ""
    
    # 检查文件名
    filename = secure_filename(file.filename)
    if not filename:
        return False, "文件名无效"
    
    # 取消文件扩展名检查，允许所有文件类型
    # if not allowed_file(filename):
    #     return False, f"不支持的文件类型，仅支持：{', '.join(ALLOWED_EXTENSIONS)}"
    
    # 检查文件大小（限制为100MB）
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if file_size > 100 * 1024 * 1024:  # 100MB
        return False, "文件大小不能超过100MB"
    
    # 取消文件内容魔数检查，允许所有文件类型
    # file_header = file.read(8)
    # file.seek(0)  # 重置文件指针
    # 
    # # PDF文件魔数检查
    # if filename.lower().endswith('.pdf'):
    #     if not file_header.startswith(b'%PDF'):
    #         return False, "PDF文件格式无效"
    # 
    # # Office文档魔数检查
    # elif filename.lower().endswith(('.doc', '.xls')):
    #     if not file_header.startswith(b'\xd0\xcf\x11\xe0'):
    #         return False, "Office文档格式无效"
    # 
    # elif filename.lower().endswith(('.docx', '.xlsx')):
    #     if not file_header.startswith(b'PK'):
    #         return False, "Office文档格式无效"
    
    return True, ""

def log_admin_operation(operation_type, ip_address, before_state, after_state):
    """记录管理员操作日志"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation_type': operation_type,
        'ip_address': ip_address,
        'before_state': before_state,
        'after_state': after_state
    }
    
    log_file = os.path.join(LOG_FOLDER, 'admin_operations.json')
    logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/admin')
def admin_login():
    """管理员登录页面"""
    if 'admin_logged_in' in session:
        return render_template('admin.html')
    return render_template('admin_login.html')

@app.route('/admin/panel')
def admin_panel():
    """管理员面板"""
    if not check_admin_session():
        return redirect(url_for('admin_login'))
    return render_template('admin.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """管理员登录处理"""
    password = request.form.get('password')
    if not password:
        return jsonify({'success': False, 'message': '请输入密码'})
    
    # 验证密码
    with open(ADMIN_PASSWORD_FILE, 'r', encoding='utf-8') as f:
        admin_data = json.load(f)
    
    password_hash = hashlib.md5(password.encode()).hexdigest()
    if password_hash == admin_data['password']:
        session.permanent = True
        session['admin_logged_in'] = True
        session['login_time'] = datetime.now().isoformat()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '密码错误'})

@app.route('/admin/logout')
def admin_logout():
    """管理员登出"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/logout', methods=['POST'])
def admin_logout_api():
    """管理员登出API"""
    session.clear()
    return jsonify({'success': True, 'message': '已成功登出'})

@app.route('/api/dropdown-config')
def get_dropdown_config():
    """获取下拉列表配置"""
    with open(DROPDOWN_CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return jsonify(config)

@app.route('/api/config')
def get_config():
    """获取基础配置信息（仅返回baseUrl）"""
    try:
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 只返回baseUrl，其他配置信息不再暴露
        return jsonify({
            'baseUrl': config.get('baseUrl', 'http://localhost:8000')
        })
    except Exception as e:
        # 如果读取失败，返回默认配置
        return jsonify({
            'baseUrl': 'http://localhost:8000'
        })



@app.route('/api/generate-qrcode', methods=['POST'])
def generate_qrcode():
    """生成二维码"""
    try:
        # 获取表单数据
        specimen_number = request.form.get('specimen_number', '').strip()
        material = request.form.get('material', '').strip()
        reflector_type = request.form.get('reflector_type', '').strip()
        storage_area = request.form.get('storage_area', '').strip()
        
        # 验证必填字段
        if not all([specimen_number, material, reflector_type, storage_area]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'})
        
        # 验证试块编号格式
        is_valid, error_msg = validate_specimen_number(specimen_number)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg})
        
        # 清理用户输入
        specimen_number = sanitize_input(specimen_number)
        material = sanitize_input(material)
        reflector_type = sanitize_input(reflector_type)
        storage_area = sanitize_input(storage_area)
        
        # 处理文件上传
        certificate_file = None
        if 'certificate' in request.files:
            file = request.files['certificate']
            if file and file.filename:
                # 验证文件安全性
                is_safe, error_msg = validate_file_security(file)
                if not is_safe:
                    return jsonify({'success': False, 'message': error_msg})
                
                filename = secure_filename(file.filename)
                # 使用UUID重命名文件
                if '.' in filename:
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{uuid.uuid4()}.{file_ext}"
                else:
                    # 如果文件没有扩展名，直接使用UUID作为文件名
                    new_filename = str(uuid.uuid4())
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                file.save(file_path)
                certificate_file = new_filename
        
        # 生成唯一ID
        record_id = str(uuid.uuid4())
        
        # 保存记录
        record_data = {
            'id': record_id,
            'specimen_number': specimen_number,
            'material': material,
            'reflector_type': reflector_type,
            'storage_area': storage_area,
            'certificate_file': certificate_file,
            'created_at': datetime.now().isoformat()
        }
        
        record_file = os.path.join(DATA_FOLDER, f"{record_id}.json")
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)
        
        # 生成二维码
        qr_url = f"{BASE_URL}/view/{record_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_filename = f"{record_id}.png"
        qr_path = os.path.join(QRCODE_FOLDER, qr_filename)
        qr_image.save(qr_path)
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'qr_image_url': f"{BASE_URL}/api/qrcode/{record_id}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'})

@app.route('/api/qrcode/<record_id>')
def get_qrcode(record_id):
    """获取二维码图片"""
    qr_path = os.path.join(QRCODE_FOLDER, f"{record_id}.png")
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    return "二维码不存在", 404

@app.route('/view/<record_id>')
def view_record(record_id):
    """查看记录详情页面"""
    record_file = os.path.join(DATA_FOLDER, f"{record_id}.json")
    if not os.path.exists(record_file):
        return "记录不存在", 404
    
    with open(record_file, 'r', encoding='utf-8') as f:
        record_data = json.load(f)
    
    return render_template('view.html', record=record_data)

@app.route('/pdf-viewer')
def pdf_viewer():
    """PDF在线预览页面"""
    return render_template('pdf_viewer.html')

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "文件不存在", 404

def check_admin_session():
    """检查管理员会话是否有效"""
    if 'admin_logged_in' not in session:
        return False
    
    if 'login_time' not in session:
        return False
    
    login_time = datetime.fromisoformat(session['login_time'])
    if datetime.now() - login_time > timedelta(hours=1):
        session.clear()
        return False
    
    return True

# 管理员API接口
@app.route('/api/admin/records')
def get_all_records():
    """获取所有记录（管理员功能）"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    records = []
    data_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.json') and f not in ['admin.json', 'dropdown_config.json', 'app_config.json']]
    
    for file in data_files:
        try:
            with open(os.path.join(DATA_FOLDER, file), 'r', encoding='utf-8') as f:
                record = json.load(f)
                records.append(record)
        except Exception as e:
            continue
    
    # 按创建时间排序
    records.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify({'success': True, 'records': records})

@app.route('/api/admin/record/<record_id>', methods=['PUT'])
def update_record(record_id):
    """更新记录（管理员功能）"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    record_file = os.path.join(DATA_FOLDER, f"{record_id}.json")
    if not os.path.exists(record_file):
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        # 读取原记录
        with open(record_file, 'r', encoding='utf-8') as f:
            old_record = json.load(f)
        
        # 获取新数据
        new_data = request.get_json()
        
        # 验证必填字段
        required_fields = ['specimen_number', 'material', 'reflector_type', 'storage_area']
        if not all(field in new_data for field in required_fields):
            return jsonify({'success': False, 'message': '缺少必填字段'})
        
        # 获取并清理输入数据
        specimen_number = str(new_data['specimen_number']).strip()
        material = str(new_data['material']).strip()
        reflector_type = str(new_data['reflector_type']).strip()
        storage_area = str(new_data['storage_area']).strip()
        
        # 验证试块编号格式
        is_valid, error_msg = validate_specimen_number(specimen_number)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg})
        
        # 清理用户输入
        specimen_number = sanitize_input(specimen_number)
        material = sanitize_input(material)
        reflector_type = sanitize_input(reflector_type)
        storage_area = sanitize_input(storage_area)
        
        # 更新记录
        old_record.update({
            'specimen_number': specimen_number,
            'material': material,
            'reflector_type': reflector_type,
            'storage_area': storage_area,
            'updated_at': datetime.now().isoformat()
        })
        
        # 保存更新后的记录
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(old_record, f, ensure_ascii=False, indent=2)
        
        # 记录操作日志
        log_admin_operation(
            'update_record',
            request.remote_addr,
            {'record_id': record_id, 'old_data': {k: v for k, v in old_record.items() if k not in ['specimen_number', 'material', 'reflector_type', 'storage_area']}},
            {'record_id': record_id, 'new_data': old_record}
        )
        
        return jsonify({'success': True, 'message': '记录更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

@app.route('/api/admin/record/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    """删除记录（管理员功能）"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    record_file = os.path.join(DATA_FOLDER, f"{record_id}.json")
    qr_file = os.path.join(QRCODE_FOLDER, f"{record_id}.png")
    
    if not os.path.exists(record_file):
        return jsonify({'success': False, 'message': '记录不存在'})
    
    try:
        # 读取要删除的记录用于日志
        with open(record_file, 'r', encoding='utf-8') as f:
            record_data = json.load(f)
        
        # 删除关联的PDF文件
        if record_data.get('certificate_file'):
            pdf_file = os.path.join(UPLOAD_FOLDER, record_data['certificate_file'])
            if os.path.exists(pdf_file):
                os.remove(pdf_file)
        
        # 删除记录文件
        os.remove(record_file)
        
        # 删除二维码文件
        if os.path.exists(qr_file):
            os.remove(qr_file)
        
        # 记录操作日志
        log_admin_operation(
            'delete_record',
            request.remote_addr,
            {'record_id': record_id, 'record_data': record_data},
            {'record_id': record_id, 'deleted': True}
        )
        
        return jsonify({'success': True, 'message': '记录删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

@app.route('/api/admin/config', methods=['PUT'])
def update_config():
    """更新下拉列表配置（管理员功能）"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    try:
        # 读取原配置
        with open(DROPDOWN_CONFIG_FILE, 'r', encoding='utf-8') as f:
            old_config = json.load(f)
        
        # 获取新配置
        new_config = request.get_json()
        
        # 验证配置格式
        required_keys = ['materials', 'reflector_types', 'storage_areas']
        for key in required_keys:
            if key not in new_config or not isinstance(new_config[key], list):
                return jsonify({'success': False, 'message': f'配置格式错误: {key}'})
        
        # 清理和验证配置项
        cleaned_config = {}
        for key in required_keys:
            cleaned_items = []
            for item in new_config[key]:
                if isinstance(item, str):
                    # 清理和验证每个配置项
                    cleaned_item = sanitize_input(item.strip())
                    if cleaned_item and len(cleaned_item) <= 100:  # 限制长度
                        cleaned_items.append(cleaned_item)
            
            # 去重并限制数量
            cleaned_items = list(dict.fromkeys(cleaned_items))[:50]  # 最多50个选项
            cleaned_config[key] = cleaned_items
        
        # 验证至少有一个选项
        for key in required_keys:
            if not cleaned_config[key]:
                return jsonify({'success': False, 'message': f'{key} 至少需要一个有效选项'})
        
        # 保存新配置
        with open(DROPDOWN_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned_config, f, ensure_ascii=False, indent=2)
        
        # 记录操作日志
        log_admin_operation(
            'update_config',
            request.remote_addr,
            old_config,
            cleaned_config
        )
        
        return jsonify({'success': True, 'message': '配置更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})

@app.route('/api/admin/password', methods=['PUT'])
def change_password():
    """修改管理员密码"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        # 验证密码长度和复杂性
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度至少6位'})
        
        if len(new_password) > 50:
            return jsonify({'success': False, 'message': '新密码长度不能超过50位'})
        
        # 检查密码是否包含危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', '\\', '/']
        if any(char in new_password for char in dangerous_chars):
            return jsonify({'success': False, 'message': '密码不能包含特殊字符: < > " \' & \\ /'})
        
        # 验证当前密码
        with open(ADMIN_PASSWORD_FILE, 'r', encoding='utf-8') as f:
            admin_data = json.load(f)
        
        current_hash = hashlib.md5(current_password.encode()).hexdigest()
        if current_hash != admin_data['password']:
            return jsonify({'success': False, 'message': '当前密码错误'})
        
        # 更新密码
        new_hash = hashlib.md5(new_password.encode()).hexdigest()
        admin_data['password'] = new_hash
        
        with open(ADMIN_PASSWORD_FILE, 'w', encoding='utf-8') as f:
            json.dump(admin_data, f)
        
        # 记录操作日志
        log_admin_operation(
            'change_password',
            request.remote_addr,
            {'action': 'password_change_request'},
            {'action': 'password_changed'}
        )
        
        return jsonify({'success': True, 'message': '密码修改成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'修改失败: {str(e)}'})

@app.route('/api/admin/logs')
def get_admin_logs():
    """获取管理员操作日志"""
    if not check_admin_session():
        return jsonify({'success': False, 'message': '未授权访问'}), 401
    
    log_file = os.path.join(LOG_FOLDER, 'admin_operations.json')
    if not os.path.exists(log_file):
        return jsonify({'success': True, 'logs': []})
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        # 按时间倒序排列
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取日志失败: {str(e)}'})



if __name__ == '__main__':
    # 启动时更新HTML模板中的appConfig配置
    update_html_templates_config()
    
    # 从配置文件获取服务器配置
    server_config = get_server_config()
    
    print(f'服务器启动配置:')
    print(f'  HOST: {server_config["host"]}')
    print(f'  PORT: {server_config["port"]}')
    print(f'  DEBUG: {server_config["debug"]}')
    print(f'  BASE_URL: {BASE_URL}')
    
    app.run(
        debug=server_config['debug'],
        host=server_config['host'],
        port=server_config['port']
    )