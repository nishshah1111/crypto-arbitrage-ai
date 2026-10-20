import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

# Create horizontal flowchart
fig, ax = plt.subplots(figsize=(16, 4))
ax.set_xlim(0, 30)
ax.set_ylim(0, 5)
ax.axis('off')

# Simple box drawing function (black and white)
def draw_box(x, y, width, height, text):
    rect = Rectangle((x, y), width, height, facecolor='white', 
                     edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    ax.text(x + width/2, y + height/2, text, ha='center', va='center', 
            fontsize=9, fontweight='bold')

# Simple arrow function
def draw_arrow(x1, y1, x2, y2):
    arrow = FancyArrowPatch((x1, y1), (x2, y2), 
                           arrowstyle='->', mutation_scale=20, 
                           linewidth=2, color='black')
    ax.add_patch(arrow)

# Title
ax.text(15, 4.3, 'System Flow Diagram', ha='center', fontsize=14, fontweight='bold')

# Horizontal flow
y_center = 2

# Step 1: Data Collection
draw_box(0.5, y_center - 0.4, 3.5, 0.8, 'Data Collection\nfrom Exchanges')
draw_arrow(4, y_center, 4.8, y_center)

# Step 2: Merge Data
draw_box(4.8, y_center - 0.4, 3.5, 0.8, 'Data Merging &\nSynchronization')
draw_arrow(8.3, y_center, 9.1, y_center)

# Step 3: Calculate Spreads
draw_box(9.1, y_center - 0.4, 3.5, 0.8, 'Spread\nCalculation')
draw_arrow(12.6, y_center, 13.4, y_center)

# Step 4: Add Features
draw_box(13.4, y_center - 0.4, 3.5, 0.8, 'Feature\nEngineering')
draw_arrow(16.9, y_center, 17.7, y_center)

# Step 5: Train Models
draw_box(17.7, y_center - 0.4, 3.5, 0.8, 'Model Training\n(72 models)')
draw_arrow(21.2, y_center, 22, y_center)

# Step 6: Evaluate
draw_box(22, y_center - 0.4, 3.5, 0.8, 'Performance\nEvaluation')
draw_arrow(25.5, y_center, 26.3, y_center)

# Step 7: Results
draw_box(26.3, y_center - 0.4, 3.5, 0.8, 'Results &\nVisualization')

plt.tight_layout()
plt.savefig('analysis/paper_figures/simple_flowchart.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('analysis/paper_figures/simple_flowchart.pdf', bbox_inches='tight', facecolor='white')
print("✓ Simple flowchart generated!")
print("  - analysis/paper_figures/simple_flowchart.png")
print("  - analysis/paper_figures/simple_flowchart.pdf")
plt.close()
