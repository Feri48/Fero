import streamlit as st
import math


# Sunstone gyári akku kisülési adatok 1,6V/cell / (W/akku) 5, 10, 15, 30, 45, 60 percre
BATTERY_DATA_SUNSTONE = {
    "SPT12-9": [338.82, 227.04, 174.3, 102.06, 78.72, 62.64],
    "SPT12-12": [457.56, 306.6, 235.38, 142.2, 106.32, 84.54],
    "SPT12-18": [685.8, 459.66, 352.86, 213.18, 159.36, 126.78],
    "ML12-26": [873, 587.4, 490.2, 295.8, 223.8, 191.28],
    "ML12-38": [1352.22, 914.58, 751.2, 453.9, 342.66, 278.22],
    "ML12-55": [1902.6, 1293, 1062, 642, 487.2, 398.4],
    "ML12-70": [2491.2, 1684.8, 1383.6, 836.4, 631.2, 512.4],
    "ML12-90": [3168.6, 2143.2, 1760.4, 1063.8, 807.6, 655.2],
    "ML12-110": [3831, 2665.2, 2188.8, 1393.2, 989.4, 796.2],
}
BATTERY_LIST_SUNSTONE = list(BATTERY_DATA_SUNSTONE.keys())
TIME_OPTIONS_SUNSTONE = [5, 10, 15, 30, 45, 60]

# Yuasa battery discharge data 1,6V/cell / ((W/akku) 5, 10, 15, 20, 30, 40, 50, 60 minutes
BATTERY_DATA_YUASA = {
   "SWL280 (7.8Ah)": (444, 280, 175, 125, 102, 85, 75, 65),  # 140W 15perc től becsült értékek
    "SWL750 (25Ah)": [1176, 768, 630, 528, 396, 312, 252, 228],
    "SWL1100 (40.6Ah)": [1710, 1200, 960, 774, 564, 468, 402, 354],
    "SWL1850 (74Ah)": [2718, 1914, 1524, 1260, 918, 750, 654, 576],
    "SWL2300 (80Ah)": [3138, 2298, 1710, 1410, 1074, 852, 696, 600],
    "SWL2500 (93.6Ah)": [3258, 2526, 1938, 1596, 1260, 1014, 876, 750],
    "SWL3300 (110.2Ah)": [4464, 3204, 2520, 2088, 1590, 1284, 1080, 936],
}

BATTERY_LIST_YUASA = list(BATTERY_DATA_YUASA.keys())
TIME_OPTIONS_YUASA = [5, 10, 15, 20, 30, 40, 50, 60]

# ez a képlet jó lesz a teljesítmény interpolálására
def interpolate_power(battery_type, minutes):  # Akkumulátor típus és idő (perc)
    if minutes in time_options:                                  # pontos egyezés
        return battery_data[battery_type][time_options.index(minutes)] # adott időponthoz tartozó teljesítmény
    elif minutes < time_options[0]:                              # 5 percnél kisebb
        return battery_data[battery_type][0]                     # 5 perces érték
    elif minutes > time_options[-1]:                             # 60 percnél nagyobb
        return battery_data[battery_type][-1]                    # 60 perces érték
    for i in range(len(time_options) - 1):                       # interpoláció a két legközelebbi időpont között
        t1, t2 = time_options[i], time_options[i + 1]            # időpontok
        if t1 < minutes < t2:                                    # ha a megadott időpont között van
            p1 = battery_data[battery_type][i]                   # teljesítmény értékek
            p2 = battery_data[battery_type][i + 1]               # teljesítmény értékek
            return p1 + (p2 - p1) * ((minutes - t1) / (t2 - t1)) # lineáris interpoláció
    return None


def calculate_energy_based_backup_time(load_kw, battery_type, battery_count, selected_time):
    power_per_batt = interpolate_power(battery_type, selected_time)
    time_hours = selected_time / 60
    energy_per_batt = power_per_batt * time_hours
    total_energy = energy_per_batt * battery_count * stringcount * efficiency
    backup_time_minutes = (total_energy / (load_kw * 1000)) * 60
    return round(backup_time_minutes, 2), round(power_per_batt, 2), round(energy_per_batt, 2)


