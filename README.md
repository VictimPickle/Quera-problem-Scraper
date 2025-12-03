# Quera Problems Scraper & Organizer

A complete end-to-end pipeline for scraping, summarizing, categorizing,
and organizing **Quera** programming problems --- fully automated using
Selenium + AI + GitHub integration.

This tool is designed for competitive programmers, students, and anyone
who wants a clean, structured archive of their solved problems.

------------------------------------------------------------------------

## 🚀 Features

### 🔍 Scraping Automation

-   Logs into your Quera account (supports cookies)
-   Iterates through selected **courses**, **assignments**, and
    **problems**
-   Saves each problem statement as `statement.txt`

### 🤖 AI-Powered Processing

For every scraped problem: - Removes unnecessary story/context\
- Extracts the **core problem description** - Generates a **clean
English + Persian summary** - Classifies the problem into **one of 10
algorithmic categories** (DP, Graph, Greedy, etc.)

### 📦 Folder Organization

Each problem gets its own directory containing: - `README.md` →
AI-generated bilingual problem summary\
- `solution.*` → Your solution code (C/C++/Python/...)

Statements remain **local only** and are ignored by Git.

### ☁️ GitHub Auto-Uploader

Automatically: - Initializes a Git repo inside `organized_problems/` -
Commits only **READMEs + code** - Pushes to your GitHub repo\
(example: `VictimPickle/Problems-solved`)

------------------------------------------------------------------------

## 📂 Output Structure

    organized_problems/
    ├── README.md
    ├── .gitignore
    ├── 01_Linear_Data_Structures/
    │   ├── some_problem/
    │   │   ├── README.md
    │   │   └── solution.c
    │   └── ...
    ├── 08_Dynamic_Programming/
    │   ├── fibonacci/
    │   │   ├── README.md
    │   │   └── solution.py
    └── 10_Geometric_Mathematical/
        └── ...

------------------------------------------------------------------------

## ⚠️ Note

This project is for **educational use only**.\
All original problems belong to Quera.org. Please respect their terms of
service.

------------------------------------------------------------------------

## 👤 Author

**VictimPickle**\
GitHub: https://github.com/VictimPickle
