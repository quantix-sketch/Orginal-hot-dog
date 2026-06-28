"""
Orginal Xotdog Bot — Asosiy fayl
Xususiyatlar:
  - Ro'yxatdan o'tish: til → ism → telefon → joylashuv (ixtiyoriy)
  - Faqat naqd to'lov
  - Admin panel (buyurtmalar, mahsulotlar, foydalanuvchilar)
  - Mini App ga profil ma'lumotlarini uzatish
"""
import asyncio
import json
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiohttp import web
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import (
    BOT_TOKEN, ADMIN_IDS, WEBAPP_URL, RESTAURANT_NAME,
    RESTAURANT_PHONE, RESTAURANT_ADDRESS, PORT
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()
BASE_DIR = Path(__file__).resolve().parent

# ── Matnlar ───────────────────────────────────────────────
T = {
    "uz": {
        "start":          "👋 Assalomu alaykum!\n<b>Orginal Xotdog</b> botiga xush kelibsiz!\n\nTilni tanlang:",
        "lang_chosen":    "✅ O'zbek tili tanlandi!",
        "name_ask":       "👤 Ismingizni kiriting:\n(Masalan: Alisher Karimov)",
        "name_saved":     "✅ Ism saqlandi!",
        "phone_ask":      "📱 Telefon raqamingizni yuboring:",
        "phone_btn":      "📱 Raqamni yuborish",
        "phone_saved":    "✅ Raqam saqlandi!",
        "location_ask":   "📍 Joylashuvingizni yuboring (ixtiyoriy):\nYoki <b>O'tkazib yuborish</b> tugmasini bosing.",
        "location_btn":   "📍 Joylashuvni yuborish",
        "skip_btn":       "⏭ O'tkazib yuborish",
        "location_saved": "✅ Joylashuv saqlandi!",
        "location_skip":  "👌 O'tkazib yuborildi.",
        "menu_btn":       "🛒 Menyu",
        "orders_btn":     "📦 Buyurtmalarim",
        "info_btn":       "ℹ️ Ma'lumot",
        "profile_btn":    "👤 Profilim",
        "main_menu":      "Asosiy menyu:",
        "info_text":      "🌭 <b>{name}</b>\n📍 {address}\n📞 {phone}\n⏰ 09:00 – 23:00",
        "no_orders":      "Hali buyurtmangiz yo'q.",
        "profile_text":   "👤 <b>Profilingiz</b>\n\n👤 Ism: {name}\n📱 Tel: {phone}\n🌐 Til: O'zbek\n📦 Buyurtmalar: {orders}",
        "order_status": {
            "pending":    "⏳ Kutilmoqda",
            "confirmed":  "✅ Tasdiqlandi",
            "cooking":    "👨‍🍳 Tayyorlanmoqda",
            "delivering": "🚗 Yetkazilmoqda",
            "done":       "✅ Yetkazildi",
            "cancelled":  "❌ Bekor qilindi",
        }
    },
    "ru": {
        "start":          "👋 Привет!\nДобро пожаловать в <b>Orginal Xotdog</b>!\n\nВыберите язык:",
        "lang_chosen":    "✅ Выбран русский язык!",
        "name_ask":       "👤 Введите ваше имя:\n(Например: Алишер Каримов)",
        "name_saved":     "✅ Имя сохранено!",
        "phone_ask":      "📱 Отправьте ваш номер телефона:",
        "phone_btn":      "📱 Отправить номер",
        "phone_saved":    "✅ Номер сохранён!",
        "location_ask":   "📍 Отправьте ваше местоположение (необязательно):\nИли нажмите <b>Пропустить</b>.",
        "location_btn":   "📍 Отправить геолокацию",
        "skip_btn":       "⏭ Пропустить",
        "location_saved": "✅ Геолокация сохранена!",
        "location_skip":  "👌 Пропущено.",
        "menu_btn":       "🛒 Меню",
        "orders_btn":     "📦 Мои заказы",
        "info_btn":       "ℹ️ Информация",
        "profile_btn":    "👤 Мой профиль",
        "main_menu":      "Главное меню:",
        "info_text":      "🌭 <b>{name}</b>\n📍 {address}\n📞 {phone}\n⏰ 09:00 – 23:00",
        "no_orders":      "У вас ещё нет заказов.",
        "profile_text":   "👤 <b>Ваш профиль</b>\n\n👤 Имя: {name}\n📱 Тел: {phone}\n🌐 Язык: Русский\n📦 Заказов: {orders}",
        "order_status": {
            "pending":    "⏳ Ожидание",
            "confirmed":  "✅ Подтверждён",
            "cooking":    "👨‍🍳 Готовится",
            "delivering": "🚗 Доставляется",
            "done":       "✅ Доставлен",
            "cancelled":  "❌ Отменён",
        }
    }
}

def t(lang, key):
    return T.get(lang, T["uz"]).get(key, key)

def restaurant_info_text(lang):
    return t(lang, "info_text").format(
        name=RESTAURANT_NAME,
        address=RESTAURANT_ADDRESS,
        phone=RESTAURANT_PHONE,
    )

# ── FSM ───────────────────────────────────────────────────
class Reg(StatesGroup):
    lang     = State()
    name     = State()
    phone    = State()
    location = State()

# ── Klaviaturalar ─────────────────────────────────────────
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbek",  callback_data="lang_uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
    ]])

