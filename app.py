#=================
#   Libraries
#=================
from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
from supabase import create_client
import os
from flask import jsonify, request
from datetime import datetime
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
def is_logged_in():
    return "user" in session
@app.route("/")
def home():
    return redirect("/dashboard") if is_logged_in() else redirect("/login")
# ==============================
# LOGIN
# ==============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            auth = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if not auth.user:
                return render_template("login.html",
                                       error="Invalid email or password.")
            # Save session
            session["user"] = auth.user.id
            session["email"] = auth.user.email
            return redirect("/dashboard")
        except Exception:
            return render_template("login.html",
                                   error="Invalid email or password.")
    return render_template("login.html")
# ==============================
# SIGNUP
# ==============================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            auth = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            if not auth.user:
                return render_template("signup.html",
                                       error="Check your email for confirmation.")
            # ❌ DO NOT INSERT INTO users TABLE
            # Trigger will handle it automatically
            return redirect("/login")
        except Exception as e:
            return render_template("signup.html",
                                   error=str(e))
    return render_template("signup.html")
#========================
#   LOGOUT
#========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# ==============================
# USER MANAGEMENT
# ==============================
@app.route("/users")
def users_page():
    if not is_logged_in():
        return redirect("/login")
    # Only admin can view
    current_user = session["user"]
    user_data = supabase.table("users") \
        .select("*") \
        .eq("id", current_user) \
        .single() \
        .execute()
    if user_data.data["role"] != "admin":
        return "Access Denied", 403
    users = supabase.table("users") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    return render_template("users.html", users=users.data)
@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    if not is_logged_in():
        return redirect("/login")
    # Delete from users table (will cascade delete auth)
    supabase.table("users").delete().eq("id", user_id).execute()
    return redirect("/users")
# ==============================
# DASHBOARD 
# ==============================
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/login")
    # =========================
    # TOTAL SALES (Manual POS)
    # =========================
    sales_res = supabase.table("manual_pos_sales") \
        .select("total_amount", count="exact") \
        .execute()
    total_sales = 0
    if sales_res.data:
        total_sales = sum(float(s["total_amount"]) for s in sales_res.data)
    # =========================
    # TOTAL EXPENSES
    # =========================
    expense_res = supabase.table("expenses") \
        .select("amount") \
        .execute()
    total_expenses = 0
    if expense_res.data:
        total_expenses = sum(float(e["amount"]) for e in expense_res.data)
    # =========================
    # LOW STOCK ITEMS
    # =========================
    stock_res = supabase.table("stock_products") \
        .select("*") \
        .execute()

    low_stock_count = 0
    if stock_res.data:
        for item in stock_res.data:
            if float(item["quantity"]) <= float(item["low_stock_limit"]):
                low_stock_count += 1

    # =========================
    # NET PROFIT
    # =========================
    net_profit = total_sales - total_expenses

    return render_template(
        "dashboard.html",
        email=session["email"],
        total_sales=total_sales,
        total_expenses=total_expenses,
        net_profit=net_profit,
        low_stock_count=low_stock_count
    )
# ==============================
# MANUAL POS MODULE
# ==============================
def generate_invoice_number():
    response = supabase.table("manual_pos_sales").select("id", count="exact").execute()
    count = response.count if response.count else 0
    return f"INV-{1001 + count}"
@app.route("/pos")
def pos():
    if not is_logged_in():
        return redirect("/login")
    invoice_number = generate_invoice_number()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("pos.html",
                           invoice_number=invoice_number,
                           current_datetime=current_datetime)
@app.route("/save_pos", methods=["POST"])
def save_pos():
    if not is_logged_in():
        return jsonify({"status": "error"})
    data = request.json
    invoice_number = generate_invoice_number()
    sale_data = {
        "invoice_number": invoice_number,
        "customer_name": data.get("customer_name"),
        "customer_phone": data.get("customer_phone"),
        "subtotal": float(data["subtotal"]),
        "gst_percentage": float(data["gst_percentage"]),
        "gst_amount": float(data["gst_amount"]),
        "discount": float(data["discount"]),
        "total_amount": float(data["grand_total"]),
        "payment_method": data["payment_method"],
        "paid_amount": float(data["paid_amount"]),
        "change_amount": float(data["change"])
    }
    sale = supabase.table("manual_pos_sales").insert(sale_data).execute()
    sale_id = sale.data[0]["id"]
    for item in data["items"]:
        supabase.table("manual_pos_items").insert({
            "sale_id": sale_id,
            "item_name": item["name"],
            "quantity": float(item["qty"]),
            "price": float(item["price"]),
            "total": float(item["total"])
        }).execute()
    return jsonify({"status": "success"})
