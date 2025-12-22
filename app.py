import streamlit as st
import pandas as pd # Necesitamos pandas para mostrar las tablas de control
import formulas
import os
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Trincaje Pro v5 (Control)", page_icon="⚓", layout="wide")
st.title("⚓ Calculadora de Trincaje (Con Panel de Control)")

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
tab_stbd, tab_port = st.tabs(["Estribor", "Babor"])

def crear_fila_trinca(i, lado, fila_excel):
    c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    seleccion = c1.selectbox(f"Trinca #{i+1}", lista_opciones_trincas, key=f"{lado}_Sel_{fila_excel}", label_visibility="collapsed")
    valor_a_enviar = opciones_calculadas[seleccion]
    val_brazo = c2.number_input("Brazo", value=0.0, key=f"{lado}_Brazo{fila_excel}", label_visibility="collapsed")
    val_alfa = c3.number_input("Alfa", value=0.0, key=f"{lado}_Alfa{fila_excel}", label_visibility="collapsed")
    val_beta = c4.number_input("Beta", value=0.0, key=f"{lado}_Beta{fila_excel}", label_visibility="collapsed")
    val_dir = c5.selectbox("Dir", ["-", "Pr", "Pp"], key=f"{lado}_Dir{fila_excel}", label_visibility="collapsed")
    
    return {"fila": fila_excel, "B": valor_a_enviar, "Brazo": val_brazo, "F": val_alfa, "G": val_beta, "H": val_dir}

inputs_estribor = []
with tab_stbd:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("CS Calc"); cols[1].write("Brazo C"); cols[2].write("Alfa"); cols[3].write("Beta"); cols[4].write("Dir")
    for i in range(6): inputs_estribor.append(crear_fila_trinca(i, "st", 86 + i))

inputs_babor = []
with tab_port:
    cols = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    cols[0].write("CS Calc"); cols[1].write("Brazo C"); cols[2].write("Alfa"); cols[3].write("Beta"); cols[4].write("Dir")
    for i in range(6): inputs_babor.append(crear_fila_trinca(i, "pt", 93 + i))

# --- 5. LÓGICA DE CÁLCULO Y CONTROL ---

