import streamlit as st
#import pandas as pd

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

BATTERY_LIST = list(BATTERY_DATA.keys())
time_options = [5, 10, 15, 30, 45, 60]
EFFICIENCY = 0.95

def interpolate_power(battery_type, minutes):                                      #ez a képlet jó lesz a teljesítmény interpolálására
    if minutes in time_options:
        return BATTERY_DATA[battery_type][time_options.index(minutes)]
    elif minutes < time_options[0]:
        return BATTERY_DATA[battery_type][0]
    elif minutes > time_options[-1]:
        return BATTERY_DATA[battery_type][-1]
    for i in range(len(time_options) - 1):
        t1, t2 = time_options[i], time_options[i + 1]
        if t1 < minutes < t2:
            p1 = BATTERY_DATA[battery_type][i]
            p2 = BATTERY_DATA[battery_type][i + 1]
            return p1 + (p2 - p1) * ((minutes - t1) / (t2 - t1))
    return None

def calculate_energy_based_backup_time(load_kw, battery_type, battery_count, selected_time):
    power_per_batt = interpolate_power(battery_type, selected_time)
    time_hours = selected_time / 60
    energy_per_batt = power_per_batt * time_hours
    total_energy = energy_per_batt * battery_count * EFFICIENCY
    backup_time_minutes = (total_energy / (load_kw * 1000)) * 60
    return round(backup_time_minutes, 2), round(power_per_batt, 2), round(energy_per_batt, 2)

def calculate_required_battery_count(load_kw, battery_type, selected_time, target_minutes):
    power_per_batt = interpolate_power(battery_type, selected_time)
    energy_per_batt = power_per_batt * (selected_time / 60)
    total_energy_required = load_kw * 1000 * target_minutes / 60 / EFFICIENCY
    batteries_needed = total_energy_required / energy_per_batt
    return int(batteries_needed) + 1


# Streamlit alkalmazás kezdete
st.set_page_config(page_title="UPS Akkumlátor Méretező", layout="centered")
st.title("🔋 UPS Akkumlátor Méretező")

col1, col2 = st.columns(2)

with col1:
    initial_battery_type = st.selectbox("Akkumlátor típus:", BATTERY_LIST)
    backup_time_min = st.number_input("Áthidalási idő [perc]", min_value=5, max_value=60, value=10)
    battery_count = st.slider("Akkumlátorok száma", min_value=1, max_value=40, value=40)

with col2:
    ups_power_kva = st.number_input("UPS névleges teljesítmény [kVA]", min_value=10.0, max_value=60.0, value=10.0)
    power_factor = st.number_input("Power Factor", min_value=0.9, max_value=1.0, value=0.9)
    load_kw = st.number_input("Terhelés [kW]", min_value=0.0, value=9.0)

if st.button("Számítás"):
    if load_kw > ups_power_kva * power_factor:
        st.error("A terhelés nem lehet nagyobb, mint az UPS valós teljesítménye.")
    else:
        recommended_battery_count = calculate_required_battery_count(load_kw, initial_battery_type, backup_time_min, backup_time_min)
        actual_time, power_per_batt, energy_per_batt = calculate_energy_based_backup_time(
            load_kw, initial_battery_type, battery_count, backup_time_min)
        
        st.subheader("📊 Eredmények")
        st.markdown(f"**✅ Valós áthidalási idő :** :red[{actual_time:.2f}] perc")
        st.markdown(f"**🔋 Ajánlott akkumlátor darabszám a {backup_time_min} perchez: {recommended_battery_count} db**")
        
        if recommended_battery_count > battery_count + 5:
            st.markdown(f"🔋 Ajánlott akkumlátor típus: **:red[Válassz nagyobbat !]**")
        elif recommended_battery_count < battery_count - 5:
            st.markdown(f"🔋 Ajánlott akkumlátor típus: **:red[Válassz kisebbet !]**")
        else:
            st.markdown(f"**🔋 Ajánlott akkumlátor típus:** {initial_battery_type}")
       
        st.markdown(f"**UPS névleges teljesítménye:** {ups_power_kva * power_factor:.2f} kW")
        st.markdown(f"**Leadott teljesítmény veszteséggel (eff = 0.95):** {load_kw / EFFICIENCY:.2f} kW")
        st.markdown(f"**Akkumlátor teljesítmény 1 db-ra ({backup_time_min} percnél):** {power_per_batt:.2f} W")
        st.markdown(f"**Energia 1 db akkuból {backup_time_min} perc alatt:** {energy_per_batt:.2f} Wh")
        st.markdown("_Képlet: idő = (akkuk összes Wh × hatásfok / terhelés) × 60_")
        #st.markdown(''':red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
        #            :gray[pretty] :rainbow[colors] and :blue-background[highlight] text.''') 
   
st.markdown(
    """
    <div style="position:fixed; left:0; bottom:0; width:100%; background: #f8e71c; color:#222; text-align:center; padding:8px 0; z-index:1000;">
    <marquee behavior="scroll" direction="left" scrollamount="6">
        🔋 UPS méretező | Készítette: Ferosoft | 2025 | Minden jog fenntartva 💡
    </marquee>
    </div>
    """,
    unsafe_allow_html=True
)
#  müködőképes verzió: 1.4.2
# 2025.05.25
