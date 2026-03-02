%%writefile app.py
import streamlit as st
import requests
import math
import webbrowser

st.set_page_config(page_title="Gestor de Rutas", layout="wide")

st.title("🧭 Gestor de Rutas (Versión Web)")

# -------------------------------
# FUNCIONES
# -------------------------------

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

def distancia_euclidiana(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

# -------------------------------
# INTERFAZ
# -------------------------------

origen = st.text_input("Origen")
destino = st.text_input("Destino")

num_paradas = st.number_input("Número de paradas intermedias", 0, 10, 0)

paradas = []
for i in range(num_paradas):
    p = st.text_input(f"Parada {i+1}")
    if p:
        paradas.append(p)

start_nearest = st.checkbox("Empezar por la parada más cercana al origen")

if st.button("🚀 Calcular Ruta"):
    if not origen or not destino:
        st.error("Debes introducir origen y destino")
    else:
        with st.spinner("Calculando ruta..."):
            origen_coords = geocode_direccion(origen)
            destino_coords = geocode_direccion(destino)

            if not origen_coords or not destino_coords:
                st.error("Error geocodificando origen o destino")
            else:
                paradas_coords = []
                for p in paradas:
                    coords = geocode_direccion(p)
                    if not coords:
                        st.error(f"No se pudo geocodificar {p}")
                        st.stop()
                    paradas_coords.append(coords)

                # Parada más cercana
                if start_nearest and paradas_coords:
                    distancias = [distancia_euclidiana(origen_coords, pc) for pc in paradas_coords]
                    idx = distancias.index(min(distancias))
                    paradas_coords = [paradas_coords[idx]] + paradas_coords[:idx] + paradas_coords[idx+1:]

                puntos = [origen_coords] + paradas_coords + [destino_coords]
                distancia, tiempo = calcular_ruta_osrm(puntos)

                if distancia:
                    st.success("Ruta calculada correctamente")
                    st.write(f"**Distancia total:** {distancia:.2f} km")
                    st.write(f"**Tiempo estimado:** {tiempo:.0f} min")

                    # Generar link Google Maps
                    url = f"https://www.google.com/maps/dir/{origen}/"
                    if paradas:
                        url += "/".join(paradas) + "/"
                    url += destino

                    st.markdown(f"[🌍 Abrir en Google Maps]({url})")
                else:
                    st.error("No se pudo calcular la ruta")

