import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

W, H = 22, 7.6
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis('off')
fig.patch.set_facecolor('white')

BLUE   = '#2980B9'; DKBLUE = '#1A5276'
ORANGE = '#E67E22'; GREEN  = '#27AE60'; DKGRN  = '#1E8449'
RED    = '#C0392B'; PURPLE = '#8E44AD'; DKPUR  = '#7D3C98'
SCARLET= '#E74C3C'; BROWN  = '#D35400'

def rbox(cx, cy, w, h, line1, line2='', fc=BLUE, fs=8.8, zo=4):
    r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle="round,pad=0.04,rounding_size=0.14",
                       facecolor=fc, edgecolor='white', linewidth=1.8, zorder=zo)
    ax.add_patch(r)
    if line2:
        ax.text(cx, cy+0.16, line1, ha='center', va='center',
                fontsize=fs, fontweight='bold', color='white', zorder=zo+1)
        ax.text(cx, cy-0.16, line2, ha='center', va='center',
                fontsize=fs-1.5, color='white', alpha=0.9, zorder=zo+1)
    else:
        ax.text(cx, cy, line1, ha='center', va='center',
                fontsize=fs, fontweight='bold', color='white', zorder=zo+1,
                multialignment='center')

def bgbox(x0, y0, bw, bh, title, fc, bc, zo=1):
    r = FancyBboxPatch((x0, y0), bw, bh,
                       boxstyle="round,pad=0.05,rounding_size=0.2",
                       facecolor=fc, edgecolor=bc, linewidth=1.5,
                       linestyle='--', zorder=zo, alpha=0.45)
    ax.add_patch(r)
    ax.text(x0+bw/2, y0+bh-0.12, title, ha='center', va='top',
            fontsize=7.2, fontweight='bold', color=bc, zorder=zo+1)

def arr(x1, y1, x2, y2, lbl='', lc='#444', lw=1.6, dashed=False, rad=0.0):
    ls = (0, (4, 3)) if dashed else '-'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=lc, lw=lw,
                                linestyle=ls,
                                connectionstyle=f'arc3,rad={rad}'))
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my+0.12, lbl, ha='center', va='bottom',
                fontsize=6.2, color=lc, style='italic', zorder=6)

# ── Y positions ───────────────────────────────────────────────────────────────
TOP = 5.9   # main flow
TMP = 4.5   # template row
OL  = 2.5   # online learning
BH  = 0.76  # box height

# ── Background groups ─────────────────────────────────────────────────────────
bgbox(0.1,  5.0,  2.3, 2.3, 'INPUT SIGNALS',       '#EBF5FB', BLUE)
bgbox(2.6,  5.0,  2.4, 2.3, 'AUDIENCE SELECTION',  '#FEF9E7', ORANGE)
bgbox(5.2,  5.3,  5.7, 2.0, 'LLM GENERATION PATH', '#E8F8F5', GREEN)
bgbox(5.2,  3.9,  5.7, 1.2, 'TEMPLATE PATH',       '#F5EEF8', PURPLE)
bgbox(11.1, 5.0,  5.6, 2.3, 'RANKING & CONTROLS',  '#FDEDEC', SCARLET)
bgbox(16.9, 5.0,  3.1, 2.3, 'DELIVERY & OUTCOMES', '#EAF2FF', DKBLUE)
bgbox(2.6,  1.3, 14.4, 2.2, 'ONLINE LEARNING',     '#FDF2F8', DKPUR)

# ── Input nodes ───────────────────────────────────────────────────────────────
rbox(1.25, TOP+0.5,  2.0, BH, 'User Profile',      'CLV · Lifecycle',   BLUE)
rbox(1.25, TOP,      2.0, BH, 'Content Inventory', 'Items · Posts',     BLUE)
rbox(1.25, TOP-0.5,  2.0, BH, 'Context',           'Time · Location',   BLUE)

