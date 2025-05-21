import streamlit as st  # Streamlit: egyszerű webes felületet készíthetsz vele Pythonból
import pandas as pd     # Pandas: táblázatos adatokhoz (itt nem feltétlenül szükséges)
# import pdb              # debugoláshoz   #pdb.set_trace()   #nyomkövetés

# Akkumulátor teljesítmény táblázat (Watt) különböző időtartamokra, 1 db akkura
# Minden típushoz 6 érték tartozik: 5, 10, 15, 30, 45, 60 perc
BATTERY_DATA = {
    "Sunstone SPT12-9":   [338.82, 227.04, 174.3, 102.06, 78.72, 62.64],
    "Sunstone SPT12-12":  [457.56, 306.6, 235.38, 142.2, 106.32, 84.54],
    "Sunstone SPT12-18":  [685.8, 459.66, 352.86, 213.18, 159.36, 126.78],
    "Sunstone ML12-26":   [873, 587.4, 490.2, 295.8, 223.8, 191.28],
    "Sunstone ML12-38":   [1352.22, 914.58, 751.2, 453.9, 342.66, 278.22],
    "Sunstone ML12-55":   [1902.6, 1293, 1062, 642, 487.2, 398.4],
    "Sunstone ML12-70":   [2491.2, 1684.8, 1383.6, 836.4, 631.2, 512.4],
    "Sunstone ML12-90":   [3168.6, 2143.2, 1760.4, 1063.8, 807.6, 655.2],
    "Sunstone ML12-110":  [3831, 2665.2, 2188.8, 1393.2, 989.4, 796.2],
}

time_options = [5, 10, 15, 30, 45, 60]  # Lehetséges áthidalási idők (percben)
EFFICIENCY = 0.95  # Hatásfok (veszteségek miatt nem 100%)

def get_power_for_time(battery_type, minutes):
    """
    Visszaadja az adott akku típushoz és időtartamhoz tartozó teljesítményt (Watt).
    Ha nem létezik ilyen időtartam, None-t ad vissza.
    """
    if minutes not in time_options:
        return None
    index = time_options.index(minutes)  # Megkeressük, hányadik az adott időtartam a listában
    return BATTERY_DATA[battery_type][index]  # Kivesszük a megfelelő teljesítményt

    """
     def get_previous_power(battery_type, minutes):
    
    #Előző időtartamhoz tartozó teljesítmény lekérdezése.
    #Ha az első elem, ugyanazt adja vissza.
    
    index = time_options.index(minutes)
    if index == 0:
        return BATTERY_DATA[battery_type][0]
       
    return BATTERY_DATA[battery_type][index - 1]
    """
def get_previous_power_and_time(battery_type, minutes):
    """
    Előző időtartamhoz tartozó teljesítmény ÉS az idő lekérdezése.
    Ha az első elem, ugyanazt adja vissza.
    """
    index = time_options.index(minutes)
    if index == 0:
        return time_options[0], BATTERY_DATA[battery_type][0]
    return time_options[index - 1], BATTERY_DATA[battery_type][index - 1]

def calculate_energy_based_backup_time(load_kw, battery_type, battery_count, selected_time):
    """
    Kiszámítja, hogy adott terhelés, akku típus, darabszám és időtartam mellett
    mennyi lesz a valós áthidalási idő, 1 akkuból mennyi energia vehető ki, stb.
    Visszatérési értékek: (áthidalási idő percben, 1 akku teljesítménye, 1 akku energiatartalma Wh-ban)
    """
    index = time_options.index(selected_time)
    power_per_batt = BATTERY_DATA[battery_type][index]  # 1 db akku adott idejű teljesítménye (W)
    time_hours = selected_time / 60                     # perc -> óra
    energy_per_batt = power_per_batt * time_hours       # 1 akku energiatartalma Wh-ban
    total_energy = energy_per_batt * battery_count * EFFICIENCY  # összes kihasználható energia (Wh), hatásfokkal
    backup_time_minutes = (total_energy / (load_kw * 1000)) * 60 # Mennyi ideig bírja a rendszer a terhelést
    return round(backup_time_minutes, 2), round(power_per_batt, 2), round(energy_per_batt, 2)

