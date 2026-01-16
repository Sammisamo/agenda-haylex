# agenda.py
import streamlit as st
import sqlite3
import hashlib

# === Funciones de base de datos ===
def get_db_connection():
    conn = sqlite3.connect('haylex_data.db')
    conn.row_factory = sqlite3.Row  # Permite acceder por nombre de columna
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# === Inicialización de la base de datos ===
def init_db():
    conn = get_db_connection()
    # Crear tabla si no existe
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'usuario'
        )
    ''')
    # Asegurar que GERENCIA exista como admin (solo si no existe)
    try:
        conn.execute('''
            INSERT INTO usuarios (usuario, password, rol)
            VALUES (?, ?, ?)
        ''', ('GERENCIA', hash_password('GERENCIA'), 'admin'))
    except sqlite3.IntegrityError:
        # Ya existe, no hacer nada
        pass
    conn.commit()
    conn.close()

# Ejecutar inicialización al cargar
init_db()

# === Interfaz de Streamlit ===
st.set_page_config(page_title="Sistema HAYLEX", layout="wide")

# Sidebar: Login
if 'user' not in st.session_state:
    st.sidebar.title("🔒 Iniciar Sesión")
    username = st.sidebar.text_input("Usuario")
    password = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Iniciar Sesión"):
        if username and password:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM usuarios WHERE usuario = ? AND password = ?",
                (username, hash_password(password))
            ).fetchone()
            conn.close()

            if user:
                st.session_state.user = dict(user)
                st.success(f"✅ Bienvenido, {user['usuario']}")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
        else:
            st.warning("⚠️ Ingresa usuario y contraseña")
    st.stop()

# Si ya hay sesión activa
user = st.session_state.user

# Sidebar: Información y cierre de sesión
st.sidebar.title("👤 Panel de Control")
st.sidebar.write(f"**Usuario:** {user['usuario']}")
st.sidebar.write(f"**Rol:** {user['rol'].capitalize()}")
if st.sidebar.button("🚪 Salir del Sistema"):
    del st.session_state.user
    st.rerun()

# === Contenido principal ===
st.title("📅 Sistema de Gestión HAYLEX")

# Menú de navegación (puedes expandirlo después)
menu = st.sidebar.radio("Menú", ["Inicio", "Control de Usuarios", "Evaluaciones", "Clientes", "Mensajes"])

if menu == "Inicio":
    st.subheader("Bienvenido al sistema")
    st.info("Selecciona una opción en el menú lateral.")

elif menu == "Control de Usuarios":
    if user['rol'] != 'admin':
        st.warning("🔒 Solo los administradores pueden gestionar usuarios.")
        st.stop()

    st.header("👥 Control de Usuarios")

    # Formulario para crear usuario
    with st.expander("➕ Crear Nuevo Usuario"):
        new_user = st.text_input("Nombre de usuario", key="new_user")
        new_pass = st.text_input("Contraseña", type="password", key="new_pass")
        rol = st.selectbox("Rol", ["usuario", "admin"], key="new_rol")

        if st.button("Crear Usuario"):
            if new_user.strip() and new_pass.strip():
                conn = get_db_connection()
                try:
                    conn.execute(
                        "INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)",
                        (new_user.strip(), hash_password(new_pass.strip()), rol)
                    )
                    conn.commit()
                    st.success(f"✅ Usuario '{new_user}' creado con rol '{rol}'")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ El nombre de usuario ya existe")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Completa todos los campos")

    # Listar usuarios
    st.subheader("Usuarios Registrados")
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM usuarios ORDER BY rol DESC, usuario").fetchall()
    conn.close()

    for u in users:
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            badge = "🛡️ **Admin**" if u['rol'] == 'admin' else "👤 Usuario"
            st.write(f"**{u['usuario']}** — {badge}")
        with col2:
            if u['usuario'] != user['usuario']:
                if st.button("🗑️ Eliminar", key=f"del_{u['id']}"):
                    conn = get_db_connection()
                    conn.execute("DELETE FROM usuarios WHERE id = ?", (u['id'],))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Usuario '{u['usuario']}' eliminado")
                    st.rerun()
        with col3:
            if u['usuario'] != user['usuario']:
                new_role = "usuario" if u['rol'] == "admin" else "admin"
                if st.button(f"🔄 Cambiar a {new_role}", key=f"role_{u['id']}"):
                    conn = get_db_connection()
                    conn.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (new_role, u['id']))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Rol de '{u['usuario']}' actualizado a '{new_role}'")
                    st.rerun()

elif menu == "Evaluaciones":
    st.subheader("📊 Evaluaciones de Desempeño")
    st.write("Próximamente...")

elif menu == "Clientes":
    st.subheader("🏢 Gestión de Clientes")
    st.write("Próximamente...")

elif menu == "Mensajes":
    st.subheader("✉️ Mensajería Interna")
    st.write("Próximamente...")

# === Footer ===
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #4A90E2;'>"
    "<strong>Desarrollado por: Miguel Sánchez Morales</strong> | Consultor"
    "</div>",
    unsafe_allow_html=True
)