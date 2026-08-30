import pandas as pd
import numpy as np
from constants import UV_WEIGHTS, UV_SUM, VIS_WEIGHTS, VIS_SUM, SOLAR_WEIGHTS, SOLAR_SUM, QC_HE, QC_HI

def parse_csv_content(csv_string):
    try:
        from io import StringIO
        lines = [line.strip() for line in csv_string.strip().splitlines() if line.strip() and not line.strip().startswith('#')]
        cleaned_csv = "\n".join(lines)
        df = pd.read_csv(StringIO(cleaned_csv), skipinitialspace=True)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # 识别波长列
        wl_candidates = [c for c in df.columns if 'nm' in c or 'wave' in c or 'lambda' in c or 'wl' in c]
        wl_col = wl_candidates[0] if wl_candidates else df.columns[0]
        
        # 识别数值列（必须排除波长列）
        other_cols = [c for c in df.columns if c != wl_col]
        if not other_cols:
            raise ValueError("CSV 文件至少需包含波长列和测试数据列。")
            
        val_candidates = [c for c in other_cols if '%t' in c or '%r' in c or 'trans' in c or 'refl' in c or '%' in c or 't' in c or 'r' in c or 'val' in c]
        val_col = val_candidates[0] if val_candidates else other_cols[0]
        
        df = df[[wl_col, val_col]].dropna()
        df[wl_col] = pd.to_numeric(df[wl_col], errors='coerce')
        df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
        df = df.dropna().sort_values(by=wl_col).set_index(wl_col)
        
        series = df[val_col]
        # 若为百分数(0-100)则转为 0-1 比例，若已为 0-1 比例则保持不变
        if series.max() > 1.0:
            series = series / 100.0
        return series
    except Exception as e:
        raise ValueError(f"解析 CSV 失败，请检查文件格式。({e})")

def calculate_params(trans_csv_content, refl_csv_content, in_refl_csv_content=None):
    tau_series = parse_csv_content(trans_csv_content)
    rho_series = parse_csv_content(refl_csv_content)
    rho_i_series = parse_csv_content(in_refl_csv_content) if in_refl_csv_content else None
    
    def interpolate_val(wl, series):
        try:
            # 使用 np.interp 确保无论如何均安全返回纯 Python float 标量
            return float(np.interp(wl, series.index.values, series.values))
        except Exception:
            return 0.0

    vlt_sum = 0
    vlr_e_sum = 0
    vlr_i_sum = 0
    for wl, wt in VIS_WEIGHTS.items():
        vlt_sum += interpolate_val(wl, tau_series) * wt
        vlr_e_sum += interpolate_val(wl, rho_series) * wt
        if rho_i_series is not None:
            vlr_i_sum += interpolate_val(wl, rho_i_series) * wt
            
    vlt = vlt_sum / VIS_SUM
    vlr_e = vlr_e_sum / VIS_SUM
    vlr_i = (vlr_i_sum / VIS_SUM) if rho_i_series is not None else None
    
    uvt_sum = 0
    for wl, wt in UV_WEIGHTS.items():
        uvt_sum += interpolate_val(wl, tau_series) * wt
    uvt = uvt_sum / UV_SUM
    
    te_sum = 0
    re_sum = 0
    for wl, wt in SOLAR_WEIGHTS.items():
        te_sum += interpolate_val(wl, tau_series) * wt
        re_sum += interpolate_val(wl, rho_series) * wt
        
    te = te_sum / SOLAR_SUM
    re = re_sum / SOLAR_SUM
    
    ae = 1.0 - te - re
    qi = ae * (QC_HI / (QC_HE + QC_HI))
    g_value = te + qi
    sc = g_value / 0.87
    
    res = {
        "VLT": vlt * 100,
        "VLR_E": vlr_e * 100,
        "VLR_I": (vlr_i * 100) if vlr_i is not None else None,
        "UVT": uvt * 100,
        "UVB": (1.0 - uvt) * 100,
        "TE": te * 100,
        "RE": re * 100,
        "G": g_value * 100,
        "TSER": (1.0 - g_value) * 100,
        "SC": sc
    }
    
    # 尝试加载 CIE241 并生成光谱数组
    spectra_data = None
    try:
        cie_path = "CIE241_H1_5nm.csv"
        try:
            cie_df = pd.read_csv(cie_path)
        except Exception:
            cie_df = pd.read_csv("./" + cie_path)
            
        cie_df.columns = ['wl', 'irr']
        cie_df = cie_df[(cie_df['wl'] >= 300) & (cie_df['wl'] <= 2500)]
        
        wl_arr = cie_df['wl'].values.astype(float)
        irr_arr = cie_df['irr'].values.astype(float)
        
        tau_arr = np.array([interpolate_val(w, tau_series) for w in wl_arr], dtype=float)
        rho_arr = np.array([interpolate_val(w, rho_series) for w in wl_arr], dtype=float)
        
        direct_arr = irr_arr * tau_arr
        
        alpha_arr = 1.0 - tau_arr - rho_arr
        qi_arr = alpha_arr * (QC_HI / (QC_HE + QC_HI))
        total_arr = irr_arr * (tau_arr + qi_arr)
        
        spectra_data = {
            "wl": [float(x) for x in wl_arr],
            "irr": [float(x) for x in irr_arr],
            "direct": [float(x) for x in direct_arr],
            "total": [float(x) for x in total_arr]
        }
    except Exception as e:
        print("CIE file error:", e)
        pass
        
    res["spectra"] = spectra_data
    return res
