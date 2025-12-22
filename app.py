import streamlit as st
import formulas
import os
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trincaje Pro v2", page_icon="⚓", layout="wide")
st.title("⚓ Calculadora de Trincaje (Motor Avanzado)")

# ==========================================
# CAMBIO REALIZADO AQUÍ ABAJO
# ==========================================
NOMBRE_HOJA = "CALCULO"  
ARCHIVO_EXCEL = "trincaje_alternativo_prueba02.xlsx" # <--- ¡Nombre actualizado!
# ==========================================

# Nombres de los materiales correspondientes a las filas 64 a 71
NOMBRES_MATERIALES = [
    "Grillete/Tensor (Fila 64)", 
    "Cabo Fibra (Fila 65)", 
    "Cable 1 uso (Fila 66)", 
    "Cable Reutilizable (Fila 67)", 
    "Fleje acero (Fila 68)", 
    "Cincha (Fila 69)", 
    "Bulldog Grip (Fila 70)", 
    "Madera (Fila 71)"
]

# --- 1. CARGA DEL MOTOR ---
@st.cache_resource
def cargar_motor():
    if not os.path.exists(ARCHIVO_EXCEL):
        return None
    # Compilamos el Excel
    xl_model = formulas.ExcelModel().loads(ARCHIVO_EXCEL).finish()
    return xl_model

try:
    modelo = cargar_motor()
except Exception as e:
    st.error(f"Error cargando el motor avanzado: {e}")
    st.stop()

if not modelo:
    st.error(f"⚠️ Error: No encuentro '{ARCHIVO_EXCEL}' en el repositorio. Verifica que lo has subido con ese nombre exacto.")
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

# --- 3. RESISTENCIA DE MATERIALES (Cálculo Dinámico de K) ---
with st.expander("🛠️ 2. Resistencia de Materiales (G64-H71)", expanded=True):
    st.info("Introduce los valores. La lista de trincas se actualizará automáticamente.")
    
    inputs_g_h = {}
    valores_k_calculados = {"🚫 Sin Trinca (0.00 t)": 0.0}
    
    filas_mat = range(64, 72)
    cols_mat = st.columns(4)
    
    for i, (nombre_mat, fila) in enumerate(zip(NOMBRES_MATERIALES, filas_mat)):
        with cols_mat[i % 4]:
            st.markdown(f"**{nombre_mat}**")
            val_g = st.number_input(f"Valor G{fila}", key=f"G{fila}", value=0.0)
            val_h = st.selectbox(f"Unidad H{fila}", ["Tm", "KN"], key=f"H{fila}")
            
            inputs_g_h[f"G{fila}"] = val_g
            inputs_g_h[f"H{fila}"] = val_h
            
            # Cálculo visual para el desplegable
            if val_h == "KN":
                k_valor = val_g * 0.10197 
            else:
                k_valor = val_g
            
            etiqueta = f"{nombre_mat.split('(')[0].strip()} ➡ {k_valor:.2f} t"
            valores_k_calculados[etiqueta] = k_valor

# --- 4. CONFIGURACIÓN DE TRINCAS ---
st.subheader("⛓️ 3. Configuración de Trincas")
st.caption("Selecciona el material usando los valores calculados arriba.")

opciones_dropdown = list(valores_k_calculados.keys())

tab_stbd, tab_port = st.tabs(["Estribor (Starboard)", "Babor (Portside)"])

def crear_fila_trinca(i, lado, fila_excel):
    c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    
    seleccion = c1.selectbox(
        f"Trinca #{i+1}", 
        opciones_dropdown, 
        key=f"{lado}_B{fila_excel}",
        label_visibility="collapsed"
    )
    valor_k_real = valores_k_calculados[seleccion]
    
    val_brazo = c2.number_input("Brazo", value=0.0, key=f"{lado}_Brazo{fila_excel}", label_visibility="collapsed")
    val_alfa = c3.number_input("Alfa", value=0.0, key=f"{lado}_Alfa{fila_excel}", label_visibility="collapsed")
    val_beta = c4.number_input("Beta", value=0.0, key=f"{lado}_Beta{fila_excel}", label_visibility="collapsed")
    val_dir = c5.selectbox("Dir", ["-", "Pr", "Pp"], key=f"{lado}_Dir{fila_excel}", label_visibility="collapsed")
    
    return {
        "fila": fila_excel, "B": valor_k_real, "Brazo": val_brazo, "F": val_alfa, "G": val_beta, "H": val_dir
    }

