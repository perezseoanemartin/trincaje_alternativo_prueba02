import streamlit as st
import formulas
import os
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trincaje Pro v3", page_icon="⚓", layout="wide")
st.title("⚓ Calculadora de Trincaje (Motor Avanzado)")

# CONSTANTES
NOMBRE_HOJA = "CALCULO"  
ARCHIVO_EXCEL = "trincaje_alternativo_prueba02.xlsx" # Asegúrate que este es el nombre correcto

# Definimos la relación exacta: Nombre -> Fila de Origen (K)
# Esto asegura que "Grillete" siempre tome el dato de la fila 64, etc.
MAPA_MATERIALES = [
    {"nombre": "Grillete/Tensor", "fila": 64}, 
    {"nombre": "Cabo Fibra",      "fila": 65}, 
    {"nombre": "Cable 1 uso",     "fila": 66}, 
    {"nombre": "Cable Reutiliz.", "fila": 67}, 
    {"nombre": "Fleje acero",     "fila": 68}, 
    {"nombre": "Cincha",          "fila": 69}, 
    {"nombre": "Bulldog Grip",    "fila": 70}, 
    {"nombre": "Madera",          "fila": 71}
]

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
    st.error(f"⚠️ Error: No encuentro '{ARCHIVO_EXCEL}' en el repositorio.")
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

# --- 3. RESISTENCIA DE MATERIALES (Cálculo de valores K) ---
with st.expander("🛠️ 2. Resistencia de Materiales (G64-H71)", expanded=True):
    st.info("Introduce los valores G y H. La App calculará la resistencia K para usarla en las trincas.")
    
    # Aquí guardaremos los inputs para Excel y también los valores calculados de K
    inputs_g_h = {}
    valores_k_mapa = {} # Diccionario: "Nombre Material" -> Valor Numérico K
    
    cols_mat = st.columns(4)
    
    for i, item in enumerate(MAPA_MATERIALES):
        nombre = item["nombre"]
        fila = item["fila"]
        
        with cols_mat[i % 4]:
            st.markdown(f"**{nombre}**")
            val_g = st.number_input(f"Valor G{fila}", key=f"G{fila}", value=0.0)
            val_h = st.selectbox(f"Unidad H{fila}", ["Tm", "KN"], key=f"H{fila}")
            
            # 1. Guardamos los inputs crudos para enviarlos al Excel (por si acaso)
            inputs_g_h[f"G{fila}"] = val_g
            inputs_g_h[f"H{fila}"] = val_h
            
            # 2. CALCULAMOS K AQUÍ MISMO (Lógica Python)
            # Si es KN, multiplicamos por 0.10197 para pasar a Toneladas. Si es Tm, se queda igual.
            if val_h == "KN":
                k_calculado = val_g * 0.10197
            else:
                k_calculado = val_g
            
            # Guardamos este valor asociado al nombre del material
            valores_k_mapa[nombre] = k_calculado
            
            # Mostramos pequeño feedback visual
            st.caption(f"K{fila} = {k_calculado:.2f} t")

# --- 4. CONFIGURACIÓN DE TRINCAS ---
st.subheader("⛓️ 3. Configuración de Trincas")

# Preparamos las opciones para el desplegable
lista_opciones = ["-"] + [m["nombre"] for m in MAPA_MATERIALES]

tab_stbd, tab_port = st.tabs(["Estribor", "Babor"])

def crear_fila_trinca(i, lado, fila_excel):
    c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    
    # SELECTOR DE MATERIAL
    seleccion_nombre = c1.selectbox(
        f"Trinca #{i+1}", 
        lista_opciones, 
        key=f"{lado}_Sel_{fila_excel}",
        label_visibility="collapsed"
    )
    
    # LÓGICA CLAVE: Si selecciona un nombre, cogemos su valor K calculado. Si es "-", es 0.
    if seleccion_nombre == "-":
        valor_a_enviar = 0.0
    else:
        valor_a_enviar = valores_k_mapa[seleccion_nombre]
    
    # Resto de inputs
    val_brazo = c2.number_input("Brazo", value=0.0, key=f"{lado}_Brazo{fila_excel}", label_visibility="collapsed")
    val_alfa = c3.number_input("Alfa", value=0.0, key=f"{lado}_Alfa{fila_excel}", label_visibility="collapsed")
    val_beta = c4.number_input("Beta", value=0.0, key=f"{lado}_Beta{fila_excel}", label_visibility="collapsed")
    val_dir = c5.selectbox("Dir", ["-", "Pr", "Pp"], key=f"{lado}_Dir{fila_excel}", label_visibility="collapsed")
    
    return {
        "fila": fila_excel,
        "B": valor_a_enviar, # <--- AQUÍ VA EL VALOR K (NUMÉRICO)
        "Brazo": val_brazo,
        "F": val_alfa,
        "G": val_beta,
        "H": val_dir
    }

# --- PESTAÑA ESTRIBOR ---
inputs_estribor = []
with tab_stbd:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("Material (Selección)")
    cols[1].write("Brazo C (E)")
    cols[2].write("Ángulo α (F)")
    cols[3].write("Ángulo β (G)")
    cols[4].write("Dir (H)")
    for i in range(6):
        inputs_estribor.append(crear_fila_trinca(i, "st", 86 + i))

# --- PESTAÑA BABOR ---
inputs_babor = []
with tab_port:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("Material (Selección)")
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

        # B) Materiales (Inputs G y H)
        for celda, valor in inputs_g_h.items():
            add(celda, valor)

        # C) Trincas (Inyectamos el VALOR K NUMÉRICO en la columna B)
        for t in inputs_estribor:
            f = t['fila']
            add(f"B{f}", t['B'])   # Esto lleva el valor K64, K65... o 0
            add(f"E{f}", t['Brazo']); add(f"F{f}", t['F']); add(f"G{f}", t['G']); add(f"H{f}", t['H'])
            
        for t in inputs_babor:
            f = t['fila']
            add(f"B{f}", t['B'])   # Esto lleva el valor K64, K65... o 0
            add(f"C{f}", t['Brazo']); add(f"F{f}", t['F']); add(f"G{f}", t['G']); add(f"H{f}", t['H'])

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
            st.metric("Transv. Estribor", f"{k104:.2f} / {l104:.2f}", "OK" if k104 > l104 else "FALLO")
            st.metric("Transv. Babor", f"{k105:.2f} / {l105:.2f}", "OK" if k105 > l105 else "FALLO")
            st.metric("Long. Proa", f"{k106:.2f} / {l106:.2f}", "OK" if k106 > l106 else "FALLO")
            st.metric("Long. Popa", f"{k107:.2f} / {l107:.2f}", "OK" if k107 > l107 else "FALLO")

        with col_r2:
            st.markdown("### 🔄 Vuelco (I > K)")
            st.metric("Vuelco Estribor", f"{i109:.2f} / {k109:.2f}", "OK" if i109 > k109 else "FALLO")
            st.metric("Vuelco Babor", f"{i110:.2f} / {k110:.2f}", "OK" if i110 > k110 else "FALLO")

    except Exception as e:
        st.error(f"Error detallado: {e}")
