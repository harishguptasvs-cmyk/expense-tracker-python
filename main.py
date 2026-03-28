import customtkinter as ctk
from tkcalendar import Calendar
import sqlite3
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Smart Expense Tracker")
app.geometry("1000x800")

# ---------- DASHBOARD ----------
dashboard_frame = ctk.CTkFrame(app)
dashboard_frame.pack(pady=10, fill="x", padx=10)

income_label = ctk.CTkLabel(dashboard_frame, text="Income: 0", font=("Arial", 16))
income_label.pack(side="left", padx=20)

expense_label = ctk.CTkLabel(dashboard_frame, text="Expense: 0", font=("Arial", 16))
expense_label.pack(side="left", padx=20)

balance_label = ctk.CTkLabel(dashboard_frame, text="Balance: 0", font=("Arial", 16, "bold"))
balance_label.pack(side="left", padx=20)

# ---------- TITLE ----------
title_label = ctk.CTkLabel(app, text="Smart Expense Tracker", font=("Arial", 28, "bold"))
title_label.pack(pady=10)

# ---------- INPUTS ----------
amount_entry = ctk.CTkEntry(app, placeholder_text="Amount")
amount_entry.pack(pady=5)

category_option = ctk.CTkOptionMenu(app, values=["Food", "Travel", "Bills", "Shopping", "Salary", "Other"])
category_option.pack(pady=5)

type_option = ctk.CTkOptionMenu(app, values=["Income", "Expense"])
type_option.pack(pady=5)

date_entry = ctk.CTkEntry(app, placeholder_text="Click to select date")
date_entry.pack(pady=5)

desc_entry = ctk.CTkEntry(app, placeholder_text="Description")
desc_entry.pack(pady=5)

selected_id = None


# ---------- CALENDAR ----------
def open_calendar(event=None):
    cal_window = ctk.CTkToplevel(app)
    cal_window.title("Select Date")

    cal = Calendar(cal_window, selectmode="day")
    cal.pack(pady=20)

    def select_date():
        date_entry.delete(0, "end")
        date_entry.insert(0, cal.get_date())
        cal_window.destroy()

    ctk.CTkButton(cal_window, text="Select", command=select_date).pack(pady=10)


date_entry.bind("<Button-1>", open_calendar)


# ---------- DATABASE FUNCTIONS ----------
def update_dashboard():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    expense = cursor.fetchone()[0] or 0

    conn.close()

    balance = income - expense

    income_label.configure(text=f"Income: {income}")
    expense_label.configure(text=f"Expense: {expense}")
    balance_label.configure(text=f"Balance: {balance}")


def load_transactions():
    for widget in history_frame.winfo_children():
        widget.destroy()

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, amount, category, type, date, description FROM transactions")
    rows = cursor.fetchall()

    conn.close()

    for row in rows:
        text = f"{row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}"
        btn = ctk.CTkButton(history_frame, text=text, anchor="w",
                            command=lambda r=row: select_record(r[0]))
        btn.pack(fill="x", pady=2)

    update_dashboard()


def select_record(record_id):
    global selected_id
    selected_id = record_id
    messagebox.showinfo("Selected", f"Transaction ID {record_id} selected")


# ---------- ADD ----------
def add_transaction():
    amount = amount_entry.get()
    category = category_option.get()
    t_type = type_option.get()
    date = date_entry.get()
    desc = desc_entry.get()

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions (amount, category, type, date, description)
        VALUES (?, ?, ?, ?, ?)
    """, (amount, category, t_type, date, desc))

    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Transaction Added!")

    amount_entry.delete(0, "end")
    date_entry.delete(0, "end")
    desc_entry.delete(0, "end")

    load_transactions()


# ---------- DELETE ----------
def delete_transaction():
    global selected_id

    if selected_id is None:
        messagebox.showwarning("Warning", "Select a transaction first!")
        return

    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id=?", (selected_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Deleted", "Transaction Deleted")

    selected_id = None
    load_transactions()


# ---------- HISTORY ----------
history_label = ctk.CTkLabel(app, text="Transaction History", font=("Arial", 20, "bold"))
history_label.pack(pady=10)

history_frame = ctk.CTkScrollableFrame(app, width=900, height=250)
history_frame.pack(pady=10)


# ---------- CHARTS ----------
def show_expense_chart():
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT amount, category, type FROM transactions", conn)
    conn.close()

    if df.empty:
        messagebox.showwarning("No Data", "No transactions available!")
        return

    expense_df = df[df["type"] == "Expense"]

    category_sum = expense_df.groupby("category")["amount"].sum()

    category_sum.plot(kind="pie", autopct="%1.1f%%")
    plt.title("Expenses by Category")
    plt.show()


def income_vs_expense_chart():
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT amount, type FROM transactions", conn)
    conn.close()

    summary = df.groupby("type")["amount"].sum()

    summary.plot(kind="bar")
    plt.title("Income vs Expense")
    plt.show()


def monthly_report():
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT amount, date FROM transactions", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()

    monthly.plot(kind="line", marker="o")
    plt.title("Monthly Report")
    plt.show()


# ---------- EXPORT ----------
def export_excel():
    conn = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()

    df.to_excel("expenses.xlsx", index=False)
    messagebox.showinfo("Exported", "Saved as expenses.xlsx")


def export_pdf():
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    rows = cursor.fetchall()
    conn.close()

    file = "expenses.pdf"
    c = canvas.Canvas(file, pagesize=letter)

    y = 750
    for row in rows:
        c.drawString(50, y, str(row))
        y -= 20

    c.save()

    messagebox.showinfo("Exported", "Saved as expenses.pdf")


# ---------- BUTTONS ----------
btn_frame = ctk.CTkFrame(app)
btn_frame.pack(pady=10)

ctk.CTkButton(btn_frame, text="Add Transaction", command=add_transaction).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Delete Selected", command=delete_transaction).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Expense Chart", command=show_expense_chart).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Income vs Expense", command=income_vs_expense_chart).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Monthly Report", command=monthly_report).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Export Excel", command=export_excel).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Export PDF", command=export_pdf).pack(side="left", padx=5)

# ---------- INIT ----------
load_transactions()

app.mainloop()
