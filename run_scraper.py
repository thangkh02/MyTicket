import os
import subprocess
import sys
import platform

def setup_environment():
    """
    Set up a virtual environment and install required dependencies
    """
    print("Setting up virtual environment...")
    
    # Determine command prefix based on OS
    is_windows = platform.system() == "Windows"
    python_cmd = "python" if is_windows else "python3"
    
    # Create virtual environment if it doesn't exist
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        subprocess.run([python_cmd, "-m", "venv", venv_dir], check=True)
    
    # Determine activation command and pip path
    if is_windows:
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
        activate_cmd = os.path.join(venv_dir, "Scripts", "activate")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        activate_cmd = os.path.join(venv_dir, "bin", "activate")
    
    print("Installing dependencies...")    # Install required packages
    requirements = [
        "django",
        "selenium",
        "beautifulsoup4",
        "requests",
        "pillow",
        "webdriver-manager",
        "unidecode",  # Add unidecode for slug creation
        "django-recaptcha"  # Add django-recaptcha for form handling
    ]
    
    if is_windows:
        # On Windows, we need to activate the virtual environment and then run pip
        cmd = f"{activate_cmd} && {pip_path} install {' '.join(requirements)}"
        subprocess.run(cmd, shell=True)
    else:
        # On Unix-like systems
        for req in requirements:
            subprocess.run([pip_path, "install", req], check=True)
    
    print("Environment setup completed.")

def run_scraper():
    """
    Run the web scraper script
    """
    print("Running web scraper...")
    
    is_windows = platform.system() == "Windows"
    if is_windows:
        # On Windows, activate the virtual environment and run the script
        subprocess.run(f"{os.path.join('venv', 'Scripts', 'activate')} && python crawl_data.py", shell=True)
    else:
        # On Unix-like systems
        python_path = os.path.join("venv", "bin", "python")
        subprocess.run([python_path, "crawl_data.py"])

if __name__ == "__main__":
    try:
        setup_environment()
        run_scraper()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
