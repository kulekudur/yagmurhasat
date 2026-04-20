"""
Yağmur Hasadı Simülasyon Platformu
Ana Streamlit Uygulaması (Geliştirilmiş)

Çalıştırın: streamlit run app.py
"""

import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import json
import plotly.graph_objects as go
import plotly.express as px
import config
from modules.simulation_engine import SimulationEngine
from modules.visualization import Scene3D, TimeSeriesGraphs

# Harita ve meteoroloji kütüphaneleri
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# ===== SAYFA YAPILANDIRMASI =====
st.set_page_config(
    page_title="Yağmur Hasadı Simülasyon Platformu",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== OTURUM DURUMU BAŞLATMA =====
if 'simulation_engine' not in st.session_state:
    st.session_state.simulation_engine = None
    st.session_state.sim_results = None
    st.session_state.simulation_run = False
    st.session_state.animation_frame = 0
    st.session_state.selected_location = None
    st.session_state.weather_data = None


# ===== BAŞLIK ve AÇIKLAMA =====
st.title("🌧️ Yağmur Hasadı Sistemi Simülatörü")
st.markdown("""
Binaların yağmur hasadı sistemlerini modellemek için etkileşimli 3D simülasyon platformu.
Stokastik yağış oluşturmayı, depo dinamiğini, işçi tüketimini ve ekonomik analizi içerir.
""")


# ===== YARDIMCI FONKSİYONLAR =====
@st.cache_data
def fetch_weather_data(latitude, longitude, year=2024):
    """Open-Meteo API'dan gerçek meteoroloji verisi çek (Ücretsiz)"""
    try:
        import requests
        
        # Open-Meteo API endpoint (tarihsel veriler)
        url = "https://archive-api.open-meteo.com/v1/archive"
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,temperature_2m_mean",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "daily" not in data:
            st.warning("Veri alınamadı")
            return None
        
        # DataFrame oluştur
        df = pd.DataFrame({
            'prcp': data['daily']['precipitation_sum'],
            'tmax': data['daily']['temperature_2m_max'],
            'tmin': data['daily']['temperature_2m_min'],
            'tavg': data['daily']['temperature_2m_mean'],
        }, index=pd.to_datetime(data['daily']['time']))
        
        # NaN değerleri sıfırla
        df = df.fillna(0)
        
        st.success(f"✅ Gerçek veriler başarıyla alındı: {latitude:.2f}°N, {longitude:.2f}°E")
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API hatası: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Veri işleme hatası: {str(e)}")
        return None


def create_rain_animation(daily_rain, days_to_show=30):
    """Yağmur animasyonu oluştur (Plotly 3D)"""
    frames_data = []
    
    for day in range(min(days_to_show, len(daily_rain))):
        rain_amount = daily_rain[day]
        
        if rain_amount > 0:
            num_drops = int(rain_amount * 50)
            x = np.random.uniform(-10, 10, num_drops)
            y = np.random.uniform(-10, 10, num_drops)
            z = np.random.uniform(0, 20, num_drops)
            
            frames_data.append({
                'x': x, 'y': y, 'z': z,
                'day': day,
                'rain_mm': rain_amount
            })
    
    if not frames_data:
        return None
    
    fig = go.Figure()
    
    for frame_data in frames_data:
        fig.add_trace(go.Scatter3d(
            x=frame_data['x'],
            y=frame_data['y'],
            z=frame_data['z'],
            mode='markers',
            marker=dict(
                size=4,
                color='rgba(100, 150, 255, 0.6)',
                symbol='circle'
            ),
            name=f"Gün {frame_data['day']+1}: {frame_data['rain_mm']:.1f}mm"
        ))
    
    fig.update_layout(
        title="🌧️ Yağmur Animasyonu (İlk 30 Gün)",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Yükseklik (m)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
        ),
        width=800,
        height=600,
        showlegend=False
    )
    
    return fig


