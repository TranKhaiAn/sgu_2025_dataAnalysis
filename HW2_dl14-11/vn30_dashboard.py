# vn30_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests

# --- BƯỚC 1: IMPORT CÁC THƯ VIỆN ---
from vnstock import Vnstock, Listing 
import plotly.express as px
# SỬA LỖI: Import thêm thư viện cho Tab 2
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#==============================================================================
# CẤU HÌNH BAN ĐẦU
#==============================================================================
st.set_page_config(layout="wide")

@st.cache_data(ttl=3600) 
def get_vn30_tickers_vnstock():
    """
    Dùng hàm Listing(source='VCI') để lấy danh sách VN30.
    """
    try:
        # SỬA LỖI: Dùng nguồn 'VCI' như bạn đã xác nhận
        listing = Listing(source='VCI') 
        vn30_series = listing.symbols_by_group('VN30')
        tickers = vn30_series.tolist()
        if not tickers:
             raise Exception("vnstock trả về danh sách VN30 rỗng")
        return ['-'] + sorted(tickers)
    except Exception as e:
        st.error(f"Không thể tải danh sách VN30 tự động từ vnstock: {e}. Sử dụng danh sách dự phòng.")
        return [
            '-', 'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG', 
            'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'SAB', 'SSI', 'STB', 'TCB', 'TPB', 
            'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE', 'SHB'
        ]

VN30_TICKERS = get_vn30_tickers_vnstock()

#==============================================================================
# Tab 1: Tổng quan (Summary) - ĐÃ HOÀN THIỆN
#==============================================================================
def tab1():
    st.title(f"Tổng quan - {ticker}")

    # --- LẤY DỮ LIỆU THÔNG TIN CÔNG TY ---
    @st.cache_data(ttl=3600) 
    def get_summary_data(ticker_symbol):
        try:
            stock = Vnstock().stock(symbol=ticker_symbol, source='TCBS')
            overview = stock.company.overview()
            overview_df = overview.T
            if overview_df.empty:
                return pd.DataFrame()
            overview_df.columns = ['Giá trị']
            return overview_df
        except Exception:
            return pd.DataFrame()

    if ticker != '-':
        summary_df = get_summary_data(ticker)
        
        if not summary_df.empty:
            st.subheader("Thông tin Cơ bản Doanh nghiệp")
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.warning(f"Không tìm thấy dữ liệu tổng quan cho mã {ticker}.")

    # --- LẤY DỮ LIỆU BIỂU ĐỒ GIÁ ---
    @st.cache_data(ttl=600) 
    def get_stock_data(ticker_symbol):
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        try:
            stock = Vnstock().stock(symbol=ticker_symbol, source='VCI') # Dùng VCI cho đồng bộ
            stockdata = stock.quote.history(start=start_date, end=end_date, interval='1D')
            stockdata = stockdata.reset_index().rename(columns={"time": "date"})
            return stockdata
        except Exception as e:
            st.error(f"Lỗi khi tải dữ liệu giá: {e}")
            return pd.DataFrame()
        
    if ticker != '-':
            st.subheader("Biểu đồ Giá (5 Năm)")
            chartdata = get_stock_data(ticker) 
                       
            if not chartdata.empty:
                fig = px.area(chartdata, x='date', y='close', title=f"Biểu đồ Giá Đóng cửa của {ticker}")
                
                fig.update_xaxes(title_text='Ngày')
                fig.update_yaxes(title_text='Giá (VND)')
                
                fig.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1Th", step="month", stepmode="backward"),
                            dict(count=3, label="3Th", step="month", stepmode="backward"),
                            dict(count=6, label="6Th", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1N", step="year", stepmode="backward"),
                            dict(count=3, label="3N", step="year", stepmode="backward"),
                            dict(label="Tất cả", step="all")
                        ])
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Không thể tải được dữ liệu biểu đồ giá cho mã {ticker}.")

