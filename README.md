Intelligent Grid Energy Scheduling using IEX Market Prices
This project implements an intelligent energy scheduling system that optimizes household appliance usage based on Indian Energy Exchange (IEX) Market Clearing Prices (MCP).
The system combines real-time market data scraping, price-aware scheduling logic, and a desktop GUI to reduce electricity cost while respecting realistic appliance constraints.

🚀 Key Features
Automated scraping of IEX Day-Ahead Market MCP data
96 × 15-minute time-slot based energy modeling
Appliance-level power and usage profiling
Rule-based, price-aware scheduling optimization
Cost comparison before and after optimization
Interactive desktop application using Tkinter
🧠 System Overview
1. IEX Market Data Scraping
Scrapes Day-Ahead Market MCP values from the IEX website
Normalizes prices into 96 standardized 15-minute blocks
Stores data locally using SQLite
Includes logging and basic fault handling
2. Appliance Modeling
Supports multiple household appliances with fixed power ratings
Handles:
Always-on (24/7) appliances
Fully shiftable appliances
Preferred time-window appliances
Contiguous and non-contiguous usage patterns
3. Scheduling & Optimization Logic
Uses price-aware heuristic scheduling (greedy selection)
Shifts appliance operation to lower-cost time slots
Avoids scheduling conflicts between appliances
Special handling for critical appliances like refrigerators
Compares original user schedule with optimized schedule
Calculates daily cost savings
4. Cost Evaluation
Computes electricity cost using:
Cost = Power × MCP × Time Slot Duration
5. Graphical User Interface
Tkinter-based desktop GUI
Allows users to:
Configure appliance usage
Mark appliances as 24/7
View optimized schedules
See cost savings summary
📁 Project Structure
intelligent-grid-iex/
├── scraper_iex_mcp.py          # IEX MCP web scraping module
├── scheduler_optimization.py  # Scheduling & cost optimization logic
├── front_gui.py               # Tkinter-based desktop interface
├── README.md
🛠️ Tech Stack
Python
Selenium & BeautifulSoup
SQLite
Tkinter
NumPy
📊 Results & Insights
Appliance loads are shifted to low-price periods
Reduced electricity cost without impacting user comfort
Transparent and explainable scheduling decisions
Practical alternative to solver-based optimization
📌 Notes
Market price data is fetched live from the IEX website
Databases and logs are excluded from this repository
Scheduling is heuristic-based (not solver-driven)
📈 Future Enhancements
Renewable energy (solar) integration
Battery storage support
Real-time smart meter data
Web-based dashboard