def phone_kb(lang):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "phone_btn"), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def location_kb(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "location_btn"), request_location=True)],
            [KeyboardButton(text=t(lang, "skip_btn"))],
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

def main_kb(lang):
    url = f"{WEBAPP_URL}?lang={lang}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "menu_btn"), web_app=WebAppInfo(url=url))],
            [KeyboardButton(text=t(lang, "orders_btn")),
             KeyboardButton(text=t(lang, "profile_btn"))],
            [KeyboardButton(text=t(lang, "info_btn"))],
        ],
        resize_keyboard=True
    )

# ── Web server ─────────────────────────────────────────────
async def webapp_index(request):
    return web.FileResponse(BASE_DIR / "webapp" / "index.html")

async def webapp_menu(request):
    return web.json_response({
        "categories": db.get_categories(),
        "products":   db.get_active_products(),
    })

async def webapp_profile(request):
    """Mini App profil ma'lumotlarini oladi"""
    user_id = request.rel_url.query.get("user_id")
    if not user_id:
        return web.json_response({"ok": False})
    try:
        user_id = int(user_id)
    except ValueError:
        return web.json_response({"ok": False})
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not row:
        return web.json_response({"ok": False})
    return web.json_response({
        "ok": True,
        "user": {
            "id":        row["id"],
            "full_name": row["full_name"] or "",
            "phone":     row["phone"] or "",
            "lang":      row["lang"] or "uz",
            "lat":       row["lat"] if "lat" in row.keys() else None,
            "lng":       row["lng"] if "lng" in row.keys() else None,
        }
    })

async def webapp_order(request):
    """Mini App dan fetch() orqali kelgan buyurtma"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid json"}, status=400)

    user_id = data.get("user_id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user_id"}, status=400)

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return web.json_response({"ok": False, "error": "bad user_id"}, status=400)

    client_items  = data.get("items", [])
    address       = str(data.get("address", "")).strip()[:300]
    delivery_type = data.get("delivery_type", "delivery")

    try:
        items, total = db.validate_order_items(client_items)
    except ValueError as exc:
        return web.json_response({"ok": False, "error": str(exc)}, status=400)

    order_id = db.create_order(
        user_id, items, total, address, "pending",
        delivery_type=delivery_type
    )

    bot = request.app["bot"]

    # Foydalanuvchi tili
    conn = db.get_conn()
    row = conn.execute("SELECT lang, full_name FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    lang = row["lang"] if row else "uz"
    full_name = (row["full_name"] or "Mijoz") if row else "Mijoz"

    # Foydalanuvchiga tasdiqlash
    try:
        lines = []
        for it in items:
            nm = it.get("name_uz" if lang == "uz" else "name_ru", it.get("name_uz", ""))
            lines.append(f"  • {nm} × {it['qty']} = {it['price'] * it['qty']:,} so'm")

        text = (
            f"✅ <b>Buyurtma #{order_id} qabul qilindi!</b>\n\n"
            f"{''.join(chr(10).join(lines))}\n\n"
            f"💰 <b>Jami: {total:,} so'm</b>\n"
            f"💵 To'lov: Naqd pul\n"
        ) if lang == "uz" else (
            f"✅ <b>Заказ #{order_id} принят!</b>\n\n"
            f"{''.join(chr(10).join(lines))}\n\n"
            f"💰 <b>Итого: {total:,} сум</b>\n"
            f"💵 Оплата: Наличными\n"
        )
        if address:
            text += f"📍 {address}"

        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.warning("Foydalanuvchiga xabar xato: %s", e)

    # Adminga
    try:
        class FU:
            id = user_id
            full_name = full_name
            username = None
        await notify_admins(bot, order_id, FU(), items, total, address, lang, delivery_type)
    except Exception as e:
        logger.warning("Adminga xabar xato: %s", e)

    return web.json_response({"ok": True, "order_id": order_id})

# ── Admin panel web ────────────────────────────────────────
async def admin_web_panel(request):
    """Admin HTML panel"""
    html = """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Panel — Orginal Xotdog</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;color:#333}