inputs_estribor = []
with tab_stbd:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("Material (Valor K)")
    cols[1].write("Brazo C (E)")
    cols[2].write("Ángulo α (F)")
    cols[3].write("Ángulo β (G)")
    cols[4].write("Dir (H)")
    for i in range(6):
        inputs_estribor.append(crear_fila_trinca(i, "st", 86 + i))

inputs_babor = []
with tab_port:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("Material (Valor K)")
    cols[1].write("Brazo C (C)")
    cols[2].write("Ángulo α (F)")
    cols[3].write("Ángulo β (G)")
    cols[4].write("Dir (H)")
    for i in range(6):
        inputs_babor.append(crear_fila_trinca(i, "pt", 93 + i))

# --- 5. LÓGICA DE CÁLCULO ---

if st.button("🚀 Calcular Seguridad", type="primary"):
    
    inputs_dict = {}
    def add(celda, valor):
        key = f"'[{ARCHIVO_EXCEL}]{NOMBRE_HOJA}'!{celda}"
        inputs_dict[key] = valor

    try:
        # A) Datos Generales
        add("C64", c_eslora); add("C65", c_velocidad); add("C67", c_corr)
        add("C69", c_ax); add("C70", c_ay); add("C71", c_az)
        add("E64", e_eslora); add("E65", e_manga); add("E66", e_altura)
        add("E67", e_masa); add("E68", e_friccion); add("E69", e_brazo_v)
        add("E70", e_brazo_br); add("E71", e_brazo_er)

        # B) Materiales
        for celda, valor in inputs_g_h.items():
            add(celda, valor)

        # C) Trincas
        for t in inputs_estribor:
            f = t['fila']
            add(f"B{f}", t['B']); add(f"E{f}", t['Brazo']); add(f"F{f}", t['F']); add(f"G{f}", t['G']); add(f"H{f}", t['H'])
            
        for t in inputs_babor:
            f = t['fila']
            add(f"B{f}", t['B']); add(f"C{f}", t['Brazo']); add(f"F{f}", t['F']); add(f"G{f}", t['G']); add(f"H{f}", t['H'])

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

        # --- VISUALIZACIÓN ---
        st.divider()
        st.subheader("📊 Informe de Seguridad")
        
        k104, l104 = get("K104"), get("L104")
        k105, l105 = get("K105"), get("L105")
        k106, l106 = get("K106"), get("L106")
        k107, l107 = get("K107"), get("L107")
        i109, k109 = get("I109"), get("K109")
        i110, k110 = get("I110"), get("K110")
        
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.markdown("### ↔️ Deslizamiento (K > L)")
            st.metric("Transv. Estribor", f"{k104:.2f} / {l104:.2f}", "OK" if k104 > l104 else "FALLO", delta_color="normal")
            st.metric("Transv. Babor", f"{k105:.2f} / {l105:.2f}", "OK" if k105 > l105 else "FALLO", delta_color="normal")
            st.metric("Long. Proa", f"{k106:.2f} / {l106:.2f}", "OK" if k106 > l106 else "FALLO", delta_color="normal")
            st.metric("Long. Popa", f"{k107:.2f} / {l107:.2f}", "OK" if k107 > l107 else "FALLO", delta_color="normal")

        with col_r2:
            st.markdown("### 🔄 Vuelco (I > K)")
            st.metric("Vuelco Estribor", f"{i109:.2f} / {k109:.2f}", "OK" if i109 > k109 else "FALLO", delta_color="normal")
            st.metric("Vuelco Babor", f"{i110:.2f} / {k110:.2f}", "OK" if i110 > k110 else "FALLO", delta_color="normal")

    except Exception as e:
        st.error(f"Error detallado: {e}")
