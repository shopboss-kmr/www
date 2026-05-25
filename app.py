from flask import Flask, request, redirect, session
import psycopg2
import requests
import os

# ---------------- APP ----------------
ShopBoss = Flask(__name__)
ShopBoss.secret_key = "fayiz_shopboss_secure_2026_ultra"

# ---------------- DATABASE ----------------
def db():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        database=os.environ.get("PGDATABASE", "shopboss"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "123456789"),
        port=int(os.environ.get("PGPORT", 5432))
    )

def init_db():

    conn = db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # PRODUCTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id SERIAL PRIMARY KEY,
        name TEXT,
        price INTEGER,
        image TEXT,
        category TEXT DEFAULT 'General'
    )
    """)
    conn.commit()

    # ADD CATEGORY COLUMN IF OLD TABLE EXISTS
    try:
        cur.execute("""
        ALTER TABLE products
        ADD COLUMN category TEXT DEFAULT 'General'
        """)
        conn.commit()

    except:
        conn.rollback()
    # ORDERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id SERIAL PRIMARY KEY,
        username TEXT,
        items TEXT,
        total INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # ADD RECEIVED COLUMN
    try:
        cur.execute("""
        ALTER TABLE orders
        ADD COLUMN received BOOLEAN DEFAULT FALSE
        """)
        conn.commit()

    except:
        conn.rollback()
    try:

        cur.execute("""
        ALTER TABLE orders
        ADD COLUMN status TEXT DEFAULT 'Ordered'
        """)

        conn.commit()

    except:
        conn.rollback()

    # DEMO PRODUCTS
    cur.execute("SELECT * FROM products")

    if not cur.fetchall():

        cur.execute("""
        INSERT INTO products(name,price,image,category)
        VALUES
        (
            'iPhone 15',
            120000,
            'https://m.media-amazon.com/images/I/71d7rfSl0wL.jpg',
            'Electronics'
        ),

        (
            'Nike Shoes',
            4500,
            'https://m.media-amazon.com/images/I/61utX8kBDlL._UY695_.jpg',
            'Fashion'
        ),

        (
            'Headphones',
            2500,
            'https://m.media-amazon.com/images/I/61CGHv6kmWL.jpg',
            'Electronics'
        )
        """)

    conn.commit()

    cur.close()
    conn.close()
# ---------------- HEADER ----------------
def header():

    cart = session.get("cart", {})
    count = sum(cart.values())

    return f"""
    <div style="
        background:#131921;
        color:white;
        padding:10px;
        display:flex;
        align-items:center;
        font-family:Arial;
    ">

        <div style="
            color:#ff9900;
            font-size:24px;
            font-weight:bold;
            margin-right:20px;
        ">
            ShopBoss
        </div>

        <form action="/home" method="get"
        style="
            flex:1;
            display:flex;
            margin:0 20px;
        ">

            <input
            name="q"
            placeholder="Search products"
            style="
                flex:1;
                padding:10px;
                border:none;
                outline:none;
            ">

            <button style="
                background:#febd69;
                border:none;
                padding:10px 20px;
                cursor:pointer;
            ">
                Search
            </button>

        </form>

        <div style="
            display:flex;
            gap:20px;
        ">

            <a href="/home"
            style="color:white;text-decoration:none;">
                Home
            </a>

            <a href="/cart"
            style="color:white;text-decoration:none;">
                Cart ({count})
            </a>

            <a href="/admin"
            style="color:white;text-decoration:none;">
                Admin
            </a>

            <a href="/logout"
            style="color:white;text-decoration:none;">
                Logout
            </a>

        </div>

    </div>
    """
# ---------START UP-----------#
@ShopBoss.route("/")
def first():

    return redirect("/splash")
# ---------------- SPLASH ----------------
@ShopBoss.route("/splash")
def splash():


    return """
    <html>

    <head>

        <meta http-equiv="refresh" content="3;url=/check">

        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <link rel="shortcut icon" href="/favicon.ico">

        <style>

            body{
                margin:0;
                background:#131921;
                display:flex;
                justify-content:center;
                align-items:center;
                height:100vh;
                font-family:Arial;
                overflow:hidden;
            }

            .box{
                text-align:center;
                animation:zoom 2s;
            }

            h1{
                color:#ff9900;
                font-size:70px;
                margin:0;
            }

            p{
                color:white;
                font-size:20px;
                margin-top:10px;
            }
            

            @keyframes zoom{
                from{
                    transform:scale(0.5);
                    opacity:0;
                }

                to{
                    transform:scale(1);
                    opacity:1;
                }
            }

        </style>

    </head>

    <body>

        <div class="box">

            <h1>Welcome To Shopboss</h1>

            <p>Kashmir's First Shopping App By Ahmad Fayiz</p>

            <div class="loader"></div>

        </div>

    </body>

    </html>
    """
# ---------------- CHECK ----------------
# ---------------- CHECK ----------------
@ShopBoss.route("/check")
def check():

    # ALREADY LOGGED IN
    if session.get("user"):

        return redirect("/home")

    # NEW USER
    else:
        return redirect("/signup")

# ---------------- HOME ----------------
@ShopBoss.route("/home")
def home():

    if not session.get("user"):
        return redirect("/signup")

    q = request.args.get("q","")

    category = request.args.get("category","")

    conn = db()
    cur = conn.cursor()

    # SEARCH + CATEGORY
    if q and category:

        cur.execute(
            """
            SELECT * FROM products
            WHERE LOWER(name) LIKE %s
            AND category=%s
            ORDER BY id DESC
            """,
            ("%"+q.lower()+"%", category)
        )

    elif q:

        cur.execute(
            """
            SELECT * FROM products
            WHERE LOWER(name) LIKE %s
            ORDER BY id DESC
            """,
            ("%"+q.lower()+"%",)
        )

    elif category:

        cur.execute(
            """
            SELECT * FROM products
            WHERE category=%s
            ORDER BY id DESC
            """,
            (category,)
        )

    else:

        cur.execute(
            "SELECT * FROM products ORDER BY id DESC"
        )

    products = cur.fetchall()

    html = header()

    html += """
    <html>

    <head>

    <title>ShopBoss • Developed by Ahmad Fayiz</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <link rel="shortcut icon" href="/favicon.ico">

    <style>

    *{
        box-sizing:border-box;
    }

    body{
        margin:0;
        background:#eaeded;
        font-family:Arial;
        overflow-x:hidden;
    }

    .main{
        padding:12px;
        width:100%;
    }

    .categories{
        display:flex;
        gap:10px;
        overflow-x:auto;
        padding-bottom:10px;
        margin-bottom:15px;
    }

    .categories::-webkit-scrollbar{
        display:none;
    }

    .cat{
        background:#f3f3f3;
        padding:10px 16px;
        border-radius:30px;
        text-decoration:none;
        color:black;
        white-space:nowrap;
        font-weight:bold;
        font-size:14px;
    }

    .products{
        display:grid;
        grid-template-columns:repeat(10,1fr);
        gap:12px;
    }

    .card{
        background:white;
        border-radius:12px;
        padding:12px;
        box-shadow:0 2px 6px rgba(0,0,0,0.08);
        width:100%;
    }

    .card img{
        width:100%;
        height:220px;
        object-fit:contain;
        border-radius:10px;
        background:#f8f8f8;
    }

    .name{
        font-size:16px;
        font-weight:bold;
        margin-top:10px;
        line-height:1.3;
        min-height:42px;
    }

    .category{
        color:#666;
        font-size:13px;
        margin-top:4px;
    }

    .price{
        color:green;
        font-size:28px;
        font-weight:bold;
        margin-top:10px;
    }

    .btn{
        display:block;
        margin-top:12px;
        background:#ffd814;
        text-align:center;
        padding:10px;
        border-radius:8px;
        text-decoration:none;
        color:black;
        font-weight:bold;
    }

    /* TABLET */
    @media(min-width:701px) and (max-width:1024px){

        .products{
            grid-template-columns:repeat(5,1fr);
            gap:10px;
        }

        .card img{
            height:150px;
        }

    }

    /* MOBILE */
    @media(max-width:700px){

        body{
            overflow-x:hidden;
        }

        .main{
            width:100%;
            padding:8px;
        }

        .categories{
            gap:6px;
            margin-bottom:10px;
        }

        .cat{
            font-size:11px;
            padding:7px 10px;
        }

        .products{
            grid-template-columns:repeat(3,1fr);
            gap:8px;
            width:100%;
        }

        .card{
            padding:6px;
            border-radius:10px;
            overflow:hidden;
        }

        .card img{
            width:100%;
            height:100px;
            object-fit:cover;
            border-radius:8px;
        }

        .name{
            font-size:12px;
            min-height:32px;
            line-height:1.2;
            margin-top:5px;
        }

        .category{
            font-size:11px;
            margin-top:3px;
        }

        .price{
            font-size:16px;
            margin-top:4px;
        }

        .btn{
            width:100%;
            padding:7px 0;
            font-size:11px;
            margin-top:6px;
            border-radius:6px;
        }
    }

    </style>

    </head>

    <body>

    <div class="main">

    <!-- CATEGORIES -->
    <div class="categories">



        <a class="cat" href="/home?category=Cricket">🏏 Cricket</a>

        <a class="cat" href="/home?category=Football">⚽ Football</a>

        <a class="cat" href="/home?category=Fashion">🧥 Fashion</a>

        <a class="cat" href="/home?category=Toys">🧩 Toys</a>

        <a class="cat" href="/home?category=Electronics">📱 Electronics</a>

        <a class="cat" href="/home?category=Kitchen">👨‍🍳 Kitchen</a>

        <a class="cat" href="/home?category=Garden">🌻 Garden</a>

        <a class="cat" href="/orders">📦 My Orders</a>

    </div>

    <!-- PRODUCTS -->
    <div class="products">
    """

    for p in products:

        category = p[4] if len(p) > 4 else "General"

        html += f"""
        <div class="card">

            <img src="{p[3]}" onclick="openImg('{p[3]}')" style="cursor:zoom-in;">

            <div class="name">
                {p[1]}
            </div>

            <div class="category">
                {category}
            </div>

            <div class="price">
                ₹{p[2]}
            </div>

            <a href="/add/{p[0]}"
            class="btn">
                Add To Cart
            </a>

        </div>
        """

    html += """
    </div>

    </div>

    <!-- LIGHTBOX -->
    <div id="lightbox" onclick="closeImg()" style="
        display:none;
        position:fixed;
        top:0;left:0;
        width:100%;height:100%;
        background:rgba(0,0,0,0.85);
        z-index:9999;
        justify-content:center;
        align-items:center;
        cursor:zoom-out;
    ">
        <img id="lightbox-img" src="" style="
            max-width:90%;
            max-height:90%;
            border-radius:12px;
            box-shadow:0 8px 40px rgba(0,0,0,0.6);
            object-fit:contain;
        ">
    </div>

    <script>
    function openImg(src){
        document.getElementById('lightbox-img').src = src;
        var lb = document.getElementById('lightbox');
        lb.style.display = 'flex';
    }
    function closeImg(){
        document.getElementById('lightbox').style.display = 'none';
    }
    document.addEventListener('keydown', function(e){
        if(e.key === 'Escape') closeImg();
    });
    </script>

    </body>

    </html>
    """

    cur.close()
    conn.close()

    return html

# ---------------- SIGNUP ----------------
@ShopBoss.route("/signup", methods=["GET","POST"])
def signup():

    if session.get("user"):
        return redirect("/home")

    if request.method == "POST":

        username = request.form["u"]
        password = request.form["p"]

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (username,password)
        )

        conn.commit()

        cur.close()
        conn.close()

        session["signedup"] = True
        session["user"] = username

        return redirect("/")

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <meta name="description" content="ShopBoss — Online shopping for Cricket, Football, Fashion, Shoes, Electronics, Kitchen & more. Best prices in Kashmir. Developed by Ahmad Fayiz.">
        <meta name="robots" content="noindex, follow">
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <link rel="shortcut icon" href="/favicon.ico">
    </head>
    <body style="margin:0;">
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        background:#f2f2f2;
        font-family:Arial;
    ">

        <form method="post"
        style="
            background:white;
            padding:30px;
            width:320px;
            border-radius:10px;
        ">

            <h2 style="text-align:center;">
                Sign Up
            </h2>

            <input
            name="u"
            placeholder="Username"
            required
            style="
                width:100%;
                padding:10px;
                margin:10px 0;
                box-sizing:border-box;
                display:block;
            ">

            <input
            type="password"
            name="p"
            placeholder="Password"
            required
            style="
                width:100%;
                padding:10px;
                margin:10px 0;
                box-sizing:border-box;
                display:block;
            ">

            <button
            style="
                width:100%;
                padding:10px;
                background:#ffd814;
                border:none;
                box-sizing:border-box;
                display:block;
            ">
                Sign Up
            </button>

        </form>

    </div>
    </body>
    </html>
    """

