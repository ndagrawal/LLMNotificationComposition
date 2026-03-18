import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H = 20, 8.5
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis('off')
fig.patch.set_facecolor('white')

# Colors
TIER1_HDR = '#1A5276'   # dark blue  — Primary Outcome
TIER2_HDR = '#6C3483'   # purple     — Guardrail
TIER3_HDR = '#1E8449'   # green      — Long-horizon
TIER4_HDR = '#784212'   # brown      — Threats

TIER1_BG  = '#D6EAF8'
TIER2_BG  = '#E8DAEF'
TIER3_BG  = '#D5F5E3'
TIER4_BG  = '#FAE5D3'

ARROW_C   = '#555555'

def rbox(cx, cy, w, h, text, fc, ec, fs=9.5, bold=False, zo=3):
    r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle="round,pad=0.06,rounding_size=0.14",
                       facecolor=fc, edgecolor=ec, linewidth=1.6, zorder=zo)
    ax.add_patch(r)
    fw = 'bold' if bold else 'normal'
    ax.text(cx, cy, text, ha='center', va='center',
            fontsize=fs, fontweight=fw, color='#1C1C1C',
            zorder=zo+1, multialignment='center', linespacing=1.4)

def header(cx, cy, w, h, text, fc, fs=11, zo=4):
    r = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle="round,pad=0.06,rounding_size=0.14",
                       facecolor=fc, edgecolor='white', linewidth=2, zorder=zo)
    ax.add_patch(r)
    ax.text(cx, cy, text, ha='center', va='center',
            fontsize=fs, fontweight='bold', color='white',
            zorder=zo+1, multialignment='center')

def arr(x1, y1, x2, y2, lc=ARROW_C, lw=1.5, dashed=False):
    ls = (0, (5, 3)) if dashed else 'solid'
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=lc, lw=lw,
                                linestyle=ls,
                                connectionstyle='arc3,rad=0.0'))

def bracket_label(x, y1, y2, label, color):
    ax.annotate('', xy=(x, y1), xytext=(x, y2),
                arrowprops=dict(arrowstyle='<->', color=color, lw=1.5))
    ax.text(x - 0.25, (y1+y2)/2, label, ha='right', va='center',
            fontsize=8, color=color, fontweight='bold', rotation=90)

# ── Layout: 4 tiers arranged as horizontal rows ───────────────────────────────
# Each tier: header on left, then 3-4 metric boxes flowing right
# Tier Y positions (center of each row)
T1Y = 7.0
T2Y = 5.35
T3Y = 3.7
T4Y = 2.05

ROW_H = 0.85  # metric box height
HDR_W = 3.0   # header width
BOX_W = 3.4   # metric box width
GAP   = 0.25  # gap between boxes
LEFT  = 0.2   # left margin

# ── Tier 1: Primary Outcome Metrics ──────────────────────────────────────────
header(LEFT + HDR_W/2, T1Y, HDR_W, ROW_H + 0.1,
       'TIER 1\nPrimary Outcome Metrics', TIER1_HDR)

t1_metrics = [
    'Click-Through Rate (CTR)\nShort-term engagement signal',
    'Conversion Rate (CVR)\nPurchase / order completion',
    'Revenue per Notification\nDirect business value',
    'Session Re-entry Rate\nApp re-engagement depth',
]
x = LEFT + HDR_W + GAP
for m in t1_metrics:
    rbox(x + BOX_W/2, T1Y, BOX_W, ROW_H, m, TIER1_BG, TIER1_HDR, fs=8.8)
    x += BOX_W + GAP

# ── Tier 2: Guardrail Metrics ─────────────────────────────────────────────────
header(LEFT + HDR_W/2, T2Y, HDR_W, ROW_H + 0.1,
       'TIER 2\nGuardrail Metrics', TIER2_HDR)

t2_metrics = [
    'Notification Opt-Out Rate\nUser tolerance signal',
    'Mute / Block Actions\nFatigue & annoyance proxy',
    'Complaint Rate\nNegative feedback signal',
    'Uninstall Risk Score\nExtreme dissatisfaction',
]
x = LEFT + HDR_W + GAP
for m in t2_metrics:
    rbox(x + BOX_W/2, T2Y, BOX_W, ROW_H, m, TIER2_BG, TIER2_HDR, fs=8.8)
    x += BOX_W + GAP

# ── Tier 3: Long-Horizon Health Metrics ───────────────────────────────────────
header(LEFT + HDR_W/2, T3Y, HDR_W, ROW_H + 0.1,
       'TIER 3\nLong-Horizon Health', TIER3_HDR)

t3_metrics = [
    '7-Day Retention Rate\nShort-term cohort health',
    '30-Day Retention Rate\nMedium-term durability',
    'Notification Fatigue Curve\nEngagement decay over time',
    'Reactivation Durability\nChurn recovery persistence',
]
x = LEFT + HDR_W + GAP
for m in t3_metrics:
    rbox(x + BOX_W/2, T3Y, BOX_W, ROW_H, m, TIER3_BG, TIER3_HDR, fs=8.8)
    x += BOX_W + GAP

# ── Tier 4: Threats to Validity ───────────────────────────────────────────────
header(LEFT + HDR_W/2, T4Y, HDR_W, ROW_H + 0.1,
       'TIER 4\nThreats to Validity', TIER4_HDR)

t4_metrics = [
    'SUTVA Violations\nNetwork interference effects',
    'Exposure Bias\nReward model confounding',
    'Temporal Degradation\nModel staleness over time',
    'Publication Bias\nSelective reporting of lifts',
]
x = LEFT + HDR_W + GAP
for m in t4_metrics:
    rbox(x + BOX_W/2, T4Y, BOX_W, ROW_H, m, TIER4_BG, TIER4_HDR, fs=8.8)
    x += BOX_W + GAP

# ── Vertical arrows between tiers ─────────────────────────────────────────────
mid_x = LEFT + HDR_W/2
arr(mid_x, T1Y - ROW_H/2 - 0.05, mid_x, T2Y + ROW_H/2 + 0.05, TIER1_HDR)
arr(mid_x, T2Y - ROW_H/2 - 0.05, mid_x, T3Y + ROW_H/2 + 0.05, TIER2_HDR)
arr(mid_x, T3Y - ROW_H/2 - 0.05, mid_x, T4Y + ROW_H/2 + 0.05, TIER3_HDR)

# ── Annotation: Multi-objective trade-off note ────────────────────────────────
note_x = LEFT + HDR_W + (4 * (BOX_W + GAP)) + 0.3
ax.text(note_x, (T1Y + T2Y)/2, 'Optimize\nTier 1\nsubject to\nTier 2\nguardrails',
        ha='left', va='center', fontsize=8, color='#555', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDFEFE',
                  edgecolor='#AAAAAA', linewidth=0.8))

ax.text(note_x, (T2Y + T3Y)/2, 'Monitor\nTier 3 for\nlong-run\nuser trust',
        ha='left', va='center', fontsize=8, color='#555', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDFEFE',
                  edgecolor='#AAAAAA', linewidth=0.8))

ax.text(note_x, (T3Y + T4Y)/2, 'Acknowledge\nTier 4\nwhen\nreporting',
        ha='left', va='center', fontsize=8, color='#555', style='italic',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#FDFEFE',
                  edgecolor='#AAAAAA', linewidth=0.8))

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(W/2, 8.2, 'Multi-Layer Evaluation Framework for LLM-Based Notification Systems',
        ha='center', va='center', fontsize=13.5, fontweight='bold', color='#1a3a5c')

plt.savefig('/home/ubuntu/acm_paper/paper/fig4_evaluation.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 4 saved.")
