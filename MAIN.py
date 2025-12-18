import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict

class LL1Parser:
    def __init__(self, grammar_text):
        self.grammar = {}
        self.start_symbol = None
        self.terminals = set()
        self.non_terminals = set()
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.parsing_table = {}
        self.original_grammar_text = grammar_text

        self.parse_grammar(grammar_text)

    def parse_grammar(self, text):
        """Parses raw text into a dictionary structure."""
        lines = text.strip().split('\n')
        self.grammar = {}
        self.non_terminals = set()
        self.terminals = set()

        first_line = True
        for line in lines:
            line = line.strip()
            if not line: continue

            if '->' in line:
                head, body = line.split('->')
            else:
                continue  # Skip invalid lines

            head = head.strip()
            if first_line:
                self.start_symbol = head
                first_line = False

            self.non_terminals.add(head)

            alternatives = [alt.strip().split() for alt in body.split('|')]
            if head not in self.grammar:
                self.grammar[head] = []
            self.grammar[head].extend(alternatives)

        # Identify Terminals
        for head, bodies in self.grammar.items():
            for body in bodies:
                for symbol in body:
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
        self.terminals.add('$')

    def remove_left_recursion(self):
        """Eliminates immediate left recursion."""
        new_grammar = {}
        ordered_non_terminals = list(self.grammar.keys())  # processing order matters

        for head in ordered_non_terminals:
            bodies = self.grammar[head]
            recursive = []
            non_recursive = []

            for body in bodies:
                if body[0] == head:
                    recursive.append(body[1:])  # Store alpha
                else:
                    non_recursive.append(body)  # Store beta

            if not recursive:
                new_grammar[head] = bodies
            else:
                # Create new Non-Terminal
                new_head = head + "'"
                self.non_terminals.add(new_head)
                self.non_terminals.add(head)  # Ensure original is kept

                # A -> beta A'
                new_grammar[head] = []
                for beta in non_recursive:
                    if beta == ['ε']:
                        new_grammar[head].append([new_head])
                    else:
                        new_grammar[head].append(beta + [new_head])

                # A' -> alpha A' | ε
                new_grammar[new_head] = []
                for alpha in recursive:
                    new_grammar[new_head].append(alpha + [new_head])
                new_grammar[new_head].append(['ε'])

        self.grammar = new_grammar
        # Re-calculate terminals just in case
        self.terminals = set()
        for head, bodies in self.grammar.items():
            for body in bodies:
                for symbol in body:
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
        self.terminals.add('$')
        return self.format_grammar()

    def format_grammar(self):
        """Returns string representation of current grammar."""
        res = []
        for head, bodies in self.grammar.items():
            bodies_str = [" ".join(b) for b in bodies]
            res.append(f"{head} -> {' | '.join(bodies_str)}")
        return "\n".join(res)

    def compute_first(self):
        """Computes First sets for all symbols."""
        self.first = defaultdict(set)

        # Initialize terminals
        for t in self.terminals:
            self.first[t].add(t)

        changed = True
        while changed:
            changed = False
            for head, bodies in self.grammar.items():
                for body in bodies:
                    # Logic for First(Head)
                    # If body is epsilon
                    if body == ['ε']:
                        if 'ε' not in self.first[head]:
                            self.first[head].add('ε')
                            changed = True
                        continue

                    # Iterate through symbols in the body
                    has_epsilon = True
                    for symbol in body:
                        # Add First(symbol) - {ε} to First(head)
                        fs = self.first[symbol]

                        to_add = fs - {'ε'}
                        if not to_add.issubset(self.first[head]):
                            self.first[head].update(to_add)
                            changed = True

                        if 'ε' not in fs:
                            has_epsilon = False
                            break

                    # If all symbols derive epsilon, add epsilon to head
                    if has_epsilon:
                        if 'ε' not in self.first[head]:
                            self.first[head].add('ε')
                            changed = True

    def compute_follow(self):
        """Computes Follow sets."""
        self.follow = defaultdict(set)
        self.follow[self.start_symbol].add('$')

        changed = True
        while changed:
            changed = False
            for head, bodies in self.grammar.items():
                for body in bodies:
                    if body == ['ε']: continue

                    # Trailing Logic
                    # A -> a B b
                    for i, symbol in enumerate(body):
                        if symbol in self.non_terminals:
                            # Look at what follows B (the suffix)
                            suffix = body[i + 1:]

                            if not suffix:
                                # A -> a B. Follow(B) += Follow(A)
                                if not self.follow[head].issubset(self.follow[symbol]):
                                    self.follow[symbol].update(self.follow[head])
                                    changed = True
                            else:
                                # Calculate First(suffix)
                                first_of_suffix = set()
                                suffix_has_epsilon = True
                                for s in suffix:
                                    fs = self.first[s]
                                    first_of_suffix.update(fs - {'ε'})
                                    if 'ε' not in fs:
                                        suffix_has_epsilon = False
                                        break

                                if not first_of_suffix.issubset(self.follow[symbol]):
                                    self.follow[symbol].update(first_of_suffix)
                                    changed = True

                                if suffix_has_epsilon:
                                    if not self.follow[head].issubset(self.follow[symbol]):
                                        self.follow[symbol].update(self.follow[head])
                                        changed = True

    def build_table(self):
        """Constructs the LL(1) Parsing Table."""
        self.parsing_table = defaultdict(dict)

        for head, bodies in self.grammar.items():
            for body in bodies:
                # Calculate First(body)
                first_body = set()
                body_has_epsilon = True
                if body == ['ε']:
                    first_body.add('ε')
                else:
                    for s in body:
                        fs = self.first[s]
                        first_body.update(fs - {'ε'})
                        if 'ε' not in fs:
                            body_has_epsilon = False
                            break
                    if body_has_epsilon:
                        first_body.add('ε')

                # Rule 1: For each terminal 'a' in First(body), add A->body to M[A,a]
                for term in first_body:
                    if term != 'ε':
                        self.parsing_table[head][term] = body

                # Rule 2: If epsilon in First(body), add A->body to M[A,b] for each b in Follow(A)
                if 'ε' in first_body:
                    for term in self.follow[head]:
                        self.parsing_table[head][term] = body

    def parse_string(self, input_string):
        """Simulates the parsing process."""
        # Tokenizer (Simple space split, adding $)
        tokens = input_string.strip().split()
        tokens.append('$')

        stack = ['$', self.start_symbol]
        trace = []

        pointer = 0
        while len(stack) > 0:
            top = stack[-1]
            current_input = tokens[pointer]

            step_data = {
                "stack": " ".join(stack),
                "input": " ".join(tokens[pointer:]),
                "action": ""
            }

            if top == current_input:
                # Match
                step_data["action"] = f"Match {current_input}"
                stack.pop()
                pointer += 1
                if top == '$':
                    step_data["action"] = "Accept"
                    trace.append(step_data)
                    break
            elif top in self.terminals:
                # Error: Terminal on stack doesn't match input
                step_data["action"] = "Error"
                trace.append(step_data)
                return trace, False
            elif top in self.non_terminals:
                # Lookup table
                entry = self.parsing_table.get(top, {}).get(current_input)
                if entry is not None:
                    # Derivation
                    step_data["action"] = f"{top} -> {' '.join(entry)}"
                    stack.pop()
                    if entry != ['ε']:
                        # Push body in reverse order
                        for symbol in reversed(entry):
                            stack.append(symbol)
                else:
                    step_data["action"] = "Error (No Rule)"
                    trace.append(step_data)
                    return trace, False
            else:
                step_data["action"] = "Error (Unknown Symbol)"
                trace.append(step_data)
                return trace, False

            trace.append(step_data)

        return trace, True


