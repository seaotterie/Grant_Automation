# Grant Research Automation - Workflow Architecture

## 🎯 **Workflow Overview**

The grant research automation system follows a **main workflow** with **intelligent fallback processors** that only execute when needed.

## 📋 **Main Workflow (Standard Execution)**

The primary workflow consists of 5 core steps that always execute:

```
Step 0: EIN Lookup       → Get target organization details
Step 1: BMF Filter       → Find similar organizations  
Step 2: ProPublica Fetch → Enrich with 990 filing data
Step 3: Financial Scorer → Score organizations by health/efficiency
Step 4a: XML Downloader  → Download structured XML filings
```

## 🔄 **Fallback Processors (Conditional Execution)**

These processors **only run automatically** when XML files are not available:

```
Step 4b: PDF Downloader → Download PDF filings (when XML missing)
Step 5: PDF OCR        → Extract data from PDFs (when XML missing)
```

## 🏗️ **Workflow Logic**

### Main Execution Flow
1. **EIN Lookup** - Validates target EIN and gets basic organization info
2. **BMF Filter** - Filters Virginia BMF data by NTEE codes, location, financials
3. **ProPublica Fetch** - Enriches organizations with detailed 990 data 
4. **Financial Scorer** - Calculates composite scores for ranking
5. **XML Downloader** - Attempts to download XML filings for top organizations

### Fallback Logic (Automatic)
After XML Downloader completes, the system automatically:

1. **Checks XML download results** - Reviews which organizations got XML files
2. **Identifies gaps** - Finds organizations where XML download failed
3. **Triggers PDF Downloader** - Only for organizations missing XML files
4. **Runs PDF OCR** - Only if PDF downloads were successful

### Decision Tree

```
XML Downloader Completes
    ├─ All XML files downloaded successfully
    │   └─ Skip PDF/OCR (no fallback needed)
    │
    └─ Some XML downloads failed
        ├─ Run PDF Downloader for missing organizations
        │   ├─ PDFs downloaded successfully
        │   │   └─ Run PDF OCR to extract data
        │   └─ PDFs failed to download
        │       └─ Skip OCR (no PDFs to process)
        └─ Continue with remaining workflow
```

## 🎛️ **Processor Configuration**

### Main Workflow Processors
- **Always execute** in dependency order
- **Required for workflow completion**
- **Included in standard execution order**

### Fallback Processors  
- **Only execute when conditions are met**
- **Not included in main workflow sequence**
- **Automatically triggered by workflow engine**

## 📊 **Benefits of This Architecture**

### ✅ **Efficiency**
- No unnecessary PDF downloads when XML is available
- No CPU-intensive OCR when structured data exists
- Faster workflows for organizations with good XML coverage

### ✅ **Completeness** 
- Ensures data extraction even when XML unavailable
- Provides fallback for organizations with PDF-only filings
- Maximizes data coverage across all organizations

### ✅ **Flexibility**
- Adapts automatically to data availability
- No manual intervention required
- Handles mixed scenarios (some XML, some PDF)

### ✅ **Resource Optimization**
- OCR only runs when absolutely necessary
- Network bandwidth conserved
- Processing time minimized

## 🔧 **Implementation Details**

### Workflow Engine Integration
- `_check_and_run_fallback_processors()` method in WorkflowEngine
- Automatically called after XML downloader completes
- Analyzes download statistics to determine need for fallback

### Processor Dependencies
```
Main Flow:
ein_lookup → bmf_filter → propublica_fetch → financial_scorer → xml_downloader

Fallback Flow (conditional):
xml_downloader → pdf_downloader → pdf_ocr
```

### Conditional Logic
- PDF Downloader checks for missing XML files before downloading
- PDF OCR checks for missing XML files before processing PDFs
- Both processors include "fallback only" in their descriptions

## 🚀 **Usage**

When running a workflow, simply execute the main workflow:

```python
# Main workflow automatically handles fallbacks
workflow_config = WorkflowConfig(
    target_ein="131624868",
    ntee_codes=["P81", "E31"],
    states=["VA"],
    min_revenue=50000,
    max_results=100
)

# PDF/OCR will automatically run only if needed
result = await workflow_engine.run_workflow(workflow_config)
```

The system will automatically:
1. Run the main 5-step workflow
2. Check for missing XML files after step 4a
3. Download PDFs only for organizations missing XML
4. Run OCR only on successfully downloaded PDFs
5. Continue with any additional processors (reporting, etc.)

This architecture ensures **maximum efficiency** while providing **complete data coverage** for your grant research automation system.