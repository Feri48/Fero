import streamlit as st
import math
import plotly.graph_objects as go
import pandas as pd

# Sunstone gyári akku kisülési adatok 1,6V/cell / (W/akku) 5, 10, 15, 30, 45, 60, 120, 180 percre
BATTERY_DATA_SUNSTONE = {
    "SPT12-9R": [338.82, 227.04, 174.3, 105.3, 78.72, 63.9, 36.96, 27.6],  # raktári
    "SPT12-12": [457.56, 306.6, 235.38, 142.2, 106.32, 84.54, 48.9, 36.54],
    "SPT12-18": [685.8, 459.66, 352.86, 213.18, 159.36, 126.78, 73.32, 54.72],
    "ML12-26R": [873, 587.4, 490.2, 295.8, 223.8, 191.28, 109.5, 81.72],  # raktári
    "ML12-38": [1352.22, 914.58, 751.2, 453.9, 342.66, 278.22, 159.3, 118.92],
    "ML12-40R": [1402.8, 982.2, 807, 487.2, 351.6, 284.1, 171.12, 127.74],  # raktári
    "ML12-55R": [1902.6, 1293, 1062, 642, 487.2, 398.4, 229.2, 89.4],  # raktári
    "ML12-70R": [2491.2, 1684.8, 1383.6, 836.4, 631.2, 512.4, 293.4, 219],  # raktári
    "ML12-90R": [3168.6, 2175.6, 1786.8, 1080, 819.6, 655.4, 382.8, 285.6],  # raktári
    "ML12-100": [3349.8, 2401.2, 1972.2, 1191.6, 904.2, 741.6, 429, 320.4],
    "ML12-110": [3831, 2665.2, 2188.8, 1393.2, 989.4, 796.2, 468.6, 333.6],
    # ehelyett inkább VG12-100, úgy raktári W/C?
}
BATTERY_LIST_SUNSTONE = list(BATTERY_DATA_SUNSTONE.keys())
TIME_OPTIONS_SUNSTONE = [5, 10, 15, 30, 45, 60, 120, 180]

