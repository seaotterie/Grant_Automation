@echo off
echo ====================================
echo Grant Research Automation Setup
echo ====================================

echo.
echo Step 1: Activating virtual environment...
call grant-research-env\Scripts\activate.bat

echo.
echo Step 2: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 3: Installing core dependencies...
pip install wheel setuptools

echo.
echo Step 4: Installing all project dependencies...
pip install -r requirements.txt

echo.
echo Step 5: Installing development dependencies...
pip install -r requirements-auth.txt

echo.
echo Step 6: Verifying installation...
python -c "import pandas, requests, streamlit, cryptography, click, pydantic; print('✅ Core libraries imported successfully')"

echo.
echo Step 7: Testing authentication system...
python -c "from src.auth.api_key_manager import get_api_key_manager; print('✅ Authentication system ready')"

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To activate the environment in the future, run:
echo   grant-research-env\Scripts\activate.bat
echo.
echo To test the authentication system, run:
echo   python setup_auth.py status
echo.
echo To start the dashboard (after setup), run:
echo   streamlit run src/dashboard/app.py
echo.
pause