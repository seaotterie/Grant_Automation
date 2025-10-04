# Quick Start: Modal Integration (10 Minutes)

**Status**: Ready to integrate
**Time Required**: 10 minutes
**Files to Edit**: 1 (index.html)

---

## Step 1: Add Modal Scripts (5 minutes)

**File**: `src/web/static/index.html`

**Location**: Add before closing `</body>` tag (line ~10587)

```html
    <!-- Modal System (Phase 9 Week 4) -->
    <script src="/static/modules/modal-component.js"></script>
    <script src="/static/modules/modal-loader.js"></script>

</body>
</html>
```

---

## Step 2: Test It Works (5 minutes)

### 2.1 Start Server

```bash
python src/web/main.py
```

Or:
```bash
launch_catalynx_web.bat
```

### 2.2 Open Browser

Navigate to: `http://localhost:8000`

### 2.3 Check Console

You should see:
```
Modal Loader: Initializing...
Modal Loader: Loaded /static/templates/profile-modals.html
Modal Loader: Loaded /static/templates/ntee-selection-modal.html
Modal Loader: Loaded /static/templates/government-criteria-modal.html
Modal Loader: Loaded /static/templates/create-delete-modals.html
Modal Loader: All templates loaded successfully
```

### 2.4 Test Modals

1. Click **PROFILES** stage
2. Click **"+ New Profile"** button
   - ✅ Create Profile modal should appear
   - ✅ Should show 2 tabs (EIN Lookup / Manual Entry)

3. If you have existing profiles, click **"Edit"** on any profile
   - ✅ Edit Profile modal should appear
   - ✅ Should show 5 tabs

4. Click **"Delete"** on any profile
   - ✅ Delete confirmation modal should appear

**That's it!** If all 3 modals open, integration is successful.

---

## Troubleshooting

### Modals don't appear
**Check**: Browser console for errors
**Fix**: Verify modal-loader.js and modal-component.js paths are correct

### Buttons don't work
**Check**: Are you in PROFILES stage?
**Fix**: Click "PROFILES" in the 3-stage navigation

### API errors
**Expected**: Create/Edit/Delete will show API errors until backend is ready
**Normal**: Focus on modal UI appearing correctly first

---

## Next Steps

✅ **Modals appearing?** → Move to `WEEK4_FINAL_SUMMARY.md` for full testing

⏳ **Issues?** → Check `MODAL_INTEGRATION_GUIDE.md` for detailed troubleshooting

---

**Total Time**: ~10 minutes for full integration!
