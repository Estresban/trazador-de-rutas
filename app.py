%%writefile app.py
import streamlit as st
import requests
import math

st.set_page_config(page_title="Gestor de Rutas", layout="wide")

st.title("🧭 Gestor de Rutas")

def geocode_direccion(direccion):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": direccion, "format": "json"}
    headers = {"User-Agent": "GestorRutasApp/1.0"}
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None

def calcular_ruta_osrm(puntos):
    coords = ";".join(f"{lon},{lat}" for lat, lon in puntos)
    url = f"http://router.project-osrm.org/trip/v1/driving/{coords}?source=first&destination=last&roundtrip=false"
    r = requests.get(url)
    data = r.json()
    if "trips" in data:
        distancia = data["trips"][0]["distance"] / 1000
        tiempo = data["trips"][0]["duration"] / 60
        return distancia, tiempo
    return None, None

origen = st.text_input("Origen")
destino = st.text_input("Destino")

if st.button("Calcular Ruta"):
    if not origen or not destino:
        st.error("Introduce origen y destino")
    else:
        with st.spinner("Calculando..."):
            origen_coords = geocode_direccion(origen)
            destino_coords = geocode_direccion(destino)
            distancia, tiempo = calcular_ruta_osrm([origen_coords, destino_coords])

            if distancia:
                st.success(f"Distancia: {distancia:.2f} km")
                st.success(f"Tiempo estimado: {tiempo:.0f} min")
