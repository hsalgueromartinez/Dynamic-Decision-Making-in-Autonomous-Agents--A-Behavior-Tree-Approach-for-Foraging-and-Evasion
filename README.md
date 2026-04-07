# Dynamic Decision-Making in Autonomous Agents: A Behavior Tree Approach for Foraging and Evasion

<br>

> **Course:** Autonomous Agents (Bachelor's Degree in AI)  
> **Institution:** Universitat Autònoma de Barcelona (UAB)  
> **Academic Year:** 2025-2026
<br>

Implementation of autonomous agents using **Behavior Trees** and **asynchronous programming** within the **AAPE (Autonomous Agents Practice Environment)** platform. The project covers three incremental scenarios involving two types of agents: the **Astronaut** 👩‍🚀 and the **CritterMantaRay** 🦈.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Scenarios](#scenarios)
- [Environment Setup](#environment-setup)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Scripts Description](#scripts-description)

---

## 🌌 Project Overview

This project implements autonomous agent behaviors using the `py_trees` library for Behavior Tree management and Python's `asyncio` for asynchronous execution. Agents communicate with the AAPE Unity simulation environment through a WebSocket connection. All agent logic is modular, separated into reusable Behavior Tree nodes organized by scenario.

---

## 🎮 Scenarios

| # | Scenario | Description |
|---|---|---|
| 1️⃣ | **Alone** | The Astronaut roams the environment, detects and collects alien flowers 🌸, manages a 2-flower inventory limit, and returns to base to unload. No hostile agents. |
| 2️⃣ | **Critters** | CritterMantaRay agents 🦈 are introduced. They roam autonomously, detect the Astronaut, chase and bite her (stunning her and stealing a flower), then retreat. |
| 3️⃣ | **Collect-and-Run** | The Astronaut must collect flowers as in the Alone scenario while actively avoiding nearby CritterMantaRay agents. |

---

## ⚙️ Environment Setup

### 📦 Requirements

- **AAPE** v0.4.1 or later
- **Python** 3.9+
- The following Python libraries:

```bash
pip install aiohttp py_trees
```

### 🔧 AAPE Configuration

1. Download and extract the AAPE release for your operating system.
2. Launch AAPE and load the **3-AAC** scene before running any agent scripts.

---

## ▶️ How to Run

> ⚠️ **Important:** Always launch AAPE and load the **3-AAC** scene before starting any Python script.

---

### 1️⃣ Scenario 1 — Alone

**Terminal:**
```bash
python AAgent_BT.py AAgent-Alpha.json
```

**Inside AAPE** (Send message field):
```bash
bt:BTRoam
```

🌸 The Astronaut will start roaming the map, collecting flowers, and returning to base autonomously.

---

### 2️⃣ Scenario 2 — Critters

First, make sure the Astronaut agent from Scenario 1 is already running (or use a manually controlled Astronaut from AAPE). Then, in a **separate terminal**:

```bash
python Spawner.py APackCritters.json
```

🦈 This spawns a group of CritterMantaRay agents that will autonomously roam and hunt the Astronaut.

---

### 3️⃣ Scenario 3 — Collect-and-Run

**Terminal 1** 👩‍🚀 — Astronaut with avoidance behavior:
```bash
python AAgent_BT.py AAgent-Alpha.json
```

**Inside AAPE** (Send message field):
```bash
bt:BTAvoid
```

**Terminal 2** 🦈 — Spawn the critters:
```bash
python Spawner.py APackCritters.json
```

🏃 The Astronaut will now collect flowers while actively evading nearby CritterMantaRay agents.

---

## 🗂️ Project Structure
AAgent_Python/
│
├── AAgent_BT.py # 🤖 Main agent entry point
├── Goals_BT_Basic.py # 🎯 Basic asynchronous goal definitions
├── Sensors.py # 👁️ Raycast sensor interface
├── Spawner.py # 🌊 Multi-agent spawner utility
│
├── BTRoam.py # 🌸 Behavior Tree — Scenario 1 (Baseline)
├── BTCritter.py # 🦈 Behavior Tree — Scenario 2 (Critters)
├── BTAvoid.py # 🏃 Behavior Tree — Scenario 3 (Collect-and-Run)
│
├── AAgent-Alpha.json # 👩‍🚀 Astronaut config (blue)
├── AAgent-Beta.json # 👩‍🚀 Astronaut config (variant)
├── AAgent-Gamma.json # 👩‍🚀 Astronaut config (variant)
├── AAgent-Delta.json # 👩‍🚀 Astronaut config (variant)
├── AAgent-1.json # 👩‍🚀 Astronaut config (variant)
├── AAgent-Critter.json # 🦈 CritterMantaRay agent config
│
├── APackCritters.json # 🌊 Spawner pack — Critters only
└── APackAstroCritters.json # 🌊 Spawner pack — Astronaut + Critters

---

## 👥 Authors
*   **David Piera** - *Developer & Researcher*
*   **Hector Salguero** - *Developer & Researcher*
---
