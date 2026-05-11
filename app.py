import streamlit as st
import pandas as pd
import plotly.express as px

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Contraseña",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False

    elif not st.session_state["password_correct"]:
        st.text_input(
            "Contraseña",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("Contraseña incorrecta")
        return False

    else:
        return True

if not check_password():
    st.stop()
# ------------------ CONFIG
st.set_page_config(
    page_title="Dashboard Signos",
    layout="wide"
)

# ------------------ COLORES MARCA
COLOR_PRINCIPAL = "#5FA8A8"
COLOR_SECUNDARIO = "#A8D5D5"
COLOR_OSCURO = "#1F3C3D"

# ------------------ ESTILOS
st.markdown(f"""
<style>
.stApp {{
    background-color: #F7FAFA;
}}

h1, h2, h3 {{
    color: {COLOR_OSCURO};
}}

.stTabs [role="tab"] {{
    background-color: #E8F3F3;
    border-radius: 10px;
    padding: 10px;
}}

.stTabs [aria-selected="true"] {{
    background-color: {COLOR_PRINCIPAL};
    color: white;
}}

[data-testid="metric-container"] {{
    background-color: white;
    border-radius: 15px;
    padding: 20px;
    border: 1px solid #E0EEEE;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}}
</style>
""", unsafe_allow_html=True)

# ------------------ HEADER PRO
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logo_blanco.png")

st.markdown(f"""
<div style='background: linear-gradient(90deg, {COLOR_PRINCIPAL}, {COLOR_SECUNDARIO}); padding: 35px; border-radius: 20px; text-align: center; margin-bottom: 30px;'>

<img src="data:image/png;base64,{logo_base64}" width="240"/>

<p style="color:white; font-size:20px; margin-top:10px; font-weight:300; letter-spacing:1px;">
Panel de análisis y gestión
</p>

</div>
""", unsafe_allow_html=True)

# ------------------ CARGA
df_general = pd.read_csv("data_general.csv", sep=";")
df_papeles = pd.read_csv("data_papeles.csv", sep=";")
df_contabilidad = pd.read_csv("data_contabilidad.csv", sep=";")

# ------------------ PREPARACION
df_general["FECHA"] = pd.to_datetime(df_general["FECHA"])
df_papeles["FECHA"] = pd.to_datetime(df_papeles["FECHA"])

df_contabilidad["MONTO"] = df_contabilidad["MONTO"].astype(str)

# 🔥 Solo limpiar si tiene coma (formato europeo)
df_contabilidad["MONTO"] = df_contabilidad["MONTO"].apply(
    lambda x: x.replace(".", "").replace(",", ".") if "," in x else x
)

df_contabilidad["MONTO"] = pd.to_numeric(
    df_contabilidad["MONTO"],
    errors="coerce"
).fillna(0)
df_contabilidad["TIPO"] = df_contabilidad["TIPO"].str.upper().str.strip()
df_contabilidad["FECHA"] = pd.to_datetime(df_contabilidad["FECHA"], errors="coerce")
df_contabilidad = df_contabilidad.dropna(subset=["FECHA"])

# ------------------ FILTRO GLOBAL DE FECHAS

fecha_min = min(
    df_general["FECHA"].min(),
    df_papeles["FECHA"].min(),
    df_contabilidad["FECHA"].min()
)

fecha_max = max(
    df_general["FECHA"].max(),
    df_papeles["FECHA"].max(),
    df_contabilidad["FECHA"].max()
)

st.markdown("### Filtrar período de análisis")

col1, col2 = st.columns(2)

with col1:
    fecha_inicio = st.date_input(
        "Fecha desde",
        value=fecha_min,
        min_value=fecha_min,
        max_value=fecha_max
    )

with col2:
    fecha_fin = st.date_input(
        "Fecha hasta",
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max
    )

# Aplicar filtros
df_general = df_general[
    (df_general["FECHA"] >= pd.to_datetime(fecha_inicio)) &
    (df_general["FECHA"] <= pd.to_datetime(fecha_fin))
]

df_papeles = df_papeles[
    (df_papeles["FECHA"] >= pd.to_datetime(fecha_inicio)) &
    (df_papeles["FECHA"] <= pd.to_datetime(fecha_fin))
]

df_contabilidad = df_contabilidad[
    (df_contabilidad["FECHA"] >= pd.to_datetime(fecha_inicio)) &
    (df_contabilidad["FECHA"] <= pd.to_datetime(fecha_fin))
]

# ------------------ TABS
tab1, tab2, tab3, tab4 = st.tabs(["General", "Estudios", "Economía", "Contabilidad"])

# ================== TAB 1 ==================
with tab1:
    # FILTRAR SIN REVALIDACIONES
    df_filtrado = df_general[
        ~df_general["MEDICO"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.contains("Revalidacion", na=False)
    ]

    # ---------------- MOVIMIENTO
    st.subheader("Movimiento de personas por día")

    df_filtrado["FECHA"] = pd.to_datetime(df_filtrado["FECHA"])

    personas_dia = df_filtrado.groupby(
        df_filtrado["FECHA"].dt.strftime("%Y-%m-%d")
    ).size()

    st.line_chart(personas_dia, color="#5FA8A8")

    # ---------------- TORTA
    st.subheader("Distribución por tipo de trámite")

    tramites = df_filtrado["TIPO_DE_TRAMITE"].value_counts()

    labels = [
        f"{tipo} ({cantidad})"
        for tipo, cantidad in zip(tramites.index, tramites.values)
    ]

    total_tramites = tramites.sum()

    fig = px.pie(
        values=tramites.values,
        names=tramites.index,
        color_discrete_sequence=[
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO,
            "#9476DB",
            "#EB6E9E",
            "#EBB56E",
            "#E3EB6E"
        ]
    )

    fig.update_traces(
        textinfo="percent"
    )

    fig.update_layout(
        title=f"Total de trámites: {total_tramites}"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ---------------- RECEPCIONISTA
    st.subheader("Atención por recepcionista")
    
    df_general["ONLINE"] = (
        df_general["ONLINE"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df_general["TIPO_ATENCION"] = df_general["ONLINE"].str.lower().apply(
        lambda x: "ONLINE" if "online" in x else "PAPELES"
    )

    df_filtrado = df_general[
    df_general["TIPO_DE_TRAMITE"].fillna("").str.lower().str.contains("licencia comun", na=False)
    ]

    recep = df_filtrado.groupby(["RECEPCIONISTA", "TIPO_ATENCION"]).size().unstack(fill_value=0)
    # Asegurar columnas
    for col in ["ONLINE", "PAPELES"]:
        if col not in recep.columns:
            recep[col] = 0
    recep = recep.reset_index()

    fig = px.bar(
        recep,
        x="RECEPCIONISTA",
        y=["ONLINE", "PAPELES"],
        barmode="stack",
        color_discrete_sequence=[COLOR_PRINCIPAL, COLOR_SECUNDARIO]
    )

    st.plotly_chart(fig, use_container_width=True)

# ================== TAB 2 ==================
with tab2:
    st.subheader("Estudios realizados")

    estudio = st.selectbox(
        "Tipo de estudio",
        [
            "ECG",
            "EEG",
            "AUDIOMETRIA",
            "PSICOLOGICO",
            "TEST_PSICOLOGICO",
            "ESPIROMETRIA",
            "ERGOMETRIA",
            "MEDICO"
        ]
    )

    valores = (
        df_general[estudio]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valores = valores[~valores.isin(["", "no aplica", "nan"])]

    # Limpiar vacíos
    valores = valores[~valores.isin(["", "no aplica", "nan"])]

    # 🔥 Si es médico, excluir revalidaciones
    if estudio == "MEDICO":
        valores = valores[
            ~valores.str.contains("revalid", na=False)
        ]

    conteo = valores.value_counts().reset_index()
    conteo.columns = ["Tipo", "Cantidad"]

    fig = px.bar(
        conteo,
        x="Tipo",
        y="Cantidad",
        color_discrete_sequence=[COLOR_PRINCIPAL]
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- REVALIDACIONES LICENCIAS COMUNES
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Licencias comunes vs Revalidaciones")

    # Normalizar
    medico_valores = (
        df_general["MEDICO"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Licencias comunes nuevas
    licencias_comunes = medico_valores[
        medico_valores.str.contains("licencia Comun")
        & ~medico_valores.str.contains("revalidacion")
    ].count()

    # Revalidaciones comunes
    revalidaciones_comunes = medico_valores[
        medico_valores.str.contains("revalidacion")
        & medico_valores.str.contains("licencia Comun")
    ].count()

    # Si "comun" no aparece en revalidaciones, probar solo revalid
    if revalidaciones_comunes == 0:
        revalidaciones_comunes = medico_valores[
            medico_valores.str.contains("revalidacion")
        ].count()

    # Dataframe
    medico_df = pd.DataFrame({
        "Tipo": ["licencia comun", "revalidacion"],
        "Cantidad": [licencia_comun, revalidacion]
    })

    medico_df = medico_df[medico_df["Cantidad"] > 0]

    fig = px.pie(
        medico_df,
        names="Tipo",
        values="Cantidad",
        color_discrete_sequence=[
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO
        ]
    )

    fig.update_traces(
        textinfo="percent+label"
    )

    fig.update_layout(
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# ================== TAB 3 ==================
with tab3: 
    import plotly.express as px

    conteo_general = pd.Series({
        "EFECTIVO": (df_general["MONTO_EN_EFECTIVO"] > 0).sum(),
        "MERCADOPAGO": (df_general["MONTO_EN_MERCADOPAGO"] > 0).sum(),
        "SANTANDER": (df_general["MONTO_EN_SANTANDER"] > 0).sum()
    })

    conteo_papeles = pd.Series({
        "EFECTIVO": (df_papeles["MONTO_EN_EFECTIVO"] > 0).sum(),
        "MERCADOPAGO": (df_papeles["MONTO_EN_MERCADOPAGO"] > 0).sum(),
        "SANTANDER": (df_papeles["MONTO_EN_SANTANDER"] > 0).sum()
    })

    metodos_df = conteo_general.add(conteo_papeles, fill_value=0).reset_index()
    metodos_df.columns = ["Metodo", "Cantidad"]

    # opcional: limpiar métodos en 0
    metodos_df = metodos_df[metodos_df["Cantidad"] > 0]

    st.subheader("Métodos de pago (distribución)")

    fig = px.pie(
        metodos_df,
        names="Metodo",
        values="Cantidad",
        color_discrete_sequence=[
            COLOR_PRINCIPAL,
            COLOR_SECUNDARIO,
            COLOR_OSCURO
        ]
    )

    fig.update_traces(
        textinfo="percent+label"
    )

    fig.update_layout(
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

# INGRESOS EN EL TIEMPO
    def preparar_datos(df):

        df["TOTAL_MONTO"] = (
            df["MONTO_EN_EFECTIVO"] +
            df["MONTO_EN_MERCADOPAGO"] +
            df["MONTO_EN_SANTANDER"]
        )
        metodos = df[[
            "MONTO_EN_EFECTIVO",
            "MONTO_EN_MERCADOPAGO",
            "MONTO_EN_SANTANDER"
        ]].sum()
        ingresos_fecha = df.groupby("FECHA")["TOTAL_MONTO"].sum().reset_index()
        
        return df, metodos, ingresos_fecha
    
   
    
    df_general, metodos_general, ingresos_general = preparar_datos(df_general)
    df_papeles, metodos_papeles, ingresos_papeles = preparar_datos(df_papeles)


    
    # RENOMBRAR PARA GRAFICO 
    ingresos_general = ingresos_general.rename(columns={"TOTAL_MONTO": "GENERAL"})
    ingresos_papeles = ingresos_papeles.rename(columns={"TOTAL_MONTO": "PAPELES"})
    
     # ❌ eliminar fechas basura
    ingresos_general = ingresos_general[
        ingresos_general["FECHA"] > "2000-01-01"
    ]

# ❌ eliminar días con 0 (opcional pero recomendable)
    ingresos_general = ingresos_general[
        ingresos_general["GENERAL"] > 0
    ]

    ingresos_papeles = ingresos_papeles[
       ingresos_papeles["PAPELES"] > 0
    ]   
    
    
    # UNIR 
    
    df_lineas = pd.merge(
        ingresos_general,
        ingresos_papeles,
        on="FECHA",
        how="outer"
    ).fillna(0) 
    df_lineas["TOTAL"] = df_lineas["GENERAL"] + df_lineas["PAPELES"]
    df_lineas["FECHA"] = pd.to_datetime(df_lineas["FECHA"])

    # 🔥 ORDENAR
    df_lineas = df_lineas.sort_values("FECHA")

    df_lineas = df_lineas.set_index("FECHA")
    

    st.subheader("Ingresos en el tiempo") 
    st.line_chart(df_lineas,color=["#5FA8A8", "#1F3C3D","#9476DB"])

# ================== TAB 4 ==================
with tab4:
    # 🔥 Excluir faltantes y sobrantes
    df_conta_filtrado = df_contabilidad[
        ~df_contabilidad["CONCEPTO"]
        .astype(str)
        .str.upper()
        .str.strip()
        .isin(["FALTANTE", "SOBRANTE"])
    ]

    ingresos = df_conta_filtrado[
        df_conta_filtrado["TIPO"] == "INGRESO"
    ]["MONTO"].sum()

    gastos = df_conta_filtrado[
        df_conta_filtrado["TIPO"] == "GASTO"
    ]["MONTO"].sum()

    balance = ingresos - gastos

    col1, col2, col3 = st.columns(3)

    col1.metric("Ingresos", f"${ingresos:,.0f}")
    col2.metric("Gastos", f"${gastos:,.0f}")
    col3.metric("Balance", f"${balance:,.0f}", delta=f"${balance:,.0f}")

    st.markdown("<hr>", unsafe_allow_html=True)

        # ---------------- GASTO PROMEDIO POR PERSONA
    st.subheader("Gasto promedio por persona atendida")

    # Total personas atendidas
    total_personas = len(df_general) + len(df_papeles)

    # Evitar división por cero
    gasto_por_persona = gastos / total_personas if total_personas > 0 else 0

    # Métrica principal
    col1, col2 = st.columns(2)

    col1.metric(
       "Costo promedio por persona",
      f"${gasto_por_persona:,.2f}"
    )

    col2.metric(
        "Total personas atendidas",
        f"{total_personas:,}"
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    # TORTA
    st.subheader("Ingresos vs Gastos")

    fig = px.pie(
        values=[ingresos, gastos],
        names=["Ingresos", "Gastos"],
        color_discrete_sequence=[COLOR_PRINCIPAL, COLOR_SECUNDARIO]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # GASTOS
    st.subheader("Gastos por categoría")

    gastos_cat = (
        df_contabilidad[df_contabilidad["TIPO"] == "GASTO"]
        .groupby("CONCEPTO")["MONTO"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        gastos_cat,
        x="CONCEPTO",
        y="MONTO",
        color_discrete_sequence=[COLOR_PRINCIPAL]
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # EVOLUCION
    st.subheader("Evolución") 
    evolucion = ( df_contabilidad .groupby(["FECHA", "TIPO"])["MONTO"] .sum() .unstack(fill_value=0) ) 
    st.line_chart(evolucion, color=["#5FA8A8", "#1F3C3D"])