# ── Audience selection ────────────────────────────────────────────────────────
rbox(3.8, TOP+0.25, 1.85, BH, 'GNN\nRanker',    '', ORANGE)
rbox(3.8, TOP-0.45, 1.85, BH, 'Budget\nRouter', '', ORANGE)

# ── LLM path ─────────────────────────────────────────────────────────────────
rbox(6.5,  TOP, 1.85, BH, 'RAG Retrieval',  'Context Grounding', GREEN)
rbox(8.45, TOP, 1.85, BH, 'LLM + LoRA',     'Style Control',     DKGRN)
rbox(10.4, TOP, 1.85, BH, 'Policy Guard',   'Factuality Check',  RED)

# ── Template path ─────────────────────────────────────────────────────────────
rbox(7.8, TMP, 2.5, BH, 'Slot-Fill Template Engine', '', PURPLE)

# ── Ranking & controls ────────────────────────────────────────────────────────
rbox(12.2, TOP, 1.85, BH, 'Pairwise\nReward Model',     '', SCARLET)
rbox(14.2, TOP, 1.85, BH, 'Diversity &\nFreq Cap',      '', ORANGE)
rbox(16.2, TOP, 1.85, BH, 'Send-Time\nBandit (UCB/TS)', '', BROWN)

# ── Delivery & outcomes ───────────────────────────────────────────────────────
rbox(18.35, TOP,  1.85, BH, 'Notification\nDelivered',  '', DKBLUE)
rbox(18.35, TMP,  1.85, BH, 'CTR · CVR\nOpt-Out Rate',  '', DKBLUE)

# ── Online learning ───────────────────────────────────────────────────────────
rbox(6.5,  OL, 2.2, BH, 'Counterfactual\nLogger', '', DKPUR)
rbox(10.8, OL, 2.4, BH, 'Model & Index\nUpdate',  '', DKPUR)

# ══════════════════════════════════════════════════════════════════════════════
# ARROWS
# ══════════════════════════════════════════════════════════════════════════════

# Inputs → GNN / Router
arr(2.25, TOP+0.5,  2.88, TOP+0.38)
arr(2.25, TOP,      2.88, TOP+0.1)
arr(2.25, TOP-0.5,  2.88, TOP-0.32)

# GNN → Router
arr(3.8, TOP-0.13, 3.8, TOP-0.07)

# Router → RAG (high-value)
arr(4.73, TOP-0.45, 5.58, TOP, 'High-value', GREEN, rad=-0.22)
# Router → Template (transactional)
arr(4.73, TOP-0.45, 5.55, TMP, 'Transactional', PURPLE, rad=0.18)

# LLM path
arr(7.43, TOP, 7.53, TOP)
arr(9.38, TOP, 9.48, TOP)

# Guard → Reward
arr(11.33, TOP, 11.28, TOP)

# Template → Reward (diagonal, slight curve)
arr(9.05, TMP, 11.28, TOP-0.38, '', '#888', lw=1.4, rad=-0.2)

# Ranking flow
arr(13.13, TOP, 13.28, TOP)
arr(15.13, TOP, 15.28, TOP)
arr(17.13, TOP, 17.43, TOP)

# Delivered → KPI
arr(18.35, TOP-0.38, 18.35, TMP+0.38)

# KPI → Logger: long feedback arc going below everything
arr(17.43, TMP, 7.6, OL+0.38, '', DKPUR, lw=1.5, rad=0.28)

# Logger → Update
arr(7.6, OL, 9.6, OL)

# Update → Reward (dashed feedback)
arr(12.0, OL+0.38, 12.2, TOP-0.38, 'Off-policy Update', DKPUR, dashed=True, rad=-0.18)
# Update → RAG (dashed index refresh)
arr(9.6, OL+0.38, 6.5, TOP-0.38, 'Index Refresh', DKPUR, dashed=True, rad=0.18)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(W/2, 7.35, 'Unified LLM-Based Notification Pipeline',
        ha='center', va='center', fontsize=13.5, fontweight='bold', color='#1a3a5c')

plt.savefig('/home/ubuntu/acm_paper/paper/fig2_pipeline.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print("Done.")