if st.button("🚀 Calcular y Verificar", type="primary"):
    
    inputs_dict = {}
    def add(celda, valor):
        key = f"'[{ARCHIVO_EXCEL}]{NOMBRE_HOJA}'!{celda}"
        inputs_dict[key] = valor

    try:
        # A) Inyección
        add("C64", c_eslora); add("C65", c_velocidad); add("C67", c_corr)
        add("C69", c_ax); add("C70", c_ay); add("C71", c_az)
        add("E64", e_eslora); add("E65", e_manga); add("E66", e_altura)
        add("E67", e_masa); add("E68", e_friccion); add("E69", e_brazo_v)
        add("E70", e_brazo_br); add("E71", e_brazo_er)

        for celda, valor in inputs_g_h.items(): add(celda, valor)

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

        # --- VISUALIZACIÓN PRINCIPAL ---
        st.divider()
        st.subheader("📊 Resultados Principales")
        
        col_res1, col_res2 = st.columns(2)
        # Recuperamos datos clave para visualización rápida
        k104, l104 = get("K104"), get("L104")
        k105, l105 = get("K105"), get("L105")
        i109, k109 = get("I109"), get("K109")
        i110, k110 = get("I110"), get("K110")
        
        with col_res1:
            st.metric("Desliz. Estribor", f"{k104:.2f} / {l104:.2f}", "OK" if k104 > l104 else "FALLO")
            st.metric("Desliz. Babor", f"{k105:.2f} / {l105:.2f}", "OK" if k105 > l105 else "FALLO")
        with col_res2:
            st.metric("Vuelco Estribor", f"{i109:.2f} / {k109:.2f}", "OK" if i109 > k109 else "FALLO")
            st.metric("Vuelco Babor", f"{i110:.2f} / {k110:.2f}", "OK" if i110 > k110 else "FALLO")

        # =========================================================
        # NUEVO APARTADO: PANEL DE CONTROL (OUTPUTS SOLICITADOS)
        # =========================================================
        st.divider()
        st.header("🔍 4. Panel de Control (Valores Internos)")
        
        tab_ctrl_trincas, tab_ctrl_fuerzas = st.tabs(["Detalle Trincas", "Fuerzas y Momentos"])
        
        with tab_ctrl_trincas:
            st.write("Valores individuales por trinca (Filas 86-91 y 93-98)")
            
            # --- TABLA ESTRIBOR ---
            st.markdown("##### Estribor (Filas 86-91)")
            datos_stbd = []
            for r in range(86, 92):
                datos_stbd.append({
                    "Fila": r,
                    "CS (D)": get(f"D{r}"),
                    "fy (I)": get(f"I{r}"),
                    "CS*fy (K)": get(f"K{r}"),
                    "fx (L)": get(f"L{r}"),
                    "CS*fx (M)": get(f"M{r}"),
                    "CS*c (N)": get(f"N{r}")
                })
            st.dataframe(pd.DataFrame(datos_stbd).set_index("Fila"), use_container_width=True)
            
            # --- TABLA BABOR ---
            st.markdown("##### Babor (Filas 93-98)")
            datos_port = []
            for r in range(93, 99):
                datos_port.append({
                    "Fila": r,
                    "CS (D)": get(f"D{r}"),
                    "fy (I)": get(f"I{r}"),
                    "CS*fy (K)": get(f"K{r}"),
                    "fx (L)": get(f"L{r}"),
                    "CS*fx (M)": get(f"M{r}"),
                    "CS*c (N)": get(f"N{r}")
                })
            st.dataframe(pd.DataFrame(datos_port).set_index("Fila"), use_container_width=True)

            # --- SUMATORIOS INTERMEDIOS ---
            st.markdown("##### Sumatorios Intermedios")
            c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
            c_sum1.metric("CS*fy Er (K92)", f"{get('K92'):.2f}")
            c_sum1.metric("CS*c Er (N92)", f"{get('N92'):.2f}")
            
            c_sum2.metric("CS*fy Br (K99)", f"{get('K99'):.2f}")
            c_sum2.metric("CS*c Br (N99)", f"{get('N99'):.2f}")
            
            c_sum3.metric("CS*fx Pr (D100)", f"{get('D100'):.2f}")
            c_sum4.metric("CS*fx Pp (G100)", f"{get('G100'):.2f}")

        with tab_ctrl_fuerzas:
            st.markdown("##### Análisis de Fuerzas y Momentos")
            
            # Organizamos los datos finales en una tabla limpia
            datos_fuerzas = [
                {"Parámetro": "CS * fy (F104/F105)", "Estribor/Proa": get("F104"), "Babor/Popa": get("F105")},
                {"Parámetro": "fz (G106/G107)",      "Estribor/Proa": get("G106"), "Babor/Popa": get("G107")},
                {"Parámetro": "fx * FZ (H106/H107)", "Estribor/Proa": get("H106"), "Babor/Popa": get("H107")},
                {"Parámetro": "CS * fx (I106/I107)", "Estribor/Proa": get("I106"), "Babor/Popa": get("I107")},
                {"Parámetro": "CS (K104-K107)",      "Estribor/Proa": get("K104"), "Babor/Popa": get("K105")}, # Fila 104/105
                {"Parámetro": "CS (K106-K107)",      "Estribor/Proa": get("K106"), "Babor/Popa": get("K107")}, # Fila 106/107
            ]
            st.dataframe(pd.DataFrame(datos_fuerzas), use_container_width=True)
            
            st.markdown("##### Momentos de Estabilidad")
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("0.9 * CS * c Er (G109)", f"{get('G109'):.2f}")
            cm2.metric("0.9 * CS * c Br (H110)", f"{get('H110'):.2f}")
            cm3.metric("CS Total (I109/I110)", f"Er: {get('I109'):.2f} / Br: {get('I110'):.2f}")

    except Exception as e:
        st.error(f"Error detallado: {e}")