.header{background:#1a1a2e;color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px}
.header h1{font-size:18px;font-weight:700}
.tabs{display:flex;background:#fff;border-bottom:2px solid #e0e0e0;overflow-x:auto}
.tab{padding:12px 20px;cursor:pointer;font-weight:600;color:#888;white-space:nowrap;border-bottom:3px solid transparent;transition:.2s}
.tab.active{color:#1a1a2e;border-bottom-color:#ff6b35}
.content{padding:16px;max-width:900px;margin:0 auto}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600}
.badge-pending{background:#fff3cd;color:#856404}
.badge-confirmed{background:#d1ecf1;color:#0c5460}
.badge-cooking{background:#f8d7da;color:#721c24}
.badge-delivering{background:#cce5ff;color:#004085}
.badge-done{background:#d4edda;color:#155724}
.badge-cancelled{background:#e2e3e5;color:#383d41}
.btn{padding:8px 16px;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:13px}
.btn-primary{background:#1a1a2e;color:#fff}
.btn-danger{background:#dc3545;color:#fff}
.btn-success{background:#28a745;color:#fff}
.btn-warning{background:#ffc107;color:#333}
.btn-sm{padding:5px 10px;font-size:12px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #eee;font-size:13px}
th{background:#f8f9fa;font-weight:700;color:#666}
tr:hover{background:#fafafa}
.form-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.form-row input,.form-row select{flex:1;min-width:140px;padding:8px 12px;border:1px solid #ddd;border-radius:8px;font-size:14px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:16px}
.stat{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.stat-num{font-size:28px;font-weight:800;color:#1a1a2e}
.stat-label{font-size:12px;color:#888;margin-top:4px}
.search{width:100%;padding:10px 14px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px}
@media(max-width:600px){.form-row{flex-direction:column}.form-row input,.form-row select{min-width:unset}}
</style>
</head>
<body>
<div class="header">
  <span style="font-size:24px">🌭</span>
  <h1>Orginal Xotdog — Admin Panel</h1>
</div>
<div class="tabs">
  <div class="tab active" onclick="showTab('orders')">📋 Buyurtmalar</div>
  <div class="tab" onclick="showTab('products')">🍔 Mahsulotlar</div>
  <div class="tab" onclick="showTab('users')">👥 Foydalanuvchilar</div>
  <div class="tab" onclick="showTab('stats')">📊 Statistika</div>
</div>

<!-- ORDERS -->
<div id="tab-orders" class="content">
  <div class="card">
    <input class="search" id="orderSearch" placeholder="🔍 Buyurtma qidirish..." oninput="filterOrders()">
    <table id="ordersTable">
      <thead><tr><th>#</th><th>Mijoz</th><th>Mahsulotlar</th><th>Summa</th><th>Tur</th><th>Status</th><th>Sana</th><th>Amal</th></tr></thead>
      <tbody id="ordersTbody"></tbody>
    </table>
  </div>
</div>

<!-- PRODUCTS -->
<div id="tab-products" class="content" style="display:none">
  <div class="card">
    <h3 style="margin-bottom:12px">➕ Yangi mahsulot qo'shish</h3>
    <div class="form-row">
      <select id="pCat"><option value="">Kategoriya</option></select>
      <input id="pNameUz" placeholder="Nomi (UZ)">
      <input id="pNameRu" placeholder="Nomi (RU)">
    </div>
    <div class="form-row">
      <input id="pDescUz" placeholder="Tavsif (UZ)">
      <input id="pDescRu" placeholder="Tavsif (RU)">
      <input id="pPrice" type="number" placeholder="Narxi (so'm)" min="0">
    </div>
    <button class="btn btn-primary" onclick="addProduct()">✅ Qo'shish</button>
  </div>
  <div class="card">
    <table>
      <thead><tr><th>#</th><th>Nom</th><th>Kategoriya</th><th>Narx</th><th>Holat</th><th>Amal</th></tr></thead>
      <tbody id="productsTbody"></tbody>
    </table>
  </div>
</div>

<!-- USERS -->
<div id="tab-users" class="content" style="display:none">
  <div class="card">
    <input class="search" id="userSearch" placeholder="🔍 Foydalanuvchi qidirish..." oninput="filterUsers()">
    <table>
      <thead><tr><th>ID</th><th>Ism</th><th>Telefon</th><th>Til</th><th>Ro'yxat</th></tr></thead>
      <tbody id="usersTbody"></tbody>
    </table>
  </div>
</div>

<!-- STATS -->
<div id="tab-stats" class="content" style="display:none">
  <div class="stat-grid" id="statsGrid"></div>
</div>

<script>
let allOrders=[], allUsers=[], allProducts=[], allCats=[];

const STATUS_LABELS = {
  pending:"⏳ Kutilmoqda", confirmed:"✅ Tasdiqlandi",
  cooking:"👨‍🍳 Tayyorlanmoqda", delivering:"🚗 Yetkazilmoqda",
  done:"✅ Yetkazildi", cancelled:"❌ Bekor qilindi"
};

function showTab(name){
  document.querySelectorAll('.content').forEach(el=>el.style.display='none');
  document.querySelectorAll('.tab').forEach(el=>el.classList.remove('active'));
  document.getElementById('tab-'+name).style.display='block';
  event.target.classList.add('active');
  if(name==='orders') loadOrders();
  if(name==='products') loadProducts();
  if(name==='users') loadUsers();
  if(name==='stats') loadStats();
}

async function loadOrders(){
  const r = await fetch('/admin/api/orders');
  allOrders = await r.json();
  renderOrders(allOrders);
}
function renderOrders(orders){
  const tb = document.getElementById('ordersTbody');
  tb.innerHTML = orders.map(o=>`
    <tr>
      <td><b>#${o.id}</b></td>
      <td>${o.full_name||'?'}<br><small style="color:#888">${o.phone||''}</small></td>
      <td style="max-width:180px;font-size:12px">${(o.items||[]).map(i=>i.name_uz+' ×'+i.qty).join(', ')}</td>
      <td><b>${(o.total_price||0).toLocaleString()} so'm</b></td>
      <td>${o.delivery_type==='pickup'?'🏪 Olib ketish':'🚗 Yetkazish'}</td>
      <td><span class="badge badge-${o.status}">${STATUS_LABELS[o.status]||o.status}</span></td>
      <td style="font-size:12px">${(o.created_at||'').slice(0,16)}</td>
      <td>
        <select onchange="changeStatus(${o.id},this.value)" style="font-size:12px;padding:4px;border:1px solid #ddd;border-radius:6px">
          <option value="">Status o'zgartir</option>
          <option value="confirmed">✅ Tasdiqlash</option>
          <option value="cooking">👨‍🍳 Tayyorlanmoqda</option>
          <option value="delivering">🚗 Yetkazilmoqda</option>
          <option value="done">✅ Yetkazildi</option>
          <option value="cancelled">❌ Bekor qilish</option>
        </select>
      </td>
    </tr>`).join('');
}
function filterOrders(){
  const q = document.getElementById('orderSearch').value.toLowerCase();
  renderOrders(allOrders.filter(o=>
    String(o.id).includes(q) ||
    (o.full_name||'').toLowerCase().includes(q) ||
    (o.phone||'').includes(q)
  ));
}
async function changeStatus(orderId, status){
  if(!status) return;
  await fetch('/admin/api/order/status', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({order_id:orderId, status})
  });
  loadOrders();
}

async function loadProducts(){
  const [pr, cr] = await Promise.all([
    fetch('/admin/api/products').then(r=>r.json()),
    fetch('/admin/api/categories').then(r=>r.json())
  ]);
  allProducts = pr; allCats = cr;
  const sel = document.getElementById('pCat');
  sel.innerHTML = '<option value="">Kategoriya</option>' +
    cr.map(c=>`<option value="${c.id}">${c.emoji} ${c.name_uz}</option>`).join('');
  const tb = document.getElementById('productsTbody');
  tb.innerHTML = pr.map(p=>`
    <tr>
      <td><b>#${p.id}</b></td>
      <td>${p.emoji||'🍽️'} ${p.name_uz}<br><small style="color:#888">${p.name_ru}</small></td>
      <td>${(cr.find(c=>c.id===p.category_id)||{}).name_uz||'?'}</td>
      <td>
        <input type="number" value="${p.price}" min="0" style="width:90px;padding:4px;border:1px solid #ddd;border-radius:6px"
          onchange="updatePrice(${p.id},this.value)">
      </td>
      <td><span class="badge ${p.active?'badge-done':'badge-cancelled'}">${p.active?'✅ Aktiv':'❌ Yashirin'}</span></td>
      <td>
        <button class="btn btn-warning btn-sm" onclick="toggleProduct(${p.id})">${p.active?'Yashir':'Aktiv'}</button>
      </td>
    </tr>`).join('');
}
async function addProduct(){
  const d = {
    category_id: parseInt(document.getElementById('pCat').value),
    name_uz: document.getElementById('pNameUz').value.trim(),
    name_ru: document.getElementById('pNameRu').value.trim(),
    desc_uz: document.getElementById('pDescUz').value.trim(),
    desc_ru: document.getElementById('pDescRu').value.trim(),
    price:   parseInt(document.getElementById('pPrice').value)||0,
  };
  if(!d.category_id||!d.name_uz||!d.price){ alert('Kategoriya, nom va narx kiritilishi shart!'); return; }
  const r = await fetch('/admin/api/product/add', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
  const res = await r.json();
  if(res.ok){ alert('✅ Mahsulot qo\\'shildi!'); loadProducts(); }
  else alert('Xato: '+res.error);
}
async function toggleProduct(pid){
  await fetch('/admin/api/product/toggle', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:pid})});
  loadProducts();
}
async function updatePrice(pid, price){
  await fetch('/admin/api/product/price', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:pid,price:parseInt(price)})});
}

async function loadUsers(){
  const r = await fetch('/admin/api/users');
  allUsers = await r.json();
  renderUsers(allUsers);
}
function renderUsers(users){
  document.getElementById('usersTbody').innerHTML = users.map(u=>`
    <tr>
      <td>${u.id}</td>
      <td>${u.full_name||'—'}</td>
      <td>${u.phone||'—'}</td>
      <td>${u.lang==='ru'?'🇷🇺 Rus':'🇺🇿 O\\'zbek'}</td>
      <td style="font-size:12px">${(u.created_at||'').slice(0,16)}</td>
    </tr>`).join('');
}
function filterUsers(){
  const q = document.getElementById('userSearch').value.toLowerCase();
  renderUsers(allUsers.filter(u=>
    String(u.id).includes(q)||
    (u.full_name||'').toLowerCase().includes(q)||
    (u.phone||'').includes(q)
  ));
}

async function loadStats(){
  const r = await fetch('/admin/api/stats');
  const s = await r.json();
  document.getElementById('statsGrid').innerHTML = `
    <div class="stat"><div class="stat-num">${s.total_orders}</div><div class="stat-label">Jami buyurtmalar</div></div>
    <div class="stat"><div class="stat-num">${s.today_orders}</div><div class="stat-label">Bugungi buyurtmalar</div></div>
    <div class="stat"><div class="stat-num">${(s.total_revenue||0).toLocaleString()}</div><div class="stat-label">Jami tushum (so'm)</div></div>
    <div class="stat"><div class="stat-num">${s.total_users}</div><div class="stat-label">Foydalanuvchilar</div></div>
    <div class="stat"><div class="stat-num">${s.active_products}</div><div class="stat-label">Aktiv mahsulotlar</div></div>
    <div class="stat"><div class="stat-num">${s.pending_orders}</div><div class="stat-label">Kutilayotgan</div></div>
  `;
}

// Auto-load on start
loadOrders();
</script>
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

# Admin API endpoints
async def admin_api_orders(request):
    conn = db.get_conn()
    orders = conn.execute("""
        SELECT o.*, u.full_name, u.phone
        FROM orders o LEFT JOIN users u ON u.id=o.user_id
        ORDER BY o.created_at DESC LIMIT 100
    """).fetchall()
    result = []
    for o in orders:
        od = dict(o)
        items = conn.execute("""
            SELECT oi.qty, oi.price, p.name_uz, p.name_ru
            FROM order_items oi JOIN products p ON p.id=oi.product_id
            WHERE oi.order_id=?
        """, (od["id"],)).fetchall()
        od["items"] = [dict(i) for i in items]
        result.append(od)
    conn.close()
    return web.json_response(result)

async def admin_api_order_status(request):
    data = await request.json()
    order_id = data.get("order_id")
    status   = data.get("status")
    if not order_id or not status:
        return web.json_response({"ok": False})
    db.update_order_status(int(order_id), status)
    # Foydalanuvchiga xabar
    try:
        bot = request.app["bot"]
        order = db.get_order(int(order_id))
        STATUS_LABELS = {
            "confirmed":  "✅ Tasdiqlandi",
            "cooking":    "👨‍🍳 Tayyorlanmoqda",
            "delivering": "🚗 Yetkazilmoqda",
            "done":       "✅ Yetkazildi",
            "cancelled":  "❌ Bekor qilindi",
        }
        if order:
            await bot.send_message(
                order["user_id"],
                f"📦 Buyurtma #{order_id} holati: {STATUS_LABELS.get(status, status)}"
            )
    except Exception as e:
        logger.warning("Status xabar xato: %s", e)
    return web.json_response({"ok": True})

async def admin_api_products(request):
    return web.json_response(db.get_all_products())

async def admin_api_categories(request):
    return web.json_response(db.get_categories())

async def admin_api_product_add(request):
    data = await request.json()
    try:
        pid = db.add_product(
            data["category_id"], data["name_uz"], data["name_ru"],
            data.get("desc_uz",""), data.get("desc_ru",""), int(data["price"])
        )
        return web.json_response({"ok": True, "id": pid})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})

async def admin_api_product_toggle(request):
    data = await request.json()
    db.toggle_product(int(data["id"]))
    return web.json_response({"ok": True})

async def admin_api_product_price(request):
    data = await request.json()
    db.update_product_price(int(data["id"]), int(data["price"]))
    return web.json_response({"ok": True})

async def admin_api_users(request):
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return web.json_response([dict(r) for r in rows])

async def admin_api_stats(request):
    conn = db.get_conn()
    total_orders  = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    today_orders  = conn.execute("SELECT COUNT(*) FROM orders WHERE date(created_at)=date('now')").fetchone()[0]
    total_revenue = conn.execute("SELECT SUM(total_price) FROM orders WHERE status='done'").fetchone()[0] or 0
    total_users   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_prods  = conn.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]
    pending       = conn.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0]
    conn.close()
    return web.json_response({
        "total_orders":   total_orders,
        "today_orders":   today_orders,
        "total_revenue":  total_revenue,
        "total_users":    total_users,
        "active_products": active_prods,
        "pending_orders": pending,
    })

async def start_web_server(bot_instance=None):
    app = web.Application()
    if bot_instance:
        app["bot"] = bot_instance

    # Mini App endpoints
    app.router.add_get("/", webapp_index)
    app.router.add_get("/api/menu", webapp_menu)
    app.router.add_get("/api/profile", webapp_profile)
    app.router.add_post("/api/order", webapp_order)

    # Admin panel
    app.router.add_get("/admin", admin_web_panel)
    app.router.add_get("/admin/api/orders", admin_api_orders)
    app.router.add_post("/admin/api/order/status", admin_api_order_status)
    app.router.add_get("/admin/api/products", admin_api_products)
    app.router.add_get("/admin/api/categories", admin_api_categories)
    app.router.add_post("/admin/api/product/add", admin_api_product_add)
    app.router.add_post("/admin/api/product/toggle", admin_api_product_toggle)
    app.router.add_post("/admin/api/product/price", admin_api_product_price)
    app.router.add_get("/admin/api/users", admin_api_users)
    app.router.add_get("/admin/api/stats", admin_api_stats)

    app.router.add_static("/webapp", BASE_DIR / "webapp")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Web server started on port %s", PORT)
    return runner

# ── Handlerlar ────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    if user.get("phone"):
        lang = user.get("lang", "uz")
        await msg.answer(t(lang, "main_menu"), reply_markup=main_kb(lang))
    else:
        await msg.answer(T["uz"]["start"], reply_markup=lang_kb(), parse_mode="HTML")
        await state.set_state(Reg.lang)


@router.callback_query(F.data.startswith("lang_"))
async def choose_lang(cq: CallbackQuery, state: FSMContext):
    lang = cq.data.split("_")[1]
    db.set_user_lang(cq.from_user.id, lang)
    await cq.message.edit_text(t(lang, "lang_chosen"))
    await cq.message.answer(t(lang, "name_ask"), parse_mode="HTML")
    await state.set_state(Reg.name)


@router.message(Reg.name, F.text)
async def save_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if len(name) < 2 or len(name) > 60:
        await msg.answer("❌ Ism 2 dan 60 gacha belgi bo'lishi kerak. Qaytadan kiriting:")
        return
    # DB ga ismni saqlash
    conn = db.get_conn()
    conn.execute("UPDATE users SET full_name=? WHERE id=?", (name, msg.from_user.id))
    conn.commit()
    conn.close()
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, name)
    lang = user.get("lang", "uz")
    await msg.answer(t(lang, "name_saved"))
    await msg.answer(t(lang, "phone_ask"), reply_markup=phone_kb(lang), parse_mode="HTML")
    await state.set_state(Reg.phone)


@router.message(Reg.phone, F.contact)
async def save_phone(msg: Message, state: FSMContext):
    if msg.contact.user_id and msg.contact.user_id != msg.from_user.id:
        user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
        await msg.answer(t(user.get("lang","uz"), "phone_ask"), reply_markup=phone_kb(user.get("lang","uz")))
        return
    phone = msg.contact.phone_number
    db.set_user_phone(msg.from_user.id, phone)
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    await msg.answer(t(lang, "phone_saved"), reply_markup=ReplyKeyboardRemove())
    await msg.answer(t(lang, "location_ask"), reply_markup=location_kb(lang), parse_mode="HTML")
    await state.set_state(Reg.location)


@router.message(Reg.location, F.location)
async def save_location(msg: Message, state: FSMContext):
    lat = msg.location.latitude
    lng = msg.location.longitude
    conn = db.get_conn()
    db.ensure_column(conn.cursor(), "users", "lat", "REAL")
    db.ensure_column(conn.cursor(), "users", "lng", "REAL")
    conn.execute("UPDATE users SET lat=?, lng=? WHERE id=?", (lat, lng, msg.from_user.id))
    conn.commit()
    conn.close()
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    await state.clear()
    await msg.answer(t(lang, "location_saved"), reply_markup=ReplyKeyboardRemove())
    await msg.answer(t(lang, "main_menu"), reply_markup=main_kb(lang))


@router.message(Reg.location, F.text)
async def skip_location(msg: Message, state: FSMContext):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    await state.clear()
    await msg.answer(t(lang, "location_skip"), reply_markup=ReplyKeyboardRemove())
    await msg.answer(t(lang, "main_menu"), reply_markup=main_kb(lang))


@router.message(F.text.in_(["📦 Buyurtmalarim", "📦 Мои заказы"]))
async def my_orders(msg: Message):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    conn = db.get_conn()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
        (msg.from_user.id,)
    ).fetchall()
    conn.close()
    if not orders:
        await msg.answer(t(lang, "no_orders"))
        return
    status_map = t(lang, "order_status")
    lines = []
    for o in orders:
        st = status_map.get(o["status"], o["status"])
        lines.append(f"📦 #{o['id']} — {o['total_price']:,} so'm\n   {st} | {o['created_at'][:16]}")
    await msg.answer("\n\n".join(lines))


@router.message(F.text.in_(["👤 Profilim", "👤 Мой профиль"]))
async def my_profile(msg: Message):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    conn = db.get_conn()
    order_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE user_id=?", (msg.from_user.id,)
    ).fetchone()[0]
    conn.close()
    text = t(lang, "profile_text").format(
        name=user.get("full_name") or "—",
        phone=user.get("phone") or "—",
        orders=order_count
    )
    await msg.answer(text, parse_mode="HTML")


@router.message(F.text.in_(["ℹ️ Ma'lumot", "ℹ️ Информация"]))
async def info(msg: Message):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    await msg.answer(restaurant_info_text(lang), parse_mode="HTML")


# ── WebApp dan sendData orqali buyurtma (fallback) ────────
@router.message(F.web_app_data)
async def webapp_order_handler(msg: Message):
    user = db.get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    lang = user.get("lang", "uz")
    try:
        data = json.loads(msg.web_app_data.data)
    except Exception:
        await msg.answer("❌ Xato. Qaytadan urinib ko'ring.")
        return
    address      = str(data.get("address", "")).strip()[:300]
    client_items = data.get("items", [])
    if not client_items:
        await msg.answer("🛒 Savat bo'sh!")
        return
    try:
        items, total = db.validate_order_items(client_items)
        order_id = db.create_order(msg.from_user.id, items, total, address, "pending",
                                   delivery_type=data.get("delivery_type","delivery"))
    except ValueError as exc:
        await msg.answer("❌ Buyurtma noto'g'ri. Qayta urinib ko'ring.")
        return
    lines = [f"  • {it.get('name_uz','')} × {it['qty']} = {it['price']*it['qty']:,} so'm" for it in items]
    text = f"✅ <b>Buyurtma #{order_id} qabul qilindi!</b>\n\n" + "\n".join(lines)
    text += f"\n\n💰 <b>Jami: {total:,} so'm</b>\n💵 To'lov: Naqd pul"
    if address:
        text += f"\n📍 {address}"
    await msg.answer(text, parse_mode="HTML")
    await notify_admins(msg.bot, order_id, msg.from_user, items, total, address, lang,
                        data.get("delivery_type","delivery"))


async def notify_admins(bot, order_id, user, items, total, address, lang, delivery_type="delivery"):
    dt = "🏪 Olib ketish" if delivery_type == "pickup" else "🚗 Yetkazish"
    lines = [
        f"🆕 <b>Yangi buyurtma #{order_id}</b>",
        f"👤 {user.full_name} | @{user.username or '—'} | ID: {user.id}",
        f"📦 {dt}",
    ]
    for it in items:
        lines.append(f"  • {it.get('name_uz','')} × {it['qty']} = {it['price']*it['qty']:,} so'm")
    lines.append(f"💰 <b>Jami: {total:,} so'm</b>")
    if address:
        lines.append(f"📍 {address}")

    status_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash",     callback_data=f"status_{order_id}_confirmed")],
        [InlineKeyboardButton(text="👨‍🍳 Tayyorlanmoqda", callback_data=f"status_{order_id}_cooking")],
        [InlineKeyboardButton(text="🚗 Yetkazilmoqda",   callback_data=f"status_{order_id}_delivering")],
        [InlineKeyboardButton(text="✅ Yetkazildi",       callback_data=f"status_{order_id}_done")],
        [InlineKeyboardButton(text="❌ Bekor qilish",     callback_data=f"status_{order_id}_cancelled")],
    ])
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "\n".join(lines),
                                   reply_markup=status_kb, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Admin %s ga xabar yo'q: %s", admin_id, exc)


@router.callback_query(F.data.startswith("status_"))
async def update_status(cq: CallbackQuery):
    if cq.from_user.id not in ADMIN_IDS:
        return
    parts = cq.data.split("_", 2)
    order_id = int(parts[1])
    status   = parts[2]
    STATUS_LABELS = {
        "confirmed":  "✅ Tasdiqlandi",
        "cooking":    "👨‍🍳 Tayyorlanmoqda",
        "delivering": "🚗 Yetkazilmoqda",
        "done":       "✅ Yetkazildi",
        "cancelled":  "❌ Bekor qilindi",
    }
    if status not in STATUS_LABELS:
        await cq.answer("Noto'g'ri status"); return
    order = db.get_order(order_id)
    if order is None:
        await cq.answer("Buyurtma topilmadi"); return
    db.update_order_status(order_id, status)
    await cq.answer(f"Status: {STATUS_LABELS[status]}")
    try:
        await cq.bot.send_message(
            order["user_id"],
            f"📦 Buyurtma #{order_id} holati: {STATUS_LABELS[status]}"
        )
    except Exception as exc:
        logger.warning("Status xabar xato: %s", exc)


# ── Admin bot buyruqlari ──────────────────────────────────
@router.message(Command("admin"))
async def admin_panel_cmd(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    panel_url = f"{WEBAPP_URL}/admin"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Admin Panelni ochish", url=panel_url)],
    ])
    await msg.answer(
        f"🛠 <b>Admin Panel</b>\n\n"
        f"Brauzer orqali:\n<code>{panel_url}</code>",
        reply_markup=kb, parse_mode="HTML"
    )


# ── Main ──────────────────────────────────────────────────
async def main():
    db.init_db()
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN":
        raise RuntimeError("BOT_TOKEN sozlanmagan!")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp  = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    web_runner = await start_web_server(bot)
    try:
        await dp.start_polling(bot)
    finally:
        await web_runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
