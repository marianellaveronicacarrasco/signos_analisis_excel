import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import unicodedata

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

creds = Credentials.from_service_account_file(
    "norse-lens-493218-f1-49efa0ee2185.json", scopes=scope
)

client = gspread.authorize(creds)

spreadsheet = client.open_by_key("1s3PvG-ob2P-KsgrdO4IyFxC8kVICHWNgiwOTiyF2BRQ")

spreadsheet_conta = client.open_by_key("1owTaWpPgb3LHMhgctAgDPCxheounko_FVeFArTN4T3o")

sheet_contabilidad = spreadsheet_conta.worksheet("INGRESOS Y GASTOS")
data_contabilidad = sheet_contabilidad.get_all_values()

df_contabilidad = pd.DataFrame(
    data_contabilidad[2:],   # datos
    columns=data_contabilidad[2]  # headers reales
)

sheet_general = spreadsheet.worksheet("GENERAL")
sheet_papeles = spreadsheet.worksheet("PAPELES")

data_general = sheet_general.get_all_records(expected_headers=sheet_general.row_values(1))
data_papeles = sheet_papeles.get_all_records(expected_headers=sheet_papeles.row_values(1))

df_general = pd.DataFrame(data_general)
df_papeles = pd.DataFrame(data_papeles)

# ---------------- NORMALIZAR PAPELES (CLAVE)
df_papeles.columns = df_papeles.columns.str.strip()

df_papeles = df_papeles.rename(columns={
    "EFECTIVO": "MONTO EN EFECTIVO",
    "DEBITO": "MONTO EN MERCADOPAGO"
})

if "MONTO EN SANTANDER" not in df_papeles.columns:
    df_papeles["MONTO EN SANTANDER"] = "0"

# ---------------- FUNCIONES

def limpiar_monto(col):
    return (
        col.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .replace("", "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

def limpiar_texto(texto):
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )

def arreglar_acentos(texto):
    try:
        return texto.encode('latin1').decode('utf-8')
    except:
        return texto

def limpiar_datos(df):
    # Columnas prolijas
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

    # Eliminar filas vacías
    df = df.dropna(how="all")

    # Limpiar strings
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Limpiar montos SOLO si existen
    if "MONTO_EN_EFECTIVO" in df.columns:
        df["MONTO_EN_EFECTIVO"] = limpiar_monto(df["MONTO_EN_EFECTIVO"])

    if "MONTO_EN_MERCADOPAGO" in df.columns:
        df["MONTO_EN_MERCADOPAGO"] = limpiar_monto(df["MONTO_EN_MERCADOPAGO"])

    if "MONTO_EN_SANTANDER" in df.columns:
        df["MONTO_EN_SANTANDER"] = limpiar_monto(df["MONTO_EN_SANTANDER"])

    # Filtrar nombres vacíos
    if "NOMBRE" in df.columns:
        df = df[df["NOMBRE"].notna()]
        df = df[df["NOMBRE"].str.strip() != ""]
        df["NOMBRE"] = df["NOMBRE"].str.title()

    # Fecha
    if "FECHA" in df.columns:
        df["FECHA"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")

    # Arreglar acentos
    df = df.map(lambda x: arreglar_acentos(x) if isinstance(x, str) else x)

    # Limpiar nombres de columnas
    df.columns = [limpiar_texto(col) for col in df.columns]
    df.columns = df.columns.str.upper().str.strip().str.replace(" ", "_")

    # Eliminar columnas vacías
    df = df.loc[:, df.columns != ""]
    df = df.drop_duplicates()

    return df
def limpiar_contabilidad(df):
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

    df = df.dropna(how="all")

    df["FECHA"] = df["FECHA"].astype(str).str.strip()
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%Y-%m", errors="coerce")

    df["TIPO"] = df["TIPO"].str.strip().str.upper()
    df["CONCEPTO"] = df["CONCEPTO"].str.strip()

    df["MONTO"] = limpiar_monto(df["MONTO"])

    return df
# ---------------- LIMPIEZA

df_general.columns = df_general.columns.str.strip()
df_general = limpiar_datos(df_general)

df_papeles = limpiar_datos(df_papeles)
df_contabilidad = limpiar_contabilidad(df_contabilidad)

# ---------------- VALIDACION

print(df_general.isnull().sum())
print(df_papeles.isnull().sum())

# ---------------- EXPORTAR

df_general.to_csv("data_general.csv", index=False, sep=";", encoding="utf-8-sig")
df_papeles.to_csv("data_papeles.csv", index=False, sep=";", encoding="utf-8-sig")
df_contabilidad.to_csv("data_contabilidad.csv", index=False, sep=";", encoding="utf-8-sig")

# ---------------- CALCULOS

# TOTAL
df_general["TOTAL_MONTO"] = (
    df_general["MONTO_EN_EFECTIVO"] +
    df_general["MONTO_EN_MERCADOPAGO"] +
    df_general["MONTO_EN_SANTANDER"]
)

df_papeles["TOTAL_MONTO"] = (
    df_papeles["MONTO_EN_EFECTIVO"] +
    df_papeles["MONTO_EN_MERCADOPAGO"] +
    df_papeles["MONTO_EN_SANTANDER"]
)

# INGRESOS POR FECHA
ingresos_fecha_general = df_general.groupby("FECHA")["TOTAL_MONTO"].sum().reset_index()
ingresos_fecha_papeles = df_papeles.groupby("FECHA")["TOTAL_MONTO"].sum().reset_index()

# METODOS
metodos_general = df_general[[
    "MONTO_EN_EFECTIVO",
    "MONTO_EN_MERCADOPAGO",
    "MONTO_EN_SANTANDER"
]].sum()

metodos_papeles = df_papeles[[
    "MONTO_EN_EFECTIVO",
    "MONTO_EN_MERCADOPAGO",
    "MONTO_EN_SANTANDER"
]].sum()

# EXTRA
ecg = df_general["ECG"].value_counts() if "ECG" in df_general.columns else None


#------------------------------

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
    # UNIR 
print("GENERAL:")
print(ingresos_general.head())

print("PAPELES:")
print(ingresos_papeles.head())

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
    
print("ESTO LE TENES QUE MANDAR A CHAT GPT")
print("------------------------------")
df_lineas.head()
df_lineas.index

print("Extracción completada correctamente")

