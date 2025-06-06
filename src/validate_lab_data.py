import json
import pandas as pd
import logging
import re
from uuid import uuid4
from fuzzywuzzy import fuzz
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LabDataValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lab Data Validator")
        self.root.geometry("1000x700")

        # Variables for file paths
        self.json_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.json_data = None
        self.csv_df = None
        self.status_updates = {}
        self.unit_updates = {}
        self.date_updates = {}
        self.current_combobox = None
        self.one_to_rule_em_all_date = tk.StringVar()  # Variable for "One to Rule 'Em All" date

        # GUI Layout
        self.create_gui()

    def create_gui(self):
        file_frame = tk.Frame(self.root, padx=10, pady=10)
        file_frame.pack(fill=tk.X)

        tk.Label(file_frame, text="JSON File:").grid(row=0, column=0, sticky="w")
        tk.Entry(file_frame, textvariable=self.json_path, width=50).grid(row=0, column=1, padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_json).grid(row=0, column=2)

        tk.Label(file_frame, text="CSV File:").grid(row=1, column=0, sticky="w")
        tk.Entry(file_frame, textvariable=self.csv_path, width=50).grid(row=1, column=1, padx=5)
        tk.Button(file_frame, text="Browse", command=self.browse_csv).grid(row=1, column=2)

        tk.Button(self.root, text="Run Validation", command=self.run_validation).pack(pady=10)

        tk.Label(self.root, text="Validation Results").pack()
        self.results_text = scrolledtext.ScrolledText(self.root, height=10, width=80, wrap=tk.WORD)
        self.results_text.pack(padx=10, pady=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Status Updates Tab
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="Status Updates")

        tk.Label(self.status_frame, text="Edit Status for 'unknown' Tests").pack()
        status_inner_frame = tk.Frame(self.status_frame)
        status_inner_frame.pack(fill=tk.BOTH, expand=True)

        status_columns = ("TestName", "Current Status", "New Status", "Calculated Range", "Result")
        self.status_tree = ttk.Treeview(status_inner_frame, columns=status_columns, show="headings")
        self.status_tree.heading("TestName", text="Test Name")
        self.status_tree.heading("Current Status", text="Current Status")
        self.status_tree.heading("New Status", text="New Status")
        self.status_tree.heading("Calculated Range", text="Calculated Range")
        self.status_tree.heading("Result", text="Result")
        self.status_tree.column("TestName", width=200)
        self.status_tree.column("Current Status", width=100)
        self.status_tree.column("New Status", width=100)
        self.status_tree.column("Calculated Range", width=150)
        self.status_tree.column("Result", width=100)
        self.status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        status_scrollbar = ttk.Scrollbar(status_inner_frame, orient=tk.VERTICAL, command=self.status_tree.yview)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_tree.configure(yscrollcommand=status_scrollbar.set)

        self.status_tree.bind("<Button-1>", self.show_status_combobox)

        # Unit Conversions Tab
        self.unit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.unit_frame, text="Unit Conversions")

        tk.Label(self.unit_frame, text="Review and Update Units Requiring Conversion").pack()
        unit_inner_frame = tk.Frame(self.unit_frame)
        unit_inner_frame.pack(fill=tk.BOTH, expand=True)

        unit_columns = ("TestName", "Current Unit", "New Unit")
        self.unit_tree = ttk.Treeview(unit_inner_frame, columns=unit_columns, show="headings")
        self.unit_tree.heading("TestName", text="Test Name")
        self.unit_tree.heading("Current Unit", text="Current Unit")
        self.unit_tree.heading("New Unit", text="New Unit")
        self.unit_tree.column("TestName", width=200)
        self.unit_tree.column("Current Unit", width=300)
        self.unit_tree.column("New Unit", width=200)
        self.unit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        unit_scrollbar = ttk.Scrollbar(unit_inner_frame, orient=tk.VERTICAL, command=self.unit_tree.yview)
        unit_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.unit_tree.configure(yscrollcommand=unit_scrollbar.set)

        self.unit_tree.bind("<Button-1>", self.show_unit_entry)

        # Date Updates Tab
        self.date_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.date_frame, text="Date Updates")

        tk.Label(self.date_frame, text="Review and Update Test Dates").pack()

        # "One to Rule 'Em All" Section
        one_to_rule_frame = tk.Frame(self.date_frame)
        one_to_rule_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(one_to_rule_frame, text="One to Rule 'Em All:").pack(side=tk.LEFT)
        tk.Entry(one_to_rule_frame, textvariable=self.one_to_rule_em_all_date, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(one_to_rule_frame, text="Apply to All", command=self.apply_date_to_all).pack(side=tk.LEFT)

        date_inner_frame = tk.Frame(self.date_frame)
        date_inner_frame.pack(fill=tk.BOTH, expand=True)

        date_columns = ("TestName", "Current Date", "New Date")
        self.date_tree = ttk.Treeview(date_inner_frame, columns=date_columns, show="headings")
        self.date_tree.heading("TestName", text="Test Name")
        self.date_tree.heading("Current Date", text="Current Date")
        self.date_tree.heading("New Date", text="New Date")
        self.date_tree.column("TestName", width=200)
        self.date_tree.column("Current Date", width=150)
        self.date_tree.column("New Date", width=150)
        self.date_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        date_scrollbar = ttk.Scrollbar(date_inner_frame, orient=tk.VERTICAL, command=self.date_tree.yview)
        date_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.date_tree.configure(yscrollcommand=date_scrollbar.set)

        self.date_tree.bind("<Button-1>", self.show_date_entry)

        tk.Button(self.root, text="Save Updated JSON", command=self.save_updated_json).pack(pady=10)

    def browse_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.json_path.set(file_path)

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_path.set(file_path)

    def load_json_data(self, json_file_path):
        """Load JSON data from a file and return the enhancedSerScanObject."""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.json_data = data
            logging.info("Successfully loaded JSON data")
            return data.get('enhancedSerScanObject', [])
        except FileNotFoundError as e:
            logging.error(f"JSON file not found: {json_file_path}. Error: {e}")
            self.results_text.insert(tk.END, f"JSON file not found: {json_file_path}. Error: {e}\n")
            return []
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format in file: {json_file_path}. Error: {e}")
            self.results_text.insert(tk.END, f"Invalid JSON format in file: {json_file_path}. Error: {e}\n")
            return []
        except Exception as e:
            logging.error(f"Unexpected error loading JSON file {json_file_path}: {e}")
            self.results_text.insert(tk.END, f"Unexpected error loading JSON: {e}\n")
            return []

    def load_csv_data(self, csv_file_path):
        """Load CSV data into a pandas DataFrame."""
        try:
            df = pd.read_csv(csv_file_path, sep=',', encoding='utf-8')
            logging.info(f"CSV columns: {df.columns.tolist()}")
            logging.info(f"CSV head:\n{df.head().to_string()}")

            if 'Search Names' not in df.columns or 'Test Name' not in df.columns or 'Calculated range' not in df.columns or 'Unit' not in df.columns:
                logging.error(f"Required columns missing in CSV. Available columns: {df.columns.tolist()}")
                self.results_text.insert(tk.END, f"Error: Required columns missing in CSV: {df.columns.tolist()}\n")

            self.csv_df = df
            return df
        except FileNotFoundError as e:
            logging.error(f"CSV file not found: {csv_file_path}. Error: {e}")
            self.results_text.insert(tk.END, f"CSV file not found: {csv_file_path}. Error: {e}\n")
            return pd.DataFrame()
        except pd.errors.EmptyDataError as e:
            logging.error(f"CSV file is empty: {csv_file_path}. Error: {e}")
            self.results_text.insert(tk.END, f"CSV file is empty: {csv_file_path}. Error: {e}\n")
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Unexpected error loading CSV file {csv_file_path}: {e}")
            self.results_text.insert(tk.END, f"Unexpected error loading CSV: {e}\n")
            return pd.DataFrame()

    def validate_status_values(self, json_data):
        """Check that no status values are null or 'unknown'."""
        issues = []
        for item in json_data:
            status = item.get('status')
            test_name = item.get('TestName')
            result = item.get('result', 'N/A')

            if status is None:
                issues.append(f"TestName: {test_name} - Status is null")
            elif status == 'unknown':
                issues.append(f"TestName: {test_name} - Status is 'unknown'")
                calculated_range = self.get_calculated_range(test_name)
                self.status_tree.insert("", tk.END,
                                        values=(test_name, 'unknown', 'Click to select...', calculated_range, result),
                                        tags=(test_name,))
        return issues

    def get_calculated_range(self, test_name):
        """Retrieve the calculated range for a test from the CSV."""
        if self.csv_df is None:
            return "N/A"

        test_name_match = self.csv_df[self.csv_df['Test Name'].str.lower() == test_name.lower()]
        if not test_name_match.empty:
            return test_name_match['Calculated range'].iloc[0]

        escaped_test_name = re.escape(test_name)
        search_names_match = self.csv_df[
            self.csv_df['Search Names'].str.contains(escaped_test_name, case=False, na=False)]
        if not search_names_match.empty:
            return search_names_match['Calculated range'].iloc[0]

        return "Not found"

    def populate_unit_conversions(self, json_data):
        """Populate the Unit Conversions tab with tests requiring unit conversion from JSON."""
        if not json_data:
            return

        for item in json_data:
            unit = item.get('unit', '')
            test_name = item.get('TestName')
            if "CONVERSION REQUIRED!!!" in unit:
                self.unit_tree.insert("", tk.END,
                                      values=(test_name, unit, 'Click to update...'),
                                      tags=(test_name,))

    def populate_date_updates(self, json_data):
        """Populate the Date Updates tab with all tests and their dates from JSON."""
        if not json_data:
            return

        for item in json_data:
            date = item.get('date', 'N/A')
            test_name = item.get('TestName')
            self.date_tree.insert("", tk.END,
                                  values=(test_name, date, 'Click to update...'),
                                  tags=(test_name,))

    def apply_date_to_all(self):
        """Apply the date from 'One to Rule 'Em All' to all test entries."""
        new_date = self.one_to_rule_em_all_date.get().strip()
        if not new_date:
            self.results_text.insert(tk.END, "\nPlease enter a date in the 'One to Rule 'Em All' field.\n")
            return

        # Update all entries in the Treeview and date_updates dictionary
        for item in self.date_tree.get_children():
            test_name = self.date_tree.item(item)['values'][0]
            current_date = self.date_tree.item(item)['values'][1]
            self.date_tree.item(item, values=(test_name, current_date, new_date))
            self.date_updates[test_name] = new_date

        logging.info(f"Applied date {new_date} to all tests")
        logging.info(f"Current date updates: {self.date_updates}")

    def find_closest_match(self, test_name, csv_df):
        """Find the closest matching test name in Test Name or Search Names using fuzzy matching."""
        all_names = pd.concat([
            csv_df['Test Name'].dropna(),
            csv_df['Search Names'].str.split(',', expand=True).stack().str.strip().reset_index(drop=True)
        ]).unique()

        best_match = None
        best_score = 0
        for name in all_names:
            score = fuzz.ratio(test_name.lower(), name.lower())
            if score > best_score and score > 50:
                best_score = score
                best_match = name

        return best_match, best_score

    def validate_test_name_and_loinc(self, json_data, csv_df):
        """Validate TestName against Test Name and Search Names, and loincCode against Loinc."""
        unmatched_tests = []
        loinc_issues = []
        csv_update_suggestions = []

        for item in json_data:
            test_name = item.get('TestName')
            loinc_code = item.get('loincCode')

            logging.info(f"Checking TestName: {test_name}")

            if 'Test Name' not in csv_df.columns or 'Search Names' not in csv_df.columns:
                unmatched_tests.append(f"TestName: {test_name} - Required columns missing in CSV")
                continue

            test_name_match = csv_df[csv_df['Test Name'].str.lower() == test_name.lower()]

            if not test_name_match.empty:
                expected_loinc = test_name_match['Loinc'].iloc[0]
                if loinc_code != expected_loinc:
                    loinc_issues.append(
                        f"TestName: {test_name} - Incorrect loincCode. Expected: {expected_loinc}, Found: {loinc_code}")
                continue

            escaped_test_name = re.escape(test_name)
            search_names_match = csv_df[csv_df['Search Names'].str.contains(escaped_test_name, case=False, na=False)]

            if not search_names_match.empty:
                expected_loinc = search_names_match['Loinc'].iloc[0]
                if loinc_code != expected_loinc:
                    loinc_issues.append(
                        f"TestName: {test_name} - Incorrect loincCode. Expected: {expected_loinc}, Found: {loinc_code}")
                continue

            closest_match, similarity_score = self.find_closest_match(test_name, csv_df)
            unmatched_tests.append(f"TestName: {test_name} - Not found in CSV Test Name or Search Names")
            if closest_match:
                matching_row = csv_df[csv_df['Test Name'].str.contains(closest_match, case=False, na=False) |
                                      csv_df['Search Names'].str.contains(closest_match, case=False, na=False)]
                if not matching_row.empty:
                    test_name_ref = matching_row['Test Name'].iloc[0]
                    csv_update_suggestions.append(
                        f"Suggest adding '{test_name}' to Search Names for Test Name: {test_name_ref} (Similarity: {similarity_score}%)"
                    )
                else:
                    csv_update_suggestions.append(
                        f"No clear Test Name found for closest match '{closest_match}'. Suggest adding '{test_name}' to a new or related test (Similarity: {similarity_score}%)"
                    )
            else:
                csv_update_suggestions.append(
                    f"No similar test found for '{test_name}'. Suggest adding '{test_name}' to a new or related test in CSV."
                )

        return unmatched_tests, loinc_issues, csv_update_suggestions

    def run_validation(self):
        """Run the validation process and display results."""
        self.results_text.delete(1.0, tk.END)
        self.status_tree.delete(*self.status_tree.get_children())
        self.unit_tree.delete(*self.unit_tree.get_children())
        self.date_tree.delete(*self.date_tree.get_children())
        self.status_updates.clear()
        self.unit_updates.clear()
        self.date_updates.clear()
        self.csv_df = None
        self.one_to_rule_em_all_date.set("")  # Clear the "One to Rule 'Em All" field

        json_path = self.json_path.get()
        csv_path = self.csv_path.get()

        if not json_path or not csv_path:
            self.results_text.insert(tk.END, "Please select both JSON and CSV files.\n")
            return

        json_data = self.load_json_data(json_path)
        csv_df = self.load_csv_data(csv_path)

        if not json_data or csv_df.empty:
            self.results_text.insert(tk.END, "Failed to load data. Check logs for details.\n")
            return

        status_issues = self.validate_status_values(json_data)
        self.populate_unit_conversions(json_data)
        self.populate_date_updates(json_data)

        unmatched_tests, loinc_issues, csv_update_suggestions = self.validate_test_name_and_loinc(json_data, csv_df)

        self.display_results(json_data, status_issues, unmatched_tests, loinc_issues, csv_update_suggestions)

    def display_results(self, json_data, status_issues, unmatched_tests, loinc_issues, csv_update_suggestions):
        """Display validation results in the text area."""
        self.results_text.insert(tk.END, "Lab Data Validation Report\n\n")
        self.results_text.insert(tk.END, "Summary\n")
        self.results_text.insert(tk.END, f"Total Tests Processed: {len(json_data)}\n")
        self.results_text.insert(tk.END, f"Status Issues: {len(status_issues)}\n")
        self.results_text.insert(tk.END, f"Unmatched Test Names: {len(unmatched_tests)}\n")
        self.results_text.insert(tk.END, f"Loinc Validation Issues: {len(loinc_issues)}\n")
        self.results_text.insert(tk.END, f"CSV Update Suggestions: {len(csv_update_suggestions)}\n\n")

        self.results_text.insert(tk.END, "Status Issues\n")
        if status_issues:
            for issue in status_issues:
                self.results_text.insert(tk.END, f"{issue}\n")
        else:
            self.results_text.insert(tk.END, "No issues found\n")
        self.results_text.insert(tk.END, "\n")

        self.results_text.insert(tk.END, "Unmatched Test Names\n")
        if unmatched_tests:
            for test in unmatched_tests:
                self.results_text.insert(tk.END, f"{test}\n")
        else:
            self.results_text.insert(tk.END, "No unmatched Test Names found\n")
        self.results_text.insert(tk.END, "\n")

        self.results_text.insert(tk.END, "Loinc Validation Issues\n")
        if loinc_issues:
            for issue in loinc_issues:
                self.results_text.insert(tk.END, f"{issue}\n")
        else:
            self.results_text.insert(tk.END, "No Loinc issues found\n")
        self.results_text.insert(tk.END, "\n")

        self.results_text.insert(tk.END, "CSV Update Suggestions\n")
        if csv_update_suggestions:
            for suggestion in csv_update_suggestions:
                self.results_text.insert(tk.END, f"{suggestion}\n")
        else:
            self.results_text.insert(tk.END, "No CSV update suggestions\n")

    def show_status_combobox(self, event):
        """Show a Combobox when clicking on the 'New Status' column."""
        if self.current_combobox:
            self.current_combobox.destroy()
            self.current_combobox = None

        row_id = self.status_tree.identify_row(event.y)
        column = self.status_tree.identify_column(event.x)

        if not row_id or column != "#3":
            return

        bbox = self.status_tree.bbox(row_id, column)
        if not bbox:
            return

        x, y, width, height = bbox
        test_name = self.status_tree.item(row_id)['values'][0]

        combobox = ttk.Combobox(self.status_tree, values=["Select...", "inRange", "warning", "outOfRange", "optimal"],
                                state="readonly", width=15)
        combobox.place(x=x, y=y, width=width, height=height)
        combobox.current(0)
        combobox.bind("<<ComboboxSelected>>", lambda e, tn=test_name: self.update_status(tn, combobox.get()))
        combobox.focus_set()

        def destroy_combobox(e):
            if e.widget != combobox:
                combobox.destroy()
                self.current_combobox = None
                self.root.unbind("<Button-1>", destroy_id)

        destroy_id = self.root.bind("<Button-1>", destroy_combobox)
        self.current_combobox = combobox
        logging.info(f"Created Combobox for TestName: {test_name} (Status Update)")

    def show_unit_entry(self, event):
        """Show an Entry widget when clicking on the 'New Unit' column."""
        if self.current_combobox:
            self.current_combobox.destroy()
            self.current_combobox = None

        row_id = self.unit_tree.identify_row(event.y)
        column = self.unit_tree.identify_column(event.x)

        if not row_id or column != "#3":
            return

        bbox = self.unit_tree.bbox(row_id, column)
        if not bbox:
            return

        x, y, width, height = bbox
        test_name = self.unit_tree.item(row_id)['values'][0]

        entry = tk.Entry(self.unit_tree, width=20)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def save_unit(e):
            new_unit = entry.get().strip()
            if new_unit:
                self.unit_updates[test_name] = new_unit
                logging.info(f"Updated unit for {test_name} to {new_unit}")
                logging.info(f"Current unit updates: {self.unit_updates}")
                for item in self.unit_tree.get_children():
                    if self.unit_tree.item(item)['values'][0] == test_name:
                        current_values = self.unit_tree.item(item)['values']
                        self.unit_tree.item(item, values=(test_name, current_values[1], new_unit))
                        break
            entry.destroy()
            self.current_combobox = None
            self.root.unbind("<Return>", save_id)
            self.root.unbind("<FocusOut>", destroy_id)

        def destroy_entry(e):
            entry.destroy()
            self.current_combobox = None
            self.root.unbind("<Return>", save_id)
            self.root.unbind("<FocusOut>", destroy_id)

        save_id = self.root.bind("<Return>", save_unit)
        destroy_id = self.root.bind("<FocusOut>", destroy_entry)
        self.current_combobox = entry
        logging.info(f"Created Entry for TestName: {test_name} (Unit Update)")

    def show_date_entry(self, event):
        """Show an Entry widget when clicking on the 'New Date' column."""
        if self.current_combobox:
            self.current_combobox.destroy()
            self.current_combobox = None

        row_id = self.date_tree.identify_row(event.y)
        column = self.date_tree.identify_column(event.x)

        if not row_id or column != "#3":
            return

        bbox = self.date_tree.bbox(row_id, column)
        if not bbox:
            return

        x, y, width, height = bbox
        test_name = self.date_tree.item(row_id)['values'][0]

        entry = tk.Entry(self.date_tree, width=20)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        def save_date(e):
            new_date = entry.get().strip()
            if new_date:
                self.date_updates[test_name] = new_date
                logging.info(f"Updated date for {test_name} to {new_date}")
                logging.info(f"Current date updates: {self.date_updates}")
                for item in self.date_tree.get_children():
                    if self.date_tree.item(item)['values'][0] == test_name:
                        current_values = self.date_tree.item(item)['values']
                        self.date_tree.item(item, values=(test_name, current_values[1], new_date))
                        break
            entry.destroy()
            self.current_combobox = None
            self.root.unbind("<Return>", save_id)
            self.root.unbind("<FocusOut>", destroy_id)

        def destroy_entry(e):
            entry.destroy()
            self.current_combobox = None
            self.root.unbind("<Return>", save_id)
            self.root.unbind("<FocusOut>", destroy_id)

        save_id = self.root.bind("<Return>", save_date)
        destroy_id = self.root.bind("<FocusOut>", destroy_entry)
        self.current_combobox = entry
        logging.info(f"Created Entry for TestName: {test_name} (Date Update)")

    def update_status(self, test_name, new_status):
        """Store the new status for a test."""
        if new_status != "Select...":
            self.status_updates[test_name] = new_status
            logging.info(f"Updated status for {test_name} to {new_status}")
            logging.info(f"Current status updates: {self.status_updates}")
            for item in self.status_tree.get_children():
                if self.status_tree.item(item)['values'][0] == test_name:
                    current_values = self.status_tree.item(item)['values']
                    self.status_tree.item(item, values=(test_name, current_values[1], new_status, current_values[3],
                                                        current_values[4]))
                    break

    def save_updated_json(self):
        """Save only the enhancedSerScanObject with updated status, unit, and date values as the root of the new JSON file."""
        if not self.json_data:
            self.results_text.insert(tk.END, "\nNo JSON data loaded to save.\n")
            logging.error("No JSON data loaded to save.")
            return

        if not self.status_updates and not self.unit_updates and not self.date_updates:
            self.results_text.insert(tk.END, "\nNo status, unit, or date updates to save.\n")
            logging.info("No status, unit, or date updates to save.")
            return

        logging.info(f"Applying status updates: {self.status_updates}")
        logging.info(f"Applying unit updates: {self.unit_updates}")
        logging.info(f"Applying date updates: {self.date_updates}")

        # Get the enhancedSerScanObject and apply updates
        enhanced_data = self.json_data.get('enhancedSerScanObject', [])
        updated_count = 0
        for item in enhanced_data:
            test_name = item.get('TestName')
            if test_name in self.status_updates:
                item['status'] = self.status_updates[test_name]
                updated_count += 1
                logging.info(f"Updated {test_name} status to {item['status']}")
            if test_name in self.unit_updates:
                item['unit'] = self.unit_updates[test_name]
                updated_count += 1
                logging.info(f"Updated {test_name} unit to {item['unit']}")
            if test_name in self.date_updates:
                item['date'] = self.date_updates[test_name]
                updated_count += 1
                logging.info(f"Updated {test_name} date to {item['date']}")

        if updated_count == 0:
            self.results_text.insert(tk.END, "\nNo matching TestNames found in enhancedSerScanObject to update.\n")
            logging.warning("No matching TestNames found in enhancedSerScanObject to update.")
            return

        logging.info(f"Updated enhancedSerScanObject to be saved: {json.dumps(enhanced_data, indent=4)}")

        output_path = Path(self.json_path.get()).with_name("updated_" + Path(self.json_path.get()).name)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=4, ensure_ascii=False)
            self.results_text.insert(tk.END, f"\nUpdated enhancedSerScanObject saved to: {output_path}\n")
            logging.info(f"Successfully saved updated enhancedSerScanObject to: {output_path}")
        except Exception as e:
            self.results_text.insert(tk.END, f"\nError saving JSON: {str(e)}\n")
            logging.error(f"Error saving JSON: {str(e)}")


def main():
    root = tk.Tk()
    app = LabDataValidatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()