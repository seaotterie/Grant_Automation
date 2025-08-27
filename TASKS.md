# Tasks - <Grant_Automation>


## Modifications
- Add a sorting carrot to the Headers in the scrollable tables to allow sorting to table place
- Add the ability for a non-profit to upload a list of Grantors, EINs Date, and Grant value.
- Fix the tabs TOP banners above the banner.  The Title and search bar area
- DISCOVER Nonprofits area, what is the IRS data refer to if not the 990 and 990-PF
- Tables
    - freeze headers
    - Filter & Sorting headers

- Requests for Proposals (RFPs) – Philanthropy News Digest  https://philanthropynewsdigest.org/rfps
 
This page offers a free, regularly updated list of request-for-proposal notices and awarded grants published daily, focused on U.S.-based philanthropic opportunities. Let me know if you’d like help navigating or filtering listings by category or region!

## Comments
- While some non profits might not provide grants they may be of value from the BOD networking and Grantors Networking.



## New Features
Manual Inputs
- Websites like banks who manage foundations and trusts
- Donor lists similar to Schedule I but coming directly from the Profile and input manually
- Add a profile's grant package and docs outlining grant writing information, about us, past performance, metrics, non profit details to help with the APPROACH tab and grant writing
- Comments on View Details provided Promote and Demote reasoning
- Feedback loop where BOD and Grantor Networks feed back in to the DISCOVERY tab

## PLAN
 Phase 1: Backend Error Recovery System
     - Create src/core/error_recovery.py with comprehensive error classification, circuit breaker patterns, exponential backoff retry logic, and graceful degradation framework
     - Enhance AI Processors with specific error handling for OpenAI API failures, rate limits, timeouts, and authentication issues
     - Standardize error response format across all API endpoints with recovery guidance
     
     Phase 2: Frontend Error Handling Enhancement  
     - Enhance src/web/static/app.js with progressive error recovery, error state management in Alpine.js, and user-friendly error messages
     - Add retry mechanisms (automatic and user-initiated) with progress indication
     - Create error state UI with modals, toast notifications, and recovery buttons
     
     Phase 3: Help Documentation System
     - Create comprehensive user guides (docs/user-guide.md, docs/api-documentation.md, docs/processor-guide.md)
     - Enhance Settings Tab UI with "Help & Documentation" section
     - Add FastAPI documentation serving endpoints with markdown rendering