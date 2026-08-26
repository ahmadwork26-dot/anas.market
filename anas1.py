import streamlit as st
from datetime import datetime
import sqlite3

# ڕێکخستنی پەڕەی وێب و بەکارهێنانی ڕوکاری مۆدێرن
st.set_page_config(page_title="Anas Market - Modern POS", page_icon="⚡", layout="wide")

# CSS ی تایبەت بۆ گۆڕینی ڕوکار بۆ شێوازێکی مۆدێرن و تاریک (Dark & Modern Theme)
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
            total_profit REAL
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# سەردێڕی سەرەکی مۆدێرن
st.title("⚡ Anas Market - POS System")
st.markdown("---")

# مێنوی لاوەکی سەردەمیانە
menu = st.sidebar.selectbox("🎯 بەشی بەڕێوەبردن", ["فرۆشتن (POS)", "زیادکردنی کاڵا", "ڕاپۆرتی داهات و قازانج"])

# 1. بەشی فرۆشتن
if menu == "فرۆشتن (POS)":
    st.header("💳 خاڵی فرۆشتنی خێرا (POS)")
    
    cursor.execute("SELECT barcode, name, sell_price FROM products")
    products = cursor.fetchall()
    
    if not products:
        st.warning("⚠️ هیچ کاڵایەک لە سیستەمدا نییە! سەرەتا لە بەشی 'زیادکردنی کاڵا' کاڵا زیاد بکە.")
    else:
        product_dict = {f"{p[1]} ➔ (نرخ: {p[2]:,.0f} IQD)": p for p in products}
        selected_product_str = st.selectbox("🔍 گەڕان یان هەڵبژاردنی کاڵا", list(product_dict.keys()))
        
        selected_p = product_dict[selected_product_str]
        barcode, name, sell_price = selected_p
        
        qty = st.number_input("📦 دانە / بڕ", min_value=1, value=1, step=1)
        
        if "cart" not in st.session_state:
            st.session_state.cart = []
            
        if st.button("➕ زیادکردن بۆ سەبەتە"):
            st.session_state.cart.append({
                "barcode": barcode,
                "name": name,
                "price": sell_price,
                "qty": qty,
                "total": sell_price * qty
            })
            st.success(f"'{name}' زیاد کرا بۆ سەبەتە.")
            
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
                cost = cursor.fetchone()[0]
                item_profit = (item['price'] - cost) * item['qty']
                cart_profit += item_profit
                cart_total += item['total']
                
                if col4.button("❌", key=f"del_{index}"):
                    st.session_state.cart.pop(index)
                    st.rerun()
                    
            st.markdown("---")
            st.markdown(f"### 💎 کۆی گشتی پارە: **{cart_total:,.0f} IQD**")
            
            if st.button("✅ تەواوکردنی فرۆشتن و چاپکردنی پسوولە"):
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                items_str = ", ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.cart])
                
                cursor.execute("INSERT INTO sales (date, items, total_amount, total_profit) VALUES (?, ?, ?, ?)",
                               (date_str, items_str, cart_total, cart_profit))
                conn.commit()
                
                st.success("🎉 فرۆشتنەکە بە سەرکەوتوویی تۆمار کراوە!")
                st.markdown("---")
                st.markdown("### 🧾 پسوولەی فەرمی (Official Receipt)")
                st.text(f"--- Anas Market ---\nکات: {date_str}\n----------------------------------")
                for item in st.session_state.cart:
                    st.text(f"• {item['name']} | بڕ: {item['qty']} | گشتی: {item['total']:,.0f} IQD")
                st.text("----------------------------------")
                st.text(f"کۆی گشتی: {cart_total:,.0f} IQD\nسوپاس بۆ متمانەتان!")
                
                st.session_state.cart = []

# 2. بەشی زیادکردنی کاڵا
elif menu == "زیادکردنی کاڵا":
    st.header("📦 بەڕێوەبردن و زیادکردنی کاڵا")
    
    with st.form("add_product_form", clear_on_submit=True):
        barcode = st.text_input("📌 بارکۆدی کاڵا (Barcode)")
        name = st.text_input("🏷️ ناوی تەواوی کاڵا")
        cost_price = st.number_input("💸 نرخی کڕین (Cost Price)", min_value=0.0, step=250.0)
        sell_price = st.number_input("💰 نرخی فرۆشتن (Sell Price)", min_value=0.0, step=250.0)
        
        submit = st.form_submit_button("💾 تۆمارکردنی کاڵای نوێ")
        
        if submit:
            if barcode and name:
                try:
                    cursor.execute("INSERT INTO products (barcode, name, cost_price, sell_price) VALUES (?, ?, ?, ?)",
                                   (barcode, name, cost_price, sell_price))
                    conn.commit()
                    st.success(f"کاڵای '{name}' بە سەرکەوتوویی تۆمار کرا.")
                except sqlite3.IntegrityError:
                    st.error("❌ هەڵە! ئەم بارکۆدە پێشتر لە سیستەمدا هەیە.")
            else:
                st.warning("⚠️ تکایە خانەکان بە تەواوی پڕ بکەرەوە.")

    st.markdown("---")
    st.subheader("📋 لیستی کاڵاکانی بەردەست")
    cursor.execute("SELECT barcode, name, cost_price, sell_price FROM products")
    all_products = cursor.fetchall()
    
    if all_products:
        for p in all_products:
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
            col1.write(f"`{p[0]}`")
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
    st.subheader("📑 مێژووی پسوولە فرۆشراوەکان")
    cursor.execute("SELECT id, date, items, total_amount, total_profit FROM sales ORDER BY id DESC")
    sales_history = cursor.fetchall()
    
    if sales_history:
        for s in sales_history:
            with st.expander(f"پسوولە #{s[0]} ➔ کات: {s[1]} ➔ کۆ: {s[3]:,.0f} IQD"):
                st.write(f"**کاڵاکان:** {s[2]}")
                st.write(f"**کۆی گشتی:** {s[3]:,.0f} IQD")
                st.write(f"**قازانجی پاک:** {s[4]:,.0f} IQD")
    else:
        st.info("ℹ️ هیچ فرۆشتنێک تا ئێستا تۆمار نەکراوە.")

