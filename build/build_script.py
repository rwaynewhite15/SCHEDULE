"""
Build script for creating the Life Wellness Calendar desktop application
Run this script to build the .exe file
"""
import os
import sys
import subprocess

def build_app():
    print("=" * 60)
    print("Building Life Wellness Calendar Desktop Application")
    print("=" * 60)
    
    # Change to the build directory
    build_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(build_dir)
    print(f"\n📁 Working directory: {os.getcwd()}")
    
    # Check if icon exists
    if not os.path.exists('calendar_app.ico'):
        print("\n⚠️  Icon file not found!")
        print("Attempting to create icon...")
        try:
            subprocess.run([sys.executable, 'icon.py'], check=True)
            print("✅ Icon created successfully!")
        except subprocess.CalledProcessError:
            print("⚠️  Could not create icon. Continuing without custom icon...")
        except FileNotFoundError:
            print("⚠️  icon.py not found. Continuing without custom icon...")
    else:
        print("\n✅ Icon file found: calendar_app.ico")
    
    # Check if PyInstaller is installed
    print("\n📦 Checking for PyInstaller...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'show', 'pyinstaller'], 
                      capture_output=True, check=True)
        print("✅ PyInstaller is installed")
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found!")
        print("Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                          check=True)
            print("✅ PyInstaller installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            print("Please install manually: pip install pyinstaller")
            return
    
    # Check if other dependencies are installed
    print("\n📋 Checking dependencies...")
    required_packages = ['tkcalendar', 'anthropic', 'python-dotenv', 'requests', 'pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                          capture_output=True, check=True)
        except subprocess.CalledProcessError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                          check=True)
            print("✅ All dependencies installed!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print(f"Please install manually: pip install {' '.join(missing_packages)}")
            return
    else:
        print("✅ All dependencies are installed")
    
    # PyInstaller command
    print("\n📦 Building executable with PyInstaller...")
    print("This may take a few minutes...\n")
    
    icon_arg = '--icon=calendar_app.ico' if os.path.exists('calendar_app.ico') else ''
    
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--name=LifeWellnessCalendar',
        '--onefile',  # Single executable file
        '--windowed',  # No console window
        icon_arg,  # Custom icon (if available)
        '--add-data=.env;.' if sys.platform == 'win32' else '--add-data=.env:.',  # Include .env
        '--hidden-import=babel.numbers',  # Required for tkcalendar
        '--hidden-import=tkcalendar',
        '--hidden-import=anthropic',
        '--hidden-import=dotenv',
        '--collect-all=tkcalendar',
        'schedule_app.py'  # Main application script
    ]
    
    # Remove empty strings from command
    cmd = [arg for arg in cmd if arg]
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 60)
        print("\n📁 Your application is ready:")
        exe_path = os.path.join(build_dir, 'dist', 'LifeWellnessCalendar.exe')
        print(f"   Location: {exe_path}")
        print("\n💡 Next steps:")
        print("   1. Test the application: dist/LifeWellnessCalendar.exe")
        print("   2. Create a shortcut on your desktop")
        print("   3. Share with others (they don't need Python installed!)")
        print("\n⚠️  Important:")
        print("   - Make sure to include your .env file with API keys")
        print("   - The app will create calendar_data.json in the same folder")
        
    except subprocess.CalledProcessError as e:
        print("\n❌ Build failed!")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_app()