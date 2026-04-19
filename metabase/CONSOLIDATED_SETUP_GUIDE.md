# Quick Setup Guide: 2 Consolidated Dashboards

## 📊 Dashboard Overview

Instead of 6 separate dashboards, create **2 comprehensive dashboards**:

```
┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD 1: Executive Overview (13 widgets)                   │
│  👥 Audience: Leadership, Stakeholders, Product Managers        │
│  🎯 Focus: High-level metrics, trends, top performers           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD 2: Technical Deep Dive (18 widgets)                  │
│  👥 Audience: Developers, Data Engineers, Analysts              │
│  🎯 Focus: Data quality, patterns, detailed analytics           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Setup (15 minutes)

### Step 1: Open Metabase
```bash
# Make sure Metabase is running
./scripts/start_metabase.sh

# Open in browser
open http://localhost:3000
```

### Step 2: Create Dashboard 1
1. Click **"New"** → **"Dashboard"**
2. Name: `GitHub Archive - Executive Overview`
3. Description: `High-level GitHub activity insights for stakeholders`
4. Click **"Create"**

### Step 3: Add Widgets to Dashboard 1
For each of the 13 queries in `consolidated_queries.sql`:

1. Click **"Add a question"** → **"Custom question"**
2. Select **"Native query"** (SQL)
3. Copy-paste query from file
4. Choose visualization type (see guide below)
5. Name the question appropriately
6. Click **"Save"** → Add to dashboard

### Step 4: Create Dashboard 2
Repeat steps 2-3 for Technical Deep Dive dashboard with 18 queries.

### Step 5: Add Filters
1. Click **"Edit Dashboard"** → **"Add Filter"**
2. Add these filters:
   - ✅ Date Range (default: Last 30 days)
   - ✅ Event Type (multi-select)
   - ✅ Is Bot (True/False/All)
3. Connect filters to appropriate widgets
4. Click **"Save"**

---

## 📈 Visualization Guide

### Dashboard 1: Executive Overview

| # | Widget Name | Viz Type | Size |
|---|-------------|----------|------|
| 1 | Total Events (Last 30 Days) | Number | 1x1 |
| 2 | Active Developers (Last 7 Days) | Number | 1x1 |
| 3 | Active Repositories (Last 7 Days) | Number | 1x1 |
| 4 | Total Organizations | Number | 1x1 |
| 5 | Daily Event Trend | Line Chart | 2x1 |
| 6 | Bot vs Human Activity | Stacked Area | 2x1 |
| 7 | Event Type Distribution | Pie Chart | 1x1 |
| 8 | Public vs Private Events | Stacked Area | 1x1 |
| 9 | Top 20 Repositories | Table | 2x1 |
| 10 | Top 25 Developers | Table | 2x1 |
| 11 | Top Organizations | Table | 1x1 |
| 12 | Repository Popularity | Pie Chart | 1x1 |
| 13 | Trending Repositories | Table | 2x1 |

### Dashboard 2: Technical Deep Dive

| # | Widget Name | Viz Type | Size |
|---|-------------|----------|------|
| 1 | Data Freshness Status | Table | 2x1 |
| 2 | Daily Record Counts | Bar Chart | 1x1 |
| 3 | Null Value Analysis | Table | 1x1 |
| 4 | Hourly Activity Pattern | Heatmap | 2x1 |
| 5 | Activity by Hour | Line Chart | 1x1 |
| 6 | Activity by Day of Week | Bar Chart | 1x1 |
| 7 | Event Type Trend | Multi-Line | 2x1 |
| 8 | Event Engagement Metrics | Table | 2x1 |
| 9 | Event Type Coverage | Table | 1x1 |
| 10 | Developer Activity Levels | Pie Chart | 1x1 |
| 11 | New vs Returning Devs | Stacked Area | 2x1 |
| 12 | Daily Active Developers | Multi-Line | 2x1 |
| 13 | Repository Growth | Line Chart | 2x1 |
| 14 | Activity Type Breakdown | Stacked Area | 2x1 |
| 15 | Top Repository Owners | Table | 2x1 |
| 16 | Org vs Individual Activity | Pie Chart | 1x1 |
| 17 | Organization Activity Trend | Line Chart | 1x1 |
| 18 | Orgs by Repo Count | Bar Chart | 1x1 |

---

## 🎨 Layout Suggestions

### Dashboard 1 Layout
```
┌────────────┬────────────┬────────────┬────────────┐
│  Number 1  │  Number 2  │  Number 3  │  Number 4  │
│ Total      │ Active     │ Active     │ Total      │
│ Events     │ Developers │ Repos      │ Orgs       │
├────────────┴────────────┼────────────┴────────────┤
│ Line Chart: Daily Trend │ Area: Bot vs Human      │
├─────────────────────────┼─────────────────────────┤
│ Pie: Event Types        │ Area: Public/Private    │
├─────────────────────────┴─────────────────────────┤
│ Table: Top 20 Repositories                        │
├───────────────────────────────────────────────────┤
│ Table: Top 25 Developers                          │
├─────────────────────────┬─────────────────────────┤
│ Table: Top Orgs         │ Pie: Repo Popularity    │
├─────────────────────────┴─────────────────────────┤
│ Table: Trending Repositories                      │
└───────────────────────────────────────────────────┘
```

### Dashboard 2 Layout
```
┌─────────────────────────┬─────────────────────────┐
│ Table: Data Freshness   │ Bar: Daily Records      │
├─────────────────────────┼─────────────────────────┤
│ Table: Null Analysis    │ Heatmap: Hourly Pattern │
├─────────────────────────┼─────────────────────────┤
│ Line: Activity by Hour  │ Bar: Activity by Day    │
├─────────────────────────┴─────────────────────────┤
│ Multi-Line: Event Type Trend                      │
├───────────────────────────────────────────────────┤
│ Table: Event Engagement Metrics                   │
├─────────────────────────┬─────────────────────────┤
│ Table: Event Coverage   │ Pie: Dev Activity Lvl   │
├─────────────────────────┴─────────────────────────┤
│ Area: New vs Returning Developers                 │
├───────────────────────────────────────────────────┤
│ Multi-Line: Daily Active Developers               │
├───────────────────────────────────────────────────┤
│ Line: Repository Growth                           │
├───────────────────────────────────────────────────┤
│ Area: Activity Type Breakdown                     │
└───────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration Tips