# ---------------- LOGIN ----------------
@ShopBoss.route("/login", methods=["GET","POST"])
def login():

    if session.get("user"):
        return redirect("/home")

    if request.method == "POST":

        username = request.form["u"]
        password = request.form["p"]

        conn = db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username,password)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:

            session["user"] = username

            return redirect("/")

        return "INVALID LOGIN"

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <meta name="description" content="ShopBoss — Online shopping for Cricket, Football, Fashion, Shoes, Electronics, Kitchen & more. Best prices in Kashmir. Developed by Ahmad Fayiz.">
        <meta name="robots" content="noindex, follow">
        <link rel="icon" type="image/x-icon" href="/favicon.ico">
        <link rel="shortcut icon" href="/favicon.ico">
    </head>
    <body style="margin:0;">
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        background:#f2f2f2;
        font-family:Arial;
    ">

        <form method="post"
        style="
            background:white;
            padding:30px;
            width:320px;
            border-radius:10px;
        ">

            <h2 style="text-align:center;">
                Login
            </h2>

            <input
            name="u"
            placeholder="Username"
            required
            style="
                width:100%;
                padding:10px;
                margin:10px 0;
                box-sizing:border-box;
                display:block;
            ">

            <input
            type="password"
            name="p"
            placeholder="Password"
            required
            style="
                width:100%;
                padding:10px;
                margin:10px 0;
                box-sizing:border-box;
                display:block;
            ">

            <button
            style="
                width:100%;
                padding:10px;
                background:#ffd814;
                border:none;
                box-sizing:border-box;
                display:block;
            ">
                Login
            </button>

        </form>

    </div>
    </body>
    </html>
    """

# ---------------- ADD TO CART ----------------
@ShopBoss.route("/add/<int:id>")
def add(id):

    cart = session.get("cart", {})

    pid = str(id)

    cart[pid] = cart.get(pid, 0) + 1

    session["cart"] = cart

    return redirect("/cart")


# ---------------- MINUS FROM CART ----------------
@ShopBoss.route("/minus/<int:id>")
def minus(id):

    cart = session.get("cart", {})

    pid = str(id)

    if pid in cart:

        cart[pid] -= 1

        # REMOVE ITEM IF 0
        if cart[pid] <= 0:
            del cart[pid]

    session["cart"] = cart

    return redirect("/cart")


# ---------------- DELETE ITEM ----------------
@ShopBoss.route("/delete/<int:id>")
def delete(id):

    cart = session.get("cart", {})

    pid = str(id)

    if pid in cart:
        del cart[pid]

    session["cart"] = cart

    return redirect("/cart")


# ---------------- CART ----------------
@ShopBoss.route("/cart")
def cart():

    cart = session.get("cart", {})

    conn = db()
    cur = conn.cursor()

    total = 0
    delivery_charge = 20

    html = header()

    html += """
    <div style="
        display:flex;
        padding:30px;
        background:#eaeded;
        font-family:Arial;
        min-height:100vh;
    ">
    """

    # LEFT SIDE
    html += """
    <div style="
        width:70%;
    ">
    """

    # EMPTY CART
    if not cart:

        html += """
        <div style="
            background:white;
            padding:40px;
            border-radius:10px;
            text-align:center;
        ">

            <h1>Opps! Your Cart Is Empty 🛒</h1>

            <a href="/"
            style="
                display:inline-block;
                margin-top:20px;
                background:#ffd814;
                padding:12px 20px;
                text-decoration:none;
                color:black;
                border-radius:5px;
                font-weight:bold;
            ">
                 Continue Shopping
            </a>

        </div>
        """

    # PRODUCTS
    for pid, qty in cart.items():

        cur.execute(
            "SELECT * FROM products WHERE id=%s",
            (pid,)
        )

        p = cur.fetchone()

        if p:

            subtotal = p[2] * qty

            total += subtotal

            html += f"""
            <div style="
                background:white;
                padding:20px;
                margin-bottom:20px;
                display:flex;
                border-radius:12px;
                box-shadow:0 2px 6px rgba(0,0,0,0.1);
            ">

                <img src="{p[3]}"
                style="
                    width:180px;
                    height:200px;
                    object-fit:cover;
                    border-radius:10px;
                    margin-right:20px;
                ">

                <div style="
                    flex:1;
                ">

                    <h2>{p[1]}</h2>

                    <h3 style="
                        color:green;
                    ">
                        ₹{p[2]}
                    </h3>

                    <div style="
                        display:flex;
                        align-items:center;
                        gap:10px;
                        margin-top:15px;
                    ">

                        <!-- MINUS -->
                        <a href="/minus/{p[0]}"
                        style="
                            width:40px;
                            height:40px;
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            background:#ffd814;
                            text-decoration:none;
                            color:black;
                            font-size:22px;
                            border-radius:6px;
                            font-weight:bold;
                        ">
                            -
                        </a>

                        <!-- PLUS -->
                        <a href="/add/{p[0]}"
                        style="
                            width:40px;
                            height:40px;
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            background:#ffd814;
                            text-decoration:none;
                            color:black;
                            font-size:22px;
                            border-radius:6px;
                            font-weight:bold;
                        ">
                            +
                        </a>

                        <!-- DELETE -->
                        <a href="/delete/{p[0]}"
                        style="
                            height:40px;
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            background:red;
                            color:white;
                            padding:0 14px;
                            text-decoration:none;
                            border-radius:6px;
                            font-weight:bold;
                        ">
                            Delete
                        </a>

                    </div>

                    <h3 style="
                        margin-top:20px;
                    ">
                        Subtotal ₹{subtotal}
                    </h3>

                </div>

            </div>
            """

    html += "</div>"

    # RIGHT SIDE
    grand_total = total + delivery_charge

    html += f"""
    <div style="
        width:30%;
        padding-left:25px;
    ">

        <div style="
            background:white;
            padding:25px;
            border-radius:10px;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
            position:sticky;
            top:10px;
        ">

            <h2>Order Summary</h2><hr>
            <p>Delivery Charge: ₹{delivery_charge}</p>
            <h1 style="color:green;font-size:22">
                ₹{grand_total}
            </h1>

            <a href="/address"
            style="
            height:39px;
            display:flex;
            justify-content:center;
            align-items:center;
            background:#ffd814;
            color:black;
            padding:0 5px;
            text-decoration:none;
            border-radius:5px;
            font-weight:bold;
            ">
            Proceed To Buy
            </a>

        </div>

    </div>
    """

    html += "</div>"

    cur.close()
    conn.close()

    return html

# ---------------- ADDRESS ----------------
@ShopBoss.route("/address", methods=["GET","POST"])
def address():

    if request.method == "POST":

        mobile = request.form["mobile"]
        address = request.form["address"]
        payment = request.form["payment"]

        conn = db()
        cur = conn.cursor()

        total = 0

        message = f"""
