import asyncio
import json
from pyscript import document, window
from calculator import calculate_params

try:
    from pyodide.ffi import create_proxy
except Exception:
    create_proxy = None

# 使用 IndexedDB 保存历史记录，storage.js 提供 localStorage 降级与旧数据迁移
COMPARE_SELECTION_KEY = "gb2680_compare_selection"
history_data = []
compare_selection = []
_event_proxies = []
_calc_in_progress = False

            try {
                data = JSON.parse(rawData);
                // 兼容：如果 data 仍然是字符串（被双重序列化），再尝试解析一次
                if (typeof data === 'string') {
                    try {
                        data = JSON.parse(data);
                    } catch (e2) {
                        // 如果仍然无法解析，留作原样（下面会判定无效并退出）
                    }
                }
            } catch(e) {
                document.getElementById('no_data').style.display = 'block';
                return;
            }

            // 如果没有有效的谱图对象或波长数组，显示无数据提示并退出
            if (!data || !data.spectra || !Array.isArray(data.spectra.wl) || data.spectra.wl.length === 0) {
                document.getElementById('no_data').style.display = 'block';
                return;
            }

async def save_history_to_storage():
    try:
        window.gb2680Storage.saveHistory(history_data)
    except Exception as e:
        print("Failed to save history to IndexedDB:", e)

def clear_history_click(event):
    if window.confirm("确定要清空所有历史计算记录吗？"):
        global history_data
        history_data = []
        compare_selection.clear()
        window.localStorage.removeItem(COMPARE_SELECTION_KEY)
        window.gb2680Storage.clearHistory()
        render_history()

def js_delete_history(idx):
    global history_data
    try:
        history_data.pop(int(idx))
        window.gb2680Storage.saveHistory(history_data)
        render_history()
    except Exception as e:
        print("Delete error:", e)

# 挂载到 window 供 js 调用
window.js_delete_history = js_delete_history

def update_right_panel(res):
    try:
        document.getElementById("results_wrapper").style.display = "block"
        document.getElementById("empty_state").style.display = "none"
        document.getElementById("hero_vlt").innerText = f"{res.get('VLT', 0):.1f}"
        document.getElementById("hero_uvb").innerText = f"{res.get('UVB', 0):.1f}"
        document.getElementById("hero_tser").innerText = f"{res.get('TSER', 0):.1f}"
        
        vlr_i = res.get('VLR_I')
        if vlr_i is not None:
            document.getElementById("hero_vlr").innerText = f"{vlr_i:.1f}"
            document.getElementById("hero_vlr_box").style.display = "block"
            document.getElementById("res_vlr_i").innerText = f"{vlr_i:.2f} %"
            document.getElementById("row_vlr_i").className = ""
        else:
            document.getElementById("hero_vlr_box").style.display = "none"
            document.getElementById("res_vlr_i").innerText = "未提供数据"
            document.getElementById("row_vlr_i").className = "text-secondary opacity-50"
        
        document.getElementById("res_vlt").innerText = f"{res.get('VLT', 0):.2f}"
        document.getElementById("res_vlr_e").innerText = f"{res.get('VLR_E', 0):.2f}"
        document.getElementById("res_uvt").innerText = f"{res.get('UVT', 0):.2f}"
        document.getElementById("res_te").innerText = f"{res.get('TE', 0):.2f}"
        document.getElementById("res_re").innerText = f"{res.get('RE', 0):.2f}"
        document.getElementById("res_g").innerText = f"{res.get('G', 0):.2f}"
        document.getElementById("res_sc").innerText = f"{res.get('SC', 0):.3f}"
        
        if res.get("spectra"):
            chart_data = {
                "fileIdent": res.get("name", "Unknown"),
                "spectra": res["spectra"]
            }
            window.gb2680Storage.saveChart(chart_data)
            document.getElementById("show_chart_link").style.display = "block"
        else:
            document.getElementById("show_chart_link").style.display = "none"
            
        if hasattr(window, 'MathJax') and hasattr(window.MathJax, 'typesetPromise'):
            window.MathJax.typesetPromise()
    except Exception as e:
        print("Update right panel error:", e)
        window.alert("旧版历史数据格式不兼容，请先清空历史记录后再试！")

def js_view_history(idx):
    try:
        item = history_data[int(idx)]
        update_right_panel(item)
    except Exception as e:
        print("View error:", e)

window.js_view_history = js_view_history

def on_export_click(event):
    if not history_data:
        window.alert("暂无历史数据可导出！")
        return
        
    csv_content = "Filename,VLT(%),TSER(%),UV Block(%),VLR(%)\n"
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

