# Florin Help

Welcome to Florin — your personal finance, expense tracking, and savings tool designed for everyone.

---

## Getting Started

### What is Florin?

Florin helps you manage your money when your income changes every month. It lets you:

- Calculate your net income after taxes and deductions
- Split your income across personal budget categories (like "Daily Life", "Savings", "Pleasure")
- Track your expenses and see how much you have left in each category
- Plan and track savings goals with deadlines
- Monitor your cash flow buffer so you always know where you stand

All your data is stored locally on your computer — nothing is sent to the internet.

### First Steps

1. Open the app. You'll land on the **Dashboard**.
2. Go to the **Income** tab and enter your gross invoice amount and deductions (VAT, tax, ZUS).
3. Check the **Dashboard** to see your net income split across categories.
4. Start logging expenses in the **Expenses** tab.
5. Set up savings goals in the **Savings** tab.

---

## Dashboard

The Dashboard gives you a quick overview of your current month:

- **Net Income** — your take-home pay after all deductions
- **Category Split** — how your net income is divided across your budget categories, shown as amounts and percentages
- **Spending Summary** — how much you've spent vs. how much was allocated per category

This is your "at a glance" view. For details, visit the individual tabs.

---

## Income

The Income tab is where you record all money coming in and going out as deductions.

### How it works

Each line item is either an **addition** (money in) or a **deduction** (money out before you receive it):

- **Additions:** Gross invoice, freelance bonuses, side income
- **Deductions:** VAT, income tax, ZUS (social security)

Your **net income** is calculated automatically: all additions minus all deductions.

### Adding an entry

Click the **+ Add** button, choose whether it's an addition or deduction, enter the name and amount, then save.

### Editing or deleting

Click the edit icon (✎) next to any entry to change it, or the delete icon (×) to remove it.

### Targeted income

Some income can be assigned directly to a specific budget category (e.g., a bonus that goes straight to "Pleasure"). When adding, select the target category — that amount will be added only to that category instead of being split proportionally.

---

## Expenses

The Expenses tab lets you log and track everything you spend.

### Adding an expense

Click **+ Add Expense** and fill in:

- **Date** — when the expense happened (DD/MM/YYYY format)
- **Amount** — how much you spent (use . or , for decimals)
- **Expense Category** — what type of expense it is (Groceries, Transport, Healthcare, etc.)
- **Funding Source** — which budget category pays for this (Daily Life, Shared, etc.) or a savings goal
- **Description** — optional note about the expense
- **Tags** — optional labels for filtering later

### Funding from Savings