A NEW ORDER RECEIVED

User: {session.get('user')}

Mobile: {mobile}

Address: {address}

Payment: {payment}

Items:

"""

        for pid, qty in session.get("cart", {}).items():

            cur.execute(
                "SELECT name,price FROM products WHERE id=%s",
                (pid,)
            )

            p = cur.fetchone()

            if p:

                total += p[1] * qty

                message += f"{p[0]} - Qty:{qty} - ₹{p[1]}\n"

        delivery_charge = 20
        grand_total = total + delivery_charge

        message += f"\nDelivery Charge = ₹{delivery_charge}"
        message += f"\nGRAND TOTAL = ₹{grand_total}"

        # SEND EMAIL
        requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            headers={
                "Content-Type":"application/json"
            },
            json={
                "service_id":"service_shopboss",
                "template_id":"template_shopboss",
                "user_id":"9bTfVOFVe_u1Mt51L",
                "template_params":{
                    "name":session.get("user"),
                    "email":"kfayizwani@gmail.com",
                    "message":message
                }
            }
        )

        # SAVE ORDER
        items_text = ""

        for pid, qty in session.get("cart", {}).items():

            cur.execute(
                "SELECT name,image FROM products WHERE id=%s",
                (pid,)
            )

            p = cur.fetchone()

            if p:

                items_text += f"{p[0]}|||{qty}|||{p[1]}\n"

        cur.execute(
            """
            INSERT INTO orders(username,items,total,status)
            VALUES(%s,%s,%s,%s)
            """,
            (
                session.get("user"),
                items_text,
                grand_total,
                "Ordered"
            )
        )

        conn.commit()

        session["cart"] = {}

        return f"""
        <div style="
            height:100vh;
            display:flex;
            justify-content:center;
            align-items:center;
            background:#eaeded;
            font-family:Arial;
        ">

            <div style="
                background:white;
                padding:40px;
                width:400px;
                border-radius:10px;
                text-align:center;
                box-shadow:0 0 10px rgba(0,0,0,0.1);
            ">

                <h1 style="
                    color:green;
                    font-size:60px;
                    margin:0;
                ">
                    ✔
                </h1>

                <h2>Order Placed Successfully</h2>

                <h3>Total Paid ₹{grand_total}</h3>

                <a href="/"
                style="
                    display:inline-block;
                    background:#ffd814;
                    padding:12px 20px;
                    text-decoration:none;
                    color:black;
                    border-radius:5px;
                    margin-top:10px;
                    font-weight:bold;
                ">
                    Continue Shopping
                </a>

            </div>

        </div>
        """

    return """
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        min-height:100vh;
        background:#f2f2f2;
        font-family:Arial;
        padding:20px;
    ">

        <form method="post"
        style="
            background:white;
            padding:30px;
            width:350px;
            border-radius:10px;
            box-shadow:0 0 10px rgba(0,0,0,0.1);
        ">

            <h2 style="
                text-align:center;
                margin-bottom:20px;
            ">
                Checkout
            </h2>

            <input
            name="mobile"
            placeholder="Mobile Number"
            required
            style="
                width:100%;
                padding:12px;
                margin:10px 0;
                border:1px solid #ccc;
                border-radius:5px;
                box-sizing:border-box;
            ">

            <input
            name="address"
            placeholder="Your Address"
            required
            style="
                width:100%;
                padding:12px;
                margin:10px 0;
                border:1px solid #ccc;
                border-radius:5px;
                box-sizing:border-box;
            ">

            <h3>Payment Options</h3>

            <label style="display:block;margin-bottom:10px;">
                <input
                type="radio"
                name="payment"
                value="Cash on Delivery"
                onclick="hideQR()"
                required>

                Cash on Delivery
            </label>

            <label style="display:block;margin-bottom:10px;">
                <input
                type="radio"
                name="payment"
                value="Online Payment"
                onclick="showQR()">

                Online Payment
            </label>

            <div id="qrBox"
            style="
                display:none;
                text-align:center;
                margin-top:15px;
            ">

                <img src="/static/qr.png"
                style="
                    width:220px;
                    border-radius:10px;
                ">

                <p style="
                    margin-top:10px;
                    font-weight:bold;
                ">
                    Scan & Pay
                </p>

            </div>

            <button
            style="
                width:100%;
                padding:12px;
                margin-top:20px;
                background:#ffd814;
                border:none;
                border-radius:5px;
                cursor:pointer;
                font-size:16px;
                font-weight:bold;
            ">
                Place Order
            </button>

        </form>

    </div>

