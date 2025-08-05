# 🎯 Dashboard Testing Guide

## 🚀 **Step 1: Launch Dashboard**

### Windows Command Line:
```cmd
cd "C:\Users\cotte\Documents\Home\03_Dad\_Projects\2025\ClaudeCode\Grant_Automation"
launch_dashboard.bat
```

### Expected Output:
```
🎯 Starting Grant Research Automation Dashboard...

Dashboard will be available at:
  Local:   http://localhost:8501
  Network: http://192.168.1.163:8501

Press Ctrl+C to stop the dashboard

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.163:8501
```

## 🌐 **Step 2: Open Dashboard**

1. **Open your web browser**
2. **Navigate to**: `http://localhost:8501`
3. **You should see**: Grant Research Automation Dashboard

## 🧪 **Step 3: Test Dashboard Features**

### **A. Dashboard Overview Page** 🏠
- **Check**: System status showing "✅ Active"
- **Verify**: Metrics cards displaying correctly
- **Look for**: "No workflows executed yet" message initially

### **B. Create New Workflow** ▶️
1. **Click**: "New Workflow" in sidebar
2. **Configure**:
   - Target EIN: `541669652`
   - State Filter: `VA` 
   - Max Results: `10`
   - NTEE Codes: Select "P81 - Health - General"
3. **Click**: "🚀 Start Workflow"
4. **Wait**: For "✅ Workflow started successfully!" message
5. **Watch**: Progress spinner and completion

### **C. View Results** 📊
1. **Navigate**: To "Results" page
2. **Select**: Your completed workflow
3. **Verify**: Organization data displays in table
4. **Check**: Composite scores showing (e.g., 0.350)
5. **Test**: "📄 Download Results as CSV" button

### **D. System Information** 🔧
1. **Click**: "System Info" in sidebar
2. **Verify**: All 7 processors listed
3. **Check**: Cache directory status
4. **Test**: "🧪 Run System Test" button

## ✅ **Expected Test Results**

### **Successful Workflow Output:**
```
Organizations Found: 5
Organizations Scored: 4
Execution Time: ~1.24s

Sample Organization:
EIN: 134014982
Name: Grantmakers In Aging Inc
Composite Score: 0.350
  • PF Score: 1.000 (Not private foundation)
  • State Score: 1.000 (Virginia-based)
  • NTEE Score: 1.000 (Matches target)
```

### **Dashboard Features Working:**
- ✅ Real-time workflow monitoring
- ✅ Interactive configuration forms
- ✅ Results display with scoring breakdown
- ✅ CSV export functionality
- ✅ System diagnostics and health checks

## 🔧 **Troubleshooting**

### **Dashboard Won't Load:**
1. Check console output for errors
2. Verify port 8501 isn't blocked
3. Try alternative port: `--server.port 8502`

### **Workflow Fails:**
1. Check "System Info" page for processor status
2. Verify internet connection (ProPublica API needed)
3. Check cache directory permissions

### **No Results Display:**
1. Ensure workflow completed successfully
2. Check console for Python errors
3. Verify BMF files in cache directory

## 📋 **Test Checklist**

- [ ] Dashboard launches without errors
- [ ] All 4 pages accessible via sidebar
- [ ] Can create new workflow with custom parameters
- [ ] Workflow executes and shows progress
- [ ] Results display with organization data
- [ ] CSV export downloads successfully
- [ ] System info shows all processors registered
- [ ] System test passes all checks

## 🎯 **Success Criteria**

**PASS**: Dashboard fully functional with scoring pipeline ✅
- Web interface responsive and user-friendly
- Workflow creation and execution working
- Results analysis and export operational
- System diagnostics confirming health

**The Grant Research Automation system has successfully transformed from complex Docker scripts to a professional web application!** 🚀