# ==========================================
# FRONTEND: TKINTER GUI
# ==========================================

class LL1GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HiLCoE Project - LL(1) Parser")
        self.root.geometry("1100x750")

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

        self.setup_ui()
        self.parser = None

    def setup_ui(self):
        # --- Top Frame: Inputs ---
        input_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        input_frame.pack(side="top", fill="x", padx=10, pady=5)

        # Grammar Input
        lbl_grammar = ttk.Label(input_frame, text="Grammar (use 'ε' for epsilon, space separated):")
        lbl_grammar.grid(row=0, column=0, sticky="w")

        self.txt_grammar = tk.Text(input_frame, height=6, width=60)
        self.txt_grammar.grid(row=1, column=0, rowspan=3, padx=5, pady=5)
        # Default Grammar (Left recursive for demo)
        default_grammar = "E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id"
        self.txt_grammar.insert("1.0", default_grammar)

        # Input String
        lbl_input = ttk.Label(input_frame, text="Input String (space separated):")
        lbl_input.grid(row=1, column=1, sticky="w", padx=10)

        self.entry_input = ttk.Entry(input_frame, width=40)
        self.entry_input.grid(row=2, column=1, sticky="w", padx=10)
        self.entry_input.insert(0, "id + id * id")

        # Parse Button
        btn_parse = ttk.Button(input_frame, text="Generate & Parse", command=self.run_parsing)
        btn_parse.grid(row=3, column=1, sticky="w", padx=10)

        # --- Bottom Frame: Notebook (Tabs) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Tab 1: Analysis (Left Rec + First/Follow)
        self.tab_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analysis, text="Step 1: Analysis")
        self.setup_analysis_tab()

        # Tab 2: Parsing Table
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text="Step 2: Parsing Table")

        # Tab 3: Simulation Trace
        self.tab_sim = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sim, text="Step 3: Simulation")
        self.setup_simulation_tab()

    def setup_analysis_tab(self):
        # Grid layout for Analysis Tab
        self.tab_analysis.columnconfigure(0, weight=1)
        self.tab_analysis.columnconfigure(1, weight=1)

        # Box 1: Grammar after Left Recursion Removal
        frame_grammar = ttk.LabelFrame(self.tab_analysis, text="Grammar (Left Recursion Removed)")
        frame_grammar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.lbl_grammar_clean = tk.Text(frame_grammar, height=10, width=40, state="disabled", bg="#f0f0f0")
        self.lbl_grammar_clean.pack(expand=True, fill="both", padx=5, pady=5)

        # Box 2: First & Follow Table
        frame_ff = ttk.LabelFrame(self.tab_analysis, text="First & Follow Sets")
        frame_ff.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        columns = ("NT", "Prods", "First", "Follow")
        self.tree_ff = ttk.Treeview(frame_ff, columns=columns, show="headings")
        self.tree_ff.heading("NT", text="Non-Terminal")
        self.tree_ff.heading("Prods", text="Productions")
        self.tree_ff.heading("First", text="First Set")
        self.tree_ff.heading("Follow", text="Follow Set")

        self.tree_ff.column("NT", width=80)
        self.tree_ff.column("Prods", width=200)
        self.tree_ff.column("First", width=150)
        self.tree_ff.column("Follow", width=150)

        self.tree_ff.pack(expand=True, fill="both", padx=5, pady=5)

    def setup_simulation_tab(self):
        columns = ("Step", "Stack", "Input", "Action")
        self.tree_sim = ttk.Treeview(self.tab_sim, columns=columns, show="headings")
        self.tree_sim.heading("Step", text="Step")
        self.tree_sim.heading("Stack", text="Stack")
        self.tree_sim.heading("Input", text="Input Buffer")
        self.tree_sim.heading("Action", text="Action")

        self.tree_sim.column("Step", width=50, anchor="center")
        self.tree_sim.column("Stack", width=300)
        self.tree_sim.column("Input", width=300, anchor="e")
        self.tree_sim.column("Action", width=250)

        self.tree_sim.pack(expand=True, fill="both", padx=5, pady=5)

    def run_parsing(self):
        grammar_text = self.txt_grammar.get("1.0", tk.END).strip()
        input_string = self.entry_input.get().strip()

        if not grammar_text:
            messagebox.showerror("Error", "Please enter grammar")
            return

        try:
            # 1. Initialize and Remove Left Recursion
            self.parser = LL1Parser(grammar_text)
            clean_grammar = self.parser.remove_left_recursion()

            # Display Clean Grammar
            self.lbl_grammar_clean.config(state="normal")
            self.lbl_grammar_clean.delete("1.0", tk.END)
            self.lbl_grammar_clean.insert("1.0", clean_grammar)
            self.lbl_grammar_clean.config(state="disabled")

            # 2. Compute Sets
            self.parser.compute_first()
            self.parser.compute_follow()

            # Display First/Follow
            for item in self.tree_ff.get_children():
                self.tree_ff.delete(item)

            for nt in self.parser.non_terminals:
                prods = " | ".join([" ".join(p) for p in self.parser.grammar[nt]])
                first_str = f"{{ {', '.join(self.parser.first[nt])} }}"
                follow_str = f"{{ {', '.join(self.parser.follow[nt])} }}"
                self.tree_ff.insert("", "end", values=(nt, prods, first_str, follow_str))

            # 3. Build Parsing Table
            self.parser.build_table()
            self.render_parsing_table()

            # 4. Simulation
            trace, success = self.parser.parse_string(input_string)
            self.render_simulation(trace)

            if success:
                messagebox.showinfo("Result", "String Accepted!")
            else:
                messagebox.showerror("Result", "String Rejected / Parsing Error")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def render_parsing_table(self):
        # Clear previous table widget
        for widget in self.tab_table.winfo_children():
            widget.destroy()

        # Get all terminals (columns)
        terminals = sorted(list(self.parser.terminals))
        if 'ε' in terminals: terminals.remove('ε')  # Epsilon is not a column in table

        columns = ["NT"] + terminals

        tree_table = ttk.Treeview(self.tab_table, columns=columns, show="headings")
        tree_table.heading("NT", text="Non-Terminal")
        tree_table.column("NT", width=100, anchor="center")

        for t in terminals:
            tree_table.heading(t, text=t)
            tree_table.column(t, width=80, anchor="center")

        for nt in self.parser.non_terminals:
            row_vals = [nt]
            for t in terminals:
                prod = self.parser.parsing_table.get(nt, {}).get(t)
                if prod:
                    row_vals.append(f"{nt} -> {' '.join(prod)}")
                else:
                    row_vals.append("")
            tree_table.insert("", "end", values=row_vals)

        tree_table.pack(expand=True, fill="both", padx=5, pady=5)

    def render_simulation(self, trace):
        for item in self.tree_sim.get_children():
            self.tree_sim.delete(item)

        for i, step in enumerate(trace):
            self.tree_sim.insert("", "end", values=(i + 1, step["stack"], step["input"], step["action"]))


if __name__ == "__main__":
    root = tk.Tk()
    app = LL1GUI(root)
    root.mainloop()