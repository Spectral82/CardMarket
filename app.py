
import sqlite3

from flask import Flask, Response, render_template, request

app = Flask(__name__)
DB_PATH = "shop.sqlite"


def get_db_connection() -> sqlite3.Connection:
    """Создаёт подключение к БД с включёнными именованными колонками."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Инициализирует БД: создаёт таблицы products и orders, заполняет их при пустоте."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT NOT NULL
            )
            """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """)

        cursor.execute("SELECT count(*) FROM products")
        if cursor.fetchone() == 0:
            products = [
                (
                    "Тариф Базовый",
                    100,
                    "10 пользователей, 2 ГБ хранилища, "
                    "Email-поддержка, доступ к центру помощи",
                ),
                (
                    "Тариф Про",
                    250,
                    "25 пользователей, 10 ГБ хранилища, "
                    "приоритетная поддержка, API доступ",
                ),
                (
                    "Тариф Бизнес",
                    500,
                    "50 пользователей, 50 ГБ хранилища, "
                    "выделенный менеджер, SLA 24/7",
                ),
                (
                    "Тариф Премиум",
                    990,
                    "Безлимитные пользователи, 200 ГБ хранилища, "
                    "персональный аккаунт-менеджер, аудит безопасности",
                ),
                (
                    "Тариф Старт",
                    50,
                    "5 пользователей, 1 ГБ хранилища, " "база знаний, форум поддержки",
                ),
                (
                    "Тариф Корпоратив",
                    1500,
                    "До 200 пользователей, 1 ТБ хранилища, "
                    "интеграция с AD/LDAP, выделенная инфраструктура",
                ),
            ]
            cursor.executemany(
                "INSERT INTO products (name, price, description) " "VALUES (?, ?, ?)",
                products,
            )

        cursor.execute("SELECT count(*) FROM orders")
        if cursor.fetchone() == 0:
            orders = [
                (
                    1,
                    "Тариф Базовый",
                    100,
                    2,
                    "Иван Петров",
                    "Выполнен",
                    "2026-10-01 14:30",
                ),
                (
                    3,
                    "Тариф Бизнес",
                    500,
                    1,
                    "Анна Смирнова",
                    "В обработке",
                    "2026-10-03 09:15",
                ),
                (
                    2,
                    "Тариф Про",
                    250,
                    3,
                    "Сергей Волков",
                    "Ожидает оплаты",
                    "2026-10-05 18:00",
                ),
            ]
            cursor.executemany(
                "INSERT INTO orders (product_id, product_name, price, "
                "quantity, customer_name, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                orders,
            )

        conn.commit()


@app.route("/")
def index() -> str:
    """Отображает главную страницу сайта."""
    with get_db_connection() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("index.html", products=products)


@app.route("/catalog")
def catalog() -> str:
    """Отображает страницу каталога с перечнем всех товаров из БД."""
    with get_db_connection() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("catalog.html", products=products)


@app.route("/category")
def category() -> str:
    """Отображает страницу категории товаров из БД."""
    with get_db_connection() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("category.html", products=products)


@app.route("/orders")
def orders() -> str:
    """Отображает страницу с историей заказов из БД."""
    with get_db_connection() as conn:
        order_rows = conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC"
        ).fetchall()
    return render_template("orders.html", orders=order_rows)


@app.route("/contacts", methods=["GET", "POST"])
def contacts() -> Response:
    """Обрабатывает GET-запрос (показ формы) и POST-запрос (приём данных формы)."""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        print("--- Новое сообщение ---")
        print(f"Имя: {name}")
        print(f"Почта: {email}")
        print(f"Сообщение: {message}")
        print("-----------------------")

    try:
        with open("templates/contacts.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return Response(html_content, mimetype="text/html; charset=utf-8")
    except FileNotFoundError:
        return Response(
            "<h1>Ошибка</h1><p>Файл contacts.html не найден.</p>",
            status=500,
            mimetype="text/html; charset=utf-8",
        )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path: str) -> Response:
    """Перехватывает все необработанные GET-запросы и отдаёт страницу контактов."""
    if "." in path.split("/")[-1]:
        return app.send_static_file(path)

    try:
        with open("templates/contacts.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return Response(html_content, mimetype="text/html; charset=utf-8")
    except FileNotFoundError:
        return Response(
            "<h1>500 - Ошибка сервера</h1>",
            status=500,
            mimetype="text/html; charset=utf-8",
        )


@app.errorhandler(404)
def page_not_found(e: Exception) -> tuple[str, int, dict[str, str]]:
    """Обрабатывает ошибку 404 — страница не найдена."""
    return (
        "<h1>404 - Страница не найдена</h1><p>Проверьте адрес страницы.</p>",
        404,
        {"Content-Type": "text/html; charset=utf-8"},
    )


@app.errorhandler(500)
def internal_server_error(e: Exception) -> tuple[str, int, dict[str, str]]:
    """Обрабатывает ошибку 500 — внутренняя ошибка сервера."""
    return (
        "<h1>500 - Ошибка сервера</h1>"
        "<p>Произошла внутренняя ошибка приложения.</p>",
        500,
        {"Content-Type": "text/html; charset=utf-8"},
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
