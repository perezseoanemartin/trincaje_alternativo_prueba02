import streamlit as st
import formulas
import os
import numpy as np
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trincaje Pro Final", page_icon="⚓", layout="wide")
st.title("⚓ Calculadora de Trincaje (Corrección Definitiva Brazo E)")

# CONSTANTES
NOMBRE_HOJA = "CALCULO"  
ARCHIVO_EXCEL = "trincaje_alternativo_prueba02.xlsx"

# FACTORES DE MATERIAL EXACTOS
FACTORES_MATERIAL = {
    "Grillete/Tensor": 0.5,
    "Cabo Fibra": 0.33,
    "Cable 1 uso": 0.8,
    "Cable Reutiliz.": 0.3,
    "Fleje acero": 0.7,
    "Cincha": 0.5,
    "Bulldog Grip": 0.7,
    "Madera": 0.3
}

# --- 1. CARGA DEL MOTOR ---
@st.cache_resource
def cargar_motor():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    xl_model = formulas.ExcelModel().loads(ARCHIVO_EXCEL).finish()
    return xl_model

try:
    modelo = cargar_motor()
except Exception as e:
    st.error(f"Error cargando el motor: {e}")
    st.stop()

if not modelo:
    st.error(f"⚠️ Error: No encuentro '{ARCHIVO_EXCEL}'.")
    st.stop()

