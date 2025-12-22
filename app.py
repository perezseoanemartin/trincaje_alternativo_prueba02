import streamlit as st
import pandas as pd
import formulas
import os
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trincaje Pro v7", page_icon="⚓", layout="wide")
st.title("⚓ Calculadora de Trincaje (Completa)")

# CONSTANTES
NOMBRE_HOJA = "CALCULO"  
ARCHIVO_EXCEL = "trincaje_alternativo_prueba02.xlsx"

# DEFINICIÓN DE MATERIALES Y FACTORES
MAPA_MATERIALES = [
    {"nombre": "Grillete/Tensor",    "fila": 64, "factor": 0.5}, 
    {"nombre": "Cabo Fibra",         "fila": 65, "factor": 0.33}, 
    {"nombre": "Cable 1 uso",        "fila": 66, "factor": 0.8}, 
    {"nombre": "Cable Reutiliz.",    "fila": 67, "factor": 0.3}, 
    {"nombre": "Fleje acero",        "fila": 68, "factor": 0.7}, 
    {"nombre": "Cincha",             "fila": 69, "factor": 0.5}, 
    {"nombre": "Bulldog Grip",       "fila": 70, "factor": 0.7}, 
    {"nombre": "Madera",             "fila": 71, "factor": 0.3}
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

# --- 3. CÁLCULO DE RESISTENCIA (CS) ---
with st.expander("🛠️ 2. Resistencia de Materiales (MSL -> CS)", expanded=True):
    st.info("Introduce la Carga de Rotura (MSL).")
    
    inputs_g_h = {}
    opciones_calculadas = {"-": 0.0}
    
    cols_mat = st.columns(4)
    
    for i, item in enumerate(MAPA_MATERIALES):
        nombre = item["nombre"]
        fila = item["fila"]
        factor = item["factor"]
        
        with cols_mat[i % 4]:
            st.markdown(f"**{nombre}**")
            st.caption(f"x{factor}")
            val_g = st.number_input(f"Val G{fila}", key=f"G{fila}", value=0.0)
            val_h = st.selectbox(f"Und H{fila}", ["-", "Tm", "KN"], key=f"H{fila}", index=0)
            
            cs_resultado = 0.0
            if val_h == "Tm": cs_resultado = val_g * 9.8 * factor
            elif val_h == "KN": cs_resultado = val_g * factor
            
            inputs_g_h[f"G{fila}"] = val_g
            inputs_g_h[f"H{fila}"] = val_h
            
            if cs_resultado > 0:
                st.markdown(f":green[**= {cs_resultado:.2f} KN**]")
                etiqueta_dropdown = f"{cs_resultado:.2f} ({nombre})"
                opciones_calculadas[etiqueta_dropdown] = cs_resultado

# --- 4. CONFIGURACIÓN DE TRINCAS ---
st.subheader("⛓️ 3. Configuración de Trincas")
lista_opciones_trincas = list(opciones_calculadas.keys())
tab_stbd, tab_port = st.tabs(["Estribor (Starboard)", "Babor (Portside)"])

# ESTRIBOR
inputs_estribor = []
with tab_stbd:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("CS Calc"); cols[1].write("Brazo C (E)"); cols[2].write("Alfa"); cols[3].write("Beta"); cols[4].write("Dir")
    
    for i in range(6):
        fila_excel = 86 + i
        c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
        
        sel = c1.selectbox(f"Trinca #{i+1}", lista_opciones_trincas, key=f"st_Sel_{fila_excel}", label_visibility="collapsed")
        val_k = opciones_calculadas[sel]
        
        brazo = c2.number_input("Brazo", 0.0, key=f"st_Brazo_{fila_excel}", label_visibility="collapsed")
        alfa = c3.number_input("Alfa", 0.0, key=f"st_Alfa_{fila_excel}", label_visibility="collapsed")
        beta = c4.number_input("Beta", 0.0, key=f"st_Beta_{fila_excel}", label_visibility="collapsed")
        dire = c5.selectbox("Dir", ["-", "Pr", "Pp"], key=f"st_Dir_{fila_excel}", label_visibility="collapsed")
        
        inputs_estribor.append({
            "fila": fila_excel, "B": val_k, "Brazo": brazo, "F": alfa, "G": beta, "H": dire
        })

# BABOR
inputs_babor = []
with tab_port:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("CS Calc"); cols[1].write("Brazo C (C)"); cols[2].write("Alfa"); cols[3].write("Beta"); cols[4].write("Dir")
    
    for i in range(6):
        fila_excel = 93 + i
        c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
        
        sel = c1.selectbox(f"Trinca #{i+1}", lista_opciones_trincas, key=f"pt_Sel_{fila_excel}", label_visibility="collapsed")
        val_k = opciones_calculadas[sel]
        
        brazo = c2.number_input("Brazo", 0.0, key=f"pt_Brazo_{fila_excel}", label_visibility="collapsed")
        alfa = c3.number_input("Alfa", 0.0, key=f"pt_Alfa_{fila_excel}", label_visibility="collapsed")
        beta = c4.number_input("Beta", 0.0, key=f"pt_Beta_{fila_excel}", label_visibility="collapsed")
        dire = c5.selectbox("Dir", ["-", "Pr", "Pp"], key=f"pt_Dir_{fila_excel}", label_visibility="collapsed")
        
        inputs_babor.append({
            "fila": fila_excel, "B": val_k, "Brazo": brazo, "F": alfa, "G": beta, "H": dire
        })

# --- 5. CÁLCULO Y CONTROL ---

if st.button("🚀 Calcular y Verificar", type="primary"):
    
    inputs_dict = {}
    def add(celda, valor):
        key = f"'[{ARCHIVO_EXCEL}]{NOMBRE_HOJA}'!{celda}"
        inputs_dict[key] = valor

    try:
        # A) Inyección Datos Generales
        add("C64", c_eslora); add("C65", c_velocidad); add("C67", c_corr)
        add("C69", c_ax); add("C70", c_ay); add("C71", c_az)
        add("E64", e_eslora); add("E65", e_manga); add("E66", e_altura)
        add("E67", e_masa); add("E68", e_friccion); add("E69", e_brazo_v)
        add("E70", e_brazo_br); add("E71", e_brazo_er)

        # B) Materiales
        for celda, valor in inputs_g_h.items(): add(celda, valor)

        # C) Inyección Estribor
        for t in inputs_estribor:
            f = t['fila']
            add(f"B{f}", t['B']); add(f"E{f}", t['Brazo']); add(f"F{f}", t['F']); add(f"G{f}", t['G']); add(f"H{f}", t['H'])

        # D) Inyección Babor
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
                except: return str(res)

        # Helper para floats seguros
        def safe_float(v):
            try: return float(v)
            except: return 0.0

        # --- VISUALIZACIÓN PRINCIPAL ---
        st.divider()
        st.subheader("📊 Resultados Principales")
        
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

        # =========================================================
        # PANEL DE CONTROL EXTENDIDO
        # =========================================================
        st.divider()
        st.header("🔍 4. Panel de Control (Debug)")
        
        tab_ctrl_trincas, tab_ctrl_glob = st.tabs(["Detalle Trincas", "Variables Globales"])
        
        with tab_ctrl_trincas:
            # --- TABLA ESTRIBOR ---
            st.markdown("##### Estribor (Filas 86-91)")
            datos_stbd = []
            for r in range(86, 92):
                datos_stbd.append({
                    "Fila": r,
                    "Input B (Enviado)": safe_float(get(f"B{r}")), # Verify input
                    "Dir (H)": get(f"H{r}"),
                    "CS (D)": safe_float(get(f"D{r}")),
                    "fy (I)": safe_float(get(f"I{r}")),
                    "CS*fy (K)": safe_float(get(f"K{r}")),
                    "fx (L)": safe_float(get(f"L{r}")),
                    "CS*fx (M)": safe_float(get(f"M{r}")),
                    "CS*c (N)": safe_float(get(f"N{r}"))
                })
            st.dataframe(pd.DataFrame(datos_stbd).set_index("Fila"), use_container_width=True)
            
            # --- TABLA BABOR ---
            st.markdown("##### Babor (Filas 93-98)")
            datos_port = []
            for r in range(93, 99):
                datos_port.append({
                    "Fila": r,
                    "Input B (Enviado)": safe_float(get(f"B{r}")), # Verify input
                    "Dir (H)": get(f"H{r}"),
                    "CS (D)": safe_float(get(f"D{r}")),
                    "fy (I)": safe_float(get(f"I{r}")),
                    "CS*fy (K)": safe_float(get(f"K{r}")),
                    "fx (L)": safe_float(get(f"L{r}")),
                    "CS*fx (M)": safe_float(get(f"M{r}")),
                    "CS*c (N)": safe_float(get(f"N{r}"))
                })
            st.dataframe(pd.DataFrame(datos_port).set_index("Fila"), use_container_width=True)

        with tab_ctrl_glob:
            st.markdown("##### Variables de Control Solicitadas")
            
            # Creamos una tabla personalizada con todas las celdas pedidas
            control_vars = [
                {"Celda": "D100 (CS*fx Pr)", "Valor": safe_float(get("D100"))},
                {"Celda": "G100 (CS*fx Pp)", "Valor": safe_float(get("G100"))},
                {"Celda": "K104 (CS Lat Er)", "Valor": safe_float(get("K104"))},
                {"Celda": "K105 (CS Lat Br)", "Valor": safe_float(get("K105"))},
                {"Celda": "K106 (CS Long Pr)", "Valor": safe_float(get("K106"))},
                {"Celda": "K107 (CS Long Pp)", "Valor": safe_float(get("K107"))},
                {"Celda": "G109 (0.9*CS*c Er)", "Valor": safe_float(get("G109"))},
                {"Celda": "I109 (CS Total Er)", "Valor": safe_float(get("I109"))},
                {"Celda": "H110 (0.9*CS*c Br)", "Valor": safe_float(get("H110"))},
                {"Celda": "I110 (CS Total Br)", "Valor": safe_float(get("I110"))},
            ]
            
            st.dataframe(pd.DataFrame(control_vars), use_container_width=True)

    except Exception as e:
        st.error(f"Error detallado: {e}")