# Yuasa battery discharge data 1,6V/cell / ((W/akku) 5, 10, 15, 20, 30, 40, 50, 60 minutes
BATTERY_DATA_YUASA = {
    "SWL280 (7.8Ah)": [450, 280, 216, 179, 137, 113, 98, 87],  # 15perc től becsült értékek (log-tér lineáris
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
    if minutes in time_options:  # pontos egyezés
        return battery_data[battery_type][time_options.index(minutes)]  # adott időponthoz tartozó teljesítmény
    elif minutes < time_options[0]:  # 5 percnél kisebb
        return battery_data[battery_type][0]  # 5 perces érték
    elif minutes > time_options[-1]:  # 120 percnél nagyobb
        return battery_data[battery_type][-1]  # 120 perces érték
    for i in range(len(time_options) - 1):  # interpoláció a két legközelebbi időpont között
        t1, t2 = time_options[i], time_options[i + 1]  # időpontok
        if t1 < minutes < t2:  # ha a megadott időpont között van
            p1 = battery_data[battery_type][i]  # teljesítmény értékek
            p2 = battery_data[battery_type][i + 1]  # teljesítmény értékek
            return p1 + (p2 - p1) * ((minutes - t1) / (t2 - t1))  # lineáris interpoláció
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


def create_power_curve_chart(battery_type, battery_count, stringcount, efficiency):
    """Teljesítmény görbe generálása különböző időtartamokra"""
    time_range = range(5, 91, 5)  # 5-től 90 percig, 5 perces lépésekkel
    powers = []

    for t in time_range:
        power_per_batt = interpolate_power(battery_type, t)
        total_power = power_per_batt * battery_count * stringcount * efficiency / 1000  # kW-ban
        powers.append(total_power)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(time_range),
        y=powers,
        mode='lines+markers',
        name=f'{battery_type}',
        line=dict(color='#FF6B35', width=3),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f'📊 Teljesítmény görbe - {battery_type} ({stringcount}x{battery_count}db)',
        xaxis_title='Idő (perc)',
        yaxis_title='Teljesítmény (kW)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def create_backup_time_chart(load_kw, battery_type, stringcount, efficiency):
    """Áthidalási idő akkumulátor darabszám függvényében"""
    battery_counts = range(6, 45, 2)  # 6-tól 44-ig, 2-es lépésekkel
    backup_times = []

    for count in battery_counts:
        # Egyszerű lineáris interpolációs számítás
        # A selected_time paraméter a felhasználó által kért időt jelenti
        # Ezt használjuk referenciaként az interpolációhoz
        selected_time = 15  # 15 perc referencia a grafikonhoz
        power_per_batt = interpolate_power(battery_type, selected_time)
        time_hours = selected_time / 60
        energy_per_batt = power_per_batt * time_hours
        total_energy = energy_per_batt * count * stringcount * efficiency
        backup_time_minutes = (total_energy / (load_kw * 1000)) * 60
        backup_times.append(round(backup_time_minutes, 2))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(battery_counts),
        y=backup_times,
        mode='lines+markers',
        name=f'{battery_type}',
        line=dict(color='#4ECDC4', width=3),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(78, 205, 196, 0.2)'
    ))

    fig.update_layout(
        title=f'⏱️ Áthidalási idő - Akkumulátor darabszám ({stringcount} string)',
        xaxis_title='Akkumulátorok száma (db)',
        yaxis_title='Áthidalási idő (perc)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def create_comparison_chart(load_kw, stringcount, efficiency, selected_time):
    """Különböző akkumulátor típusok összehasonlítása"""
    battery_types_to_compare = list(battery_data.keys())[:6]  # Első 6 típus

    fig = go.Figure()

    for batt_type in battery_types_to_compare:
        time_range = range(5, 91, 10)
        powers = []

        for t in time_range:
            power_per_batt = interpolate_power(batt_type, t)
            powers.append(power_per_batt)

        fig.add_trace(go.Scatter(
            x=list(time_range),
            y=powers,
            mode='lines+markers',
            name=batt_type,
            line=dict(width=2),
            marker=dict(size=5)
        ))

    fig.update_layout(
        title='🔋 Akkumulátor típusok összehasonlítása (1 db teljesítménye)',
        xaxis_title='Idő (perc)',
        yaxis_title='Teljesítmény (W/akku)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="right", x=0.99)
    )

    return fig


def load_sunstone_metadata(xlsx_path="Sunstone_suly_ar.xlsx"):
    """
    Excel fájl beolvasása Sunstone akku súly és ár adatokhoz
    Expects columns like: Type (or Name), Weight_kg (or Weight), Size (or Dimensions), Price (or Price_EUR)
    Returns dict: {battery_type_key: {'weight':..., 'size':..., 'price':...}}
    """
    try:
        df = pd.read_excel(xlsx_path, engine="openpyxl")
    except FileNotFoundError:
        return {}
    # normalize column names
    cols = {c.lower().strip(): c for c in df.columns}
    # find best column candidates
    col_type = cols.get("type") or cols.get("name") or next(iter(cols.values()), None)  # first column as fallback
    col_weight = cols.get("weight_kg") or cols.get("weight") or cols.get("suly") or None
    col_size = cols.get("size") or cols.get("dimensions") or cols.get("méret") or None
    col_price = cols.get("price") or cols.get("ár") or cols.get("price_eur") or None

    meta = {}
    for _, row in df.iterrows():
        key = str(row[col_type]).strip()
        if not key or key.lower() == "nan":
            continue
        meta[key] = {
            "weight": float(row[col_weight]) if col_weight and pd.notna(row[col_weight]) else None,
            "size": str(row[col_size]).strip() if col_size and pd.notna(row[col_size]) else None,
            "price": float(row[col_price]) if col_price and pd.notna(row[col_price]) else None,
            "raw_row": row.to_dict()
        }
    return meta


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

# stringlist = [1, 2, 3, 4]

# FrontView  (Design View)
st.title("🔋 UPS Akkumlátor Méretező")

col1, col2, col3, col4 = st.columns(4)

with col1:
    ups_power_kva = st.number_input("UPS névleges [kVA]", min_value=3.0, max_value=300.0, value=10.0, step=1.0,
                                    help="Látszólagos teljesítmény kVA-ban (3-300kVA).")
    backup_time_min = st.number_input("Áthidalási idő [perc]", min_value=5, max_value=180, value=10,
                                      help="Elvárt áthidalási idő 5-180(Sunstone) perc.")
    st.subheader("📊 Eredmények:")

with col3:
    manufacturer = st.selectbox("Akkumulátor gyártó:", ["Sunstone", "Yuasa"], index=0, help="Válassz akku gyártót!")
    if manufacturer == "Sunstone":
        initial_battery_type = st.selectbox("Akkumlátor típus:", BATTERY_LIST_SUNSTONE, index=0,
                                            help="Akku kapacitások /Ah. (1,6V/cell) (R)aktári")
        battery_data = BATTERY_DATA_SUNSTONE
        time_options = TIME_OPTIONS_SUNSTONE

    else:
        initial_battery_type = st.selectbox("Akkumlátor típus:", BATTERY_LIST_YUASA, index=0,
                                            help="Akku kapacitások /Ah.(1,6V/cell)")
        battery_data = BATTERY_DATA_YUASA
        time_options = TIME_OPTIONS_YUASA

    efficiency = st.number_input("DC hatásfok %", min_value=0.91, max_value=0.96, value=0.95, step=0.01,
                                 help="Akkuk DC hatásfoka 0,92-0,96 között.")
    ##
    if manufacturer == "Yuasa" and backup_time_min > 60:
        st.warning("⚠️ Yuasa akkuval maximum 60 perc áthidalási idő választható!")
        backup_time_min = 60

with col2:
    load_kw = st.number_input("Terhelés [kW]", min_value=2.0, max_value=300.0, value=9.0, step=1.0,
                              help="A valós terhelés kW-ban (2-300kW).")
    power_factor = st.number_input("Teljesítménytényező (PF)", min_value=0.89, max_value=1.00, value=1.00, step=0.01,
                                   help="Teljesítménytényező (AC) 0,90-1,00 között.")

with col4:
    stringcount = st.selectbox("Stringek", [1, 2, 3, 4, 5, 6, 7, 8], index=0, help="A stringek száma 1-8 között.")

    battery_count = st.slider("Akkumlátorok száma", min_value=6, max_value=44, value=40,
                              help="Akkuk száma 6-44 között.")
    # if  power_factor >= 0.95 and
    if battery_count <= 36:
        st.toast("Figyelem: 36db akkunál (SOCOMEC)! / csökkenhet a DC hatásfok! <95%.",
                 icon="⚠️")  # st.error("⚠️ A hatásfok az akkuk  száma miatt 95%!")

if load_kw > ups_power_kva * power_factor:
    st.error("⚠️ A terhelés nem lehet nagyobb, mint az UPS valós teljesítménye.")

else:
    recommended_battery_count = calculate_required_battery_count(load_kw, initial_battery_type, backup_time_min,
                                                                 backup_time_min)
    actual_time, power_per_batt, energy_per_batt = calculate_energy_based_backup_time(
        load_kw, initial_battery_type, battery_count, backup_time_min)

    minutes = int(actual_time)
    seconds = int(round((actual_time - minutes) * 60))
    st.markdown(
        f"**✅ Valós áthidalási idő : :red[{minutes}] perc :red[{seconds}] mp** (String:{stringcount}x{battery_count}db össz:{stringcount * battery_count}db), **String feszültség:** {battery_count * 12} V")

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

    # === SUNSTONE METADATA (súly, méret, ár) ===
    if manufacturer == "Sunstone":
        sunstone_meta = load_sunstone_metadata("Sunstone_suly_ar.xlsx")
        # try exact key first, then try prefix match
        meta = sunstone_meta.get(initial_battery_type)
        if not meta:
            # try matching by containment / startswith
            for k in sunstone_meta:
                if k.lower() in initial_battery_type.lower() or initial_battery_type.lower() in k.lower() or initial_battery_type.lower().startswith(
                        k.lower()) or k.lower().startswith(initial_battery_type.lower()):
                    meta = sunstone_meta[k]
                    break

        if meta:
            st.markdown(
                f"**Akku súlya:** {meta['weight']} kg/db, **Méret:** {meta['size']} (LxWxH), **Ár:** {meta['price']:.2f} €/db")
            st.markdown(
                f"**Akku össz.súlya:** {meta['weight'] * stringcount * battery_count} kg, **Össz Ára:** {meta['price'] * stringcount * battery_count:.2f} €, **/{stringcount * battery_count}db**")
        else:
            st.info("ℹ️ Nem található adat a `Sunstone_suly_ar.xlsx` fájlban az aktuális akkutípushoz.")

    # === GRAFIKONOK ===
    st.markdown("---")
    st.subheader("📈 Grafikus elemzések")

    # Tabok létrehozása a különböző grafikonokhoz
    tab1, tab2, tab3 = st.tabs(["⚡ Teljesítmény görbe", "⏱️ Áthidalási idő", "🔋 Típus összehasonlítás"])

    with tab1:
        st.plotly_chart(
            create_power_curve_chart(initial_battery_type, battery_count, stringcount, efficiency),
            use_container_width=True
        )
        st.info(
            "📌 Ez a grafikon mutatja, hogy a kiválasztott akkumulátor konfiguráció mennyi teljesítményt tud leadni különböző időtartamok alatt.")

    with tab2:
        st.plotly_chart(
            create_backup_time_chart(load_kw, initial_battery_type, stringcount, efficiency),
            use_container_width=True
        )
        st.info("📌 Ez a grafikon mutatja, hogyan változik az áthidalási idő az akkumulátorok számának függvényében.")

    with tab3:
        st.plotly_chart(
            create_comparison_chart(load_kw, stringcount, efficiency, backup_time_min),
            use_container_width=True
        )
        st.info("📌 Ez a grafikon összehasonlítja a különböző akkumulátor típusok teljesítményét.")

st.markdown(
    """
    <div style="position:fixed; left:0; bottom:0; width:100%; background: #f8e71c; color:#222; text-align:center; padding:8px 0; z-index:1000;">
    <marquee behavior="scroll" direction="left" scrollamount="6">
        🔋 UPS méretező | Készítette: Ferosoft ™®| ©2025 V1.6.0 - Grafikus elemzések 📊💾 | Minden jog fenntartva !💡
    </marquee>
    </div>
    """,
    unsafe_allow_html=True
)

# 2025.02.08  Ferosoft™® UPS méretező V1.6.0 - Teljes funkciókészlet
# Új funkciók:
# - Teljesítmény görbe az idő függvényében (Plotly)
# - Áthidalási idő vs. akkumulátor darabszám grafikon
# - Akkumulátor típusok összehasonlítása
# - Excel fájl beolvasás (Sunstone súly, méret, ár adatok)
# - String feszültség megjelenítés
# - 180 perces áthidalási idő támogatás (Sunstone)
# - 1-8 string támogatás
# Futtatás: python -m streamlit run UPS_szamolo_ver1_6_0_chart.py
# Web: http://<szerver_neve>:8501
