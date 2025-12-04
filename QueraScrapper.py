# ========================================
# QUERA SCRAPER - Complete Pipeline
# Scrape → Classify → Upload to GitHub
# ========================================

import os
import time
import json
import pickle
import logging
import random
import shutil
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from openai import OpenAI

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)8s | %(name)s | %(message)s",
)
logger = logging.getLogger("QueraScraper")

# ==================== CONFIGURATION ====================
# Quera Credentials
QUERA_EMAIL = "Youremail"
QUERA_PASSWORD = "YourPass"

# OpenRouter API
OPENROUTER_API_KEY = "sk-or-v..."

# GitHub Configuration
GITHUB_USERNAME = "VictimPickle"
GITHUB_REPO_NAME = "Problems-solved"

# Paths
BASE_DIR = "quera_questions"
ORGANIZED_DIR = "organized_problems"

# Categories for classification
CATEGORIES = {
    "01_Linear_Data_Structures": "ساختمان داده‌های خطی",
    "02_Tree_Structures": "ساختمان داده‌های درختی",
    "03_Graph_Structures": "ساختمان داده‌های گرافی",
    "04_Advanced_Data_Structures": "ساختمان داده‌های پیشرفته",
    "05_Search_Algorithms": "الگوریتم‌های جستجو",
    "06_Sorting_Algorithms": "الگوریتم‌های مرتب‌سازی",
    "07_Graph_Algorithms": "الگوریتم‌های گراف",
    "08_Dynamic_Programming": "الگوریتم‌های برنامه‌نویسی پویا",
    "09_Greedy_Algorithms": "الگوریتم‌های حریصانه",
    "10_Geometric_Mathematical": "الگوریتم‌های هندسی و ریاضی"
}

# ==================== UTILITY FUNCTIONS ====================

