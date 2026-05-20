import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time

st.set_page_config(page_title="Kuyruk Simülasyonu", layout="wide")

def get_random_value(dist_type, params):
    val = 0
    if dist_type == "Sabit":
        val = params['sabit_deger']
    elif dist_type == "Normal":
        val = np.random.normal(params['mu'], params['sigma'])
    elif dist_type == "Üstel":
        val = np.random.exponential(1.0 / params['lam']) if params['lam'] > 0 else 0
    elif dist_type == "Poisson":
        val = np.random.poisson(params['lam'])
    elif dist_type == "Empirik":
        try:
            pairs = params['empirik_str'].split(',')
            values, probs = [], []
            for p in pairs:
                v, pr = p.split(':')
                values.append(float(v.strip()))
                probs.append(float(pr.strip()))
            val = np.random.choice(values, p=probs)
        except:
            val = 1 
    return max(0.01, val) 

def run_simulation(sim_time, max_q, servers_count, arr_dist, arr_params, srv_dist, srv_params, grp_dist, grp_params):
    servers = [{'id': i, 'free_at': 0, 'busy_time': 0} for i in range(servers_count)]
    current_time = 0
    queue = 0
    lost_customers = 0
    served_customers = 0
    state_log = []
    
    next_arrival = get_random_value(arr_dist, arr_params)
    
    while current_time < sim_time or queue > 0 or any(s['free_at'] > current_time for s in servers):
        busy_servers = [s for s in servers if s['free_at'] > current_time]
        next_finish_time = min((s['free_at'] for s in busy_servers), default=float('inf'))
        
        if next_arrival <= next_finish_time and current_time < sim_time:
            current_time = next_arrival
            group_size = int(get_random_value(grp_dist, grp_params))
            group_size = max(1, group_size)
            
            lost_this_turn = 0
            for _ in range(group_size):
                if queue < max_q:
                    queue += 1
                else:
                    lost_customers += 1
                    lost_this_turn += 1
            
            state_log.append({
                'Zaman': round(current_time, 2),
                'Olay': 'Geliş',
                'Gelen': group_size,
                'Kuyruk': queue,
                'Kaybedilen': lost_this_turn,
                'Hizmet_Alan_Sunucu': '-'
            })
            next_arrival = current_time + get_random_value(arr_dist, arr_params)
            
        elif next_finish_time != float('inf'):
            current_time = next_finish_time
        else:
            break
            
        free_servers = [s for s in servers if s['free_at'] <= current_time]
        for s in free_servers:
            if queue > 0:
                queue -= 1
                served_customers += 1
                service_t = get_random_value(srv_dist, srv_params)
                s['free_at'] = current_time + service_t
                s['busy_time'] += service_t
                
                state_log.append({
                    'Zaman': round(current_time, 2),
                    'Olay': 'Hizmet Başlangıcı',
                    'Gelen': 0,
                    'Kuyruk': queue,
                    'Kaybedilen': 0,
                    'Hizmet_Alan_Sunucu': f"Sunucu-{s['id']+1}"
                })

    df = pd.DataFrame(state_log)
    if not df.empty:
        df['Adım'] = range(1, len(df) + 1)
        
    return df, servers, served_customers, lost_customers, current_time

st.title("⚙️ Kuyruk Sistemi Simülasyonu & Karar Destek Sistemi")
st.markdown("Bu uygulama; kafe, berber, gişe gibi sistemlerin performansını ölçmek ve mühendislik kararları almak için geliştirilmiştir.")

st.sidebar.header("📝 Simülasyon Parametreleri")

sim_time = st.sidebar.number_input("Simülasyon Süresi (dk)", min_value=10, max_value=1000, value=60)
servers_count = st.sidebar.number_input("Servis/Çalışan/Makine Sayısı", min_value=1, max_value=20, value=2)
max_q = st.sidebar.number_input("Maksimum Kuyruk Uzunluğu (Kapasite)", min_value=1, max_value=100, value=10)
crit_q = st.sidebar.number_input("Kritik Kuyruk Eşiği (Uyarı için)", min_value=1, max_value=100, value=5)

st.sidebar.markdown("---")
st.sidebar.subheader("Geliş Aralığı Dağılımı")
arr_dist = st.sidebar.selectbox("Geliş Dağılım Tipi", ["Üstel", "Normal", "Sabit", "Empirik"], key='arr')
arr_params = {}
if arr_dist == "Üstel":
    arr_params['lam'] = st.sidebar.number_input("Lambda (Geliş Hızı)", value=0.5)
