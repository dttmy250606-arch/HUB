import streamlit as st
import numpy as np
from typing import List, Optional
import pandas as pd 

class Node:
    def __init__(self, is_leaf: bool = False):
        self.keys: List[str] = []
        self.children: List[Node] = []
        self.is_leaf: bool = is_leaf
        self.next: Optional[Node] = None
        self.data: List[np.ndarray] = []

class BPlusTree:
    def __init__(self, order: int = 4):
        self.root: Node = Node(is_leaf=True)
        self.order: int = order

    def search(self, key: str) -> Optional[np.ndarray]:
        current = self.root
        while not current.is_leaf:
            idx = self._find_child_index(current, key)
            current = current.children[idx]
        try:
            key_idx = current.keys.index(key)
            return current.data[key_idx]
        except ValueError:
            return None

    def _find_child_index(self, node: Node, key: str) -> int:
        for i, k in enumerate(node.keys):
            if key < k:
                return i
        return len(node.children) - 1

    def insert(self, key: str, price_data: np.ndarray):
        current = self.root
        while not current.is_leaf:
            idx = self._find_child_index(current, key)
            current = current.children[idx]
        self._insert_into_leaf(current, key, price_data)

    def _insert_into_leaf(self, leaf: Node, key: str, data: np.ndarray):
        if key in leaf.keys:
            return 
        insert_idx = 0
        while insert_idx < len(leaf.keys) and leaf.keys[insert_idx] < key:
            insert_idx += 1
        leaf.keys.insert(insert_idx, key)
        leaf.data.insert(insert_idx, data)

    def batch_insert_stock_data(self, stock_symbols: List[str], price_histories: List[np.ndarray]):
        for symbol, prices in zip(stock_symbols, price_histories):
            self.insert(symbol, prices)

    def get_tree_structure(self, node: Optional[Node] = None, level: int = 0) -> str:
        if node is None:
            node = self.root
        
        indent = "    " * level
        node_type = "LEAF" if node.is_leaf else "INTERNAL"
        output = f"{indent}{node_type} | Keys: {node.keys}\n"

        if not node.is_leaf:
            for child in node.children:
                output += self.get_tree_structure(child, level + 1)
        return output

class StockPriceQuerySystem:
    def __init__(self):
        self.bplus_tree = BPlusTree(order=4)
        self._sample_data()

    def _sample_data(self):
        np.random.seed(42)
        stock_symbols = ['VIC', 'VHM', 'VRE', 'MSN', 'HPG', 'FPT', 'CTG', 'MBB', 'VCB', 'ACB']
        price_histories = []
        for symbol in stock_symbols:
            base_price = np.random.uniform(30, 150)
            daily_returns = np.random.normal(0.001, 0.02, 30)
            prices = base_price * np.cumprod(1 + daily_returns)
            prices = np.round(prices, 2)
            price_histories.append(prices)
        self.bplus_tree.batch_insert_stock_data(stock_symbols, price_histories)

    def query_stock_price(self, symbol: str):
        return self.bplus_tree.search(symbol)

    def get_all_stocks(self):
        stocks = {}
        current = self.bplus_tree.root
        while not current.is_leaf:
            current = current.children[0]
        while current:
            for key, data in zip(current.keys, current.data):
                stocks[key] = data
            current = current.next
        return stocks

st.set_page_config(page_title="Hệ thống Giá Cổ Phiếu B+ Tree", layout="wide")

if 'system' not in st.session_state:
    st.session_state.system = StockPriceQuerySystem()

with st.sidebar:
    st.header("Menu Chức năng")
    option = st.radio("Chọn thao tác:", ["Tra cứu Cổ phiếu", "So sánh Cổ phiếu", "Cấu trúc B+ Tree"])
    st.info("Hệ thống sử dụng cấu trúc dữ liệu B+ Tree để lưu trữ và truy xuất lịch sử giá.")

system = st.session_state.system

if option == "Tra cứu Cổ phiếu":
    st.title("Tra cứu Lịch sử Giá")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        search_symbol = st.text_input("Nhập mã cổ phiếu (VD: VIC, FPT):", "").upper()
        search_btn = st.button("Tìm kiếm")

    if search_btn and search_symbol:
        prices = system.query_stock_price(search_symbol)
        
        if prices is not None:
            curr_price = prices[-1]
            prev_price = prices[-2]
            delta = curr_price - prev_price
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Mã CP", search_symbol)
            c2.metric("Giá hiện tại", f"{curr_price:,.2f}", f"{delta:,.2f}")
            c3.metric("Biến động (Vol)", f"{np.std(prices):.4f}")

            st.subheader(f"Biểu đồ giá 30 ngày qua của {search_symbol}")
            
            chart_data = pd.DataFrame(prices, columns=["Giá đóng cửa"])
            st.line_chart(chart_data)
            
            with st.expander("Xem dữ liệu chi tiết"):
                st.write(prices)
        else:
            st.error(f"Không tìm thấy mã cổ phiếu '{search_symbol}' trong cây B+ Tree.")

elif option == "So sánh Cổ phiếu":
    st.title("So sánh Hiệu suất")
    
    all_stocks = system.get_all_stocks()
    selected_symbols = st.multiselect("Chọn các mã cổ phiếu:", list(all_stocks.keys()), default=['VIC', 'FPT'])
    
    if selected_symbols:
        df_compare = pd.DataFrame()
        for sym in selected_symbols:
            df_compare[sym] = all_stocks[sym]
        
        st.subheader("Biểu đồ so sánh giá")
        st.line_chart(df_compare)
        
        st.subheader("Bảng thống kê")
        st.dataframe(df_compare.describe())

elif option == "Cấu trúc B+ Tree":
    st.title("Trực quan hóa Cấu trúc Dữ liệu")
    
    st.markdown("""
    Dưới đây là cấu trúc hiện tại của cây B+ trong bộ nhớ. 
    - **INTERNAL**: Node chỉ chứa key điều hướng.
    - **LEAF**: Node chứa dữ liệu thực tế (Linked List).
    """)
    
    # Lấy string cấu trúc cây
    tree_str = system.bplus_tree.get_tree_structure()
    
    # Hiển thị trong khung code
    st.code(tree_str, language="text")
    
    st.warning("Lưu ý: Đây là phiên bản Simple B+ Tree (chưa implement split node đầy đủ).")
