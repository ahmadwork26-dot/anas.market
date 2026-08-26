import streamlit as st
from datetime import datetime
import sqlite3

# ڕێکخستنی پەڕەی وێب و بەکارهێنانی ڕوکاری مۆدێرن
st.set_page_config(page_title="Anas Market - Modern POS", page_icon="⚡", layout="wide")

# CSS ی تایبەت بۆ گۆڕینی ڕوکار بۆ شێوازێکی مۆدێرن و تاریک
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Tajawal', sans-serif;
    }
    .sidebar .stSelectbox {
        background-color: #1e293b;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #075985 100%);
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# دروستکردن یان بەستنەوە بە داتابەیس
def init_db():
    conn = sqlite3.connect("market.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            cost_price REAL NOT NULL,
            sell_price REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            items TEXT,
            total_amount REAL,
            total_profit REAL,
            sale_type TEXT,
            customer_name TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT,
            total_debt REAL,
            date TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# سەردێڕی سەرەکی مۆدێرن
st.title("⚡ Anas Market - POS & Debt System")
st.markdown("---")

# مێنوی لاوەکی سەردەمیانە
menu = st.sidebar.selectbox("🎯 بەشی بەڕێوەبردن", [
    "فرۆشتن (POS)", 
    "زیادکردنی کاڵا", 
    "ڕاپۆرتی داهات و قازانج", 
    "بەڕێوەبردنی قەرزەکان"
])

# 1. بەشی فرۆشتن
if menu == "فرۆشتن (POS)":
    st.header("💳 خاڵی فرۆشتنی خێرا (POS)")
    
    # وەرگرتنی بارکۆد لە ڕێگەی سکانەری دەرەکییەوە
    scanner_input = st.text_input("🔍 بارکۆدی کاڵا لێرە سکان بکە (Barcode Scanner)", key="scanner_box", placeholder="بارکۆد لێرە بنووسە یان سکان بکە...")
    
    if scanner_input:
        cursor.execute("SELECT barcode, name, cost_price, sell_price FROM products WHERE barcode = ?", (scanner_input.strip(),))
        matched_p = cursor.fetchone()
        
        if matched_p:
            p_barcode, p_name, p_cost, p_sell = matched_p
            if "cart" not in st.session_state:
                st.session_state.cart = []
            
            # پشکنین ئەگەر کاڵاکە پێشتر لە سەبەتەدا هەبێت بڕەکەی زیاد بکە
            found_in_cart = False
            for item in st.session_state.cart:
                if item["barcode"] == p_barcode:
                    item["qty"] += 1
                    item["total"] = item["qty"] * item["price"]
                    found_in_cart = True
                    break
            
            if not found_in_cart:
                st.session_state.cart.append({
                    "barcode": p_barcode,
                    "name": p_name,
                    "price": p_sell,
                    "qty": 1,
                    "total": p_sell
                })
            st.success(f"✅ کاڵای '{p_name}' زیاد کرا بۆ سەبەتە!")
        else:
            st.error("❌ هیچ کاڵایەک بەم بارکۆدە نەدۆزرایەوە!")

    st.markdown("---")
    
    if "cart" not in st.session_state:
        st.session_state.cart = []
        
    if st.session_state.cart:
        st.markdown("### 🛍️ سەبەتەی کڕین")
        cart_total = 0
        cart_profit = 0
        
        for index, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"▪️ {item['name']}")
            col2.write(f"{item['qty']} x {item['price']:,.0f}")
            col3.write(f"**{item['total']:,.0f} IQD**")
            
            cursor.execute("SELECT cost_price FROM products WHERE barcode = ?", (item['barcode'],))
            res = cursor.fetchone()
            cost = res[0] if res else 0
            item_profit = (item['price'] - cost) * item['qty']
            cart_profit += item_profit
            cart_total += item['total']
            
            if col4.button("❌", key=f"del_{index}"):
                st.session_state.cart.pop(index)
                st.rerun()
                
        st.markdown("---")
        st.markdown(f"### 💎 کۆی گشتی پارە: **{cart_total:,.0f} IQD**")
        
        # جۆری پارەدان (کاش یان قەرز)
        sale_type = st.radio("💳 جۆری فرۆشتن هەڵبژێرە:", ["کاش (Cash)", "قەرز (Credit)"])
        customer_name = ""
        customer_phone = ""
        
        if sale_type == "قەرز (Credit)":
            customer_name = st.text_input("👤 ناوی کڕیار (قەرزدار)")
            customer_phone = st.text_input("📞 ژمارەی مۆبایلی کڕیار")
        
        if st.button("✅ تەواوکردنی پرۆسەی فرۆشتن"):
            if sale_type == "قەرز (Credit)" and not customer_name:
                st.warning("⚠️ تکایە ناوی کڕیار بنووسە بۆ فرۆشتنی قەرز!")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                items_str = ", ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.cart])
                c_name = customer_name if customer_name else "کاشی گشتی"
                
                # تۆمارکردن لە خشتەی فرۆشتن
                cursor.execute("INSERT INTO sales (date, items, total_amount, total_profit, sale_type, customer_name) VALUES (?, ?, ?, ?, ?, ?)",
                               (date_str, items_str, cart_total, cart_profit, sale_type, c_name))
                
                # ئەگەر قەرز بوو، با لە خشتەی قەرزەکانیش تۆمار بکرێت
                if sale_type == "قەرز (Credit)":
                    cursor.execute("INSERT INTO debts (customer_name, phone, total_debt, date, status) VALUES (?, ?, ?, ?, ?)",
                                   (c_name, customer_phone, cart_total, date_str, "قەرزدار"))
                
                conn.commit()
                st.success("🎉 فرۆشتنەکە بە سەرکەوتوویی تۆمار کراوە!")
                
                if sale_type == "قەرز (Credit)":
                    st.info(f"📌 بڕی {cart_total:,.0f} IQD بە ناوی ({c_name})ـەوە وەکو قەرز تۆمار کرا.")
                
                st.session_state.cart = []
    else:
        st.info("ℹ️ سەبەتە خاڵییە. بارکۆدی کاڵایەک سکان بکە یان لێرە دەركەوێت.")

# 2. بەشی زیادکردنی کاڵا
elif menu == "زیادکردنی کاڵا":
    st.header("📦 بەڕێوەبردن و زیادکردنی کاڵا")
    
    with st.form("add_product_form", clear_on_submit=True):
        scanned_barcode = st.text_input("📌 بارکۆدی کاڵا (سکان یان بنووسە)")
        name = st.text_input("🏷️ ناوی تەواوی کاڵا")
        cost_price = st.number_input("💸 نرخی کڕین (Cost Price)", min_value=0.0, step=250.0)
        sell_price = st.number_input("💰 نرخی فرۆشتن (Sell Price)", min_value=0.0, step=250.0)
        
        submit = st.form_submit_button("💾 تۆمارکردنی کاڵای نوێ")
        
        if submit:
            if scanned_barcode and name:
                try:
                    cursor.execute("INSERT INTO products (barcode, name, cost_price, sell_price) VALUES (?, ?, ?, ?)",
                                   (scanned_barcode.strip(), name, cost_price, sell_price))
                    conn.commit()
                    st.success(f"کاڵای '{name}' بە سەرکەوتوویی تۆمار کرا.")
                except sqlite3.IntegrityError:
                    st.error("❌ هەڵە! ئەم بارکۆدە پێشتر لە سیستەمدا هەیە.")
            else:
                st.warning("⚠️ تکایە بارکۆد و ناوی کاڵا پڕ بکەرەوە.")

    st.markdown("---")
    st.subheader("📋 لیستی کاڵاکانی بەردەست")
    cursor.execute("SELECT barcode, name, cost_price, sell_price FROM products")
    all_products = cursor.fetchall()
    
    if all_products:
        for p in all_products:
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
            col1.write(`{p[0]}`)
            col2.write(f"**{p[1]}**")
            col3.write(f"کڕین: {p[2]:,.0f}")
            col4.write(f"فرۆشتن: {p[3]:,.0f}")
            if col5.button("🗑️", key=f"del_p_{p[0]}"):
                cursor.execute("DELETE FROM products WHERE barcode = ?", (p[0],))
                conn.commit()
                st.rerun()

# 3. بەشی ڕاپۆرتی داهات و قازانج
elif menu == "ڕاپۆرتی داهات و قازانج":
    st.header("📊 داشبۆردی داهات و قازانج")
    
    cursor.execute("SELECT SUM(total_amount), SUM(total_profit) FROM sales")
    total_sales, total_profit = cursor.fetchone()
    
    total_sales = total_sales if total_sales else 0.0
    total_profit = total_profit if total_profit else 0.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 کۆی گشتی داهات", f"{total_sales:,.0f} IQD")
    with col2:
        st.metric("📈 کۆی گشتی قازانج", f"{total_profit:,.0f} IQD")
    
    st.markdown("---")
    st.subheader("📑 مێژووی فرۆشتنەکان")
    cursor.execute("SELECT id, date, items, total_amount, sale_type, customer_name FROM sales ORDER BY id DESC")
    sales_history = cursor.fetchall()
    
    if sales_history:
        for s in sales_history:
            st.write(f"🔹 **پسوولە #{s[0]}** | جۆر: **{s[4]}** | کڕیار: **{s[5]}** | گشتی: **{s[3]:,.0f} IQD** | کات: {s[1]}")
            st.text(f"   کاڵاکان: {s[2]}")
            st.markdown("---")
    else:
        st.info("ℹ️ هیچ فرۆشتنێک تۆمار نەکراوە.")

# 4. بەشی بەڕێوەبردنی قەرزەکان
elif menu == "بەڕێوەبردنی قەرزەکان":
    st.header(" دفتر قەرزەکان (Debt Management)")
    
    cursor.execute("SELECT id, customer_name, phone, total_debt, date, status FROM debts WHERE status = 'قەرزدار'")
    debts_list = cursor.fetchall()
    
    if debts_list:
        st.warning("⚠️ لیستی ئەو کەسانەی کە قەرزدارن:")
        for d in debts_list:
            debt_id, c_name, c_phone, c_debt, d_date, status = d
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            col1.write(f"👤 **{c_name}** (مۆبایل: {c_phone})")
            col2.write(f"💰 بڕی قەرز: **{c_debt:,.0f} IQD**")
            col3.write(f"📅 ڕێکەوت: {d_date}")
            
            if col4.button("💵 تسویە/پێدانەوە", key=f"pay_debt_{debt_id}"):
                cursor.execute("UPDATE debts SET status = 'دراوە' WHERE id = ?", (debt_id,))
                conn.commit()
                st.success(f"قەرزی ({c_name}) بە سەرکەوتوویی درایەوە!")
                st.rerun()
            st.markdown("---")
    else:
        st.success("✅ هیچ قەرزێکی هەڵواسراو نییە! هەموو کڕیارەکان پاکن.")
