class TreeDrawer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.node_radius = 20
        self.level_height = 80

    def draw(self, root_node):
        self.canvas.delete("all")
        if not root_node: return

        # 1. Assign coordinates
        self.leaves_count = 0
        self.assign_coords(root_node, 0)

        # Center the tree
        canvas_width = int(self.canvas['width'])
        # A simple centering strategy based on number of leaves
        total_width = max(1, self.leaves_count) * 60
        start_x = (canvas_width - total_width) // 2

        # 2. Draw Recursive
        self.draw_recursive(root_node, start_x + 30)

    def assign_coords(self, node, depth):
        # We don't calculate exact X here, just traverse to count leaves
        # We will determine X during drawing based on leaf index
        if not node.children:
            node.leaf_index = self.leaves_count
            self.leaves_count += 1
        else:
            for child in node.children:
                self.assign_coords(child, depth + 1)

    def draw_recursive(self, node, offset_x):
        # Calculate X position:
        # If leaf: x is based on its index
        # If internal: x is average of first and last child

        x = self.get_node_x(node) * 60 + offset_x
        y = self.get_node_depth(node) * self.level_height + 50

        # Draw connections to children
        if node.children:
            for child in node.children:
                child_x = self.get_node_x(child) * 60 + offset_x
                child_y = self.get_node_depth(child) * self.level_height + 50
                self.canvas.create_line(x, y + self.node_radius, child_x, child_y - self.node_radius, fill="#555")
                self.draw_recursive(child, offset_x)

        # Draw Node
        self.canvas.create_oval(x - self.node_radius, y - self.node_radius,
                                x + self.node_radius, y + self.node_radius,
                                fill="#e1f5fe", outline="#0277bd")
        self.canvas.create_text(x, y, text=node.label, font=("Arial", 10, "bold"))

    def get_node_x(self, node):
        if not node.children:
            return node.leaf_index
        else:
            # Average of children
            first = self.get_node_x(node.children[0])
            last = self.get_node_x(node.children[-1])
            return (first + last) / 2

    def get_node_depth(self, node, depth=0):
        # We need to store depth in the node object during assign_coords for efficiency,
        # but let's just hack it here by traversing up? No, parent pointer missing.
        # Let's re-traverse or just pass depth in draw_recursive.
        # Better: Modify assign_coords to store depth.
        return getattr(node, 'depth', 0)

    # Redefine assign_coords to store depth
    def assign_coords(self, node, depth):
        node.depth = depth
        if not node.children:
            node.leaf_index = self.leaves_count
            self.leaves_count += 1
        else:
            for child in node.children:
                self.assign_coords(child, depth + 1)