from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trh_cyberpunk_secret' 
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- KHỞI TẠO ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- CẤU HÌNH ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1457372740381179994/dPNAMwShbts0IYmxQA-C8y7bCSm2BwAI2Yc1tqfSWYbjztE5zDehFRctCZGDaAIW7SSk"
ADMIN_SECRET = "TRH_CONFIRM_2026"

# --- MODEL ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default="Member")
    is_banned = db.Column(db.Boolean, default=False)

order_states = {}

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- CSS CYBERPUNK NEON ---
CYBER_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');
    
    :root { 
        --primary: #ff0055; 
        --accent: #00f2ff; 
        --gold: #ffd700;
        --bg: #050505; 
        --glass: rgba(10, 10, 10, 0.6); 
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    body { 
        background-color: var(--bg); color: white; font-family: 'Rajdhani', sans-serif; margin: 0; 
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(255, 0, 85, 0.15), transparent 25%), 
            radial-gradient(circle at 85% 30%, rgba(0, 242, 255, 0.15), transparent 25%);
        min-height: 100vh;
        overflow-x: hidden;
    }

    /* Scrollbar đẹp */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }

    /* Glass Panel */
    .glass-panel {
        background: var(--glass); 
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border); 
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }

    /* Navbar */
    .navbar { 
        display: flex; justify-content: space-between; align-items: center; padding: 15px 40px; 
        background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05);
        position: sticky; top: 0; z-index: 100;
    }
    .logo { 
        font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 900; color: white;
        text-shadow: 0 0 10px var(--primary);
    }
    
    /* Buttons */
    .btn {
        background: transparent; border: 1px solid var(--primary); color: var(--primary);
        padding: 10px 25px; font-weight: bold; border-radius: 5px; cursor: pointer; 
        transition: 0.3s; text-decoration: none; font-size: 1rem; display: inline-block;
        font-family: 'Orbitron', sans-serif; letter-spacing: 1px;
    }
    .btn:hover { 
        background: var(--primary); color: white; 
        box-shadow: 0 0 20px var(--primary), 0 0 40px var(--primary);
        border-color: transparent;
    }
    
    .btn-buy {
        background: linear-gradient(90deg, var(--primary), #ff4d88); border: none; color: white;
        width: 100%; padding: 12px; margin-top: 15px;
    }
    .btn-buy:hover { transform: scale(1.02); }

    /* Product Cards - Hiệu ứng Glow mạnh */
    .product-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.05);
        border-radius: 15px; overflow: hidden; transition: all 0.4s ease;
        position: relative;
    }
    
    /* Khi di chuột vào: SÁNG RỰC */
    .product-card:hover {
        transform: translateY(-10px);
        background: rgba(255, 255, 255, 0.07);
        border-color: var(--accent);
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.3), inset 0 0 20px rgba(0, 242, 255, 0.1);
    }
    
    .card-icon { 
        height: 180px; display: flex; align-items: center; justify-content: center; 
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(0,0,0,0) 70%);
    }
    .card-icon i { font-size: 80px; color: white; transition: 0.4s; filter: drop-shadow(0 0 10px rgba(255,255,255,0.5)); }
    .product-card:hover .card-icon i { transform: scale(1.1); filter: drop-shadow(0 0 20px var(--accent)); color: var(--accent); }

    /* Badges */
    .badge { padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; font-family: 'Orbitron'; margin-right: 15px; }
    .role-Dev { background: #ff0000; color: white; box-shadow: 0 0 15px red; }
    .role-VIP { background: gold; color: black; box-shadow: 0 0 15px gold; }
    .role-Member { background: #00f2ff; color: black; box-shadow: 0 0 10px #00f2ff; }

    /* Table Admin */
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th { text-align: left; padding: 15px; color: var(--primary); border-bottom: 2px solid rgba(255,255,255,0.1); text-transform: uppercase; letter-spacing: 2px; }
    td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); color: #ddd; }
    tr:hover { background: rgba(255,255,255,0.05); }

    /* Inputs */
    input { 
        width: 100%; padding: 15px; margin: 10px 0; background: rgba(0,0,0,0.5); border: 1px solid #333; 
        color: white; border-radius: 5px; font-family: 'Rajdhani'; font-size: 1.1rem; outline: none; transition: 0.3s; box-sizing: border-box;
    }
    input:focus { border-color: var(--accent); box-shadow: 0 0 15px rgba(0, 242, 255, 0.3); }
</style>
"""

# --- HOME ROUTE ---
@app.route('/')
@login_required
def home():
    return render_template_string(CYBER_CSS + """
    <html>
        <head>
            <title>ShopTrhCE | Cyber Store</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </head>
        <body>
            <div class="navbar">
                <div class="logo"><i class="fas fa-robot"></i> ShopTrhCE</div>
                <div style="display:flex; align-items:center">
                    <span class="badge role-{{ current_user.role }}">{{ current_user.role }}</span>
                    <span style="font-weight:bold; margin-right:20px; font-size:1.2rem; letter-spacing:1px;">{{ current_user.username }}</span>
                    
                    {% if current_user.role == 'Dev' %}
                        <a href="/admin/users" class="btn" style="border-color:#ff0000; color:#ff0000; margin-right:15px; padding: 5px 15px; font-size:0.8rem">
                            <i class="fas fa-users-cog"></i> ADMIN
                        </a>
                    {% endif %}
                    
                    <a href="/logout" style="color:#aaa; text-decoration:none;"><i class="fas fa-sign-out-alt"></i></a>
                </div>
            </div>

            <div style="max-width: 1100px; margin: 60px auto; padding: 20px;">
                <h1 style="text-align:center; font-family:'Orbitron'; font-size: 3rem; margin-bottom: 50px; text-shadow: 0 0 20px var(--primary);">
                    STORE <span style="color:var(--accent)">ACCESS</span>
                </h1>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 40px;">
                    
                    <div class="product-card">
                        <div class="card-icon">
                            <i class="fas fa-crosshairs"></i>
                        </div>
                        <div style="padding: 25px;">
                            <h2 style="margin:0; font-family:'Orbitron'">AimAssist Custom</h2>
                            <p style="color:#aaa; margin: 15px 0;">Script hỗ trợ ngắm bắn siêu chuẩn. Tích hợp Bypass Anti-Cheat.</p>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                                <span style="font-size:1.8rem; font-weight:bold; color:var(--accent); text-shadow: 0 0 10px var(--accent);">2.000đ</span>
                            </div>
                            <button onclick="openDeposit(2000, 'AimAssist Custom')" class="btn btn-buy">MUA NGAY</button>
                        </div>
                    </div>

                    <div class="product-card" style="border-color: rgba(255, 215, 0, 0.2);">
                        <div class="card-icon">
                            <i class="fas fa-bug" style="color:gold;"></i>
                        </div>
                        <div style="padding: 25px;">
                            <h2 style="margin:0; font-family:'Orbitron'; color:gold;">Bug Huy Hiệu</h2>
                            <p style="color:#aaa; margin: 15px 0;">Tool bug full bộ sưu tập huy hiệu sự kiện mới nhất.</p>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                                <span style="font-size:1.8rem; font-weight:bold; color:gold; text-shadow: 0 0 10px gold;">5.000đ</span>
                            </div>
                            <button onclick="openDeposit(5000, 'Bug Huy Hiệu')" class="btn btn-buy" style="background: linear-gradient(90deg, gold, orange); color:black;">MUA NGAY</button>
                        </div>
                    </div>

                </div>
            </div>

            <div id="paymentModal" style="display:none; position:fixed; z-index:999; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.95); backdrop-filter:blur(8px);">
                <div class="glass-panel" style="max-width:380px; margin: 80px auto; padding:40px; text-align:center; position:relative; border: 1px solid var(--accent); box-shadow: 0 0 50px rgba(0, 242, 255, 0.2);">
                    <span onclick="closeModal()" style="position:absolute; top:20px; right:25px; font-size:30px; cursor:pointer; color:white;">&times;</span>
                    
                    <h2 style="color:var(--accent); margin-top:0; font-family:'Orbitron'; letter-spacing:2px;">THANH TOÁN</h2>
                    <p id="productName" style="color:white; font-weight:bold; font-size:1.2rem;">...</p>
                    
                    <div style="position:relative; display:inline-block; margin: 20px 0;">
                        <div style="position:absolute; inset:-5px; background:linear-gradient(45deg, var(--primary), var(--accent)); filter:blur(10px); z-index:-1;"></div>
                        <img id="qrImage" src="" style="width:200px; border-radius:10px; display:block;">
                    </div>

                    <div style="background:rgba(0,0,0,0.6); padding:15px; border-radius:10px; margin-bottom:20px; border:1px dashed #555;">
                        <p style="margin:0; font-size:0.9rem; color:#aaa;">Nội dung chuyển khoản (Bắt buộc):</p>
                        <p id="payInfo" style="margin:5px 0 0; font-size:1.5rem; font-weight:bold; color:var(--gold); letter-spacing:2px; font-family:'Orbitron'">...</p>
                    </div>

                    <button id="checkBtn" onclick="sendNotification()" class="btn btn-buy" style="background:var(--accent); color:black; font-family:'Orbitron'">ĐÃ CHUYỂN KHOẢN</button>
                    <p id="stMsg" style="margin-top:20px; font-size:1rem; color:#888; font-weight:bold;"></p>
                </div>
            </div>

            <script>
                const modal = document.getElementById("paymentModal");
                let currentOrderId = "", currentProduct = "", checkInterval = null;

                function openDeposit(amount, product) {
                    currentProduct = product;
                    currentOrderId = 'TRH' + Math.floor(10000 + Math.random() * 90000);
                    document.getElementById("qrImage").src = `https://img.vietqr.io/image/970426-80000018552-compact.png?amount=${amount}&addInfo=${currentOrderId}&accountName=DO%20THI%20TRUC%20QUYNH`;
                    document.getElementById("payInfo").innerText = currentOrderId;
                    document.getElementById("productName").innerText = product;
                    document.getElementById("stMsg").innerText = "";
                    document.getElementById("checkBtn").disabled = false;
                    document.getElementById("checkBtn").innerText = "ĐÃ CHUYỂN KHOẢN";
                    if(checkInterval) clearInterval(checkInterval);
                    modal.style.display = "block";
                }

                function closeModal() { modal.style.display = "none"; if(checkInterval) clearInterval(checkInterval); }

                async function sendNotification() {
                    const btn = document.getElementById("checkBtn");
                    const st = document.getElementById("stMsg");
                    btn.disabled = true;
                    btn.innerText = "ĐANG XỬ LÝ...";
                    st.innerText = "Đang gửi tín hiệu lên hệ thống...";
                    
                    const res = await fetch('/notify', {
                        method: 'POST', headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ 
                            orderId: currentOrderId, 
                            amount: document.getElementById("payAmount") ? document.getElementById("payAmount").innerText : "Checking...", 
                            product: currentProduct 
                        })
                    });
                    
                    if(res.ok) {
                        st.innerHTML = "<span style='color:var(--gold)'><i class='fas fa-spinner fa-spin'></i> Đang chờ Admin duyệt...</span>";
                        startPolling();
                    }
                }

                function startPolling() {
                    const st = document.getElementById("stMsg");
                    checkInterval = setInterval(async () => {
                        const res = await fetch('/check-status/' + currentOrderId);
                        const data = await res.json();
                        if (data.status === 'approved') {
                            clearInterval(checkInterval);
                            st.innerHTML = "<span style='color:#00ff00; font-size:1.2rem; text-shadow:0 0 10px #00ff00'>✅ GIAO DỊCH THÀNH CÔNG!</span><br>Vui lòng kiểm tra tin nhắn.";
                        } else if (data.status === 'rejected') {
                            clearInterval(checkInterval);
                            st.innerHTML = "<span style='color:red'>❌ ĐƠN BỊ TỪ CHỐI</span>";
                        }
                    }, 3000);
                }
            </script>
        </body>
    </html>
    """)

# --- ADMIN PANEL ---
@app.route('/admin/users')
@login_required
def user_list():
    if current_user.role != 'Dev': return "<h1>KHÔNG CÓ QUYỀN!</h1>", 403
    return render_template_string(CYBER_CSS + """
    <html>
        <body>
            <div style="max-width: 1000px; margin: 50px auto;">
                <div class="glass-panel" style="padding: 40px; border-color:var(--primary);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
                        <h1 style="margin:0; color:var(--primary); font-family:'Orbitron'; text-shadow:0 0 10px red;">ADMIN COMMAND CENTER</h1>
                        <a href="/" class="btn" style="border-color:white; color:white;">⬅ BACK</a>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>USER</th>
                                <th>ROLE</th>
                                <th>STATUS</th>
                                <th style="text-align:right">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for u in users %}
                            <tr>
                                <td style="color:#666; font-weight:bold;">#{{ u.id }}</td>
                                <td style="font-weight:bold; font-size:1.1rem; color:white;">{{ u.username }}</td>
                                <td><span class="badge role-{{ u.role }}">{{ u.role }}</span></td>
                                <td>
                                    {% if u.is_banned %}
                                        <span style="color:red; font-weight:bold; text-shadow:0 0 5px red;">🚫 BANNED</span>
                                    {% else %}
                                        <span style="color:#00ff00; font-weight:bold;">ACTIVE</span>
                                    {% endif %}
                                </td>
                                <td style="text-align:right;">
                                    {% if u.role != 'Dev' %}
                                        <div style="display:flex; gap:10px; justify-content:flex-end;">
                                            {% if u.is_banned %}
                                                <a href="/admin/unban/{{ u.id }}" class="btn" style="border-color:lime; color:lime; padding:5px 10px; font-size:0.7rem">UNBAN</a>
                                            {% else %}
                                                <a href="/admin/ban/{{ u.id }}" class="btn" style="border-color:red; color:red; padding:5px 10px; font-size:0.7rem">BAN</a>
                                            {% endif %}

                                            {% if u.role == 'VIP' %}
                                                <a href="/admin/demote/{{ u.id }}" class="btn" style="border-color:orange; color:orange; padding:5px 10px; font-size:0.7rem">DEMOTE</a>
                                            {% elif u.role == 'Member' %}
                                                <a href="/admin/promote/{{ u.id }}" class="btn" style="border-color:gold; color:gold; padding:5px 10px; font-size:0.7rem">SET VIP</a>
                                            {% endif %}
                                        </div>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
    </html>
    """, users=User.query.all())

# --- LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            if user.is_banned: return "<body style='background:black; color:red; text-align:center; padding-top:50px; font-family:sans-serif;'><h1>⛔ ACCESS DENIED</h1><p>Tài khoản này đã bị trục xuất!</p></body>"
            login_user(user)
            return redirect('/')
        return redirect('/login')
        
    return render_template_string(CYBER_CSS + """
    <html><body>
        <div style="display:flex; justify-content:center; align-items:center; height:100vh;">
            <div class="glass-panel" style="width:100%; max-width:400px; padding:50px; text-align:center; border: 1px solid var(--primary); box-shadow: 0 0 50px rgba(255, 0, 85, 0.2);">
                <h1 style="color:var(--primary); margin-bottom:40px; font-family:'Orbitron'; letter-spacing:4px; text-shadow:0 0 10px var(--primary);">SYSTEM LOGIN</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="USERNAME" required>
                    <input type="password" name="password" placeholder="PASSWORD" required>
                    <button type="submit" class="btn btn-buy" style="margin-top:30px; font-family:'Orbitron'">ACCESS</button>
                </form>
                <p style="margin-top:30px; color:#888;">New user? <a href="/register" style="color:var(--accent); text-decoration:none; font-weight:bold;">Register Here</a></p>
            </div>
        </div>
    </body></html>
    """)

# --- REGISTER ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if User.query.filter_by(username=u).first(): return "User exists"
        r = "Dev" if u == "NgTrHai" and p == "emoemo123" else "Member"
        db.session.add(User(username=u, password=generate_password_hash(p), role=r))
        db.session.commit()
        return redirect('/login')
        
    return render_template_string(CYBER_CSS + """
    <html><body>
        <div style="display:flex; justify-content:center; align-items:center; height:100vh;">
            <div class="glass-panel" style="width:100%; max-width:400px; padding:50px; text-align:center; border: 1px solid var(--accent); box-shadow: 0 0 50px rgba(0, 242, 255, 0.2);">
                <h1 style="color:var(--accent); margin-bottom:40px; font-family:'Orbitron'; letter-spacing:4px; text-shadow:0 0 10px var(--accent);">NEW IDENTITY</h1>
                <form method="POST">
                    <input type="text" name="username" placeholder="USERNAME" required>
                    <input type="password" name="password" placeholder="PASSWORD" required>
                    <button type="submit" class="btn btn-buy" style="margin-top:30px; font-family:'Orbitron'; background:var(--accent); color:black;">INITIALIZE</button>
                </form>
                <p style="margin-top:30px; color:#888;">Already have acc? <a href="/login" style="color:var(--primary); text-decoration:none; font-weight:bold;">Login</a></p>
            </div>
        </div>
    </body></html>
    """)

# --- LOGIC FUNCTION ---
@app.route('/logout')
def logout(): logout_user(); return redirect('/login')

@app.route('/admin/ban/<int:id>')
@login_required
def ban(id):
    if current_user.role == 'Dev': db.session.get(User, id).is_banned = True; db.session.commit()
    return redirect('/admin/users')

@app.route('/admin/unban/<int:id>')
@login_required
def unban(id):
    if current_user.role == 'Dev': db.session.get(User, id).is_banned = False; db.session.commit()
    return redirect('/admin/users')

@app.route('/admin/promote/<int:id>')
@login_required
def promote(id):
    if current_user.role == 'Dev': db.session.get(User, id).role = "VIP"; db.session.commit()
    return redirect('/admin/users')

@app.route('/admin/demote/<int:id>')
@login_required
def demote(id):
    if current_user.role == 'Dev': db.session.get(User, id).role = "Member"; db.session.commit()
    return redirect('/admin/users')

@app.route('/check-status/<oid>')
def check(oid): return jsonify({"status": order_states.get(oid, 'pending')})

@app.post('/notify')
@login_required
def notify():
    data = request.json; oid = data['orderId']; order_states[oid] = 'pending'
    link = f"{request.host_url}admin/exec?oid={oid}&act=approve&sec={ADMIN_SECRET}&uid={current_user.id}"
    rej = f"{request.host_url}admin/exec?oid={oid}&act=reject&sec={ADMIN_SECRET}"
    requests.post(DISCORD_WEBHOOK_URL, json={"content": f"**ĐƠN MỚI!**\nUser: {current_user.username}\nMã: `{oid}`\n[✅ DUYỆT]({link}) | [❌ TỪ CHỐI]({rej})"})
    return "OK"

@app.route('/admin/exec')
def exec_order():
    if request.args.get('sec') != ADMIN_SECRET: return "Sai Secret"
    oid = request.args.get('oid'); act = request.args.get('act')
    if act == 'approve':
        order_states[oid] = 'approved'
        user = db.session.get(User, request.args.get('uid'))
        if user and user.role != 'Dev': user.role = "VIP"; db.session.commit()
        return "<h1 style='color:lime; background:black; padding:50px; text-align:center; font-family:sans-serif'>✅ XÁC NHẬN THÀNH CÔNG!</h1>"
    else:
        order_states[oid] = 'rejected'
        return "<h1 style='color:red; background:black; padding:50px; text-align:center; font-family:sans-serif'>❌ ĐÃ TỪ CHỐI!</h1>"

if __name__ == "__main__":
    with app.app_context():
        # db.drop_all() # Reset DB nếu cần
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