<script>

function showQR(){

    document.getElementById("qrBox").style.display = "block";
}

function hideQR(){

    document.getElementById("qrBox").style.display = "none";
}

</script>
"""
    # ---------------- UPDATE STATUS ----------------
@ShopBoss.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        (status, id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/all_orders")
# ---------------- ADMIN ----------------
@ShopBoss.route("/admin", methods=["GET","POST"])
def admin():

    if request.method == "POST":

        if request.form["s"] == "fayiz":

            session["admin"] = True

            return redirect("/panel")

        

    return """
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        height:100vh;
        background:#f2f2f2;
        font-family:Arial;
    ">

        <form method="post"
        style="
            background:white;
            padding:30px;
            width:320px;
            border-radius:10px;
        ">

            <h2 style="text-align:center;">
                Admin Login
            </h2>

            <input
            type="password"
            name="s"
            placeholder="Secret Key"
            required
            style="
                width:100%;
                padding:10px;
                margin:10px 0;
            ">

            <button
            style="
                width:100%;
                padding:10px;
                background:#ffd814;
                border:none;
            ">
                ENTER TO THE PANEL
            </button>

        </form>

    </div>
    """

# ---------------- PANEL ----------------
@ShopBoss.route("/panel", methods=["GET","POST"])
def panel():

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()
    

    # -------- ADD PRODUCT --------
    if request.method == "POST":

        # ADD
        if "add" in request.form:

            cur.execute(
                """
                INSERT INTO products(name,price,image,category)
                VALUES(%s,%s,%s,%s)
                """,
                (
                    request.form["name"],
                    request.form["price"],
                    request.form["image"],
                    request.form["category"]
                )
            )

        # UPDATE
        elif "update" in request.form:

            cur.execute(
                """
                UPDATE products
                SET name=%s, price=%s, image=%s, category=%s
                WHERE id=%s
                """,
                (
                    request.form["name"],
                    request.form["price"],
                    request.form["image"],
                    request.form["category"],
                    request.form["id"]
                )
            )

        # DELETE
        elif "delete" in request.form:

            cur.execute(
                "DELETE FROM products WHERE id=%s",
                (request.form["id"],)
            )

        conn.commit()

    # GET PRODUCTS
    cur.execute("SELECT * FROM products ORDER BY id DESC")

    products = cur.fetchall()

    html = header()

    html += """
    <div style="
        background:#eaeded;
        min-height:100vh;
        padding:25px;
        font-family:Arial;
    ">

        <!-- TOP BAR -->
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:20px;
          ">
            <a href="/all_orders"
            style="
            background:#ffd814;
            padding:10px 20px;
            text-decoration:none;
            color:black;
            border-radius:6px;
            font-weight:bold;
            ">
               View Orders
            </a>
        

            <h1>Admin Panel</h1>

        </div>

        <!-- ADD PRODUCT BOX -->
        <div style="
            background:white;
            padding:20px;
            border-radius:10px;
            margin-bottom:25px;
            box-shadow:0 2px 8px rgba(0,0,0,0.1);
        ">

            <h2>Add Product</h2>

            <form method="post"
            style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
            ">

                <input
                name="name"
                placeholder="Product Name"
                required
                style="
                    flex:1;
                    padding:10px;
                ">

                <input
                name="price"
                placeholder="Price"
                required
                style="
                    width:120px;
                    padding:10px;
                ">

                <input
                name="image"
                placeholder="Image URL"
                required
                style="
                    flex:2;
                    padding:10px;
                ">

                <select
                name="category"
                required
                style="
                    padding:10px;
                ">

                    <option value="">Category</option>

                    <option>Cricket</option>

                    <option>Football</option>

                    <option>Fashion</option>

                    <option>Toys</option>

                    <option>Electronics</option>

                    <option>Kitchen</option>

                    <option>Garden</option>

                </select>

                <button
                name="add"
                style="
                    background:#ffd814;
                    border:none;
                    padding:10px 20px;
                    cursor:pointer;
                    font-weight:bold;
                ">
                    Add
                </button>

            </form>

        </div>

        <!-- PRODUCTS GRID -->
        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
            gap:20px;
        ">
    """

    # -------- PRODUCTS --------
    for p in products:

        category = p[4] if len(p) > 4 else "General"

        html += f"""
        <div style="
            background:white;
            padding:15px;
            border-radius:10px;
            box-shadow:0 2px 8px rgba(0,0,0,0.1);
        ">

            <img src="{p[3]}"
            style="
                width:100%;
                height:220px;
                object-fit:cover;
                border-radius:8px;
            ">

            <form method="post"
            style="
                margin-top:12px;
                display:flex;
                flex-direction:column;
                gap:10px;
            ">

                <input type="hidden" name="id" value="{p[0]}">

                <input
                name="name"
                value="{p[1]}"
                style="padding:10px;">

                <input
                name="price"
                value="{p[2]}"
                style="padding:10px;">

                <input
                name="image"
                value="{p[3]}"
                style="padding:10px;">

                <select
                name="category"
                style="padding:10px;">

                    <option {"selected" if category=="Cricket" else ""}>
                        Cricket
                    </option>

                    <option {"selected" if category=="Football" else ""}>
                        Football
                    </option>

                    <option {"selected" if category=="Fashion" else ""}>
                        Fashion
                    </option>

                    <option {"selected" if category=="Toys" else ""}>
                        Toys
                    </option>

                    <option {"selected" if category=="Electronics" else ""}>
                        Electronics
                    </option>

                    <option {"selected" if category=="Kitchen" else ""}>
                        Kitchen
                    </option>

                     <option {"selected" if category=="Garden" else ""}>
                        Garden
                    </option>

                </select>

                <div style="display:flex;gap:10px;">

                    <button
                    name="update"
                    style="
                        flex:1;
                        background:green;
                        color:white;
                        border:none;
                        padding:10px;
                        cursor:pointer;
                    ">
                        Update
                    </button>

                    <button
                    name="delete"
                    style="
                        flex:1;
                        background:red;
                        color:white;
                        border:none;
                        padding:10px;
                        cursor:pointer;
                    ">
                        Delete
                    </button>

                </div>

            </form>

        </div>
        """

    html += """
        </div>
    </div>
    """

    cur.close()
    conn.close()

    return html
# ---------------- ALL ORDERS ----------------
@ShopBoss.route("/all_orders")
def all_orders():

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
    SELECT id,username,total,status,created_at
    FROM orders
    ORDER BY id DESC
    """)

    orders = cur.fetchall()

    html = header()

    html += """
    <div style="
        padding:20px;
        background:#eaeded;
        min-height:100vh;
        font-family:Arial;
    ">

    <h1>All Orders</h1>
    """

    for o in orders:

        html += f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:12px;
            margin-bottom:20px;
        ">

            <h2>Order #{o[0]}</h2>

            <p>User: {o[1]}</p>

            <p>Total: ₹{o[2]}</p>

            <p>Status: <b>{o[3]}</b></p>

            <p>{o[4]}</p>

            <div style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                margin-top:15px;
            ">

                <a href="/update_status/{o[0]}/Ordered">Ordered</a>

                <a href="/update_status/{o[0]}/Packed">Packed</a>

                <a href="/update_status/{o[0]}/Shipped">Shipped</a>

                <a href="/update_status/{o[0]}/Out For Delivery">Out For Delivery</a>

                <a href="/update_status/{o[0]}/Delivered">Delivered</a>

            </div>

        </div>
        """

    html += "</div>"

    cur.close()
    conn.close()

    return html
# ---------------- ORDERS ----------------
@ShopBoss.route("/orders")
def orders():

    if not session.get("user"):
        return redirect("/login")

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id,items,total,created_at,received,status
        FROM orders
        WHERE username=%s
        ORDER BY id DESC
        """,
        (session.get("user"),)
    )

    orders = cur.fetchall()

    html = header()

    html += """
    <html>

    <head>

    <style>

    body{
        margin:0;
        background:#eaeded;
        font-family:Arial;
    }

    .main{
        padding:18px;
    }

    .order-card{
        background:white;
        padding:18px;
        border-radius:15px;
        margin-bottom:25px;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
    }

    @keyframes truckmove{

        0%{
            transform:translateX(-3px);
        }

        50%{
            transform:translateX(3px);
        }

        100%{
            transform:translateX(-3px);
        }
    }

    @media(max-width:900px){

        .flex-box{
            flex-direction:column;
        }

        .left-box{
            width:100% !important;
        }

        .right-box{
            width:100% !important;
        }

        .product-img{
            width:100% !important;
            height:220px !important;
        }

        .steps{
            font-size:10px !important;
        }

        .truck{
            font-size:38px !important;
        }

        .status-text{
            font-size:24px !important;
        }
    }

    </style>

    </head>

    <body>

    <div class="main">

        <h1 style="
            margin-bottom:20px;
        ">
            📦 My Orders
        </h1>
    """

    # NO ORDERS
    if not orders:

        html += """
        <div class="order-card">

            <h2>No Orders Yet</h2>

            <a href="/orders"
                style="
                    display:inline-block;
                    margin-top:20px;
                    background:#ffd814;
                    padding:14px 26px;
                    font-size:20px;
                    text-align:center;
                    text-decoration:none;
                    color:black;
                    border-radius:60px;
                    font-weight:bold;
                ">
                    Continue Shopping
            </a>

        </div>
        """

    # ORDERS LOOP
    for o in orders:

        order_id = o[0]
        items = o[1]
        total = o[2]
        created = o[3]
        received = o[4]
        status = o[5] if o[5] else "Ordered"

        # PROGRESS WIDTH
        progress_width = (
            "12%" if status == "Ordered"
            else "32%" if status == "Packed"
            else "55%" if status == "Shipped"
            else "80%" if status == "Out For Delivery"
            else "100%"
        )

        html += f"""
        <div class="order-card">

            <!-- TOP -->
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                flex-wrap:wrap;
                gap:10px;
                margin-bottom:20px;
            ">

                <h2 style="
                    margin:0;
                    color:green;
                    font-size:28px;
                ">
                    ₹{total}
                </h2>

                <div style="
                    color:gray;
                    font-size:13px;
                ">
                    {created}
                </div>

            </div>
        """

        # PRODUCTS
        for item in items.splitlines():

            try:

                parts = item.split("|||")

                name = parts[0]

                if parts[1].startswith("http"):

                    image = parts[1]
                    qty = parts[2]

                else:

                    qty = parts[1]
                    image = parts[2]

                html += f"""
                <div style="
                    background:#f9f9f9;
                    border-radius:15px;
                    padding:18px;
                    margin-top:20px;
                    border:1px solid #ddd;
                ">

                    <div class="flex-box"
                    style="
                        display:flex;
                        gap:25px;
                        align-items:center;
                        flex-wrap:wrap;
                    ">

                        <!-- LEFT -->
                        <div class="left-box"
                        style="
                            width:220px;
                            text-align:center;
                        ">

                            <img src="{image}"
                            onerror="this.src='https://via.placeholder.com/250'"
                            class="product-img"
                            style="
                                width:170px;
                                height:170px;
                                object-fit:cover;
                                border-radius:12px;
                                background:white;
                                border:1px solid #ddd;
                            ">

                            <h2 style="
                                margin-top:15px;
                                font-size:26px;
                                color:#111;
                            ">
                                {name}
                            </h2>

                            <p style="
                                font-size:18px;
                                font-weight:bold;
                                color:#555;
                            ">
                                Quantity: {qty}
                            </p>

                        </div>

                        <!-- RIGHT -->
                        <div class="right-box"
                        style="
                            flex:1;
                            min-width:280px;
                            background:white;
                            padding:22px;
                            border-radius:15px;
                            border:1px solid #eee;
                        ">

                            <!-- STATUS -->
                            <div class="status-text"
                            style="
                                font-size:30px;
                                font-weight:bold;
                                margin-bottom:25px;
                                color:#111;
                            ">
                                🚚 {status}
                            </div>

                            <!-- TRACK -->
                            <div style="
                                margin-top:20px;
                            ">

                                <!-- LINE -->
                                <div style="
                                    position:relative;
                                    height:8px;
                                    background:#ddd;
                                    border-radius:20px;
                                    overflow:visible;
                                ">

                                    <!-- GREEN LINE -->
                                    <div style="
                                        position:absolute;
                                        left:0;
                                        top:0;
                                        height:100%;
                                        width:{progress_width};
                                        background:#28a745;
                                        border-radius:20px;
                                        transition:1s;
                                    "></div>

                                    <!-- TRUCK -->
                                    <div class="truck"
                                    style="
                                        position:absolute;
                                        top:-30px;
                                        left:calc({progress_width} - 28px);
                                        font-size:39px;
                                        transition:1s;
                                        animation:{
                                            'none' if status == 'Delivered'
                                            else 'truckmove 0.8s infinite'
                                        };
                                    ">
                                        🚚
                                    </div>

                                </div>

                                <!-- STEPS -->
                                <div class="steps"
                                style="
                                    display:flex;
                                    justify-content:space-between;
                                    margin-top:18px;
                                    font-size:12px;
                                    font-weight:bold;
                                    color:#555;
                                    flex-wrap:wrap;
                                    gap:10px;
                                ">

                                    <span>Ordered</span>

                                    <span>Packed</span>

                                    <span>Shipped</span>

                                    <span>Out For Delivery</span>

                                    <span>Delivered</span>

                                </div>

                            </div>
                """

                # SHOW BUTTON ONLY AFTER DELIVERED
                if status == "Delivered":

                    # ORDER RECEIVED
                    if not received:

                        html += f"""
                        <div style="
                            text-align:center;
                            margin-top:25px;
                        ">

                            <a href="/received/{order_id}"
                            style="
                                display:inline-block;
                                background:green;
                                color:white;
                                text-decoration:none;
                                padding:12px 25px;
                                border-radius:10px;
                                font-size:16px;
                                font-weight:bold;
                            ">
                                Order Received
                            </a>

                        </div>
                        """

                    # RETURN BUTTON
                    else:

                        html += f"""
                        <div style="
                            text-align:center;
                            margin-top:25px;
                        ">

                            <form method="post"
                            action="/return_order">

                                <input
                                type="hidden"
                                name="product"
                                value="{name}">

                                <input
                                type="hidden"
                                name="order_time"
                                value="{created}">

                                <button type="submit"
                                style="
                                    background:red;
                                    color:white;
                                    border:none;
                                    padding:12px 25px;
                                    border-radius:10px;
                                    cursor:pointer;
                                    font-size:16px;
                                    font-weight:bold;
                                ">
                                    Return Product
                                </button>

                            </form>

                        </div>
                        """

                html += """
                        </div>

                    </div>

                </div>
                """

            except:
                pass

        html += "</div>"

    html += """
    </div>

    </body>

    </html>
    """

    cur.close()
    conn.close()

    return html