def update_compare_controls():
    button = document.getElementById("compare_btn")
    counter = document.getElementById("compare_count")
    if button:
        button.disabled = len(compare_selection) == 0
    if counter:
        counter.innerText = f"{len(compare_selection)}/5"

def on_compare_selection_change(idx, checked):
    index = int(idx)
    if checked and index not in compare_selection:
        if len(compare_selection) >= 5:
            window.alert("最多选择 5 个测试样品进行对比。")
            checkbox = document.getElementById(f"compare_check_{index}")
            if checkbox:
                checkbox.checked = False
            return
        compare_selection.append(index)
    elif not checked and index in compare_selection:
        compare_selection.remove(index)
    compare_selection.sort()
    window.localStorage.setItem(COMPARE_SELECTION_KEY, json.dumps(compare_selection))
    update_compare_controls()

window.js_compare_selection_change = on_compare_selection_change

def on_compare_click(event):
    if not compare_selection:
        window.alert("请至少选择一个测试样品。")
        return
    window.open("compare.html", "_blank")

def render_history():
    tbody = document.getElementById("history_tbody")
    if not history_data:
        tbody.innerHTML = '<tr><td colspan="7" class="text-muted py-3">（计算结果将自动保存在这里）</td></tr>'
        update_compare_controls()
        return

    try:
        html = ""
        for i, item in enumerate(history_data):
            if not isinstance(item, dict):
                continue

            vlr_i = item.get('VLR_I')
            vlr = f"{vlr_i:.1f}" if isinstance(vlr_i, (int, float)) else "-"

            name = str(item.get('name', f'记录{i + 1}'))
            short_name = name if len(name) <= 12 else name[:10] + "..."

            vlt = float(item.get('VLT', 0) or 0)
            tser = float(item.get('TSER', 0) or 0)
            uvb = float(item.get('UVB', 0) or 0)

            html += (
                f"<tr style='cursor: pointer;'>"
                f"<td onclick='event.stopPropagation();'><input class='form-check-input' type='checkbox' id='compare_check_{i}' onchange='window.js_compare_selection_change({i}, this.checked)' {'checked' if i in compare_selection else ''} aria-label='选择 {short_name} 加入对比'></td>"
                f"<td class='text-start text-primary fw-bold' onclick='window.js_view_history({i})' title='点击查看详情: {name}'>{short_name}</td>"
                f"<td onclick='window.js_view_history({i})'>{vlt:.1f}</td>"
                f"<td onclick='window.js_view_history({i})'>{tser:.1f}</td>"
                f"<td onclick='window.js_view_history({i})'>{uvb:.1f}</td>"
                f"<td onclick='window.js_view_history({i})'>{vlr}</td>"
                f"<td><button class='btn btn-sm btn-outline-danger py-0 px-1' onclick='window.js_delete_history({i}); event.stopPropagation();' title='删除'>&times;</button></td>"
                f"</tr>"
            )

        tbody.innerHTML = html if html else '<tr><td colspan="7" class="text-muted py-3">（暂无有效历史数据）</td></tr>'
        update_compare_controls()
    except Exception as e:
        print("Render history error:", e)
        tbody.innerHTML = '<tr><td colspan="7" class="text-warning py-3">历史数据异常，建议清空后重试</td></tr>'


def bind_click_handler_by_id(element_id, handler):
    el = document.getElementById(element_id)
    if not el:
        return
    try:
        if create_proxy is not None:
            proxy = create_proxy(handler)
            _event_proxies.append(proxy)
            el.addEventListener("click", proxy)
        else:
            el.onclick = handler
    except Exception as e:
        print(f"Bind click error for #{element_id}:", e)


def bind_click_handler_by_selector(selector, handler):
    el = document.querySelector(selector)
    if not el:
        return
    try:
        if create_proxy is not None:
            proxy = create_proxy(handler)
            _event_proxies.append(proxy)
            el.addEventListener("click", proxy)
        else:
            el.onclick = handler
    except Exception as e:
        print(f"Bind click error for selector {selector}:", e)

def get_file_count(file_input):
    try:
        return int(file_input.files.length)
    except Exception:
        try:
            return len(file_input.files)
        except Exception:
            return 0

def update_file_status(event):
    file_input = event.target
    status_id = {
        "trans_csv": "trans_status",
        "refl_csv": "refl_status",
        "in_refl_csv": "in_refl_status"
    }.get(file_input.id)
    if not status_id:
        return
    status = document.getElementById(status_id)
    if get_file_count(file_input) > 0:
        selected_file = file_input.files.item(0)
        status.innerText = f"已选择：{selected_file.name}"
        status.className = "file-status ready"
    elif file_input.id == "in_refl_csv":
        status.innerText = "未提供时将跳过室内反射率"
        status.className = "file-status"
    else:
        status.innerText = "尚未选择文件"
        status.className = "file-status"