def calculate_required_battery_count(load_kw, battery_type, selected_time, target_minutes):
    power_per_batt = interpolate_power(battery_type, selected_time)
    energy_per_batt = power_per_batt * (selected_time / 60)
    total_energy_required = load_kw * 1000 * target_minutes / 60 / efficiency
    batteries_needed = total_energy_required / energy_per_batt
    return math.ceil(batteries_needed)  # felfelé kerekit szemben az : int(batteries_needed)   #+ 1


def suggest_better_battery_type(load_kw, selected_time, target_minutes, stringcount):
    total_energy_required = load_kw * 1000 * target_minutes / 60 / efficiency
    closest_type = None
    min_diff = float("inf")

    for batt_type, power_list in battery_data.items():
        power = interpolate_power(batt_type, selected_time)
        energy_per_batt = power * (selected_time / 60)
        total_energy = energy_per_batt * stringcount  # 1 akkumulátor-string

        diff = abs(total_energy_required - total_energy)
        if diff < min_diff:
            min_diff = diff
            closest_type = batt_type

    return closest_type


# Streamlit alkalmazás kezdete
st.set_page_config(page_title="UPS Akkumlátor Méretező", layout="centered")
st.markdown(""" <style> .block-container {padding-top: 3rem;</style> """, unsafe_allow_html=True)

# Bal felső sarok: logó + felirat
logo_col, text_col = st.columns([6, 1])
with logo_col:
    st.image("ccsi_logo.svg", width=120)  # Cég logója (ccsi_logo.svg) 120px széles a file gyökerében legyen elérhető
with text_col:
    st.markdown(":orange[Ferosoft™]", unsafe_allow_html=True)  # Jobb felső sarok: Ferosoft felirat
# with text_col:
#    st.markdown("<h2 style='margin-bottom:0px;'>Ferosoft <sup style='font-size:0.1em;'>™</sup></h2>", unsafe_allow_html=True)

#stringlist = [1, 2, 3, 4]


st.title("🔋 UPS Akkumlátor Méretező")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ups_power_kva = st.number_input("UPS névleges [kVA]", min_value=10.0, max_value=250.0, value=10.0, step=1.0,
                                    help="Látszólagos teljesítmény kVA-ban (max:250kVA).")
    backup_time_min = st.number_input("Áthidalási idő [perc]", min_value=5, max_value=60, value=10,
                                      help="Elvárt áthidalási idő 5-60 perc.")
    st.subheader("📊 Eredmények:")

with col3:
    manufacturer = st.selectbox("Akkumulátor gyártó:", ["Sunstone", "Yuasa"], index = 0, help="Válassz akku gyártót!")
    if manufacturer == "Sunstone":
        initial_battery_type = st.selectbox("Akkumlátor típus:", BATTERY_LIST_SUNSTONE, index=0, help="Akku kapacitások /Ah. (1,6V/cell)")
        battery_data = BATTERY_DATA_SUNSTONE
        time_options = TIME_OPTIONS_SUNSTONE

    else:
        initial_battery_type = st.selectbox("Akkumlátor típus:", BATTERY_LIST_YUASA, index=0, help="Akku kapacitások /Ah. (1,6V/cell)")
        battery_data = BATTERY_DATA_YUASA
        time_options = TIME_OPTIONS_YUASA

    efficiency = st.number_input("DC hatásfok %", min_value=0.91, max_value=0.96, value=0.95, step=0.01,
                                 help="Akkuk DC hatásfoka 0,92-0,96 között.")

with col2:
    load_kw = st.number_input("Terhelés [kW]", min_value=5.0, max_value=250.0, value=9.0,step=1.0,
                              help="A valós terhelés kW-ban (max:250kW).")
    power_factor = st.number_input("Teljesítménytényező (PF)", min_value=0.89, max_value=1.00, value=1.00, step=0.01,
                                   help="Teljesítménytényező (AC) 0,90-1,00 között.")

with col4:
    stringcount = st.selectbox("Stringek", [1, 2, 3, 4], index = 0, help="A stringek száma 1-4 között.")
    
    battery_count = st.slider("Akkumlátorok száma", min_value=32, max_value=44, value=40,
                              help="Akkuk száma 32-44 között(INVT).")    
    # if  power_factor >= 0.95 and
    if battery_count <= 36:
        st.toast("Figyelem: 36db akkunál kevesebb nem lehet(SOCOMEC)! / csökkenhet a DC hatásfok! <95%.",
                 icon="⚠️")  # st.error("⚠️ A hatásfok az akkuk  száma miatt 95%!")

