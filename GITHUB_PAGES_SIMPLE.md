# 🚀 Deploy Dashboard to GitHub Pages

## Your static dashboard is ready!

The file `docs/index.html` contains your Metabase dashboard as a static webpage.

## 📤 Deploy to GitHub Pages (3 Steps)

### Step 1: Push to GitHub

```bash
git add docs/index.html
git add export_dashboard_simple.py
git commit -m "Add static dashboard"
git push
```

### Step 2: Enable GitHub Pages

1. Go to your GitHub repository
2. Click **Settings** → **Pages**
3. Under **Source**, select:
   - Branch: **master** (or **main**)
   - Folder: **/docs**
4. Click **Save**

### Step 3: View Your Dashboard

After 1-2 minutes, visit:

```
https://YOUR_USERNAME.github.io/github-activity-data-pipeline/
```

Replace `YOUR_USERNAME` with your GitHub username.

## 🔄 Update Dashboard

Whenever you want to update the dashboard:

```bash
# Export fresh data from Metabase
python3 export_dashboard_simple.py

# Commit and push
git add docs/index.html
git commit -m "Update dashboard"
git push
```

GitHub Pages will automatically update in 1-2 minutes!

## ✅ That's it!

Your dashboard is now a static website hosted for free on GitHub Pages.

---

**Note:** The dashboard currently shows "No data available" because dashboard #4 has no cards/visualizations. Add some visualizations in Metabase at http://localhost:3000/dashboard/4 and re-export.

