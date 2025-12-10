from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, hashlib, os
import pandas
from io import BytesIO  # 【新增】内存流
import re  # 【新增】正则解析联系方式

app = Flask(__name__)
CORS(app)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db.sqlite')
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    with sqlite3.connect(DB) as conn:
        # 【修改】原有users表保持不变
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # 【修改】contacts表：新增is_favorite字段
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_favorite INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 【新增】联系方式表（一对多）
        conn.execute('''
            CREATE TABLE IF NOT EXISTS contact_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('phone', 'email', 'social', 'address')),
                value TEXT NOT NULL,
                label TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
            )
        ''')
    print("数据库初始化完成 (含收藏与多联系方式支持)")

def hash_pwd(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- 静态资源 ----------
@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'contacts.html')

# ---------- 用户 ----------
@app.post('/register')
def register():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return jsonify(error='Username and password are required'), 400
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, hash_pwd(password)))
        return jsonify(msg='Registration successful'), 201
    except sqlite3.IntegrityError:
        return jsonify(error='Username already exists'), 400
    except Exception as e:
        return jsonify(error=f'Registration failed: {str(e)}'), 500

@app.post('/login')
def login():
    data = request.json
    username, password = data.get('username'), data.get('password')
    if not username or not password:
        return jsonify(error='Username and password are required'), 400
    with sqlite3.connect(DB) as conn:
        user = conn.execute(
            'SELECT id FROM users WHERE username=? AND password=?',
            (username, hash_pwd(password))
        ).fetchone()
    if user:
        return jsonify(user_id=user[0]), 200
    else:
        return jsonify(error='Invalid username or password'), 401

# ---------- 联系人 ----------
# 【修改】添加联系人（支持多种联系方式）
@app.post('/contacts')
def add_contact():
    data = request.json
    user_id, name = data.get('user_id'), data.get('name')
    methods = data.get('methods', [])  # 【新增】联系方式数组
    if not all([user_id, name]):
        return jsonify(error='User ID and name are required'), 400
    
    try:
        with sqlite3.connect(DB) as conn:
            # 插入联系人基础信息
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO contacts (user_id, name) VALUES (?, ?)',
                (user_id, name))
            contact_id = cur.lastrowid
            
            # 【新增】插入联系方式
            for m in methods:
                if m.get('value'):  # 仅处理非空值
                    cur.execute(
                        'INSERT INTO contact_methods (contact_id, type, value, label) VALUES (?, ?, ?, ?)',
                        (contact_id, m['type'], m['value'], m.get('label', '')))
        return jsonify(msg='Contact added successfully', id=contact_id), 201
    except Exception as e:
        return jsonify(error=f'Failed to add contact: {str(e)}'), 500

# 【修改】获取联系人（包含嵌套的联系方式）
@app.get('/contacts/<int:user_id>')
def get_contacts(user_id):
    try:
        with sqlite3.connect(DB) as conn:
            # 获取所有联系人
            contact_rows = conn.execute(
                'SELECT id, name, is_favorite FROM contacts WHERE user_id=?',
                (user_id,)
            ).fetchall()
            
            contacts = []
            for r in contact_rows:
                # 获取该联系人的所有联系方式
                method_rows = conn.execute(
                    'SELECT id, type, value, label FROM contact_methods WHERE contact_id=?',
                    (r[0],)
                ).fetchall()
                methods = [{'id': mr[0], 'type': mr[1], 'value': mr[2], 'label': mr[3]} 
                          for mr in method_rows]
                
                contacts.append({
                    'id': r[0],
                    'name': r[1],
                    'is_favorite': bool(r[2]),
                    'methods': methods
                })
        return jsonify(contacts), 200
    except Exception as e:
        return jsonify(error=f'Failed to get contacts: {str(e)}'), 500

# 【新增】切换收藏状态
@app.post('/contacts/<int:contact_id>/favorite')
def toggle_favorite(contact_id):
    try:
        with sqlite3.connect(DB) as conn:
            # 切换is_favorite状态
            cur = conn.execute(
                'UPDATE contacts SET is_favorite = CASE WHEN is_favorite=1 THEN 0 ELSE 1 END WHERE id=?',
                (contact_id,))
            if cur.rowcount == 0:
                return jsonify(error='Contact not found'), 404
        return jsonify(msg='Favorite status updated'), 200
    except Exception as e:
        return jsonify(error=f'Failed to update favorite: {str(e)}'), 500

