# 🌭 Orginal Xotdog Bot

Telegram Mini App + Bot — buyurtma tizimi (naqd to'lov).

## 📁 Fayl tuzilmasi

```
orginal_xotdog_bot/
├── bot.py            # Asosiy bot (aiogram 3.x) + web server + admin panel
├── database.py       # SQLite ma'lumotlar bazasi
├── payments.py       # (kelajak uchun)
├── config.py         # Tokenlar va sozlamalar
├── requirements.txt
├── nixpacks.toml     # Railway deploy config
└── webapp/
    ├── index.html    # Telegram Mini App
    ├── logo.png
    └── logo_cropped.png
```

## 🚀 Deploy (Railway)

### 1. Environment Variables qo'shing

| Variable | Qiymat |
|----------|--------|
| `BOT_TOKEN` | BotFather dan olingan token |
| `ADMIN_IDS` | Sizning Telegram ID (vergul bilan: 123,456) |
| `WEBAPP_URL` | Railway URL (masalan: https://xotdog.up.railway.app) |
| `RESTAURANT_PHONE` | +998 XX XXX XX XX |
| `RESTAURANT_ADDRESS` | Toshkent, Ibn Sino ... |

### 2. BotFather sozlamalari

```
@BotFather → /setmenubutton → botingiz → WEBAPP_URL
```

### 3. Admin panel

Deploy qilgandan keyin:
```
https://sizning-url.railway.app/admin
```

## 🤖 Bot oqimi

1. /start → Til tanlash
2. Ism kiriting
3. Telefon raqam (tugma orqali)
4. Joylashuv (ixtiyoriy)
5. Asosiy menyu → Mini App ochiladi

## 🛠 Admin panel imkoniyatlari

- 📋 Buyurtmalar — ko'rish, status o'zgartirish
- 🍔 Mahsulotlar — qo'shish, narx, yashirish
- 👥 Foydalanuvchilar — ro'yxat
- 📊 Statistika — tushum, buyurtmalar soni