elif arr_dist == "Normal":
    arr_params['mu'] = st.sidebar.number_input("Ortalama (Geliş)", value=2.0)
    arr_params['sigma'] = st.sidebar.number_input("Standart Sapma (Geliş)", value=0.5)
elif arr_dist == "Sabit":
    arr_params['sabit_deger'] = st.sidebar.number_input("Sabit Geliş Aralığı (dk)", value=2.0)
elif arr_dist == "Empirik":
    arr_params['empirik_str'] = st.sidebar.text_input("Değer:Olasılık (Örn: 1:0.5, 2:0.5)", value="1:0.3, 2:0.7")

st.sidebar.markdown("---")
st.sidebar.subheader("Hizmet Süresi Dağılımı")
srv_dist = st.sidebar.selectbox("Hizmet Dağılım Tipi", ["Normal", "Üstel", "Sabit", "Empirik"], key='srv')
srv_params = {}
if srv_dist == "Normal":
    srv_params['mu'] = st.sidebar.number_input("Ortalama (Hizmet)", value=3.0)
    srv_params['sigma'] = st.sidebar.number_input("Standart Sapma (Hizmet)", value=1.0)
elif srv_dist == "Üstel":
    srv_params['lam'] = st.sidebar.number_input("Lambda (Hizmet Hızı)", value=0.3)
elif srv_dist == "Sabit":
    srv_params['sabit_deger'] = st.sidebar.number_input("Sabit Hizmet Süresi (dk)", value=3.0)
elif srv_dist == "Empirik":
    srv_params['empirik_str'] = st.sidebar.text_input("Değer:Olasılık", value="2:0.4, 4:0.6", key='srv_emp')

st.sidebar.markdown("---")
st.sidebar.subheader("Grup Büyüklüğü (Aynı anda gelen)")
grp_dist = st.sidebar.selectbox("Grup Dağılımı", ["Sabit", "Poisson"], key='grp')
grp_params = {}
if grp_dist == "Sabit":
    grp_params['sabit_deger'] = st.sidebar.number_input("Kişi Sayısı", value=1, min_value=1)
elif grp_dist == "Poisson":
    grp_params['lam'] = st.sidebar.number_input("Lambda (Grup)", value=1.5)

if st.sidebar.button("🚀 Simülasyonu Çalıştır", use_container_width=True):
    with st.spinner('Simülasyon hesaplanıyor...'):
        df_log, server_stats, served, lost, total_time = run_simulation(
            sim_time, max_q, servers_count, 
            arr_dist, arr_params, 
            srv_dist, srv_params, 
            grp_dist, grp_params
        )
        
        st.session_state['df_log'] = df_log
        st.session_state['server_stats'] = server_stats
        st.session_state['served'] = served
        st.session_state['lost'] = lost
        st.session_state['total_time'] = total_time
        st.session_state['crit_q'] = crit_q
        st.session_state['servers_count'] = servers_count
        
        # Yeni simülasyonda oynatıcıyı en sona al ve durdur
        st.session_state['anim_step'] = len(df_log)
        st.session_state['is_playing'] = False

