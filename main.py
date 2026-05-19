import asyncio
import json
from pyscript import document, window
from calculator import calculate_params

# 从 localStorage 加载历史记录
LOCAL_STORAGE_KEY = "gb2680_history_data"
history_data = []

def load_history_from_storage():
    global history_data
    try:
        stored = window.localStorage.getItem(LOCAL_STORAGE_KEY)
        if stored:
            history_data = json.loads(stored)
    except:
        history_data = []

def save_history_to_storage():
    try:
        window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(history_data))
    except Exception as e:
        print("Failed to save history to localStorage:", e)

def clear_history_click(event):
    if window.confirm("确定要清空所有历史计算记录吗？"):
        global history_data
        history_data = []
        save_history_to_storage()
        render_history()

def js_delete_history(idx):
    global history_data
    try:
        history_data.pop(int(idx))
        save_history_to_storage()
        render_history()
    except Exception as e:
        print("Delete error:", e)

# 挂载到 window 供 js 调用
window.js_delete_history = js_delete_history

def on_export_click(event):
    if not history_data:
        window.alert("暂无历史数据可导出！")
        return
        
    csv_content = "Filename,VLT(%),Tser(%),UV Block(%),VLR(%)\n"
    for item in history_data:
        vlr_str = f"{item['VLR_I']:.1f}" if item['VLR_I'] is not None else "N/A"
        csv_content += f"{item['name']},{item['VLT']:.1f},{item['TSER']:.1f},{item['UVB']:.1f},{vlr_str}\n"
        
    encoded_uri = window.encodeURI("data:text/csv;charset=utf-8,\ufeff" + csv_content)
    a = window.document.createElement("a")
    a.setAttribute("href", encoded_uri)
    a.setAttribute("download", "GB2680_history_data.csv")
    document.body.appendChild(a)
    a.click()
    a.remove()

def render_history():
    tbody = document.getElementById("history_tbody")
    if not history_data:
        tbody.innerHTML = '<tr><td colspan="6" class="text-muted py-3">（计算结果将自动保存在这里）</td></tr>'
        return
        
    html = ""
    for i, item in enumerate(history_data):
        vlr = f"{item['VLR_I']:.1f}" if item['VLR_I'] is not None else "-"
        name = item['name']
        short_name = name if len(name) <= 12 else name[:10] + "..."
        html += f"<tr><td class='text-start' title='{name}'>{short_name}</td><td>{item['VLT']:.1f}</td><td>{item['TSER']:.1f}</td><td>{item['UVB']:.1f}</td><td>{vlr}</td><td><button class='btn btn-sm btn-outline-danger py-0 px-1' onclick='window.js_delete_history({i})' title='删除'>&times;</button></td></tr>"
    tbody.innerHTML = html

def on_calculate_click(event):
    document.getElementById("results_wrapper").style.display = "none"
    document.getElementById("error_msg").innerHTML = ""
    document.getElementById("hero_vlr_box").style.display = "none"
    
    trans_file_input = document.getElementById("trans_csv")
    refl_file_input = document.getElementById("refl_csv")
    in_refl_file_input = document.getElementById("in_refl_csv")
    
    if len(trans_file_input.files) == 0 or len(refl_file_input.files) == 0:
        document.getElementById("error_msg").innerHTML = "错误: 必须上传 透光率(T%) 和 室外反射率(R%) CSV 文件。"
        return

    async def process_files():
        try:
            trans_file = trans_file_input.files.item(0)
            refl_file = refl_file_input.files.item(0)
            
            trans_text = await trans_file.text()
            refl_text = await refl_file.text()
            
            in_refl_text = None
            if len(in_refl_file_input.files) > 0:
                in_refl_file = in_refl_file_input.files.item(0)
                in_refl_text = await in_refl_file.text()
            
            # 使用算法核心模块处理
            res = calculate_params(trans_text, refl_text, in_refl_text)
            
            # 保存到历史
            file_ident = trans_file.name.replace(".csv", "").replace(".样品", "").replace(".原始数据", "").replace("-trans", "").replace("-refl-front", "")
            history_data.insert(0, {
                "name": file_ident,
                "VLT": res['VLT'],
                "TSER": res['TSER'],
                "UVB": res['UVB'],
                "VLR_I": res['VLR_I']
            })
            if len(history_data) > 100:
                history_data.pop()
            
            save_history_to_storage()
            render_history()
            
            # Layer 1
            document.getElementById("hero_vlt").innerText = f"{res['VLT']:.1f}"
            document.getElementById("hero_uvb").innerText = f"{res['UVB']:.1f}"
            document.getElementById("hero_tser").innerText = f"{res['TSER']:.1f}"
            
            if res['VLR_I'] is not None:
                document.getElementById("hero_vlr").innerText = f"{res['VLR_I']:.1f}"
                document.getElementById("hero_vlr_box").style.display = "block"
                document.getElementById("res_vlr_i").innerText = f"{res['VLR_I']:.2f} %"
                document.getElementById("row_vlr_i").className = ""
            else:
                document.getElementById("hero_vlr_box").style.display = "none"
                document.getElementById("res_vlr_i").innerText = "未提供数据"
                document.getElementById("row_vlr_i").className = "text-secondary opacity-50"
            
            # Layer 2
            document.getElementById("res_vlt").innerText = f"{res['VLT']:.2f}"
            document.getElementById("res_vlr_e").innerText = f"{res['VLR_E']:.2f}"
            document.getElementById("res_uvt").innerText = f"{res['UVT']:.2f}"
            document.getElementById("res_te").innerText = f"{res['TE']:.2f}"
            document.getElementById("res_re").innerText = f"{res['RE']:.2f}"
            document.getElementById("res_g").innerText = f"{res['G']:.2f}"
            document.getElementById("res_sc").innerText = f"{res['SC']:.3f}"
            
            document.getElementById("results_wrapper").style.display = "block"
            
                        # 保存图表数据以便在新标签页中显示
            if res.get("spectra"):
                import json
                chart_data = {
                    "fileIdent": file_ident,
                    "spectra": res["spectra"]
                }
                window.localStorage.setItem("current_chart_data", json.dumps(chart_data))
                document.getElementById("show_chart_link").style.display = "block"
            
            if hasattr(window, 'MathJax') and hasattr(window.MathJax, 'typesetPromise'):
                window.MathJax.typesetPromise()
            
        except Exception as e:
            document.getElementById("error_msg").innerHTML = f"计算出错: {str(e)}"
            
    asyncio.ensure_future(process_files())

load_history_from_storage()
render_history()