def bind_change_handler(element_id, handler):
    el = document.getElementById(element_id)
    if not el:
        return
    try:
        proxy = create_proxy(handler) if create_proxy is not None else handler
        if create_proxy is not None:
            _event_proxies.append(proxy)
        el.addEventListener("change", proxy)
    except Exception as e:
        print(f"Bind change error for #{element_id}:", e)


def init_event_handlers():
    # Keep py-click attributes, and bind explicitly as a fallback to avoid silent non-response.
    bind_click_handler_by_id("calc_btn", on_calculate_click)
    bind_click_handler_by_id("export_btn", on_export_click)
    bind_click_handler_by_id("compare_btn", on_compare_click)
    bind_click_handler_by_selector("button[py-click='clear_history_click']", clear_history_click)
    bind_change_handler("trans_csv", update_file_status)
    bind_change_handler("refl_csv", update_file_status)
    bind_change_handler("in_refl_csv", update_file_status)

def on_calculate_click(event):
    global _calc_in_progress

    if _calc_in_progress:
        return

    document.getElementById("results_wrapper").style.display = "none"
    document.getElementById("error_msg").innerHTML = ""
    document.getElementById("error_msg").style.display = "none"
    document.getElementById("calculation_status").innerText = ""
    document.getElementById("hero_vlr_box").style.display = "none"

    trans_file_input = document.getElementById("trans_csv")
    refl_file_input = document.getElementById("refl_csv")
    in_refl_file_input = document.getElementById("in_refl_csv")

    try:
        if get_file_count(trans_file_input) == 0 or get_file_count(refl_file_input) == 0:
            document.getElementById("error_msg").innerHTML = "请先上传透光率 (T%) 和外反射率 (R%) CSV 文件。"
            document.getElementById("error_msg").style.display = "block"
            return
    except Exception as e:
        document.getElementById("error_msg").innerHTML = f"文件读取异常: {str(e)}"
        document.getElementById("error_msg").style.display = "block"
        return

    _calc_in_progress = True
    calc_btn = document.getElementById("calc_btn")
    if calc_btn:
        calc_btn.disabled = True
    document.getElementById("calc_btn_label").innerText = "正在计算"
    document.getElementById("calc_spinner").style.display = "inline-block"
    document.getElementById("calculation_status").innerText = "正在读取光谱数据，请稍候..."

    async def process_files():
        global _calc_in_progress
        try:
            trans_file = trans_file_input.files.item(0)
            refl_file = refl_file_input.files.item(0)
            
            trans_text = await trans_file.text()
            refl_text = await refl_file.text()
            
            in_refl_text = None
            if get_file_count(in_refl_file_input) > 0:
                in_refl_file = in_refl_file_input.files.item(0)
                in_refl_text = await in_refl_file.text()
            
            # 使用算法核心模块处理
            res = calculate_params(trans_text, refl_text, in_refl_text)
            document.getElementById("calculation_status").innerText = "计算完成，结果已更新。"
            
            # 保存到历史，直接存入 res 字典(包含了所有指标与 spectra 光谱阵列)，用于随时切换浏览
            trans_name = str(trans_file.name)
            base_name = trans_name.rsplit(".", 1)[0]
            file_ident = (base_name.split("-", 1)[0].strip() or base_name)
            res["name"] = file_ident
            history_data.insert(0, res)
            
            # 由于带有 spectra, 不宜保存过多，将 localStorage 缓存深度缩减到 30 条以免越界
            if len(history_data) > 30:
                history_data.pop()
            
            window.gb2680Storage.saveHistory(history_data)
            render_history()
            
            # 调用新方法集中刷新右侧面板
            update_right_panel(res)
            
        except Exception as e:
            error_msg = f"计算出错: {str(e)}"
            print("Error in process_files:", error_msg)
            document.getElementById("error_msg").innerHTML = error_msg
            document.getElementById("error_msg").style.display = "block"
            document.getElementById("calculation_status").innerText = "计算未完成"
        finally:
            _calc_in_progress = False
            if calc_btn:
                calc_btn.disabled = False
            document.getElementById("calc_btn_label").innerText = "开始计算"
            document.getElementById("calc_spinner").style.display = "none"
            
    asyncio.ensure_future(process_files())

async def initialize_page():
    global compare_selection
    await load_history_from_storage()
    try:
        stored_selection = window.localStorage.getItem(COMPARE_SELECTION_KEY)
        if stored_selection:
            compare_selection = [
                int(index) for index in json.loads(stored_selection)
                if 0 <= int(index) < len(history_data)
            ][:5]
    except Exception:
        compare_selection = []
    render_history()
    init_event_handlers()

asyncio.ensure_future(initialize_page())
