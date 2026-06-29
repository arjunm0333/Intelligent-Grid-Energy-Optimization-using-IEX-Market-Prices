# Intelligent Grid Energy Scheduling using IEX Market Prices

An intelligent energy scheduling system that optimizes household appliance usage based on **Indian Energy Exchange (IEX) Day-Ahead Market Clearing Prices (MCP)**. The project combines live electricity market data, price-aware scheduling, and an interactive desktop application to minimize daily electricity costs while respecting appliance usage constraints.

---

## Overview

Electricity prices in the Indian Energy Exchange (IEX) fluctuate throughout the day. Instead of operating appliances during expensive time periods, this system intelligently shifts flexible appliance usage to lower-cost intervals while maintaining user comfort.

The project uses **live IEX market prices**, heuristic scheduling, and a Tkinter-based GUI to provide an efficient and practical demand-side energy management solution.

---

## Features

* Live scraping of IEX Day-Ahead Market Clearing Prices (MCP)
* 96 × 15-minute time-slot energy scheduling
* Household appliance modeling with power ratings and usage constraints
* Price-aware scheduling optimization using heuristic algorithms
* Daily electricity cost estimation before and after optimization
* Interactive desktop application built with Tkinter
* Local data storage using SQLite
* Explainable scheduling decisions and cost savings analysis

---

## System Architecture

### 1. Market Price Collection

* Retrieves Day-Ahead Market Clearing Prices from the IEX website.
* Processes market data into 96 standardized 15-minute intervals.
* Stores price information locally using SQLite.
* Includes logging and basic error handling.

### 2. Appliance Modeling

The scheduler supports different categories of household appliances:

* Always-on appliances (e.g., Refrigerator)
* Fully shiftable appliances (e.g., Washing Machine)
* Time-window constrained appliances
* Continuous and non-continuous operation requirements

Each appliance includes:

* Power rating
* Daily operating duration
* User-defined scheduling constraints

### 3. Scheduling Optimization

A heuristic, price-aware scheduling algorithm minimizes electricity costs by:

* Identifying low-price time slots
* Shifting flexible appliance usage
* Preventing scheduling conflicts
* Respecting appliance-specific constraints
* Preserving continuous operation where required

Unlike optimization solvers, this approach is lightweight, fast, and suitable for practical deployment.

### 4. Cost Analysis

Electricity cost is calculated as:

```
Cost = Power Rating × Market Clearing Price × Time Slot Duration
```

The application compares:

* Original user schedule
* Optimized schedule
* Total daily electricity cost
* Estimated daily savings

### 5. Desktop Application

The Tkinter-based GUI enables users to:

* Configure appliance usage
* Set appliance constraints
* Mark always-on appliances
* Generate optimized schedules
* Compare electricity costs
* View estimated savings

---

## Project Structure

```
intelligent-grid-iex/
│
├── scraper_iex_mcp.py          # IEX market price scraping
├── scheduler_optimization.py   # Scheduling and optimization engine
├── front_gui.py                # Tkinter graphical interface
├── README.md
```

---

## Technologies Used

* Python
* Selenium
* BeautifulSoup
* SQLite
* Tkinter
* NumPy

---

## Results

The proposed scheduling system successfully:

* Reduces household electricity costs
* Shifts flexible appliance loads to low-price periods
* Maintains user comfort through scheduling constraints
* Provides transparent and explainable scheduling decisions
* Demonstrates a practical alternative to computationally expensive optimization methods

---

## Future Enhancements

* Solar PV integration
* Battery Energy Storage System (BESS) support
* Smart meter integration
* Machine learning-based load prediction
* Web dashboard for remote monitoring
* IoT-enabled appliance control
* Mobile application support

---

## Notes

* Live market prices are obtained from the Indian Energy Exchange (IEX).
* SQLite database files and log files are excluded from the repository.
* The scheduling engine uses a heuristic optimization strategy rather than mathematical optimization solvers.

---

## Author

**Arjun M**

B.Tech – Electrical and Computer Engineering

Amrita Vishwa Vidyapeetham