# 【修改】更新联系人（支持更新联系方式）
@app.put('/contacts/<int:contact_id>')
def update_contact(contact_id):
    data = request.json
    name, methods = data.get('name'), data.get('methods', [])
    if not name:
        return jsonify(error='Name is required'), 400
    try:
        with sqlite3.connect(DB) as conn:
            # 更新基础信息
            cur = conn.execute(
                'UPDATE contacts SET name=? WHERE id=?',
                (name, contact_id))
            if cur.rowcount == 0:
                return jsonify(error='Contact not found'), 404
            
            # 【新增】删除旧的联系方式，插入新的
            conn.execute('DELETE FROM contact_methods WHERE contact_id=?', (contact_id,))
            for m in methods:
                if m.get('value'):
                    conn.execute(
                        'INSERT INTO contact_methods (contact_id, type, value, label) VALUES (?, ?, ?, ?)',
                        (contact_id, m['type'], m['value'], m.get('label', '')))
        return jsonify(msg='Contact updated successfully'), 200
    except Exception as e:
        return jsonify(error=f'Failed to update contact: {str(e)}'), 500

@app.delete('/contacts/<int:contact_id>')
def delete_contact(contact_id):
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute('DELETE FROM contacts WHERE id=?', (contact_id,))
        return jsonify(msg='Contact deleted successfully'), 200
    except Exception as e:
        return jsonify(error=f'Failed to delete contact: {str(e)}'), 500

@app.get('/contacts/count/<int:user_id>')
def count_contacts(user_id):
    try:
        with sqlite3.connect(DB) as conn:
            total = conn.execute('SELECT COUNT(*) FROM contacts WHERE user_id=?', (user_id,)).fetchone()[0]
        return jsonify(total=total), 200
    except Exception as e:
        return jsonify(error=f'Failed to count contacts: {str(e)}'), 500

# 【新增】Excel导出
@app.route('/contacts/export/<int:user_id>', methods=['GET'])  # 修改这行
def export_contacts(user_id):
    try:
        with sqlite3.connect(DB) as conn:
            rows = conn.execute('''
                SELECT c.id, c.name, cm.type, cm.value, cm.label, c.is_favorite
                FROM contacts c
                LEFT JOIN contact_methods cm ON c.id = cm.contact_id
                WHERE c.user_id=?
                ORDER BY c.id, cm.type
            ''', (user_id,)).fetchall()
            
            data = {}
            for r in rows:
                cid = r[0]
                if cid not in data:
                    data[cid] = {'姓名': r[1], '收藏': '是' if r[5] else '否', 
                                 '电话': '', '邮箱': '', '社交媒体': '', '地址': ''}
                if r[2] and r[3]:
                    if r[2] == 'phone':
                        data[cid]['电话'] += (', ' if data[cid]['电话'] else '') + r[3]
                    elif r[2] == 'email':
                        data[cid]['邮箱'] += (', ' if data[cid]['邮箱'] else '') + r[3]
                    elif r[2] == 'social':
                        data[cid]['社交媒体'] += (', ' if data[cid]['社交媒体'] else '') + r[3]
                    elif r[2] == 'address':
                        data[cid]['地址'] += (', ' if data[cid]['地址'] else '') + r[3]
            
            df = pd.DataFrame.from_dict(data, orient='index')
            df = df[['姓名', '收藏', '电话', '邮箱', '社交媒体', '地址']]
            
            # 【修改】使用 send_file 直接发送内存数据
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Contacts', index=False)
            
            output.seek(0)
            from flask import send_file  # 添加这行
            
            return send_file(
                output,
                as_attachment=True,
                download_name='contacts.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
    except Exception as e:
        return jsonify(error=f'Export failed: {str(e)}'), 500

# 【新增】Excel导入
@app.post('/contacts/import/<int:user_id>')
def import_contacts(user_id):
    if 'file' not in request.files:
        return jsonify(error='No file uploaded'), 400
    
    file = request.files['file']
    if not file.filename.endswith(('.xls', '.xlsx')):
        return jsonify(error='Please upload Excel file'), 400
    
    try:
        # 读取Excel
        df = pd.read_excel(file)
        if '姓名' not in df.columns:
            return jsonify(error='Excel must contain "姓名" column'), 400
        
        with sqlite3.connect(DB) as conn:
            cur = conn.cursor()
            for _, row in df.iterrows():
                # 插入联系人
                cur.execute(
                    'INSERT INTO contacts (user_id, name, is_favorite) VALUES (?, ?, ?)',
                    (user_id, row['姓名'], 1 if row.get('收藏') == '是' else 0))
                contact_id = cur.lastrowid
                
                # 解析各列并插入联系方式
                def add_methods(col_name, m_type):
                    if col_name in df.columns and pd.notna(row[col_name]):
                        values = str(row[col_name]).split(',')
                        for val in values:
                            val = val.strip()
                            if val:
                                cur.execute(
                                    'INSERT INTO contact_methods (contact_id, type, value) VALUES (?, ?, ?)',
                                    (contact_id, m_type, val))
                
                add_methods('电话', 'phone')
                add_methods('邮箱', 'email')
                add_methods('社交媒体', 'social')
                add_methods('地址', 'address')
        
        return jsonify(msg=f'Successfully imported {len(df)} contacts'), 200
    except Exception as e:
        return jsonify(error=f'Import failed: {str(e)}'), 500

# ---------- 启动 ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5500)