# Sorftime Exploration Task Quality Metrics

> **Core Principle**: Exists != Usable. Enumerated != Scanned. Explored != Recorded.

---

## 1. Completeness Metrics

| Metric | Calculation | Pass Threshold | Excellence Threshold |
|--------|-------------|----------------|----------------------|
| **Feature Coverage** | Verified Tabs / Total Tabs x 100% | >= 80% | 100% |
| **Field Coverage** | Enumerated Fields / Actual Fields x 100% | >= 90% | 100% |
| **Sub-Feature Exploration Rate** | Sub-Pages Visited / Sub-Pages Discovered x 100% | >= 70% | 100% |
| **Field Dictionary Completion Rate** | Defined Fields / Total Fields x 100% | >= 60% | >= 90% |

**Verification Method**:

```javascript
// Enumerate all tabs
const tabs = document.querySelectorAll('.el-tabs__item');
console.log('Total tabs:', tabs.length);

// Get field list after clicking export
const fields = document.querySelectorAll('.el-checkbox__label');
console.log('Total fields:', fields.length);
```

---

## 2. Verification Depth Metrics

| Metric | Calculation | Pass Threshold | Excellence Threshold |
|--------|-------------|----------------|----------------------|
| **Button Click Verification Rate** | Buttons Clicked / Buttons Discovered x 100% | >= 90% | 100% |
| **Dropdown Expand Verification Rate** | Dropdowns Expanded / Dropdowns Discovered x 100% | >= 80% | 100% |
| **Sub-Feature Click Verification Rate** | Features Clicked / Features Discovered x 100% | >= 80% | 100% |

**Pass Criteria**:

- ✅ All clickable elements clicked and verified
- ✅ All dropdown menus expanded to view options
- ✅ All discovered features have response records

---

## 3. Accuracy Metrics

| Metric | Calculation | Pass Threshold | Excellence Threshold |
|--------|-------------|----------------|----------------------|
| **Information Accuracy Rate** | Accurate Records / Total Records x 100% | >= 95% | 100% |
| **Field Definition Rate** | Defined Fields / Total Fields x 100% | >= 60% | >= 90% |
| **Directory Structure Match Rate** | Complete Canvas Nodes / Standard Nodes x 100% | >= 80% | 100% |

**Standard Node Checklist (Canvas must include)**:

```
✅ Feature Entry Points (including Tab list)
✅ Filter Dimensions (complete list)
✅ Export Fields (complete list) ⚠️
✅ Field Dictionary (definitions / data definitions) ⚠️
✅ Usage SOP
✅ Seller Value
```

**⚠️ Exhaustive Recording Principle (must comply)**

| Wrong Practice ❌ | Correct Practice ✅ |
|-------------------|---------------------|
| "119 dimensions verified" | Must list all 119 field names individually |
| "40+ filter dimensions" | Must fully enumerate all 40+ dimension names |
| "Multiple tabs" | Must list all tab names |
| "Contains X categories" | Must list all items by category, one by one |

**Anti-Patterns (observed cases)**:

- ❌ "✅ 108+ dimensions verified" — only recorded the total count, did not list details
- ✅ Market Dashboard Canvas: 11 categories, 119 fields listed individually (dim1-Market Trends 12 fields, dim2-Low-Price Market 6 fields...)

**Verification Command**:

```javascript
// Enumerate all field options (must click export/filter modal first, then execute)
const fields = await page.evaluate(() => {
  const labels = document.querySelectorAll('.el-checkbox__label');
  return [...new Set(Array.from(labels).map(l => l.innerText.trim()))];
});
console.log('Total fields:', fields.length);
console.log('Field list:', fields);
```

---

## 4. Process Compliance Metrics

| Metric | Calculation | Pass Threshold | Excellence Threshold |
|--------|-------------|----------------|----------------------|
| **Checkpoint Save Rate** | Checkpoints Saved / Checkpoints Should-Be-Saved x 100% | 100% | 100% |
| **Session Verification Rate** | Sessions Verified / Operations Performed x 100% | >= 80% | 100% |
| **Checklist Completion Rate** | Items Completed / Total Checklist Items x 100% | >= 80% | 100% |

**Checkpoint Save Triggers**:

- ✅ After every tab switch
- ✅ After every sub-page entry
- ✅ After completing a feature module
- ✅ Before session expiry

---

## 5. Quality Gate Checklist ⚠️ [All Must Pass]

| # | Check Item | Weight | Consequence of Failure |
|---|-----------|--------|------------------------|
| 1 | All tabs clicked and verified | Required | ❌ Not accepted |
| 2 | All filter options expanded and listed | Required | ❌ Not accepted |
| 3 | All export fields obtained | Required | ❌ Not accepted |
| 4 | At least 1 sub-page explored in depth | Required | ❌ Not accepted |
| 5 | Field dictionary completed (>= 60%) | Required | ⚠️ Degraded acceptance |
| 6 | Checkpoints saved | Required | ❌ Not accepted |
| 7 | SOP recorded | Recommended | ⚠️ Degraded acceptance |

---

## 6. Quantitative Scoring Formula

```
Exploration Quality Score =
  (Feature Coverage x 20%)
+ (Field Coverage x 25%)
+ (Verification Depth x 25%)
+ (Accuracy x 20%)
+ (Process Compliance x 10%)

Scoring Tiers:
- 90-100: Excellent ✅
- 70-89:  Pass ✅
- 60-69:  Needs Improvement ⚠️
- < 60:   Fail ❌
```

---

## 7. Pre / During / Post Exploration Checklists

### Pre-Exploration

- [ ] Read reference documentation (outline / legacy knowledge base)
- [ ] Confirm session is valid
- [ ] Check checkpoint (resume or create new)

### During Exploration

- [ ] Enumerate all tabs / buttons / filters / fields
- [ ] Click every tab, record findings
- [ ] Click Export, obtain complete field list
- [ ] Save checkpoint after every tab switch

### Post-Exploration

- [ ] Quality gate — 6 checks
- [ ] Calculate quantitative score
- [ ] Update Canvas to "✅ Completed"
- [ ] Save memory

---

## 8. Quick Self-Check Commands

```bash
# 1. Check tab count
playwright-cli eval "() => document.querySelectorAll('.el-tabs__item').length"

# 2. Check field count (after clicking export)
playwright-cli eval "() => document.querySelectorAll('.el-checkbox__label').length"

# 3. Check button count
playwright-cli eval "() => document.querySelectorAll('button').length"

# 4. Check whether checkpoint exists
ls ~/.claude/skills/sorftime-explorer/progress/amazon/{module}/checkpoint.json
```

---

## 9. Root Cause Analysis (2026-04-02 Learnings)

### Root Causes of 70% Detail Loss During Exploration

| Root Cause | Solution |
|-------------|----------|
| playwright only captured static snapshot | Use page.evaluate() + waitForTimeout() |
| Dropdown menus not expanded | Add step to enumerate all dropdown options |
| Sub-pages not clicked into | Add tab-switch exploration step |
| Field list incomplete | Click "Export" or field selection modal to get complete list |

### Lessons Learned

1. **Exists != Usable** — seeing a button doesn't count; must click and verify its response.
2. **Enumerated != Scanned** — must expand every dropdown menu.
3. **Explored != Recorded** — must enter sub-pages to retrieve detail.
4. **Checkpoints are critical** — must save after every tab switch.
