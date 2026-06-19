import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

query = "SELECT * FROM products"
df = pd.read_sql_query(query, conn)

st.title("Inventory Automation System")

st.set_page_config(
    page_title="Inventory Automation System",
    layout="wide"
)

# search/filter
search = st.text_input("Search Product")

filtered_df = df.copy()

if search:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search, case=False)
    ]

categories = ["All"] + list(df["category"].unique())

selected_category = st.selectbox(
    "Category",
    categories
)

# Charts
st.subheader("Stock by Category")

category_stock = df.groupby("category")["stock"].sum()

st.bar_chart(category_stock)

# download CSV
csv = filtered_df.to_csv(index=False)

st.download_button(
    "Download Inventory CSV",
    csv,
    "inventory.csv",
    "text/csv"
)

# sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "📦 Inventory",
        "🔄 Stock Movement",
        "🚚 Suppliers"
    ]
)

# KPI
total_products = len(df)

total_units = df["stock"].sum()

low_stock_count = len(df[df["stock"] <= df["reorder_level"]])

inventory_value = (df["stock"] * df["unit_cost"]).sum()

# show KPI on UI
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Products", total_products)

with col2:
    st.metric("Total Units", total_units)

with col3:
    st.metric("Low Stock", low_stock_count)

with col4:
    st.metric("Inventory Value", f"{inventory_value:,.0f}")

# Add product
st.subheader("Add Product")

st.subheader("Stock Movement")

selected_product = st.selectbox(
    "Seclect Product",
    df["name"]
)

qty = st.number_input("Quantity", min_value=1)

selected_row = df[df["name"] == selected_product]

current_stock = int(selected_row.iloc[0]["stock"].item())
qty = int(qty)

st.write(current_stock)

# stock in
if st.button("Stock in"):
    new_stock = int(current_stock + qty)
    product_id = int(selected_row.iloc[0]["id"].item())

    cursor.execute("""
        UPDATE products
        SET stock = ?
        WHERE id = ?
    """, (new_stock, product_id))

    conn.commit()

    cursor.execute("""
        INSERT INTO stock_movements (
            product_id,
            movement_type,
            quantity,
            timestamp
        )
        VALUES (?, ?, ?, datetime('now'))
    """, (
        product_id,
        "IN",
        qty
    ))

    conn.commit()

    cursor.execute("SELECT * FROM stock_movements")
    print(cursor.fetchall())

    cursor.execute(
        "SELECT id, name, stock FROM products WHERE id = ?",
        (product_id,)
    )
    print(cursor.fetchone())

    st.success("Stock updated!")
    df = pd.read_sql_query("SELECT * FROM products", conn)

# stock out
if st.button("Stock Out"):
    new_stock = int(current_stock - qty)
    product_id = int(selected_row.iloc[0]["id"])

    if qty > current_stock:
        st.error("⚠️ Insufficient stock")

    else:
        cursor.execute("""
        UPDATE products 
        SET stock = ?
        WHERE id = ?
        """, (new_stock, product_id))

        cursor.execute("""
            INSERT INTO stock_movements (
                product_id,
                movement_type,
                quantity,
                timestamp
            )
            VALUES (?, ?, ?, datetime('now'))
        """, (
            product_id,
            "OUT",
            qty
        ))

        conn.commit()
        st.success("Stock updated!")

# product
name = st.text_input("Product Name")
category = st.text_input("Category")
stock = st.number_input("Stock", min_value=0)
unit_cost = st.number_input("Unit Cost", min_value=0)
selling_price = st.number_input("Selling Price", min_value=0)
reorder_level = st.number_input("Reorder Level", min_value=0)
supplier = st.text_input("Supplier")

