import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 20, 11.5
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Colors ────────────────────────────────────────────────────────────────────
# Domain header colors
COL_SM  = '#2980B9'   # Social Media  — blue
COL_FD  = '#E67E22'   # Food Delivery — orange
COL_EC  = '#27AE60'   # E-Commerce    — green

# Row label color
COL_ROW = '#4A4A4A'

# Cell background alternating
BG_EVEN = '#F8F9FA'
BG_ODD  = '#FFFFFF'

# Row accent colors (left bar)
ROW_COLORS = ['#2980B9', '#E74C3C', '#8E44AD', '#27AE60', '#E67E22', '#1A5276', '#7D3C98']

# ── Layout constants ──────────────────────────────────────────────────────────
LEFT_W   = 3.2    # row label column width
COL_W    = (W - LEFT_W - 0.3) / 3   # each domain column width
ROW_H    = 1.35   # row height
HEADER_H = 0.95   # header row height
TOP_Y    = H - 0.5  # top of table

# Column x-starts
X0 = 0.15                       # row label start
X1 = X0 + LEFT_W               # Social Media start
X2 = X1 + COL_W                # Food Delivery start
X3 = X2 + COL_W                # E-Commerce start

# ── Row definitions ───────────────────────────────────────────────────────────
rows = [
    {
        'label': '"High-Value"\nUser Definition',
        'sm':    'High-DAU user with\nstrong social graph;\ninfluencer or power user',
        'fd':    'Repeat orderer with\nhigh AOV; lapsed user\nwith reactivation potential',
        'ec':    'High-CLV customer;\nabandoned-cart user\nwith purchase intent',
    },
    {
        'label': 'Primary\nSuccess Metric',
        'sm':    'Engagement Rate\n(likes, shares, comments)\nSession re-entry',
        'fd':    'Order Conversion Rate\nGMV per notification\nReactivation rate',
        'ec':    'Click-to-Purchase CVR\nRevenue per notification\nCart recovery rate',
    },
    {
        'label': 'Key Contextual\nSignals',
        'sm':    'Social activity feed\nFriend/follower events\nContent freshness',
        'fd':    'Time of day (meal windows)\nOrder history & recency\nLocation & weather',
        'ec':    'Browse & cart history\nPrice drop / stock alerts\nSeasonal promotions',
    },
    {
        'label': 'LLM Role\nin Pipeline',
        'sm':    'Personalise social\nrecap & trending content\nsummaries',
        'fd':    'Generate contextual\nurgency copy\n(e.g., lunch offers)',
        'ec':    'Produce persuasive\nproduct descriptions\n& recovery messages',
    },
    {
        'label': 'Persuasion\nTolerance',
        'sm':    'Moderate — users\nexpect social updates,\nnot hard selling',
        'fd':    'High during meal\nwindows; low outside\npeak hours',
        'ec':    'High for deal/discount\nframes; low for\ngeneric promotions',
    },
    {
        'label': 'Dominant\nFailure Mode',
        'sm':    'Notification fatigue\nfrom over-frequency;\ntone mismatch',
        'fd':    'False urgency\n(dark pattern risk);\nstale context',
        'ec':    'Hallucinated prices\nor stock levels;\nreward hacking',
    },
    {
        'label': 'Cross-Domain\nTransferability',
        'sm':    'GNN audience\nselection transfers;\nLLM copy style\ndoes not',
        'fd':    'STO bandit transfers;\nurgency framing\nis domain-specific',
        'ec':    'RAG grounding\ntransfers; CLV\nsegmentation\ntransfers broadly',
    },
]

# ── Draw header ───────────────────────────────────────────────────────────────
def header_cell(x, y, w, h, text, fc, icon=''):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.04,rounding_size=0.12",
                          facecolor=fc, edgecolor='white', linewidth=2, zorder=3)
    ax.add_patch(rect)
    full = f'{icon}  {text}' if icon else text
    ax.text(x + w/2, y + h/2, full, ha='center', va='center',
            fontsize=12, fontweight='bold', color='white', zorder=4,
            multialignment='center')