# ==============================
# STOCK MODULE 
# ==============================
@app.route("/stock")
def stock():
    if not is_logged_in():
        return redirect("/login")
    products = supabase.table("stock_products").select("*").order("created_at", desc=True).execute()
    # Calculate total value per product
    for p in products.data:
        p["total_value"] = float(p["quantity"]) * float(p["cost_price"])
    return render_template("stock.html",
                           products=products.data)
#-----------------------
#add product in stock
#-----------------------
@app.route("/add_product", methods=["POST"])
def add_product():
    if not is_logged_in():
        return jsonify({"status": "error"})
    data = request.json
    product_name = data["product_name"].strip()
    category = data["category"]
    unit_type = data["unit_type"]
    cost_price = float(data["cost_price"])
    selling_price = float(data["selling_price"])
    quantity = float(data["quantity"])
    # 🔍 Check if product already exists (case-insensitive)
    existing = supabase.table("stock_products") \
        .select("*") \
        .ilike("product_name", product_name) \
        .eq("unit_type", unit_type) \
        .execute()
    if existing.data:
        # ✅ Update quantity
        product = existing.data[0]
        new_quantity = float(product["quantity"]) + quantity
        supabase.table("stock_products") \
            .update({
                "quantity": new_quantity,
                "cost_price": cost_price,
                "selling_price": selling_price
            }) \
            .eq("id", product["id"]) \
            .execute()
    else:
        # ✅ Insert new product
        supabase.table("stock_products").insert({
            "product_name": product_name,
            "category": category,
            "unit_type": unit_type,
            "cost_price": cost_price,
            "selling_price": selling_price,
            "quantity": quantity,
            "low_stock_limit": 10
        }).execute()
    return jsonify({"status": "success"})
#--------------------
#update stock product
#--------------------
@app.route("/update_product/<id>", methods=["POST"])
def update_product(id):
    if not is_logged_in():
        return jsonify({"status": "error"})
    data = request.json
    supabase.table("stock_products").update({
        "cost_price": float(data["cost_price"]),
        "selling_price": float(data["selling_price"]),
        "quantity": float(data["quantity"])
    }).eq("id", id).execute()
    return jsonify({"status": "success"})
@app.route("/delete_product/<id>")
def delete_product(id):
    if not is_logged_in():
        return redirect("/login")
    supabase.table("stock_products").delete().eq("id", id).execute()
    return redirect("/stock")
# ==============================
# SALES MODULE 
# ==============================
def generate_sale_invoice():
    response = supabase.table("sales").select("id", count="exact").execute()
    count = response.count if response.count else 0
    return f"SALE-{1001 + count}"
@app.route("/sales")
def sales():
    if not is_logged_in():
        return redirect("/login")
    invoice_number = generate_sale_invoice()
    # ✅ FIXED: Correct table name
    products = supabase.table("stock_products") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute().data
    return render_template("sales.html",
                           invoice_number=invoice_number,
                           products=products)
@app.route("/complete_sale", methods=["POST"])
def complete_sale():
    if not is_logged_in():
        return jsonify({"status": "error"})
    data = request.json
    invoice_number = generate_sale_invoice()
    sale_data = {
        "invoice_number": invoice_number,
        "customer_name": data.get("customer_name"),
        "customer_phone": data.get("customer_phone"),
        "subtotal": float(data["subtotal"]),
        "gst_percentage": float(data["gst_percentage"]),
        "gst_amount": float(data["gst_amount"]),
        "discount": float(data["discount"]),
        "total_amount": float(data["grand_total"]),
        "payment_method": data["payment_method"],
        "paid_amount": float(data["paid_amount"]),
        "change_amount": float(data["change"])
    }
    # Insert sale
    sale = supabase.table("sales").insert(sale_data).execute()
    sale_id = sale.data[0]["id"]
    # Save items + update stock
    for item in data["items"]:
        # Insert sale item
        supabase.table("sale_items").insert({
            "sale_id": sale_id,
            "stock_id": item["stock_id"],  # UUID supported
            "quantity": float(item["qty"]),
            "price": float(item["price"]),
            "total": float(item["total"])
        }).execute()

        # ✅ FIXED: Get stock from stock_products table
        stock_item = supabase.table("stock_products") \
            .select("quantity") \
            .eq("id", item["stock_id"]) \
            .single() \
            .execute()

        current_qty = float(stock_item.data["quantity"])
        new_qty = current_qty - float(item["qty"])

        # Prevent negative stock
        if new_qty < 0:
            return jsonify({
                "status": "error",
                "message": "Insufficient stock!"
            })

        # ✅ FIXED: Update correct table
        supabase.table("stock_products") \
            .update({"quantity": new_qty}) \
            .eq("id", item["stock_id"]) \
            .execute()

    return jsonify({"status": "success"})
# ==============================
# SALE RETURN MODULE (FINAL CLEAN VERSION
# ==============================