if st.button("Add Product"):

    if not name or not category or not supplier:
        st.error("Please fill all required fields")
    else:
        if selling_price <= unit_cost:
            st.warning("⚠️Suspicious business")

        cursor.execute("""
            INSERT INTO products (
                name,
                category,
                stock,
                unit_cost,
                selling_price,
                reorder_level,
                supplier
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(name),
            str(category),
            int(stock),
            float(unit_cost),
            float(selling_price),
            int(reorder_level),
            str(supplier)
        ))

        conn.commit()

        df = pd.read_sql_query("SELECT * FROM products", conn)

        st.success("Product added!")

# edit / delete
st.subheader("Edit / Delete Product")

selected_edit_product = st.selectbox(
    "Select Product to Edit",
    df["name"],
    key="edit_product"
)

edit_row = df[df["name"] == selected_edit_product]

product = edit_row.iloc[0]

edit_name = st.text_input(
    "Product Name",
    value=product["name"],
    key="edit_name"
)

edit_category = st.text_input(
    "Category",
    value=product["category"],
    key="edit_category"
)

edit_stock = st.number_input(
    "Stock",
    min_value=0,
    value=int(product["stock"]),
    key="edit_stock"
)

edit_unit_cost = st.number_input(
    "Unit Cost",
    min_value=0,
    value=int(product["unit_cost"]),
    key="edit_cost"
)

edit_selling_price = st.number_input(
    "Selling Price",
    min_value=0,
    value=int(product["selling_price"]),
    key="edit_price"
)

edit_reorder = st.number_input(
    "Reorder Level",
    min_value=0,
    value=int(product["reorder_level"]),
    key="edit_reorder"
)

edit_supplier = st.text_input(
    "Supplier",
    value=product["supplier"],
    key="edit_supplier"
)

if st.button("Save Changes"):
    product_id = int(product["id"])

    cursor.execute("""
        UPDATE products
        SET
            name = ?,
            category = ?,
            stock = ?,
            unit_cost = ?,
            selling_price = ?,
            reorder_level = ?,
            supplier = ?
        WHERE id = ?
    """, (
        edit_name,
        edit_category,
        edit_stock,
        edit_unit_cost,
        edit_selling_price,
        edit_reorder,
        edit_supplier,
        product_id
    ))

    conn.commit()

    df = pd.read_sql_query("SELECT * FROM products", conn)

    st.success("Product updated!")

    cursor.execute(
        "SELECT name, stock FROM products WHERE id = ?",
        (product_id,)
    )
    print(cursor.fetchone())

# Delete
confirm_delete = st.checkbox("Confirm delete")

if st.button("Delete Product"):
    if confirm_delete:
        product_id = int(product["id"])

        cursor.execute("""
            DELETE FROM products
            WHERE id = ?
        """, (product_id,))

        conn.commit()
        st.success("Product deleted!")
        st.rerun()
    else:
        st.warning("Please confirm deletion")

# low stock
low_stock_df = df[df["stock"] <= df["reorder_level"]].copy()

st.subheader("Low Stock Alert")

if not low_stock_df.empty:
    st.warning("⚠️ Products need reorder")
    st.dataframe(low_stock_df)

else:
    st.success("All products healthy")

low_stock_df["reorder_qty"] = (
        low_stock_df["reorder_level"] - low_stock_df["stock"]
)

for _, row in low_stock_df.iterrows():
    st.write(
        f"Reorder {row['reorder_qty']} units of {row['name']}"
    )

st.subheader("Supplier Dashboard")

supplier_df = low_stock_df[
    ["supplier", "name", "stock", "reorder_level", "reorder_qty"]
]

st.dataframe(supplier_df)

supplier_summary = low_stock_df.groupby("supplier")["reorder_qty"].sum()

for _, row in low_stock_df.iterrows():
    st.write(
        f"Call {row['supplier']} for "
        f"{row['reorder_qty']} units of {row['name']}"
    )

st.dataframe(
    low_stock_df[
        ["name", "stock", "reorder_level", "reorder_qty"]
    ]
)

st.dataframe(df)

st.subheader("Stock Movement History")

movement_df = pd.read_sql_query("""
    SELECT
        sm.id,
        p.name,
        sm.movement_type,
        sm.quantity,
        sm.timestamp
    FROM stock_movements sm
    JOIN products p
    ON sm.product_id = p.id
    ORDER BY sm.id DESC
""", conn)

st.dataframe(movement_df)

conn.close()