# ---------------- RECEIVED ----------------
@ShopBoss.route("/received/<int:id>")
def received(id):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE orders SET received=TRUE WHERE id=%s",
        (id,)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/orders")
# ---------------- RETURN ORDER ----------------
@ShopBoss.route("/return_order", methods=["POST"])
def return_order():

    from datetime import datetime

    if not session.get("user"):
        return redirect("/login")

    product = request.form["product"]
    order_time = request.form["order_time"]

    # CHECK 2 DAYS
    order_date = datetime.strptime(
        str(order_time).split(".")[0],
        "%Y-%m-%d %H:%M:%S"
    )

    now = datetime.now()

    difference = now - order_date

    # MORE THAN 2 DAYS
    if difference.total_seconds() >= 1800:

        return """
        <div style="
            height:100vh;
            display:flex;
            justify-content:center;
            align-items:center;
            background:#eaeded;
            font-family:Arial;
        ">

            <div style="
                background:white;
                padding:40px;
                border-radius:12px;
                text-align:center;
            ">

                <h1 style="color:red;">✖</h1>

                <h2>Order Can Not Be Returned Now</h2>

                <a href="/orders"
                style="
                    display:inline-block;
                    margin-top:20px;
                    background:#ffd814;
                    padding:14px 26px;
                    font-size:18px;;
                    text-decoration:none;
                    color:black;
                    border-radius:6px;
                    font-weight:bold;
                ">
                    Back To Orders
                </a>

            </div>

        </div>
        """

    # SEND RETURN REQUEST
    message = f"""
RETURN REQUEST

User: {session.get('user')}

Product: {product}
"""

    requests.post(
        "https://api.emailjs.com/api/v1.0/email/send",
        headers={
            "Content-Type":"application/json"
        },
        json={
            "service_id":"service_shopboss",
            "template_id":"template_shopboss",
            "user_id":"9bTfVOFVe_u1Mt51L",
            "template_params":{
                "name":session.get("user"),
                "email":"kfayizwani@gmail.com",
                "message":message
            }
        }
    )

    return f"""
    <div style="
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        background:#eaeded;
        font-family:Arial;
    ">

        <div style="
            background:white;
            padding:40px;
            border-radius:12px;
            text-align:center;
        ">

            <h1 style="color:green;">✔</h1>

            <h2>Return Request Sent</h2>

            <p>{product}</p>

            <a href="/orders"
            style="
                display:inline-block;
                margin-top:20px;
                background:#ffd814;
                padding:12px 20px;
                text-decoration:none;
                color:black;
                border-radius:6px;
                font-weight:bold;
            ">
                Back To Orders
            </a>

        </div>

    </div>
    """
