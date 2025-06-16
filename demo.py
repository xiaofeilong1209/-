from flask import Flask, request, jsonify
from flask_cors import CORS
from gevent import pywsgi
import pymysql

app = Flask(__name__)

# 配置CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 数据库连接
try:
    db = pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='成绩管理系统',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    print("数据库连接成功!")
except pymysql.Error as e:
    print(f"数据库连接失败: {e}")
    exit(1)

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "running", 
        "message": "Flask服务器正常运行",
        "endpoints": {
            "/login": "POST - 用户登录",
            "/get_all_students": "POST - 获取所有学生",
            "/delete_student": "POST - 删除学生",
            "/add_score": "POST - 添加成绩"
        }
    })

@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({"status": "preflight"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"info": "false1", "message": "请求数据不能为空"}), 400
    
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"info": "false1", "message": "用户名和密码不能为空"}), 400
    
    try:
        with db.cursor() as cur:
            cur.execute("SELECT Akey FROM admin_account WHERE Ano = %s", (username,))
            admin_result = cur.fetchone()
            
            if not admin_result:
                return jsonify({"info": "false1", "message": "用户不存在"}), 401

            if admin_result['Akey'] != password:
                return jsonify({"info": "false2", "message": "密码错误"}), 401
            
            return jsonify({
                "info": "true", 
                "au": "true",
                "message": "登录成功"
            })
            
    except Exception as e:
        print(f"登录错误: {str(e)}")
        return jsonify({"info": "error", "message": "服务器内部错误"}), 500

@app.route("/get_all_students", methods=["POST", "OPTIONS"])
def get_all_students():
    if request.method == "OPTIONS":
        return jsonify({"status": "preflight"}), 200
    
    try:
        with db.cursor() as cur:
            cur.execute("SELECT Sno, Sname, Ssum FROM students ORDER BY Sno ASC") 
            rows = cur.fetchall()
            return jsonify({
                "success": True,
                "tableData": rows,
                "message": "学生数据获取成功"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "tableData": [],
            "message": f"获取学生数据失败: {str(e)}"
        })
    
@app.route("/search_student", methods=["POST", "OPTIONS"])
def search_student():
    if request.method == "OPTIONS":
        return jsonify({"status": "preflight"}), 200
    
    data = request.get_json()
    print("收到搜索请求，数据:", data)  # 调试输出
    
    sno = data.get("Sno", "").strip()
    print("搜索学号:", sno)  # 调试输出
    
    try:
        with db.cursor() as cur:
            cur.execute("SELECT Sno, Sname, Ssum FROM students WHERE Sno = %s", (sno,))
            row = cur.fetchone()
            print("查询结果:", row)  # 调试输出
            
            if not row:
                print("未找到学生记录")  # 调试输出
                return jsonify({
                    "success": False,
                    "tableData": [],
                    "message": "未找到该学号的学生"
                }), 404
                
            print("找到学生:", row)  # 调试输出
            return jsonify({
                "success": True,
                "tableData": [row],
                "message": "找到学生信息"
            })

    except Exception as e:
        print("查询出错:", str(e))  # 调试输出
        return jsonify({
            "success": False,
            "tableData": [],
            "message": f"查询失败: {str(e)}"
        }), 500

@app.route("/delete_student", methods=["POST", "OPTIONS"])
def delete_student():
    if request.method == "OPTIONS":
        return jsonify({"status": "preflight"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据不能为空"}), 400
    
    sno = data.get("Sno", "").strip()
    if not sno:
        return jsonify({"success": False, "message": "学号不能为空"}), 400
    
    try:
        with db.cursor() as cur:
            # 检查学生是否存在
            cur.execute("SELECT 1 FROM students WHERE Sno = %s", (sno,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "该学号不存在"}), 404

            # 删除学生
            cur.execute("DELETE FROM students WHERE Sno = %s", (sno,))
            return jsonify({
                "success": True,
                "message": "学生删除成功"
            })
            
    except Exception as e:
        print(f"删除学生错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"删除失败: {str(e)}"
        }), 500

@app.route("/add_score", methods=["POST", "OPTIONS"])
def add_score():
    if request.method == "OPTIONS":
        return jsonify({"status": "preflight"}), 200
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据不能为空"}), 400
    
    cno = data.get("Cno", "").strip()
    sno = data.get("Sno", "").strip()
    score = data.get("Score", "").strip()
    dates = data.get("Dates", "").strip()
    tname = data.get("Tname", "").strip()
    
    if not all([cno, sno, score, dates]):
        return jsonify({"success": False, "message": "必填字段不能为空"}), 400
    
    try:
        with db.cursor() as cur:
            # 检查学生是否存在
            cur.execute("SELECT 1 FROM students WHERE Sno = %s", (sno,))
            if not cur.fetchone():
                return jsonify({"success": False, "message": "该学号不存在"}), 404

            # 添加成绩
            cur.execute("""
                INSERT INTO Reports (Cno, Sno, Score, Dates, Tname)
                VALUES (%s, %s, %s, %s, %s)
            """, (cno, sno, score, dates, tname))
            
            return jsonify({
                "success": True,
                "message": "成绩添加成功"
            })
            
    except Exception as e:
        print(f"添加成绩错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"添加成绩失败: {str(e)}"
        }), 500

if __name__ == "__main__":
    print("🚀 服务器正常运行，访问地址: http://127.0.0.1:5000")
    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app)
    server.serve_forever()