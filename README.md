# 3M Window Film 计算器 (GB/T 2680)

基于 GB/T 2680 标准的窗膜光学参数计算工具。项目使用前端页面 + PyScript（Python in Browser）实现，支持上传分光光度计 CSV 数据并自动计算关键指标及生成谱图。

## 功能特性

- 上传透光率 `T%`、外反射率 `R%`、可选内反射率 `R_in%` CSV 文件
- 自动计算以下指标：
  - 可见光透射比 `VLT`
  - 可见光外反射比 `VLR_E`
  - 可见光内反射比 `VLR_I`（可选）
  - 紫外线透射比 `UVT`
  - 紫外线阻隔率 `UV Block`
  - 太阳光直接透射比 `TE`
  - 太阳光直接反射比 `RE`
  - 太阳能总透射比 `g`
  - 总隔热率 `TSER`
  - 遮阳系数 `SC`
- 计算历史本地缓存（`localStorage`）
- 历史数据 CSV 导出
- 太阳能谱图展示（原始、直接透过、总透过）

## 项目结构

- `index.html`：主页面与上传/结果展示 UI
- `chart.html`：谱图展示页（Plotly）
- `main.py`：页面交互、事件处理、历史记录逻辑
- `calculator.py`：核心计算逻辑
- `constants.py`：GB/T 2680 相关权重系数与常量
- `CIE241_H1_5nm.csv`：太阳光谱数据

## 本地运行

> 注意：请使用本地 HTTP 服务启动，不要直接双击打开 `index.html`。

1. 进入项目目录

```powershell
cd "c:\Users\A7N6PZZ\OneDrive - 3M\Documents\5. Lab & Field Test\window_film_calculation\github_pages_app"
```

2. 启动静态服务

```powershell
py -m http.server 8000
```

3. 浏览器打开

```text
http://127.0.0.1:8000/index.html
```

## GitHub Pages 部署建议

- 将项目文件放在仓库根目录
- 在仓库 Settings -> Pages 中选择：
  - Source: `Deploy from a branch`
  - Branch: `main`
  - Folder: `/ (root)`
- 等待部署完成后访问 Pages 地址

## 常见问题

### 1) 点击“开始计算”没有反应

常见原因：

- PyScript 资源地址无效或版本不匹配
- 本地 Python 文件未被 PyScript 正确加载（缺少 fetch/config）
- CSV 文件未上传完整（必须有透光率与外反射率）

### 2) 报错 `ModuleNotFoundError: No module named 'calculator'`

请确认页面配置已包含以下文件加载：

- `main.py`
- `calculator.py`
- `constants.py`
- `CIE241_H1_5nm.csv`

### 3) 样式加载失败（stylesheet URL 404）

请检查外链 CSS 地址是否可用，并固定到可用版本，避免使用失效的 `latest` 地址。

## 许可证

本项目用于内部测试与计算验证，请按公司规范使用。