def retry(tries=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
    """Retry decorator for functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            for attempt in range(_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == _tries - 1:
                        raise
                    logger.warning(f"{func.__name__}: retry {attempt+1}/{tries} after {_delay:.1f}s")
                    time.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator

def human_sleep(min_s: float = 5.0, max_s: float = 10.0):
    """Random sleep to mimic human behavior"""
    t = random.uniform(min_s, max_s)
    logger.info(f"⏳ Sleeping {t:.1f}s...")
    time.sleep(t)

def safe_filename(name: str) -> str:
    """Make filename safe for filesystem"""
    name = name.strip().replace(" ", "_")
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "")
    return name or "untitled"

# ==================== QUERA SCRAPER CLASS ====================

class QueraScraper:
    BASE_URL = "https://quera.org"
    
    def __init__(self, email: str, password: str, headless: bool = False):
        self.email = email
        self.password = password
        
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("detach", True)
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        if headless:
            self.options.add_argument("--headless=new")
        
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 20)
        self.cookies_file = "quera_cookies.pkl"
        
        self.target_courses = {
            "14834": "مبانی برنامه‌سازی-پاییز ۱۴۰۲",
            "17076": "برنامه سازی پیشرفته",
            "18934": "ساختمان داده و الگوریتم ها",
            "23310": "طراحی و تحلیل الگوریتم‌ها",
        }
    
    def save_cookies(self):
        try:
            with open(self.cookies_file, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
            logger.info("🍪 Cookies saved")
        except Exception as e:
            logger.warning(f"Cookie save error: {e}")
    
    def load_cookies(self) -> bool:
        if not os.path.exists(self.cookies_file):
            return False
        try:
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            with open(self.cookies_file, "rb") as f:
                for cookie in pickle.load(f):
                    cookie.pop("sameSite", None)
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        pass
            logger.info("🍪 Cookies loaded")
            return True
        except Exception as e:
            logger.warning(f"Cookie load error: {e}")
            return False
    
    def is_logged_in(self) -> bool:
        try:
            self.driver.get(f"{self.BASE_URL}/dashboard")
            time.sleep(4)
            return "accounts/login" not in self.driver.current_url
        except:
            return False
    
    @retry(tries=3, delay=3, exceptions=(TimeoutException, WebDriverException))
    def login(self):
        logger.info("🚀 Logging in to Quera...")
        self.driver.get(f"{self.BASE_URL}/accounts/login")
        
        user_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "identifier")))
        user_field.send_keys(self.email, Keys.RETURN)
        
        pass_field = self.wait.until(EC.visibility_of_element_located((By.NAME, "password")))
        pass_field.send_keys(self.password, Keys.RETURN)
        
        self.wait.until_not(EC.url_contains("/accounts/login"))
        
        if self.is_logged_in():
            logger.info("✅ Login successful")
            self.save_cookies()
        else:
            raise RuntimeError("Login failed")
    
    def scrape_all_courses(self, base_dir: str = BASE_DIR):
        """Main scraping method - scrapes all courses and saves statements"""
        logger.info("=" * 70)
        logger.info("🚀 STARTING QUERA SCRAPER")
        logger.info("=" * 70)
        
        # Login
        if self.load_cookies() and self.is_logged_in():
            logger.info("✅ Using existing session")
        else:
            self.login()
        
        # Navigate and get courses
        self.driver.get(f"{self.BASE_URL}/course")
        human_sleep(5, 8)
        
        courses = self._extract_course_links()
        os.makedirs(base_dir, exist_ok=True)
        
        for course in courses:
            self._scrape_course(course, base_dir)
            human_sleep(15, 30)
        
        logger.info(f"✅ Scraping complete! Files in: {os.path.abspath(base_dir)}")
    
    def _extract_course_links(self) -> List[Dict]:
        """Extract target course links"""
        found = []
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/course/']")
        
        for link in links:
            href = link.get_attribute("href") or ""
            try:
                course_id = href.split("/course/")[1].split("/")[0].split("?")[0].strip()
                if course_id in self.target_courses and course_id not in [c["id"] for c in found]:
                    found.append({
                        "id": course_id,
                        "name": self.target_courses[course_id],
                        "url": f"{self.BASE_URL}/course/{course_id}"
                    })
            except:
                continue
        
        logger.info(f"✅ Found {len(found)} target courses")
        return found
    
    def _scrape_course(self, course: Dict, base_dir: str):
        """Scrape a single course"""
        logger.info(f"\n📚 Processing: {course['name']}")
        
        course_dir = os.path.join(base_dir, f"{course['id']}_{safe_filename(course['name'])}")
        os.makedirs(course_dir, exist_ok=True)
        
        self.driver.get(course["url"])
        human_sleep(5, 8)
        
        # Get assignments
        assignments = self._get_assignments()
        
        for assignment in assignments:
            self._scrape_assignment(assignment, course_dir)
            human_sleep(10, 20)
    
    def _get_assignments(self) -> List[Dict]:
        """Get assignments from current course page"""
        assignments = []
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/course/assignments/']")
        
        for link in links:
            href = link.get_attribute("href") or ""
            try:
                assignment_id = href.split("/assignments/")[1].split("/")[0].strip()
                name = (link.text or "").strip() or f"Assignment {assignment_id}"
                
                if assignment_id not in [a["id"] for a in assignments]:
                    assignments.append({
                        "id": assignment_id,
                        "name": name,
                        "url": href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    })
            except:
                continue
        
        logger.info(f"  ➜ Found {len(assignments)} assignments")
        return assignments
    
    def _scrape_assignment(self, assignment: Dict, course_dir: str):
        """Scrape a single assignment"""
        logger.info(f"  📝 Assignment: {assignment['name']}")
        
        assignment_dir = os.path.join(course_dir, f"{assignment['id']}_{safe_filename(assignment['name'])}")
        os.makedirs(assignment_dir, exist_ok=True)
        
        self.driver.get(assignment["url"])
        human_sleep(5, 8)
        
        # Get problems
        problems = self._get_problems()
        
        for problem in problems:
            self._scrape_problem(problem, assignment_dir)
            human_sleep(5, 10)
    
    def _get_problems(self) -> List[Dict]:
        """Get problems from current assignment page"""
        problems = []
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-pid]")
        
        for link in links:
            problem_id = link.get_attribute("data-pid") or ""
            if not problem_id:
                continue
            
            href = link.get_attribute("href") or ""
            name = (link.text or "").split("\n")[0].strip() or f"Problem {problem_id}"
            
            problems.append({
                "id": problem_id,
                "name": name,
                "url": href if href.startswith("http") else f"{self.BASE_URL}{href}"
            })
        
        logger.info(f"    ➜ Found {len(problems)} problems")
        return problems
    
    def _scrape_problem(self, problem: Dict, assignment_dir: str):
        """Scrape a single problem and save statement"""
        logger.info(f"    🔍 Problem: {problem['name']}")
        
        self.driver.get(problem["url"])
        human_sleep(5, 9)
        
        # Check rate limit
        if "به کجا چنین شتابان" in self.driver.page_source:
            logger.warning("⚠️ Rate limited! Waiting 90s...")
            time.sleep(90)
            self.driver.get(problem["url"])
            human_sleep(5, 9)
        
        try:
            # Get problem text
            markdown_div = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='description_md-'], article"))
            )
            text = markdown_div.get_attribute("textContent") or ""
            
            # Get title
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
            except:
                title = problem["name"]
            
            # Save to file
            problem_dir = os.path.join(assignment_dir, safe_filename(title))
            os.makedirs(problem_dir, exist_ok=True)
            
            with open(os.path.join(problem_dir, "statement.txt"), "w", encoding="utf-8") as f:
                f.write(f"{title}\n\n{text.strip()}")
            
            logger.info(f"      ✅ Saved statement")
        
        except Exception as e:
            logger.error(f"      ❌ Error: {e}")
    
    def close(self):
        """Close browser"""
        try:
            self.driver.quit()
        except:
            pass

# ==================== AI CLASSIFIER ====================

class AIClassifier:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "Quera Classifier"
            }
        )
    
    def classify_and_summarize(self, problem_text: str) -> str:
        """Classify problem and generate bilingual summary"""
        categories_list = "\n".join([f"{i+1}. {name} - {desc}" 
                                     for i, (name, desc) in enumerate(CATEGORIES.items())])
        
        prompt = f"""You are an expert at classifying CS problems.

Given a programming problem:
1. Classify into ONE category
2. Extract core problem (remove stories)
3. Provide summaries in English and Persian with LaTeX support

Categories:
{categories_list}

Problem:
{problem_text[:2000]}

Format:
CATEGORY: [exact category name like "01_Linear_Data_Structures"]

## English Summary
[summary with $inline$ and $$block$$ LaTeX]

## Persian Summary / خلاصه فارسی
[خلاصه با فرمول‌های LaTeX]
"""
        
        response = self.client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at classifying CS problems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    def organize_problems(self, base_path: str, output_path: str):
        """Organize all problems by category"""
        logger.info("=" * 70)
        logger.info("🤖 AI CLASSIFICATION & ORGANIZATION")
        logger.info("=" * 70)
        
        base_path = Path(base_path)
        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True)
        
        # Create category folders
        for cat in list(CATEGORIES.keys()) + ["00_Uncategorized"]:
            (output_path / cat).mkdir(exist_ok=True)
        
        stats = {cat: 0 for cat in list(CATEGORIES.keys()) + ["00_Uncategorized"]}
        
        # Process all problems
        for root, dirs, files in os.walk(base_path):
            if "statement.txt" not in files:
                continue
            
            folder_name = Path(root).name
            statement_path = Path(root) / "statement.txt"
            
            try:
                logger.info(f"📄 Processing: {folder_name}")
                
                with open(statement_path, 'r', encoding='utf-8') as f:
                    problem_text = f.read()
                
                # Classify
                ai_response = self.classify_and_summarize(problem_text)
                category = self._extract_category(ai_response)
                
                logger.info(f"   📁 Category: {category}")
                
                # Copy to organized folder
                problem_folder = output_path / category / folder_name
                problem_folder.mkdir(exist_ok=True)
                
                for file in Path(root).glob("*"):
                    if file.is_file():
                        shutil.copy2(file, problem_folder / file.name)
                
                # Create README
                readme_lines = [line for line in ai_response.split('\n') 
                               if not line.startswith('CATEGORY:')]
                with open(problem_folder / "README.md", 'w', encoding='utf-8') as f:
                    f.write(f"# {folder_name}\n\n{''.join(readme_lines).strip()}")
                
                stats[category] += 1
                logger.info(f"   ✅ Done")
                
            except Exception as e:
                logger.error(f"   ❌ Error: {e}")
        
        # Print stats
        logger.info("\n" + "=" * 70)
        logger.info("📊 CLASSIFICATION RESULTS:")
        for cat, count in stats.items():
            if count > 0:
                logger.info(f"   {cat}: {count} problems")
        logger.info("=" * 70)
    
    def _extract_category(self, ai_response: str) -> str:
        """Extract category from AI response"""
        for line in ai_response.split('\n'):
            if line.startswith('CATEGORY:'):
                category = line.replace('CATEGORY:', '').strip()
                if category in CATEGORIES:
                    return category
        return "00_Uncategorized"

# ==================== GITHUB UPLOADER ====================

class GitHubUploader:
    def __init__(self, local_path: str, username: str, repo_name: str):
        self.local_path = Path(local_path)
        self.username = username
        self.repo_name = repo_name
    
    def upload(self):
        """Upload to GitHub"""
        logger.info("=" * 70)
        logger.info("🚀 UPLOADING TO GITHUB")
        logger.info("=" * 70)
        
        os.chdir(self.local_path)
        
        # Check Git
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except:
            logger.error("❌ Git not installed!")
            return
        
        # Initialize
        if not (self.local_path / ".git").exists():
            subprocess.run(["git", "init"], check=True)
            subprocess.run(["git", "branch", "-M", "main"], check=True)
        
        # Create README
        self._create_readme()
        
        # Create .gitignore
        self._create_gitignore()
        
        # Add files
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "add", ".gitignore"], check=True)
        subprocess.run(["git", "add", "**/README.md"], check=True)
        
        for ext in [".c", ".cpp", ".py", ".java", ".js", ".cs", ".go"]:
            subprocess.run(["git", "add", f"**/*{ext}"], capture_output=True)
        
        # Commit
        subprocess.run(["git", "commit", "-m", "Add Quera problems with AI summaries"], check=True)
        
        # Add remote
        remote_url = f"https://github.com/{self.username}/{self.repo_name}.git"
        result = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if "origin" not in result.stdout:
            subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
        # Push
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True)
        
        logger.info(f"🎉 SUCCESS! Check: https://github.com/{self.username}/{self.repo_name}")
    
    def _create_readme(self):
        """Create main README"""
        readme = """# 🎯 Quera Programming Problems

Collection of programming problems from [Quera](https://quera.org) with AI-generated summaries in English and Persian.

## 📚 Categories

- 1️⃣ Linear Data Structures | ساختمان داده‌های خطی
- 2️⃣ Tree Structures | ساختمان داده‌های درختی
- 3️⃣ Graph Structures | ساختمان داده‌های گرافی
- 4️⃣ Advanced Data Structures | ساختمان داده‌های پیشرفته
- 5️⃣ Search Algorithms | الگوریتم‌های جستجو
- 6️⃣ Sorting Algorithms | الگوریتم‌های مرتب‌سازی
- 7️⃣ Graph Algorithms | الگوریتم‌های گراف
- 8️⃣ Dynamic Programming | برنامه‌نویسی پویا
- 9️⃣ Greedy Algorithms | الگوریتم‌های حریصانه
- 🔟 Geometric & Mathematical | هندسی و ریاضی

## 🤖 AI-Powered

All summaries generated using AI. Bilingual documentation.

## 📝 Note

Educational purposes only. Problems © [Quera.org](https://quera.org)

---

<div dir="rtl">
مجموعه مسائل برنامه‌نویسی کوئرا با خلاصه هوشمند
</div>
"""
        with open(self.local_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme)
        logger.info("✅ README created")
    
    def _create_gitignore(self):
        """Create .gitignore"""
        gitignore = """statement.txt
ai_summary.txt
input.txt
output.txt
__pycache__/
*.pyc
.DS_Store
"""
        with open(self.local_path / ".gitignore", 'w') as f:
            f.write(gitignore)
        logger.info("✅ .gitignore created")

# ==================== MAIN PIPELINE ====================

def main():
    """Complete pipeline: Scrape → Classify → Upload"""
    
    # Step 1: Scrape Quera
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: SCRAPING QUERA")
    logger.info("=" * 70 + "\n")
    
    scraper = QueraScraper(QUERA_EMAIL, QUERA_PASSWORD, headless=False)
    try:
        scraper.scrape_all_courses(BASE_DIR)
    finally:
        scraper.close()
    
    # Step 2: Classify with AI
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: AI CLASSIFICATION")
    logger.info("=" * 70 + "\n")
    
    classifier = AIClassifier(OPENROUTER_API_KEY)
    classifier.organize_problems(BASE_DIR, ORGANIZED_DIR)
    
    # Step 3: Upload to GitHub
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3: GITHUB UPLOAD")
    logger.info("=" * 70 + "\n")
    
    uploader = GitHubUploader(ORGANIZED_DIR, GITHUB_USERNAME, GITHUB_REPO_NAME)
    uploader.upload()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ COMPLETE PIPELINE FINISHED!")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
