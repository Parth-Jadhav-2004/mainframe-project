# Mainframe Project

Welcome to the **Mainframe Project**! This repository showcases a project primarily developed using Python, HTML, CSS, and JavaScript. Below, you'll find an overview of the project, its purpose, and how to get started.

---

## 📚 Table of Contents
1. [About the Project](#about-the-project)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
5. [Contributing](#contributing)
6. [License](#license)

---

## 📖 About the Project

We've built an AI-powered COBOL-to-pseudocode converter that helps modern developers understand legacy mainframe code. The tool automatically analyzes COBOL programs and generates three key outputs: (1) clean, structured pseudocode with modern syntax, (2) plain-English explanations of the code's logic, and (3) visual flowcharts showing the program's control flow. This bridges the knowledge gap for developers unfamiliar with COBOL's verbose syntax.

Technical Implementation:
The system uses Python (Flask) for the backend, with Google's Gemini AI for code analysis and explanations, and Graphviz for flowchart generation. Users upload COBOL files (.cob or .txt) through a web interface, and the system processes them through three stages: parsing the COBOL structure, converting to pseudocode with AI, and generating visual diagrams. The responsive web UI shows results in separate tabs with copy/download options.

Key Benefits:
This tool dramatically reduces the time needed to understand legacy systems, helps onboard new developers to mainframe projects, and supports modernization efforts. Unlike manual analysis, it provides instant, consistent documentation with visual aids - especially valuable as COBOL expertise becomes scarce. The entire solution runs as a web app for easy access without local setup.


---

## ✨ Features

- **Python-Powered Backend**: Efficient backend logic with Python.
- **Interactive Web Design**: Frontend built with HTML, CSS, and JavaScript.
- **Responsive UI**: Ensures accessibility across devices.
- **Extensible Codebase**: Modular and easy-to-extend.

---

## 💻 Tech Stack

- **Python**: Backend logic and data processing .
- **HTML**: Structuring the web pages .
- **CSS**: Styling and responsive design.
- **JavaScript**: Adding interactivity to the web pages.

---

## 🚀 Getting Started

Follow these steps to set up the project in your local environment:

### Prerequisites
- Python (v3.8 or higher)
- A modern web browser
- Git (optional)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Parth-Jadhav-2004/mainframe-project.git
   cd mainframe-project
   ```
2. Install necessary dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Open your browser and navigate to `http://localhost:8000`.

---

## 🤝 Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add your message here'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

Please make sure your code adheres to the repository's coding guidelines.

---

## 📜 License

This repository is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute this project.

---
