# GUI User Testing Plan - Catalynx Web Interface

**Version**: 1.0
**Date**: 2025-10-10
**Phase**: Phase 9 - Production Readiness Validation
**Testing Duration**: 8-10 hours (3 days recommended)

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Environment Setup](#test-environment-setup)
3. [Test Scenarios](#test-scenarios)
4. [Cross-Cutting Concerns](#cross-cutting-concerns)
5. [Bug Triage Guidelines](#bug-triage-guidelines)
6. [Test Execution Tips](#test-execution-tips)

---

## Testing Philosophy

### Real-World User Focus

This is **not** a technical QA test. This is a **user experience validation** to answer:

- Can a grant researcher use this system without training?
- Are workflows intuitive and efficient?
- Does the system handle errors gracefully?
- Is performance acceptable for daily use?
- Can users accomplish their goals without frustration?

### Testing Mindset

**Think like a user, not a developer**:
- Don't excuse confusing workflows ("users will figure it out")
- Don't tolerate unhelpful error messages ("it's clear to me")
- Don't accept slow performance ("it's fast enough")
- Don't skip mobile testing ("desktop is more important")
- Don't ignore accessibility ("most users don't need it")

**Document everything**:
- Screenshot confusing UI elements
- Record error messages verbatim
- Note timestamps for performance issues
- Capture browser console errors
- Document workarounds you discover

---

## Test Environment Setup

### 1. Pre-Testing System Verification

#### Server Health Check
```bash
# Launch web server
launch_catalynx_web.bat

# Verify startup messages
# Expected output:
# - "Uvicorn running on http://127.0.0.1:8000"
# - "Application startup complete"
# - No error messages

# Check homepage
# Open browser: http://localhost:8000
# Expected: Catalynx dashboard loads in <2 seconds
```

#### Database Verification
```bash
# Check databases exist
dir data\catalynx.db                    # Application database
dir data\nonprofit_intelligence.db      # Intelligence database (6-8GB)

# Expected:
# - Both files exist
# - nonprofit_intelligence.db is 6-8GB in size
```

#### API Documentation Check
```
# Open in browser
http://localhost:8000/api/docs

# Expected:
# - OpenAPI (Swagger) documentation loads
# - All endpoints are documented
# - "Try it out" feature works
```

### 2. Browser Setup

#### Recommended Browsers (Test in Order)
1. **Chrome 90+** (Primary) - Best DevTools, most users
2. **Firefox 88+** (Secondary) - Cross-browser validation
3. **Edge 90+** (Tertiary) - Windows enterprise users
4. **Safari 14+** (Optional) - Mac users

#### Browser DevTools Setup
```
# Open DevTools (F12 or Ctrl+Shift+I)

# Essential Tabs:
1. Console - Monitor for errors and warnings
2. Network - Track API calls and performance
3. Performance - Lighthouse audits
4. Application - Check storage and caching

# Disable cache during testing:
Network tab → Check "Disable cache"
```

#### Mobile Device Emulation
```
# Chrome DevTools
1. Click device toolbar icon (Ctrl+Shift+M)
2. Test these device sizes:
   - Mobile: 375x667 (iPhone SE)
   - Tablet: 768x1024 (iPad)
   - Desktop: 1920x1080 (Full HD)
```

### 3. Test Data Preparation

#### Sample Data Files

Create these test files in `test_data/` directory:

**test_profile_minimal.json** (Minimum required fields):
```json
{
  "organization_name": "Test Nonprofit",
  "ein": "12-3456789",
  "organization_type": "NONPROFIT",
  "status": "active"
}
```

**test_profile_complete.json** (All fields):
```json
{
  "organization_name": "Complete Test Organization",
  "ein": "98-7654321",
  "organization_type": "NONPROFIT",
  "status": "active",
  "mission_statement": "Empowering communities through education and technology",
  "focus_areas": ["education", "technology", "youth"],
  "ntee_codes": ["B25", "T20"],
  "primary_ntee_code": "B25",
  "annual_revenue": 1500000,
  "state": "VA",
  "city": "Richmond",
  "zip_code": "23219"
}
```

**test_opportunities_200.csv** (For batch screening):
```csv
opportunity_id,title,agency,amount,deadline
OPP-001,STEM Education Grant,NSF,500000,2025-12-31
OPP-002,Community Development,HUD,250000,2025-11-30
... (200 rows total)
```

---

## Test Scenarios

---

## Scenario 1: Profile Management Workflow

**Duration**: 15 minutes
**User Persona**: Grant Researcher setting up their organization
**Goal**: Create and manage nonprofit organization profile

### Test Case 1.1: Create New Profile (Happy Path)

**Steps**:
1. Navigate to http://localhost:8000
2. Click "Create New Profile" or "Add Profile" button
3. Fill in required fields:
   - Organization Name: "Test Nonprofit Organization"
   - EIN: "12-3456789" (valid format)
   - Organization Type: Select "Nonprofit"
4. Click "Create" or "Save"

**Expected Results**:
- ✅ Form accepts input without errors
- ✅ EIN format is validated (shows checkmark or "valid" indicator)
- ✅ Profile is created successfully
- ✅ Success notification appears ("Profile created successfully")
- ✅ Profile appears in profiles list immediately
- ✅ User is redirected to profile detail view

**Performance Target**: <1 second from click to success

**What to Watch For**:
- Is the form intuitive? Are labels clear?
- Does EIN validation happen in real-time or on submit?
- Are error messages helpful if validation fails?
- Does the success notification timeout appropriately?

---

### Test Case 1.2: Create Profile with Invalid Data

**Steps**:
1. Click "Create New Profile"
2. Test each validation rule:
   - **Test A**: Leave Organization Name blank, try to submit
   - **Test B**: Enter invalid EIN "123456789" (missing hyphen)
   - **Test C**: Enter invalid EIN "00-0000000" (invalid prefix)
   - **Test D**: Leave Organization Type unselected

**Expected Results for Each Test**:
- ✅ Form does NOT submit
- ✅ Specific error message appears near the invalid field
- ✅ Error message is clear and actionable ("EIN must be in format XX-XXXXXXX")
- ✅ Other valid fields retain their values (don't clear the form)
- ✅ Focus moves to the first invalid field

**What to Watch For**:
- Are error messages visible and clear?
- Does the form feel responsive (real-time validation)?
- Is it obvious which field has the error?
- Does the form preserve user input after validation?

---

### Test Case 1.3: Edit Existing Profile

**Steps**:
1. Select an existing profile from the list
2. Click "Edit" or edit icon
3. Modify these fields:
   - Mission Statement: Add 2-3 sentence description
   - Focus Areas: Add "education", "technology"
   - Annual Revenue: Enter "$1,500,000"
4. Click "Save Changes"

**Expected Results**:
- ✅ Edit mode activates (fields become editable)
- ✅ Current values pre-populate in form
- ✅ Changes save successfully
- ✅ Success notification appears
- ✅ Updated values display immediately (no page refresh needed)
- ✅ Profile list updates with new data

**Performance Target**: <500ms from save to update

**What to Watch For**:
- Is edit mode clearly indicated (visual cue)?
- Can user cancel editing without saving?
- Are changes saved immediately or after clicking save?
- Does the interface feel responsive?

---

### Test Case 1.4: Search and Filter Profiles

**Steps**:
1. Create 5 test profiles with varied data:
   - Different organization names
   - Different EIN numbers
   - Different organization types
   - Different states
2. Use search box to find profiles by:
   - **Test A**: Organization name (partial match)
   - **Test B**: EIN number
   - **Test C**: Mission statement keywords
3. Use filters to narrow results:
   - **Test D**: Filter by organization type
   - **Test E**: Filter by state
   - **Test F**: Combine search + filter

**Expected Results**:
- ✅ Search is case-insensitive
- ✅ Partial matches work ("Test" finds "Test Nonprofit")
- ✅ Results update in real-time as user types
- ✅ Filters work correctly
- ✅ Combined search + filter works as expected
- ✅ "No results" message appears if nothing matches
- ✅ Clear/reset button returns to full list

**Performance Target**: <200ms search response

**What to Watch For**:
- Is search debounced (doesn't search on every keystroke)?
- Are results highlighted or indicated clearly?
- Can user easily clear search/filters?
- Does the search feel fast and responsive?

---

### Test Case 1.5: Archive and Restore Profile

**Steps**:
1. Select a profile from the list
2. Click "Archive" or "Delete" button
3. Confirm action in confirmation dialog
4. Verify profile is archived (removed from active list)
5. Navigate to "Archived Profiles" view
6. Select archived profile
7. Click "Restore" button

**Expected Results**:
- ✅ Confirmation dialog appears before archiving
- ✅ Profile is removed from active list
- ✅ Success notification: "Profile archived successfully"
- ✅ Archived profile appears in "Archived" section
- ✅ Restore button is visible and functional
- ✅ Restored profile returns to active list
- ✅ All profile data is preserved during archive/restore

**What to Watch For**:
- Is there accidental deletion protection?
- Is it clear how to find archived profiles?
- Can user undo accidental archive?
- Are there soft delete vs hard delete options?

---

## Scenario 2: Discovery & Research Workflow

**Duration**: 20 minutes
**User Persona**: Grant Researcher searching for potential funders
**Goal**: Discover 470+ matching organizations using BMF database

### Test Case 2.1: Start BMF Discovery Session

**Steps**:
1. Select a profile (or create one if none exist)
2. Navigate to "Discovery" or "Find Opportunities" section
3. Click "Start BMF Discovery" or similar
4. Observe discovery interface loads

**Expected Results**:
- ✅ Discovery interface loads in <2 seconds
- ✅ Profile information is pre-populated if applicable
- ✅ Filter options are visible and understandable
- ✅ Help text or tooltips explain how to use discovery
- ✅ No console errors appear

**What to Watch For**:
- Is it clear what BMF discovery does?
- Are filter options overwhelming or intuitive?
- Is there guidance for first-time users?

---

### Test Case 2.2: Apply Filters and Search

**Steps**:
1. Apply these filters one at a time, observing results:
   - **NTEE Codes**: Select "B25" (Higher Education)
   - **States**: Select "VA", "MD", "DC" (multi-select)
   - **Revenue Range**: Set min $1M, max $10M
   - **Organization Type**: Select "Foundation"
2. Click "Search" or "Apply Filters"

**Expected Results**:
- ✅ Search completes in <3 seconds (searching 2M+ records)
- ✅ Loading indicator appears during search
- ✅ Results display in table or card format
- ✅ Results count is accurate (e.g., "Found 472 organizations")
- ✅ Results are sortable by column (name, revenue, state)
- ✅ Pagination works if >50 results

**Performance Target**: <3 seconds for 2M+ record search

**What to Watch For**:
- Does the loading state give feedback?
- Are results clearly formatted and readable?
- Can user modify filters without starting over?
- Is the results count prominent and accurate?

---

### Test Case 2.3: Review Discovery Results

**Steps**:
1. Examine results table/cards
2. Sort results by different columns:
   - Organization Name (A-Z, Z-A)
   - Annual Revenue (high to low, low to high)
   - State (alphabetical)
3. Click on an organization to view details
4. Navigate back to results

**Expected Results**:
- ✅ Results are clearly formatted with key information
- ✅ Sorting works correctly for each column
- ✅ Detail view shows comprehensive organization data
- ✅ Back button returns to exact place in results
- ✅ Results are paginated if >50 records
- ✅ Pagination preserves sorting and filters

**What to Watch For**:
- Is key information visible without clicking?
- Are results scannable (easy to review quickly)?
- Does detail view load quickly?
- Is navigation intuitive?

---

### Test Case 2.4: Export Results

**Steps**:
1. After viewing results, click "Export" button
2. Select export format:
   - **Test A**: CSV format
   - **Test B**: Excel format
   - **Test C**: JSON format (if available)
3. Download and open each file

**Expected Results**:
- ✅ Export button is prominently visible
- ✅ Format options are clear
- ✅ Export completes in <5 seconds for 400-500 records
- ✅ File downloads automatically
- ✅ CSV file opens in Excel/Sheets without errors
- ✅ Excel file has proper formatting (columns, headers)
- ✅ JSON file is valid JSON structure
- ✅ All data from results is included in export

**What to Watch For**:
- Is export format selection intuitive?
- Does export include all result columns?
- Are column headers descriptive?
- Is the filename descriptive (includes date/time)?

---

### Test Case 2.5: Save Discovery Session

**Steps**:
1. Complete a discovery search with filters
2. Click "Save Session" or "Save Search"
3. Enter session name: "VA/MD/DC Higher Ed Foundations"
4. Navigate away from discovery
5. Return and load saved session

**Expected Results**:
- ✅ Save option is available after search completes
- ✅ Session name is editable and descriptive
- ✅ Session saves successfully with confirmation
- ✅ Saved sessions appear in "My Searches" or similar
- ✅ Loading saved session restores all filters and results
- ✅ User can edit or delete saved sessions

**What to Watch For**:
- Is it obvious how to save a session?
- Can user find saved sessions easily?
- Are saved sessions persistent across logins?

---

## Scenario 3: Opportunity Screening Workflow

**Duration**: 25 minutes
**User Persona**: Grant Researcher screening 200 opportunities
**Goal**: Screen opportunities → Get 10-15 recommendations

### Test Case 3.1: Import Opportunity List

**Steps**:
1. Navigate to "Opportunity Screening" section
2. Click "Import Opportunities" or "Batch Upload"
3. Select import method:
   - **Test A**: CSV file upload (test_opportunities_200.csv)
   - **Test B**: Paste JSON data
   - **Test C**: Manual entry (single opportunity)
4. Review import preview
5. Confirm import

**Expected Results**:
- ✅ File upload interface is clear and accessible
- ✅ Supported formats are listed (CSV, JSON, Excel)
- ✅ File validates before import (shows preview)
- ✅ Invalid data shows specific errors with row numbers
- ✅ Import completes in <10 seconds for 200 records
- ✅ Progress bar shows import progress
- ✅ Success notification shows count: "200 opportunities imported"
- ✅ Opportunities appear in opportunities list

**What to Watch For**:
- Is the import process intuitive?
- Are error messages specific and helpful?
- Does the preview help catch errors?
- Is progress indication adequate for large imports?

---

### Test Case 3.2: Run Fast Screening Mode (Tool 1)

**Steps**:
1. Select imported opportunities (all 200)
2. Choose "Fast Screening" mode (Tool 1)
3. Click "Start Screening"
4. Monitor progress via:
   - Progress bar
   - WebSocket real-time updates
   - Status messages
5. Wait for completion (~2 minutes for 200 opportunities)

**Expected Results**:
- ✅ Screening starts immediately after click
- ✅ Progress bar updates in real-time (every 1-2 seconds)
- ✅ Status messages show current opportunity being screened
- ✅ Estimated time remaining is displayed
- ✅ User can cancel screening mid-process
- ✅ Screening completes in ~2 minutes (200 opportunities)
- ✅ Success notification appears on completion
- ✅ Results load automatically

**Performance Target**: ~2 minutes for 200 opportunities (~0.6s per opportunity)

**What to Watch For**:
- Is progress feedback adequate?
- Can user work on other tabs while screening runs?
- Does the UI feel responsive during screening?
- Are WebSocket updates smooth or choppy?

---

### Test Case 3.3: Review Screening Results

**Steps**:
1. View screening results table/cards
2. Examine result columns:
   - Opportunity title
   - Overall score (0-100)
   - Eligibility score
   - Geographic score
   - Timing score
   - Financial score
   - Recommendation (HIGH/MEDIUM/LOW)
3. Sort by different columns
4. Filter by recommendation level

**Expected Results**:
- ✅ Results display in clear, scannable format
- ✅ Scores are color-coded (green/yellow/red)
- ✅ Recommendation badges are prominent
- ✅ Sorting works for all numeric columns
- ✅ Filters narrow results correctly
- ✅ HIGH recommendations appear first by default
- ✅ User can click opportunity for detailed view

**What to Watch For**:
- Are scores easy to understand?
- Is the recommendation logic clear?
- Can user quickly identify top opportunities?
- Is the table overwhelming or well-organized?

---

### Test Case 3.4: Apply Filters and Refine Results

**Steps**:
1. Start with all 200 screening results
2. Apply filters to narrow down:
   - **Filter A**: Recommendation = "HIGH"
   - **Filter B**: Eligibility score ≥ 80
   - **Filter C**: Amount range $250K - $1M
   - **Filter D**: Deadline within next 90 days
3. Combine multiple filters
4. Export filtered results to CSV

**Expected Results**:
- ✅ Filters apply instantly (<200ms)
- ✅ Results count updates (e.g., "15 of 200 opportunities")
- ✅ Combined filters work with AND logic
- ✅ Clear all filters button resets to full list
- ✅ Filtered results can be exported
- ✅ Export includes only filtered records

**What to Watch For**:
- Are filter options intuitive?
- Is it clear how many results match?
- Can user easily clear filters?
- Does filtering feel fast and responsive?

---

### Test Case 3.5: Select Opportunities for Deep Analysis

**Steps**:
1. Review top 10-15 HIGH recommendation opportunities
2. Select opportunities using checkboxes
3. Click "Deep Analysis" or "Analyze Selected"
4. Choose analysis depth:
   - ESSENTIALS ($2 per opportunity)
   - PREMIUM ($8 per opportunity)
5. Review cost estimate (10 × $2 = $20)
6. Confirm and proceed to Scenario 4

**Expected Results**:
- ✅ Checkbox selection works smoothly
- ✅ "Select All" option available
- ✅ Selected count displays (e.g., "10 selected")
- ✅ Deep Analysis button is enabled when ≥1 selected
- ✅ Cost calculator shows accurate estimate
- ✅ Depth level options are clearly explained
- ✅ User can modify selection before confirming

**What to Watch For**:
- Is selection clear and responsive?
- Is cost transparency helpful or confusing?
- Are depth level differences explained?
- Can user easily adjust selection?

---

## Scenario 4: Deep Intelligence Workflow

**Duration**: 30 minutes
**User Persona**: Grant Researcher performing deep analysis
**Goal**: Comprehensive analysis of 10 selected opportunities

### Test Case 4.1: Start Deep Intelligence Analysis

**Steps**:
1. With 10 opportunities selected from screening
2. Click "Start Deep Analysis" button
3. Confirm depth level (ESSENTIALS or PREMIUM)
4. Review analysis summary:
   - Number of opportunities: 10
   - Depth level: ESSENTIALS ($2 each)
   - Total cost: $20
   - Estimated time: 15-20 minutes
5. Click "Start Analysis"

**Expected Results**:
- ✅ Confirmation modal shows all details
- ✅ Cost and time estimates are accurate
- ✅ User can go back and change selection
- ✅ "Start Analysis" initiates Tool 2 execution
- ✅ Progress interface loads immediately
- ✅ No console errors appear

**What to Watch For**:
- Is the confirmation clear about what will happen?
- Are costs and time estimates helpful?
- Does the user have a chance to back out?

---

### Test Case 4.2: Monitor Real-Time Progress

**Steps**:
1. Observe progress monitoring interface
2. Watch WebSocket real-time updates:
   - Overall progress (0-100%)
   - Current opportunity being analyzed
   - Estimated time remaining
   - Analysis stage (PLAN → ANALYZE → EXAMINE → APPROACH)
3. Test browser behaviors:
   - **Test A**: Minimize browser, restore after 1 minute
   - **Test B**: Switch to another tab, return after 2 minutes
   - **Test C**: Refresh page (only if safe to test)

**Expected Results**:
- ✅ Progress bar updates every 5-10 seconds
- ✅ Status messages show current activity
- ✅ Estimated time remaining is reasonably accurate
- ✅ Analysis stage indicator updates correctly
- ✅ WebSocket reconnects if connection drops
- ✅ Progress persists if user switches tabs
- ✅ No page refresh needed to see updates

**What to Watch For**:
- Is progress feedback adequate for long-running task?
- Does the interface feel "alive" or "frozen"?
- Can user navigate away and return?
- Are WebSocket updates smooth?

---

### Test Case 4.3: Review Analysis Results

**Steps**:
1. After analysis completes (15-20 minutes), review results
2. For each analyzed opportunity, check:
   - Strategic Fit Analysis
   - Financial Viability Assessment
   - Operational Readiness Evaluation
   - Risk Assessment
   - Network Intelligence (if included)
   - Historical Intelligence
   - Geographic Analysis
3. Compare results across opportunities
4. Sort by overall score or recommendation

**Expected Results**:
- ✅ Results load immediately after completion
- ✅ All analysis modules are present
- ✅ Results are well-formatted and readable
- ✅ Charts/visualizations render correctly
- ✅ Detailed insights are actionable
- ✅ Comparison view available
- ✅ Export option is available

**What to Watch For**:
- Are results overwhelming or well-organized?
- Is the analysis depth appropriate for price?
- Are insights actionable or generic?
- Can user quickly identify top opportunities?

---

### Test Case 4.4: Generate Professional Report

**Steps**:
1. Select 1 analyzed opportunity
2. Click "Generate Report" button
3. Choose report template:
   - **Test A**: Comprehensive Report (20+ pages)
   - **Test B**: Executive Summary (2-3 pages)
   - **Test C**: Risk Analysis Report
4. Select output format:
   - HTML (web view)
   - PDF (download)
5. Generate and review report

**Expected Results**:
- ✅ Report generation starts immediately
- ✅ Generation completes in <10 seconds
- ✅ HTML report displays in new tab/modal
- ✅ PDF downloads automatically
- ✅ Report is professionally formatted
- ✅ All analysis sections are included
- ✅ Charts and tables render correctly
- ✅ Report is ready to share with stakeholders

**Performance Target**: <10 seconds for report generation

**What to Watch For**:
- Are report templates clearly differentiated?
- Is the report professional enough for stakeholders?
- Are charts and visualizations high quality?
- Is the PDF file size reasonable (<5MB)?

---

### Test Case 4.5: Export Analysis Package

**Steps**:
1. Select all 10 analyzed opportunities
2. Click "Export Package" or "Export All"
3. Choose export options:
   - Include raw data (JSON)
   - Include summary report (PDF)
   - Include opportunity details (CSV)
   - Include analysis results (Excel)
4. Click "Export Package"
5. Download and extract ZIP file

**Expected Results**:
- ✅ Export options are clear and configurable
- ✅ Package generation completes in <15 seconds
- ✅ ZIP file downloads automatically
- ✅ ZIP file includes all selected components
- ✅ Files are organized in logical folders
- ✅ All file formats open correctly
- ✅ Data integrity is maintained in all formats

**What to Watch For**:
- Is the export package comprehensive?
- Are files organized logically?
- Can stakeholders open and use these files?
- Is the export process efficient?

---

## Scenario 5: System Administration Workflow

**Duration**: 15 minutes
**User Persona**: System Administrator or Power User
**Goal**: Monitor system health and manage data

### Test Case 5.1: View System Dashboard

**Steps**:
1. Navigate to "Dashboard" or "Overview" section
2. Review dashboard metrics:
   - Total profiles count
   - Active opportunities count
   - Screening jobs (completed/running)
   - Analysis jobs (completed/running)
   - API usage statistics
   - System health indicators
3. Observe auto-refresh behavior

**Expected Results**:
- ✅ Dashboard loads in <2 seconds
- ✅ All metrics display with current values
- ✅ Metrics auto-refresh every 30-60 seconds
- ✅ Charts visualize trends over time
- ✅ Health indicators are green (healthy)
- ✅ No stale data (timestamps are current)

**What to Watch For**:
- Are metrics meaningful and actionable?
- Is the refresh rate appropriate?
- Are health indicators clear?
- Is the dashboard overwhelming or clean?

---

### Test Case 5.2: Check Tool Status

**Steps**:
1. Navigate to "Tools" or "System Status" section
2. Review tool inventory:
   - Should show 22 operational tools
   - Tool names, versions, status
3. Click on individual tool to view details:
   - Tool description
   - Last execution time
   - Success rate
   - Average execution time
   - Configuration

**Expected Results**:
- ✅ All 22 tools show "operational" status
- ✅ Tool details are comprehensive
- ✅ Status indicators are color-coded
- ✅ Tool versions are accurate
- ✅ Last execution data is recent (if tools were used)
- ✅ No deprecated tools appear unless archived

**What to Watch For**:
- Is tool status immediately obvious?
- Are tool names and descriptions clear?
- Can admin quickly identify issues?

---

### Test Case 5.3: Review API Documentation

**Steps**:
1. Navigate to http://localhost:8000/api/docs
2. Review API documentation structure
3. Test "Try it out" feature:
   - **Test A**: GET /api/profiles (list profiles)
   - **Test B**: POST /api/profiles (create profile)
   - **Test C**: GET /health (health check)
4. Review response schemas and examples

**Expected Results**:
- ✅ API docs load in <1 second
- ✅ All endpoints are documented
- ✅ Request/response schemas are clear
- ✅ "Try it out" feature works correctly
- ✅ Example requests are valid
- ✅ Authentication requirements are documented
- ✅ Error responses are documented

**What to Watch For**:
- Is API documentation complete?
- Are examples helpful?
- Can a developer integrate with the API using this documentation?

---

### Test Case 5.4: Test Individual Tool Endpoints

**Steps**:
1. In API docs, navigate to Tool execution endpoints
2. Test these tool endpoints:
   - **Tool 1**: POST /api/tools/opportunity-screening
   - **Tool 2**: POST /api/tools/deep-intelligence
   - **Tool 17**: POST /api/tools/bmf-filter
3. Provide sample input data
4. Execute and review response

**Expected Results**:
- ✅ All tool endpoints respond successfully
- ✅ Input validation works correctly
- ✅ Tools execute and return structured output
- ✅ Response includes execution metadata
- ✅ Error responses are descriptive
- ✅ Execution time is acceptable (<30s)

**What to Watch For**:
- Are tool APIs consistent?
- Are errors handled gracefully?
- Is output structure documented?

---

### Test Case 5.5: Export System Logs

**Steps**:
1. Navigate to "Logs" or "System Logs" section
2. Filter logs by:
   - **Test A**: Date range (last 7 days)
   - **Test B**: Log level (ERROR, WARNING, INFO)
   - **Test C**: Component (web, api, tools)
3. Export filtered logs to file
4. Review exported log file

**Expected Results**:
- ✅ Logs display in reverse chronological order
- ✅ Filters work correctly
- ✅ Log entries are readable and informative
- ✅ Export completes in <5 seconds
- ✅ Exported file is valid format (CSV/JSON)
- ✅ No sensitive data exposed in logs

**What to Watch For**:
- Are logs useful for debugging?
- Can admin find relevant logs quickly?
- Is log export efficient?

---

## Cross-Cutting Concerns

### WebSocket Real-Time Updates

**Test Across All Scenarios**:
- [ ] WebSocket connects on page load (check console)
- [ ] Progress updates appear in real-time
- [ ] Multiple browser tabs receive updates
- [ ] Connection recovers after network interruption
- [ ] Updates are smooth, not choppy or delayed
- [ ] No duplicate messages received
- [ ] WebSocket disconnects gracefully on page unload

**How to Test**:
1. Open browser console
2. Look for "WebSocket connected" message
3. Monitor messages during long-running operations
4. Disconnect network briefly, observe reconnection

---

### Chart.js Visualizations

**Test Across All Scenarios**:
- [ ] Bar charts render correctly
- [ ] Line charts show trends accurately
- [ ] Pie charts display percentages
- [ ] Interactive tooltips work on hover
- [ ] Charts are responsive (resize with window)
- [ ] Color schemes are consistent
- [ ] Charts are accessible (keyboard navigation)
- [ ] Export chart as image works (if available)

**Chart Types to Test**:
1. **Screening Results**: Bar chart of score distributions
2. **Discovery Results**: Pie chart of organization types
3. **Deep Intelligence**: Radar chart of dimensional scores
4. **Dashboard**: Line chart of usage trends
5. **Reports**: Multiple chart types in PDF exports

---

### API Error Handling

**Test Across All Scenarios**:
- [ ] Network errors show "Connection failed" message
- [ ] 400 errors show specific validation errors
- [ ] 401 errors redirect to login (if auth enabled)
- [ ] 403 errors show "Permission denied" message
- [ ] 404 errors show "Resource not found" message
- [ ] 500 errors show "Server error" with retry option
- [ ] Rate limit errors show "Too many requests" message
- [ ] Timeouts show "Request timed out" with retry option

**How to Test**:
1. Simulate network failure (disable Wi-Fi briefly)
2. Submit invalid data to trigger 400 errors
3. Request non-existent resources for 404 errors
4. Monitor console for unhandled errors

---

### Form Validation

**Test Across All Scenarios**:
- [ ] Required fields show error on submit
- [ ] Real-time validation provides instant feedback
- [ ] Error messages are specific and actionable
- [ ] Valid input shows green checkmark or success indicator
- [ ] Tab key navigation follows logical order
- [ ] Enter key submits form (where appropriate)
- [ ] Escape key cancels form (where appropriate)
- [ ] Form preserves input after validation error

**Validation Rules to Test**:
1. **EIN Format**: Must match XX-XXXXXXX pattern
2. **Email Format**: Valid email address
3. **Date Validation**: Future dates only for deadlines
4. **Numeric Ranges**: Min/max values enforced
5. **Text Length**: Character limits displayed and enforced

---

### Loading States and Feedback

**Test Across All Scenarios**:
- [ ] Loading spinners appear immediately on action
- [ ] Progress bars update smoothly
- [ ] Skeleton screens display during initial load
- [ ] "Loading..." text is descriptive ("Loading profiles...")
- [ ] Estimated time remaining is shown for long operations
- [ ] User can cancel long-running operations
- [ ] Success/failure notifications appear after completion
- [ ] Loading states don't block entire interface

**What Good Loading States Look Like**:
- Immediate feedback (<100ms)
- Descriptive messages ("Analyzing 10 opportunities...")
- Progress indication (20% complete, 2 minutes remaining)
- Option to cancel or navigate away
- Success confirmation when complete

---

### Mobile Responsiveness

**Test at 3 Screen Sizes**:

#### Mobile (375x667 - iPhone SE)
- [ ] Hamburger menu appears and works
- [ ] Tables scroll horizontally or reflow
- [ ] Forms are touch-friendly (no tiny inputs)
- [ ] Buttons are at least 44x44px (Apple guideline)
- [ ] Text is readable without zooming (16px minimum)
- [ ] Modals fit on screen without scrolling
- [ ] Charts are legible and interactive
- [ ] No horizontal scrolling on main content

#### Tablet (768x1024 - iPad)
- [ ] Layout uses available space efficiently
- [ ] Sidebar/navigation is accessible
- [ ] Tables display more columns than mobile
- [ ] Two-column layouts work well
- [ ] Touch targets are appropriately sized
- [ ] Charts are clear and interactive

#### Desktop (1920x1080 - Full HD)
- [ ] Layout is not stretched or cramped
- [ ] Multi-column layouts are used effectively
- [ ] Tables show all columns without scrolling
- [ ] Charts are large and detailed
- [ ] Dashboard makes good use of space
- [ ] No wasted whitespace

---

### Accessibility (WCAG 2.1 AA)

**Keyboard Navigation**:
- [ ] Tab key moves focus logically through page
- [ ] Shift+Tab moves focus backwards
- [ ] Enter key activates buttons and links
- [ ] Escape key closes modals and dialogs
- [ ] Arrow keys navigate within components (dropdowns, tabs)
- [ ] Focus indicators are clearly visible
- [ ] Skip to main content link is available
- [ ] Keyboard traps are avoided (can always escape)

**Screen Reader Compatibility**:
- [ ] All images have alt text
- [ ] Form fields have associated labels
- [ ] ARIA labels are present for icons and buttons
- [ ] ARIA live regions announce dynamic updates
- [ ] Headings follow logical hierarchy (h1 → h2 → h3)
- [ ] Links have descriptive text (not "click here")
- [ ] Error messages are announced
- [ ] Tables have proper header associations

**Color Contrast**:
- [ ] Text on background ≥4.5:1 ratio (normal text)
- [ ] Large text on background ≥3:1 ratio (18pt+ bold or 24pt+)
- [ ] UI component contrast ≥3:1 (buttons, borders)
- [ ] Color is not the only indicator (use icons too)
- [ ] Links are distinguishable from surrounding text
- [ ] Error states use both color and text/icons

**How to Test**:
1. **Keyboard Navigation**: Unplug mouse, navigate entire interface
2. **Screen Reader**: Use NVDA (Windows) or JAWS to navigate
3. **Color Contrast**: Use Chrome DevTools Accessibility panel
4. **WCAG Audit**: Run Lighthouse accessibility audit (target score >90)

---

## Bug Triage Guidelines

### Severity Definitions

#### Critical (P0 - Fix Immediately)
- **Data Loss**: User data is deleted or corrupted
- **Security**: Vulnerability exposing sensitive data
- **Crash**: Application crashes or becomes unusable
- **Blocking Workflow**: Core workflow cannot be completed

**Examples**:
- Profile data is deleted when editing
- API authentication is broken (all requests fail)
- Page crashes with console error on load
- Cannot create profiles (blocking core feature)

---

#### High (P1 - Fix Before Release)
- **Major Feature Broken**: Important feature is non-functional
- **Poor UX**: Workflow is confusing or frustrating
- **Performance**: Operation takes >2x target time
- **Accessibility**: WCAG A violation (critical barrier)

**Examples**:
- BMF search returns no results (feature broken)
- Form validation is unclear (poor UX)
- Deep analysis takes 40 minutes instead of 20 (performance)
- Keyboard navigation doesn't work (accessibility)

---

#### Medium (P2 - Fix Soon)
- **Minor Feature Broken**: Optional feature is non-functional
- **UX Polish**: Small improvement needed
- **Performance**: Operation slightly slower than target
- **Accessibility**: WCAG AA violation (moderate barrier)

**Examples**:
- Export to Excel doesn't work (CSV export works)
- Button labels could be clearer
- Dashboard loads in 3s instead of 2s
- Color contrast is 4.3:1 instead of 4.5:1

---

#### Low (P3 - Future Enhancement)
- **Enhancement**: New feature request
- **Cosmetic**: Visual polish or minor styling issue
- **Documentation**: Documentation improvement needed
- **Nice-to-Have**: Quality of life improvement

**Examples**:
- Add dark mode theme
- Adjust button padding by 2px
- Add more examples to API docs
- Add keyboard shortcut for common action

---

### Priority Assignment Matrix

| Severity | Impact High | Impact Medium | Impact Low |
|----------|-------------|---------------|------------|
| **Frequent** (>50% users) | P0 Critical | P1 High | P2 Medium |
| **Occasional** (10-50% users) | P1 High | P2 Medium | P3 Low |
| **Rare** (<10% users) | P2 Medium | P3 Low | P3 Low |

---

## Test Execution Tips

### Effective Testing Practices

1. **Start Fresh**: Clear browser cache and cookies before testing
2. **Document Everything**: Screenshot, record screen, note timestamps
3. **Think Out Loud**: Narrate your thought process as you test
4. **Try to Break It**: Don't just follow happy paths, be adversarial
5. **Test Edge Cases**: Empty states, max values, special characters
6. **Vary Your Pace**: Test both fast clicks and slow deliberate actions
7. **Use Real Data**: Test with realistic organization names and amounts
8. **Check Console**: Monitor browser console for errors throughout
9. **Test Combinations**: Try unexpected combinations of features
10. **Take Breaks**: Fresh eyes catch more bugs

---

### Common Testing Pitfalls

❌ **Don't Do This**:
- Test only happy paths (everything works as expected)
- Ignore console errors ("it still works")
- Test only on desktop ("most users have desktops")
- Skip documentation review ("I know how it works")
- Rush through tests ("I'll test quickly")
- Dismiss UX issues ("users will figure it out")
- Ignore performance ("it's fast enough for me")
- Skip accessibility ("not my job")

✅ **Do This Instead**:
- Test both happy and unhappy paths
- Investigate every console error
- Test on mobile, tablet, and desktop
- Review documentation as a new user would
- Take time to thoroughly test each scenario
- Document every UX confusion or frustration
- Measure performance against targets
- Test basic accessibility (keyboard, screen reader)

---

### When to Stop Testing

**You're Done When**:
- ✅ All 5 test scenarios completed
- ✅ All critical features tested
- ✅ All bugs documented with screenshots
- ✅ Performance benchmarks recorded
- ✅ Accessibility audit completed
- ✅ Mobile responsiveness validated
- ✅ Production readiness assessment drafted

**Don't Stop Until**:
- You can confidently recommend production deployment
- You've identified all blocking issues
- You've given actionable feedback for improvements
- You've validated the system works for real users

---

## Next Steps After Testing

### 1. Compile Test Results
- Use `docs/GUI_TEST_RESULTS_TEMPLATE.md` to document findings
- Organize bugs by severity (P0, P1, P2, P3)
- Record performance benchmarks
- Note accessibility violations

### 2. Create Bug Reports
- File detailed bug reports for each issue
- Include screenshots and reproduction steps
- Assign severity and priority
- Suggest fixes or workarounds

### 3. Write Production Readiness Assessment
- Overall verdict: Ready / Needs Work / Not Ready
- List blocking issues (must fix before deployment)
- List high priority improvements (should fix soon)
- Timeline estimate for fixes

### 4. Plan Phase 9 Continuation
- Prioritize bug fixes
- Schedule UX improvements
- Plan performance optimizations
- Define acceptance criteria for deployment

---

## Appendix: Quick Reference

### URLs
- Homepage: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

### Performance Targets
- Page load: <2s
- API response: <500ms
- BMF search: <3s
- Tool execution: <5s (screening), 15-20min (deep intelligence)
- Report generation: <10s

### Accessibility Targets
- WCAG 2.1 AA compliance
- Keyboard navigation fully functional
- Screen reader compatible
- Color contrast ≥4.5:1

### Test Data
- Test EIN: 12-3456789 (valid format)
- Invalid EIN: 123456789 (missing hyphen)
- Test Organization: "Test Nonprofit Organization"

---

**Good luck with testing!** Remember: You're testing for **real users in real scenarios**, not just checking boxes. Your honest feedback will determine production readiness.
