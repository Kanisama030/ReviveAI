import pandas as pd

def process_carbon_catalogue(excel_file_path, output_csv_path):
    """
    處理Carbon Catalogue資料庫，清理數據並轉換為CSV格式
    """
    print("開始讀取Excel檔案...")
    # 1. 讀取Excel數據
    try:
        df = pd.read_excel(excel_file_path, sheet_name="Product Level Data")
        print(f"成功讀取Excel，共有{len(df)}行數據")
    except Exception as e:
        print(f"讀取Excel出錯: {e}")
        return
    
    # 2. 選擇所需欄位並重命名
    selected_columns = {
        '*PCF-ID': 'product_id',
        'Product name (and functional unit)': 'product_name',
        'Product detail': 'product_detail',
        'Company': 'company',
        '*Company\'s sector': 'sector',
        'Product weight (kg)': 'weight_kg',
        'Product\'s carbon footprint (PCF, kg CO2e)': 'carbon_footprint',
        'Country (where company is incorporated)': 'country',
        'Year of reporting': 'year'
    }
    
    try:
        # 檢查所有欄位是否存在
        missing_columns = [col for col in selected_columns.keys() if col not in df.columns]
        if missing_columns:
            print(f"警告: 以下欄位在Excel中不存在: {missing_columns}")
            # 從selected_columns中移除不存在的欄位
            for col in missing_columns:
                selected_columns.pop(col)
        
        # 選擇欄位並重命名
        cleaned_df = df[selected_columns.keys()].rename(columns=selected_columns)
        print(f"選擇並重命名欄位完成，保留{len(selected_columns)}個欄位")
    except Exception as e:
        print(f"選擇欄位時出錯: {e}")
        return
    
    # 3. 清理產品名稱和描述
    print("開始清理產品名稱和描述...")
    
    def clean_product_text(row):
        """清理產品名稱和描述文本"""
        try:
            name = str(row['product_name']).strip()
            detail = str(row['product_detail']).strip()
            
            # 處理 NaN 或空值情況
            if pd.isna(row['product_detail']) or detail.lower() in ['nan', '', 'field not included in 2013 data']:
                detail = '[no detail provided]'
            
            if pd.isna(row['product_name']) or name.lower() == 'nan':
                return None, None  # 產品名稱為空時返回 None
            
            if len(name) > 50:
                words = name.split()
                for i, word in enumerate(words):
                    if word.lower() == 'is':
                        possible_name = ' '.join(words[:i])
                        if possible_name and len(possible_name) < len(name):
                            return possible_name, name
                        break
            
            words = detail.split()
            if len(words) >= 4:
                first_two = ' '.join(words[:2])
                next_two = ' '.join(words[2:4])
                if first_two == next_two:
                    detail = ' '.join(words[2:])
                    name = first_two
            
            return name, detail
        except Exception as e:
            print(f"清理文本時出錯: {e}")
            return str(row['product_name']), str(row['product_detail'])
    
    try:
        # 應用清理函數
        cleaned_texts = cleaned_df.apply(clean_product_text, axis=1)
        cleaned_df['product_name'] = [x[0] for x in cleaned_texts]
        cleaned_df['product_detail'] = [x[1] for x in cleaned_texts]
        
        # 移除產品名稱為 None 的行
        cleaned_df = cleaned_df.dropna(subset=['product_name'])
        print(f"清理後保留{len(cleaned_df)}行數據")
        
        # 確保 product_detail 不為 NaN
        cleaned_df['product_detail'] = cleaned_df['product_detail'].fillna('[no detail provided]')
    except Exception as e:
        print(f"應用清理函數時出錯: {e}")
        return
    
    # 4. 處理重複的產品描述文本
    print("處理產品描述重複問題...")
    cleaned_df.loc[cleaned_df['product_detail'] == cleaned_df['product_name'], 'product_detail'] = '[same as product_name]'
    
    # 5. 處理相同產品在不同年份的問題
    print("處理相同產品在不同年份的問題...")
    try:
        # 按照產品ID的模式提取產品基本標識符(去除年份部分)
        cleaned_df['product_base_id'] = cleaned_df['product_id'].str.extract(r'(.*)-\d+-\d+')
        
        # 標記為相同產品的最新年份
        cleaned_df['is_latest'] = cleaned_df.groupby('product_base_id')['year'].transform('max') == cleaned_df['year']
        
        # 檢查是否有重複產品
        duplicate_count = cleaned_df[~cleaned_df['is_latest']].shape[0]
        print(f"找到{duplicate_count}個舊版本產品(非最新年份)")
        
        # 只保留最新年份的產品版本
        latest_df = cleaned_df[cleaned_df['is_latest']]
        print(f"保留最新版本後剩餘{len(latest_df)}行數據")
        
        # 移除臨時列
        latest_df = latest_df.drop(columns=['product_base_id', 'is_latest'])
    except Exception as e:
        print(f"處理重複產品時出錯: {e}")
        # 如果出錯，使用原始清理後的數據繼續
        latest_df = cleaned_df
    
    # 6. 數據類型轉換
    print("數據類型轉換...")
    try:
        # 確保數值欄位為數值類型
        numeric_columns = ['weight_kg', 'carbon_footprint', 'year']
        for col in numeric_columns:
            if col in latest_df.columns:
                latest_df[col] = pd.to_numeric(latest_df[col], errors='coerce')
        
        # 移除碳足跡為空的行
        final_df = latest_df.dropna(subset=['carbon_footprint'])
        print(f"移除無效碳足跡後剩餘{len(final_df)}行數據")
    except Exception as e:
        print(f"數據類型轉換時出錯: {e}")
        final_df = latest_df
    
    # 7. 保存為CSV
    print(f"保存處理後的數據到{output_csv_path}...")
    try:
        final_df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print("資料處理完成!")
        return final_df
    except Exception as e:
        print(f"保存CSV時出錯: {e}")
        return final_df

# 使用範例
processed_data = process_carbon_catalogue("carbon_catalogue.xlsx", "cleaned_carbon_catalogue.csv")