# ---------------- FAVICON ----------------
@ShopBoss.route("/favicon.ico")
def favicon():
    from flask import send_from_directory
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")

# ---------------- GOOGLE VERIFICATION ----------------
@ShopBoss.route("/google0e3bd8ae06ba190d.html")
def google_verify():
    return "google-site-verification: google0e3bd8ae06ba190d.html"

# ---------------- ROBOTS.TXT ----------------
@ShopBoss.route("/robots.txt")
def robots():
    from flask import Response
    content = """User-agent: *
Allow: /
Sitemap: https://www--shopboss.replit.app/sitemap.xml
"""
    return Response(content, mimetype="text/plain")

# ---------------- SITEMAP.XML ----------------
@ShopBoss.route("/sitemap.xml")
def sitemap():
    from flask import Response
    base = "https://www--shopboss.replit.app"
    urls = [
        "/",
        "/home",
        "/home?category=Cricket",
        "/home?category=Football",
        "/home?category=Fashion",
        "/home?category=Shoes",
        "/home?category=Electronics",
        "/home?category=Kitchen",
        "/home?category=Garden",
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{base}{u}</loc></url>\n"
    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")

# ---------------- LOGOUT ----------------
@ShopBoss.route("/logout")
def logout():

    session.clear()

    return redirect("/splash")
# ---------------- RUN ----------------
# ---------------- RUN ----------------
if __name__ == "__main__":

    init_db()

    ShopBoss.run(
        host="0.0.0.0",
        port=5500
    )
