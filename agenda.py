import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, date
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Haylex Cloud 2026 - Master", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #F2F2F2; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #F2F2F2; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: #FFFFFF; color: #800000; 
        border-radius: 5px 5px 0px 0px; padding: 10px 20px;
        border: 1px solid #D3D3D3;
    }
    .stTabs [aria-selected="true"] { background-color: #800000 !important; color: white !important; }
    div.stButton > button:first-child { background-color: #800000; color: white; border-radius: 5px; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 2px solid #800000; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS ---
def crear_conexion():
    return sqlite3.connect('haylex_data.db', check_same_thread=False)

def inicializar_db():
    conn = crear_conexion()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, pass TEXT, rol TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_cliente TEXT UNIQUE, ejecutivo_asignado TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS tareas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_inicio TEXT, fecha_fin TEXT, 
                  ejecutivo TEXT, cliente TEXT, t1 TEXT, t2 TEXT, t3 TEXT, t4 TEXT, t5 TEXT, t6 TEXT,
                  avance INTEGER, estado TEXT, calificacion INTEGER, notas_admin TEXT)''')
    c.execute("INSERT OR IGNORE INTO usuarios VALUES ('GERENCIA', 'admin123', 'admin')")
    conn.commit()
    conn.close()

inicializar_db()

# --- SIDEBAR ---
with st.sidebar:
    logo_file = st.file_uploader("📥 Importar Logo de Empresa", type=['png', 'jpg', 'jpeg'])
    if logo_file:
        img = Image.open(logo_file)
        c_l1, c_l2 = st.columns([1, 3])
        with c_l1: st.image(img, width=60)
        with c_l2: st.markdown("<h3 style='color: #800000; margin-top: 10px;'>Control Haylex</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color: #800000;'>Control Haylex</h2>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state.auth = {'conectado': False}
        st.rerun()

# --- ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = {'conectado': False, 'user': None, 'rol': None}

if not st.session_state.auth['conectado']:
    st.title("Acceso Haylex Cloud")
    with st.form("login"):
        u = st.text_input("Usuario").upper().strip()
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Acceder", width='stretch'):
            conn = crear_conexion()
            res = pd.read_sql(f"SELECT * FROM usuarios WHERE usuario='{u}' AND pass='{p}'", conn)
            conn.close()
            if not res.empty:
                st.session_state.auth = {'conectado': True, 'user': u, 'rol': res.iloc[0]['rol']}
                st.rerun()
            else: st.error("Credenciales incorrectas")
else:
    u_act = st.session_state.auth['user']
    rol_act = st.session_state.auth['rol']

    if rol_act == 'admin':
        t_usr, t_cli, t_rev, t_dash = st.tabs(["👥 USUARIOS", "🏢 CLIENTES", "✅ REVISIÓN", "📊 PANEL"])

        # USUARIOS
        with t_usr:
            st.subheader("Gestión de Personal")
            c1, c2 = st.columns([1, 2])
            with c1:
                with st.form("a_u", clear_on_submit=True):
                    un = st.text_input("Nombre").upper()
                    pw = st.text_input("Pass")
                    if st.form_submit_button("Registrar Ejecutivo"):
                        conn = crear_conexion()
                        try:
                            conn.execute("INSERT INTO usuarios VALUES (?,?,'user')", (un,pw))
                            conn.commit(); st.rerun()
                        except: st.error("Ya existe")
                        conn.close()
            with c2:
                conn = crear_conexion()
                df_u = pd.read_sql("SELECT usuario FROM usuarios WHERE rol='user'", conn)
                for _, r in df_u.iterrows():
                    ca, cb = st.columns([3, 1])
                    ca.write(f"👤 {r['usuario']}")
                    if cb.button("Borrar", key=f"del_{r['usuario']}"):
                        conn.execute(f"DELETE FROM usuarios WHERE usuario='{r['usuario']}'")
                        conn.commit(); conn.close(); st.rerun()
                conn.close()

        # CLIENTES
        with t_cli:
            st.subheader("Control de Clientes")
            col_izq, col_der = st.columns([1, 1.5])
            with col_izq:
                conn = crear_conexion()
                usrs_list = pd.read_sql("SELECT usuario FROM usuarios WHERE rol='user'", conn)['usuario'].tolist()
                with st.form("a_c", clear_on_submit=True):
                    cn = st.text_input("Empresa").upper()
                    ue = st.selectbox("Ejecutivo", usrs_list)
                    if st.form_submit_button("Asignar"):
                        try:
                            conn.execute("INSERT INTO clientes (nombre_cliente, ejecutivo_asignado) VALUES (?,?)", (cn,ue))
                            conn.commit(); st.rerun()
                        except: st.error("Cliente ya registrado")
                conn.close()
            with col_der:
                st.write("### Catálogo de Clientes y Responsables")
                conn = crear_conexion()
                df_c = pd.read_sql("SELECT * FROM clientes", conn)
                for _, r in df_c.iterrows():
                    ca, cb, cc = st.columns([2, 1, 1])
                    ca.write(f"🏢 {r['nombre_cliente']}")
                    cb.write(f"💼 {r['ejecutivo_asignado']}")
                    if cc.button("Quitar", key=f"cli_{r['id']}"):
                        conn.execute(f"DELETE FROM clientes WHERE id={r['id']}")
                        conn.commit(); conn.close(); st.rerun()
                conn.close()

        # REVISIÓN
        with t_rev:
            st.subheader("Seguimiento y Comentarios")
            conn = crear_conexion()
            pends = pd.read_sql("SELECT * FROM tareas WHERE estado != 'Finalizado'", conn)
            for _, r in pends.iterrows():
                with st.expander(f"📋 {r['ejecutivo']} - {r['cliente']} ({r['avance']}%)"):
                    coment = st.text_area("Notas", value=r['notas_admin'] or "", key=f"com_{r['id']}")
                    calif = st.slider("Calificación", 0, 100, int(r['calificacion']), key=f"cal_{r['id']}")
                    
                    c_b1, c_b2 = st.columns(2)
                    if c_b1.button("💾 Guardar Cambios", key=f"sv_{r['id']}", width='stretch'):
                        conn.execute("UPDATE tareas SET calificacion=?, notas_admin=? WHERE id=?", (calif, coment, r['id']))
                        conn.commit(); st.success("Guardado"); st.rerun()
                    if c_b2.button("✔️ Finalizar Actividad", key=f"fn_{r['id']}", width='stretch'):
                        conn.execute("UPDATE tareas SET estado='Finalizado', calificacion=?, notas_admin=? WHERE id=?", (calif, coment, r['id']))
                        conn.commit(); st.rerun()
            conn.close()

        # PANEL (GRÁFICOS RESTAURADOS)
        with t_dash:
            conn = crear_conexion()
            df_dash = pd.read_sql("SELECT * FROM tareas", conn)
            conn.close()
            if not df_dash.empty:
                st.subheader("Análisis Gerencial")
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    fig_pie = px.pie(df_dash, values='avance', names='ejecutivo', title='Carga de Trabajo (%)', color_discrete_sequence=['#800000', '#D3D3D3'])
                    st.plotly_chart(fig_pie, use_container_width=True, key="pie_carga")
                
                with col_g2:
                    # RESTAURACIÓN: Gráfico de Barras de Calificaciones
                    df_cal = df_dash.groupby('ejecutivo')['calificacion'].mean().reset_index()
                    fig_bar = px.bar(df_cal, x='ejecutivo', y='calificacion', title='Promedio de Calificación por Ejecutivo', 
                                     color_discrete_sequence=['#800000'])
                    fig_bar.update_yaxes(range=[0, 100])
                    st.plotly_chart(fig_bar, use_container_width=True, key="bar_calif")

                if st.button("✨ Generar Reporte Detallado"):
                    st.divider()
                    st.dataframe(df_dash[['ejecutivo', 'cliente', 'avance', 'calificacion', 'estado']])
            else:
                st.info("Aún no hay datos para mostrar gráficos.")

    else:
        # --- VISTA EJECUTIVO ---
        st.header(f"Ejecutivo: {u_act}")
        conn = crear_conexion()
        mis_clis = pd.read_sql(f"SELECT nombre_cliente FROM clientes WHERE ejecutivo_asignado='{u_act}'", conn)['nombre_cliente'].tolist()
        
        if mis_clis:
            c_sel = st.selectbox("Seleccionar Cliente:", mis_clis)
            prev = pd.read_sql(f"SELECT * FROM tareas WHERE ejecutivo='{u_act}' AND cliente='{c_sel}' AND estado!='Finalizado'", conn)
            
            if not prev.empty:
                r = prev.iloc[0]
                t_v = [r['t1'], r['t2'], r['t3'], r['t4'], r['t5'], r['t6']]
                av_v = int(r['avance'])
                f_i_v = datetime.strptime(r['fecha_inicio'], '%Y-%m-%d').date()
                f_f_v = datetime.strptime(r['fecha_fin'], '%Y-%m-%d').date()
                id_tarea = r['id']
            else:
                t_v = [""]*6; av_v = 0; f_i_v = date.today(); f_f_v = date.today(); id_tarea = None

            with st.form(key="f_tareas_ejecutivo"):
                col1, col2 = st.columns(2)
                f_ini = col1.date_input("Fecha Inicio", f_i_v)
                f_fin = col2.date_input("Fecha Fin", f_f_v)
                t1 = col1.text_input("Tarea 1", t_v[0]); t2 = col2.text_input("Tarea 2", t_v[1])
                t3 = col1.text_input("Tarea 3", t_v[2]); t4 = col2.text_input("Tarea 4", t_v[3])
                t5 = col1.text_input("Tarea 5", t_v[4]); t6 = col2.text_input("Tarea 6", t_v[5])
                
                av = st.select_slider("Nivel de Avance %", options=[0, 10, 25, 50, 75, 100], value=av_v)
                
                if st.form_submit_button("Guardar Mi Progreso"):
                    if id_tarea is None:
                        conn.execute('''INSERT INTO tareas (fecha_inicio, fecha_fin, ejecutivo, cliente, t1, t2, t3, t4, t5, t6, avance, estado, calificacion) 
                                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                     (f_ini.isoformat(), f_fin.isoformat(), u_act, c_sel, t1, t2, t3, t4, t5, t6, av, 'En Proceso', 0))
                    else:
                        conn.execute('''UPDATE tareas SET fecha_inicio=?, fecha_fin=?, t1=?, t2=?, t3=?, t4=?, t5=?, t6=?, avance=? WHERE id=?''', 
                                     (f_ini.isoformat(), f_fin.isoformat(), t1, t2, t3, t4, t5, t6, av, id_tarea))
                    conn.commit()
                    st.success("✅ Progreso actualizado correctamente.")
                    st.rerun()
        else:
            st.warning("No tienes clientes asignados actualmente.")
        conn.close()