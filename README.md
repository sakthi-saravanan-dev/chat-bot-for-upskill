# Project Setup Guide

## 🚀 Getting Started

Follow the steps below to set up and run the application locally.

---

## 📌 Prerequisites

Ensure you have Python 3.x installed on your system. You can download the latest version from the official Python website: [python.org](https://www.python.org/).

---

## ⚙️ Setup Instructions

### 1️⃣ Create and Activate a Virtual Environment

```bash
python -m venv venv
```

For Windows:
```bash
venv\Scripts\activate
```

For macOS/Linux:
```bash
source venv/bin/activate
```

---

### 2️⃣ Install Dependencies

With the virtual environment activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Set Up API Key

To run the application, set a valid API key as an environment variable:

```python
import openai
openai.api_key = 'your-openai-api-key'
```

🔹 Replace `'your-openai-api-key'` with your actual API key.

---

### 4️⃣ Run the Application

Execute the following command to start the application:

```bash
python app.py  # Replace 'app.py' with your actual filename
```

✅ Your application should now be up and running!

---

## 🎯 Additional Notes
- Ensure your virtual environment is activated before running the application.
- If you face issues with dependencies, try updating `pip` before installing:

  ```bash
  pip install --upgrade pip
  ```

---