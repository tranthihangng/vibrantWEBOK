import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import plotly.express as px
import requests
from datetime import datetime
import json

# Cấu hình trang
st.set_page_config(
    page_title="Giám sát Động cơ",
    page_icon="🔄",
    layout="wide"
)

# Cấu hình API endpoint
API_URL = st.secrets.get("API_URL", "http://localhost:5000")  # Có thể thay đổi trong Streamlit Cloud

# Định nghĩa các màu trạng thái
STATUS_COLORS = {
    'normal': '#28a745',
    'rung_6': '#ffc107',
    'rung_12_5': '#dc3545',
    'stop': '#6c757d'
}

STATUS_LABELS = {
    'normal': 'Bình thường',
    'rung_6': 'Lỗi 1(rung nhẹ)',
    'rung_12_5': 'Lỗi 2(rung nặng)',
    'stop': 'Dừng'
}

@st.cache_data(ttl=5)  # Cache data for 5 seconds
def load_data():
    try:
        response = requests.get(f"{API_URL}/api/status")
        data = response.json()
        data['last_updated'] = datetime.strptime(data['last_updated'], '%Y-%m-%d %H:%M:%S')
        return data
    except Exception as e:
        st.error(f"Không thể kết nối với máy chủ: {str(e)}")
        return None

@st.cache_data(ttl=60)  # Cache data for 1 minute
def load_daily_stats():
    try:
        response = requests.get(f"{API_URL}/api/daily-stats")
        return response.json()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu thống kê: {str(e)}")
        return None

@st.cache_data(ttl=60)  # Cache data for 1 minute
def load_heatmap_data():
    try:
        response = requests.get(f"{API_URL}/api/heatmap-data")
        return response.json()
    except Exception as e:
        st.error(f"Không thể tải dữ liệu heatmap: {str(e)}")
        return None

def create_status_card(status_data):
    if not status_data:
        st.error("Không có dữ liệu trạng thái")
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Trạng thái Động cơ")
        status = status_data['status']
        color = STATUS_COLORS[status]
        
        st.markdown(
            f"""
            <div style='background-color: {color}20; padding: 20px; border-radius: 10px; border: 2px solid {color}'>
                <h2 style='color: {color}; text-align: center; margin: 0;'>
                    {STATUS_LABELS[status]}
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(f"*Cập nhật lần cuối: {status_data['last_updated'].strftime('%H:%M:%S %d/%m/%Y')}*")
        
        st.markdown("#### Xác suất các trạng thái:")
        for state, prob in status_data['probabilities'].items():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.progress(prob)
            with col2:
                st.write(f"{prob*100:.1f}%")

def create_daily_stats():
    data = load_daily_stats()
    if not data:
        return

    st.markdown("### Thống kê 7 ngày qua")
    
    # Chuyển đổi dữ liệu
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Tạo stacked bar chart
    fig = go.Figure()
    for status in STATUS_LABELS.keys():
        fig.add_trace(go.Bar(
            name=STATUS_LABELS[status],
            x=df['date'],
            y=df[f'{status}_count'],
            marker_color=STATUS_COLORS[status]
        ))
    
    fig.update_layout(
        barmode='stack',
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_status_heatmap():
    data = load_heatmap_data()
    if not data:
        return

    st.markdown("### Phân bố trạng thái theo giờ")
    
    # Chuyển đổi dữ liệu
    df = pd.DataFrame(data)
    df['total'] = df['normal_count'] + df['rung_6_count'] + df['rung_12_5_count'] + df['stop_count']
    
    fig = px.density_heatmap(
        df,
        x='hour',
        y='date',
        z='total',
        color_continuous_scale=[
            [0, 'white'],
            [1, STATUS_COLORS['normal']]
        ],
        labels={'hour': 'Giờ', 'date': 'Ngày', 'total': 'Số lượng'}
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    # Tải dữ liệu
    status_data = load_data()
    
    # Hiển thị status card
    create_status_card(status_data)
    
    # Tạo layout cho biểu đồ
    col1, col2 = st.columns([1, 1])
    
    with col1:
        create_daily_stats()
    
    with col2:
        create_status_heatmap()

    # Auto-refresh
    st.empty()
    st.experimental_rerun()

if __name__ == "__main__":
    main() 