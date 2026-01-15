import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from supabase import create_client, Client

# --- IMPORTACIÓN PARA PDF ---
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# --- CONFIGURACION ---
st.set_page_config(page_title="HAYLEX CLOUD PRO", layout="wide")

LOGO_PATH = "logo_pers.png"
DEVELOPER_LOGO = "MM.png"  # Asegúrate de tener este archivo en tu repo

# --- SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "TU_URL_DE_SUPABASE")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "TU_CLAVE_ANON_DE_SUPABASE")

if "TU_URL" in SUPABASE_URL or "TU_CLAVE" in SUPABASE_KEY:
    st.error("❌ Debes configurar las variables de entorno SUPABASE_URL y SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def inicializar_db():
    """Asegura que el usuario GERENCIA exista en Supabase."""
    try:
        res = supabase.table("usuarios").select("*").eq("usuario", "GERENCIA").execute()
        if not res.data:
            supabase.table("usuarios").insert({
                "usuario": "GERENCIA",
                "pass": "admin123",
                "rol": "admin"
            }).execute()
    except Exception as e:
        st.error(f"Error al inicializar Supabase: {e}")

inicializar_db()

def mostrar_cabecera(titulo):
    col_img, col_txt = st.columns([1, 7])
    if os.path.exists(LOGO_PATH):
        col_img.image(LOGO_PATH, width=100)
    col_txt.title(titulo)
    st.divider()

def reiniciar_sistema():
    """Borra todos los datos excepto GERENCIA (solo en desarrollo local)."""
    try:
        supabase.table("tareas").delete().execute()
        supabase.table("clientes").delete().execute()
        supabase.table("mensajes").delete().execute()
        supabase.table("usuarios").delete().neq("usuario", "GERENCIA").execute()
        st.success("✅ Sistema reiniciado exitosamente.")
    except Exception as e:
        st.error(f"Error al reiniciar: {e}")

def generar_pdf_ayuda(rol):
    if not PDF_AVAILABLE:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    try:
        pdf.set_font("Arial", size=12)
    except:
        pdf.set_font("Helvetica", size=12)

    pdf.set_font_size(16)
    if rol == 'admin':
        pdf.cell(0, 10, 'Guía del Administrador - HAYLEX CLOUD PRO', ln=True, align='C')
    else:
        pdf.cell(0, 10, 'Guía del Ejecutivo - HAYLEX CLOUD PRO', ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font_size(12)

    if rol == 'admin':
        contenido = """
PANEL DE ADMINISTRACIÓN

1. Evaluación de Tareas
   - Revise las tareas enviadas por los ejecutivos.
   - Asigne una calificación (%) y deje comentarios.
   - Al guardar, la tarea se marca como Finalizado.

2. Gestión de Clientes
   - Registre nuevos clientes y asígneles un ejecutivo.
   - Edite o elimine clientes existentes.

3. Gestión de Usuarios
   - Cree nuevas cuentas para ejecutivos.
   - Actualice contraseñas o elimine usuarios.

4. Métricas de Desempeño
   - Visualice el avance individual y por cliente/proyecto.
   - Use filtros para analizar periodos específicos.

5. Reiniciar Sistema
   - Borre todos los datos (excepto su cuenta) si es necesario.
        """
    else:
        contenido = """
PORTAL DEL EJECUTIVO

1. Trabajo Actual
   - Seleccione un cliente asignado.
   - Escriba hasta 6 tareas (puede agregar más).
   - Adjunte evidencia como imagen (formatos: PNG, JPG).

2. Guardar vs Enviar
   - 💾 Guardar progreso: Guarda sus cambios sin enviarlos a revisión.
   - 📤 Enviar a revisión: Envía sus tareas al administrador para evaluación.

3. Editar Tareas Enviadas
   - Puede seguir editando tareas que ya envió, mientras no estén Finalizadas.
   - Las tareas Finalizadas solo se ven en el historial.

4. Historial
   - Revise sus tareas evaluadas, calificaciones y comentarios del admin.
        """

    for line in contenido.strip().split('\n'):
        pdf.multi_cell(0, 8, line.strip())
    
    return pdf.output(dest='S')

# Funciones para mensajería
def enviar_mensaje(remitente, destinatario, mensaje):
    supabase.table("mensajes").insert({
        "remitente": remitente,
        "destinatario": destinatario,
        "mensaje": mensaje,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }).execute()

def obtener_mensajes(usuario):
    res = supabase.table("mensajes").select("*").or_(f"destinatario.eq.{usuario},remitente.eq.{usuario}").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def marcar_como_leido(mensaje_id):
    supabase.table("mensajes").update({"leido": 1}).eq("id", mensaje_id).execute()

# --- BARRA LATERAL ---
if 'auth' not in st.session_state:
    st.session_state.auth = {'conectado': False, 'user': None, 'rol': None}

with st.sidebar:
    st.header("CONFIGURACION")
    # Solo permitir subida de logo en desarrollo local (no en Streamlit Cloud)
    if "STREAMLIT_RUNTIME" not in os.environ:
        with st.expander("Imagen de Empresa"):
            logo_file = st.file_uploader("Subir imagen institucional", type=["png", "jpg", "jpeg"])
            if logo_file:
                with open(LOGO_PATH, "wb") as f:
                    f.write(logo_file.getbuffer())
                st.rerun()
    
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    
    st.divider()
    if st.session_state.auth['conectado']:
        st.write(f"Usuario: {st.session_state.auth['user']}")
        if st.button("SALIR DEL SISTEMA", use_container_width=True):
            st.session_state.auth = {'conectado': False}
            st.rerun()
        
        if st.session_state.auth['rol'] == 'admin':
            st.divider()
            with st.expander("🛠️ Herramientas de Admin"):
                if st.button("🗑️ Reiniciar Sistema", use_container_width=True):
                    st.session_state.show_confirmation = True
                
                if st.session_state.get('show_confirmation', False):
                    st.warning("⚠️ ¿Estás seguro? Esta acción eliminará todos los clientes, usuarios (excepto GERENCIA) y tareas. ¡No se puede deshacer!")
                    col_conf1, col_conf2 = st.columns(2)
                    with col_conf1:
                        if st.button("✅ Sí, Reiniciar", use_container_width=True):
                            reiniciar_sistema()
                            st.session_state.show_confirmation = False
                            st.rerun()
                    with col_conf2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state.show_confirmation = False
                            st.rerun()
        
        st.divider()
        with st.expander("ℹ️ Ayuda y Guía de Uso"):
            seccion_ayuda = st.selectbox(
                "Seleccione una sección:",
                ["Inicio", "Guía Rápida", "Preguntas Frecuentes", "Soporte Técnico"]
            )
            
            if seccion_ayuda == "Inicio":
                st.markdown("### 📚 Bienvenido a HAYLEX CLOUD PRO")
                st.markdown("""
                Este sistema permite el seguimiento y evaluación del desempeño de los colaboradores.
                
                - **Ejecutivos**: Capturan tareas, adjuntan evidencia y envían a revisión.
                - **Administrador**: Evalúa tareas, gestiona usuarios y visualiza métricas.
                """)
            
            elif seccion_ayuda == "Guía Rápida":
                if st.session_state.auth['rol'] == 'admin':
                    st.markdown("### 👨‍💼 Guía Rápida para Administradores")
                    st.markdown("""
                    **1. Evaluación de Tareas**  
                    - Revise las tareas en la pestaña **"EVALUACION"**.  
                    - Asigne calificación (%) y comentarios.  
                    - Haga clic en **"GUARDAR EVALUACION"** para finalizar.

                    **2. Gestión de Usuarios**  
                    - Cree nuevos ejecutivos en la pestaña **"USUARIOS"**.  
                    - Actualice contraseñas o elimine usuarios.

                    **3. Gestión de Clientes**  
                    - Registre clientes y asígnelos a ejecutivos.  
                    - Edite o elimine clientes existentes.

                    **4. Métricas**  
                    - Visualice el rendimiento individual y por cliente/proyecto.  
                    - Use filtros para analizar periodos específicos.
                    """)
                else:
                    st.markdown("### 👤 Guía Rápida para Ejecutivos")
                    st.markdown("""
                    **1. Trabajo Actual**  
                    - Seleccione un cliente asignado.  
                    - Complete sus tareas en los campos proporcionados.  
                    - Adjunte evidencia como imagen (PNG, JPG).

                    **2. Guardar vs Enviar**  
                    - **💾 Guardar progreso**: Guarda sus cambios sin enviarlos.  
                    - **📤 Enviar a revisión**: Envía sus tareas al administrador.

                    **3. Editar Tareas**  
                    - Puede editar tareas ya enviadas mientras no estén *Finalizadas*.  
                    - Las tareas *Finalizadas* solo se ven en el historial.

                    **4. Historial**  
                    - Revise sus calificaciones y comentarios del administrador.
                    """)
                
                if PDF_AVAILABLE:
                    if st.button("📥 Descargar Guía Completa en PDF", use_container_width=True):
                        pdf_data = generar_pdf_ayuda(st.session_state.auth['rol'])
                        filename = "Guia_Admin_HAYLEX_CLOUD_PRO.pdf" if st.session_state.auth['rol'] == 'admin' else "Guia_Ejecutivo_HAYLEX_CLOUD_PRO.pdf"
                        st.download_button(
                            label="📄 Descargar PDF",
                            data=pdf_data,
                            file_name=filename,
                            mime="application/pdf"
                        )
            
            elif seccion_ayuda == "Preguntas Frecuentes":
                st.markdown("### ❓ Preguntas Frecuentes")
                if st.session_state.auth['rol'] == 'admin':
                    faq_admin = [
                        ("¿Cómo veo las tareas de los ejecutivos?", "Las tareas aparecen en la pestaña **'EVALUACION'** solo cuando los ejecutivos hacen clic en **'Enviar a revisión'**."),
                        ("¿Por qué no veo métricas?", "Las métricas solo se generan a partir de tareas **'Finalizadas'**."),
                        ("¿Cómo reinicio el sistema?", "Use el botón **'🗑️ Reiniciar Sistema'** en **'Herramientas de Admin'**.")
                    ]
                    for pregunta, respuesta in faq_admin:
                        with st.expander(f"❓ {pregunta}"):
                            st.write(respuesta)
                else:
                    faq_user = [
                        ("¿Por qué no veo mis tareas en Gerencia?", "Las tareas solo aparecen en Gerencia cuando haces clic en **'Enviar a revisión'**."),
                        ("¿Puedo editar tareas ya enviadas?", "Sí, puedes editar tareas que ya enviaste mientras el administrador no las haya **'Finalizado'**."),
                        ("¿Dónde veo mis calificaciones?", "Tus calificaciones y comentarios del administrador están en la pestaña **'HISTORIAL'**.")
                    ]
                    for pregunta, respuesta in faq_user:
                        with st.expander(f"❓ {pregunta}"):
                            st.write(respuesta)
            
            elif seccion_ayuda == "Soporte Técnico":
                st.markdown("### 🛠️ Soporte Técnico")
                st.markdown("""
                **Contacto:**  
                - Email: soporte@haylex.com
                
                **Errores comunes:**  
                - Si los campos no se limpian al cambiar de cliente, recargue la página (F5).
                """)

# --- LOGIN ---
if not st.session_state.auth['conectado']:
    mostrar_cabecera("HAYLEX CLOUD - ACCESO")
    with st.form("login_form"):
        u = st.text_input("USUARIO").upper().strip()
        p = st.text_input("CLAVE", type="password")
        if st.form_submit_button("INGRESAR", use_container_width=True):
            res = supabase.table("usuarios").select("*").eq("usuario", u).eq("pass", p).execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                st.session_state.auth = {'conectado': True, 'user': u, 'rol': df.iloc[0]['rol']}
                st.rerun()
            else:
                st.error("Acceso incorrecto")
else:
    rol = st.session_state.auth['rol']
    user = st.session_state.auth['user']

    if rol == 'admin':
        mostrar_cabecera("PANEL DE ADMINISTRACION")
        t1, t2, t3, t4, t5 = st.tabs(["EVALUACION", "CLIENTES", "USUARIOS", "METRICAS", "MENSAJES"])

        with t1:
            res = supabase.table("tareas").select("*").eq("estado", "Revision").execute()
            pends = pd.DataFrame(res.data)
            if pends.empty:
                st.info("No hay tareas para calificar.")
            else:
                for _, r in pends.iterrows():
                    with st.expander(f"REVISAR: {r['ejecutivo']} - {r['cliente']}"):
                        fecha = r.get('fecha', 'Fecha no disponible')
                        st.write(f"Fecha: {fecha}")
                        tasks = r['tareas_json'].split('||') if r['tareas_json'] else []
                        for i, t in enumerate(tasks, 1):
                            st.write(f"Tarea {i}: {t}")
                        if r['evidencia_link']:
                            if r['evidencia_link'].startswith("http"):
                                st.link_button("VER EVIDENCIA ADJUNTA", r['evidencia_link'])
                            else:
                                st.warning("Evidencia local no disponible en la nube.")
                        
                        fb = st.text_area("Comentarios para el user", value=r.get('notas_admin', ''), key=f"fb_{r['id']}")
                        pts = st.slider("Avance %", 0, 100, int(r.get('calificacion', 0)), key=f"pts_{r['id']}")
                        if st.button("GUARDAR EVALUACION", key=f"btn_{r['id']}", type="primary"):
                            supabase.table("tareas").update({
                                "notas_admin": fb,
                                "calificacion": pts,
                                "estado": "Finalizado"
                            }).eq("id", r["id"]).execute()
                            st.rerun()

        with t2:
            st.subheader("Control de Clientes")
            res_u = supabase.table("usuarios").select("usuario").eq("rol", "user").execute()
            u_list = [u["usuario"] for u in res_u.data] if res_u.data else []
            with st.form("new_cli"):
                n_c = st.text_input("Nombre de Cliente").upper()
                if u_list:
                    n_e = st.selectbox("Asignar Ejecutivo", u_list)
                else:
                    st.warning("⚠️ No hay usuarios disponibles.")
                    n_e = None
                if st.form_submit_button("REGISTRAR"):
                    if n_c and n_e:
                        try:
                            supabase.table("clientes").insert({
                                "nombre_cliente": n_c,
                                "ejecutivo_asignado": n_e
                            }).execute()
                            st.rerun()
                        except Exception as e:
                            st.error("El cliente ya existe o error en inserción.")

            res_clis = supabase.table("clientes").select("*").execute()
            clis = pd.DataFrame(res_clis.data)
            for _, c in clis.iterrows():
                with st.expander(f"CLIENTE: {c['nombre_cliente']}"):
                    edit_n = st.text_input("Nombre", c['nombre_cliente'], key=f"cn_{c['id']}")
                    edit_e = st.selectbox("Ejecutivo", u_list, index=u_list.index(c['ejecutivo_asignado']) if c['ejecutivo_asignado'] in u_list else 0, key=f"ce_{c['id']}")
                    c1, c2 = st.columns(2)
                    if c1.button("GUARDAR", key=f"sv_{c['id']}"):
                        supabase.table("clientes").update({
                            "nombre_cliente": edit_n,
                            "ejecutivo_asignado": edit_e
                        }).eq("id", c["id"]).execute()
                        st.rerun()
                    if c2.button("ELIMINAR", key=f"dl_{c['id']}"):
                        supabase.table("clientes").delete().eq("id", c["id"]).execute()
                        st.rerun()

        with t3:
            st.subheader("Control de Usuarios")
            with st.form("new_u"):
                nu = st.text_input("Usuario").upper()
                np = st.text_input("Password")
                if st.form_submit_button("CREAR"):
                    if nu and np:
                        try:
                            supabase.table("usuarios").insert({
                                "usuario": nu,
                                "pass": np,
                                "rol": "user"
                            }).execute()
                            st.rerun()
                        except Exception as e:
                            st.error("El usuario ya existe.")
            res_us = supabase.table("usuarios").select("*").eq("rol", "user").execute()
            us_data = pd.DataFrame(res_us.data)
            for _, u in us_data.iterrows():
                with st.expander(f"USER: {u['usuario']}"):
                    up_p = st.text_input("Password", u['pass'], key=f"up_{u['usuario']}")
                    if st.button("ACTUALIZAR CLAVE", key=f"btnu_{u['usuario']}"):
                        supabase.table("usuarios").update({"pass": up_p}).eq("usuario", u["usuario"]).execute()
                        st.success("Actualizado")
                    if st.button("BORRAR USUARIO", key=f"delu_{u['usuario']}"):
                        supabase.table("usuarios").delete().eq("usuario", u["usuario"]).execute()
                        st.rerun()

        with t4:
            st.subheader("📊 Sistema de Evaluación de Avance")
            res_tareas = supabase.table("tareas").select("*").eq("estado", "Finalizado").execute()
            df_tareas = pd.DataFrame(res_tareas.data)
            
            if df_tareas.empty:
                st.info("No hay datos de evaluación suficientes.")
            else:
                df_tareas['fecha_dt'] = pd.to_datetime(df_tareas['fecha'], format='%d/%m/%Y', errors='coerce')
                df_avance = df_tareas.groupby(['ejecutivo', 'cliente']).agg(
                    promedio_usuario=('calificacion', 'mean'),
                    tareas_evaluadas=('calificacion', 'count'),
                    ultima_evaluacion=('fecha', 'max')
                ).reset_index()

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    clientes_unicos = ["TODOS"] + list(df_avance['cliente'].unique())
                    filtro_cliente = st.selectbox("🔍 Filtrar por Cliente", clientes_unicos)
                with col_f2:
                    fecha_inicio = st.date_input("📅 Desde", value=pd.to_datetime("2024-01-01").date())
                    fecha_fin = st.date_input("📅 Hasta", value=datetime.today().date())
                
                df_filtrado = df_avance if filtro_cliente == "TODOS" else df_avance[df_avance['cliente'] == filtro_cliente]
                df_tareas_filtrado = df_tareas[
                    (df_tareas['fecha_dt'] >= pd.Timestamp(fecha_inicio)) & 
                    (df_tareas['fecha_dt'] <= pd.Timestamp(fecha_fin))
                ]
                if not df_tareas_filtrado.empty:
                    usuarios_filtrados = df_tareas_filtrado['ejecutivo'].unique()
                    df_filtrado = df_filtrado[df_filtrado['ejecutivo'].isin(usuarios_filtrados)]
                
                if df_filtrado.empty:
                    st.warning("No hay datos para los filtros seleccionados.")
                else:
                    st.markdown("### 👤 Avance Individual por Usuario")
                    df_usuario = df_filtrado.groupby('ejecutivo').agg({
                        'promedio_usuario': 'mean',
                        'tareas_evaluadas': 'sum'
                    }).round(2).reset_index()
                    df_usuario = df_usuario.rename(columns={'promedio_usuario': 'Promedio (%)', 'tareas_evaluadas': 'Tareas'})
                    df_usuario = df_usuario.sort_values('Promedio (%)', ascending=False)
                    st.dataframe(df_usuario.style.format({"Promedio (%)": "{:.2f}"}), use_container_width=True)
                    
                    fig_user = px.bar(df_usuario, x='Promedio (%)', y='ejecutivo', orientation='h', title='Rendimiento Individual', color='Promedio (%)', color_continuous_scale='Blues', text='Promedio (%)')
                    fig_user.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_user.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_user, use_container_width=True)
                    
                    st.markdown("### 📂 Avance por Cliente / Proyecto")
                    df_equipo = df_filtrado.groupby('cliente').agg({
                        'promedio_usuario': 'mean',
                        'ejecutivo': 'count'
                    }).round(2).reset_index()
                    df_equipo = df_equipo.rename(columns={'promedio_usuario': 'Promedio Equipo (%)', 'ejecutivo': 'Miembros'})
                    st.dataframe(df_equipo.style.format({"Promedio Equipo (%)": "{:.2f}"}), use_container_width=True)
                    
                    fig_team = px.pie(df_equipo, values='Promedio Equipo (%)', names='cliente', title='Rendimiento por Cliente / Proyecto', hole=0.4)
                    st.plotly_chart(fig_team, use_container_width=True)
                    
                    st.markdown("### 📈 Resumen General del Sistema")
                    promedio_general = df_filtrado['promedio_usuario'].mean()
                    total_usuarios = df_filtrado['ejecutivo'].nunique()
                    total_clientes = df_filtrado['cliente'].nunique()
                    col_r1, col_r2, col_r3 = st.columns(3)
                    col_r1.metric("🎯 Promedio General", f"{promedio_general:.1f}%")
                    col_r2.metric("👥 Usuarios Activos", total_usuarios)
                    col_r3.metric("🏢 Clientes Atendidos", total_clientes)
                    
                    if len(df_tareas_filtrado) > 1:
                        df_tareas_filtrado['semana'] = df_tareas_filtrado['fecha_dt'].dt.to_period('W').dt.start_time
                        tendencia = df_tareas_filtrado.groupby('semana')['calificacion'].mean().reset_index()
                        if len(tendencia) > 1:
                            fig_trend = px.line(tendencia, x='semana', y='calificacion', title='Tendencia de Calificaciones en el Tiempo', markers=True)
                            fig_trend.update_yaxes(range=[0, 100])
                            st.plotly_chart(fig_trend, use_container_width=True)

        with t5:
            st.subheader("✉️ Mensajes")
            res_us = supabase.table("usuarios").select("usuario").eq("rol", "user").execute()
            usuarios = [u["usuario"] for u in res_us.data] if res_us.data else []
            
            if usuarios:
                destinatario = st.selectbox("Enviar mensaje a:", usuarios)
                mensaje = st.text_area("Mensaje:")
                if st.button("Enviar Mensaje", type="primary"):
                    if mensaje.strip():
                        enviar_mensaje(user, destinatario, mensaje.strip())
                        st.success("Mensaje enviado!")
                        st.rerun()
                    else:
                        st.warning("El mensaje no puede estar vacío.")
            
            st.divider()
            st.subheader("Bandeja de Entrada")
            mensajes = obtener_mensajes(user)
            if mensajes.empty:
                st.info("No tienes mensajes.")
            else:
                for _, msg in mensajes.iterrows():
                    if msg['remitente'] == user:
                        st.info(f"**Tú** a {msg['destinatario']} ({msg['fecha']}): {msg['mensaje']}")
                    else:
                        st.success(f"**{msg['remitente']}** ({msg['fecha']}): {msg['mensaje']}")
                        if msg['leido'] == 0:
                            marcar_como_leido(msg['id'])

    else:
        mostrar_cabecera(f"TAREAS DE: {user}")
        t_work, t_history, t_messages = st.tabs(["TRABAJO ACTUAL", "HISTORIAL", "MENSAJES"])

        with t_work:
            res_clis = supabase.table("clientes").select("nombre_cliente").eq("ejecutivo_asignado", user).execute()
            clis_u = [c["nombre_cliente"] for c in res_clis.data] if res_clis.data else []
            if not clis_u:
                st.warning("No tiene clientes asignados.")
            else:
                cliente_anterior = st.session_state.get('cliente_seleccionado', None)
                cl_sel = st.selectbox("Seleccione Cliente", clis_u, key="select_cliente")
                
                if cliente_anterior is not None and cliente_anterior != cl_sel:
                    keys_to_clear = [k for k in st.session_state.keys() if k.startswith('tx_')]
                    for k in keys_to_clear:
                        del st.session_state[k]
                    st.session_state.total_t = 6
                    st.session_state['cliente_seleccionado'] = cl_sel
                    st.rerun()
                
                st.session_state['cliente_seleccionado'] = cl_sel

                res_tarea = supabase.table("tareas").select("*").eq("ejecutivo", user).eq("cliente", cl_sel).neq("estado", "Finalizado").order("id", desc=True).limit(1).execute()
                df_tarea = pd.DataFrame(res_tarea.data)
                tarea_activa = df_tarea.iloc[0] if not df_tarea.empty else None

                if 'total_t' not in st.session_state:
                    st.session_state.total_t = 6

                tareas_existentes = []
                evidencia_existente = ""
                estado_actual = "En progreso"
                if tarea_activa is not None:
                    tareas_existentes = tarea_activa['tareas_json'].split('||') if tarea_activa['tareas_json'] else []
                    evidencia_existente = tarea_activa['evidencia_link']
                    estado_actual = tarea_activa['estado']
                    st.session_state.total_t = max(6, len(tareas_existentes))

                inputs = []
                for i in range(st.session_state.total_t):
                    valor_previo = tareas_existentes[i] if i < len(tareas_existentes) else ""
                    inp = st.text_input(f"Tarea {i+1}", value=valor_previo, key=f"tx_{i}")
                    inputs.append(inp)

                st.subheader("Adjuntar Evidencia")
                st.info("En la versión en la nube, solo se admiten enlaces URL (ej. Google Drive, Dropbox).")
                link_ev = st.text_input("URL de evidencia (opcional)", value=evidencia_existente)

                c1, c2 = st.columns(2)
                guardar = c1.button("💾 Guardar progreso", use_container_width=True)
                enviar = c2.button("📤 Enviar a revisión", use_container_width=True)

                if guardar or enviar:
                    tasks_str = "||".join([t.strip() for t in inputs if t.strip()])
                    if not tasks_str:
                        st.warning("Debe ingresar al menos una tarea.")
                    else:
                        fecha_actual = datetime.now().strftime("%d/%m/%Y")
                        nuevo_estado = "Revision" if enviar else "En progreso"

                        if tarea_activa is not None:
                            supabase.table("tareas").update({
                                "tareas_json": tasks_str,
                                "evidencia_link": link_ev,
                                "estado": nuevo_estado,
                                "fecha": fecha_actual
                            }).eq("id", tarea_activa["id"]).execute()
                        else:
                            supabase.table("tareas").insert({
                                "fecha": fecha_actual,
                                "ejecutivo": user,
                                "cliente": cl_sel,
                                "tareas_json": tasks_str,
                                "evidencia_link": link_ev,
                                "estado": nuevo_estado,
                                "calificacion": 0
                            }).execute()
                        
                        accion = "enviada a revisión" if enviar else "guardada"
                        st.success(f"✅ Tarea {accion} correctamente!")
                        st.rerun()

                if st.button("➕ Agregar nueva tarea"):
                    st.session_state.total_t += 1
                    st.rerun()

        with t_history:
            st.subheader("Evolución de Avance")
            res_u = supabase.table("tareas").select("*").eq("ejecutivo", user).order("id", desc=True).execute()
            df_u = pd.DataFrame(res_u.data)
            if df_u.empty:
                st.info("Aún no tiene registros.")
            else:
                for _, r in df_u.iterrows():
                    with st.container(border=True):
                        st.write(f"CLIENTE: {r['cliente']} | ESTADO: {r['estado']}")
                        if r['estado'] == 'Finalizado':
                            calif = r.get('calificacion', 0)
                            st.success(f"CALIFICACIÓN: {calif}%")
                            st.info(f"COMENTARIO ADMIN: {r.get('notas_admin', '')}")
                            st.progress(calif / 100)
                        if r['evidencia_link']:
                            st.link_button("Ver evidencia", r['evidencia_link'])

        with t_messages:
            st.subheader("✉️ Mensajes")
            destinatario = "GERENCIA"
            mensaje = st.text_area("Mensaje para Gerencia:")
            if st.button("Enviar Mensaje", type="primary"):
                if mensaje.strip():
                    enviar_mensaje(user, destinatario, mensaje.strip())
                    st.success("Mensaje enviado a Gerencia!")
                    st.rerun()
                else:
                    st.warning("El mensaje no puede estar vacío.")
            
            st.divider()
            st.subheader("Bandeja de Entrada")
            mensajes = obtener_mensajes(user)
            if mensajes.empty:
                st.info("No tienes mensajes.")
            else:
                for _, msg in mensajes.iterrows():
                    if msg['remitente'] == user:
                        st.info(f"**Tú** a {msg['destinatario']} ({msg['fecha']}): {msg['mensaje']}")
                    else:
                        st.success(f"**{msg['remitente']}** ({msg['fecha']}): {msg['mensaje']}")
                        if msg['leido'] == 0:
                            marcar_como_leido(msg['id'])

# --- PIE DE PÁGINA MEJORADO ---
st.divider()
col_logo, col_text = st.columns([0.2, 0.8])
with col_logo:
    if os.path.exists(DEVELOPER_LOGO):
        st.image(DEVELOPER_LOGO, width=100)
with col_text:
    st.markdown(
        """
        <div style="font-size: 14px; color: #555; font-weight: 300;">
            Desarrollado por Miguel Sánchez Morales
        </div>
        """,
        unsafe_allow_html=True
    )