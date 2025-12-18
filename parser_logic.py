from collections import defaultdict


class LL1ParserLogic:
    def __init__(self, grammar, start_symbol, non_terminals):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.non_terminals = non_terminals
        self.terminals = set()
        self.first = defaultdict(set)
        self.follow = defaultdict(set)
        self.parsing_table = defaultdict(dict)

        # Identify Terminals
        for head, bodies in self.grammar.items():
            for body in bodies:
                for symbol in body:
                    if symbol not in self.non_terminals and symbol != 'ε':
                        self.terminals.add(symbol)
        self.terminals.add('$')

    def compute_first(self):
        for t in self.terminals:
            self.first[t].add(t)

        changed = True
        while changed:
            changed = False
            for head, bodies in self.grammar.items():
                for body in bodies:
                    if body == ['ε']:
                        if 'ε' not in self.first[head]:
                            self.first[head].add('ε')
                            changed = True
                        continue

                    # Compute First(Body)
                    has_epsilon = True
                    for symbol in body:
                        fs = self.first[symbol]
                        to_add = fs - {'ε'}
                        if not to_add.issubset(self.first[head]):
                            self.first[head].update(to_add)
                            changed = True
                        if 'ε' not in fs:
                            has_epsilon = False
                            break

                    if has_epsilon:
                        if 'ε' not in self.first[head]:
                            self.first[head].add('ε')
                            changed = True

    def compute_follow(self):
        self.follow[self.start_symbol].add('$')
        changed = True
        while changed:
            changed = False
            for head, bodies in self.grammar.items():
                for body in bodies:
                    if body == ['ε']: continue

                    for i, symbol in enumerate(body):
                        if symbol in self.non_terminals:
                            suffix = body[i + 1:]
                            # Calculate First(suffix)
                            suffix_first = set()
                            suffix_has_epsilon = True
                            if not suffix:
                                suffix_has_epsilon = True
                            else:
                                for s in suffix:
                                    fs = self.first[s]
                                    suffix_first.update(fs - {'ε'})
                                    if 'ε' not in fs:
                                        suffix_has_epsilon = False
                                        break

                            if not suffix_first.issubset(self.follow[symbol]):
                                self.follow[symbol].update(suffix_first)
                                changed = True

                            if suffix_has_epsilon:
                                if not self.follow[head].issubset(self.follow[symbol]):
                                    self.follow[symbol].update(self.follow[head])
                                    changed = True

    def build_table(self):
        self.parsing_table = defaultdict(dict)
        for head, bodies in self.grammar.items():
            for body in bodies:
                # First(Body)
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

                # Rule 1
                for term in first_body:
                    if term != 'ε':
                        self.parsing_table[head][term] = body

                # Rule 2
                if 'ε' in first_body:
                    for term in self.follow[head]:
                        self.parsing_table[head][term] = body

    def parse_string(self, input_string):
        """
        Returns: (trace, success, root_node)
        Trace is a list of steps.
        Root_node is a dict structure for the tree: {'id': unique_id, 'label': 'E', 'children': []}
        """
        tokens = input_string.strip().split()
        tokens.append('$')

        # We need a custom stack that tracks Tree Nodes
        # Node structure: [label, children_list]
        root_node = {'label': self.start_symbol, 'children': []}

        # Stack contains tuples: (symbol, parent_node_reference)
        # However, parent_node needs to know WHERE to add the child.
        # A simpler way: The stack contains Node objects.

        class TreeNode:
            def __init__(self, label):
                self.label = label
                self.children = []

        root_obj = TreeNode(self.start_symbol)
        stack = [TreeNode('$'), root_obj]

        trace = []
        pointer = 0
        success = False

        while len(stack) > 0:
            top_node = stack[-1]
            top_symbol = top_node.label
            current_input = tokens[pointer]

            step_data = {
                "stack": " ".join([n.label for n in stack]),
                "input": " ".join(tokens[pointer:]),
                "action": ""
            }

            if top_symbol == current_input:
                step_data["action"] = f"Match {current_input}"
                stack.pop()
                pointer += 1
                if top_symbol == '$':
                    step_data["action"] = "Accept"
                    success = True
                    trace.append(step_data)
                    break
            elif top_symbol in self.terminals:
                step_data["action"] = "Error: Mismatch"
                trace.append(step_data)
                return trace, False, root_obj
            elif top_symbol in self.non_terminals:
                entry = self.parsing_table.get(top_symbol, {}).get(current_input)
                if entry is not None:
                    step_data["action"] = f"{top_symbol} -> {' '.join(entry)}"
                    stack.pop()  # Pop the Non-Terminal

                    # Create children nodes
                    new_nodes = []
                    if entry == ['ε']:
                        child = TreeNode('ε')
                        top_node.children.append(child)
                        # Do not push epsilon to stack
                    else:
                        for symbol in entry:
                            child = TreeNode(symbol)
                            new_nodes.append(child)
                            top_node.children.append(child)

                        # Push to stack in reverse
                        for child in reversed(new_nodes):
                            stack.append(child)
                else:
                    step_data["action"] = "Error: No Rule"
                    trace.append(step_data)
                    return trace, False, root_obj
            else:
                step_data["action"] = "Error: Unknown Symbol"
                trace.append(step_data)
                return trace, False, root_obj

            trace.append(step_data)

        return trace, success, root_obj