if 'df_log' in st.session_state and not st.session_state['df_log'].empty:
    df_log = st.session_state['df_log']
    crit_q = st.session_state['crit_q']
    
    st.divider()
    st.subheader("1. Adım Adım Simülasyon İzleme")
    
    # --- OYNATICI MANTIĞI ---
    if 'anim_step' not in st.session_state:
        st.session_state['anim_step'] = len(df_log)
    if 'is_playing' not in st.session_state:
        st.session_state['is_playing'] = False

    if st.session_state['is_playing']:
        if st.session_state['anim_step'] < len(df_log):
            st.session_state['anim_step'] += 1
            time.sleep(0.05) # Animasyon hızı (Saniye)
            st.rerun()
        else:
            st.session_state['is_playing'] = False

    col1, col2 = st.columns([3, 1])
    with col1:
        # Slider değeri session_state'e bağlandı
        step = st.slider("İzlenecek Adım", min_value=1, max_value=len(df_log), value=st.session_state['anim_step'])
        if step != st.session_state['anim_step']:
            st.session_state['anim_step'] = step
            st.session_state['is_playing'] = False # Kullanıcı slidera dokunursa otomatik oynatma dursun
            st.rerun()
            
    with col2:
        if st.button("▶️ Canlı Oynat", use_container_width=True):
            st.session_state['anim_step'] = 1 # 1. adımdan başlat
            st.session_state['is_playing'] = True
            st.rerun()

    # O anki adıma kadar olan veriyi göster
    current_df = df_log[df_log['Adım'] <= st.session_state['anim_step']]
    last_state = current_df.iloc[-1]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⏱️ Mevcut Zaman", f"{last_state['Zaman']} dk")
    m2.metric("👥 Anlık Kuyruk", int(last_state['Kuyruk']))
    m3.metric("🚨 Toplam Kaybedilen", int(current_df['Kaybedilen'].sum()))
    m4.metric("⚙️ Son Olay", last_state['Olay'])

    st.write("**Son Gerçekleşen Olaylar:**")
    st.dataframe(current_df.tail(5)[['Adım', 'Zaman', 'Olay', 'Gelen', 'Kuyruk', 'Kaybedilen', 'Hizmet_Alan_Sunucu']], use_container_width=True)

    st.subheader("2. Kuyruk Durumu Grafiği")
    
    line_df = pd.DataFrame({'Zaman': [0, current_df['Zaman'].max()], 'Kritik': [crit_q, crit_q]})
    
    base = alt.Chart(current_df).encode(x=alt.X('Zaman:Q', title="Simülasyon Süresi (dk)"))
    
    bars = base.mark_area(opacity=0.6).encode(
        y=alt.Y('Kuyruk:Q', title="Kuyruk Uzunluğu"),
        color=alt.condition(
            alt.datum.Kuyruk >= crit_q,
            alt.value('red'),
            alt.value('green')
        )
    )
    
    rule = alt.Chart(line_df).mark_line(color='orange', strokeDash=[5, 5]).encode(
        x='Zaman:Q',
        y='Kritik:Q'
    )
    
    st.altair_chart(bars + rule, use_container_width=True)

    # Sadece animasyon bittiğinde veya slider en sondayken sonuçları göster
    if st.session_state['anim_step'] == len(df_log):
        st.divider()
        st.subheader("3. Simülasyon Sonuçları ve Mühendislik Kararı")
        
        served = st.session_state['served']
        lost = st.session_state['lost']
        total_time = st.session_state['total_time']
        server_stats = st.session_state['server_stats']
        servers_count = st.session_state['servers_count']
        
        max_q_reached = current_df['Kuyruk'].max()
        
        utilizations = []
        for s in server_stats:
            util_rate = (s['busy_time'] / total_time) * 100 if total_time > 0 else 0
            utilizations.append(util_rate)
            
        avg_util = np.mean(utilizations)
        
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("✅ Hizmet Verilen", served)
        res2.metric("❌ Kaçan Müşteri", lost)
        res3.metric("📊 Max Kuyruk", int(max_q_reached))
        res4.metric("📈 Ort. Sistem Kullanımı", f"%{avg_util:.1f}")

        st.markdown("### 🧠 Sistem Analizi ve Karar")
        
        if lost > 0 or max_q_reached >= crit_q or avg_util > 85:
            st.error("🚨 **KARAR: SİSTEM YETERSİZ - YENİ YATIRIM GEREKLİ!**")
            st.write(f"- Müşteri kaybı yaşanmıştır ({lost} kişi) veya kuyruk kritik seviyeyi aşmıştır.")
            st.write("- **Öneri:** İşletmeye yeni bir personel/barista/makine eklenmeli veya mevcut hizmet hızı artırılmalıdır.")
        elif avg_util < 35:
            st.warning("⚠️ **KARAR: KAPASİTE FAZLASI VAR!**")
            st.write(f"- Sistem kullanım oranı çok düşük (%{avg_util:.1f}).")
            st.write("- **Öneri:** Personel sayısı azaltılabilir veya pazarlama stratejileri ile müşteri geliş hızı artırılabilir. Maliyet israfı söz konusu.")
        else:
            st.success("✅ **KARAR: MEVCUT SİSTEM YETERLİ VE DENGELİ.**")
            st.write(f"- Sistem kapasitesi talebi sorunsuz bir şekilde karşılıyor (Kullanım: %{avg_util:.1f}).")
            st.write("- **Öneri:** Mevcut düzen korunabilir, ek yatırıma şu an için gerek yoktur.")
            
        with st.expander("Çalışan/Sunucu Detayları"):
            s_data = []
            for i, s in enumerate(server_stats):
                s_data.append({
                    "Sunucu": f"Sunucu/Çalışan {i+1}",
                    "Aktif Çalışma (dk)": round(s['busy_time'], 2),
                    "Boş Kalma (dk)": round(total_time - s['busy_time'], 2),
                    "Kullanım Oranı (%)": round((s['busy_time']/total_time)*100, 2)
                })
            st.dataframe(pd.DataFrame(s_data), use_container_width=True)
elif 'df_log' not in st.session_state:
    st.info("👈 Simülasyonu başlatmak için sol menüden parametreleri ayarlayıp 'Çalıştır' butonuna basınız.")