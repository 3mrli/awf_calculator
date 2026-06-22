# 3M Window Film Calculator (GB/T 2680)

A GB/T 2680-based window film optical performance calculator.
This project is built with an HTML frontend + PyScript (Python in the browser). It supports uploading spectrophotometer CSV data, automatic parameter calculation, and spectrum chart generation.

## Features

- Upload transmission `T%`, external reflectance `R%`, and optional internal reflectance `R_in%` CSV files
- Automatically calculates:
  - Visible Light Transmittance `VLT`
  - Visible Light External Reflectance `VLR_E`
  - Visible Light Internal Reflectance `VLR_I` (optional)
  - Ultraviolet Transmittance `UVT`
  - UV Block Rate `UV Block`
  - Direct Solar Transmittance `TE`
  - Direct Solar Reflectance `RE`
  - Solar Heat Gain Coefficient `g`
  - Total Solar Energy Rejection `TSER`
  - Shading Coefficient `SC`
- Local calculation history cache (`localStorage`)
- History export to CSV
- Solar spectrum visualization (original, direct transmitted, total transmitted)

## Project Structure

- `index.html`: Main UI (upload + results)
- `chart.html`: Spectrum chart page (Plotly)
- `main.py`: Event handling, UI updates, history management
- `calculator.py`: Core calculation logic
- `constants.py`: GB/T 2680 weighting factors and constants
- `CIE241_H1_5nm.csv`: Solar spectrum data

## Run Locally

Important: run with a local HTTP server. Do not open `index.html` directly by double-clicking.

1. Go to the project directory

```powershell
cd "c:\Users\A7N6PZZ\OneDrive - 3M\Documents\5. Lab & Field Test\window_film_calculation\github_pages_app"
```

2. Start a static server

```powershell
py -m http.server 8000
```

3. Open in browser

```text
http://127.0.0.1:8000/index.html
```

## GitHub Pages Deployment

- Keep all project files in repository root
- In repository Settings -> Pages:
  - Source: Deploy from a branch
  - Branch: main
  - Folder: / (root)
- Wait for deployment, then open your Pages URL

## Troubleshooting

### 1) No response after clicking Start Calculation

Common causes:

- Invalid or incompatible PyScript resource URLs
- Local Python files not properly loaded into PyScript runtime (missing fetch/config)
- Required CSV files are missing (transmission + external reflectance are mandatory)

### 2) Error: ModuleNotFoundError: No module named calculator

Verify your PyScript config includes these files:

- `main.py`
- `calculator.py`
- `constants.py`
- `CIE241_H1_5nm.csv`

### 3) Stylesheet URL failed (404)

Check external CSS links and pin to a valid version instead of a broken latest alias.

## License

This project is for internal testing and calculation validation. Please follow your company policy and compliance requirements.
