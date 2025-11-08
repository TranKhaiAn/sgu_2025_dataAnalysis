# vn30_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- BƯỚC 1: IMPORT CHO TAB 1 & SIDEBAR (THEO TÀI LIỆU V3.x) ---
from vnstock import Vnstock, Listing 
import plotly.express as px

# (Chúng ta sẽ import Finance, Trading... cho các tab sau)

#==============================================================================
# CẤU HÌNH BAN ĐẦU
#==============================================================================
st.set_page_config(layout="wide")

@st.cache_data(ttl=3600) # Cache trong 1 giờ
def get_vn30_tickers_vnstock():
    """
    SỬA LỖI 1: Dùng hàm Listing().symbols_by_group('VN30')
    theo đúng tài liệu v3.x bạn đã cung cấp.
    """
    try:
        # Khởi tạo lớp Listing (theo tài liệu 8.13)
        # Chúng ta dùng nguồn 'TCBS' vì nó miễn phí và phổ biến
        listing = Listing(source='VCI') 
        vn30_series = listing.symbols_by_group('VN30')
        
        # SỬA LỖI: Dữ liệu trả về là một Series, không phải DataFrame.
        tickers = vn30_series.tolist()
        
        if not tickers:
             raise Exception("vnstock trả về danh sách VN30 rỗng")
        return ['-'] + sorted(tickers)
    except Exception as e:
        st.error(f"Không thể tải danh sách VN30 tự động từ vnstock: {e}. Sử dụng danh sách dự phòng.")
        # Danh sách dự phòng (fallback)
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
        """
        Tải thông tin tổng quan của công ty (theo tài liệu 8.7)
        """
        try:
            # Khởi tạo đối tượng stock BÊN TRONG hàm (để tránh lỗi cache)
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
            st.warning(f"Không tìm thấy dữ liệu tổng quan cho mã {ticker}. (API của vnstock có thể không hỗ trợ mã này).")

    # --- LẤY DỮ LIỆU BIỂU ĐỒ GIÁ ---
    @st.cache_data(ttl=600) 
    def get_stock_data(ticker_symbol):
        """
        Tải dữ liệu giá lịch sử (theo tài liệu 8.7)
        """
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        try:
            # Khởi tạo đối tượng stock BÊN TRONG hàm
            stock = Vnstock().stock(symbol=ticker_symbol, source='TCBS')
            stockdata = stock.quote.history(start=start_date, end=end_date, interval='1D')
            
            # SỬA LỖI 2: Đổi tên cột index 'time' (vnstock v3 dùng 'time')
            stockdata = stockdata.reset_index().rename(columns={"time": "date"})
            return stockdata
        except Exception as e:
            st.error(f"Lỗi khi tải dữ liệu giá: {e}")
            return pd.DataFrame()
        
    if ticker != '-':
            st.subheader("Biểu đồ Giá (5 Năm)")
            chartdata = get_stock_data(ticker) 
                       
            if not chartdata.empty:
                # SỬA LỖI 2: Dùng đúng tên cột: x='date' và y='close' (viết thường)
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
# Tab 2: Biểu đồ Kỹ thuật (Chart) - CHƯA LÀM
#==============================================================================
def tab2():
    st.title(f"Biểu đồ Kỹ thuật - {ticker}")
    st.info("Chức năng này sẽ được xây dựng ở bước tiếp theo.")

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