import sqlite3
import logging
import bcrypt
import os
from dotenv import load_dotenv

# variables env
load_dotenv()
DB_NAME = os.getenv("DB_NAME", "inventory.db")
LOG_FILE = os.getenv("LOG_FILE", "app.log")

# configs de logs
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# db
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                category TEXT NOT NULL
            )
        ''')
        conn.commit()

        # usuario default
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            default_pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", default_pw))
            conn.commit()
            logging.info("Usuario por defecto 'admin' creado.")
    except Exception as e:
        logging.error(f"Error al inicializar la base de datos: {e}")
    finally:
        conn.close()

# registro de new user (solo si hay uno logeado)
def register_user(current_user, username, password):
    if not current_user:
        print("Debe iniciar sesión como administrador para registrar nuevos usuarios.")
        return
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        logging.info(f"Usuario {username} registrado exitosamente por {current_user}.")
        print("Usuario registrado exitosamente.")
    except sqlite3.IntegrityError:
        logging.warning(f"Intento de registrar usuario existente: {username}.")
        print("El nombre de usuario ya existe.")
    except Exception as e:
        logging.error(f"Error registrando usuario {username}: {e}")
        print("Error al registrar usuario.")
    finally:
        conn.close()

# login
def authenticate_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode(), user[0]):
            logging.info(f"Usuario {username} autenticado correctamente.")
            return True
        logging.warning(f"Fallo en autenticación de usuario: {username}.")
        return False
    except Exception as e:
        logging.error(f"Error en autenticación de usuario {username}: {e}")
        return False
    finally:
        conn.close()

# crud para los products
def add_product(name, description, quantity, price, category):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, quantity, price, category) VALUES (?, ?, ?, ?, ?)", 
                    (name, description, quantity, price, category))
        conn.commit()
        logging.info(f"Producto '{name}' agregado al inventario.")
    except Exception as e:
        logging.error(f"Error agregando producto '{name}': {e}")
        print("Error al agregar producto.")
    finally:
        conn.close()

def get_products():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error obteniendo productos: {e}")
        return []
    finally:
        conn.close()

def update_product(product_id, name, description, quantity, price, category):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET name=?, description=?, quantity=?, price=?, category=? WHERE id= ?", 
                    (name, description, quantity, price, category, product_id))
        conn.commit()
        logging.info(f"Producto ID {product_id} actualizado.")
    except Exception as e:
        logging.error(f"Error actualizando producto ID {product_id}: {e}")
        print("Error al actualizar producto.")
    finally:
        conn.close()

def delete_product(product_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        logging.info(f"Producto ID {product_id} eliminado del inventario.")
    except Exception as e:
        logging.error(f"Error eliminando producto ID {product_id}: {e}")
        print("Error al eliminar producto.")
    finally:
        conn.close()

# update para el stock
def update_stock(product_id, quantity_change):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM products WHERE id=?", (product_id,))
        product = cursor.fetchone()
        if product:
            new_quantity = product[0] + quantity_change
            if new_quantity < 0:
                logging.warning(f"Intento de reducir el stock por debajo de 0 para el producto ID {product_id}.")
                print("No se puede reducir el stock por debajo de 0.")
            else:
                cursor.execute("UPDATE products SET quantity=? WHERE id=?", (new_quantity, product_id))
                conn.commit()
                logging.info(f"Stock del producto ID {product_id} actualizado a {new_quantity}.")
        else:
            logging.warning(f"Intento de actualizar stock para producto inexistente ID {product_id}.")
            print("Producto no encontrado.")
    except Exception as e:
        logging.error(f"Error actualizando stock del producto ID {product_id}: {e}")
        print("Error al actualizar stock.")
    finally:
        conn.close()

# busqueda
def search_products(keyword):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name LIKE ? OR category LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error buscando productos con palabra clave '{keyword}': {e}")
        return []
    finally:
        conn.close()

# main menu
def menu(current_user):
    while True:
        print("\n--- Menú de Inventario ---")
        print("1. Ver productos")
        print("2. Agregar producto")
        print("3. Actualizar producto")
        print("4. Eliminar producto")
        print("5. Actualizar stock")
        print("6. Buscar productos")
        print("7. Registrar nuevo usuario")
        print("8. Salir")

        opcion = input("Seleccione una opción: ")

        try:
            if opcion == "1":
                productos = get_products()
                for p in productos:
                    print(p)
            elif opcion == "2":
                nombre = input("Nombre: ")
                descripcion = input("Descripción: ")
                cantidad = int(input("Cantidad: "))
                precio = float(input("Precio: "))
                categoria = input("Categoría: ")
                add_product(nombre, descripcion, cantidad, precio, categoria)
            elif opcion == "3":
                pid = int(input("ID del producto a actualizar: "))
                nombre = input("Nuevo nombre: ")
                descripcion = input("Nueva descripción: ")
                cantidad = int(input("Nueva cantidad: "))
                precio = float(input("Nuevo precio: "))
                categoria = input("Nueva categoría: ")
                update_product(pid, nombre, descripcion, cantidad, precio, categoria)
            elif opcion == "4":
                pid = int(input("ID del producto a eliminar: "))
                delete_product(pid)
            elif opcion == "5":
                pid = int(input("ID del producto: "))
                cambio = int(input("Cambio de cantidad (+/-): "))
                update_stock(pid, cambio)
            elif opcion == "6":
                palabra = input("Ingrese palabra clave: ")
                resultados = search_products(palabra)
                for r in resultados:
                    print(r)
            elif opcion == "7":
                username = input("Nuevo usuario: ")
                password = input("Nueva contraseña: ")
                register_user(current_user, username, password)
            elif opcion == "8":
                print("Saliendo...")
                break
            else:
                print("Opción no válida.")
        except Exception as e:
            logging.error(f"Error en el menú de inventario: {e}")
            print("Ha ocurrido un error. Intente nuevamente.")

if __name__ == "__main__":
    init_db()
    print("Bienvenido al sistema de inventario.")

    current_user = None
    while True:
        print("\n--- Inicio de Sesión ---")
        print("1. Iniciar sesión")
        print("2. Salir")
        choice = input("Seleccione una opción: ")

        if choice == "1":
            username = input("Usuario: ")
            password = input("Contraseña: ")
            if authenticate_user(username, password):
                print("Inicio de sesión exitoso.")
                current_user = username
                menu(current_user)
                current_user = None
            else:
                print("Credenciales incorrectas.")
        elif choice == "2":
            print("Hasta luego.")
            break
        else:
            print("Opción no válida.")