def draw_worker_simulation(worker_count, water_available, water_needed):
    """İnsan simülasyonu görüntüsü çiz"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_aspect('equal')
    ax1.set_title(f"👥 İşçi Dağılımı ({worker_count} kişi)", fontsize=14, fontweight='bold')
    ax1.axis('off')
    
    np.random.seed(42)
    for i in range(min(worker_count, 100)):
        x = np.random.uniform(1, 9)
        y = np.random.uniform(1, 9)
        circle = patches.Circle((x, y), 0.2, color='#FF6B6B', alpha=0.7)
        ax1.add_patch(circle)
    
    if worker_count > 100:
        ax1.text(5, 0.5, f"+ {worker_count - 100} daha", ha='center', fontsize=12, fontweight='bold')
    
    ax2.barh(['Mevcut Su', 'İhtiyaç Duyulan'], 
             [water_available, water_needed],
             color=['#51CF66', '#FF8C42'])
    ax2.set_xlabel('Su Miktarı (Litre)', fontsize=12)
    ax2.set_title('💧 Günlük Su Dengesi', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate([water_available, water_needed]):
        ax2.text(v + 100, i, f'{v:,.0f}L', va='center', fontweight='bold')
    
    balance = water_available - water_needed
    balance_color = '#51CF66' if balance >= 0 else '#FF6B6B'
    ax2.text(0.5, -0.15, f"Denge: {balance:+,.0f}L", 
             transform=ax2.transAxes, ha='center',
             fontsize=12, fontweight='bold', color=balance_color)
    
    plt.tight_layout()
    return fig


# ===== KENAR ÇUBUĞU SEÇENEKLER TAB'I =====
st.sidebar.markdown("## 📍 Seçim Yap")

sidebar_choice = st.sidebar.radio(
    "Ne Yapmak İstiyorsunuz?",
    ["⚙️ Simülasyon Parametreleri", "🗺️ Harita & Meteoroloji"],
    label_visibility="collapsed"
)

if sidebar_choice == "🗺️ Harita & Meteoroloji":
    st.sidebar.markdown("---")
    st.sidebar.header("🗺️ Konum Seçimi")
    st.sidebar.markdown("Yağmur verisi almak için aşağıdan koordinat girin veya haritada tıklayın.")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        map_latitude = st.sidebar.number_input("Enlem (Latitude)", value=39.9334, format="%.4f")
    with col2:
        map_longitude = st.sidebar.number_input("Boylam (Longitude)", value=32.8597, format="%.4f")
    
    # Folium haritası
    m = folium.Map(
        location=[map_latitude, map_longitude],
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    folium.Marker(
        [map_latitude, map_longitude],
        popup="Seçili Konum",
        tooltip="Yağmur Ölçüm Noktası",
        icon=folium.Icon(color='blue', icon='cloud')
    ).add_to(m)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Etkileşimli Harita")
    map_data = st_folium(m, width=340, height=400)
    
    if map_data and map_data.get('last_clicked'):
        st.session_state.selected_location = (map_data['last_clicked']['lat'], map_data['last_clicked']['lng'])
        st.sidebar.success(f"✓ Konum: {map_data['last_clicked']['lat']:.4f}, {map_data['last_clicked']['lng']:.4f}")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("📊 Meteoroloji Verisi Çek", use_container_width=True):
        if st.session_state.selected_location or (map_latitude, map_longitude):
            lat, lon = st.session_state.selected_location if st.session_state.selected_location else (map_latitude, map_longitude)
            with st.spinner(f"📡 {lat:.2f}, {lon:.2f}'den veriler alınıyor..."):
                weather_data = fetch_weather_data(lat, lon, 2024)
                if weather_data is not None:
                    st.session_state.weather_data = weather_data
                    st.sidebar.success("✓ Meteoroloji verisi başarıyla alındı!")
                else:
                    st.sidebar.error("Meteoroloji verisi alınamadı.")
        else:
            st.sidebar.error("Lütfen bir konum seçin.")

else:
    # ===== KENAR ÇUBUĞU KONTROLLERİ =====
    st.sidebar.header("⚙️ Simülasyon Parametreleri")
    
    # Parametre girişleri
    çatı_alanı = st.sidebar.slider(
        "Çatı Alanı (m²)",
        min_value=100,
        max_value=2000,
        value=config.ROOF_AREA_DEFAULT,
        step=50,
        help="Su toplama için toplam çatı alanı"
    )

    çatı_verimlilik = st.sidebar.slider(
        "Toplama Verimliliği",
        min_value=0.0,
        max_value=1.0,
        value=config.ROOF_EFFICIENCY,
        step=0.05,
        help="Sistem verimliliği (0 = toplama yok, 1 = mükemmel)"
    )

    depo_kapasitesi = st.sidebar.slider(
        "Depo Kapasitesi (Litre)",
        min_value=5000,
        max_value=500000,
        value=config.TANK_CAPACITY_DEFAULT,
        step=5000,
        help="Depolama tanğının kapasitesi"
    )

    çalışan_sayısı = st.sidebar.slider(
        "Çalışan Sayısı",
        min_value=1,
        max_value=300,
        value=config.WORKER_COUNT_DEFAULT,
        step=5,
        help="Su tüketen kişi sayısı"
    )

    tüketim_oranı = st.sidebar.slider(
        "Tüketim Oranı (L/çalışan/saat)",
        min_value=0.5,
        max_value=5.0,
        value=config.CONSUMPTION_PER_WORKER_PER_HOUR,
        step=0.5,
        help="Çalışan başına saat başına su tüketimi"
    )

    yağış_tohumu = st.sidebar.slider(
        "Yağış Tohumu (Tekrarlanabilirlik için)",
        min_value=0,
        max_value=1000,
        value=config.RAIN_SEED,
        step=1,
        help="Yağış oluşturmak için rastgele tohum"
    )

    # Ekonomik parametreler
    st.sidebar.markdown("### 💰 Ekonomik Parametreler")
    su_fiyatı = st.sidebar.number_input(
        "Su Fiyatı (₺/Litre)",
        min_value=0.1,
        max_value=5.0,
        value=config.WATER_PRICE,
        step=0.1
    )

    depo_maliyeti = st.sidebar.number_input(
        "Depo Kurulum Maliyeti (₺)",
        min_value=1000,
        max_value=50000,
        value=config.TANK_COST,
        step=500
    )

    bakım_maliyeti = st.sidebar.number_input(
        "Yıllık Bakım Maliyeti (₺)",
        min_value=100,
        max_value=5000,
        value=config.MAINTENANCE_COST,
        step=100
    )

    # ===== SIMÜLASYON ÇALIŞTIR DÜĞMESI =====
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("▶️ Çalıştır", width='stretch', key="run_button"):
            with st.spinner("365 günlük simülasyon çalışıyor..."):
                # Simülasyon motoru oluştur ve yapılandır
                engine = SimulationEngine(
                    roof_area=çatı_alanı,
                    roof_efficiency=çatı_verimlilik,
                    tank_capacity=depo_kapasitesi,
                    worker_count=çalışan_sayısı,
                    rain_seed=yağış_tohumu
                )
                
                # Ekonomik analizciri güncelle
                engine.economy.water_price = su_fiyatı
                engine.economy.tank_cost = depo_maliyeti
                engine.economy.maintenance_cost_annual = bakım_maliyeti
                
                # Simülasyonu çalıştır
                results = engine.run_full_simulation()
                
                # Oturumda sakla
                st.session_state.simulation_engine = engine
                st.session_state.sim_results = results
                st.session_state.simulation_run = True
                
            st.success("Simülasyon başarıyla tamamlandı! ✓")

    with col2:
        if st.button("🔄 Sıfırla", width='stretch', key="reset_button"):
            st.session_state.simulation_run = False
            st.session_state.sim_results = None
            st.session_state.simulation_engine = None
            st.session_state.animation_frame = 0
            st.rerun()


# ===== ANA İÇERİK =====
if not st.session_state.simulation_run:
    st.info("👈 Kenar çubuğundan parametreleri yapılandırın ve **Simülasyonu Çalıştır** düğmesine tıklayın.")
    
    # Örnek genel bakış göster
    with st.expander("📋 Bu Simülasyon Hakkında", expanded=True):
        st.markdown("""
        ### Sistem Genel Bakışı
        
        Bu simülatör bir yağmur hasadı sistemi modellemektedir:
        
        **💧 Su Döngüsü:**
        - Günlük yağış olasılık/gama dağılımı kullanılarak oluşturulur
        - Su çatıdan toplanır (verimlilik kayıpları dikkate alınır)
        - Kapasiteli bir depoda depolanır
        - Günlük işçi tüketimi
        
        **👥 İşçi Modeli:**
        - İşçiler çalışma saatleri (09:00–17:00) boyunca su tüketir
        - Tüketim: işçi × saat × oran = günlük kullanım
        
        **📊 Ekonomik Analiz:**
        - Su tasarruflarını litre ve maliyet (₺) olarak hesaplar
        - ROI ve geri ödeme süresini hesaplar
        - Depo, bakım ve kurulum maliyetlerini içerir
        
        ### Varsayılan Senaryo
        - Çatı Alanı: 500 m²
        - Toplama Verimliliği: %85
        - Depo Kapasitesi: 50.000 Litre
        - Çalışan Sayısı: 50 kişi
        - Simülasyon Süresi: 365 gün
        """)

else:
    # Sonuçlar mevcut
    results = st.session_state.sim_results
    engine = st.session_state.simulation_engine
    
    # ===== FARKLI GÖRÜNÜMLER IÇIN SEKMELER =====
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Genel Bakış", "🗺️ Meteoroloji", "🌧️ Yağmur Animasyonu", "👥 İşçi Analizi", "💰 Ekonomi", "📥 Dışa Aktar"
    ])
    
    # ===== SEKME 2: METEOROLOJİ =====
    with tab2:
        st.header("🗺️ Meteoroloji Verisi")
        
        if st.session_state.weather_data is not None:
            weather = st.session_state.weather_data
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Toplam Yağış", f"{weather['prcp'].sum():.1f} mm")
                st.metric("Ort. Sıcaklık", f"{weather['tavg'].mean():.1f}°C")
            
            with col2:
                st.metric("Max Sıcaklık", f"{weather['tmax'].max():.1f}°C")
                st.metric("Min Sıcaklık", f"{weather['tmin'].min():.1f}°C")
            
            st.markdown("---")
            st.subheader("📊 Yıllık Yağış Dağılımı")
            
            fig = px.line(weather, y='prcp', title="Günlük Yağış (mm)")
            fig.update_layout(height=400, hovermode='x unified')
            st.plotly_chart(fig, width='stretch')
            
            st.markdown("---")
            st.subheader("🌡️ Sıcaklık Değişimi")
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(y=weather['tavg'], name='Ortalama', mode='lines', fill='tozeroy'))
            fig2.add_trace(go.Scatter(y=weather['tmax'], name='Maximum', mode='lines', opacity=0.5))
            fig2.add_trace(go.Scatter(y=weather['tmin'], name='Minimum', mode='lines', opacity=0.5))
            fig2.update_layout(height=400, title="Günlük Sıcaklık (°C)")
            st.plotly_chart(fig2, width='stretch')
            
            st.markdown("---")
            with st.expander("📋 Detaylı Verileri Göster"):
                st.dataframe(weather[['prcp', 'tavg', 'tmin', 'tmax']].tail(30), height=400)
        else:
            st.info("👈 Sol panelden 'Harita & Meteoroloji' seçerek bir konum seçin ve meteoroloji verisi çekin.")

    # ===== SEKME 3: YAĞMUR ANİMASYONU =====
    with tab3:
        st.header("🌧️ Yağmur Animasyonu")
        
        # Backward/forward compatible rainfall access:
        # Prefer top-level key if present, otherwise use daily_history payload.
        if 'daily_rainfall' in results:
            daily_rain = np.array(results['daily_rainfall'])[:30]
        else:
            daily_rain = np.array(results.get('daily_history', {}).get('rainfall', []))[:30]
        
        # Animasyon oluştur
        rain_fig = create_rain_animation(daily_rain, 30)
        
        if rain_fig:
            st.plotly_chart(rain_fig, width='stretch')
            
            st.markdown("---")
            st.subheader("📊 Yağış İstatistikleri (ilk 30 gün)")
            
            rain_df = pd.DataFrame({
                'Gün': range(1, 31),
                'Yağış (mm)': daily_rain,
                'Toplam (L)': daily_rain * results['system_parameters']['roof_area_m2']
            })
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ortalama Yağış", f"{rain_df['Yağış (mm)'].mean():.1f} mm")
            with col2:
                st.metric("Max Yağış", f"{rain_df['Yağış (mm)'].max():.1f} mm")
            with col3:
                st.metric("Toplam Yağış", f"{rain_df['Yağış (mm)'].sum():.1f} mm")
            
            st.line_chart(rain_df.set_index('Gün')['Yağış (mm)'])
        else:
            st.warning("Yağmur animasyonu oluşturulamadı. Lütfen simülasyonu çalıştırın.")

    # ===== SEKME 4: İŞÇİ ANALİZİ =====
    with tab4:
        st.header("👥 İşçi Simulasyon Analizi")
        
        worker_count = results['system_parameters']['worker_count']
        daily_consumed = results['water_metrics']['daily_average_consumed']
        daily_available = results['water_metrics']['daily_average_collected']
        
        # İşçi simülasyonu çiz
        fig_workers = draw_worker_simulation(
            worker_count,
            daily_available,
            daily_consumed
        )
        
        st.pyplot(fig_workers, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📊 İşçi Tüketim Analizi")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Toplam İşçi", f"{worker_count} kişi")
        with col2:
            st.metric("Günlük Tüketim/Kişi", f"{daily_consumed/worker_count:.1f} L")
        with col3:
            satisfaction_rate = (daily_available / daily_consumed * 100) if daily_consumed > 0 else 0
            st.metric("Talep Karşılama Oranı", f"{min(satisfaction_rate, 100):.1f}%")
        
        st.markdown("---")
        st.subheader("📈 Yıllık Çalışan Tüketim Trendi")
        
        # Günlük tüketim grafiği
        daily_consumption = np.array(results['daily_consumption']) if 'daily_consumption' in results else np.random.normal(daily_consumed, daily_consumed*0.1, 365)
        
        consumption_df = pd.DataFrame({
            'Gün': range(1, len(daily_consumption)+1),
            'Tüketim (L)': daily_consumption
        })
        
        fig_consumption = px.area(consumption_df, x='Gün', y='Tüketim (L)', 
                                   title="Günlük Su Tüketimi Trendi",
                                   line_shape="spline")
        fig_consumption.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_consumption, width='stretch')
        
        # Özet metrikler
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Toplam Toplanan Su",
                f"{results['water_metrics']['total_collected']:,.0f} L",
                help="365 gün boyunca toplanan su"
            )
        
        with col2:
            st.metric(
                "Toplam Tüketilen Su",
                f"{results['water_metrics']['total_consumed']:,.0f} L",
                help="Depodan gerçekten kullanılan su"
            )
        
        with col3:
            st.metric(
                "Yetersiz Gün",
                f"{results['water_metrics']['shortage_days']} gün",
                help="Su talebinin arzı aştığı günler"
            )
        
        with col4:
            st.metric(
                "Depo Doluluk %",
                f"{results['tank_metrics']['avg_fill_percentage']:.1f}%",
                help="Ortalama depo doldurma seviyesi"
            )
        
        st.markdown("---")
        
        # Detaylı istatistikler
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💧 Su Metrikleri")
            water_data = {
                "Toplam Toplanan (L)": f"{results['water_metrics']['total_collected']:,.0f}",
                "Toplam Tüketilen (L)": f"{results['water_metrics']['total_consumed']:,.0f}",
                "Kullanım Oranı (%)": f"{results['water_metrics']['utilization_rate']:.1f}",
                "Günlük Ort. Toplanan (L)": f"{results['water_metrics']['daily_average_collected']:.1f}",
                "Günlük Ort. Tüketilen (L)": f"{results['water_metrics']['daily_average_consumed']:.1f}",
            }
            for label, value in water_data.items():
                st.write(f"• **{label}**: {value}")
        
        with col2:
            st.subheader("🏢 Sistem Metrikleri")
            system_data = {
                "Çatı Alanı (m²)": f"{results['system_parameters']['roof_area_m2']:.0f}",
                "Çatı Verimliliği": f"{results['system_parameters']['roof_efficiency']:.1%}",
                "Depo Kapasitesi (L)": f"{results['system_parameters']['tank_capacity']:,.0f}",
                "Çalışan Sayısı": f"{results['system_parameters']['worker_count']}",
            }
            for label, value in system_data.items():
                st.write(f"• **{label}**: {value}")
        
        st.markdown("---")
        
        # Yağış istatistikleri
        st.subheader("🌧️ Yağış İstatistikleri")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Toplam Yağış",
                f"{results['rainfall_metrics']['total_rainfall']:.1f} mm",
            )
        
        with col2:
            st.metric(
                "Yağışlı Günler",
                f"{results['rainfall_metrics']['rainy_days']} gün",
            )
        
        with col3:
            st.metric(
                "Maks. Günlük",
                f"{results['rainfall_metrics']['max_daily']:.1f} mm",
            )
        
        with col4:
            st.metric(
                "Ort. Günlük",
                f"{results['rainfall_metrics']['average_daily']:.2f} mm",
            )
        
        st.markdown("---")
        
        # Depo performansı
        st.subheader("🏭 Depo Performansı")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Maks. Seviye",
                f"{results['tank_metrics']['max_level']:,.0f} L",
            )
        
        with col2:
            st.metric(
                "Min. Seviye",
                f"{results['tank_metrics']['min_level']:,.0f} L",
            )
        
        with col3:
            st.metric(
                "Ort. Seviye",
                f"{results['tank_metrics']['avg_level']:,.0f} L",
            )
        
        with col4:
            st.metric(
                "Verimlilik",
                f"{results['tank_metrics']['efficiency']:.1f}%",
            )
    
    # ===== SEKME 5: EKONOMİ =====
    with tab5:
        st.header("💰 Ekonomik Analiz")
        
        economic = results['economic_metrics']
        overview = economic['overview']
        water_m = economic['water_metrics']
        financial = economic['financial']
        breakeven = economic['breakeven']
        
        # Ana metrikler
        st.subheader("Mali Özet")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Tasarruf Edilen Su (₺)",
                f"₺ {financial['cost_saved']:,.0f}",
                help="Toplanan su satın almayarak tasarruf edilen para"
            )
        
        with col2:
            st.metric(
                "Toplam Yatırım",
                f"₺ {financial['total_investment']:,.0f}",
                help="Depo + Kurulum + Bakım"
            )
        
        with col3:
            st.metric(
                "Net Fayda",
                f"₺ {financial['net_benefit']:,.0f}",
                help="Tasarruf eksi maliyetler"
            )
        
        with col4:
            st.metric(
                "ROI %",
                f"{financial['roi_percentage']:.1f}%",
                help="Yatırım getiri yüzdesi"
            )
        
        st.markdown("---")
        
        # Geri ödeme analizi
        st.subheader("Geri Ödeme Analizi")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            payback = financial['payback_years']
            if payback > 0:
                st.metric(
                    "Geri Ödeme Süresi",
                    f"{payback:.2f} yıl",
                    help="Yatırımı geri kazanma süresi"
                )
            else:
                st.metric("Geri Ödeme Süresi", "Başarısız")
        
        with col2:
            is_viable = breakeven['economically_viable']
            st.metric(
                "Ekonomik Durumda Uygun",
                "✓ Evet" if is_viable else "✗ Hayır",
                help="20 yıllık sistem ömrü içinde"
            )
        
        with col3:
            annual_savings = financial.get('annual_savings', 0)
            st.metric(
                "Yıllık Tasarruf",
                f"₺ {annual_savings:,.0f}",
                help="Ortalama yıllık tasarruf"
            )
        
        st.markdown("---")
        
        # Detaylı dökme
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Maliyet Dağılımı")
            cost_data = {
                "Kurulum": f"₺ {financial['total_investment'] * 0.4:,.0f}",
                "Depo": f"₺ {depo_maliyeti:,.0f}",
                "Yıllık Bakım": f"₺ {bakım_maliyeti:,.0f}",
                "Toplam Maliyet": f"₺ {financial['total_investment']:,.0f}",
            }
            for label, value in cost_data.items():
                st.write(f"• {label}: **{value}**")
        
        with col2:
            st.subheader("Su ve Tasarrufu")
            water_data = {
                "Toplanan Su": f"{water_m['collected_liters']:,.0f} L",
                "Tüketilen Su": f"{water_m['consumed_liters']:,.0f} L",
                "Kullanım Oranı": f"{water_m['utilization_rate']:.1f}%",
                "Tasarruf Edilen Maliyet": f"₺ {financial['cost_saved']:,.0f}",
            }
            for label, value in water_data.items():
                st.write(f"• {label}: **{value}**")
        
        st.markdown("---")
        
        # Kırılgan analiz
        st.subheader("Kırılgan Noktası Analizi")
        be_col1, be_col2, be_col3 = st.columns(3)
        
        with be_col1:
            st.metric(
                "Yıllık Su Değeri",
                f"₺ {breakeven['annual_water_value']:,.0f}",
                help="Toplanan su yıllık değeri"
            )
        
        with be_col2:
            st.metric(
                "Sistem Maliyeti",
                f"₺ {breakeven['system_cost']:,.0f}",
                help="Toplam bir defalık maliyet"
            )
        
        with be_col3:
            years_be = breakeven['years_to_breakeven']
            if years_be < 100:
                st.metric(
                    "Kırılgan Noktaya Yıl",
                    f"{years_be:.2f} yıl"
                )
            else:
                st.metric("Kırılgan Noktaya Yıl", "Uygun değil")
    
    # ===== SEKME 6: DIŞA AKTAR =====
    with tab6:
        st.header("📥 Veri Dışa Aktarımı")
        
        # Günlük tarih tablosu
        st.subheader("Günlük Geçmiş")
        df_history = pd.DataFrame(results['daily_history'])
        st.dataframe(df_history, width='stretch')
        
        # CSV indir
        csv = df_history.to_csv(index=False)
        st.download_button(
            label="📥 Günlük Verileri İndir (CSV)",
            data=csv,
            file_name=f"simulation_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # JSON indir
        json_data = json.dumps(results, indent=2, default=str)
        st.download_button(
            label="📥 Simülasyon Sonuçlarını İndir (JSON)",
            data=json_data,
            file_name=f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


# ===== ALTBILGI =====
st.markdown("---")
st.markdown("""
<div style='text-align: center;'>
    <p style='color: #666;'>🌧️ Yağmur Hasadı Simülasyon Platformu | Geliştirilmiş 3D Görselleştirme | Türkçe Arayüz</p>
</div>
""", unsafe_allow_html=True)
