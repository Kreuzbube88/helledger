# 📥 Import

HELLEDGER supports importing transactions from **CSV**, **OFX**, and **QFX** files.

---

## Starting an Import

1. Select **Import** in the navigation menu
2. Upload a file via drag & drop or file picker
3. Map the columns
4. Start the import

---

## CSV Import

CSV files are imported with a **column mapping** step. You define which column contains the date, amount, and description.

**Configurable:**
- Date format (e.g. `DD.MM.YYYY`, `YYYY-MM-DD`)
- Decimal separator (comma or dot)
- Default category (optional)
- Target account

**Example format:**
```
Date,Description,Amount
2026-04-01,Salary,2500.00
2026-04-03,Rent,-900.00
```

---

## OFX / QFX Import

OFX and QFX files (standard bank exports) are automatically detected and parsed. No manual column mapping required.

---

## Duplicate Detection

HELLEDGER detects already-imported transactions based on date, amount, and description, and skips duplicates automatically. The result page shows:

- ✅ Imported
- ⚠️ Duplicates found
- ❌ Errors
