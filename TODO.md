# TODO - Major UI Stability Fixes & Help Module Admin Enhancements

## Implementation Plan (Confirmed per User)

### Phase 1: Help Module Admin Content Management
- [ ] **views/help.py** - Add admin content-management mode with "+" action buttons per tab
  - Add "＋" button on each Help tab header (Guide, FAQs, System Requirements)
  - For admin only: open modal to add entries (title + bullet lines + admin_only flag for Guide, question + answer for FAQ, category + label + value for System Requirement)
  - Add admin inline edit/delete controls per rendered guide/faq/spec card
  - Persist custom additions/edits in DB tables while keeping built-in defaults as fallback
  - Clarify export behavior: Add note stating PDF export is in Reports module
  - Optional: Add "Open Reports" shortcut button

### Phase 2: Borrow/Return Logs & Validation Hardening  
- [x] **views/borrowing.py** - Borrow/Return logs modal:
  - Remove "🖨️ Reprint Receipt" button in deployment details modal for logs/history view
- [x] **views/borrowing.py** - Retrieval validation hardening:
  - Require verified employee, verified tool/TRN, quantity > 0
  - Require return condition to be explicitly selected and condition details non-empty when condition != "Good"
- [x] **views/borrowing.py** - Issuance validation hardening:
  - Require employee verified, project selected, non-empty cart
  - Add pre-submit summary check for missing required data and fail fast with precise messages

### Phase 3: Calendar Uniformity Fix
- [x] **views/borrowing.py** - Deployment Schedule calendar:
  - Replace manual per-cell frame packing approach with fixed 7x6 grid strategy
  - Always render 6 week rows, each row fixed minsize and uniform cell height/width
  - Use grid_propagate(False) on each cell + consistent internal anchor layout
  - Center/clip-safe day numbers and indicator dots
  - This removes per-month shape drift and incomplete day rendering

### Phase 4: Table Clipping/Alignment System-Wide
- [x] Root cause: header/row minsize calculation + scrollbar padding mismatch + insufficient right gutter
- [x] Apply stronger table layout helper changes:
  - Increase base width in minsize computation from 1100 to dynamic container width when available (fallback to 1350)
  - Standardize right padding for header/data containers to account for scrollbar width
  - Ensure all table row labels keep sticky="w" and headers use sticky="ew", anchor="center"
- [x] Target files:
  - [x] dashboard.py
  - [x] views/projects.py
  - [x] views/inventory.py
  - [x] views/borrowing.py
  - [x] views/tagging.py
  - [x] views/reports.py
  - [x] views/tracking.py
  - [x] views/maintenance.py
  - [x] views/role_management.py
  - [x] views/profile.py

### Phase 5: Venv Prompt Default (Windows PowerShell)
- [x] Non-code guidance + command setup:
  - Add .venv\Scripts\Activate.ps1 usage
  - Optionally add profile auto-activation snippet for this project path
  - Add VSCode setting recommendation: Python: Select Interpreter = .venv\Scripts\python.exe

### Phase 6: Testing Follow-up
- [x] Runtime checks on affected modules:
  - Table clipping and alignment screenshots across modules
  - Deployment Schedule calendar month-to-month uniformity
  - Borrow/return validation flows
  - Help admin add/edit/delete flow and tab "+" controls
  - Confirm no regressions in Reports export "⎙ Export Now"

## Progress Tracking
- [ ] Create/update task checklist and mark progress while implementing each item

## Already Implemented (From Previous Sessions)
- [x] Quick Actions row removed from dashboard
- [x] Action Items card clickable to Maintenance
- [x] Tagging duplicate empty header removed
- [x] Export dialog button label changed to "⎙ Export Now"
- [x] Auto-logout after 5 minutes inactivity implemented
- [x] Dashboard min window size set to 1350x750

## Final Validation
- [ ] Run syntax validation on edited files
- [ ] Summarize all completed changes
