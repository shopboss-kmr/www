from flask import Flask, request, redirect, session, send_from_directory
import psycopg2
import requests
import os
from werkzeug.utils import secure_filename

# ---------------- APP ----------------
def send_order_email(username, items_text, grand_total, payment_method):
    try:
        requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            headers={"Content-Type": "application/json"},
            json={
                "service_id": "service_shopboss2",
                "template_id": "template_3jp7vty",
                "user_id": "9bTfVOFVe_u1Mt51L",
                "template_params": {
                    "name": username,
                    "email": "kfayizwani@gmail.com",
                    "message":
                     "NEW ORDER RECEIVED\n\nUser: " + username + "\n\nAmount: Rs." + str(grand_total) + "\n\nPayment: " + payment_method + "\n\nItems: " + items_text
                }
            }
        )()
    except:
        pass
ShopBoss = Flask(__name__)
ShopBoss.secret_key = "fayiz_shopboss_secure_2026_ultra"

# ----------------UPLOADS 1 -------------------

UPLOAD_FOLDER = "static/uploads"
ShopBoss.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    # ADD STOCK COLUMN IF OLD TABLE EXISTS
    try:
        cur.execute("""
        ALTER TABLE products
        ADD COLUMN stock INTEGER DEFAULT 100
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

    # REVIEWS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews(
        id SERIAL PRIMARY KEY,
        product_id INTEGER,
        username TEXT,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
# ---------------- REVIEW HELPERS ----------------
def avg_stars(product_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT rating FROM reviews WHERE product_id=%s", (product_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if not rows:
        return "☆☆☆☆☆ (No reviews)"
    avg = sum(r[0] for r in rows) / len(rows)
    full = int(avg)
    half = 1 if avg - full >= 0.5 else 0
    empty_n = 5 - full - half
    stars = "★" * full + ("½" if half else "") + "☆" * empty_n
    return f"{stars} ({len(rows)})"

# --------- HEADER -------------#
def header():

    cart_count = sum(session.get("cart", {}).values())

    return f"""
<!DOCTYPE html>
<html>

<head>
<meta name="viewport" content="width=device-width, initial-scale=0.67">

<style>

*{{
    box-sizing:border-box;
}}

body{{
    margin:0;
    font-family:Arial;
    background:#eaeded;
}}

.topbar{{
    background:#131921;
    height:58px;
    display:flex;
    align-items:center;
    padding:0 12px;
    gap:10px;
    position:sticky;
    top:0;
    z-index:999;
}}

.logo{{
    color:#ff9900;
    text-decoration:none;
    font-size:24px;
    font-weight:bold;
    white-space:nowrap;
}}

.search-form{{
    flex:1;
    display:flex;
    align-items:center;
}}

.search-input{{
    flex:1;
    height:38px;
    border:none;
    outline:none;
    padding:0 12px;
    font-size:14px;
    border-radius:4px 0 0 4px;
    text-align:left;
}}

.search-btn{{
    height:38px;
    width:60px;
    border:none;
    background:#febd69;
    cursor:pointer;
    font-weight:bold;
    border-radius:0 4px 4px 0;
}}

.search-btn:hover{{
    background:#f3a847;
}}

.nav{{
    display:flex;
    align-items:center;
    gap:14px;
}}

.nav a{{
    color:white;
    text-decoration:none;
    font-size:13px;
    font-weight:bold;
}}

.nav a:hover{{
    color:#febd69;
}}

.cart-count{{
    color:#ff9900;
}}

@media(max-width:850px){{

    .topbar{{
        height:auto;
        padding:6px 8px;
        gap:8px;
        flex-wrap:nowrap;
        overflow:visible;
    }}

    .logo{{
        font-size:14px;
        flex-shrink:0;
    }}

    .search-form{{
        flex:1 1 0;
        min-width:0;
    }}

    .search-input{{
        height:30px;
        font-size:11px;
        padding:0 6px;
        min-width:0;
        width:100%;
    }}

    .search-btn{{
        height:30px;
        width:46px;
        font-size:10px;
        flex-shrink:0;
    }}

    .nav{{
        gap:8px;
        flex-shrink:0;
        flex-wrap:nowrap;
    }}

    .nav a{{
        font-size:11px;
        white-space:nowrap;
    }}

}}

</style>
</head>

<body>

<div class="topbar">

    <a href="/home" class="logo">
        ShopBoss
    </a>

    <form action="/home" method="get" class="search-form">

        <input
        type="text"
        name="q"
        class="search-input"
        placeholder="Search products">

        <button class="search-btn">
            Search
        </button>

    </form>

    <div class="nav">

        <a href="/home">
            Home
        </a>

        <a href="/cart">
            Cart
                ({cart_count})

        </a>

        <a href="/logout">
            Logout
        </a>

    </div>

</div>


<script>

// SECRET ADMIN SHORTCUT
document.addEventListener("keydown", function(e){{

    if(e.shiftKey && e.key.toLowerCase() === "z"){{
        window.location.href = "/admin";
    }}

}});

</script>
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

        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="robots" content="index, follow">
        <meta name="description" content="ShopBoss — Kashmir's first online shopping app. Buy Cricket, Football, Fashion, Electronics, Kitchen & more at best prices. Developed by Ahmad Fayiz.">
        <meta name="keywords" content="ShopBoss, Kashmir shopping, online shopping Kashmir, buy cricket gear, electronics Kashmir, Ahmad Fayiz">
        <meta property="og:title" content="ShopBoss — Kashmir's First Shopping App">
        <meta property="og:description" content="Shop Cricket, Football, Fashion, Electronics & more. Best prices in Kashmir.">
        <meta property="og:url" content="https://www--shopbosskmr.replit.app">
        <meta property="og:type" content="website">
        <link rel="canonical" href="https://www--shopbosskmr.replit.app/splash">

        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <link rel="icon" type="image/png" sizes="512x512" href="/favicon-512.png">
        <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png">
        <link rel="manifest" href="/site.webmanifest">
        <link rel="shortcut icon" href="/favicon.ico">

        <style>

            *{ box-sizing:border-box; }

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
                padding:20px;
            }

            h1{
                color:#ff9900;
                font-size:clamp(36px, 10vw, 70px);
                margin:0;
            }

            p{
                color:white;
                font-size:clamp(14px, 3.5vw, 20px);
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

            <h1>Welcome To ShopBoss</h1>

            <p>Kashmir's First Shopping App By Ahmad Fayiz</p>

            <div class="loader"></div>

        </div>

    </body>

    <script>setTimeout(function(){ window.location="/check"; }, 3000);</script>
    </html>
    """
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

    <meta name="viewport" content="width=device-width, initial-scale=0.67">
    <meta name="robots" content="index, follow">
    <meta name="description" content="ShopBoss — Shop Cricket, Football, Fashion, Electronics, Kitchen & more at best prices in Kashmir.">
    <meta name="keywords" content="ShopBoss, Kashmir online shopping, cricket gear Kashmir, electronics, fashion">
    <meta property="og:title" content="ShopBoss — Kashmir's First Shopping App">
    <meta property="og:description" content="Shop Cricket, Football, Fashion, Electronics & more. Best prices in Kashmir.">
    <meta property="og:url" content="https://www--shopbosskmr.replit.app/home">
    <meta property="og:type" content="website">
    <link rel="canonical" href="https://www--shopbosskmr.replit.app/home">
    <link rel="icon" type="image/png" sizes="512x512" href="/favicon-512.png">
    <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
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

        <a class="cat" href="/home?category=Decoration">🎉 Decoration</a>

        <a class="cat" href="/home?category=House">🏠 House Hold</a>

        <a class="cat" href="/orders">📦 My Orders</a>

    </div>

    <!-- PRODUCTS -->
    <div class="products">
    """

    for p in products:

        category = p[4] if len(p) > 4 else "General"
        stock = p[5] if len(p) > 5 else 100

        html += f"""
        <div class="card">

            <img src="{p[3]}" onclick="openImg('{p[3]}')" style="cursor:zoom-in;">

            <a href="/product/{p[0]}" style="text-decoration:none;color:inherit;">
        <div class="name">
                {p[1]}
            </div>
            </a>

            <div class="category">
                {category}
            </div>

            <div style="font-size:13px;color:#e47911;margin:2px 0 2px;">
                {avg_stars(p[0])}
            </div>

            <div class="price">
                ₹{p[2]}
            </div>

            {"<a href='/add/"+str(p[0])+"' class='btn'>Add To Cart</a>" if stock > 0 else "<div class='btn' style='background:#ccc;color:#666;cursor:not-allowed;'>Sold Out</div>"}
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

# ---------------- PRODUCT DETAIL ----------------
@ShopBoss.route("/product/<int:pid>")
def product_detail(pid):
    if not session.get("user"):
        return redirect("/login")
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s", (pid,))
    p = cur.fetchone()
    if not p:
        cur.close(); conn.close()
        return redirect("/home")
    cur.execute("SELECT username, rating, comment, created_at FROM reviews WHERE product_id=%s ORDER BY created_at DESC", (pid,))
    revs = cur.fetchall()
    cur.close(); conn.close()
    stock = p[5] if len(p) > 5 else 100
    user = session.get("user", "")
    already = any(r[0] == user for r in revs)
    avg = avg_stars(pid)

    reviews_html = ""
    for r in revs:
        stars = "★" * r[1] + "☆" * (5 - r[1])
        reviews_html += f"""<div style="border-bottom:1px solid #eee;padding:10px 0;">
            <b>{r[0]}</b> <span style="color:#e47911;">{stars}</span>
            <div style="color:#555;margin-top:4px;">{r[2]}</div>
            <div style="font-size:11px;color:#aaa;">{r[3].strftime("%d %b %Y") if r[3] else ""}</div>
        </div>"""

    review_form = ""
    if user and not already:
        review_form = f"""<form method="post" action="/review/{pid}" style="margin-top:18px;" onsubmit="return checkRating()">
            <input type="hidden" name="rating" id="ratingVal" value="">
            <div style="font-weight:bold;margin-bottom:10px;font-size:15px;">Leave a Review</div>
            <div style="margin-bottom:12px;">
                <div style="font-size:13px;color:#555;margin-bottom:6px;">Tap a star to rate:</div>
                <div id="starRow" style="display:flex;gap:6px;cursor:pointer;">
                    <span onclick="setRating(1)" style="font-size:34px;color:#ccc;" data-val="1">☆</span>
                    <span onclick="setRating(2)" style="font-size:34px;color:#ccc;" data-val="2">☆</span>
                    <span onclick="setRating(3)" style="font-size:34px;color:#ccc;" data-val="3">☆</span>
                    <span onclick="setRating(4)" style="font-size:34px;color:#ccc;" data-val="4">☆</span>
                    <span onclick="setRating(5)" style="font-size:34px;color:#ccc;" data-val="5">☆</span>
                </div>
                <div id="ratingLabel" style="font-size:12px;color:#888;margin-top:4px;">No rating selected</div>
            </div>
            <textarea name="comment" placeholder="Write your review (optional)..." rows="3"
                style="width:100%;padding:8px;box-sizing:border-box;border:1px solid #ccc;border-radius:4px;font-size:13px;resize:vertical;"></textarea>
            <button type="submit"
                style="margin-top:10px;background:#ffd814;border:none;padding:10px 26px;border-radius:4px;cursor:pointer;font-weight:bold;font-size:14px;">
                Submit Review
            </button>
            <script>
            var chosen = 0;
            var labels = ["","Terrible","Poor","Okay","Good","Excellent"];
            function setRating(n){{
                chosen = n;
                document.getElementById("ratingVal").value = n;
                var stars = document.getElementById("starRow").children;
                for(var i=0;i<5;i++){{
                    stars[i].textContent = i < n ? "★" : "☆";
                    stars[i].style.color = i < n ? "#e47911" : "#ccc";
                }}
                document.getElementById("ratingLabel").textContent = n + " star" + (n>1?"s":"") + " — " + labels[n];
            }}
            function checkRating(){{
                if(!chosen){{ alert("Please select a star rating first!"); return false; }}
                return true;
            }}
            // Hover effects
            document.getElementById("starRow").addEventListener("mouseover", function(e){{
                if(e.target.dataset.val){{
                    var n = parseInt(e.target.dataset.val);
                    var stars = this.children;
                    for(var i=0;i<5;i++){{
                        stars[i].textContent = i < n ? "★" : "☆";
                        stars[i].style.color = i < n ? "#e47911" : "#ccc";
                    }}
                }}
            }});
            document.getElementById("starRow").addEventListener("mouseleave", function(){{
                setRating(chosen);
                if(!chosen){{
                    var stars = this.children;
                    for(var i=0;i<5;i++){{
                        stars[i].textContent="☆";
                        stars[i].style.color="#ccc";
                    }}
                }}
            }});
            </script>
        </form>"""
    elif already:
        review_form = '<div style="color:#888;margin-top:14px;font-size:13px;">You have already reviewed this product.</div>'
    else:
        review_form = '<div style="color:#888;margin-top:14px;font-size:13px;"><a href="/login">Login</a> to leave a review.</div>'

    add_btn = f"<a href='/add/{pid}' style='display:inline-block;background:#ffd814;border:none;padding:10px 28px;border-radius:6px;cursor:pointer;font-weight:bold;text-decoration:none;color:#111;'>Add To Cart</a>" if stock > 0 else "<div style='display:inline-block;background:#ccc;color:#666;padding:10px 28px;border-radius:6px;'>Sold Out</div>"

    html = header() + f"""<html><head>
    <title>{p[1]} - ShopBoss</title>
    <meta name="viewport" content="width=device-width,initial-scale=0.67">
    <style>
    body{{margin:0;background:#eaeded;font-family:Arial;}}
    .pd-wrap{{max-width:860px;margin:30px auto;background:white;border-radius:10px;padding:28px;box-shadow:0 2px 12px rgba(0,0,0,0.08);}}
    .pd-top{{display:flex;gap:28px;flex-wrap:wrap;}}
    .pd-img{{width:260px;max-width:100%;border-radius:8px;object-fit:contain;}}
    .pd-info{{flex:1;min-width:200px;}}
    .pd-name{{font-size:22px;font-weight:bold;margin-bottom:8px;}}
    .pd-price{{font-size:20px;color:#B12704;font-weight:bold;margin-bottom:6px;}}
    .pd-cat{{font-size:13px;color:#888;margin-bottom:8px;}}
    .pd-avg{{font-size:16px;color:#e47911;margin-bottom:14px;}}
    .pd-back{{display:inline-block;margin-bottom:20px;color:#007185;font-size:13px;text-decoration:none;}}
    @media(max-width:600px){{.pd-top{{flex-direction:column;}}.pd-img{{width:100%;}}}}
    </style></head><body>
    <div class="pd-wrap">
        <a href="/home" class="pd-back">&larr; Back to Home</a>
        <div class="pd-top">
            <img src="{p[3]}" class="pd-img">
            <div class="pd-info">
                <div class="pd-name">{p[1]}</div>
                <div class="pd-price">₹{p[2]}</div>
                <div class="pd-cat">{p[4] if len(p) > 4 else ""}</div>
                <div class="pd-avg">{avg}</div>
                {add_btn}
            </div>
        </div>
        <hr style="margin:24px 0;">
        <div style="font-size:18px;font-weight:bold;margin-bottom:12px;">Customer Reviews</div>
        {reviews_html if reviews_html else '<div style="color:#999;font-size:13px;">No reviews yet. Be the first!</div>'}
        {review_form}
    </div></body></html>"""
    return html

# ---------------- SUBMIT REVIEW ----------------
@ShopBoss.route("/review/<int:pid>", methods=["POST"])
def submit_review(pid):
    user = session.get("user")
    if not user:
        return redirect("/login")
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()
    rating = max(1, min(5, rating))
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM reviews WHERE product_id=%s AND username=%s", (pid, user))
    if not cur.fetchone():
        cur.execute("INSERT INTO reviews(product_id, username, rating, comment) VALUES(%s,%s,%s,%s)",
                    (pid, user, rating, comment))
        conn.commit()
    cur.close(); conn.close()
    return redirect(f"/product/{pid}")

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

        cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        exists = cur.fetchone()

        if exists:
            cur.close()
            conn.close()
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=0.67">
                <title>Username Taken – ShopBoss</title>
                <link rel="icon" type="image/png" sizes="512x512" href="/favicon-512.png">
                <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png">
                <link rel="manifest" href="/site.webmanifest">
            </head>
            <body style="margin:0;font-family:Arial;background:#f2f2f2;">
            <div style="
                display:flex;
                justify-content:center;
                align-items:center;
                min-height:100vh;
                padding:20px;
                box-sizing:border-box;
            ">
                <div style="
                    background:white;
                    border-radius:16px;
                    padding:40px 32px;
                    max-width:360px;
                    width:100%;
                    text-align:center;
                    box-shadow:0 4px 20px rgba(0,0,0,0.1);
                ">
                    <div style="font-size:56px;margin-bottom:16px;">😕</div>

                    <h2 style="margin:0 0 10px;font-size:22px;color:#111;">
                        Username Already Taken
                    </h2>

                    <p style="color:#555;font-size:14px;margin:0 0 28px;line-height:1.6;">
                        <strong style="color:#111;">@{username}</strong> is already in use.<br>
                        Do you want to log in instead?
                    </p>

                    <a href="/login"
                    style="
                        display:block;
                        background:#ffd814;
                        color:#111;
                        text-decoration:none;
                        padding:12px;
                        border-radius:8px;
                        font-weight:bold;
                        font-size:15px;
                        margin-bottom:12px;
                    ">
                        Yes, Log Me In
                    </a>

                    <a href="/signup"
                    style="
                        display:block;
                        background:#f2f2f2;
                        color:#333;
                        text-decoration:none;
                        padding:12px;
                        border-radius:8px;
                        font-weight:bold;
                        font-size:15px;
                    ">
                        Try a Different Username
                    </a>

                </div>
            </div>
            </body>
            </html>
            """

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
        <meta name="viewport" content="width=device-width, initial-scale=0.67">
        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <meta name="description" content="ShopBoss — Online shopping for Cricket, Football, Fashion, Shoes, Electronics, Kitchen & more. Best prices in Kashmir. Developed by Ahmad Fayiz.">
        <meta name="robots" content="index, follow">
        <link rel="icon" type="image/png" sizes="512x512" href="/favicon-512.png">
        <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png">
        <link rel="manifest" href="/site.webmanifest">
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


            <p style="text-align:center;margin-top:12px;font-size:14px;">
                Already have an account?
                <a href="/login" style="color:#ff9900;text-decoration:none;font-weight:bold;">Login</a>
            </p>

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
        width:320px;
        box-shadow:0 2px 10px rgba(0,0,0,0.1);
    ">

        <h1 style="
            color:red;
            font-size:60px;
            margin:0;
        ">
            ✖
        </h1>

        <h2 style="margin-top:10px;">
            Invalid Login
        </h2>

        <p style="color:#666;">
            Wrong username or password
        </p>

        <a href="/login"
        style="
            display:inline-block;
            margin-top:20px;
            background:#ffd814;
            padding:12px 22px;
            text-decoration:none;
            color:black;
            border-radius:6px;
            font-weight:bold;
        ">
            Try Again
        </a>

    </div>

</div>
"""

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=0.67">
        <title>ShopBoss • Developed by Ahmad Fayiz</title>
        <meta name="description" content="ShopBoss — Online shopping for Cricket, Football, Fashion, Shoes, Electronics, Kitchen & more. Best prices in Kashmir. Developed by Ahmad Fayiz.">
        <meta name="robots" content="index, follow">
        <link rel="icon" type="image/png" sizes="512x512" href="/favicon-512.png">
        <link rel="apple-touch-icon" sizes="512x512" href="/apple-touch-icon.png">
        <link rel="manifest" href="/site.webmanifest">
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


            <p style="text-align:center;margin-top:12px;font-size:14px;">
                New here?
                <a href="/signup" style="color:#ff9900;text-decoration:none;font-weight:bold;">Create an account</a>
            </p>

        </form>

    </div>
    </body>
    </html>
    """

# ---------------- ADD TO CART ----------------
@ShopBoss.route("/add/<int:id>")
def add(id):

    conn2 = db()
    cur2 = conn2.cursor()
    cur2.execute("SELECT stock FROM products WHERE id=%s", (id,))
    pstock = cur2.fetchone()
    cur2.close()
    conn2.close()
    if pstock and pstock[0] <= 0:
        return redirect("/home")
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
    total_items = sum(session.get("cart", {}).values())
    delivery_charge = 20 * total_items

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
            top:7px;
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
                Enter
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

    # ---------------- POST ----------------
    if request.method == "POST":

        # ADD PRODUCT
        if "add" in request.form:

            image = ""

            image_file = request.files.get("image")

            if image_file and image_file.filename:

                filename = secure_filename(image_file.filename)

                filepath = os.path.join(
                    ShopBoss.config["UPLOAD_FOLDER"],
                    filename
                )

                image_file.save(filepath)

                image = "/" + filepath.replace("\\", "/")

            cur.execute(
                """
                INSERT INTO products
                (name,price,image,category)
                VALUES(%s,%s,%s,%s)
                """,
                (
                    request.form["name"],
                    request.form["price"],
                    image,
                    request.form["category"]
                )
            )

        # UPDATE PRODUCT
        elif "update" in request.form:

            image = request.form["old_image"]

            image_file = request.files.get("image")

            if image_file and image_file.filename:

                filename = secure_filename(image_file.filename)

                filepath = os.path.join(
                    ShopBoss.config["UPLOAD_FOLDER"],
                    filename
                )

                image_file.save(filepath)

                image = "/" + filepath.replace("\\", "/")

            cur.execute(
                """
                UPDATE products
                SET
                    name=%s,
                    price=%s,
                    image=%s,
                    category=%s
                WHERE id=%s
                """,
                (
                    request.form["name"],
                    request.form["price"],
                    image,
                    request.form["category"],
                    request.form["id"]
                )
            )

        # DELETE PRODUCT
        elif "delete" in request.form:

            cur.execute(
                "DELETE FROM products WHERE id=%s",
                (request.form["id"],)
            )

        conn.commit()

    cur.execute(
        "SELECT * FROM products ORDER BY id DESC"
    )

    products = cur.fetchall()

    html = header()

    html += """
    <div style="
        background:#eaeded;
        min-height:100vh;
        padding:25px;
        font-family:Arial;
    ">

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

        <div style="
            background:white;
            padding:20px;
            border-radius:10px;
            margin-bottom:25px;
            box-shadow:0 2px 8px rgba(0,0,0,0.1);
        ">

            <h2>Add Product</h2>

            <form method="post"
            enctype="multipart/form-data"
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

                <label style="
                    flex:2;
                    padding:10px;
                    border:1px solid #ccc;
                    background:white;
                    cursor:pointer;
                    border-radius:2px;
                    display:flex;
                    align-items:center;
                ">
                    Upload Image

                    <input
                    type="file"
                    name="image"
                    accept="image/*"
                    required
                    style="display:none;">
                </label>

                <select
                name="category"
                required
                style="padding:10px;">

                    <option value="">Category</option>
                    <option>Cricket</option>
                    <option>Football</option>
                    <option>Fashion</option>
                    <option>Toys</option>
                    <option>Electronics</option>
                    <option>Kitchen</option>
                    <option>Garden</option>
                    <option>Decoration</option>
                    <option>House Hold</option>

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

        <div style="
            display:grid;
            grid-template-columns:
            repeat(auto-fill,minmax(280px,1fr));
            gap:20px;
        ">
    """

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
            enctype="multipart/form-data"
            style="
                margin-top:12px;
                display:flex;
                flex-direction:column;
                gap:10px;
            ">

                <input type="hidden" name="id" value="{p[0]}">

                <input type="hidden"
                name="old_image"
                value="{p[3]}">

                <input
                name="name"
                value="{p[1]}"
                style="padding:10px;">

                <input
                name="price"
                value="{p[2]}"
                style="padding:10px;">

                <input
                type="file"
                name="image"
                accept="image/*">

                <select
                name="category"
                style="padding:10px;">

                    <option {"selected" if category=="Cricket" else ""}>Cricket</option>
                    <option {"selected" if category=="Football" else ""}>Football</option>
                    <option {"selected" if category=="Fashion" else ""}>Fashion</option>
                    <option {"selected" if category=="Toys" else ""}>Toys</option>
                    <option {"selected" if category=="Electronics" else ""}>Electronics</option>
                    <option {"selected" if category=="Kitchen" else ""}>Kitchen</option>
                    <option {"selected" if category=="Garden" else ""}>Garden</option>
                    <option {"selected" if category=="Decoration" else ""}>Decoration</option>
                    <option {"selected" if category=="House Hold" else ""}>House Hold</option>

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
# ------------------UPLOADS-------------------
@ShopBoss.route("/static/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(
        "static/uploads",
        filename
    )
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
            border-radius:20px;
            margin-bottom:40px;
            font-weight:bold;
        ">

            <h2>Order No {o[0]}</h2>

            <p>Customer:- {o[1]}</p>

            <p>Total Amount: ₹{o[2]}</p>

            <p>Status: {o[3]}</b></p>

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
# ------------- ADDRESS --------------
# ------------- ADDRESS --------------
@ShopBoss.route("/address", methods=["GET", "POST"])
def address():

    if not session.get("user"):
        return redirect("/login")

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        mobile = request.form["mobile"]
        address = request.form["address"]
        payment = request.form["payment"]

        # =========================
        # MOBILE VALIDATION
        # =========================
        if len(mobile) != 10 or not mobile.isdigit():
            return """
            <h2 style='color:red;text-align:center;margin-top:50px;'>
                Dear Customer,Your Mobile Number Is Invalid
            </h2>
            """

        conn = db()
        cur = conn.cursor()

        total = 0
        items_text = ""

        # =========================
        # CALCULATE TOTAL
        # =========================
        for pid, qty in session.get("cart", {}).items():

            cur.execute(
                "SELECT name,price,image,stock FROM products WHERE id=%s",
                (pid,)
            )

            p = cur.fetchone()

            if p:

                name = p[0]
                price = p[1]
                image = p[2]
                stock = p[3]

                # STOCK CHECK
                if stock < qty:
                    return f"""
                    <h2 style='color:red;text-align:center;margin-top:50px;'>
                        {name} is out of stock
                    </h2>
                    """

                subtotal = price * qty

                total += subtotal

                # =========================
                # FIXED ITEMS TEXT
                # =========================
                items_text += f"{name}|||{qty}|||{image}\n"

        delivery_charge = 20 * sum(session.get("cart", {}).values())

        grand_total = total + delivery_charge

        # ======================================================
        # ONLINE PAYMENT
        # ======================================================
        if payment == "Online Payment":

            upi_id = "7006219128@ybl"
            name = "ShopBoss"
            note = "Pay To ShopBoss"

            upi_url = (
                f"upi://pay?pa={upi_id}"
                f"&pn={name}"
                f"&am={grand_total}"
                f"&cu=INR"
                f"&tn={note}"
            )

            # SAVE ORDER BEFORE PAYMENT
            cur.execute("""
                INSERT INTO orders(username,items,total,status)
                VALUES(%s,%s,%s,%s)
            """, (
                session.get("user"),
                items_text,
                grand_total,
                "Payment Pending"
            ))

            conn.commit()

            send_order_email(
                session.get("user",""),
                items_text,
                grand_total,
                "UPI - Payment Pending"
            )

            session["cart"] = {}

            return f"""
                        <html>
            <head>
                <meta name="viewport" content="width=device-width,initial-scale=0.67">
            </head>

            <body style="margin:0;font-family:Arial;background:#eaeded;">

            <div style="min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px;">

                <div style="background:white;padding:30px;max-width:400px;width:100%;border-radius:12px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,0.2);">

                    <div style="font-size:40px;margin-bottom:10px;">&#128722;</div>

                    <h2 style="color:#131921;margin:0 0 6px;">
                        Pay via UPI
                    </h2>

                    <p style="color:#555;font-size:13px;margin:0 0 20px;">
                        Open PhonePe, GPay, or Paytm and send the exact amount to the UPI ID below
                    </p>

                    <div style="background:#f5f5f5;border-radius:8px;padding:16px;margin-bottom:14px;">

                        <p style="margin:0 0 4px;font-size:12px;color:#888;">
                            UPI ID
                        </p>

                        <p style="margin:0;font-size:20px;font-weight:bold;color:#131921;letter-spacing:1px;" id="upiid">
                            {upi_id}
                        </p>

                        <button
                        onclick="navigator.clipboard.writeText('{upi_id}');this.innerText='Copied!';setTimeout(()=>this.innerText='Copy UPI ID',2000)"
                        style="
                            margin-top:10px;
                            background:#ffd814;
                            border:none;
                            padding:8px 20px;
                            border-radius:6px;
                            cursor:pointer;
                            font-weight:bold;
                            font-size:13px;
                        ">
                            Copy UPI ID
                        </button>

                    </div>

                    <div style="
                        background:#fff8e1;
                        border:2px solid #ffd814;
                        border-radius:8px;
                        padding:14px;
                        margin-bottom:18px;
                    ">

                        <p style="margin:0 0 4px;font-size:12px;color:#888;">
                            Amount to Pay
                        </p>

                        <p style="
                            margin:0;
                            font-size:28px;
                            font-weight:bold;
                            color:#131921;
                        ">
                            ₹{grand_total}
                        </p>

                    </div>

                    <ol style="
                        text-align:left;
                        font-size:13px;
                        color:#444;
                        margin:0 0 18px;
                        padding-left:18px;
                        line-height:2;
                    ">

                        <li>Copy the UPI ID above</li>

                        <li>Open PhonePe / GPay / Paytm</li>

                        <li>Tap <b>Send Money</b> or <b>Pay</b></li>

                        <li>
                            Paste UPI ID &amp; enter amount
                            <b>₹{grand_total}</b>
                        </li>

                        <li>Complete payment and come back</li>

                        <li>Then Click I Have Paid</li>

                    </ol>

                    <form action="/payment-success" method="post">

                        <input
                        type="hidden"
                        name="amount"
                        value="{grand_total}">

                        <button
                        type="submit"
                        style="
                            width:100%;
                            background:#ffd814;
                            border:none;
                            padding:13px;
                            border-radius:8px;
                            font-weight:bold;
                            font-size:16px;
                            cursor:pointer;
                        ">
                            I Have Paid &#10003;
                        </button>

                    </form>

                    <a href="/cart"
                    style="
                        display:block;
                        margin-top:12px;
                        color:#007185;
                        font-size:13px;
                    ">
                        ← Back to Cart
                    </a>

                </div>

            </div>

            </body>
            </html>
            """

        # ======================================================
        # CASH ON DELIVERY
        # ======================================================

        # STOCK UPDATE
        for pid, qty in session.get("cart", {}).items():

            cur.execute("""
                UPDATE products
                SET stock = stock - %s
                WHERE id=%s
            """, (qty, pid))

        # SAVE ORDER
        cur.execute("""
            INSERT INTO orders(username,items,total,status)
            VALUES(%s,%s,%s,%s)
        """, (
            session.get("user"),
            items_text,
            grand_total,
            "Ordered"
        ))

        conn.commit()

        send_order_email(
            session.get("user",""),
            items_text,
            grand_total,
            "Cash On Delivery"
        )

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
                border-radius:12px;
                text-align:center;
                width:400px;
            ">

                <h1 style="
                    color:green;
                    font-size:60px;
                ">
                    ✔
                </h1>

                <h2>
                    Order Placed Successfully
                </h2>

                <p>
                    Total Amount ₹{grand_total}
                </p>

                <a href="/"
                style="
                    display:inline-block;
                    margin-top:15px;
                    background:#ffd814;
                    padding:12px 20px;
                    text-decoration:none;
                    color:black;
                    font-weight:bold;
                    border-radius:8px;
                ">
                    Continue Shopping
                </a>

            </div>

        </div>
        """

    # =========================
    # GET UI
    # =========================

    return """
    <div style="
        display:flex;
        justify-content:center;
        align-items:center;
        min-height:100vh;
        background:#eaeded;
        font-family:Arial;
        padding:20px;
    ">

        <form method="post"
        style="
            background:white;
            padding:30px;
            width:380px;
            border-radius:12px;
            box-shadow:0 2px 10px rgba(0,0,0,0.1);
        ">

            <h2 style="text-align:center;">
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
            ">

            <input
            name="address"
            placeholder="Your Address"
            required
            style="
                width:100%;
                padding:12px;
                margin:10px 0;
            ">

            <h3>
                Payment Method
            </h3>

            <label style="
                display:block;
                margin:10px 0;
            ">
                <input
                type="radio"
                name="payment"
                value="Cash on Delivery"
                required>

                Cash on Delivery
            </label>

            <label style="
                display:block;
                margin:10px 0;
            ">
                <input
                type="radio"
                name="payment"
                value="Online Payment">

                Online Payment

            </label>

            <button style="
                width:100%;
                padding:12px;
                background:#ffd814;
                border:none;
                font-weight:bold;
                border-radius:6px;
                cursor:pointer;
            ">
                Place Order
            </button>

        </form>

    </div>
    """


# -------- PAYMENT SUCCESSFUL ------------

@ShopBoss.route("/payment-success", methods=["POST"])
def payment_success():

    username = session.get("user", "Unknown")
    amount = request.form.get("amount", "Unknown")

    # EMAIL ADMIN ABOUT CLAIMED PAYMENT
    try:
        requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            headers={"Content-Type": "application/json"},
            json={
                "service_id": "service_shopboss2",
                "template_id": "template_3jp7vty",
                "user_id": "9bTfVOFVe_u1Mt51L",
                "template_params": {
                    "name": username,
                    "email": "kfayizwani@gmail.com",
                    "message":
                    "PAYMENT CLAIMED\n"
                    "User: " + username +
                    "\nAmount: Rs." + str(amount) +
                    "\nPlease check UPI (7006219128@ybl) and verify.\n"
                    "Confirm in admin panel (all_orders)."
                }
            }
        )
    except:
        pass

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
            max-width:400px;
            width:90%;
            box-shadow:0 2px 10px rgba(0,0,0,0.15);
        ">
            <div style="font-size:50px;">
                &#9203;
            </div>

            <h2 style="
                color:#131921;
                margin:10px 0 6px;
            ">
                Order Placed!
            </h2>

            <p style="
                color:#555;
                font-size:14px;
                margin:0 0 16px;
            ">
                Your order is
                <b>awaiting payment verification</b>.
                <br>
                We will confirm it once we verify your UPI payment of
                <b>₹{amount}</b>.
            </p>

            <div style="
                background:#fff8e1;
                border:2px solid #ffd814;
                border-radius:8px;
                padding:12px;
                font-size:13px;
                color:#444;
                margin-bottom:20px;
            ">
                You will receive confirmation shortly after we check our UPI account.
            </div>

            <a href="/orders"
            style="
                display:inline-block;
                margin-top:5px;
                background:#ffd814;
                padding:12px 24px;
                text-decoration:none;
                color:black;
                font-weight:bold;
                border-radius:8px;
                margin-right:8px;
            ">
                My Orders
            </a>

            <a href="/home"
            style="
                display:inline-block;
                margin-top:5px;
                background:#131921;
                padding:12px 24px;
                text-decoration:none;
                color:white;
                font-weight:bold;
                border-radius:8px;
            ">
                Continue Shopping
            </a>

        </div>
    </div>
    """

---------------- DELETE SINGLE ORDER ----------------

@ShopBoss.route("/delete_order/int:order_id")
def delete_order(order_id):

if not session.get("user"):
    return redirect("/login")

conn = db()
cur = conn.cursor()

cur.execute("""
    DELETE FROM orders
    WHERE id=%s
    AND username=%s
    AND status='Delivered'
""", (order_id, session.get("user")))

conn.commit()

cur.close()
conn.close()

return redirect("/orders")
---------------- DELETE MULTIPLE ORDERS ----------------

@ShopBoss.route("/delete_orders", methods=["POST"])
def delete_orders():

if not session.get("user"):
    return redirect("/login")

order_ids = request.form.getlist("order_ids")

if order_ids:

    conn = db()
    cur = conn.cursor()

    for oid in order_ids:

        cur.execute("""
            DELETE FROM orders
            WHERE id=%s
            AND username=%s
            AND status='Delivered'
        """, (oid, session.get("user")))

    conn.commit()

    cur.close()
    conn.close()

return redirect("/orders")
---------------- ORDERS ----------------

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
        transform:scaleX(-1) translateX(-3px);
    }

    50%{
        transform:scaleX(-1) translateX(3px);
    }

    100%{
        transform:scaleX(-1) translateX(-3px);
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
        font-size:24px !important;
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
html += """ <form method="post" action="/delete_orders"> 
"""
    # ORDERS LOOP
    for o in orders:

        order_id = o[0]
        items = o[1]
        total = o[2]
        created = o[3]
        received = o[4]
        status = o[5] if o[5] else "Ordered"

        delete_checkbox = ""

        if status == "Delivered":
            delete_checkbox = f"""
            <label style="
                display:flex;
                align-items:center;
                gap:8px;
                color:red;
                font-weight:bold;
            ">
                <input
                    type="checkbox"
                    name="order_ids"
                    value="{order_id}"
                    style="width:20px;height:20px;">
                Select To Delete
            </label>
            """

        progress_width = (
            "12%" if status == "Ordered"
            else "32%" if status == "Packed"
            else "55%" if status == "Shipped"
            else "80%" if status == "Out For Delivery"
            else "0%" if status == "Payment Pending"
            else "100%"
        )

        html += f"""
        <div class="order-card">

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

                {delete_checkbox}

                <div style="
                    color:gray;
                    font-size:13px;
                ">
                    {created}
                </div>

            </div>
        """

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

                if not name.strip():
                    continue

                html += f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:16px;
                    background:#f9f9f9;
                    border-radius:14px;
                    padding:14px;
                    margin-bottom:12px;
                    border:1px solid #e0e0e0;
                ">
                    <img src="{image}"
                    onerror="this.src='https://via.placeholder.com/100'"
                    style="
                        width:90px;
                        height:90px;
                        object-fit:cover;
                        border-radius:10px;
                        border:1px solid #ddd;
                        flex-shrink:0;
                    ">
                    <div>

                        <div style="
                            font-size:17px;
                            font-weight:bold;
                            color:#111;
                            margin-bottom:5px;
                        ">
                            {name}
                        </div>

                        <div style="
                            font-size:14px;
                            color:#555;
                            font-weight:bold;
                        ">
                            Quantity: {qty}
                        </div>

                    </div>
                </div>
                """

            except:
                pass

        truck_left = (
            "2px"
            if status == "Payment Pending"
            else f"calc({progress_width} - 14px)"
        )

        truck_anim = (
            "none"
            if status == "Delivered"
            else "truckmove 0.8s infinite"
        )

        html += f"""
        <div style="
            font-size:22px;
            font-weight:bold;
            color:#111;
            margin:18px 0 10px;
        ">
            {status}
        </div>

        <div style="margin-bottom:10px;">

            <div style="
                position:relative;
                height:8px;
                background:#ddd;
                border-radius:20px;
                overflow:visible;
            ">

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

                <div style="
                    position:absolute;
                    top:-18px;
                    left:{truck_left};
                    font-size:24px;
                    transition:1s;
                    transform:scaleX(-1);
                    animation:{truck_anim};
                ">
                    🚚
                </div>

            </div>

            <div style="
                display:flex;
                justify-content:space-between;
                margin-top:18px;
                font-size:11px;
                font-weight:bold;
                color:#555;
            ">
                <span>Ordered</span>
                <span>Packed</span>
                <span>Shipped</span>
                <span>Out For Delivery</span>
                <span>Delivered</span>
            </div>

        </div>
        """
        # BUTTONS
        if status == "Delivered":

            if not received:

                html += f"""
                <div style="text-align:center;margin-top:18px;">

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

            else:

                html += f"""
                <div style="text-align:center;margin-top:18px;">

                    <form method="post" action="/return_order">

                        <input
                            type="hidden"
                            name="product"
                            value="{items}">

                        <input
                            type="hidden"
                            name="order_time"
                            value="{created}">

                        <button
                            type="submit"
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

            html += f"""
            <div style="
                text-align:center;
                margin-top:12px;
            ">

                <a
                href="/delete_order/{order_id}"
                onclick="return confirm('Delete this order permanently?')"
                style="
                    display:inline-block;
                    background:#dc3545;
                    color:white;
                    text-decoration:none;
                    padding:12px 25px;
                    border-radius:10px;
                    font-size:16px;
                    font-weight:bold;
                ">
                    🗑 Delete Order
                </a>

            </div>
            """

        html += "</div>"

    html += """
    <div style="
        position:sticky;
        bottom:15px;
        text-align:center;
        margin-top:20px;
    ">

        <button
            type="submit"
            onclick="return confirm('Delete selected delivered orders permanently?')"
            style="
                background:#dc3545;
                color:white;
                border:none;
                padding:14px 30px;
                border-radius:12px;
                font-size:18px;
                font-weight:bold;
                cursor:pointer;
            ">
            🗑 Delete Selected Orders
        </button>

    </div>

    </form>

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

    try:
        resp2 = requests.post(
        "https://api.emailjs.com/api/v1.0/email/send",
        headers={
            "Content-Type":"application/json"
        },
        json={
            "service_id":"service_shopboss2",
            "template_id":"template_3jp7vty",
            "user_id":"9bTfVOFVe_u1Mt51L",
            "template_params":{
                "name":session.get("user"),
                "email":"kfayizwani@gmail.com",
                "message":message
            }
        }
        )
        print("EMAIL2 RESPONSE:", resp2.status_code, resp2.text)
    except Exception as e:
        print("EMAIL2 ERROR:", e)

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
    # ------------?--------------
@ShopBoss.route("/update_status/<int:order_id>/<status>")
def update_status(order_id, status):

    if not session.get("admin"):
        return redirect("/admin")

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE orders
        SET status=%s
        WHERE id=%s
        """,
        (status, order_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/all_orders")
# ---------------- FAVICON ----------------
@ShopBoss.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico", mimetype="image/x-icon")

@ShopBoss.route("/favicon-512.png")
def favicon_512():
    return send_from_directory("static", "favicon-512.png", mimetype="image/png")

@ShopBoss.route("/apple-touch-icon.png")
def apple_touch_icon():
    return send_from_directory("static", "apple-touch-icon.png", mimetype="image/png")

@ShopBoss.route("/icon-192.png")
def icon_192():
    return send_from_directory("static", "icon-192.png", mimetype="image/png")

@ShopBoss.route("/site.webmanifest")
def webmanifest():
    return send_from_directory("static", "site.webmanifest", mimetype="application/manifest+json")

# ---------------- GOOGLE VERIFICATION ----------------
@ShopBoss.route("/google0e3bd8ae06ba190d.html")
def google_verify():
    return "google-site-verification: google0e3bd8ae06ba190d.html"

@ShopBoss.route("/google929ecdecc4249da0.html")
def google_verify2():
    return "google-site-verification: google929ecdecc4249da0.html"

# ---------------- ROBOTS.TXT ----------------
@ShopBoss.route("/robots.txt")
def robots():
    from flask import Response
    content = """User-agent: *
Allow: /
Sitemap: https://www--shopbosskmr.replit.app/sitemap.xml
"""
    return Response(content, mimetype="text/plain")

# ---------------- SITEMAP.XML ----------------
@ShopBoss.route("/sitemap.xml")
def sitemap():
    from flask import Response
    base = "https://www--shopbosskmr.replit.app"
    urls = [
        "https://www--shopbosskmr.replit.app/signup",
        "https://www--shopbosskmr.replit.app/login",
        "https://www--shopbosskmr.replit.app/home",
        "https://www--shopbosskmr.replit.app/home?category=Cricket",
        "https://www--shopbosskmr.replit.app/home?category=Football",
        "https://www--shopbosskmr.replit.app/home?category=Fashion",
        "https://www--shopbosskmr.replit.app/home?category=Shoes",
        "https://www--shopbosskmr.replit.app/home?category=Electronics",
        "https://www--shopbosskmr.replit.app/home?category=Kitchen",
        "https://www--shopbosskmr.replit.app/home?category=Garden",
        "https://www--shopbosskmr.replit.app/home?category=Decoration",
        "https://www--shopbosskmr.replit.app/home?category=House Hold",
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
        port=5000
    )
