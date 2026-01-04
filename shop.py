from flask import Flask

app = Flask(__name__)

@app.get('/')
def home():
    return """
    <html>
        <head>
            <title>ShopTrhCE</title>
            <style>
                body { background-color: #1a1a1a; color: white; font-family: sans-serif; text-align: center; padding: 50px; }
                .logo { font-size: 50px; font-weight: bold; color: #ff0055; }
                .product-grid { display: flex; justify-content: center; gap: 20px; margin-top: 30px; }
                .card { border: 1px solid #333; padding: 20px; border-radius: 10px; background: #222; width: 200px; }
                button { background: #ff0055; color: white; border: none; padding: 10px; cursor: pointer; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="logo">ShopTrhCE</div>
            <p>Chuyên cung cấp sản phẩm cao cấp phong cách Vape.gg</p>
            <div class="product-grid">
                <div class="card">
                    <h3>Sản phẩm A</h3>
                    <p>Price: 500.000đ</p>
                    <button>Mua ngay</button>
                </div>
                <div class="card">
                    <h3>Sản phẩm B</h3>
                    <p>Price: 750.000đ</p>
                    <button>Mua ngay</button>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)