# Generate Return Invoice Number
def generate_return_invoice():
    response = supabase.table("sale_returns") \
        .select("id", count="exact") \
        .execute()

    count = response.count if response.count else 0
    return f"RET-{1001 + count}"


# ==============================
# SALE RETURN PAGE
# ==============================
@app.route("/sale_return")
def sale_return():
    if not is_logged_in():
        return redirect("/login")
    return render_template("sale_return.html")


# ==============================
# SEARCH SALE BY INVOICE
# ==============================
@app.route("/search_sale", methods=["POST"])
def search_sale():
    try:
        if not is_logged_in():
            return jsonify({"status": "error", "message": "Unauthorized"})

        invoice = request.json.get("invoice")

        if not invoice:
            return jsonify({"status": "error", "message": "Invoice required"})

        # Get Sale
        sale_res = supabase.table("sales") \
            .select("*") \
            .eq("invoice_number", invoice) \
            .execute()

        if not sale_res.data:
            return jsonify({"status": "not_found"})

        sale = sale_res.data[0]
        sale_id = sale["id"]

        # Get Sale Items with product name
        items_res = supabase.table("sale_items") \
            .select("*, stock_products(product_name)") \
            .eq("sale_id", sale_id) \
            .execute()

        items = items_res.data

        # Calculate already returned quantity
        for item in items:
            return_res = supabase.table("sale_return_items") \
                .select("quantity") \
                .eq("sale_item_id", item["id"]) \
                .execute()

            returned_qty = 0
            if return_res.data:
                returned_qty = sum(float(r["quantity"]) for r in return_res.data)

            item["returned_quantity"] = returned_qty
            item["remaining_quantity"] = float(item["quantity"]) - returned_qty

        return jsonify({
            "status": "found",
            "sale": sale,
            "items": items
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ==============================
# COMPLETE RETURN
# ==============================
@app.route("/complete_return", methods=["POST"])
def complete_return():
    try:
        if not is_logged_in():
            return jsonify({"status": "error", "message": "Unauthorized"})

        data = request.json
        sale_id = data.get("sale_id")
        items = data.get("items", [])
        reason = data.get("reason", "")
        refund_method = data.get("refund_method", "Cash")

        if not sale_id:
            return jsonify({"status": "error", "message": "Sale ID missing"})

        if not items:
            return jsonify({"status": "error", "message": "No items selected"})

        return_invoice = generate_return_invoice()

        # Create Sale Return Record
        return_entry = supabase.table("sale_returns").insert({
            "sale_id": sale_id,
            "return_invoice": return_invoice,
            "refund_method": refund_method,
            "reason": reason,
            "total_refund": 0
        }).execute()

        if not return_entry.data:
            return jsonify({"status": "error", "message": "Return creation failed"})

        return_id = return_entry.data[0]["id"]
        total_refund = 0

        # Process Each Item
        for item in items:
            sale_item_id = item["sale_item_id"]
            stock_id = item["stock_id"]
            return_qty = float(item["qty"])
            price = float(item["price"])

            # Get sold quantity
            sold_res = supabase.table("sale_items") \
                .select("quantity") \
                .eq("id", sale_item_id) \
                .execute()

            if not sold_res.data:
                continue

            sold_qty = float(sold_res.data[0]["quantity"])

            # Get already returned quantity
            returned_res = supabase.table("sale_return_items") \
                .select("quantity") \
                .eq("sale_item_id", sale_item_id) \
                .execute()

            already_returned = 0
            if returned_res.data:
                already_returned = sum(float(r["quantity"]) for r in returned_res.data)

            remaining = sold_qty - already_returned

            if return_qty > remaining:
                return jsonify({
                    "status": "error",
                    "message": "Return quantity exceeds remaining limit"
                })

            item_total = return_qty * price
            total_refund += item_total

            # Insert Return Item
            supabase.table("sale_return_items").insert({
                "return_id": return_id,
                "sale_item_id": sale_item_id,
                "stock_id": stock_id,
                "quantity": return_qty,
                "price": price,
                "total": item_total
            }).execute()

            # Update Stock
            stock_res = supabase.table("stock_products") \
                .select("quantity") \
                .eq("id", stock_id) \
                .execute()

            current_stock = float(stock_res.data[0]["quantity"])
            new_stock = current_stock + return_qty

            supabase.table("stock_products") \
                .update({"quantity": new_stock}) \
                .eq("id", stock_id) \
                .execute()

        # Update total refund
        supabase.table("sale_returns") \
            .update({"total_refund": total_refund}) \
            .eq("id", return_id) \
            .execute()

        return jsonify({
            "status": "success",
            "return_invoice": return_invoice,
            "total_refund": total_refund
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
# ==============================
# PURCHASE MODULE (FINAL CLEAN)
# ==============================
def generate_purchase_invoice():
    response = supabase.table("purchases").select("id", count="exact").execute()
    count = response.count if response.count else 0
    return f"PUR-{1001 + count}"

@app.route("/purchase")
def purchase():
    if not is_logged_in():
        return redirect("/login")

    invoice_number = generate_purchase_invoice()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template("purchase.html",
                           invoice_number=invoice_number,
                           current_date=current_date)

@app.route("/complete_purchase", methods=["POST"])
def complete_purchase():
    if not is_logged_in():
        return jsonify({"status": "error"})

    data = request.json
    invoice_number = generate_purchase_invoice()

    supplier_name = data["supplier_name"].strip()
    phone = data["phone"]

    # ✅ Check supplier exists
    supplier_res = supabase.table("suppliers") \
        .select("*") \
        .ilike("supplier_name", supplier_name) \
        .execute()

    if supplier_res.data:
        supplier_id = supplier_res.data[0]["id"]
    else:
        new_supplier = supabase.table("suppliers").insert({
            "supplier_name": supplier_name,
            "phone": phone,
            "opening_balance": 0,
            "total_payable": 0
        }).execute()
        supplier_id = new_supplier.data[0]["id"]
    subtotal = float(data["subtotal"])
    gst_percentage = float(data["gst"])
    tax_amount = float(data["tax_amount"])
    discount = float(data["discount"])
    grand_total = float(data["grand_total"])
    paid_amount = float(data["paid"])
    balance_amount = float(data["balance"])
    payment_method = data["payment_method"]
    # ✅ Insert purchase
    purchase = supabase.table("purchases").insert({
        "purchase_invoice": invoice_number,
        "supplier_id": supplier_id,
        "subtotal": subtotal,
        "tax_percentage": gst_percentage,
        "tax_amount": tax_amount,
        "discount": discount,
        "total_amount": grand_total,
        "paid_amount": paid_amount,
        "balance_amount": balance_amount,
        "payment_method": payment_method
    }).execute()
    purchase_id = purchase.data[0]["id"]
    # ✅ Insert items + update stock
    for item in data["items"]:
        product_name = item["product"]
        category = item["category"]
        unit = item["unit"]
        quantity = float(item["quantity"])
        cost_price = float(item["cost"])
        sell_price = float(item["sell"])
        total = float(item["total"])
        # Insert purchase item
        supabase.table("purchase_items").insert({
            "purchase_id": purchase_id,
            "product_name": product_name,
            "category": category,
            "unit": unit,
            "quantity": quantity,
            "cost_price": cost_price,
            "sell_price": sell_price,
            "total": total
        }).execute()
        # ✅ Update stock_products
        existing = supabase.table("stock_products") \
            .select("*") \
            .ilike("product_name", product_name) \
            .eq("unit_type", unit) \
            .execute()
        if existing.data:
            current_qty = float(existing.data[0]["quantity"])
            new_qty = current_qty + quantity
            supabase.table("stock_products") \
                .update({
                    "quantity": new_qty,
                    "cost_price": cost_price,
                    "selling_price": sell_price
                }) \
                .eq("id", existing.data[0]["id"]) \
                .execute()
        else:
            supabase.table("stock_products").insert({
                "product_name": product_name,
                "category": category,
                "unit_type": unit,
                "cost_price": cost_price,
                "selling_price": sell_price,
                "quantity": quantity,
                "low_stock_limit": 10
            }).execute()
    # ✅ Update supplier payable
    supplier_data = supabase.table("suppliers") \
        .select("total_payable") \
        .eq("id", supplier_id) \
        .execute()
    current_payable = float(supplier_data.data[0]["total_payable"])
    new_payable = current_payable + balance_amount
    supabase.table("suppliers") \
        .update({"total_payable": new_payable}) \
        .eq("id", supplier_id) \
        .execute()
    return jsonify({
        "status": "success",
        "invoice": invoice_number
    })
#======================
# customer detail
#=======================
@app.route("/customers")
def customers():
    if not is_logged_in():
        return redirect("/login")
    customers = supabase.table("customers") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    return render_template("customers.html",
                           customers=customers.data)
@app.route("/customer/<int:id>")
def customer_detail(id):
    if not is_logged_in():
        return redirect("/login")
    customer = supabase.table("customers") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute()
    return render_template("customer_detail.html",
                           customer=customer.data)
# ============================================================
# ================= SUPPLIER MODULE (ADDED ONLY) ============
# ============================================================
@app.route("/suppliers")
def suppliers():
    if not is_logged_in():
        return redirect("/login")
    suppliers = supabase.table("suppliers") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()
    return render_template("suppliers.html",
                           suppliers=suppliers.data)
@app.route("/supplier/<int:id>")
def supplier_detail(id):
    if not is_logged_in():
        return redirect("/login")
    supplier = supabase.table("suppliers") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute()
    return render_template("supplier_detail.html",
                           supplier=supplier.data)
# ============================================================
# ================= HELPER FUNCTION (ALREADY EXISTING) ======
# ============================================================
def get_or_create_customer(name, phone, source, total_amount, paid_amount):
    if not name:
        return None
    existing = supabase.table("customers") \
        .select("*") \
        .ilike("customer_name", name) \
        .execute()
    if existing.data:
        customer = existing.data[0]
        customer_id = customer["id"]
        new_total_purchase = float(customer["total_purchase"]) + total_amount
        new_total_paid = float(customer["total_paid"]) + paid_amount
        new_total_due = new_total_purchase - new_total_paid
        supabase.table("customers").update({
            "total_purchase": new_total_purchase,
            "total_paid": new_total_paid,
            "total_due": new_total_due
        }).eq("id", customer_id).execute()
    else:
        new_customer = supabase.table("customers").insert({
            "customer_name": name,
            "phone": phone,
            "source": source,
            "total_purchase": total_amount,
            "total_paid": paid_amount,
            "total_due": total_amount - paid_amount
        }).execute()
        customer_id = new_customer.data[0]["id"]
    return customer_id
# ==============================
# PURCHASE RETURN MODULE (FINAL CORRECTED)
# ==============================
@app.route("/purchase-return")
def purchase_return():
    if not is_logged_in():
        return redirect("/login")
    return render_template("purchase-return.html")
# -------------------------------
# SEARCH PURCHASE INVOICE
# -------------------------------
@app.route("/search_purchase_invoice", methods=["POST"])
def search_purchase_invoice():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"})
    data = request.json
    invoice = data.get("invoice")
    purchase = supabase.table("purchases") \
        .select("*") \
        .eq("purchase_invoice", invoice) \
        .execute()
    if not purchase.data:
        return jsonify({"error": "Invoice not found"})
    purchase = purchase.data[0]
    supplier = supabase.table("suppliers") \
        .select("*") \
        .eq("id", purchase["supplier_id"]) \
        .execute()
    supplier = supplier.data[0] if supplier.data else {}
    items = supabase.table("purchase_items") \
        .select("*") \
        .eq("purchase_id", purchase["id"]) \
        .execute()

    result_items = []

    for item in items.data:

        stock = supabase.table("stock_products") \
            .select("id, quantity") \
            .ilike("product_name", item["product_name"]) \
            .execute()
        stock_qty = stock.data[0]["quantity"] if stock.data else 0
        stock_id = stock.data[0]["id"] if stock.data else None
        result_items.append({
            **item,
            "stock_quantity": stock_qty,
            "stock_id": stock_id
        })
    return jsonify({
        "purchase": purchase,
        "supplier": supplier,
        "items": result_items
    })
# -------------------------------
# SAVE PURCHASE RETURN
# -------------------------------
@app.route("/save_purchase_return", methods=["POST"])
def save_purchase_return():
    try:
        if not is_logged_in():
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
        purchase_id = data.get("purchase_id")
        supplier_id = data.get("supplier_id")
        items = data.get("items", [])
        refund_method = data.get("refund_method")
        tax_percentage = float(data.get("tax_percentage", 0))
        discount = float(data.get("discount", 0))
        if not items:
            return jsonify({"error": "No items selected"}), 400
        subtotal = 0
        return_invoice = f"PR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return_insert = supabase.table("purchase_returns").insert({
            "return_invoice": return_invoice,
            "purchase_id": purchase_id,
            "supplier_id": supplier_id,
            "refund_method": refund_method,
            "tax_percentage": tax_percentage,
            "discount": discount
        }).execute()
        return_id = return_insert.data[0]["id"]
        for item in items:
            qty = float(item["return_qty"])
            cost = float(item["cost_price"])
            total = qty * cost
            subtotal += total
            # Insert return item
            supabase.table("purchase_return_items").insert({
                "return_id": return_id,
                "purchase_item_id": item["id"],
                "product_name": item["product_name"],
                "quantity": qty,
                "cost_price": cost,
                "total": total
            }).execute()
            # ------------------------------
            # UPDATE RETURNED QUANTITY
            # ------------------------------
            purchase_item = supabase.table("purchase_items") \
                .select("returned_quantity") \
                .eq("id", item["id"]) \
                .execute()
            old_returned = purchase_item.data[0].get("returned_quantity", 0) if purchase_item.data else 0
            new_returned = float(old_returned) + qty
            supabase.table("purchase_items") \
                .update({"returned_quantity": new_returned}) \
                .eq("id", item["id"]) \
                .execute()
            # ------------------------------
            # REDUCE STOCK QUANTITY
            # ------------------------------
            stock = supabase.table("stock_products") \
                .select("quantity") \
                .ilike("product_name", item["product_name"]) \
                .execute()
            if stock.data:
                current_stock = float(stock.data[0]["quantity"])
                new_stock = current_stock - qty
                if new_stock < 0:
                    new_stock = 0
                supabase.table("stock_products") \
                    .update({"quantity": new_stock}) \
                    .ilike("product_name", item["product_name"]) \
                    .execute()
        tax_amount = subtotal * (tax_percentage / 100)
        grand_total = subtotal + tax_amount - discount
        supabase.table("purchase_returns").update({
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "grand_total": grand_total
        }).eq("id", return_id).execute()
        return jsonify({
            "success": True,
            "invoice": return_invoice
        })
    except Exception as e:
        print("ERROR IN SAVE PURCHASE RETURN:", str(e))
        return jsonify({"error": str(e)}), 500
# ==============================
# EXPENSES MODULE
# ==============================
@app.route("/expenses")
def expenses_page():
    if not is_logged_in():
        return redirect("/login")
    return render_template("expenses.html")
# ------------------------------
# ADD EXPENSE
# ------------------------------
@app.route("/add_expense", methods=["POST"])
def add_expense():
    try:
        if not is_logged_in():
            return jsonify({"error": "Unauthorized"}), 401
        data = request.get_json()
        expense_date = data.get("expense_date")
        category = data.get("category")
        description = data.get("description")
        amount = float(data.get("amount"))
        payment_method = data.get("payment_method")
        reference = data.get("reference")
        supabase.table("expenses").insert({
            "expense_date": expense_date,
            "category": category,
            "description": description,
            "amount": amount,
            "payment_method": payment_method,
            "reference": reference
        }).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ------------------------------
# GET EXPENSES (WITH FILTER)
# ------------------------------
@app.route("/get_expenses", methods=["POST"])
def get_expenses():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    category = data.get("category")
    payment_method = data.get("payment_method")
    query = supabase.table("expenses").select("*").order("id", desc=True)
    if start_date and end_date:
        query = query.gte("expense_date", start_date).lte("expense_date", end_date)
    if category and category != "All":
        query = query.eq("category", category)
    if payment_method and payment_method != "All":
        query = query.eq("payment_method", payment_method)
    expenses = query.execute()
    total = sum(float(e["amount"]) for e in expenses.data)
    return jsonify({
        "expenses": expenses.data,
        "total": total
    })
# ------------------------------
# DELETE EXPENSE
# ------------------------------
@app.route("/delete_expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    supabase.table("expenses").delete().eq("id", expense_id).execute()
    return jsonify({"success": True})
# ==============================
# REPORTS MODULE
# ==============================
@app.route("/reports")
def reports():
    if not is_logged_in():
        return redirect("/login")
    return render_template("reports.html")
@app.route("/get_report_data/<string:report_type>")
def get_report_data(report_type):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    table_map = {
        "sales": "sales",
        "purchase": "purchases",
        "sale_return": "sale_returns",
        "purchase_return": "purchase_returns",
        "pos": "manual_pos_sales",
        "expenses": "expenses"
    }
    if report_type not in table_map:
        return jsonify({"error": "Invalid report type"}), 400
    table = table_map[report_type]
    if report_type == "expenses":
        data = supabase.table(table).select("*").order("id", desc=True).execute()
        formatted = [{
            "id": d["id"],
            "invoice_number": f"EXP-{d['id']}",
            "total_amount": d["amount"],
            "created_at": d["expense_date"]
        } for d in data.data]
        return jsonify(formatted)
    data = supabase.table(table).select("*").order("id", desc=True).execute()
    formatted = []
    for d in data.data:
        invoice_number = (
            d.get("invoice_number") or
            d.get("purchase_invoice") or
            d.get("return_invoice")
        )
        total_amount = (
            d.get("total_amount") or
            d.get("grand_total") or
            d.get("total_refund") or
            0
        )
        formatted.append({
            "id": d["id"],
            "invoice_number": invoice_number,
            "total_amount": total_amount,
            "created_at": d.get("created_at") or d.get("expense_date")
        })
    return jsonify(formatted)
@app.route("/delete_record/<string:report_type>/<int:record_id>", methods=["DELETE"])
def delete_record(report_type, record_id):
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    table_map = {
        "sales": "sales",
        "purchase": "purchases",
        "sale_return": "sale_returns",
        "purchase_return": "purchase_returns",
        "pos": "manual_pos_sales",
        "expenses": "expenses"
    }
    if report_type not in table_map:
        return jsonify({"error": "Invalid type"}), 400
    supabase.table(table_map[report_type]).delete().eq("id", record_id).execute()
    return jsonify({"success": True})
@app.route("/print_invoice/<string:invoice_type>/<int:invoice_id>")
def print_invoice(invoice_type, invoice_id):
    if not is_logged_in():
        return redirect("/login")
    shop_res = supabase.table("shop_settings").select("*").limit(1).execute()
    shop = shop_res.data[0] if shop_res.data else {}
    party = {}
    items = []
    # SALES
    if invoice_type == "sales":
        invoice = supabase.table("sales").select("*").eq("id", invoice_id).single().execute().data
        items = supabase.table("sale_items").select("*, stock_products(product_name)").eq("sale_id", invoice_id).execute().data
        party = {
            "name": invoice.get("customer_name"),
            "phone": invoice.get("customer_phone")
        }
    # PURCHASE
    elif invoice_type == "purchase":
        invoice = supabase.table("purchases").select("*").eq("id", invoice_id).single().execute().data
        items = supabase.table("purchase_items").select("*").eq("purchase_id", invoice_id).execute().data
        supplier = supabase.table("suppliers").select("*").eq("id", invoice["supplier_id"]).single().execute().data
        party = {
            "name": supplier.get("supplier_name"),
            "phone": supplier.get("phone")
        }
    # SALE RETURN
    elif invoice_type == "sale_return":
        invoice = supabase.table("sale_returns").select("*").eq("id", invoice_id).single().execute().data
        items = supabase.table("sale_return_items").select("*").eq("return_id", invoice_id).execute().data
    # PURCHASE RETURN
    elif invoice_type == "purchase_return":
        invoice = supabase.table("purchase_returns").select("*").eq("id", invoice_id).single().execute().data
        items = supabase.table("purchase_return_items").select("*").eq("return_id", invoice_id).execute().data
    # POS
    elif invoice_type == "pos":
        invoice = supabase.table("manual_pos_sales").select("*").eq("id", invoice_id).single().execute().data
        items = supabase.table("manual_pos_items").select("*").eq("sale_id", invoice_id).execute().data
        party = {
            "name": invoice.get("customer_name"),
            "phone": invoice.get("customer_phone")
        }
    # EXPENSE
    elif invoice_type == "expenses":
        invoice = supabase.table("expenses").select("*").eq("id", invoice_id).single().execute().data
    else:
        return "Unsupported Invoice Type", 400
    return render_template(
        "print_invoice.html",
        shop=shop,
        invoice=invoice,
        items=items,
        party=party,
        type=invoice_type
    )
# ==============================
# PROFIT & LOSS MODULE (FINAL CORRECTED)
# ==============================
import matplotlib.pyplot as plt
import io
import base64
@app.route("/profit-loss")
def profit_loss_page():
    if not is_logged_in():
        return redirect("/login")
    return render_template("profit_loss.html")
# ==============================
# API FOR PROFIT CALCULATION
# ==============================
@app.route("/api/profit-loss")
def get_profit_loss():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    # ---- SALES ----
    sales_query = supabase.table("sales").select("total_amount, created_at")
    # ---- PURCHASES ---
    purchase_query = supabase.table("purchases").select("total_amount, purchase_date")
    # ---- EXPENSES ---
    expense_query = supabase.table("expenses").select("amount, expense_date")
    # ---- SALE RETURNS ----
    sale_return_query = supabase.table("sale_returns").select("total_refund, created_at")
    # ---- PURCHASE RETURNS ----
    purchase_return_query = supabase.table("purchase_returns").select("grand_total, created_at")
    # Apply date filters if provided
    if start_date and end_date:
        sales_query = sales_query.gte("created_at", start_date).lte("created_at", end_date)
        purchase_query = purchase_query.gte("purchase_date", start_date).lte("purchase_date", end_date)
        expense_query = expense_query.gte("expense_date", start_date).lte("expense_date", end_date)
        sale_return_query = sale_return_query.gte("created_at", start_date).lte("created_at", end_date)
        purchase_return_query = purchase_return_query.gte("created_at", start_date).lte("created_at", end_date)
    sales = sales_query.execute()
    purchases = purchase_query.execute()
    expenses = expense_query.execute()
    sale_returns = sale_return_query.execute()
    purchase_returns = purchase_return_query.execute()
    # Safe sum calculations
    total_sales = sum(float(s["total_amount"]) for s in sales.data) if sales.data else 0
    total_purchase = sum(float(p["total_amount"]) for p in purchases.data) if purchases.data else 0
    total_expenses = sum(float(e["amount"]) for e in expenses.data) if expenses.data else 0
    total_sale_return = sum(float(r["total_refund"]) for r in sale_returns.data) if sale_returns.data else 0
    total_purchase_return = sum(float(r["grand_total"]) for r in purchase_returns.data) if purchase_returns.data else 0
    # Calculations
    net_sales = total_sales - total_sale_return
    net_purchase = total_purchase - total_purchase_return
    gross_profit = net_sales - net_purchase
    net_profit = gross_profit - total_expenses
    return jsonify({
        "total_sales": total_sales,
        "total_purchase": total_purchase,
        "total_expenses": total_expenses,
        "total_sale_return": total_sale_return,
        "total_purchase_return": total_purchase_return,
        "net_profit": net_profit
    })
# ==============================
# PROFIT GRAPH
# ==============================
@app.route("/profit-graph")
def profit_graph():
    if not is_logged_in():
        return redirect("/login")
    sales = supabase.table("sales").select("total_amount, created_at").execute()
    purchases = supabase.table("purchases").select("total_amount, purchase_date").execute()
    expenses = supabase.table("expenses").select("amount, expense_date").execute()
    monthly_profit = {}
    # ---- ADD SALES ----
    if sales.data:
        for s in sales.data:
            month = s["created_at"][:7]
            monthly_profit.setdefault(month, 0)
            monthly_profit[month] += float(s["total_amount"] or 0)
    # ---- SUBTRACT PURCHASES ----
    if purchases.data:
        for p in purchases.data:
            month = p["purchase_date"][:7]
            monthly_profit.setdefault(month, 0)
            monthly_profit[month] -= float(p["total_amount"] or 0)
    # ---- SUBTRACT EXPENSES ----
    if expenses.data:
        for e in expenses.data:
            month = e["expense_date"][:7]
            monthly_profit.setdefault(month, 0)
            monthly_profit[month] -= float(e["amount"] or 0)
    months = sorted(monthly_profit.keys())
    profits = [monthly_profit[m] for m in months]
    plt.figure()
    plt.plot(months, profits)
    plt.title("Monthly Net Profit")
    plt.xlabel("Month")
    plt.ylabel("Profit")
    plt.xticks(rotation=45)
    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format="png")
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f'<img src="data:image/png;base64,{graph_url}"/>'
# ==============================
# LOW STOCK MODULE
# ==============================
@app.route("/low-stock")
def low_stock_page():
    if not is_logged_in():
        return redirect("/login")
    return render_template("low_stock.html")
# API to fetch low stock items
@app.route("/api/low-stock")
def get_low_stock():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    search = request.args.get("search", "").lower()
    filter_type = request.args.get("filter", "all")
    stock = supabase.table("stock").select("*").execute()
    low_stock_items = []
    if stock.data:
        for item in stock.data:
            quantity = float(item["quantity"] or 0)
            limit = float(item["low_stock_limit"] or 0)
            status = "OK"
            if quantity == 0:
                status = "Out of Stock"
            elif quantity <= limit:
                status = "Low Stock"
            if filter_type == "low" and status != "Low Stock":
                continue
            if filter_type == "out" and status != "Out of Stock":
                continue
            if search and search not in item["product_name"].lower():
                continue
            if status != "OK":
                item["status"] = status
                low_stock_items.append(item)
    return jsonify(low_stock_items)
# ==============================
# SETTINGS MODULE
# ==============================
@app.route("/settings")
def settings_page():
    if not is_logged_in():
        return redirect("/login")
    # Get shop settings
    shop_res = supabase.table("shop_settings").select("*").limit(1).execute()
    shop = shop_res.data[0] if shop_res.data else {}
    # Get system settings
    system_res = supabase.table("system_settings").select("*").limit(1).execute()
    system = system_res.data[0] if system_res.data else {}
    return render_template("settings.html", shop=shop, system=system)
# ------------------------------
# UPDATE SHOP SETTINGS
# ------------------------------
@app.route("/update_shop_settings", methods=["POST"])
def update_shop_settings():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    supabase.table("shop_settings").update({
        "shop_name": data.get("shop_name"),
        "logo_url": data.get("logo_url"),
        "address": data.get("address"),
        "phone": data.get("phone"),
        "gst_percentage": float(data.get("gst_percentage", 0)),
        "return_policy": data.get("return_policy"),
        "footer_message": data.get("footer_message"),
        "currency_symbol": data.get("currency_symbol")
    }).eq("id", 1).execute()
    return jsonify({"success": True})
# ------------------------------
# UPDATE SYSTEM SETTINGS
# ------------------------------
@app.route("/update_system_settings", methods=["POST"])
def update_system_settings():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    supabase.table("system_settings").update({
        "default_low_stock_limit": int(data.get("default_low_stock_limit", 10)),
        "show_low_stock_badge": data.get("show_low_stock_badge", True),
        "auto_logout_minutes": int(data.get("auto_logout_minutes", 30)),
        "invoice_prefix": data.get("invoice_prefix")
    }).eq("id", 1).execute()
    return jsonify({"success": True})
# ==============================
# ACCOUNT SETTINGS
# ==============================
@app.route("/update_email", methods=["POST"])
def update_email():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    new_email = data.get("email")
    try:
        supabase.auth.update_user({
            "email": new_email
        })
        session["user_email"] = new_email
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.route("/update_password", methods=["POST"])
def update_password():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    new_password = data.get("password")
    try:
        supabase.auth.update_user({
            "password": new_password
        })
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
#----------------------
#   Don't change this 
#----------------------
if __name__ == "__main__":
    app.run(debug=True)