if load_kw > ups_power_kva * power_factor:
    st.error("⚠️ A terhelés nem lehet nagyobb, mint az UPS valós teljesítménye.")

else:
    recommended_battery_count = calculate_required_battery_count(load_kw, initial_battery_type, backup_time_min,
                                                                 backup_time_min)
    actual_time, power_per_batt, energy_per_batt = calculate_energy_based_backup_time(
        load_kw, initial_battery_type, battery_count, backup_time_min)

    # st.markdown(f"**✅ Valós áthidalási idő :** :red[{actual_time:.2f}] perc :orange[{actual_time % 60:.2f}]mp (String:{stringcount} x{battery_count}db Össz:{stringcount*battery_count})")
    minutes = int(actual_time)
    seconds = int(round((actual_time - minutes) * 60))
    st.markdown(
        f"**✅ Valós áthidalási idő : :red[{minutes}] perc :red[{seconds}] mp (String:{stringcount}x{battery_count}db össz:{stringcount * battery_count}db**)")
    # Az időtartamot percben adjuk meg, de a számításokhoz másodpercben kell
    st.markdown(f"**🔋 Ajánlott akkumlátor darabszám a {backup_time_min} perchez: {recommended_battery_count} db**")
    current_total_batt = battery_count * stringcount
    if recommended_battery_count > current_total_batt + 5:
        st.markdown(f"Ajánlott méret: **:red[Válassz nagyobbat vagy több stringet!]⬆️**")
        suggested_type = suggest_better_battery_type(load_kw, backup_time_min, backup_time_min, current_total_batt)
        st.markdown(f"🔍 Próbáld ki ezt az akkutípust: **:orange[{suggested_type}]**")
    elif recommended_battery_count < current_total_batt - 5:
        st.markdown(f"Ajánlott méret: **:red[Válassz kisebbet vagy kevesebb stringet!]⬇️**")
        suggested_type = suggest_better_battery_type(load_kw, backup_time_min, backup_time_min, current_total_batt)
        st.markdown(f"🔍 Próbáld ki ezt az akkutípust: **:orange[{suggested_type}]**")
    else:
        st.markdown(f"**🔋 Ajánlott akkumlátor típus: {initial_battery_type}** 👍")

    st.markdown(f"**Leadott teljesítmény veszteséggel (eff = {efficiency:.2f}):** {load_kw / efficiency:.2f} kW")
    st.markdown(
        f"**Akkumlátor teljesítmény 1 db-ra ({backup_time_min} percnél):** {power_per_batt:.2f} W - {power_per_batt / 6:.2f} W/cella ")
    st.markdown(f"**Energia 1 db akkuból {backup_time_min} perc alatt:** {energy_per_batt:.2f} Wh")

    #st.markdown(f"PF={power_factor:.2f} cosfi")
    # st.markdown(f"**UPS névleges teljesítménye:** {ups_power_kva * power_factor:.2f} kW")
    # st.markdown("_Képlet: idő = (akkuk összes Wh × hatásfok / terhelés) × 60_")
    # st.markdown(''':red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
    #            :gray[pretty] :rainbow[colors] and :blue-background[highlight] text.''') 

st.markdown(
    """
    <div style="position:fixed; left:0; bottom:0; width:100%; background: #f8e71c; color:#222; text-align:center; padding:8px 0; z-index:1000;">
    <marquee behavior="scroll" direction="left" scrollamount="6">
        🔋 UPS méretező | Készítette: Ferosoft ™®| ©2025 V1.5.0| Minden jog fenntartva !💡
    </marquee>
    </div>
    """,
    unsafe_allow_html=True
)

# 2025.06.05.  Ferosoft™® UPS méretező V1.5.1   Bővitett Yuasa akku adatokkal
# # 2025-07-07 10:00-ig
# python -m streamlit run UPS_szamolo_ver1_5_1.py
# http://<szerver_neve>:8501
