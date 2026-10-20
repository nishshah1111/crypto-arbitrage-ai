"""
Visualization Script for Research Paper
Generates all relevant graphs showing ML performance vs economic viability trade-off
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import warnings

warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

# Load data
print("Loading data...")
ml_results = pd.read_csv('data/model_results.csv')
economic_results = pd.read_csv('data/economic_analysis_results.csv')
btc = pd.read_csv('data/btc_usdt_features.csv')
eth = pd.read_csv('data/eth_usdt_features.csv')

# Filter classification models only
ml_results_class = ml_results[ml_results['Model'].isin(['RF', 'XGBoost'])].copy()
ml_results_class['F1_Score'] = pd.to_numeric(ml_results_class['F1_Score'])
ml_results_class['Accuracy'] = pd.to_numeric(ml_results_class['Accuracy'])

print("Creating visualizations...")

# ============================================================================
# FIGURE 1: ML Performance vs Economic Viability Trade-off (MAIN FIGURE)
# ============================================================================
fig1, ax1 = plt.subplots(figsize=(10, 6))

thresholds = [0.1, 0.2, 0.5]
threshold_labels = ['0.1%', '0.2%', '0.5%']

# Get best F1 scores for each threshold
btc_f1 = []
eth_f1 = []
for t_label in threshold_labels:
    btc_subset = ml_results_class[(ml_results_class['Pair'] == 'BTC/USDT') & 
                                   (ml_results_class['Threshold'] == t_label)]
    eth_subset = ml_results_class[(ml_results_class['Pair'] == 'ETH/USDT') & 
                                   (ml_results_class['Threshold'] == t_label)]
    btc_f1.append(btc_subset['F1_Score'].max() if len(btc_subset) > 0 else 0)
    eth_f1.append(eth_subset['F1_Score'].max() if len(eth_subset) > 0 else 0)

# Get net profit from economic results
btc_profit = []
eth_profit = []
for t_label in threshold_labels:
    btc_econ = economic_results[(economic_results['Pair'] == 'BTC/USDT') & 
                                 (economic_results['Threshold'] == t_label)]
    eth_econ = economic_results[(economic_results['Pair'] == 'ETH/USDT') & 
                                 (economic_results['Threshold'] == t_label)]
    btc_profit.append(float(btc_econ['Avg_Net_Profit'].values[0].rstrip('%')) if len(btc_econ) > 0 else 0)
    eth_profit.append(float(eth_econ['Avg_Net_Profit'].values[0].rstrip('%')) if len(eth_econ) > 0 else 0)

# Plot with dual y-axes
ax1_twin = ax1.twinx()

# ML Performance (F1 Score)
line1 = ax1.plot(thresholds, btc_f1, 'o-', label='BTC/USDT F1 Score', 
                 color='#f7931a', linewidth=3, markersize=10, markeredgecolor='black')
line2 = ax1.plot(thresholds, eth_f1, 's-', label='ETH/USDT F1 Score', 
                 color='#627eea', linewidth=3, markersize=10, markeredgecolor='black')

# Economic Performance (Net Profit)
line3 = ax1_twin.plot(thresholds, btc_profit, 'D--', label='BTC/USDT Net Profit', 
                      color='darkgreen', linewidth=3, markersize=10, markeredgecolor='black', alpha=0.8)
line4 = ax1_twin.plot(thresholds, eth_profit, '^--', label='ETH/USDT Net Profit', 
                      color='darkblue', linewidth=3, markersize=10, markeredgecolor='black', alpha=0.8)

# Formatting
ax1.set_xlabel('Arbitrage Threshold (%)', fontsize=13, fontweight='bold')
ax1.set_ylabel('F1 Score (ML Performance)', fontsize=13, fontweight='bold', color='black')
ax1_twin.set_ylabel('Average Net Profit % (Economic Performance)', fontsize=13, fontweight='bold', color='darkgreen')
ax1.set_title('The Trade-off: ML Performance vs Economic Viability\nInverse Relationship in Cryptocurrency Arbitrage', 
              fontsize=14, fontweight='bold', pad=20)

# Set axis limits
ax1.set_ylim([-0.05, 1.0])
ax1.set_xlim([0.05, 0.55])
ax1_twin.axhline(y=0, color='red', linestyle=':', alpha=0.6, linewidth=2, label='Break-even')

# Grid
ax1.grid(True, alpha=0.3)

# Combined legend
lines = line1 + line2 + line3 + line4
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left', fontsize=11, framealpha=0.9)

# Add annotations
ax1.annotate('High ML Performance\nBut UNPROFITABLE', 
             xy=(0.1, btc_f1[0]), xytext=(0.15, 0.7),
             arrowprops=dict(arrowstyle='->', color='red', lw=2),
             fontsize=10, color='red', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

ax1.annotate('Optimal Balance\n(Recommended)', 
             xy=(0.2, btc_f1[1]), xytext=(0.25, 0.4),
             arrowprops=dict(arrowstyle='->', color='green', lw=2),
             fontsize=10, color='green', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7))

plt.tight_layout()
plt.savefig('data/figures/fig1_ml_vs_economic_tradeoff.png', bbox_inches='tight')
print("✓ Saved: fig1_ml_vs_economic_tradeoff.png")

# ============================================================================
# FIGURE 2: Opportunity Distribution by Threshold
# ============================================================================
fig2, ax2 = plt.subplots(figsize=(10, 6))

btc_opps = [btc[f'arbitrage_label_{t}'].sum() for t in thresholds]
eth_opps = [eth[f'arbitrage_label_{t}'].sum() for t in thresholds]

x = np.arange(len(threshold_labels))
width = 0.35

bars1 = ax2.bar(x - width/2, btc_opps, width, label='BTC/USDT', 
                color='#f7931a', alpha=0.8, edgecolor='black', linewidth=1.5)
bars2 = ax2.bar(x + width/2, eth_opps, width, label='ETH/USDT', 
                color='#627eea', alpha=0.8, edgecolor='black', linewidth=1.5)

ax2.set_xlabel('Arbitrage Threshold', fontsize=13, fontweight='bold')
ax2.set_ylabel('Number of Opportunities', fontsize=13, fontweight='bold')
ax2.set_title('Arbitrage Opportunity Distribution by Threshold\n(5 days, 1-minute intervals)', 
              fontsize=14, fontweight='bold', pad=20)
ax2.set_xticks(x)
ax2.set_xticklabels(threshold_labels, fontsize=12)
ax2.legend(fontsize=12)
ax2.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('data/figures/fig2_opportunity_distribution.png', bbox_inches='tight')
print("✓ Saved: fig2_opportunity_distribution.png")

# ============================================================================
# FIGURE 3: Model Performance Comparison (F1 Scores)
# ============================================================================
fig3, axes = plt.subplots(1, 3, figsize=(15, 5))
fig3.suptitle('Model Performance Comparison Across Thresholds', fontsize=14, fontweight='bold')

for idx, (threshold, t_label) in enumerate(zip(thresholds, threshold_labels)):
    ax = axes[idx]
    
    # Get data for this threshold
    threshold_data = ml_results_class[ml_results_class['Threshold'] == t_label]
    
    # Prepare data for plotting
    models = ['RF', 'XGBoost']
    btc_scores = []
    eth_scores = []
    
    for model in models:
        btc_score = threshold_data[(threshold_data['Pair'] == 'BTC/USDT') & 
                                    (threshold_data['Model'] == model)]['F1_Score'].max()
        eth_score = threshold_data[(threshold_data['Pair'] == 'ETH/USDT') & 
                                    (threshold_data['Model'] == model)]['F1_Score'].max()
        btc_scores.append(btc_score if not pd.isna(btc_score) else 0)
        eth_scores.append(eth_score if not pd.isna(eth_score) else 0)
    
    x = np.arange(len(models))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, btc_scores, width, label='BTC/USDT', 
                   color='#f7931a', alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, eth_scores, width, label='ETH/USDT', 
                   color='#627eea', alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Model', fontsize=11, fontweight='bold')
    ax.set_ylabel('F1 Score', fontsize=11, fontweight='bold')
    ax.set_title(f'Threshold: {t_label}', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10)
    ax.set_ylim([0, 1.0])
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0.01:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('data/figures/fig3_model_comparison.png', bbox_inches='tight')
print("✓ Saved: fig3_model_comparison.png")

# ============================================================================
# FIGURE 4: Profitability Analysis (Win Rates & Net Profit)
# ============================================================================
fig4, (ax4a, ax4b) = plt.subplots(1, 2, figsize=(14, 6))
fig4.suptitle('Economic Analysis: Profitability After 0.2% Transaction Fees', 
              fontsize=14, fontweight='bold')

# Extract win rates and profits
btc_win_rates = []
eth_win_rates = []
btc_profits = []
eth_profits = []

for t_label in threshold_labels:
    btc_row = economic_results[(economic_results['Pair'] == 'BTC/USDT') & 
                                (economic_results['Threshold'] == t_label)]
    eth_row = economic_results[(economic_results['Pair'] == 'ETH/USDT') & 
                                (economic_results['Threshold'] == t_label)]
    
    btc_win_rates.append(float(btc_row['Win_Rate'].values[0].rstrip('%')) if len(btc_row) > 0 else 0)
    eth_win_rates.append(float(eth_row['Win_Rate'].values[0].rstrip('%')) if len(eth_row) > 0 else 0)
    btc_profits.append(float(btc_row['Avg_Net_Profit'].values[0].rstrip('%')) if len(btc_row) > 0 else 0)
    eth_profits.append(float(eth_row['Avg_Net_Profit'].values[0].rstrip('%')) if len(eth_row) > 0 else 0)

# Plot 4a: Win Rates
x = np.arange(len(threshold_labels))
width = 0.35

bars1 = ax4a.bar(x - width/2, btc_win_rates, width, label='BTC/USDT', 
                 color='#f7931a', alpha=0.8, edgecolor='black', linewidth=1.5)
bars2 = ax4a.bar(x + width/2, eth_win_rates, width, label='ETH/USDT', 
                 color='#627eea', alpha=0.8, edgecolor='black', linewidth=1.5)

ax4a.set_xlabel('Threshold', fontsize=12, fontweight='bold')
ax4a.set_ylabel('Win Rate (%)', fontsize=12, fontweight='bold')
ax4a.set_title('(a) Profitable Trade Win Rate', fontsize=12, fontweight='bold')
ax4a.set_xticks(x)
ax4a.set_xticklabels(threshold_labels)
ax4a.axhline(y=50, color='red', linestyle='--', alpha=0.5, linewidth=2, label='50% Breakeven')
ax4a.legend(fontsize=10)
ax4a.grid(axis='y', alpha=0.3)
ax4a.set_ylim([0, 110])

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 1:
            ax4a.text(bar.get_x() + bar.get_width()/2., height + 2,
                     f'{height:.0f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Plot 4b: Average Net Profit
colors_btc = ['red' if x < 0 else 'green' for x in btc_profits]
colors_eth = ['red' if x < 0 else 'green' for x in eth_profits]

bars1 = ax4b.bar(x - width/2, btc_profits, width, label='BTC/USDT', 
                 alpha=0.7, color=colors_btc, edgecolor='black', linewidth=1.5)
bars2 = ax4b.bar(x + width/2, eth_profits, width, label='ETH/USDT', 
                 alpha=0.7, color=colors_eth, edgecolor='black', linewidth=1.5)

ax4b.set_xlabel('Threshold', fontsize=12, fontweight='bold')
ax4b.set_ylabel('Average Net Profit (%)', fontsize=12, fontweight='bold')
ax4b.set_title('(b) Average Net Profit per Trade', fontsize=12, fontweight='bold')
ax4b.set_xticks(x)
ax4b.set_xticklabels(threshold_labels)
ax4b.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=2)
ax4b.legend(fontsize=10)
ax4b.grid(axis='y', alpha=0.3)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if abs(height) > 0.01:
            ax4b.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.3f}%', ha='center', 
                     va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('data/figures/fig4_profitability_analysis.png', bbox_inches='tight')
print("✓ Saved: fig4_profitability_analysis.png")

# ============================================================================
# FIGURE 5: Class Imbalance Visualization
# ============================================================================
fig5, axes = plt.subplots(2, 3, figsize=(15, 8))
fig5.suptitle('Class Distribution Across Thresholds (Imbalance Problem)', 
              fontsize=14, fontweight='bold')

for pair_idx, (pair_name, df) in enumerate([('BTC/USDT', btc), ('ETH/USDT', eth)]):
    for thresh_idx, (threshold, t_label) in enumerate(zip(thresholds, threshold_labels)):
        ax = axes[pair_idx, thresh_idx]
        
        label_col = f'arbitrage_label_{threshold}'
        positive = df[label_col].sum()
        negative = len(df) - positive
        
        # Pie chart
        sizes = [positive, negative]
        colors = ['#ff6b6b', '#51cf66']
        labels = [f'Opportunity\n({positive})', f'No Opportunity\n({negative})']
        explode = (0.1, 0)
        
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                            autopct='%1.2f%%', shadow=True, startangle=90)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        ax.set_title(f'{pair_name} - {t_label}', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('data/figures/fig5_class_imbalance.png', bbox_inches='tight')
print("✓ Saved: fig5_class_imbalance.png")

# ============================================================================
# FIGURE 6: Spread Distribution Histogram
# ============================================================================
fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(14, 6))
fig6.suptitle('Price Spread Distribution Across Exchanges', fontsize=14, fontweight='bold')

spread_cols = ['spread_binance_coinbase', 'spread_binance_kraken', 'spread_binance_cryptocompare']

# BTC spreads
for col in spread_cols:
    spreads = btc[col].dropna().abs()
    ax6a.hist(spreads, bins=50, alpha=0.6, label=col.replace('spread_binance_', '').title(), 
              edgecolor='black')

ax6a.axvline(x=0.1, color='green', linestyle='--', linewidth=2, label='0.1% threshold')
ax6a.axvline(x=0.2, color='orange', linestyle='--', linewidth=2, label='0.2% threshold')
ax6a.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='0.5% threshold')
ax6a.set_xlabel('Absolute Spread (%)', fontsize=12, fontweight='bold')
ax6a.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax6a.set_title('(a) BTC/USDT Spread Distribution', fontsize=12, fontweight='bold')
ax6a.legend(fontsize=9)
ax6a.grid(axis='y', alpha=0.3)
ax6a.set_xlim([0, 1.0])

# ETH spreads
for col in spread_cols:
    spreads = eth[col].dropna().abs()
    ax6b.hist(spreads, bins=50, alpha=0.6, label=col.replace('spread_binance_', '').title(), 
              edgecolor='black')

ax6b.axvline(x=0.1, color='green', linestyle='--', linewidth=2, label='0.1% threshold')
ax6b.axvline(x=0.2, color='orange', linestyle='--', linewidth=2, label='0.2% threshold')
ax6b.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='0.5% threshold')
ax6b.set_xlabel('Absolute Spread (%)', fontsize=12, fontweight='bold')
ax6b.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax6b.set_title('(b) ETH/USDT Spread Distribution', fontsize=12, fontweight='bold')
ax6b.legend(fontsize=9)
ax6b.grid(axis='y', alpha=0.3)
ax6b.set_xlim([0, 1.0])

plt.tight_layout()
plt.savefig('data/figures/fig6_spread_distribution.png', bbox_inches='tight')
print("✓ Saved: fig6_spread_distribution.png")

# ============================================================================
# FIGURE 7: Summary Comparison Table (as image)
# ============================================================================
fig7, ax7 = plt.subplots(figsize=(12, 6))
ax7.axis('tight')
ax7.axis('off')

# Prepare summary data
summary_data = []
for pair in ['BTC/USDT', 'ETH/USDT']:
    for t_label in threshold_labels:
        ml_row = ml_results_class[(ml_results_class['Pair'] == pair) & 
                                   (ml_results_class['Threshold'] == t_label)]
        econ_row = economic_results[(economic_results['Pair'] == pair) & 
                                     (economic_results['Threshold'] == t_label)]
        
        if len(ml_row) > 0 and len(econ_row) > 0:
            best_f1 = ml_row['F1_Score'].max()
            opps = econ_row['Opportunities'].values[0]
            net_profit = econ_row['Avg_Net_Profit'].values[0]
            status = econ_row['Status'].values[0]
            
            summary_data.append([
                pair,
                t_label,
                opps,
                f'{best_f1:.4f}',
                net_profit,
                status
            ])

table = ax7.table(cellText=summary_data,
                  colLabels=['Pair', 'Threshold', 'Opportunities', 'Best F1 Score', 'Avg Net Profit', 'Economic Status'],
                  cellLoc='center',
                  loc='center',
                  colWidths=[0.15, 0.12, 0.15, 0.15, 0.18, 0.18])

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 2.5)

# Color code the cells
for i in range(len(summary_data)):
    # F1 Score coloring
    f1_val = float(summary_data[i][3])
    if f1_val > 0.7:
        table[(i+1, 3)].set_facecolor('#90EE90')  # Light green
    elif f1_val > 0.4:
        table[(i+1, 3)].set_facecolor('#FFFFE0')  # Light yellow
    else:
        table[(i+1, 3)].set_facecolor('#FFB6C1')  # Light pink
    
    # Economic status coloring
    if summary_data[i][5] == 'PROFITABLE':
        table[(i+1, 5)].set_facecolor('#90EE90')
    else:
        table[(i+1, 5)].set_facecolor('#FFB6C1')

# Header styling
for j in range(6):
    table[(0, j)].set_facecolor('#4472C4')
    table[(0, j)].set_text_props(weight='bold', color='white')

ax7.set_title('Summary: ML Performance vs Economic Viability', 
              fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('data/figures/fig7_summary_table.png', bbox_inches='tight')
print("✓ Saved: fig7_summary_table.png")

print("\n" + "="*80)
print("ALL FIGURES GENERATED SUCCESSFULLY!")
print("="*80)
print("\nFigures saved in: data/figures/")
print("\nGenerated figures:")
print("  1. fig1_ml_vs_economic_tradeoff.png - MAIN FIGURE (trade-off)")
print("  2. fig2_opportunity_distribution.png - Opportunities by threshold")
print("  3. fig3_model_comparison.png - RF vs XGBoost performance")
print("  4. fig4_profitability_analysis.png - Win rates & net profit")
print("  5. fig5_class_imbalance.png - Class distribution pie charts")
print("  6. fig6_spread_distribution.png - Spread histograms")
print("  7. fig7_summary_table.png - Complete summary table")
print("\nAll figures are high-resolution (300 DPI) and ready for publication!")
