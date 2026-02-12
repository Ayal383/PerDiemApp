import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO

# =====================================
# CONFIGURACIÓN DE PÁGINA
# =====================================

st.set_page_config(page_title="Expences Validator", layout="wide")

img = Image.open("Logo COR3.png")
img_resized = img.resize((200, 100))  # width=300px, height=200px

st.image(img_resized)

st.title("Expences Validator")
st.markdown("---")

# =====================================
# CARGAR ARCHIVOS 
# =====================================

@st.cache_data
def cargar_datos():
    mileage_df = pd.read_excel("Mileaje rate.xlsx")
    perdiem_df = pd.read_excel("OCONUS and OVERSEAS Per Diem Rates Query Results.xlsx")

    # Eliminar columnas duplicadas
    mileage_df = mileage_df.loc[:, ~mileage_df.columns.duplicated()]
    perdiem_df = perdiem_df.loc[:, ~perdiem_df.columns.duplicated()]

    # Convertir fechas
    mileage_df["Effective Date"] = pd.to_datetime(
        mileage_df["Effective Date"], errors="coerce"
    )

    perdiem_df["Effective Date"] = pd.to_datetime(
        perdiem_df["Effective Date"], errors="coerce"
    )

    return mileage_df, perdiem_df


mileage_df, perdiem_df = cargar_datos()

# =====================================
# MENÚ LATERAL
# =====================================

opcion = st.sidebar.selectbox(
    "Seleccione cálculo:",
    ["Millaje", "Per Diem"]
)

# =====================================
# MILLAGE
# =====================================

if opcion == "Millaje":

    st.header("Cálculo de Millaje")

    año = st.selectbox("Año del viaje", [2023,2024,2025,2026])

    transporte = st.selectbox(
        "Medio de transporte",
        ["Car", "Motorcycle", "Airplane", "MALT", "Other"]
    )

    millas = st.number_input("Millas recorridas", min_value=0)

    if st.button("Calcular Millaje"):

        tarifas_validas = mileage_df[
            mileage_df["Effective Date"].dt.year <= año
        ].sort_values("Effective Date", ascending=False)

        if tarifas_validas.empty:
            st.error("No hay tarifas disponibles para ese año.")
        else:
            tarifa = tarifas_validas.iloc[0][transporte]
            total = millas * tarifa

            st.success("Cálculo completado ✅")

            st.metric("Tarifa aplicada", f"${tarifa}")
            st.metric("Total a pagar", f"${total:,.2f}")

# =====================================
# PER DIEM
# =====================================

elif opcion == "Per Diem":

    st.header("Cálculo de Per Diem")

    fecha = st.date_input("Fecha del viaje")
    mes_dia = fecha.strftime("%m/%d")

    localidades = sorted(perdiem_df["Locality"].dropna().unique())
    localidad = st.selectbox("Seleccione localidad", localidades)

    dias = st.number_input("Cantidad de días", min_value=1, step=1)

    numtraveldays = 0
    aplicar_travel = st.checkbox(
        "Aplicar 75% en primer y último día (Travel Days)", value=True)
    
    if aplicar_travel == True:
    
        numtraveldays=st.number_input("Cantidad de dias de travel")

    # hacer una nueva condicion para poder ingrasar inputs de cuantos travel day son 
    

    if st.button("Calcular Per Diem"):

        df_local = perdiem_df[perdiem_df["Locality"] == localidad]

        fila_valida = None

        for _, row in df_local.iterrows():
            temporada = row["Seasons (Beg-End)"]

            if pd.isna(temporada):
                continue

            inicio, fin = temporada.split(" - ")

            # Manejo temporada normal
            if inicio <= fin:
                if inicio <= mes_dia <= fin:
                    fila_valida = row
                    break
            else:
                # Temporada que cruza año (ej: 10/01 - 03/31)
                if mes_dia >= inicio or mes_dia <= fin:
                    fila_valida = row
                    break

        if fila_valida is None:
            st.error("No se encontró temporada válida.")
        else:
            lodging = fila_valida["Maximum Lodging"]
            meals = fila_valida["Local Meals"]
            incidental = fila_valida["Local Incidental"]

            meals_diario = meals + incidental

            # ===== Travel Day Logic =====
            if aplicar_travel:
                if dias == 1:
                    total_meals = meals_diario * 0.75
                else:
                    dias_normales = dias - 2
                    total_meals = (meals_diario * 0.75 * 2) + \
                                  (meals_diario * dias_normales)
            else:
                total_meals = meals_diario * dias

            
            
            TravelDay = meals_diario * .75
            TotalTravelDay = (numtraveldays * TravelDay)
            Total_Meals_Incidental = ((dias - numtraveldays) * meals_diario)
            total_lodging = lodging * dias
            total_perdiem = total_lodging + Total_Meals_Incidental + TotalTravelDay


            st.success("Cálculo completado ✅")
            no_se = ""
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Lodging diario", f"${lodging:,.2f}")
            col2.metric("Meals + Incidental diario", f"${meals_diario:,.2f}")
            col3.metric("Max Travel Day", f"${TravelDay:,.2f}")
            col4.metric("Total Per Diem", f"${total_perdiem:,.2f}")
            
            col5, col6, col7, col8 = st.columns(4)
            
            col5.metric("Total Lodging", f"${total_lodging:,.2f}")
            col6.metric("Total Meals + Incidental", f"${Total_Meals_Incidental:,.2f}")
            col7.metric("Total Travel Day", f"${TotalTravelDay:,.2f}")
            col8.metric("", f"{no_se:}")
            
            

            st.info(f"Temporada aplicada: {fila_valida['Seasons (Beg-End)']}")



