# 📊 InsightData (AI Analyst Agent)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-8E75B2?logo=google&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**InsightData** is an advanced AI Data Analyst powered by **Google's Gemini 2.5 Flash** and built upon the **ReAct (Reasoning + Acting)** architecture.

Unlike standard chatbots, InsightData doesn't just guess answers. It actively **reasons** about your data—whether it's a local **CSV/Excel file** or a live **Google Sheets link**. It functions like a real data scientist: understanding your dataset structure, writing and executing **Python code** (Pandas/Matplotlib) in real-time, cleaning data on-the-fly, and visualizing trends—all in your preferred language (English or Indonesian).

## ✨ Key Features

### 🧠 Advanced ReAct Agent Engine
Using the `LangChain` Pandas Agent framework, the assistant follows a strict cognitive loop:
1.  **Thought:** Analyzes the user's question and plans the analysis steps.
2.  **Action:** Generates and runs actual **Python/Pandas code**.
3.  **Observation:** Reviews the execution result (numbers or plots) to ensure accuracy.
4.  **Final Answer:** Synthesizes the findings into business insights.

### 🌐 Multilingual Intelligence
* **Dual Language Support:** Seamlessly switch between **English** and **Indonesian** via the sidebar.
* **Smart Translation:** The agent enforces a strict logic layer to ensure the final answer matches your chosen language, regardless of the language used in the query.

### 📊 Auto-Visualization & Download
* **Generative Plotting:** Just ask *"Show me the sales trend"* or *"Plot the top 5 categories"*, and the AI will generate **Matplotlib/Seaborn** charts instantly.
* **Interactive Downloads:** Every generated plot comes with a direct **📥 Download Button** so you can save insights for your reports.

### 🛡️ Smart Data Handling & Safety
* **Auto-Cleaning:** automatically removes "ghost" data (empty rows/cols) and duplicates upon upload to prevent system crashes.
* **Hybrid Data Source:** Supports local **Files (.csv/.xlsx)** and **Google Sheets (URL)**.
* **Privacy First:** Data is processed in temporary memory. The Agent cannot overwrite or delete your original files.

## 🛠️ Tech Stack
* **LLM:** Google Gemini 2.5 Flash (via `ChatGoogleGenerativeAI`).
* **Framework:** Streamlit (Frontend).
* **Orchestration:** LangChain (Pandas DataFrame Agent).
* **Data Processing:** Pandas, Matplotlib, Seaborn.
* **Memory:** ConversationBufferMemory.

## ⚠️ Limitations & Data Rules

### 1. Data Hygiene (Crucial)
To ensure the AI understands your data, your file **MUST** follow these rules:
* **🚫 No Merged Cells:** Unmerge all cells.
* **📝 Single-Row Header:** The first row must be the header.
* **🔢 Consistent Data Types:** Do not mix text and numbers in one column (e.g., avoid `1,000` as string vs `1000` as int).

### 2. Data Source Priority
* **Priority:** The system prioritizes **Local Files** over URLs.
* **Switching:** If you want to analyze a Google Sheet URL, you must remove all uploaded files first.

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/viochris/insight-data-ai-analyst.git
    cd insight-data-ai-analyst
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

## 🚀 Usage Guide

1.  **Configuration (Sidebar):**
    * Enter your **Google Gemini API Key**.
    * Select your **Language Preference** (English/Indonesian).
2.  **Load Data:**
    * **Option A:** Upload `.csv` or `.xlsx` files.
    * **Option B:** Paste a public Google Sheets URL.
    * Click **"⚡ Initialize & Analyze"** to wake up the Agent.
3.  **Query:**
    * Type your question naturally (e.g., *"What is the total revenue?"* or *"Visualize the correlation between price and rating"*).
    * Watch the **"Thinking Process"** expander to see the Python code being generated.
4.  **Manage:**
    * Use **"🧹 Clear Conversation"** to tidy up the chat while keeping data loaded.
    * Use **"🔴 Hard Reset System"** to wipe everything and restart the session.

## 📷 Gallery

### 1. Landing Interface
![Home UI](assets/home_ui.png)
*The clean, modern landing page offering quick configuration for API keys, data uploads, and language settings.*

### 2. High-Quality Visualization
![Analysis Chart](assets/analysis_chart.png)
*The Agent generates standalone, high-resolution matplotlib charts that can be downloaded directly for reports.*

### 3. Transparent Reasoning (Full Interaction Flow)
*The ReAct engine provides a detailed breakdown of the analysis. Below is the complete flow captured in three parts:*

**Part 1: Query & Response Generation**  
![Interaction Part 1](assets/result1.png)  
*The Agent receives the natural language prompt, instantly generates the visualization within the chat, and begins the analysis.*

**Part 2: Deep Dive Analysis**  
![Interaction Part 2](assets/result2.png)  
*Instead of just describing the chart, the Agent calculates supporting metrics (rating, price, recommendation rate) to explain **why** the trend exists.*

**Part 3: Final Insight**  
![Interaction Part 3](assets/result3.png)  
*The AI synthesizes all statistical findings into a clear, business-friendly summary in the user's chosen language.*

---
**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*"Stop writing complex Python code. Start asking questions."*
