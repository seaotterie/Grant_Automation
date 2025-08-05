# 🧭 Grant Automation System — Workflow Overview

## ✅ Workflow 1: EIN-Driven Profile Generation

**Purpose:** Create a structured nonprofit profile from a single EIN to serve as the foundation for bulk filtering and grant prospecting.

### Key Components:
- EIN as Entry Point  
- Fetch ProPublica BMF JSON + IRS 990 XML  
- Keyword Extraction + NTEE Matching  
- Top 10 NTEE Code Suggestions  
- User Review Interface  
- Finalized Profile Saved  
- Master Profile List for Future Use  

---

## 🔄 Workflow 2: Bulk Filtering, Scoring & XML Retrieval

**Purpose:** Use the NTEE profile to identify potential peer or aligned nonprofits for funding analysis.

### Key Components:
- Input: EIN profile’s reviewed NTEE codes  
- Filter IRS BMF dataset (starting with Virginia)  
- Score filtered orgs using profile-specific rubric  
- Pull IRS 990 XMLs for orgs scoring ≥ 0.7  

---

## 📊 Workflow 3: Deeper Scoring and Opportunity Refinement

**Purpose:** Perform a second scoring pass using rich XML content.

### Key Components:
- Extract & parse additional schedules (O, A, I, etc.)  
- Analyze narrative sections (e.g., mission, program service)  
- Improve rubric score via AI/NLP or rule-based logic  
- Output enhanced score + structured insights  

---

## 🧬 Workflow 4: Board of Directors Relationship Mapping

**Purpose:** Detect possible personal or organizational connections between candidates and the initiating nonprofit.

### Key Components:
- Extract board member names from Part VII of 990  
- Build relationship graphs  
- Compare against profile nonprofit’s known affiliates  
- Flag matches or influential overlaps  
- Adjust opportunity score accordingly  

---

## 🧩 Workflow 5: Schedule I Grant Relationship Mapping

**Purpose:** Map outbound grant patterns and identify potential opportunity paths.

### Key Components:
- Parse Schedule I for grants to orgs/individuals  
- Build connection graphs (granter → grantee)  
- Identify shared targets or funding ecosystems  
- Add new prospects or refine existing ones  
- Feed results into score and recommendations  

---

## 🚀 Workflow 6: Dossier Creation + Grant Planning Triggers

**Purpose:** Generate reports, export data, and initiate grant pursuit actions.

### Key Components:
- **Create Dossier Workbook**:
  - Tabs: Filter Config, Scores, Downloaded XMLs, Board/Grant Relationships, Notes
  - Export to `/data/output/dossiers/`  
- **Generate Summary Reports (PDF, Markdown, Excel)**  
- **Flag High-Scoring Opportunities for Pursuit**  
- **Trigger Grant Writing or Outreach Actions (optional)**  
- **Track Status of Each Opportunity** via GUI or n8n