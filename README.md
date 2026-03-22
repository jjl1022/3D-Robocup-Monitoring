# ⚽ 3D Soccer Match Monitoring & Batch Evaluation System

## 📌 Overview
This project is a **GUI-based 3D soccer match monitoring and automated evaluation system** built with PyQt5 and rcssserver3d.

It is designed to **run large-scale competitions between multiple teams**, monitor matches in real time, and automatically record and analyze results.

---

## ✨ Key Features

### 🎮 Real-time Match Monitoring
- Live display of play mode, game time, and score
- Continuous updates during match execution
- Clear and intuitive GUI interface

### 🔁 Automated Batch Competition
- Round-robin style evaluation between multiple teams
- Configurable number of matches per pair
- Optional side switching (home/away fairness)

### ⚙️ Flexible Configuration
- Adjustable retry mechanism for unstable matches
- Configurable server IP and port
- Easy team directory management

### 📊 Result Recording & Analysis
- Detailed match logs saved as CSV
- Per-match and per-team statistics
- Win / Draw / Loss / Error tracking
- Automatic win rate calculation

### 🖥️ User-Friendly GUI
- Built with PyQt5
- Start / Stop controls
- Real-time logs and progress bar
- Non-blocking UI using multi-threading

---



## 🏗️ System Architecture

```

GUI (PyQt5)
│
├── Configuration Panel
├── Real-time Display
└── Control Panel
│
▼
GameThread (QThread)
│
▼
Runner
│
├── rcssserver3d Control
├── Team Process Management
├── Socket Communication
└── Match State Parsing

```

---

## 🛠️ Tech Stack

- **Python 3**
- **PyQt5** (GUI)
- **Socket Programming**
- **Multi-threading (QThread)**
- **rcssserver3d** (3D soccer simulation)

---

## 📂 Project Structure

```

project/
│── main.py                # GUI application
│── runner.py              # Core match execution logic
│── config.json            # Configuration file
│── binary/
│   ├── our/               # Our teams
│   └── opp/               # Opponent teams
│── *.csv                  # Output result files

````

---

## ⚡ Getting Started

### 1️⃣ Install dependencies
```bash
pip install PyQt5
````

### 2️⃣ Install rcssserver3d

Make sure `rcssserver3d` is installed and accessible in your system PATH.

### 3️⃣ Prepare team binaries

Place your teams in:

```
binary/our/
binary/opp/
```

Each team directory must contain:

```
start.sh
```

### 4️⃣ Run the system

```bash
python main.py
```

---

## ⚙️ Configuration

You can configure parameters via GUI or `config.json`:

* Server IP / Port
* Number of matches
* Retry times
* Side switching (exchange)
* Team directories

---

## 📊 Output

After execution, the system generates:

* `*-detail.csv` → Detailed match results
* `*-single.csv` → Per-team summary
* `*-all.txt` → Overall statistics

---

## 🧠 Core Design

### 🔹 Runner Module

Handles:

* Launching `rcssserver3d`
* Running team processes
* Socket communication with server
* Parsing real-time match data
* Controlling match flow

### 🔹 Multi-threading

* Uses **QThread** to prevent GUI freezing
* Enables real-time updates during execution

---

## ⚠️ Notes

* Linux environment is recommended
* Ensure `rcssserver3d` is properly installed
* Windows users may use WSL

---

## 🌟 Highlights

* Full-stack system: GUI + backend + simulation control
* Real-time data processing via socket communication
* Automated evaluation platform for multi-agent systems
* Scalable batch experiment framework
* Clean separation between UI and logic

---

## 👨‍💻 Author

**J2Life**

---


```
```