If an expense is paid from a savings goal (e.g., you saved for a dentist visit and now you're paying), select the savings category as the funding source. This will deduct from that savings goal's balance.

### Month filter

The expense list shows the **current month** by default. Use the month navigation arrows at the top to browse other months.

### Managing expense categories

Click the category manager button to add, rename, or delete expense categories. Deleting a category won't delete the expenses — they'll just become uncategorized.

---

## Savings

The Savings tab is your savings planner. It helps you set goals, plan monthly contributions, and track actual progress throughout the year.

### Groups and Categories

- A **category** is a single savings goal (e.g., "Dentist", "Birthday gifts", "New laptop")
- A **group** organizes related categories together (e.g., "Health & Beauty", "Gifts & Holidays")

Groups are collapsible — click the group name to expand or collapse its categories.

### Adding a new group

1. Click **✎ Edit** to enter Edit mode
2. Click **+ Group**
3. Enter the group name and save

### Adding a new category

1. Click **✎ Edit** to enter Edit mode
2. Click **+ Category**
3. Fill in:
   - **Name** — what you're saving for
   - **Target Amount** — how much you need in total
   - **Deadline Month** — when you need the money by
   - **Group** — which group it belongs to (optional)
   - **Next Year Target** — if this is a recurring goal, enter next year's target amount

### The Actual Savings Table (top section)

This shows what you've **actually saved** each month. The columns on the right summarize your progress:

| Column | Meaning |
|--------|---------|
| **Saved** | Total amount you've put aside so far (all months combined) |
| **Missing** | How much more you need to reach your target (0 if fully funded) |
| **%** | Percentage of your target reached |
| **Spent** | How much you've already spent from this savings goal |
| **Balance** | Saved minus Spent — what's actually left available |

### Recording actual payments

1. Click **✎ Edit** to enter Edit mode
2. Type the amount you saved this month into the cell for the correct month
3. Click **✓ Done** to save

### The Planning Grid (bottom section)

This is your **plan** — how much you intend to save each month for each category. When you create a category, Florin automatically distributes the target evenly across months up to the deadline.

- **Assumed Available** row: How much total savings budget you expect to have each month
- **Total Allocated** row: Sum of all planned amounts for that month
- **Remaining** row: Assumed minus Allocated (green = under budget, red = over budget)

### Strikethrough numbers (Surplus Cascade)

Sometimes you'll see numbers crossed out with a new value below them (e.g., ~~18~~ → 0). This means:

1. You fully funded a goal AND spent the money (e.g., bought the gift)
2. You had leftover surplus (saved more than you spent)
3. Florin automatically reduces your future planned amounts for that category's next-year savings, since the surplus carries forward

This is automatic — you don't need to do anything. It keeps your plan accurate.

### Deadline months

The deadline month is highlighted with a purple/accent background in both tables. This is the month by which you need to have the full target amount saved.

### Collapsing and expanding groups

Click any group name (with the ▶ or ▼ arrow) to collapse or expand it. Collapsed groups hide their category rows to reduce clutter. Your collapse preferences are remembered during the session.

### Edit mode

- Click **✎ Edit** to enter edit mode — cells become editable, and add/delete buttons appear
- Make your changes (type amounts, add categories, etc.)
- Click **✓ Done** to save everything and return to view mode

---

## Cash Flow

The Cash Flow tab helps you manage your buffer accounts — minimum balances you want to maintain in specific accounts.

### How it works

1. In **Settings**, define your cash flow targets (account names and minimum balances)
2. In the Cash Flow tab, enter your current actual balance for each account
3. Florin calculates how much you need to **top up** each account to reach the minimum

This tells you exactly how to distribute your paycheck across accounts after it arrives.

---

## History

The History tab lets you browse data from previous months.

### Browsing past months

Use the month selector to switch between months. Each month shows its own income, expenses, and category splits as they were recorded at the time.

---

## Settings

The Settings tab lets you configure:

- **Default Income Items** — the template entries that appear when a new month starts (e.g., "Gross Invoice", "VAT", "Income Tax", "ZUS"). Add or remove items here.
- **Cash Flow Targets** — your buffer accounts and their minimum balances. Add, edit, or remove targets here.

Changes in Settings apply to future months. They don't retroactively change past data.

---

## Frequently Asked Questions

### Can I lose my data?

Your data is as safe as any file on your computer. It could be lost if:
- You delete the database file
- Your hard drive fails
- You reinstall your system without backing up

**Tip:** Periodically copy your `florin.db` database file somewhere safe (USB drive, cloud backup folder) for peace of mind. See the **Where Is My Data Stored?** section below for the file location.

### What should I do if something doesn't work?

1. Close and reopen the app — this fixes most display issues.
2. Check that your database file exists.
3. As a last resort, you can delete `config.json` to reset settings (your monthly data and savings will be preserved).

### Can I use the app in Polish?

Yes! Florin's interface is fully bilingual (English and Polish).

### Can I use commas for decimal numbers?

Yes! You can type either `1234.56` or `1234,56` — Florin converts commas to dots automatically.

### What currency does Florin use?

Florin displays amounts in PLN (Polish Złoty) but doesn't enforce any currency. The numbers work the same regardless of what currency you use mentally.


---

## Running Florin

### On Windows

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/)
2. Open a terminal (Command Prompt or PowerShell)
3. Navigate to the Florin folder: `cd path\to\florin`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the app: `python main.py`

**Tip:** You can also double-click `main.py` if Python is associated with `.py` files, or use the included `create_shortcut.ps1` script to make a desktop shortcut.

### On macOS

1. Install Python 3.10 or newer (via [python.org](https://www.python.org/downloads/) or `brew install python`).
2. Double-click the `run_on_mac.command` file in the Florin folder. This will automatically set up the virtual environment, install dependencies, and launch the app.

*(If macOS complains about the file being from an unidentified developer, right-click the file, select **Open**, and confirm).*

---

## Where Is My Data Stored?

Florin stores all your data in a local database file on your computer. Nothing is sent to the internet.

| Operating System | Database Location |
|-----------------|-------------------|
| Windows | `C:\Users\<YourName>\AppData\Local\Florin\florin.db` |
| macOS | `~/Library/Application Support/Florin/florin.db` |

### Can multiple people use Florin?

Yes! Each person uses Florin independently on their own computer. Your data is completely separate — there's no shared account or cloud sync.

If your partner also wants to use Florin, they simply install it on their own machine and get their own private database automatically.

### What about my old data?

If you previously used Florin with JSON files (in the `data/` folder), the app automatically migrates your data to the new database on first launch. Your old files are kept as backup — you can delete them once you've confirmed everything works.

### Backing up your data

To back up your data, copy the database file to a safe location:

- **Windows:** Copy `C:\Users\<YourName>\AppData\Local\Florin\florin.db`
- **macOS:** Copy `~/Library/Application Support/Florin/florin.db`

Store the copy on a USB drive, cloud backup folder, or anywhere safe.
