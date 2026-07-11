# ⚡ Lightning Laptop — Website

Full project: Frontend (HTML+CSS+JS single file) + Backend (Flask) + Database (SQLite).

## Folder structure
```
lightning_laptop/
├── app.py                     -> Backend (Flask + SQLite APIs)
├── lightning_laptop.db        -> Database (already created, 8 sample laptops)
├── requirements.txt           -> Python packages needed
└── templates/
    └── index.html             -> Frontend (HTML + CSS + JS, ore file)
```

## Setup pannuvathu eppadi (VS Code la)

1. Indha folder full-a copy pannunga (`app.py`, `templates/`, `lightning_laptop.db`, `requirements.txt`) — same structure oda irukanum, illana Flask template ah kandupidikaathu.

2. Terminal open pannunga, indha folder ku po:
   ```
   cd lightning_laptop
   ```

3. Flask install pannunga (already install pannirundha skip pannunga):
   ```
   pip install -r requirements.txt
   ```

4. Run pannunga:
   ```
   python app.py
   ```

5. Browser la open pannunga:
   ```
   http://127.0.0.1:5000
   ```

Adhu than — website ready. Product list, add to cart, checkout, order tracking ella work aagum.

## Enna features irukku
- Home page la 8 Lightning laptops (sample data) — DB already irukku, so first run oda dhaan products varum.
- Add to cart, quantity increase/decrease, cart drawer.
- Checkout — name, phone, address kudutha order DB la save aagum, stock automatic-a reduce aagum.
- Track Order — Order ID kudutha status paakalam.

## Admin API (optional, Postman/curl use pannalam)
- New laptop add pannuna: `POST /api/products`
  ```json
  {
    "name": "Lightning Neo 15",
    "brand": "Lightning",
    "processor": "Intel i5",
    "ram": "16GB",
    "storage": "512GB SSD",
    "price": 65990,
    "stock": 10
  }
  ```
- Ella orders list: `GET /api/orders`
- Order status update: `POST /api/order/<id>/status` body: `{"status": "Shipped"}`

## Database reset pannanuma?
`lightning_laptop.db` file delete pannitu, `python app.py` run pannunga — automatic-a fresh DB with sample laptops create aagum (`init_db()` function app.py la irukku).

## Notes
- Cart data browser memory la dhaan irukku (page refresh pannina reset aagum) — intha demo scope ku adhu போதும்.
- Product images emoji (💻) use pannirukom, real images vena `card-img` CSS class edit pannikonga `index.html` la.