# Row label column header
rect = FancyBboxPatch((X0, TOP_Y - HEADER_H), LEFT_W - 0.1, HEADER_H,
                      boxstyle="round,pad=0.04,rounding_size=0.12",
                      facecolor='#2C3E50', edgecolor='white', linewidth=2, zorder=3)
ax.add_patch(rect)
ax.text(X0 + (LEFT_W-0.1)/2, TOP_Y - HEADER_H/2, 'Dimension',
        ha='center', va='center', fontsize=12, fontweight='bold',
        color='white', zorder=4)

header_cell(X1, TOP_Y - HEADER_H, COL_W - 0.1, HEADER_H, 'Social Media',    COL_SM,  '📱')
header_cell(X2, TOP_Y - HEADER_H, COL_W - 0.1, HEADER_H, 'Food Delivery',   COL_FD,  '🍔')
header_cell(X3, TOP_Y - HEADER_H, COL_W - 0.1, HEADER_H, 'E-Commerce',      COL_EC,  '🛒')

# ── Draw rows ─────────────────────────────────────────────────────────────────
def cell(x, y, w, h, text, bg, border_color=None, fs=9.5):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.04,rounding_size=0.08",
                          facecolor=bg, edgecolor='#DDDDDD', linewidth=0.8, zorder=2)
    ax.add_patch(rect)
    if border_color:
        # left accent bar
        bar = FancyBboxPatch((x, y), 0.12, h,
                             boxstyle="square,pad=0",
                             facecolor=border_color, edgecolor='none', zorder=3)
        ax.add_patch(bar)
    ax.text(x + w/2 + (0.06 if border_color else 0), y + h/2, text,
            ha='center', va='center', fontsize=fs, color='#2C3E50',
            zorder=4, multialignment='center', linespacing=1.4)

for i, row in enumerate(rows):
    y = TOP_Y - HEADER_H - (i + 1) * ROW_H
    bg = BG_EVEN if i % 2 == 0 else BG_ODD
    rc = ROW_COLORS[i % len(ROW_COLORS)]

    # Row label
    cell(X0, y, LEFT_W - 0.1, ROW_H - 0.08, row['label'], '#ECF0F1',
         border_color=rc, fs=9.5)

    # Domain cells
    cell(X1, y, COL_W - 0.1, ROW_H - 0.08, row['sm'], bg, fs=9.2)
    cell(X2, y, COL_W - 0.1, ROW_H - 0.08, row['fd'], bg, fs=9.2)
    cell(X3, y, COL_W - 0.1, ROW_H - 0.08, row['ec'], bg, fs=9.2)

    # Subtle horizontal divider
    ax.axhline(y + ROW_H - 0.04, color='#CCCCCC', lw=0.5, zorder=1,
               xmin=X0/W, xmax=(W-0.15)/W)

# ── Outer border ──────────────────────────────────────────────────────────────
table_h = HEADER_H + len(rows) * ROW_H
rect = FancyBboxPatch((X0, TOP_Y - table_h), W - X0 - 0.15, table_h,
                      boxstyle="round,pad=0.04,rounding_size=0.15",
                      facecolor='none', edgecolor='#AAAAAA', linewidth=1.5, zorder=5)
ax.add_patch(rect)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(W/2, H - 0.22, 'Domain Generalizability Matrix',
        ha='center', va='top', fontsize=14, fontweight='bold', color='#1a3a5c')

# ── Legend ────────────────────────────────────────────────────────────────────
legend_y = TOP_Y - table_h - 0.35
ax.text(W/2, legend_y,
        'Shaded left bars indicate row dimension category. '
        'Green cells = transferable across domains. '
        'White cells = domain-specific.',
        ha='center', va='top', fontsize=8, color='#666666', style='italic')

plt.savefig('/home/ubuntu/acm_paper/paper/fig3_domain.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 3 saved.")