### Colors
- **Bot Activity**: 🔴 Red (#E74C3C)
- **Human Activity**: 🔵 Blue (#3498DB)
- **Public Repos**: 🟢 Green (#2ECC71)
- **Private Repos**: 🟡 Yellow (#F39C12)

### Number Formatting
- Events: `1,234,567` (comma separators)
- Percentages: `45.67%` (2 decimals)
- Growth: `+125.5%` or `-10.2%`

### Date Formatting
- Dashboard titles: `April 19, 2026`
- Axes: `Apr 19` or `2026-04-19`

### Auto-Refresh
- Executive Dashboard: Every 30 minutes
- Technical Dashboard: Every 15 minutes (for data quality monitoring)

---

## 📋 Checklist

Dashboard 1 (Executive):
- [ ] Create dashboard
- [ ] Add all 13 widgets
- [ ] Set up visualizations
- [ ] Add filters (Date, Event Type)
- [ ] Arrange layout logically
- [ ] Set auto-refresh (30 min)
- [ ] Test on mobile
- [ ] Share with stakeholders

Dashboard 2 (Technical):
- [ ] Create dashboard
- [ ] Add all 18 widgets
- [ ] Set up visualizations
- [ ] Add filters (Date, Event Type, Bot)
- [ ] Arrange layout logically
- [ ] Set auto-refresh (15 min)
- [ ] Test performance
- [ ] Share with team

---

## 🔍 Testing Your Dashboards

After setup, verify:
1. ✅ All widgets load without errors
2. ✅ Filters apply correctly
3. ✅ Visualizations render properly
4. ✅ Data looks reasonable (no NULLs where unexpected)
5. ✅ Auto-refresh works
6. ✅ Mobile view is usable
7. ✅ Export to PDF/PNG works

---

## 🎯 Benefits vs 6 Dashboards

| Aspect | 6 Dashboards | 2 Dashboards |
|--------|--------------|--------------|
| Navigation | 😞 Lots of clicking | 😊 Easy scrolling |
| Context | 😞 Fragmented view | 😊 Complete picture |
| Maintenance | 😞 Update 6 places | 😊 Update 2 places |
| Loading | 😞 Slower | 😊 Faster |
| Sharing | 😞 Multiple links | 😊 Single link |
| Storytelling | 😞 Disjointed | 😊 Cohesive |

---

## 📚 Files Created

1. `CONSOLIDATED_DASHBOARDS.md` - Full guide with all details
2. `consolidated_queries.sql` - All SQL queries ready to copy-paste
3. `CONSOLIDATED_SETUP_GUIDE.md` - This file (quick reference)

---

## 🆘 Need Help?

**Common Issues:**
- Query fails: Check if dbt models are built (`dbt run`)
- No data: Verify data ingestion is running
- Slow performance: Add indexes or use aggregation tables
- Visual issues: Try different chart types

**Next Steps:**
1. Set up email subscriptions for daily reports
2. Configure Slack/Teams alerts for anomalies
3. Create custom SQL snippets for common filters
4. Build pulse notifications for key metrics

---

Happy dashboarding! 🚀

