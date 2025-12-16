# Quera Problem Scraper

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Tool-Selenium-green)]()

**Automated Problem Scraper & Repository Generator** - Scrapes Quera courses, generates AI summaries (English & Persian), organizes problems by category, and uploads to GitHub.

## 📊 Overview

Automates competitive programming practice by:
- 🔗 Scraping Quera problem descriptions & solutions
- 👌 Generating AI summaries in multiple languages
- 📁 Organizing problems by difficulty & category
- 🔧 Creating well-structured repository
- 🤖 Automating GitHub uploads

## 🛠️ Technologies

```
Python | Selenium | BeautifulSoup | GitHub API | Requests
```

## ✨ Features

- **Web Scraping:** Automated data extraction from Quera
- **AI Summaries:** English & Persian problem summaries
- **Auto-Organization:** Problems grouped by:
  - Difficulty level
  - Algorithm category
  - Topic area
- **GitHub Integration:** Automatic repo creation & updates
- **Batch Processing:** Handle multiple courses efficiently

## 🚀 Quick Start

```bash
git clone https://github.com/VictimPickle/Quera-problem-Scraper.git
cd Quera-problem-Scraper
pip install selenium beautifulsoup4 requests gitpython
python scraper.py --course <course_id>
```

## 🔘️ Usage

```bash
# Scrape specific course
python scraper.py --course 12345

# Scrape with AI summaries
python scraper.py --course 12345 --summarize --lang en_fa

# Auto-upload to GitHub
python scraper.py --course 12345 --upload-github
```

## 📁 Output Structure

```
quera-problems/
├── dynamic-programming/
│   ├── easy/
│   │   └── problem-1.md
│   ├── medium/
│   │   └── problem-2.md
│   └── hard/
├── graphs/
├── README.md
└── index.json
```

## 💡 Key Features

1. **Smart Scraping** - Handles dynamic content, authentication
2. **Language Support** - Persian/English summaries
3. **Category Detection** - Auto-identifies problem category
4. **Error Handling** - Robust retry & fallback mechanisms
5. **Progress Tracking** - Real-time scraping updates

## 📚 Documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

---

**Created by:** Mobin Ghorbani | December 2025