#==============================================================================
# Tab 2: Biểu đồ Kỹ thuật (Chart) - ĐÃ HOÀN THIỆN
#==============================================================================
def tab2():
    st.title(f"Biểu đồ Kỹ thuật - {ticker}")
    
    # --- TÙY CHỌN ĐẦU VÀO ---
    c1, c2, c3, c4 = st.columns((1,1,1,1))
    
    with c1:
        start_date = st.date_input("Ngày bắt đầu", datetime.today().date() - timedelta(days=365))
    with c2:
        end_date = st.date_input("Ngày kết thúc", datetime.today().date())        
    with c3: 
        # vnstock hỗ trợ '1D', '1W', '1M'
        inter = st.selectbox("Chọn Tần suất", ['1D', '1W', '1M'], key="tab2_interval") 
    with c4:
        plot_type = st.selectbox("Chọn Loại Biểu đồ", ['Đường (Line)', 'Nến (Candle)'], key="tab2_plot")
        
    # --- HÀM LẤY DỮ LIỆU ---
    @st.cache_data            
    def get_chart_data(ticker_symbol, start_date, end_date, interval):
        try:
            # Chuyển đổi định dạng ngày tháng
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Khởi tạo đối tượng stock
            stock = Vnstock().stock(symbol=ticker_symbol, source='VCI')
            # Lấy dữ liệu
            chartdata = stock.quote.history(start=start_str, end=end_str, interval=interval)
            
            # Tính SMA 50
            chartdata['SMA_50'] = chartdata['close'].rolling(50).mean()
            
            # Reset index để có cột 'time' (hoặc 'date')
            chartdata = chartdata.reset_index().rename(columns={"time": "date"})
            
            return chartdata
        except Exception as e:
            st.error(f"Lỗi tải dữ liệu biểu đồ: {e}")
            return pd.DataFrame()
    
    if ticker != '-':
        chartdata = get_chart_data(ticker, start_date, end_date, inter) 
        
        if not chartdata.empty:
            # --- VẼ BIỂU ĐỒ ---
            # Sử dụng subplots để có 2 trục y (Giá và Khối lượng)
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Thêm Biểu đồ Nến hoặc Đường
            if plot_type == 'Đường (Line)':
                fig.add_trace(go.Scatter(x=chartdata['date'], y=chartdata['close'], mode='lines', 
                                         name = 'Giá Đóng cửa'), secondary_y = False)
            else:
                fig.add_trace(go.Candlestick(x = chartdata['date'], open = chartdata['open'], 
                                             high = chartdata['high'], low = chartdata['low'], 
                                             close = chartdata['close'], name = 'Giá (Nến)'), 
                                             secondary_y = False)
          
            # Thêm đường SMA 50
            fig.add_trace(go.Scatter(x=chartdata['date'], y=chartdata['SMA_50'], mode='lines', 
                                     name = 'SMA 50', line=dict(color='orange', dash='dash')), 
                                     secondary_y = False)
            
            # Thêm Biểu đồ Khối lượng (Volume) vào trục y thứ 2
            fig.add_trace(go.Bar(x = chartdata['date'], y = chartdata['volume'], name = 'Khối lượng'), secondary_y = True)

            fig.update_layout(
                title=f"Biểu đồ Kỹ thuật {ticker} ({inter})",
                yaxis_title="Giá (VND)",
                xaxis_title="Ngày",
                legend_title="Chú thích",
                xaxis_rangeslider_visible=False # Ẩn thanh trượt mặc định khi dùng nến
            )
            # Ẩn nhãn của trục y thứ 2 (khối lượng) và điều chỉnh
            fig.update_yaxes(range=[0, chartdata['volume'].max()*3], showticklabels=False, secondary_y=True)
        
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Không có dữ liệu cho khoảng thời gian/tần suất đã chọn.")

#==============================================================================
# Tab 3: Thống kê (Statistics) - CHƯA LÀM
#==============================================================================
def tab3():
    st.title(f"Thống kê Chi tiết - {ticker}")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

#==============================================================================
# Tab 4: Báo cáo Tài chính (Financials) - CHƯA LÀM
#==============================================================================
def tab4():
    st.title(f"Báo cáo Tài chính - {ticker}")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

#==============================================================================
# Tab 5: Phân tích (Analysis) - CHƯA LÀM
#==============================================================================
def tab5():
    st.title(f"Phân tích & Khuyến nghị - {ticker}")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

#==============================================================================
# Tab 6: Mô phỏng Monte Carlo - CHƯA LÀM
#==============================================================================
def tab6():
    st.title(f"Mô phỏng Monte Carlo - {ticker}")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

#==============================================================================
# Tab 7: Xu hướng Portfolio - CHƯA LÀM
#==============================================================================
def tab7():
    st.title("Xu hướng Portfolio (5 Năm)")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

#==============================================================================
# Hàm RUN chính của ứng dụng
#==============================================================================
def run():
    
    st.sidebar.title("Bảng điều khiển FinDash 🇻🇳")
    
    global ticker
    ticker = st.sidebar.selectbox("Chọn cổ phiếu VN-30", VN30_TICKERS)
    
    select_tab = st.sidebar.radio("Chọn chức năng", 
                                  ['Tổng quan', 'Biểu đồ Kỹ thuật', 'Thống kê', 
                                   'Báo cáo Tài chính', 'Phân tích', 
                                   'Mô phỏng Monte Carlo', "Xu hướng Portfolio"])
    
    # Xử lý logic hiển thị Tab
    if select_tab == 'Tổng quan':
        if ticker == '-':
            st.warning("Vui lòng chọn một mã cổ phiếu từ thanh bên trái.")
        else:
            tab1()
    elif select_tab == 'Biểu đồ Kỹ thuật':
        if ticker == '-':
            st.warning("Vui lòng chọn một mã cổ phiếu từ thanh bên trái.")
        else:
            tab2()
    # (Các tab khác sẽ được xử lý tương tự)
    else:
        if ticker == '-':
            st.warning("Vui lòng chọn một mã cổ phiếu từ thanh bên trái.")
        else:
            tabs = {
                'Thống kê': tab3,
                'Báo cáo Tài chính': tab4,
                'Phân tích': tab5,
                'Mô phỏng Monte Carlo': tab6
            }
            if select_tab in tabs:
                tabs[select_tab]()
        
        if select_tab == "Xu hướng Portfolio":
            tab7()
       
if __name__ == "__main__":
    run()