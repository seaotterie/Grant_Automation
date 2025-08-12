# Catalynx Web Interface - Startup Guide

## 🚀 Quick Start

### Step 1: Start the Server
```bash
# Option A: Use the launcher (Recommended)
launch_catalynx_web.bat

# Option B: Manual start
cd src/web
"../../grant-research-env/Scripts/python.exe" main.py
```

### Step 2: Verify Server is Running
You should see output like:
```
Starting Catalynx Web Interface on http://127.0.0.1:8000
Press Ctrl+C to stop the server
==================================================
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO: Catalynx API ready!
```

### Step 3: Access the Interface
Open your web browser and go to:
- **Main Interface**: http://127.0.0.1:8000
- **API Test Page**: http://127.0.0.1:8000/static/test.html
- **API Documentation**: http://127.0.0.1:8000/api/docs

## 🔧 Troubleshooting

### Issue: "NetworkError when attempting to fetch resource"

**This has been FIXED with the following improvements:**

1. **API Retry Logic**: Automatic retries for failed requests
2. **Better Error Handling**: Graceful fallbacks when APIs fail
3. **Timeout Management**: 30-second timeouts with retry logic
4. **Initialization Delays**: Wait for server startup before making API calls

### Issue: Website loads but times out

**Solution**: The interface now handles timeouts gracefully:
- APIs that fail will retry automatically
- Safe defaults are used if APIs are unavailable
- User gets clear error messages instead of crashes

### Issue: Cannot connect to server

**Check these steps:**
1. Make sure the server is running (see Step 1 above)
2. Check that you're using the correct URL: http://127.0.0.1:8000
3. Try the API test page: http://127.0.0.1:8000/static/test.html
4. Check Windows Firewall isn't blocking port 8000

### Issue: Server starts but APIs don't work

1. **Check the API test page**: http://127.0.0.1:8000/static/test.html
2. **Check browser console**: Press F12 and look for errors in the Console tab
3. **Check server logs**: Look at the terminal where the server is running

## 🎯 Features Available

### Real-Time Interface
- **Dashboard**: System statistics and live progress monitoring
- **Classification**: Intelligent classification with real-time progress
- **Workflows**: Complete workflow management
- **Analytics**: Performance metrics and visualizations
- **Exports**: Download results in multiple formats

### WebSocket Features
- Live progress updates during classification
- Real-time qualification breakdown
- Processing speed and ETA calculations
- Automatic reconnection on disconnects

## ✅ Verification Steps

1. **Start the server** using `launch_catalynx_web.bat`
2. **Open http://127.0.0.1:8000** - should show the Catalynx dashboard
3. **Check API test page** at http://127.0.0.1:8000/static/test.html - all tests should pass
4. **Try classification** - click "Classification" tab and start a test run
5. **Monitor progress** - you should see real-time updates

## 📊 What's Working

- ✅ FastAPI backend with 12 processors registered
- ✅ Professional WordPress-style interface
- ✅ Real-time WebSocket progress monitoring
- ✅ Automatic API retry logic and error handling
- ✅ Responsive design with Tailwind CSS
- ✅ Interactive data tables and charts
- ✅ Export management with download functionality

## 🎉 Success Indicators

When everything is working correctly, you should see:
- Server starts with "Catalynx API ready!" message
- Dashboard loads with system statistics
- API test page shows all green "SUCCESS" results
- Classification can be started and shows real-time progress
- No "NetworkError" messages in browser console

The network timeout and fetch errors have been resolved with robust retry logic and graceful error handling!