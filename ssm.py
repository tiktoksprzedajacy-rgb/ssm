from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import requests
import random

app = Flask(__name__)
app.secret_key = "tajny_klucz_sesji_zabezpieczający"

# --- KONFIGURACJA ---
SMM_API_URL = "https://cheapsmmpanel.com/api/v2"
SMM_API_KEY = "********************************"  # Twój klucz SMM
SERVICE_ID = 230                                   # ID usługi YouTube Subscribers

NOWPAYMENTS_API_KEY = "W5WHHB7-33E43RY-PN5292F-6X5V18H" # Twój klucz NOWPayments

USERS_DB = {}   
ORDERS_DB = {}  
# --------------------

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>SMM Reseller Panel - YouTube Subs</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; max-width: 650px; margin: auto; }
        .card { background: #1e1e1e; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); margin-bottom: 20px; }
        input, button, select { width: 100%; padding: 12px; margin-top: 10px; border-radius: 5px; border: none; font-size: 16px; box-sizing: border-box; }
        input, select { background: #2a2a2a; color: #fff; }
        button { background: #00ffcc; color: #000; font-weight: bold; cursor: pointer; }
        button:hover { background: #00b38f; }
        .nav { display: flex; justify-content: space-between; background: #222; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; align-items: center; }
        .nav a { color: #00ffcc; text-decoration: none; font-weight: bold; margin-left: 15px; }
        .info { font-size: 14px; color: #aaa; margin-top: 10px; line-height: 1.5; }
        .stats { display: flex; justify-content: space-between; margin-top: 15px; background: #2a2a2a; padding: 12px; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #333; padding: 10px; text-align: left; font-size: 14px; }
        th { background: #252525; }
    </style>
</head>
<body>

    <div class="nav">
        <span>Witaj, <b>{{ username if username else 'Gość' }}</b></span>
        <div>
            {% if username %}
                <a href="/">Zamów</a>
                <a href="/tracker">Śledź zamówienia</a>
                <a href="/logout" style="color: #ff5555;">Wyloguj</a>
            {% else %}
                <a href="/login">Logowanie</a>
                <a href="/register">Rejestracja</a>
            {% endif %}
        </div>
    </div>

    {% if page == 'home' %}
    <div class="card">
        <h2>Zamów Subskrypcje YouTube</h2>
        <p class="info">Cena: $0.15 / 1000 sztuk (Min. 10 subskrypcji) | Płatność automatyczna Crypto</p>
        
        <label>Link do kanału YouTube:</label>
        <input type="text" id="channelUrl" placeholder="https://www.youtube.com/@TwojKanal">

        <label>Liczba subskrypcji (Min: 10, Max: 2000):</label>
        <input type="number" id="subsCount" min="10" max="2000" value="10" oninput="calculate()">

        <div class="stats">
            <span>Do zapłaty: <strong id="price" style="color: #00ffcc;">$0.0015</strong></span>
        </div>

        <button onclick="createPayment()">OPŁAĆ KRYPTOWALUTĄ</button>
        <div id="status" style="margin-top: 15px; font-weight: bold; text-align: center;"></div>
    </div>
    {% endif %}

    {% if page == 'tracker' %}
    <div class="card">
        <h2>Śledzenie Zamówień</h2>
        <p class="info">Status realizacji Twoich paczek subskrypcji w czasie rzeczywistym.</p>
        <table>
            <tr>
                <th>ID</th>
                <th>Link</th>
                <th>Ilość</th>
                <th>Status / Postęp</th>
            </tr>
            {% for o_id, order in orders.items() %}
            {% if order.username == username %}
            <tr>
                <td>#{{ o_id }}</td>
                <td style="max-width: 150px; overflow: hidden; text-overflow: ellipsis;">{{ order.link }}</td>
                <td>{{ order.quantity }}</td>
                <td><b style="color: #00ffcc;">{{ order.status }}</b></td>
            </tr>
            {% endif %}
            {% endfor %}
        </table>
    </div>
    {% endif %}

    {% if page == 'auth' %}
    <div class="card">
        <h2>{{ title }}</h2>
        <form method="POST">
            <label>Nazwa użytkownika (Login):</label>
            <input type="text" name="username" required>
            
            <label>Hasło:</label>
            <input type="password" name="password" required>
            
            <button type="submit" style="margin-top: 20px;">{{ title }}</button>
        </form>
        {% if error %}
        <p style="color: #ff5555; text-align: center; margin-top: 10px;">{{ error }}</p>
        {% endif %}
    </div>
    {% endif %}

    <script>
        function calculate() {
            let count = parseInt(document.getElementById('subsCount').value);
            if(isNaN(count) || count < 10) count = 10;
            if(count > 2000) count = 2000;
            
            // Dokładna kalkulacja proporcjonalna ($0.15 za 1000 sztuk)
            let total = (count / 1000) * 0.15;

            // Wyświetlamy z dokładnością do 4 miejsc po przecinku (np. $0.0015 dla 10 sztuk)
            document.getElementById('price').innerText = "$" + total.toFixed(4);
        }

        function createPayment() {
            let url = document.getElementById('channelUrl').value;
            let count = parseInt(document.getElementById('subsCount').value);
            
            if(!url) { alert("Podaj link do kanału!"); return; }
            if(count < 10) { alert("Minimalna liczba subskrypcji to 10!"); return; }

            document.getElementById('status').style.color = "#ffa500";
            document.getElementById('status').innerText = "Generowanie bramki płatności...";

            fetch('/create-payment', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url, count: count})
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) { window.location.href = data.invoice_url; }
                else { document.getElementById('status').style.color = "#ff5555"; document.getElementById('status').innerText = data.message; }
            });
        }
        if(document.getElementById('subsCount')) calculate();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE, page='home', username=session['user'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user in USERS_DB:
            error = "Taki użytkownik już istnieje!"
        else:
            USERS_DB[user] = {'password': pwd}
            session['user'] = user
            return redirect(url_for('index'))
    return render_template_string(HTML_TEMPLATE, page='auth', title="Rejestracja", error=error, username=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user in USERS_DB and USERS_DB[user]['password'] == pwd:
            session['user'] = user
            return redirect(url_for('index'))
        else:
            error = "Niepoprawny login lub hasło!"
    return render_template_string(HTML_TEMPLATE, page='auth', title="Logowanie", error=error, username=None)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/tracker')
def tracker():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    for o_id, order in ORDERS_DB.items():
        if order['username'] == session['user'] and order.get('smm_id'):
            try:
                status_res = requests.post(SMM_API_URL, data={'key': SMM_API_KEY, 'action': 'status', 'order': order['smm_id']}).json()
                if 'status' in status_res:
                    order['status'] = f"Status: {status_res['status']} | Pozostało: {status_res.get('remains', '0')}"
            except:
                pass

    return render_template_string(HTML_TEMPLATE, page='tracker', username=session['user'], orders=ORDERS_DB)

@app.route('/create-payment', methods=['POST'])
def create_payment():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Musisz być zalogowany!"})
        
    data = request.json
    url = data.get('url')
    count = int(data.get('count', 10))
    
    if count < 10:
        return jsonify({"success": False, "message": "Minimalne zamówienie to 10 subskrypcji!"})
    if count > 2000:
        return jsonify({"success": False, "message": "Maksymalny limit to 2000 sztuk!"})
    
    # Dokładne wyliczenie ceny bez sztywnego minimalnego progu centowego (bramka crypto obsłuży ułamki)
    price_to_pay = round((count / 1000) * 0.15, 4)

    np_url = "https://api.nowpayments.io/v1/invoice"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Content-Type": "application/json"}
    
    order_id = random.randint(10000, 99999)
    
    payload = {
        "price_amount": price_to_pay,
        "price_currency": "usd",
        "order_id": str(order_id),
        "order_description": f"Zamówienie {count} subskrypcji YouTube dla {session['user']}",
        "ipn_callback_url": "https://twoja-domena.pl/crypto-webhook", 
        "success_url": "http://127.0.0.1:5000/tracker",
        "cancel_url": "http://127.0.0.1:5000"
    }

    try:
        response = requests.post(np_url, json=payload, headers=headers)
        res_json = response.json()
        
        if 'invoice_url' in res_json:
            ORDERS_DB[order_id] = {
                'username': session['user'],
                'link': url,
                'quantity': count,
                'smm_id': None,
                'status': 'Oczekiwanie na płatność crypto'
            }
            return jsonify({"success": True, "invoice_url": res_json['invoice_url']})
        else:
            return jsonify({"success": False, "message": "Błąd API NOWPayments: " + str(res_json)})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/crypto-webhook', methods=['POST'])
def crypto_webhook():
    webhook_data = request.json
    payment_status = webhook_data.get('payment_status')
    order_id = webhook_data.get('order_id')
    
    if payment_status in ['finished', 'confirmed'] and order_id and int(order_id) in ORDERS_DB:
        order = ORDERS_DB[int(order_id)]
        
        smm_payload = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': SERVICE_ID,
            'link': order['link'],
            'quantity': order['quantity']
        }
        
        smm_res = requests.post(SMM_API_URL, data=smm_payload).json()
        
        if 'order' in smm_res:
            order['smm_id'] = smm_res['order']
            order['status'] = "W realizacji (Wysłane do SMM)"
        else:
            order['status'] = "Opłacone, błąd wysyłki do SMM"
            
        return jsonify({"status": "success"}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)