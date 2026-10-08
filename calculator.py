import csv
from bisect import bisect_left
from io import StringIO

from constants import UV_WEIGHTS, UV_SUM, VIS_WEIGHTS, VIS_SUM, SOLAR_WEIGHTS, SOLAR_SUM, QC_HE, QC_HI

def parse_csv_content(csv_string):
    try:
        lines = [line.strip() for line in csv_string.strip().splitlines() if line.strip() and not line.strip().startswith('#')]
        rows = list(csv.reader(StringIO("\n".join(lines)), skipinitialspace=True))
        if not rows:
            raise ValueError("CSV 文件为空。")

        headers = [str(value).strip().lower() for value in rows[0]]
        data_rows = [row for row in rows[1:] if len(row) >= len(headers)]
        
        # 识别波长列
        wl_candidates = [i for i, name in enumerate(headers) if 'nm' in name or 'wave' in name or 'lambda' in name or 'wl' in name]
        wl_index = wl_candidates[0] if wl_candidates else 0
        
        # 识别数值列（必须排除波长列）
        other_indices = [i for i in range(len(headers)) if i != wl_index]
        if not other_indices:
            raise ValueError("CSV 文件至少需包含波长列和测试数据列。")
            
        val_candidates = [i for i in other_indices if '%t' in headers[i] or '%r' in headers[i] or 'trans' in headers[i] or 'refl' in headers[i] or '%' in headers[i] or headers[i] in ('t', 'r') or 'val' in headers[i]]
        val_index = val_candidates[0] if val_candidates else other_indices[0]
        series = []
        for row in data_rows:
            try:
                series.append((float(row[wl_index]), float(row[val_index])))
            except (TypeError, ValueError):
                continue
        if not series:
            raise ValueError("CSV 文件中没有有效数值。")
        series.sort()

        # 若为百分数(0-100)则转为 0-1 比例，若已为 0-1 比例则保持不变
        if max(value for _, value in series) > 1.0:
            series = [(wavelength, value / 100.0) for wavelength, value in series]
        return series
    except Exception as e:
        raise ValueError(f"解析 CSV 失败，请检查文件格式。({e})")

def calculate_params(trans_csv_content, refl_csv_content, in_refl_csv_content=None):
    tau_series = parse_csv_content(trans_csv_content)
    rho_series = parse_csv_content(refl_csv_content)
    rho_i_series = parse_csv_content(in_refl_csv_content) if in_refl_csv_content else None
    
    def interpolate_val(wl, series):
        try:
            wavelengths = [item[0] for item in series]
            values = [item[1] for item in series]
            position = bisect_left(wavelengths, wl)
            if position <= 0:
                return values[0]
            if position >= len(wavelengths):
                return values[-1]
            left_wavelength, right_wavelength = wavelengths[position - 1], wavelengths[position]
            left_value, right_value = values[position - 1], values[position]
            ratio = (wl - left_wavelength) / (right_wavelength - left_wavelength)
            return float(left_value + ratio * (right_value - left_value))
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
        with open(cie_path, newline="", encoding="utf-8-sig") as cie_file:
            cie_rows = csv.reader(cie_file)
            next(cie_rows, None)
            cie_data = []
            for row in cie_rows:
                try:
                    wavelength, irradiance = float(row[0]), float(row[1])
                    if 300 <= wavelength <= 2500:
                        cie_data.append((wavelength, irradiance))
                except (IndexError, TypeError, ValueError):
                    continue

        wl_arr = [wavelength for wavelength, _ in cie_data]
        irr_arr = [irradiance for _, irradiance in cie_data]
        tau_arr = [interpolate_val(w, tau_series) for w in wl_arr]
        rho_arr = [interpolate_val(w, rho_series) for w in wl_arr]
        direct_arr = [irr * tau for irr, tau in zip(irr_arr, tau_arr)]
        total_arr = []
        for irr, tau, rho in zip(irr_arr, tau_arr, rho_arr):
            alpha = 1.0 - tau - rho
            qi = alpha * (QC_HI / (QC_HE + QC_HI))
            total_arr.append(irr * (tau + qi))
        
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
