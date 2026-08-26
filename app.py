import streamlit as st
from datetime import datetime
import sqlite3

# ڕێکخستنی پەڕەی وێب
st.set_page_config(page_title="Anas Market - POS", page_icon="🛒", layout="wide")

# دروستکردن یان بەستنەوە بە داتابەیس
def init_db():
    conn = sqlite3.connect("market.db", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            qty INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            total_amount REAL NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'قەرز'
        )
    ''')
    conn.commit()

    # زانیاری سەرەتایی ئەگەر داتابەیسەکە بەتاڵ بێت
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        initial_data = [
            ("6291001", "شیر (1 ליטר)", 1000, 50),
            ("6291002", "پەنیر (كيلۆ)", 4000, 30),
            ("6291003", "نان (سەموون)", 250, 200),
            ("6291004", "ئاو (پەداوی)", 500, 150),
            ("6291005", "ماست (گۆلا)", 1250, 40)
        ]
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", initial_data)
        conn.commit()
    return conn

conn = init_db()
cursor = conn.cursor()

# بەڕێوەبردنی سەبەتە لە Session Stateـی وێب ئەپەکەدا
if 'cart' not in st.session_state:
    st.session_state.cart = []

# سەرۆکی وێب ئەپ
st.markdown("<h1 style='text-align: center; color: #16a34a;'>🛒 Anas Market - POS System</h1>", unsafe_allow_html=True)
st.divider()

# بەشی لاوەکی (Sidebar) بۆ کارەکان (زیادکردنی کاڵا و قەرزەکان)
st.sidebar.markdown("### ⚙️ بەڕێوەبردنی مارکێت")
menu = st.sidebar.selectbox("هەڵبژاردەی بەش", ["فرۆشتن (POS)", "زیادکردنی کاڵای نوێ", "بەشی قەرزەکان"])

# 1. بەشی فرۆشتن
if menu == "فرۆشتن (POS)":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📦 هەڵبژاردنی کاڵا")
        cursor.execute("SELECT barcode, name, price, qty FROM products")
        products = cursor.fetchall()
        
        # دروستکردنی لیستی کاڵاکان بۆ هەڵبژاردن
        product_options = {f"{p[1]} - نرخی: {p[2]} IQD (مایە: {p[3]})": p for p in products}
        selected_prod_name = st.selectbox("کاڵا ببژێرە یان بارکۆد بنووسە", options=list(product_options.keys()))
        
        if st.button("➕ زیادکردن بۆ سەبەتە", use_container_width=True):
            p = product_options[selected_prod_name]
            code, name, price, store_qty = p[0], p[1], p[2], p[3]
            
            if store_qty > 0:
                # کەمکردنەوەی دانە لە داتابەیس
                cursor.execute("UPDATE products SET qty = ? WHERE barcode = ?", (store_qty - 1, code))
                conn.commit()

                # زیادکردن بۆ سەبەتەی کڕین
                found = False
                for item in st.session_state.cart:
                    if item["code"] == code:
                        item["qty"] += 1
                        item["total"] = item["qty"] * price
                        found = True
                        break
                if not found:
                    st.session_state.cart.append({
                        "code": code, "name": name, "price": price, "qty": 1, "total": price
                    })
                st.success(f"({name}) زیاد کرا!")
                st.rerun()
            else:
                st.error("❌ ئەم کاڵایە لە کۆگا تەواو بووە!")

    with col2:
        st.markdown("### 🛒 سەبەتەی کڕین")
        if not st.session_state.cart:
            st.info("سەبەتە بەتاڵە")
        else:
            grand_total = 0
            for i, item in enumerate(st.session_state.cart):
                st.write(f"**{item['name']}**")
                st.write(f"بڕ: {item['qty']} | نرخ: {item['total']:,} IQD")
                if st.button(f"❌ لادان {item['name']}", key=f"del_{i}"):
                    # گەڕاندنەوەی بڕەکە بۆ کۆگا
                    cursor.execute("UPDATE products SET qty = qty + ? WHERE barcode = ?", (item['qty'], item['code']))
                    conn.commit()
                    st.session_state.cart.pop(i)
                    st.rerun()
                grand_total += item['total']
                st.divider()

            st.markdown(f"### 💵 کۆی گشتی: {grand_total:,} IQD")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💵 پارەدان (Cash)", use_container_width=True):
                    st.success("✅ پرۆسەی فرۆشتن بە سەرکەوتوویی ئەنجام درا!")
                    st.session_state.cart = []
                    st.rerun()
            with col_b:
                if st.button("📝 قەرز", use_container_width=True):
                    st.session_state.checkout_debt_mode = True

            if st.session_state.get("checkout_debt_mode", False):
                debt_name = st.text_input("ناوی کەسی قەرزدار:")
                if st.button("تۆمارکردنی قەرز"):
                    if debt_name:
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                        cursor.execute("INSERT INTO debts (customer_name, total_amount, date) VALUES (?, ?, ?)", 
                                       (debt_name, grand_total, current_date))
                        conn.commit()
                        st.success("قەرزەکە بە سەرکەوتوویی تۆمار کرا!")
                        st.session_state.cart = []
                        st.session_state.checkout_debt_mode = False
                        st.rerun()

# 2. بەشی زیادکردنی کاڵای نوێ
elif menu == "زیادکردنی کاڵای نوێ":
    st.markdown("### ➕ ناساندنی کاڵای نوێ بۆ کۆگا")
    with st.form("add_product_form"):
        bc = st.text_input("بارکۆد")
        name = st.text_input("ناوی کاڵا")
        price = st.number_input("نرخ (IQD)", min_value=0.0, step=500.0)
        qty = st.number_input("بڕی کۆگا (دانە)", min_value=0, step=1)
        
        submit = st.form_submit_button("💾 پاشەکەوتکردن")
        if submit:
            if bc and name:
                try:
                    cursor.execute("INSERT INTO products VALUES (?, ?, ?, ?)", (bc, name, price, qty))
                    conn.commit()
                    st.success("کاڵاکە بە سەرکەوتوویی زیاد کرا!")
                except sqlite3.IntegrityError:
                    st.error("❌ ئەم بارکۆدە پێشتر بوونی هەیە!")
            else:
                st.warning("تکایە خانەکان پڕ بکەرەوە.")

# 3. بەشی قەرزەکان
elif menu == "بەشی قەرزەکان":
    st.markdown("### 👥 لیستی قەرزدارەکان")
    cursor.execute("SELECT id, customer_name, total_amount, date, status FROM debts")
    debts = cursor.fetchall()
    
    if not debts:
        st.info("هیچ قەرزێک تۆمار نەکراوە.")
    else:
        for d in debts:
            st.write(id)
            st.info(f"👤 **ناو:** {d[1]}  |  💰 **بڕ:** {d[2]:,} IQD  |  📅 **بەروار:** {d[3]}")
            if st.button(f"✅ دانەوەی قەرزی {d[1]} (سڕینەوە)", key=f"pay_{d[0]}"):
                cursor.execute("DELETE FROM debts WHERE id = ?", (d[0],))
                conn.commit()
                st.success("قەرزەکە درایەوە!")
                st.rerun()
