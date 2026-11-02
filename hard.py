"""
Створити веб-сервіс для обробки зберігання даних про каталог товарів у магазині. Кожен товар має бути описаний як мінімум за 3 параметрами, наприклад ідентифікатор товара, ціна, розмір, вага, колір, і т.д. Елементи каталога товарів рекомендується писати англійською у разі збереження каталогу у файл.
Розробити REST API веб-сервісу з використанням будь-якого фреймворку python (flask, bottle, etc.). Веб-сервіс повинен:
Реалізовувати 2 API endpoints:
/items - за цим ендпоінтом проводяться операції з усіма товарами в каталозі, наприклад можливо вивести те, що зберігається у каталозі
/items/<id> - інформація про конкретний товар за його атрибутом <id> 
Підтримувати HTTP Basic аутентифікацію. Користувацькі дані (тобто username password) повинні зберігатися:
[Hard] у sqlite БД
Веб-сервіс повинен обробляти 4 HTTP методи під час запиту до REST API:
GET для зчитування записів
POST для створення записів
PUT для оновлення запису
DELETE для видалення записів 
Для ендпоінту /items/<id> - підтримка методу POST не потрібна
Веб-сервіс повинен обробляти дані (тобто отримувати запити та формувати відповідь) у форматі json
Організувати зберігання каталогу товарів:
[Hard] у sqlite БД
[easy] Протестувати функціональність веб-сервісу за допомогою Postman
[medium] З використанням бібліотеки requests написати клієнт для веб-сервісу, за допомогою якого можна зчитувати каталог товарів, додавати, оновлювати та видаляти товари з каталогу
"""
import sqlite3
import hashlib
import hmac
import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

DB_NM = "user_cat.db"

# Модель Pydantic для валидации входных данных
class ItemSchema(BaseModel):
    name: str
    price: float
    size: str
    weight: float
    color: str

class ItemResponse(ItemSchema):
    id: int

def get_db_connection():
        conn = sqlite3.connect(DB_NM)
        conn.row_factory = sqlite3.Row
        return conn

def hash_password(password: str, salt: bytes = None) -> str:
    if not salt:
        salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${pwd_hash.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_password.split("$")
        salt = bytes.fromhex(salt_hex)
        recalculated = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000).hex()
        return hmac.compare_digest(hash_hex, recalculated)
    except Exception:
        return False

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 1. Таблица юзеров для HTTP Basic Auth
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        
        # 2. Таблица товаров (id, name, price, size, weight, color)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                size TEXT NOT NULL,
                weight REAL NOT NULL,
                color TEXT NOT NULL
            )
        """)
        # Добавляем тестового админа (логин: admin, пароль: secret123), если база пустая
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if not cursor.fetchone():
            default_hash = hash_password("secret123")
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("admin", default_hash)
            )
        conn.commit()
        
init_db()
app = FastAPI(title="CRUD Store Catalog")
security = HTTPBasic()

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (credentials.username,))
    row = cursor.fetchone()
    conn.close()

    stored_hash = row["password_hash"] if row else None
    if not stored_hash or not verify_password(stored_hash, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
def root():
    return {'status': 'ok', 'message': 'service running...'}

# --- Операции со всеми товарами ---

@app.get("/items", response_model=List[ItemResponse])
def get_items(current_user: str = Depends(auth_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, size, weight, color FROM items")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemSchema, current_user: str = Depends(auth_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, price, size, weight, color) VALUES (?, ?, ?, ?, ?)",
        (item.name, item.price, item.size, item.weight, item.color)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {**item.dict(), "id": new_id}

# --- Операции с конкретным товаром ---

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, current_user: str = Depends(auth_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemSchema, current_user: str = Depends(auth_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    cursor.execute(
        "UPDATE items SET name=?, price=?, size=?, weight=?, color=? WHERE id=?",
        (item.name, item.price, item.size, item.weight, item.color, item_id)
    )
    conn.commit()
    conn.close()
    return {**item.dict(), "id": item_id}

@app.delete("/items/{item_id}")
def delete_item(item_id: int, current_user: str = Depends(auth_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")

    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": f"Item {item_id} deleted successfully"}

