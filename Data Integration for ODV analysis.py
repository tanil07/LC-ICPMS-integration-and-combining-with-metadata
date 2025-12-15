# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 12:25:01 2024
@author: Chemistry/Anil Timilsina
"""
#change filename for metadata
#change filename for quantitative data
#Make sure  data column names on metadata and quantitative metadata match
#change 'end_time' to 'stop_time' if necessary based on your LC-ICPMD data integration code

import pandas as pd
import numpy as np
import re
from datetime import datetime
import os

# Load metadata and quantitative data
data_dir = 'C:/Users/Chemistry/Desktop/UMN Research/ICPMS_analysis/ICP_MS data/gp17_oce_env_old/rerun_test/'
os.chdir(data_dir)

meta = pd.read_csv(data_dir + '/temp_meta.csv')
quant_data = pd.read_csv(data_dir + '/all_results.csv')
concentration_factor = 4000  # Example sample concentration factor during SPE

def odv_integrate(metal_id='56Fe', meta=meta, quant_data=quant_data, blank_substraction=False, concentration_factor=concentration_factor):
    meta.fillna(0)
    quant_data['filename'] = quant_data['filename'].astype(str)
    meta['GT'] = meta['GT'].astype(int).astype(str)
    
    quant_data['GT'] = quant_data['filename'].str.extract(f"({'|'.join(meta['GT'])})")
    sample_data = quant_data.dropna(subset=['GT'])
    sample_data.set_index('GT', inplace=True)
    
    sample_data[metal_id] = sample_data[metal_id].astype(float, errors="ignore")
    sample_data[metal_id][sample_data[metal_id]<0]=0
    sample_data[metal_id] = sample_data[metal_id]/concentration_factor
    
    # Get unique time pairs
    time_pairs = quant_data[['start_time', 'end_time']].drop_duplicates()
    time_pairs = time_pairs.sort_values(['start_time', 'end_time'])
    
    new_cols = [f'{metal_id}_{row["start_time"]}_{row["end_time"]}' for _, row in time_pairs.iterrows()]

    matches = pd.Series(quant_data['filename']).apply(
        lambda x: [gt_id for gt_id in meta['GT'] if gt_id in str(x)]
    )
    
    matches_df = meta[meta['GT'].isin([gt_id for sublist in matches for gt_id in sublist])] 
    matches_df['filename'] = matches_df['GT'].apply(
        lambda gt: quant_data.loc[quant_data['GT'] == gt, 'filename'].values[0] if gt in quant_data['GT'].values else None
    )
    matches_df = matches_df.reindex(columns=list(matches_df.columns) + new_cols)
    matches_df.set_index('GT', inplace=True)
    
    def extract_date(filenames):
        date = re.search(r'(\d{8})', filenames)
        return date.group(1) if date else None
    
    if blank_substraction == True:
        # Extract blank file data and unique dates
        blank_list = quant_data[quant_data['filename'].str.contains('blk|blank|H2O', case=False, na=False)]
        blank_file_names = blank_list['filename']
        all_dates = blank_file_names.apply(extract_date)
        unique_dates = np.array(all_dates.unique())
        
        for _, time_pair in time_pairs.iterrows():
            start_time = time_pair['start_time']
            end_time = time_pair['end_time']
            col_name = f'{metal_id}_{start_time}_{end_time}'
            
            for date in unique_dates:
                blank_row = blank_list.loc[
                    (blank_list['start_time'].astype(int) == start_time) & 
                    (blank_list['end_time'].astype(int) == end_time) & 
                    (blank_list['filename'].str.contains(date))
                ]
                if not blank_row.empty:
                    blank_data = blank_row.iloc[0][metal_id]
                    blank_data = float(blank_data)
                    print(f'{start_time}-{end_time}: {blank_data}')
                else:
                    blank_data = 0
                
                time_data = sample_data.loc[
                    (sample_data['start_time'].astype(int, errors='ignore') == start_time) &
                    (sample_data['end_time'].astype(int, errors='ignore') == end_time)
                ]
                if blank_data > 0:
                    for index, row in time_data.iterrows():
                        sample_value = float(row[metal_id]) if isinstance(row[metal_id], (int, float, str)) else 0.0        
                        blank_subtracted = sample_value - blank_data
                        matches_df.loc[row.name, col_name] = blank_subtracted
    
    elif blank_substraction == False:
        for _, time_pair in time_pairs.iterrows():
            start_time = time_pair['start_time']
            end_time = time_pair['end_time']
            col_name = f'{metal_id}_{start_time}_{end_time}'
            
            time_data = sample_data.loc[
                (sample_data['start_time'].astype(int, errors='ignore') == start_time) &
                (sample_data['end_time'].astype(int, errors='ignore') == end_time)
            ]
            for index, row in time_data.iterrows():
                matches_df.loc[row.name, col_name] = row[metal_id]
                    
    #cols_to_sum = matches_df.filter(like=metal_id).columns
    #matches_df[f'{metal_id}_total'] = matches_df[cols_to_sum].sum(axis=1)

    return matches_df

#metals = ['56Fe_conc', '63Cu_conc', '55Mn_conc', '66Zn_conc', '59Co_conc', '60Ni_conc','27Al_conc']
metals = ['56Fe', '63Cu', '55Mn', '127I', '66Zn', '59Co', '79Br', '60Ni','31P','27Al', '69Ga']
results = [odv_integrate(metal_id=metal, concentration_factor=4000, meta=meta, quant_data=quant_data) for metal in metals]

combined_df = results[0]
for df in results[1:]:
    columns_to_add = [col for col in df.columns if col not in combined_df.columns]
    combined_df = pd.concat([combined_df, df[columns_to_add]], axis=1)

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")    

combined_df.to_csv(f'{current_time}_ODV_list.csv')