# --- 2. INTERFAZ: DATOS GENERALES ---
with st.expander("🚢 1. Datos del Buque y Carga", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Buque**")
        c_eslora = st.number_input("Eslora (C64)", value=0.0)
        c_velocidad = st.number_input("Velocidad (C65)", value=0.0)
        c_corr = st.number_input("Corrección Tabla 4 (C67)", value=0.0)
    with col2:
        st.markdown("**Aceleraciones**")
        c_ax = st.number_input("ax (C69)", value=0.0)
        c_ay = st.number_input("ay (C70)", value=0.0)
        c_az = st.number_input("az (C71)", value=0.0)
    with col3:
        st.markdown("**Carga**")
        e_eslora = st.number_input("Eslora Carga (E64)", value=0.0)
        e_manga = st.number_input("Manga Carga (E65)", value=0.0)
        e_altura = st.number_input("Altura Carga (E66)", value=0.0)
        e_masa = st.number_input("Masa Carga (E67)", value=0.0)
        e_friccion = st.number_input("Coef. Fricción (E68)", value=0.0)
    
    st.markdown("**Brazos de Estabilidad**")
    c_b1, c_b2, c_b3 = st.columns(3)
    e_brazo_v = c_b1.number_input("Brazo Vuelco (E69)", value=0.0)
    e_brazo_br = c_b2.number_input("Brazo Estab. Br (E70)", value=0.0)
    e_brazo_er = c_b3.number_input("Brazo Estab. Er (E71)", value=0.0)

# --- 3. CONFIGURACIÓN DE TRINCAS ---
st.subheader("⛓️ 3. Configuración de Trincas")

col_fs, _ = st.columns([1, 3])
FS_GLOBAL = col_fs.number_input("Factor de Seguridad (Divisor)", value=1.35, step=0.05)

tab_stbd, tab_port = st.tabs(["Estribor (Starboard)", "Babor (Portside)"])

def fila_trinca_completa(i, lado, fila_excel):
    # Layout ancho
    c_mat, c_val, c_uni, c_res, c_geo1, c_geo2, c_geo3, c_dir = st.columns([2, 1.2, 0.8, 1, 1, 1, 1, 1])
    
    # Material
    material = c_mat.selectbox(f"Trinca #{i+1}", list(FACTORES_MATERIAL.keys()), key=f"{lado}_mat_{fila_excel}", label_visibility="collapsed")
    factor_mat = FACTORES_MATERIAL[material]
    
    # Input Valor
    valor_input = c_val.number_input("Valor", value=0.0, key=f"{lado}_val_{fila_excel}", label_visibility="collapsed")
    
    # Input Unidad
    unidad = c_uni.selectbox("Uni", ["Tm", "KN"], key=f"{lado}_uni_{fila_excel}", label_visibility="collapsed")
    
    # --- CÁLCULO DE PYTHON ---
    val_paso1 = valor_input * 9.81 if unidad == "Tm" else valor_input
    val_paso2 = val_paso1 * factor_mat
    
    if FS_GLOBAL > 0:
        cs_final_d = val_paso2 / FS_GLOBAL
    else:
        cs_final_d = 0.0
    
    # Truncado a 2 decimales
    cs_final_d = float(int(cs_final_d * 100) / 100)
    
    if cs_final_d > 0:
        c_res.markdown(f":green[**= {cs_final_d}**]")
    else:
        c_res.caption("= 0.0")

    # Geometría
    brazo = c_geo1.number_input("Brazo", 0.0, key=f"{lado}_brazo_{fila_excel}", label_visibility="collapsed")
    alfa = c_geo2.number_input("Alfa", 0.0, key=f"{lado}_alfa_{fila_excel}", label_visibility="collapsed")
    beta = c_geo3.number_input("Beta", 0.0, key=f"{lado}_beta_{fila_excel}", label_visibility="collapsed")
    dire = c_dir.selectbox("Dir", ["-", "Pr", "Pp"], key=f"{lado}_dir_{fila_excel}", label_visibility="collapsed")
    
    return {
        "fila": fila_excel,
        "D": cs_final_d,
        "Brazo": brazo,
        "F": alfa,
        "G": beta,
        "H": dire
    }

datos_estribor = []
datos_babor = []

# --- ESTRIBOR ---
with tab_stbd:
    cols = st.columns([2, 1.2, 0.8, 1, 1, 1, 1, 1])
    cols[0].write("Material"); cols[1].write("MSL"); cols[2].write("Unit"); cols[3].write("CS (D)"); 
    cols[4].write("Brazo C (E)"); cols[5].write("Alfa"); cols[6].write("Beta"); cols[7].write("Dir")
    
    for i in range(6):
        datos_estribor.append(fila_trinca_completa(i, "st", 86 + i))

# --- BABOR ---
with tab_port:
    cols = st.columns([2, 1.2, 0.8, 1, 1, 1, 1, 1])
    cols[0].write("Material"); cols[1].write("MSL"); cols[2].write("Unit"); cols[3].write("CS (D)"); 
    cols[4].write("Brazo C (E)"); # <--- AHORA VA A COLUMNA E
    cols[5].write("Alfa"); cols[6].write("Beta"); cols[7].write("Dir")
    
    for i in range(6):
        datos_babor.append(fila_trinca_completa(i, "pt", 93 + i))

# --- 5. CÁLCULO ---
if st.button("🚀 Calcular Seguridad", type="primary"):
    
    inputs_dict = {}
    def add(celda, valor):
        key = f"'[{ARCHIVO_EXCEL}]{NOMBRE_HOJA}'!{celda}"
        inputs_dict[key] = valor

    try:
        # A) General
        add("C64", c_eslora); add("C65", c_velocidad); add("C67", c_corr)
        add("C69", c_ax); add("C70", c_ay); add("C71", c_az)
        add("E64", e_eslora); add("E65", e_manga); add("E66", e_altura)
        add("E67", e_masa); add("E68", e_friccion); add("E69", e_brazo_v)
        add("E70", e_brazo_br); add("E71", e_brazo_er)

        # B) Trincas Estribor (Columna E para Brazo)
        for t in datos_estribor:
            f = t['fila']
            add(f"D{f}", t['D']) 
            add(f"E{f}", t['Brazo'])
            add(f"F{f}", t['F'])
            add(f"G{f}", t['G'])
            add(f"H{f}", t['H'])

        # C) Trincas Babor (Columna E para Brazo - CORREGIDO)
        for t in datos_babor:
            f = t['fila']
            add(f"D{f}", t['D']) 
            add(f"E{f}", t['Brazo']) # <--- AQUÍ ESTÁ EL CAMBIO CLAVE (Columna E)
            add(f"F{f}", t['F'])
            add(f"G{f}", t['G'])
            add(f"H{f}", t['H'])

        # --- EJECUCIÓN ---
        solution = modelo.calculate(inputs=inputs_dict)

        def get(celda):
            key = f"'[{ARCHIVO_EXCEL}]{NOMBRE_HOJA}'!{celda}"
            res = solution[key].value
            if isinstance(res, Exception): return 0.0
            try: return float(res)
            except:
                try: return float(res.item())
                except: return 0.0
        
        def safe_float(v):
            try: return float(v)
            except: return 0.0

        # --- RESULTADOS ---
        st.divider()
        st.subheader("📊 Resultados de Seguridad")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        k104, l104 = safe_float(get("K104")), safe_float(get("L104"))
        k105, l105 = safe_float(get("K105")), safe_float(get("L105"))
        k106, l106 = safe_float(get("K106")), safe_float(get("L106"))
        k107, l107 = safe_float(get("K107")), safe_float(get("L107"))
        i109, k109 = safe_float(get("I109")), safe_float(get("K109"))
        i110, k110 = safe_float(get("I110")), safe_float(get("K110"))
        
        with col_res1:
            st.markdown("##### ↔️ Desliz. Transversal")
            st.metric("Estribor", f"{k104:.2f} / {l104:.2f}", "OK" if k104 > l104 else "FALLO")
            st.metric("Babor", f"{k105:.2f} / {l105:.2f}", "OK" if k105 > l105 else "FALLO")
        with col_res2:
            st.markdown("##### ↕️ Desliz. Longitudinal")
            st.metric("Proa", f"{k106:.2f} / {l106:.2f}", "OK" if k106 > l106 else "FALLO")
            st.metric("Popa", f"{k107:.2f} / {l107:.2f}", "OK" if k107 > l107 else "FALLO")
        with col_res3:
            st.markdown("##### 🔄 Vuelco")
            st.metric("Estribor", f"{i109:.2f} / {k109:.2f}", "OK" if i109 > k109 else "FALLO")
            st.metric("Babor", f"{i110:.2f} / {k110:.2f}", "OK" if i110 > k110 else "FALLO")

        # --- PANEL DE CONTROL ---
        st.divider()
        st.header("🔍 4. Panel de Control")
        
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            st.markdown("##### Fuerzas Estribor (Er)")
            st.write(f"CS Er (D86): {get('D86'):.2f}")
            st.write(f"CS*fy Er (K92): {get('K92'):.2f}")
            st.write(f"CS*c Er (N92): {get('N92'):.2f}")
            
        with c_ctrl2:
            st.markdown("##### Fuerzas Babor (Br)")
            st.write(f"CS Br (D93): {get('D93'):.2f}")
            st.write(f"CS*fy Br (K99): {get('K99'):.2f}")
            # Verificación clave: N93 ahora debería tener valor
            st.write(f"**CS*c Br (N93):** {get('N93'):.2f}") 

        st.markdown("##### Fuerzas Long y Vuelco")
        st.write(f"CS*fx Pr (D100): {get('D100'):.2f}")
        st.write(f"CS*fx Pp (G100): {get('G100'):.2f}")
        
    except Exception as e:
        st.error(f"Error detallado: {e}")
    