def calculate_required_battery_count(load_kw, battery_type, selected_time, target_minutes):
    """
    Kiszámítja, hogy adott terhelés, akku típus, időtartam és cél áthidalási idő mellett
    hány darab akkura van szükség.
    """
    index = time_options.index(selected_time)
    power_per_batt = BATTERY_DATA[battery_type][index]  # 1 akku teljesítménye ennél az időnél
    energy_per_batt = power_per_batt * (selected_time / 60)  # 1 akku energiatartalma
    total_energy_required = load_kw * 1000 * target_minutes / 60 / EFFICIENCY  # Szükséges összes energia (Wh)
    batteries_needed = total_energy_required / energy_per_batt   # Szükséges darabszám (tört szám lehet)
    return int(batteries_needed) + 1  # Felkerekítjük egész fölé (mindig több legyen mint kevesebb)


# Streamlit oldal beállítása
st.set_page_config(page_title="UPS Akkumlátor Méretező", layout="centered")  # Oldal címe és elrendezése
st.title("🔋 UPS Akkumulátor Méretező")  # Főcím

        
col1, col2 = st.columns(2)  # Két oszlopos elrendezés a beviteli mezőknek

with col1:
    # Bal oszlop: akku paraméterek
    battery_type = st.selectbox("Akkumlátor típus:", list(BATTERY_DATA.keys()))  # Akku típus választó
    backup_time_min = st.selectbox("Áthidalási idő [perc]", time_options,1)          # Időtartam választó
    battery_count = st.slider("Akkumlátorok száma", min_value=1, max_value=40, value=40)  # Akku darabszám csúszka

with col2:
    # Jobb oszlop: UPS és terhelés paraméterei
    ups_power_kva = st.number_input("UPS névleges teljesítmény [kVA]", min_value=10.0, max_value=60.0, value=10.0)
    power_factor = st.number_input("Power Factor", min_value=0.8, max_value=1.0, value=0.9)
    load_kw = st.number_input("Terhelés [kW]", min_value=0.0, value=9.0)
  
# Számítás gomb megnyomásakor
if st.button("Számítás"):

    # Ellenőrizzük, hogy a terhelés nem nagyobb, mint az UPS valódi teljesítménye
    if load_kw > ups_power_kva * power_factor:
        st.error("A terhelés nem lehet nagyobb, mint az UPS valós teljesítménye.")
    else:
        # Valós áthidalási idő és egyéb adatok számítása
        actual_time, power_per_batt, energy_per_batt = calculate_energy_based_backup_time(
            load_kw, battery_type, battery_count, backup_time_min)
        previous_timer, previous_power  = get_previous_power_and_time(battery_type, backup_time_min)
        recommended_battery_count = calculate_required_battery_count(load_kw, battery_type, backup_time_min, backup_time_min)

        # Eredmények megjelenítése a felületen
        st.subheader("📊 Eredmények")
        st.markdown(f"**UPS névleges teljesítménye:** {ups_power_kva * power_factor:.2f} kW")
        st.markdown(f"**Leadott teljesítmény veszteséggel (eff = 0.95):** {load_kw / EFFICIENCY:.2f} kW")
        st.markdown(f"**✅ Valós áthidalási idő :** {actual_time:.2f} perc")
        st.markdown(f"**🔋 Ajánlott akkumlátor darabszám a {backup_time_min} perchez:** {recommended_battery_count} db")
        st.markdown(f"**Akkumlátor teljesítmény 1 db-ra ({backup_time_min} percnél):** {power_per_batt:.2f} W")
        st.markdown(f"**Akkumlátor teljesítmény 1 db-ra ( {previous_timer} percnél):** {previous_power:.2f} W")
        st.markdown(f"**Energia 1 db akkuból {backup_time_min} perc alatt:** {energy_per_batt:.2f} Wh")
        st.markdown("_Képlet: idő = (akkuk összes Wh × hatásfok / terhelés) × 60_")
        
        # Marquee (futó szöveg) az oldal alján
st.markdown(
         """
         <div style="position:fixed; left:0; bottom:0; width:100%; background: #f8e71c; color:#222; text-align:center; padding:8px 0; z-index:1000;">
        <marquee behavior="scroll" direction="left" scrollamount="6">
            🔋 UPS méretező | Készítette: Ferosoft | 2025 | Minden jog fenntartva 💡
         </marquee>
        </div>
         """,
unsafe_allow_html=True)
