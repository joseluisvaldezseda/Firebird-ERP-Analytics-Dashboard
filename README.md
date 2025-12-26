# Microsip Multi-Branch BI: Data Pipeline & Dashboard

🔗 **[Live Demo](https://firebird-erp-analytics-dashboard.streamlit.app/)**

## Overview
This project is an end-to-end Business Intelligence solution that extracts, processes, and visualizes sales data from 4 different retail branches using Microsip ERP (Firebird SQL). It features an automated data pipeline and a high-performance interactive dashboard.

## 📂 Project Structure
```
Streamlit App/
├── lectura_informacion/         # Jupyter Notebooks for DB connections (Store 1-4)
├── Dashboard.py                 # Main Streamlit application
├── run_pipeline.py              # Papermill-based execution script
├── ejecutar_actualizacion.bat   # Trigger for the data pipeline
├── encender_dashboard.bat       # Trigger to launch the Streamlit server
├── Actualización Automática.xml # Windows Task Scheduler preset (Pipeline)
├── Encender Dashboard.xml       # Windows Task Scheduler preset (Launch)
├── Reporte_Ventas_Historico.csv # Consolidated Sales Data
├── Reporte_Cortes_Detallado.csv # Cashier Audit Data
├── Reporte_Facturas_Detallado.csv # Invoicing Data
└── ejecucion_log.txt            # Automated execution logs
```

## ⚙️ How It Works

### 1. Data Extraction Pipeline (`run_pipeline.py`)
- The system uses **Papermill** to programmatically execute a series of Jupyter Notebooks located in the `lectura_informacion/` folder
- Each notebook (`Conexion_Base_TiendaX.ipynb`) connects to a specific Firebird SQL database
- The script logs every success or failure in `ejecucion_log.txt`
- Data is cleaned, consolidated, and exported into CSV files for the dashboard to consume

### 2. Business Intelligence Dashboard (`Dashboard.py`)
A high-performance Streamlit dashboard that provides:
- **Branch Comparison**: Real-time metrics across all 4 locations
- **Sales Audit**: Detection of price manipulations, unauthorized discounts, and $0.00 sales
- **Cashier Performance**: Analysis of cash drawer balances (over/short), withdrawals, and opening funds
- **Customer Insights**: Top 10 customer rankings and Pareto (80/20) product analysis
- **Operational Efficiency**: Heatmaps showing peak hours and transaction "dead zones"

### 3. Automation & Orchestration
The project is designed for **Zero-Touch Operation** on Windows environments:
- **Batch Files**: `.bat` scripts wrap the Python commands for easy execution
- **Task Scheduler**: Included `.xml` files allow for easy import into the Windows Task Scheduler, enabling:
  - **Auto-Update**: Scheduled data refresh (e.g., daily or weekly)
  - **Auto-Boot**: Ensures the dashboard is running even after a system reboot

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.x |
| Orchestration | Papermill |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly (Express & Graph Objects) |
| Database | Firebird SQL (Microsip ERP) |
| Deployment | Windows Task Scheduler & Batch Scripting |

## 🚀 Setup & Installation

1. **Clone the repository:**
```bash
   git clone https://github.com/YourUser/Microsip-Branch-Insights.git
```

2. **Install dependencies:**
```bash
   pip install streamlit pandas plotly papermill ipykernel sqlalchemy fdb
```

3. **Configure Database Connections:**
   - Update the connection strings inside the notebooks in the `lectura_informacion/` folder with your local Firebird server credentials

4. **Run the Pipeline:**
   - Double-click `ejecutar_actualizacion.bat` to pull fresh data

5. **Launch the Dashboard:**
   - Double-click `encender_dashboard.bat`

## 🔒 Security & Data Masking

For demonstration purposes, this repository includes an **Anonymization Script**. It scales financial values by a random factor and masks PII (Personally Identifiable Information) such as customer names and Tax IDs, ensuring business confidentiality while maintaining data proportions for trend analysis.

## 📝 Logging & Monitoring

All automated tasks are recorded in `ejecucion_log.txt`.

**Example log entry:**
```
2025-12-26 15:00:01 - INFO - --- Iniciando proceso de actualización ---
2025-12-26 15:00:15 - INFO - ÉXITO: Conexion_Base_Tienda1.ipynb ejecutado correctamente.
2025-12-26 15:01:02 - INFO - --- Pipeline finalizado con éxito total ---
```

---

*Developed for advanced retail analytics and ERP data integration.*
