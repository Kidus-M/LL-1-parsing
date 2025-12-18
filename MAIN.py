import tkinter as tk
from tkinter import ttk, messagebox
import grammar_utils
from parser_logic import LL1ParserLogic
from tree_drawer import TreeDrawer


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HiLCoE Project - Modular LL(1) Parser")
        self.root.geometry("1200x800")

        self.parser_logic = None
        self.setup_ui()

    def setup_ui(self):
        # --- Top Frame: Inputs ---
        control_frame = ttk.LabelFrame(self.root, text="Step 0: Configuration", padding=10)
        control_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Grammar Input
        tk.Label(control_frame, text="Grammar:").grid(row=0, column=0, sticky="nw")
        self.txt_grammar = tk.Text(control_frame, height=5, width=50)
        self.txt_grammar.grid(row=1, column=0, padx=5, pady=5)
        self.txt_grammar.insert("1.0", "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id")

        # Input String
        tk.Label(control_frame, text="Input String:").grid(row=0, column=1, sticky="nw")
        self.entry_input = ttk.Entry(control_frame, width=30)
        self.entry_input.grid(row=1, column=1, sticky="n", padx=5, pady=5)
        self.entry_input.insert(0, "id + id * id")

        # Run Button
        ttk.Button(control_frame, text="Run Complete Parsing", command=self.run_process).grid(row=1, column=2, padx=20)

        # --- Main Tabs ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # Tab 1: Left Recursion & Analysis
        self.tab_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analysis, text="Step 1 & 2: Sets")
        self.setup_analysis_tab()

        # Tab 2: Parsing Table
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text="Step 3: Table")
        self.tree_table = ttk.Treeview(self.tab_table)  # Placeholder
        self.tree_table.pack(expand=True, fill="both")

        # Tab 3: Simulation
        self.tab_sim = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sim, text="Step 4: Simulation")
        self.setup_simulation_tab()

        # Tab 4: Parse Tree
        self.tab_tree = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_tree, text="Step 5: Parse Tree")

        self.canvas_tree = tk.Canvas(self.tab_tree, bg="white", width=1100, height=600, scrollregion=(0, 0, 2000, 2000))

        # Scrollbars for canvas
        hbar = ttk.Scrollbar(self.tab_tree, orient="horizontal", command=self.canvas_tree.xview)
        hbar.pack(side="bottom", fill="x")
        vbar = ttk.Scrollbar(self.tab_tree, orient="vertical", command=self.canvas_tree.yview)
        vbar.pack(side="right", fill="y")
        self.canvas_tree.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas_tree.pack(side="left", expand=True, fill="both")

        self.tree_drawer = TreeDrawer(self.canvas_tree)

    def setup_analysis_tab(self):
        # Two columns: Clean Grammar | First/Follow
        self.tab_analysis.columnconfigure(0, weight=1)
        self.tab_analysis.columnconfigure(1, weight=1)

        f1 = ttk.LabelFrame(self.tab_analysis, text="Grammar (Left Recursion Removed)")
        f1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.lbl_clean_grammar = tk.Text(f1, height=15, width=40, state="disabled", bg="#f0f0f0")
        self.lbl_clean_grammar.pack(fill="both", expand=True)

        f2 = ttk.LabelFrame(self.tab_analysis, text="First & Follow")
        f2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        cols = ("NT", "First", "Follow")
        self.tree_sets = ttk.Treeview(f2, columns=cols, show="headings")
        self.tree_sets.heading("NT", text="Non-Terminal")
        self.tree_sets.heading("First", text="First")
        self.tree_sets.heading("Follow", text="Follow")
        self.tree_sets.pack(fill="both", expand=True)

    def setup_simulation_tab(self):
        cols = ("Step", "Stack", "Input", "Action")
        self.tree_sim = ttk.Treeview(self.tab_sim, columns=cols, show="headings")
        self.tree_sim.heading("Step", text="Step")
        self.tree_sim.column("Step", width=50)
        self.tree_sim.heading("Stack", text="Stack")
        self.tree_sim.heading("Input", text="Input")
        self.tree_sim.heading("Action", text="Action")
        self.tree_sim.pack(fill="both", expand=True)

    def run_process(self):
        raw_grammar = self.txt_grammar.get("1.0", tk.END)
        input_str = self.entry_input.get()

        try:
            # 1. Parse & Remove Left Recursion (grammar_utils.py)
            grammar_dict, start, non_terms = grammar_utils.parse_grammar(raw_grammar)
            clean_grammar, non_terms = grammar_utils.remove_left_recursion(grammar_dict, non_terms)

            # Display Clean Grammar
            self.lbl_clean_grammar.config(state="normal")
            self.lbl_clean_grammar.delete("1.0", tk.END)
            self.lbl_clean_grammar.insert("1.0", grammar_utils.format_grammar(clean_grammar))
            self.lbl_clean_grammar.config(state="disabled")

            # 2. Logic (parser_logic.py)
            self.parser_logic = LL1ParserLogic(clean_grammar, start, non_terms)
            self.parser_logic.compute_first()
            self.parser_logic.compute_follow()

            # Display Sets
            for item in self.tree_sets.get_children(): self.tree_sets.delete(item)
            for nt in self.parser_logic.non_terminals:
                f = ", ".join(self.parser_logic.first[nt])
                fl = ", ".join(self.parser_logic.follow[nt])
                self.tree_sets.insert("", "end", values=(nt, f"{{ {f} }}", f"{{ {fl} }}"))

            # 3. Table
            self.parser_logic.build_table()
            self.render_table()

            # 4. Simulation & Tree
            trace, success, root_node = self.parser_logic.parse_string(input_str)

            # Render Simulation
            for item in self.tree_sim.get_children(): self.tree_sim.delete(item)
            for i, step in enumerate(trace):
                self.tree_sim.insert("", "end", values=(i + 1, step['stack'], step['input'], step['action']))

            # Render Tree
            self.tree_drawer.draw(root_node)

            if success:
                messagebox.showinfo("Success", "String Accepted!")
            else:
                messagebox.showerror("Failure", "String Rejected or Parsing Error")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            raise e

    def render_table(self):
        # Dynamic Table Columns
        self.tree_table.destroy()
        terminals = sorted(list(self.parser_logic.terminals))
        if 'ε' in terminals: terminals.remove('ε')

        cols = ["NT"] + terminals
        self.tree_table = ttk.Treeview(self.tab_table, columns=cols, show="headings")

        self.tree_table.heading("NT", text="Non-Terminal")
        self.tree_table.column("NT", width=80, anchor="center")

        for t in terminals:
            self.tree_table.heading(t, text=t)
            self.tree_table.column(t, width=80, anchor="center")

        for nt in self.parser_logic.non_terminals:
            row = [nt]
            for t in terminals:
                prod = self.parser_logic.parsing_table.get(nt, {}).get(t)
                row.append(" -> ".join([nt, " ".join(prod)]) if prod else "")
            self.tree_table.insert("", "end", values=row)

        self.tree_table.pack(expand=True, fill="both")


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()