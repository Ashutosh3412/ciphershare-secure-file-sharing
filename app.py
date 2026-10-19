from pathlib import Path
import hashlib
import streamlit as st
from cryptography.hazmat.primitives import serialization

from crypto_utils import (
    generate_rsa_key_pair,
    encrypt_file_aes,
    decrypt_file_aes,
    create_secure_package,
    decrypt_secure_package,
    tamper_package_ciphertext,
)

st.set_page_config(
    page_title="CipherShare — Secure File Sharing with Hybrid Cryptography",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Design system: restrained navy, soft slate, one blue accent, strong hierarchy.
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
      --bg: #0a0f17;
      --sidebar: #0c121c;
      --panel: #111a27;
      --panel-raised: #151f2e;
      --panel-soft: #0e1622;
      --line: #263448;
      --line-soft: rgba(140, 163, 192, .16);
      --text: #edf3fb;
      --muted: #98a9bf;
      --muted-2: #6f829c;
      --blue: #78a9ff;
      --blue-strong: #4c88f5;
      --teal: #5bd7c4;
      --green: #66d6a5;
      --amber: #e5bb75;
      --red: #f28c98;
    }
    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .stApp {
      background:
        radial-gradient(ellipse at 18% -14%, rgba(76,136,245,.14), transparent 32%),
        radial-gradient(ellipse at 98% 2%, rgba(91,215,196,.07), transparent 25%),
        var(--bg);
      color: var(--text);
    }
    [data-testid="stHeader"] { background: rgba(10,15,23,.84); }
    [data-testid="stAppViewContainer"] .main .block-container {
      max-width: 1380px;
      padding-top: 1.45rem;
      padding-bottom: 3.25rem;
    }
    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #0c121c 0%, #0a1019 100%);
      border-right: 1px solid #1d2a3b;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #aab9cc; }
    [data-testid="stSidebar"] hr { border-color: #1f2c3e; margin: 1.1rem 0; }
    h1, h2, h3, h4 { color: var(--text) !important; letter-spacing: -.035em; }
    h1 { font-weight: 750 !important; }
    h2 { font-size: 1.55rem !important; font-weight: 720 !important; }
    h3 { font-size: 1.12rem !important; font-weight: 700 !important; }
    p, li, label { color: #d0d9e7; }
    [data-testid="stMarkdownContainer"] p { line-height: 1.62; }
    .brand-row { display:flex; align-items:center; gap:12px; margin: 0 0 4px 0; }
    .brand-mark {
      width: 42px; height: 42px; display:flex; align-items:center; justify-content:center;
      border-radius: 13px; color:#07111f; font-size: 1.02rem; font-weight: 900;
      background: linear-gradient(135deg, #8fb8ff 0%, #5bd7c4 100%);
      box-shadow: 0 7px 24px rgba(76,136,245,.18);
    }
    .brand-name { color:#f0f5fd; font-size:1.14rem; font-weight:850; letter-spacing:-.035em; line-height:1.1; }
    .brand-sub { color:#8194ad; font-size:.74rem; margin-top:4px; letter-spacing:.02em; }
    .side-label { color:#697e99; font-size:.68rem; font-weight:800; letter-spacing:.15em; text-transform:uppercase; margin: 1.45rem 0 .55rem; }
    .side-stack { border:1px solid #202e41; border-radius:14px; padding:12px 13px; background:rgba(17,26,39,.72); }
    .side-stack-row { display:flex; align-items:center; justify-content:space-between; gap:8px; margin:7px 0; color:#c8d4e4; font-size:.79rem; }
    .small-dot { width:7px;height:7px;display:inline-block;border-radius:50%;background:var(--teal);margin-right:7px;box-shadow:0 0 0 3px rgba(91,215,196,.08); }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 5px; }
    [data-testid="stSidebar"] [role="radiogroup"] > label {
      border: 1px solid transparent; border-radius: 10px; padding: 9px 11px;
      margin: 0; color: #a8b7ca; background: transparent; transition: .15s ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label:hover { background:#121d2b; border-color:#23344a; color:#eef5ff; }
    [data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
      background: linear-gradient(90deg, rgba(76,136,245,.19), rgba(76,136,245,.07));
      border-color: rgba(120,169,255,.32); color:#f2f7ff;
    }
    [data-testid="stSidebar"] [role="radiogroup"] > label p { font-size:.87rem; font-weight:650; }
    .topline { display:flex; justify-content:space-between; align-items:center; gap:12px; margin:0 0 13px; }
    .topline-left { color:#8ea1ba; font-size:.75rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
    .topline-right { display:flex; align-items:center; gap:8px; color:#a9b9cc; font-size:.76rem; }
    .status-pill { display:inline-flex; align-items:center; gap:7px; border:1px solid #294154; background:rgba(16,31,42,.7); border-radius:999px; padding:6px 10px; color:#c6e8e3; font-weight:650; }
    .hero {
      position:relative; overflow:hidden; border:1px solid rgba(120,169,255,.24); border-radius:22px;
      background:linear-gradient(112deg, rgba(20,34,54,.98) 0%, rgba(16,29,44,.97) 57%, rgba(13,37,42,.96) 100%);
      padding: clamp(23px, 3.4vw, 38px); box-shadow:0 18px 55px rgba(0,0,0,.16); margin-bottom:22px;
    }
    .hero:before { content:""; position:absolute; width:360px;height:360px; right:-160px;top:-200px;border-radius:50%;border:1px solid rgba(91,215,196,.21);box-shadow:0 0 0 30px rgba(91,215,196,.025),0 0 0 66px rgba(120,169,255,.024);pointer-events:none; }
    .eyebrow { color:var(--teal); font-weight:850; font-size:.7rem; letter-spacing:.16em; text-transform:uppercase; margin-bottom:13px; }
    .hero-title { color:#f4f7fc; font-size:clamp(2rem,4vw,3.2rem); line-height:1.07; font-weight:820; letter-spacing:-.06em; margin:0 0 14px; max-width:740px; }
    .hero-copy { color:#bdccdf; font-size:.99rem; line-height:1.72; max-width:720px; margin:0; }
    .hero-tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:20px; }
    .hero-tag { color:#d6e6f9; background:rgba(9,17,29,.44); border:1px solid rgba(145,174,213,.24); padding:6px 10px; border-radius:8px; font-size:.73rem; font-weight:650; }
    .pipeline { position:relative; z-index:1; border:1px solid rgba(133,169,208,.23); background:rgba(8,16,26,.48); border-radius:17px; padding:19px; height:100%; }
    .pipeline-title { color:#8ea2bc; font-size:.68rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin-bottom:14px; }
    .pipeline-row { display:flex; align-items:center; gap:11px; padding:12px 0; border-bottom:1px solid rgba(135,159,188,.13); }
    .pipeline-row:last-child { border-bottom:0; padding-bottom:0; }
    .pipeline-icon { flex:0 0 35px; width:35px; height:35px; border:1px solid #34475f; border-radius:11px; display:flex; align-items:center; justify-content:center; color:#9fc0ff; background:#142237; font-size:.86rem; font-weight:850; }
    .pipeline-main { color:#eaf1fb; font-size:.83rem; font-weight:750; }
    .pipeline-sub { color:#8094af; font-size:.72rem; margin-top:3px; }
    .section-kicker { color:var(--teal); font-size:.7rem; font-weight:850; text-transform:uppercase; letter-spacing:.15em; margin:3px 0 6px; }
    .section-desc { color:var(--muted) !important; margin-top:-2px; margin-bottom:18px; max-width:850px; font-size:.91rem; }
    .metric-card { min-height:118px; padding:17px 18px; border:1px solid var(--line); border-radius:15px; background:linear-gradient(145deg, rgba(18,28,42,.98), rgba(14,22,34,.98)); }
    .metric-top { display:flex; align-items:center; justify-content:space-between; gap:8px; color:#91a3bc; font-size:.71rem; font-weight:750; text-transform:uppercase; letter-spacing:.08em; }
    .metric-icon { border:1px solid #2d4059; background:#15243a; color:#9fc0ff; border-radius:9px; padding:5px 8px; font-size:.75rem; }
    .metric-value { margin-top:12px; color:#edf4ff; font-size:1.28rem; font-weight:820; letter-spacing:-.035em; }
    .metric-note { margin-top:4px; color:#8194ad; font-size:.79rem; line-height:1.45; }
    .workflow-card { height:100%; border:1px solid var(--line); border-radius:15px; padding:17px; background:rgba(15,24,37,.82); }
    .workflow-no { display:flex;align-items:center;justify-content:center;width:31px;height:31px;border:1px solid #365274;border-radius:9px;background:#152943;color:#a9c8ff;font-size:.78rem;font-weight:850;margin-bottom:13px; }
    .workflow-title { color:#eaf1fb; font-weight:760; font-size:.93rem; margin-bottom:6px; }
    .workflow-copy { color:#94a6bd; font-size:.81rem; line-height:1.56; }
    .panel-heading { display:flex; align-items:center; gap:10px; margin-bottom:5px; }
    .panel-number { flex:0 0 30px; width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#182b44;color:#9fc0ff;font-size:.75rem;font-weight:850;border:1px solid #2e4563; }
    .file-note { color:#90a2ba; font-size:.8rem; line-height:1.55; }
    .callout { display:flex; gap:11px; border:1px solid #2a4155; background:rgba(15,37,47,.6); border-radius:12px; padding:13px 14px; color:#c8e8e4; font-size:.82rem; line-height:1.55; }
    .callout-symbol { color:var(--teal); font-weight:900; }
    .result-card { border:1px solid #2a4f47; background:linear-gradient(120deg,rgba(17,48,43,.7),rgba(15,31,37,.72)); border-radius:13px; padding:15px 16px; }
    .result-title { color:#a7f1d1; font-size:.88rem; font-weight:800; }
    .result-copy { color:#a6bdb9; font-size:.8rem; line-height:1.5; margin-top:5px; }
    .muted-box { border:1px solid var(--line); background:rgba(16,25,38,.8); border-radius:13px; padding:14px 15px; }
    .muted-box-title { color:#e5edf9; font-size:.84rem; font-weight:750; margin-bottom:5px; }
    .muted-box-copy { color:#8fa1b8; font-size:.79rem; line-height:1.5; }
    .stButton > button, .stDownloadButton > button {
      border-radius:10px; min-height:42px; padding:.55rem 1rem; font-weight:750;
      border:1px solid #354b66; color:#edf4ff; background:linear-gradient(135deg,#1b2c43,#172639);
      transition:background .15s ease,border-color .15s ease,transform .15s ease;
    }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
      background:linear-gradient(135deg,#4c88f5,#3975dc); color:#fff; border:1px solid #6da0ff;
      box-shadow:0 8px 22px rgba(60,115,220,.18);
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:#76a9ff; color:#fff; transform:translateY(-1px); }
    .stButton > button:disabled { background:#121b28; border-color:#253449; color:#64768e; transform:none; box-shadow:none; }
    .stTextInput input, .stTextArea textarea { background:#0c1420 !important; color:var(--text) !important; border:1px solid #2b3d53 !important; border-radius:10px !important; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color:#6e9df1 !important; box-shadow:0 0 0 1px #6e9df1 !important; }
    [data-testid="stFileUploader"] section { background:#0d1623; border:1px dashed #3b526e; border-radius:13px; padding:14px; }
    [data-testid="stFileUploader"] section:hover { border-color:#77a8ff; background:#101d2c; }
    [data-testid="stFileUploader"] small { color:#8da1bb !important; }
    [data-testid="stAlert"] { border-radius:12px; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color:#27374b !important; border-radius:15px !important; background:rgba(15,23,35,.60); }
    [data-baseweb="tab-list"] { gap:5px; }
    .stProgress > div > div > div > div { background:var(--teal); }
    div[data-testid="stMetric"] { background:rgba(18,28,42,.9); border:1px solid #26374c; border-radius:13px; padding:13px 15px; }
    div[data-testid="stMetricLabel"] { color:#8fa3bb; }
    div[data-testid="stMetricValue"] { color:#edf4ff; }
    hr { border-color:#243247; margin:1.4rem 0; }
    code { color:#a7eddf; background:#0a1522; border-radius:5px; }
    .footer { color:#687d97; font-size:.74rem; padding:24px 0 4px; text-align:center; border-top:1px solid #1c293b; margin-top:32px; }

    /* Motion system: restrained entrance, progress movement, and hover feedback. */
    @keyframes csPageEnter {
      from { opacity: 0; transform: translate3d(0, 11px, 0); filter: blur(2px); }
      to   { opacity: 1; transform: translate3d(0, 0, 0); filter: blur(0); }
    }
    @keyframes csSoftPulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(91,215,196,0); }
      50% { box-shadow: 0 0 0 6px rgba(91,215,196,.055); }
    }
    @keyframes csScan {
      0% { transform: translateX(-120%); opacity: 0; }
      18% { opacity: .7; }
      65% { opacity: .18; }
      100% { transform: translateX(240%); opacity: 0; }
    }
    @keyframes csLineIn {
      from { width: 0; }
      to { width: var(--progress-width); }
    }
    [data-testid="stAppViewBlockContainer"] { animation: csPageEnter .48s cubic-bezier(.2,.7,.2,1) both; }
    .hero { isolation:isolate; }
    .hero:after {
      content:""; position:absolute; z-index:-1; left:0; top:0; bottom:0; width:28%;
      background:linear-gradient(100deg,transparent,rgba(132,183,255,.075),transparent);
      transform:translateX(-120%); animation:csScan 2.1s .25s ease-out 1 both; pointer-events:none;
    }
    .metric-card, .workflow-card, .muted-box, .result-card, .side-stack {
      transition:transform .22s ease,border-color .22s ease,background .22s ease,box-shadow .22s ease;
    }
    .metric-card:hover, .workflow-card:hover, .muted-box:hover, .result-card:hover {
      transform:translateY(-3px); border-color:rgba(120,169,255,.42);
      box-shadow:0 12px 32px rgba(0,0,0,.17);
    }
    .workflow-card:hover .workflow-no { animation:csSoftPulse 1.2s ease-in-out infinite; }
    .stButton > button, .stDownloadButton > button, [data-testid="stSidebar"] [role="radiogroup"] > label {
      transition:transform .18s ease,border-color .18s ease,background .18s ease,box-shadow .18s ease,color .18s ease;
    }
    .stButton > button:active, .stDownloadButton > button:active { transform:scale(.985); }
    .step-guide {
      position:relative; overflow:hidden; border:1px solid rgba(120,169,255,.25); border-radius:16px;
      background:linear-gradient(112deg,rgba(19,34,54,.9),rgba(14,28,42,.9));
      padding:17px 19px; margin: 15px 0 22px; animation:csPageEnter .46s .06s both;
    }
    .step-guide:after {
      content:""; position:absolute; top:0; bottom:0; right:0; width:4px;
      background:linear-gradient(180deg,var(--blue),var(--teal)); opacity:.9;
    }
    .guide-head {display:flex;align-items:center;gap:12px;margin-bottom:14px;}
    .guide-icon {display:flex;align-items:center;justify-content:center;flex:0 0 38px;width:38px;height:38px;border-radius:12px;background:#172b45;border:1px solid #385578;color:#a6c6ff;font-size:1.02rem;font-weight:900;}
    .guide-eyebrow {color:var(--teal);font-size:.66rem;font-weight:850;letter-spacing:.14em;text-transform:uppercase;margin-bottom:3px;}
    .guide-title {color:#f0f5fc;font-size:1.02rem;font-weight:800;letter-spacing:-.025em;}
    .guide-step {margin-left:auto;border:1px solid #2f4762;background:#101e2e;padding:5px 9px;border-radius:8px;color:#9fb5d0;font-size:.68rem;font-weight:800;white-space:nowrap;}
    .guide-grid {display:grid;grid-template-columns:1fr 1fr;gap:12px;}
    .guide-cell {border:1px solid rgba(136,162,195,.15);background:rgba(7,15,26,.28);border-radius:10px;padding:11px 12px;}
    .guide-label {font-size:.65rem;color:#82a0c1;text-transform:uppercase;letter-spacing:.12em;font-weight:850;margin-bottom:5px;}
    .guide-copy {font-size:.8rem;line-height:1.55;color:#c1d0e2;}
    .wizard-shell {border:1px solid #24354a;background:rgba(12,20,31,.82);border-radius:16px;padding:16px 17px 12px;margin:4px 0 24px;animation:csPageEnter .42s both;}
    .wizard-top {display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px;}
    .wizard-label {color:#c8d7e9;font-size:.75rem;font-weight:800;letter-spacing:.06em;}
    .wizard-caption {color:#7f94ae;font-size:.72rem;}
    .wizard-rail {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;position:relative;}
    .wizard-node {position:relative;min-width:0;text-align:center;}
    .wizard-node-circle {width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:11px;margin:0 auto 8px;border:1px solid #334860;background:#111d2c;color:#7f93ad;font-weight:850;font-size:.77rem;position:relative;z-index:2;transition:all .28s ease;}
    .wizard-node.is-current .wizard-node-circle {background:linear-gradient(135deg,#4c88f5,#2866c9);border-color:#8bb4ff;color:white;box-shadow:0 0 0 5px rgba(76,136,245,.12),0 8px 22px rgba(54,112,220,.2);transform:translateY(-2px);}
    .wizard-node.is-done .wizard-node-circle {background:#15342f;border-color:#347d70;color:#8ce3d2;}
    .wizard-node-label {color:#a0b0c4;font-size:.7rem;font-weight:700;line-height:1.25;overflow-wrap:anywhere;}
    .wizard-node.is-current .wizard-node-label {color:#f1f6ff;}
    .wizard-node.is-done .wizard-node-label {color:#a9d8cf;}
    .wizard-node-status {color:#647b97;font-size:.62rem;margin-top:4px;}
    .wizard-node.is-current .wizard-node-status {color:#91b8ff;}
    .wizard-node.is-done .wizard-node-status {color:#72cdbb;}
    .wizard-progress-track {height:3px;background:#1d2c40;border-radius:99px;overflow:hidden;margin:0 6% 14px;}
    .wizard-progress-fill {height:100%;width:var(--progress-width);background:linear-gradient(90deg,#4c88f5,#5bd7c4);border-radius:99px;transition:width .6s cubic-bezier(.2,.75,.2,1);box-shadow:0 0 12px rgba(91,215,196,.2);}
    .step-nav-row {display:flex;justify-content:space-between;gap:12px;align-items:center;margin-top:24px;padding-top:18px;border-top:1px solid #202e40;}
    .step-nav-hint {color:#7389a4;font-size:.75rem;line-height:1.5;}
    .overview-start {
      border:1px solid rgba(91,215,196,.26);border-radius:14px;padding:15px 17px;
      background:linear-gradient(105deg,rgba(20,53,53,.5),rgba(15,28,43,.72));margin-top:18px;
    }
    .overview-start-title {color:#e6f9f5;font-weight:800;font-size:.91rem;margin-bottom:4px;}
    .overview-start-copy {color:#9ebdbb;font-size:.8rem;line-height:1.55;}
    .security-test-card {border:1px solid #293d54;border-radius:14px;background:rgba(14,23,36,.74);padding:16px;}
    @media (max-width: 800px) {
      .guide-grid {grid-template-columns:1fr;}
      .guide-step {display:none;}
      .wizard-node-label {font-size:.62rem;}
      .wizard-node-circle {width:30px;height:30px;border-radius:9px;}
      .step-nav-row {align-items:stretch;flex-direction:column;}
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {animation-duration:.01ms !important;animation-iteration-count:1 !important;scroll-behavior:auto !important;transition-duration:.01ms !important;}
    }

    @media (max-width: 800px) {
      [data-testid="stAppViewContainer"] .main .block-container { padding-top:1rem; }
      .hero-title { font-size:2.1rem; }
      .topline { align-items:flex-start; flex-direction:column; }
    }
    

    /* Project presentation layer + per-step animated protocol diagrams. */
    @keyframes csAuroraDrift {
      0%,100% { transform: translate3d(0,0,0) scale(1); }
      50% { transform: translate3d(-18px,12px,0) scale(1.05); }
    }
    @keyframes csRailShimmer {
      0% { transform:translateX(-140%); opacity:0; }
      20% { opacity:.9; }
      70% { opacity:.35; }
      100% { transform:translateX(430%); opacity:0; }
    }
    @keyframes csNodeArrive {
      0% { opacity:0; transform:translateY(13px) scale(.97); filter:blur(3px); }
      72% { opacity:1; transform:translateY(-2px) scale(1.005); filter:blur(0); }
      100% { opacity:1; transform:translateY(0) scale(1); filter:blur(0); }
    }
    @keyframes csGlyphGlow {
      0%,100% { box-shadow:0 0 0 0 rgba(91,215,196,0), 0 0 0 rgba(91,215,196,0); }
      50% { box-shadow:0 0 0 5px rgba(91,215,196,.08), 0 0 22px rgba(91,215,196,.13); }
    }
    @keyframes csFlowPacket {
      0% { left:0%; opacity:0; }
      12% { opacity:1; }
      88% { opacity:1; }
      100% { left:100%; opacity:0; }
    }
    @keyframes csHeroAura {
      0%,100% { transform:translate3d(0,0,0); opacity:.62; }
      50% { transform:translate3d(-22px,15px,0); opacity:1; }
    }
    @keyframes csStepProgressGlow {
      0% { transform:translateX(-140%); }
      100% { transform:translateX(360%); }
    }
    .project-topline-title { color:#d7e7fc; font-size:.73rem; font-weight:850; letter-spacing:.12em; text-transform:uppercase; }
    .project-topline-sub { color:#8195af; font-size:.68rem; margin-top:4px; letter-spacing:.025em; }
    .hero { animation:csPageEnter .55s cubic-bezier(.2,.7,.2,1) both; }
    .hero:before { animation:csHeroAura 11s ease-in-out infinite; }
    .hero-title { max-width:850px; }
    .hero-project-name { color:#f3f7fd; font-size:clamp(2rem,4.1vw,3.35rem); line-height:1.04; font-weight:850; letter-spacing:-.06em; margin:0 0 13px; max-width:820px; }
    .hero-tagline { color:#8fe7d9; font-size:.98rem; font-weight:800; letter-spacing:-.01em; margin:0 0 13px; }
    .hero-copy { max-width:790px; }
    .project-intro-grid { display:grid; grid-template-columns:1.15fr .85fr; gap:14px; margin:18px 0 24px; }
    .project-info-card { position:relative; overflow:hidden; border:1px solid #25384e; border-radius:15px; padding:18px 19px; background:linear-gradient(145deg,rgba(17,28,43,.92),rgba(13,21,33,.95)); }
    .project-info-card:after { content:""; position:absolute; left:0; top:0; bottom:0; width:2px; background:linear-gradient(180deg,#78a9ff,#5bd7c4); opacity:.78; }
    .project-info-title { color:#eaf2fd; font-size:.92rem; font-weight:820; margin-bottom:8px; letter-spacing:-.015em; }
    .project-info-copy { color:#9fb0c6; font-size:.81rem; line-height:1.65; }
    .project-objective-list { display:grid; grid-template-columns:1fr 1fr; gap:8px 12px; margin-top:12px; }
    .project-objective { display:flex; align-items:flex-start; gap:8px; color:#c4d2e3; font-size:.78rem; line-height:1.5; }
    .project-objective-mark { flex:0 0 19px; width:19px; height:19px; display:flex; justify-content:center; align-items:center; border-radius:6px; background:#17312f; color:#72dcca; border:1px solid #265149; font-size:.68rem; font-weight:900; }
    .architecture-strip { border:1px solid #273b52; border-radius:17px; padding:18px; background:linear-gradient(120deg,rgba(14,24,38,.95),rgba(14,29,38,.94)); margin:16px 0 23px; }
    .architecture-head { display:flex; align-items:flex-end; justify-content:space-between; gap:15px; margin-bottom:15px; }
    .architecture-title { color:#eff5fd; font-size:.94rem; font-weight:820; }
    .architecture-caption { color:#7f94af; font-size:.7rem; }
    .architecture-flow { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; position:relative; }
    .architecture-node { position:relative; border:1px solid #2d425a; border-radius:11px; background:#101b29; padding:13px 12px; min-height:112px; animation:csNodeArrive .55s cubic-bezier(.2,.7,.2,1) both; animation-delay:calc(var(--node-index) * .12s); }
    .architecture-node:nth-child(2) { background:linear-gradient(145deg,#111f33,#101a28); }
    .architecture-node:nth-child(3) { background:linear-gradient(145deg,#102b2d,#101b29); }
    .architecture-no { color:#73d6c7; font-size:.64rem; letter-spacing:.12em; font-weight:900; margin-bottom:8px; }
    .architecture-node-title { color:#e7f0fc; font-size:.8rem; font-weight:780; margin-bottom:5px; }
    .architecture-node-copy { color:#8ea3bd; font-size:.71rem; line-height:1.48; }
    .architecture-node:not(:last-child):after { content:"→"; color:#719bdc; position:absolute; right:-12px; top:34px; z-index:3; width:15px; height:19px; font-size:1rem; font-weight:900; text-align:center; animation:csSoftPulse 2s ease-in-out infinite; }
    .motion-panel { position:relative; overflow:hidden; border:1px solid rgba(109,155,211,.3); border-radius:17px; padding:17px 18px 15px; margin:17px 0 24px; background:linear-gradient(120deg,rgba(14,26,42,.98),rgba(12,29,36,.96)); animation:csPageEnter .48s cubic-bezier(.2,.7,.2,1) both; }
    .motion-panel:before { content:""; position:absolute; left:-15%; right:-15%; top:0; height:1px; background:linear-gradient(90deg,transparent,rgba(120,169,255,.7),rgba(91,215,196,.7),transparent); animation:csRailShimmer 4.2s ease-in-out infinite; }
    .motion-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:13px; margin-bottom:5px; }
    .motion-title { color:#edf4fe; font-size:.96rem; font-weight:830; letter-spacing:-.02em; }
    .motion-label { color:#7e97b7; border:1px solid #2b4059; background:#111f30; border-radius:7px; padding:5px 8px; font-size:.62rem; font-weight:850; letter-spacing:.09em; white-space:nowrap; }
    .motion-subtitle { color:#91a5be; font-size:.78rem; line-height:1.55; margin-bottom:16px; max-width:880px; }
    .motion-track { --motion-count:4; display:grid; grid-template-columns:repeat(var(--motion-count),minmax(0,1fr)); gap:9px; position:relative; }
    .motion-track:before { content:""; position:absolute; top:26px; left:5%; right:5%; height:2px; background:linear-gradient(90deg,#2b4567,#2a615d,#2b4567); opacity:.8; }
    .motion-track:after { content:""; position:absolute; top:24px; height:5px; width:12%; left:3%; border-radius:99px; background:linear-gradient(90deg,transparent,#81b3ff,#69e0c9,transparent); filter:drop-shadow(0 0 5px rgba(91,215,196,.45)); animation:csFlowPacket 3.4s ease-in-out infinite; pointer-events:none; }
    .motion-node { position:relative; z-index:1; min-width:0; padding:0 10px 11px; text-align:center; border:1px solid rgba(46,65,88,.86); border-radius:12px; background:rgba(13,23,36,.9); animation:csNodeArrive .58s cubic-bezier(.2,.7,.2,1) both; animation-delay:calc(var(--node-index) * .15s); transition:transform .2s ease,border-color .2s ease,background .2s ease; }
    .motion-node:hover { transform:translateY(-3px); border-color:#6699e8; }
    .motion-glyph { position:relative; display:flex; justify-content:center; align-items:center; width:39px; height:39px; margin:7px auto 9px; border:1px solid #354d6b; border-radius:12px; color:#a9c8ff; background:linear-gradient(145deg,#1a2f4c,#13243a); font-size:1rem; font-weight:900; }
    .motion-node.is-spotlight .motion-glyph { color:#93eedf; border-color:#36776f; background:linear-gradient(145deg,#173e3d,#142b34); animation:csGlyphGlow 2.5s ease-in-out infinite; }
    .motion-node-title { color:#e5eefb; font-size:.75rem; font-weight:820; line-height:1.32; margin-bottom:5px; overflow-wrap:anywhere; }
    .motion-node-copy { color:#849ab5; font-size:.68rem; line-height:1.45; overflow-wrap:anywhere; }
    .motion-takeaway { display:flex; align-items:flex-start; gap:9px; border-top:1px solid rgba(133,158,191,.15); margin-top:13px; padding-top:12px; color:#b4c7dc; font-size:.76rem; line-height:1.58; }
    .motion-takeaway-mark { color:#69dfca; font-weight:900; }
    .step-explainer { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:17px 0 22px; }
    .step-explainer-card { border:1px solid #263a51; border-radius:13px; padding:14px 15px; background:rgba(15,24,37,.74); }
    .step-explainer-label { color:#7fa6da; font-size:.64rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin-bottom:7px; }
    .step-explainer-title { color:#eaf2fd; font-size:.82rem; font-weight:800; margin-bottom:5px; }
    .step-explainer-copy { color:#95a9c1; font-size:.76rem; line-height:1.58; }
    .wizard-node.is-current .wizard-node-circle { animation:csGlyphGlow 2.8s ease-in-out infinite; }
    .wizard-progress-fill { position:relative; overflow:hidden; }
    .wizard-progress-fill:after { content:""; position:absolute; top:0; bottom:0; width:25%; background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent); animation:csStepProgressGlow 2.9s ease-in-out infinite; }
    .workflow-card { animation:csNodeArrive .55s cubic-bezier(.2,.7,.2,1) both; }
    .workflow-card:nth-child(2) { animation-delay:.1s; }
    .workflow-card:nth-child(3) { animation-delay:.2s; }
    .workflow-card:nth-child(4) { animation-delay:.3s; }
    @media (max-width: 900px) {
      .project-intro-grid { grid-template-columns:1fr; }
      .architecture-flow { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .architecture-node:nth-child(2):after { display:none; }
      .motion-track { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .motion-track:before, .motion-track:after { display:none; }
      .step-explainer { grid-template-columns:1fr; }
    }
    @media (max-width: 540px) {
      .project-objective-list { grid-template-columns:1fr; }
      .architecture-flow { grid-template-columns:1fr; }
      .architecture-node:after { display:none !important; }
      .motion-heading { flex-direction:column; }
      .motion-track { grid-template-columns:1fr 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      .hero, .hero:before, .motion-panel, .motion-panel:before, .motion-node,
      .motion-track:after, .architecture-node, .workflow-card,
      .wizard-progress-fill:after, .wizard-node.is-current .wizard-node-circle,
      .workflow-card:hover .workflow-no {
        animation:none !important;
        transition:none !important;
        filter:none !important;
      }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# Session state used by the application.
def ensure_state(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default

for _key, _default in {
    "generated_public_key": None,
    "generated_private_key": None,
    "aes_lab": None,
    "aes_lab_recovered": None,
    "secure_package_data": None,
    "secure_package_name": None,
    "recovered_secure_file": None,
    "last_decrypt_status": None,
    "last_tamper_status": None,
    "last_wrong_key_status": None,
}.items():
    ensure_state(_key, _default)

# Guided workflow helpers. Streamlit reruns on navigation; CSS animates the new stage.
STEP_PAGES = [
    "Step 1 · Keys & identity",
    "Step 2 · Encrypt & share",
    "Step 3 · Decrypt & verify",
    "Step 4 · Security tests",
]


def set_navigation(target: str) -> None:
    st.session_state["workspace_navigation"] = target


def render_step_guide(number: int, title: str, action: str, expected: str) -> None:
    st.markdown(
        f'<div class="step-guide">'
        f'<div class="guide-head"><div class="guide-icon">{number:02d}</div>'
        f'<div><div class="guide-eyebrow">Your task in this step</div>'
        f'<div class="guide-title">{title}</div></div>'
        f'<div class="guide-step">STEP {number:02d} / 04</div></div>'
        f'<div class="guide-grid"><div class="guide-cell"><div class="guide-label">What to do</div>'
        f'<div class="guide-copy">{action}</div></div><div class="guide-cell">'
        f'<div class="guide-label">Expected result</div><div class="guide-copy">{expected}</div>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )



PROCESS_STORY = {
    0: {
        "title": "The end-to-end cryptographic journey",
        "subtitle": "Follow the file from recipient key setup through hybrid encryption, authenticated recovery, and negative security tests.",
        "nodes": [
            ("01", "Create identity", "Generate an RSA public/private key pair."),
            ("02", "Encrypt & wrap", "AES protects the file; RSA protects the AES key."),
            ("03", "Recover & verify", "The recipient unwraps the key and authenticates the data."),
            ("04", "Test security", "Wrong keys and altered ciphertext must be rejected."),
        ],
        "takeaway": "Project goal: demonstrate confidentiality and ciphertext integrity in a local, reproducible academic prototype.",
    },
    1: {
        "title": "Inside Step 1 · Establish recipient identity",
        "subtitle": "Key creation is the foundation: the public key is used by the sender; the private key stays with the recipient and is encrypted at rest with a passphrase.",
        "nodes": [
            ("PW", "Passphrase", "Choose and confirm a unique passphrase."),
            ("RSA", "Generate RSA", "Create a 3072-bit RSA key pair."),
            ("PUB", "Public key", "Share the public key with the sender."),
            ("LOCK", "Private key", "Keep the encrypted private key and passphrase safe."),
        ],
        "takeaway": "Identity note: RSA key generation does not prove who owns a public key. In a real deployment, recipients need a trusted way to verify the public key.",
    },
    2: {
        "title": "Inside Step 2 · Encrypt and package",
        "subtitle": "The actual file never goes through RSA. A fresh AES key encrypts the file, and RSA-OAEP encrypts only that small AES key.",
        "nodes": [
            ("FILE", "Original file", "Select a file and the recipient's trusted public key."),
            ("AES", "AES-256-GCM", "Encrypt the file and authenticate the contents."),
            ("RSA", "RSA-OAEP", "Wrap the random AES key with the public key."),
            ("PKG", "Secure package", "Bundle ciphertext, wrapped key, nonce and metadata."),
        ],
        "takeaway": "Key distinction: AES is efficient for large file contents; RSA-OAEP protects the randomly generated AES key.",
    },
    3: {
        "title": "Inside Step 3 · Recover and verify",
        "subtitle": "The recipient needs the package plus the matching encrypted private key and passphrase. The application releases the original only after authenticated decryption succeeds.",
        "nodes": [
            ("PKG", "Open package", "Read the manifest and ciphertext."),
            ("RSA", "Unwrap AES key", "Use the matching RSA private key."),
            ("AUTH", "Verify AES-GCM", "Authenticate the encrypted data before accepting it."),
            ("FILE", "Recover file", "Download the recovered original bytes."),
        ],
        "takeaway": "If the private key does not match or the ciphertext has changed, recovery should fail rather than accept unauthenticated data.",
    },
    4: {
        "title": "Inside Step 4 · Validate the protections",
        "subtitle": "Security claims need negative tests. First prove the package works with the matching key, then show that incorrect or modified inputs fail.",
        "nodes": [
            ("OK", "Valid baseline", "Confirm the original package and key work."),
            ("KEY", "Wrong key", "A different RSA private key must not unwrap the AES key."),
            ("TAMPER", "Modify ciphertext", "Flip a bit in a temporary in-memory copy."),
            ("BLOCK", "Reject input", "RSA or AES-GCM validation should fail."),
        ],
        "takeaway": "Run both tests and save screenshots of the results for the project report. The original downloaded package is not modified by the tamper test.",
    },
}


def render_process_animation(step: int) -> None:
    story = PROCESS_STORY.get(step, PROCESS_STORY[0])
    nodes = []
    count = len(story["nodes"])
    for index, (glyph, title, copy) in enumerate(story["nodes"]):
        spotlight = " is-spotlight" if index == count - 1 else ""
        nodes.append(
            f'<div class="motion-node{spotlight}" style="--node-index:{index}">'
            f'<div class="motion-glyph">{glyph}</div>'
            f'<div class="motion-node-title">{title}</div>'
            f'<div class="motion-node-copy">{copy}</div></div>'
        )
    st.markdown(
        '<section class="motion-panel">'
        '<div class="motion-heading"><div class="motion-title">' + story["title"] + '</div>'
        '<div class="motion-label">LIVE FLOW EXPLAINER</div></div>'
        '<div class="motion-subtitle">' + story["subtitle"] + '</div>'
        f'<div class="motion-track" style="--motion-count:{count}">{"".join(nodes)}</div>'
        '<div class="motion-takeaway"><span class="motion-takeaway-mark">↳</span>'
        '<span>' + story["takeaway"] + '</span></div></section>',
        unsafe_allow_html=True,
    )


def render_project_explanation() -> None:
    st.markdown(
        '<div class="project-intro-grid">'
        '<div class="project-info-card"><div class="project-info-title">Project overview</div>'
        '<div class="project-info-copy">CipherShare is a Python and Streamlit academic prototype for secure file sharing. It demonstrates hybrid encryption: AES-256-GCM encrypts the file contents, while RSA-OAEP protects the randomly generated AES key so the intended recipient can recover it with the matching private key.</div>'
        '<div class="project-objective-list">'
        '<div class="project-objective"><span class="project-objective-mark">✓</span><span>Keep file contents confidential during handoff.</span></div>'
        '<div class="project-objective"><span class="project-objective-mark">✓</span><span>Detect ciphertext modification through authentication.</span></div>'
        '<div class="project-objective"><span class="project-objective-mark">✓</span><span>Use separate public and private key roles.</span></div>'
        '<div class="project-objective"><span class="project-objective-mark">✓</span><span>Demonstrate correct-key, wrong-key and tamper cases.</span></div>'
        '</div></div>'
        '<div class="project-info-card"><div class="project-info-title">Why hybrid encryption?</div>'
        '<div class="project-info-copy">Public-key cryptography is useful for protecting a small secret, but it is inefficient for large files. CipherShare uses a fresh AES key for the file, then encrypts that AES key with the recipient’s RSA public key. The recipient reverses those operations with the private key.</div>'
        '<div class="project-objective-list">'
        '<div class="project-objective"><span class="project-objective-mark">A</span><span><b>AES-256-GCM</b> — file encryption and tamper detection.</span></div>'
        '<div class="project-objective"><span class="project-objective-mark">R</span><span><b>RSA-OAEP / SHA-256</b> — protects the AES key.</span></div>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="architecture-strip"><div class="architecture-head">'
        '<div><div class="section-kicker">System architecture</div><div class="architecture-title">From sender input to recipient recovery</div></div>'
        '<div class="architecture-caption">Four stages · one protected package</div></div>'
        '<div class="architecture-flow">'
        '<div class="architecture-node" style="--node-index:0"><div class="architecture-no">STAGE 01</div><div class="architecture-node-title">Recipient identity</div><div class="architecture-node-copy">RSA public key is shared; private key is protected separately.</div></div>'
        '<div class="architecture-node" style="--node-index:1"><div class="architecture-no">STAGE 02</div><div class="architecture-node-title">Hybrid encryption</div><div class="architecture-node-copy">AES-GCM encrypts the file; RSA-OAEP wraps the AES key.</div></div>'
        '<div class="architecture-node" style="--node-index:2"><div class="architecture-no">STAGE 03</div><div class="architecture-node-title">Authenticated recovery</div><div class="architecture-node-copy">The matching private key unwraps the key, then AES-GCM authenticates.</div></div>'
        '<div class="architecture-node" style="--node-index:3"><div class="architecture-no">STAGE 04</div><div class="architecture-node-title">Security validation</div><div class="architecture-node-copy">Negative tests check wrong-key and tamper rejection.</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

def render_wizard_progress(page: str) -> None:
    step_for_page = {
        "Step 1 · Keys & identity": 1,
        "Step 2 · Encrypt & share": 2,
        "Step 3 · Decrypt & verify": 3,
        "Step 4 · Security tests": 4,
    }
    current = step_for_page.get(page, 0)
    done = [
        st.session_state.get("generated_public_key") is not None,
        st.session_state.get("secure_package_data") is not None,
        st.session_state.get("recovered_secure_file") is not None,
        st.session_state.get("last_tamper_status") == "passed"
        and st.session_state.get("last_wrong_key_status") == "passed",
    ]
    if current:
        progress = int((current - 1) / 3 * 100)
        caption = f"Step {current} of 4 · Guided secure-sharing workflow"
    elif page == "AES lab (optional)":
        progress = 0
        caption = "Optional lab · Explore AES independently"
    else:
        progress = 0
        caption = "Start here · Follow the four steps in order"
    names = ["Create keys", "Encrypt & package", "Recover file", "Validate security"]
    nodes = []
    for i, name in enumerate(names, start=1):
        state = "is-current" if current == i else ("is-done" if done[i-1] else "")
        marker = "✓" if done[i-1] and current != i else f"{i:02d}"
        status = "Complete" if done[i-1] else ("In progress" if current == i else "Pending")
        nodes.append(
            f'<div class="wizard-node {state}"><div class="wizard-node-circle">{marker}</div>'
            f'<div class="wizard-node-label">{name}</div><div class="wizard-node-status">{status}</div></div>'
        )
    st.markdown(
        '<div class="wizard-shell"><div class="wizard-top">'
        '<div class="wizard-label">SECURE-SHARING WORKFLOW</div>'
        f'<div class="wizard-caption">{caption}</div></div>'
        f'<div class="wizard-progress-track"><div class="wizard-progress-fill" style="--progress-width:{progress}%"></div></div>'
        f'<div class="wizard-rail">{"".join(nodes)}</div></div>',
        unsafe_allow_html=True,
    )


def render_step_navigation(page: str) -> None:
    routes = {
        "Overview": (None, STEP_PAGES[0]),
        STEP_PAGES[0]: ("Overview", STEP_PAGES[1]),
        STEP_PAGES[1]: (STEP_PAGES[0], STEP_PAGES[2]),
        STEP_PAGES[2]: (STEP_PAGES[1], STEP_PAGES[3]),
        STEP_PAGES[3]: (STEP_PAGES[2], "Overview"),
        "AES lab (optional)": ("Overview", STEP_PAGES[1]),
    }
    if page not in routes:
        return
    prev_page, next_page = routes[page]
    st.markdown('<div class="step-nav-row">', unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="medium")
    with left:
        if prev_page:
            st.button("← Previous", key=f"nav_prev_{page}", on_click=set_navigation, args=(prev_page,), use_container_width=True)
        else:
            st.markdown('<div class="step-nav-hint">Start with the recipient’s keys. The same key pair must be used for encryption and recovery.</div>', unsafe_allow_html=True)
    with right:
        label = "Finish · Back to overview ↗" if page == STEP_PAGES[3] else ("Start guided workflow →" if page == "Overview" else ("Next step →" if page != "AES lab (optional)" else "Continue to secure sharing →"))
        st.button(label, key=f"nav_next_{page}", on_click=set_navigation, args=(next_page,), type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Sidebar / main navigation.
with st.sidebar:
    st.markdown(
        '<div class="brand-row"><div class="brand-mark">CS</div><div><div class="brand-name">CipherShare</div><div class="brand-sub">Hybrid cryptography · Guided project</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
    page = st.radio(
        "Workspace navigation",
        ["Overview", "Step 1 · Keys & identity", "Step 2 · Encrypt & share", "Step 3 · Decrypt & verify", "Step 4 · Security tests", "AES lab (optional)"],
        label_visibility="collapsed",
        key="workspace_navigation",
    )
    st.markdown('<div class="side-label">Cryptographic stack</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-stack">'
        '<div class="side-stack-row"><span>AES-256-GCM</span><span style="color:#75d8c7">Content</span></div>'
        '<div class="side-stack-row"><span>RSA-OAEP</span><span style="color:#9fc0ff">Key wrap</span></div>'
        '<div class="side-stack-row"><span>SHA-256 for OAEP</span><span style="color:#b4c0d0">OAEP digest</span></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-label">Environment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="side-stack">'
        '<div class="side-stack-row"><span><span class="small-dot"></span>Local prototype</span><span style="color:#8ca1ba">Active</span></div>'
        '<div style="color:#7e91a9;font-size:.73rem;line-height:1.5;margin-top:7px">Files are processed by this running Streamlit app. No online transfer server is configured.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("\n")
    st.caption("Academic prototype · Cryptography & Network Security")

# Shared product top bar.
st.markdown(
    '<div class="topline"><div><div class="project-topline-title">Secure File Sharing Using Hybrid Cryptography</div>'
    '<div class="project-topline-sub">Cryptography &amp; Network Security · Academic project workspace</div></div>'
    '<div class="topline-right"><span class="status-pill"><span class="small-dot"></span>Local session</span><span>v1.1 · Guided demo</span></div></div>',
    unsafe_allow_html=True,
)

render_wizard_progress(page)

# Overview hero is intentionally compact, with a meaningful protocol preview.
if page == "Overview":
    st.markdown(
        '<div class="hero"><div class="eyebrow">CRYPTOGRAPHY &amp; NETWORK SECURITY · MINI PROJECT</div>'
        '<div class="hero-project-name">Secure File Sharing<br>Using Hybrid Cryptography</div>'
        '<div class="hero-tagline">Send the file. Not the plaintext.</div>'
        '<p class="hero-copy">CipherShare is a guided demonstration of confidential file handoff. A fresh AES-256-GCM key encrypts the original file, RSA-OAEP protects that AES key for the recipient, and authenticated decryption checks that the encrypted data has not been altered.</p>'
        '<div class="hero-tags"><span class="hero-tag">AES-256-GCM · File contents</span><span class="hero-tag">RSA-OAEP / SHA-256 · Key protection</span><span class="hero-tag">Wrong-key validation</span><span class="hero-tag">Ciphertext tamper test</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-kicker">Project introduction</div>', unsafe_allow_html=True)
    st.markdown('## What this project demonstrates')
    st.markdown('<p class="section-desc">The goal is to send a file without sending its plaintext or exposing the AES key. The four-step workflow walks through key setup, encryption, recipient recovery, and security checks.</p>', unsafe_allow_html=True)
    render_project_explanation()
    render_process_animation(0)
    key_ready = st.session_state["generated_public_key"] is not None
    package_ready = st.session_state["secure_package_data"] is not None
    file_recovered = st.session_state["recovered_secure_file"] is not None
    m1, m2, m3 = st.columns(3, gap="medium")
    with m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-top"><span>Key management</span><span class="metric-icon">01</span></div><div class="metric-value">{"Key pair ready" if key_ready else "Awaiting keys"}</div><div class="metric-note">{"Public and encrypted private key generated in this session" if key_ready else "Generate an RSA key pair to begin"}</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-top"><span>Secure package</span><span class="metric-icon">02</span></div><div class="metric-value">{"Package prepared" if package_ready else "Not created yet"}</div><div class="metric-note">{"Ready to download and test with the recipient" if package_ready else "Encrypt a file for a recipient's public key"}</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-top"><span>Recipient recovery</span><span class="metric-icon">03</span></div><div class="metric-value">{"File recovered" if file_recovered else "Waiting to verify"}</div><div class="metric-note">{"A file was recovered during this session" if file_recovered else "Decrypt the package using the matching private key"}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="overview-start"><div class="overview-start-title">Recommended route · Start with Step 1</div><div class="overview-start-copy">Generate the recipient keys first, encrypt a file for that public key, recover it with the matching private key, then prove wrong-key and tamper rejection. The AES lab is optional and separate from the complete sharing package.</div></div>', unsafe_allow_html=True)
    st.markdown("\n")
    st.markdown('<div class="section-kicker">The workflow</div>', unsafe_allow_html=True)
    st.markdown("## Your guided project walkthrough")
    st.markdown('<p class="section-desc">Follow the steps in order. Each stage explains the action, the cryptographic operation, and the result to verify before moving forward.</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        st.markdown('<div class="workflow-card"><div class="workflow-no">01</div><div class="workflow-title">Keys &amp; identity</div><div class="workflow-copy">Generate a matched RSA key pair. Share the public key; protect the private key.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="workflow-card"><div class="workflow-no">02</div><div class="workflow-title">Encrypt &amp; share</div><div class="workflow-copy">AES-GCM encrypts the file, while RSA-OAEP wraps the AES key in a package.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="workflow-card"><div class="workflow-no">03</div><div class="workflow-title">Decrypt &amp; verify</div><div class="workflow-copy">The matching private key unwraps the AES key; authenticated decryption recovers the file.</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="workflow-card"><div class="workflow-no">04</div><div class="workflow-title">Security tests</div><div class="workflow-copy">Show rejection of a different private key and of modified ciphertext.</div></div>', unsafe_allow_html=True)

    st.markdown("\n")
    st.markdown('<div class="callout"><span class="callout-symbol">i</span><span><b>Project scope.</b> This is a local academic prototype, not a hosted multi-user transfer service. Public-key identity verification, user accounts, remote delivery, and production key storage are outside the current implementation. The sender must obtain the recipient’s public key through a trusted channel.</span></div>', unsafe_allow_html=True)

elif page == "Step 1 · Keys & identity":
    st.markdown('<div class="section-kicker">01 / Recipient setup</div>', unsafe_allow_html=True)
    st.markdown("## Keys & identity")
    st.markdown('<p class="section-desc">Every secure exchange begins with a recipient identity. Create a matching RSA public/private key pair; the public key is used by the sender, while the passphrase-protected private key stays with the recipient.</p>', unsafe_allow_html=True)
    render_step_guide(1, "Create the recipient identity", "Enter a new, unique passphrase twice, generate the RSA key pair, then download both PEM files. Share only the public key; retain the encrypted private key and passphrase separately.", "You will have a public key for the sender and a passphrase-protected private key for recipient-side recovery.")
    render_process_animation(1)
    st.markdown('<div class="step-explainer"><div class="step-explainer-card"><div class="step-explainer-label">Why this step matters</div><div class="step-explainer-title">The keys are a matched pair</div><div class="step-explainer-copy">Only the corresponding private key can unwrap an AES key encrypted with this public key. If you generate a different pair later, packages for the earlier public key will not decrypt.</div></div><div class="step-explainer-card"><div class="step-explainer-label">What to keep</div><div class="step-explainer-title">Two files, different handling</div><div class="step-explainer-copy">Give the sender <code>recipient_public_key.pem</code>. Keep <code>recipient_private_key_encrypted.pem</code> and its passphrase private.</div></div></div>', unsafe_allow_html=True)
    left, right = st.columns([1.2, .8], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="panel-heading"><div class="panel-number">01</div><h3 style="margin:0">Generate RSA key pair</h3></div>', unsafe_allow_html=True)
            st.markdown('<p class="file-note">Use a unique passphrase of at least 12 characters. Keep it separate from the downloaded private-key file.</p>', unsafe_allow_html=True)
            passphrase = st.text_input("Private-key passphrase", type="password", key="rsa_passphrase", placeholder="Create a strong, unique passphrase")
            confirm_passphrase = st.text_input("Confirm passphrase", type="password", key="rsa_passphrase_confirm", placeholder="Re-enter passphrase")
            if st.button("Generate RSA key pair", key="generate_rsa_button", type="primary", use_container_width=True):
                if len(passphrase) < 12:
                    st.error("Use a passphrase with at least 12 characters.")
                elif passphrase != confirm_passphrase:
                    st.error("The passphrases do not match.")
                else:
                    try:
                        public_key, private_key = generate_rsa_key_pair(passphrase)
                        st.session_state["generated_public_key"] = public_key
                        st.session_state["generated_private_key"] = private_key
                        st.success("RSA key pair generated successfully.")
                    except Exception:
                        st.error("Key generation failed. Check the VS Code terminal for details.")
    with right:
        st.markdown('<div class="muted-box"><div class="muted-box-title">Public key</div><div class="muted-box-copy">Share this file with a sender. It is used to encrypt the AES key, not the entire file.</div></div>', unsafe_allow_html=True)
        st.markdown("\n")
        st.markdown('<div class="muted-box"><div class="muted-box-title">Encrypted private key</div><div class="muted-box-copy">Keep this file private. The passphrase is needed to unlock it before decryption.</div></div>', unsafe_allow_html=True)
        st.markdown("\n")
        st.markdown('<div class="callout"><span class="callout-symbol">!</span><span>Regenerating a key pair creates a new identity. Packages encrypted for an earlier public key will not decrypt with the new private key.</span></div>', unsafe_allow_html=True)

    if st.session_state["generated_public_key"] is not None:
        st.markdown("\n")
        st.markdown("### Export keys")
        pc, qc = st.columns(2, gap="medium")
        with pc:
            with st.container(border=True):
                st.markdown("**Public key**")
                st.caption("Safe to distribute to the sender.")
                st.download_button("Download public key", data=st.session_state["generated_public_key"], file_name="recipient_public_key.pem", mime="application/x-pem-file", key="download_public_key", use_container_width=True)
        with qc:
            with st.container(border=True):
                st.markdown("**Passphrase-protected private key**")
                st.caption("Store securely. Never send it with the package.")
                st.download_button("Download encrypted private key", data=st.session_state["generated_private_key"], file_name="recipient_private_key_encrypted.pem", mime="application/x-pem-file", key="download_private_key", use_container_width=True)

elif page == "AES lab (optional)":
    st.markdown('<div class="section-kicker">02 / Algorithm demonstration</div>', unsafe_allow_html=True)
    st.markdown("## AES-256-GCM lab")
    st.markdown('<p class="section-desc">A standalone algorithm test for your report and viva. Its ciphertext download is for demonstration only; it does not include the AES key needed for an independent recipient.</p>', unsafe_allow_html=True)
    st.markdown('<div class="step-guide"><div class="guide-head"><div class="guide-icon">LAB</div><div><div class="guide-eyebrow">Optional learning tool</div><div class="guide-title">Test AES before the full sharing flow</div></div></div><div class="guide-grid"><div class="guide-cell"><div class="guide-label">What to do</div><div class="guide-copy">Upload a small test file, encrypt it, then click “Decrypt and verify”.</div></div><div class="guide-cell"><div class="guide-label">Expected result</div><div class="guide-copy">The recovered bytes match the original. Continue to Step 2 for the complete AES + RSA package.</div></div></div></div>', unsafe_allow_html=True)
    upload_col, detail_col = st.columns([1.15, .85], gap="large")
    with upload_col:
        with st.container(border=True):
            st.markdown('<div class="panel-heading"><div class="panel-number">01</div><h3 style="margin:0">Choose a test file</h3></div>', unsafe_allow_html=True)
            aes_upload = st.file_uploader("Select a file for AES-only encryption", key="aes_lab_upload")
            if aes_upload is not None:
                st.markdown(f'<div class="result-card"><div class="result-title">File selected</div><div class="result-copy">{len(aes_upload.getvalue()):,} bytes · {Path(aes_upload.name).suffix or "no extension"}</div></div>', unsafe_allow_html=True)
            if st.button("Encrypt with AES-256-GCM", key="aes_lab_encrypt", disabled=aes_upload is None, type="primary", use_container_width=True):
                try:
                    original_data = aes_upload.getvalue()
                    aes_key, nonce, ciphertext = encrypt_file_aes(original_data)
                    st.session_state["aes_lab"] = {"filename": aes_upload.name, "mime_type": aes_upload.type or "application/octet-stream", "key": aes_key, "nonce": nonce, "ciphertext": ciphertext, "original_hash": hashlib.sha256(original_data).hexdigest()}
                    st.session_state["aes_lab_recovered"] = None
                    st.success("File encrypted successfully.")
                except Exception:
                    st.error("AES encryption failed. Check the terminal for details.")
    with detail_col:
        st.markdown('<div class="muted-box"><div class="muted-box-title">What this demonstrates</div><div class="muted-box-copy">A fresh 256-bit AES key encrypts the file. GCM authenticates the ciphertext and rejects altered data during decryption.</div></div>', unsafe_allow_html=True)
        st.markdown("\n")
        st.markdown('<div class="muted-box"><div class="muted-box-title">What this does not demonstrate</div><div class="muted-box-copy">The standalone lab is not the full sharing flow because the AES key stays in this Streamlit session.</div></div>', unsafe_allow_html=True)

    if st.session_state["aes_lab"] is not None:
        aes_demo = st.session_state["aes_lab"]
        st.markdown("\n")
        st.markdown("### Test output")
        out1, out2 = st.columns([1, 1], gap="medium")
        with out1:
            with st.container(border=True):
                st.markdown("**Encrypted output**")
                st.caption(f"{aes_demo['filename']} · {len(aes_demo['ciphertext']):,} ciphertext bytes")
                st.download_button("Download AES ciphertext", data=aes_demo["nonce"] + aes_demo["ciphertext"], file_name=aes_demo["filename"] + ".aesgcm", mime="application/octet-stream", key="aes_lab_download", use_container_width=True)
        with out2:
            with st.container(border=True):
                st.markdown("**Recovery test**")
                st.caption("Decrypt and compare the recovered bytes with the original.")
                if st.button("Decrypt and verify", key="aes_lab_decrypt", use_container_width=True):
                    try:
                        recovered = decrypt_file_aes(aes_demo["key"], aes_demo["nonce"], aes_demo["ciphertext"])
                        if hashlib.sha256(recovered).hexdigest() == aes_demo["original_hash"]:
                            st.session_state["aes_lab_recovered"] = recovered
                            st.success("Verification passed. The bytes match.")
                        else:
                            st.error("The recovered content differs from the original.")
                    except Exception:
                        st.error("AES decryption failed; data may be invalid or modified.")
                if st.session_state["aes_lab_recovered"] is not None:
                    st.download_button("Download recovered file", data=st.session_state["aes_lab_recovered"], file_name=aes_demo["filename"], mime=aes_demo["mime_type"], key="aes_lab_recovered_download", use_container_width=True)

elif page == "Step 2 · Encrypt & share":
    st.markdown('<div class="section-kicker">03 / Sender workspace</div>', unsafe_allow_html=True)
    st.markdown("## Encrypt & share")
    st.markdown('<p class="section-desc">This is the sender’s stage. The file contents are encrypted with AES-256-GCM, then RSA-OAEP encrypts the newly generated AES key for the recipient.</p>', unsafe_allow_html=True)
    render_step_guide(2, "Create the encrypted sharing package", "Upload the recipient’s trusted public key (.pem), select the original file, and create the package. Download the resulting .securepkg file. Share the package separately from the recipient’s private key.", "The package contains ciphertext, the RSA-wrapped AES key, the nonce, and metadata needed for authenticated recovery.")
    render_process_animation(2)
    st.markdown('<div class="step-explainer"><div class="step-explainer-card"><div class="step-explainer-label">What gets encrypted?</div><div class="step-explainer-title">AES protects the file</div><div class="step-explainer-copy">A fresh 256-bit AES key and unique nonce are generated for this operation. AES-GCM encrypts the bytes and creates an authentication tag.</div></div><div class="step-explainer-card"><div class="step-explainer-label">Why RSA is used</div><div class="step-explainer-title">RSA protects only the AES key</div><div class="step-explainer-copy">RSA-OAEP encrypts the small AES key with the recipient’s public key. It is not used to encrypt the entire file.</div></div></div>', unsafe_allow_html=True)
    stage1, stage2, stage3 = st.columns(3, gap="small")
    for col, no, title, copy in [
        (stage1, "01", "Recipient key", "Choose a trusted public key."),
        (stage2, "02", "Source file", "Select the original file."),
        (stage3, "03", "Encrypted package", "Create and download the package."),
    ]:
        with col:
            st.markdown(f'<div class="workflow-card"><div class="workflow-no">{no}</div><div class="workflow-title">{title}</div><div class="workflow-copy">{copy}</div></div>', unsafe_allow_html=True)
    st.markdown("\n")
    with st.container(border=True):
        st.markdown('<div class="panel-heading"><div class="panel-number">01</div><h3 style="margin:0">Prepare secure package</h3></div>', unsafe_allow_html=True)
        public_key_file = st.file_uploader("Recipient public key (.pem)", type=["pem"], key="sender_public_key_upload")
        source_file = st.file_uploader("File to protect", key="sender_source_file_upload")
        if st.button("Create secure sharing package", key="create_hybrid_package", disabled=public_key_file is None or source_file is None, type="primary", use_container_width=True):
            try:
                package_bytes = create_secure_package(file_data=source_file.getvalue(), filename=source_file.name, public_key_pem=public_key_file.getvalue())
                st.session_state["secure_package_data"] = package_bytes
                st.session_state["secure_package_name"] = f"secure_share_{Path(source_file.name).stem}.securepkg"
                st.session_state["recovered_secure_file"] = None
                st.session_state["last_tamper_status"] = None
                st.session_state["last_wrong_key_status"] = None
                st.success("Secure package created successfully.")
            except Exception:
                st.error("Package creation failed. Confirm the uploaded file is a valid RSA public key in PEM format.")

    if st.session_state["secure_package_data"] is not None:
        st.markdown("\n")
        st.markdown('<div class="section-kicker">Package output</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="result-card"><div class="result-title">Package ready to download</div><div class="result-copy">The package contains the encrypted file, the RSA-protected AES key, and the metadata needed for decryption.</div></div>', unsafe_allow_html=True)
            st.markdown("\n")
            pkg_col, steps_col = st.columns([1, 1.3], gap="large")
            with pkg_col:
                st.markdown(f"**{st.session_state['secure_package_name']}**")
                st.caption(f"{len(st.session_state['secure_package_data']):,} bytes · encrypted package")
                st.download_button("Download secure package", data=st.session_state["secure_package_data"], file_name=st.session_state["secure_package_name"], mime="application/octet-stream", key="download_hybrid_package", type="primary", use_container_width=True)
            with steps_col:
                st.markdown("**Next: recipient verification**")
                st.markdown('<div class="file-note">Send the package to the recipient separately from their private key. The recipient must use the private key that matches the public key selected above.</div>', unsafe_allow_html=True)

elif page == "Step 3 · Decrypt & verify":
    st.markdown('<div class="section-kicker">04 / Recipient workspace</div>', unsafe_allow_html=True)
    st.markdown("## Decrypt & verify")
    st.markdown('<p class="section-desc">This is the recipient’s stage. The application opens the package, uses the matching private key to recover the AES key, and only releases the original bytes after AES-GCM authentication succeeds.</p>', unsafe_allow_html=True)
    render_step_guide(3, "Recover the original file", "Upload the .securepkg file, the matching passphrase-protected private key, and that key’s passphrase. Click “Decrypt secure package”. Do not use a newly generated or unrelated private key.", "Successful decryption returns a download of the original file. A wrong key, wrong passphrase, or altered encrypted data should fail.")
    render_process_animation(3)
    st.markdown('<div class="step-explainer"><div class="step-explainer-card"><div class="step-explainer-label">Recovery sequence</div><div class="step-explainer-title">RSA first, AES second</div><div class="step-explainer-copy">RSA-OAEP recovers the AES key using the recipient’s private key. AES-GCM then authenticates and decrypts the file contents.</div></div><div class="step-explainer-card"><div class="step-explainer-label">What success means</div><div class="step-explainer-title">The data passed authentication</div><div class="step-explainer-copy">A successful recovery proves that these bytes authenticate under the supplied key and package. It does not independently prove who created or supplied the public key.</div></div></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="panel-heading"><div class="panel-number">01</div><h3 style="margin:0">Recover the original file</h3></div>', unsafe_allow_html=True)
        recipient_package = st.file_uploader("Secure sharing package", key="recipient_package_upload")
        recipient_private_key = st.file_uploader("Matching encrypted private key (.pem)", type=["pem"], key="recipient_private_key_upload")
        recipient_passphrase = st.text_input("Private-key passphrase", type="password", key="recipient_private_key_passphrase", placeholder="Enter the passphrase for this private key")
        current_package_hash = hashlib.sha256(recipient_package.getvalue()).hexdigest() if recipient_package is not None else None
        if st.button("Decrypt secure package", key="recipient_decrypt_button", disabled=recipient_package is None or recipient_private_key is None or not recipient_passphrase, type="primary", use_container_width=True):
            try:
                filename, recovered_data = decrypt_secure_package(package_data=recipient_package.getvalue(), private_key_pem=recipient_private_key.getvalue(), passphrase=recipient_passphrase)
                st.session_state["recovered_secure_file"] = {"filename": filename, "data": recovered_data, "package_hash": current_package_hash}
                st.session_state["last_decrypt_status"] = "success"
                st.session_state["last_tamper_status"] = None
                st.success("Decryption successful. The original file was recovered and authenticated.")
            except Exception:
                st.session_state["recovered_secure_file"] = None
                st.session_state["last_decrypt_status"] = "failed"
                st.error("Decryption failed. Check the package, private key, and passphrase. The package may have been modified.")

    recovered_file = st.session_state["recovered_secure_file"]
    if recovered_file is not None and recovered_file.get("package_hash") == current_package_hash:
        st.markdown("\n")
        with st.container(border=True):
            st.markdown('<div class="result-card"><div class="result-title">Original file recovered</div><div class="result-copy">AES-GCM authentication succeeded. The download below contains the recovered file bytes.</div></div>', unsafe_allow_html=True)
            st.markdown("\n")
            dc1, dc2 = st.columns([1, 1.5], gap="large")
            with dc1:
                st.markdown(f"**{recovered_file['filename']}**")
                st.caption(f"{len(recovered_file['data']):,} bytes · authenticated recovery")
                st.download_button("Download recovered original", data=recovered_file["data"], file_name=recovered_file["filename"], mime="application/octet-stream", key="recipient_download_recovered", type="primary", use_container_width=True)
            with dc2:
                st.markdown('<div class="file-note">A successful result proves that this package can be decrypted with the supplied matching key and passphrase. It does not by itself verify who originally supplied the public key.</div>', unsafe_allow_html=True)



elif page == "Step 4 · Security tests":
    st.markdown('<div class="section-kicker">04 / Validate the protections</div>', unsafe_allow_html=True)
    st.markdown("## Security tests")
    st.markdown('<p class="section-desc">This final stage checks failure behaviour rather than just the happy path. The valid baseline must decrypt, a different RSA private key must not recover the AES key, and altered ciphertext must fail AES-GCM authentication.</p>', unsafe_allow_html=True)
    render_step_guide(4, "Prove the package fails safely", "Upload the valid package and its matching private key/passphrase. Run the tamper test, then upload a different valid RSA private key with its own passphrase and run the wrong-key test.", "Both negative tests should show rejection. The tamper test modifies an in-memory copy and leaves your downloaded original package unchanged.")
    render_process_animation(4)
    st.markdown('<div class="step-explainer"><div class="step-explainer-card"><div class="step-explainer-label">Test A · Integrity</div><div class="step-explainer-title">Flip a bit in ciphertext</div><div class="step-explainer-copy">The modified in-memory package should fail the AES-GCM authentication check. The original package is not overwritten.</div></div><div class="step-explainer-card"><div class="step-explainer-label">Test B · Key agreement</div><div class="step-explainer-title">Try another RSA private key</div><div class="step-explainer-copy">Use a separate key pair and its own passphrase. It should not unwrap the AES key that was encrypted to the real recipient.</div></div></div>', unsafe_allow_html=True)

    st.markdown("### Select the valid package and recipient key")
    with st.container(border=True):
        security_package = st.file_uploader("Secure sharing package (.securepkg)", key="security_package_upload")
        security_private = st.file_uploader("Matching encrypted private key (.pem)", type=["pem"], key="security_private_upload")
        security_passphrase = st.text_input("Matching private-key passphrase", type="password", key="security_passphrase", placeholder="Enter the passphrase for the matching key")
        st.caption("The baseline key and passphrase are required for either test. Do not paste a passphrase into a screenshot or report.")

    st.markdown("### Test A · Tamper detection")
    with st.container(border=True):
        st.markdown('<div class="file-note">This test authenticates the original package, alters one bit in an in-memory copy of its ciphertext, then verifies that AES-GCM rejects the altered copy. The source file on disk is not changed.</div>', unsafe_allow_html=True)
        if st.button("Run tamper-detection test", key="security_tamper_button", type="primary", use_container_width=True, disabled=security_package is None or security_private is None or not security_passphrase):
            try:
                package_bytes = security_package.getvalue()
                private_bytes = security_private.getvalue()
                decrypt_secure_package(package_bytes, private_bytes, security_passphrase)
            except Exception:
                st.session_state["last_tamper_status"] = "blocked"
                st.error("Baseline validation failed. Check the package, matching private key, and passphrase first.")
            else:
                try:
                    changed_copy = tamper_package_ciphertext(package_bytes)
                    decrypt_secure_package(changed_copy, private_bytes, security_passphrase)
                except Exception:
                    st.session_state["last_tamper_status"] = "passed"
                    st.success("Passed: AES-GCM rejected the modified ciphertext.")
                else:
                    st.session_state["last_tamper_status"] = "failed"
                    st.error("Failed: altered ciphertext was accepted. Review the cryptographic implementation.")

    st.markdown("### Test B · Wrong-private-key rejection")
    with st.container(border=True):
        st.markdown('<div class="file-note">Generate a separate RSA key pair for this test. Upload its encrypted private key and the passphrase used for that separate key. The app checks that the test key itself unlocks before trying the package.</div>', unsafe_allow_html=True)
        wrong_private = st.file_uploader("Different RSA private key (.pem)", type=["pem"], key="security_wrong_private_upload")
        wrong_passphrase = st.text_input("Test key passphrase", type="password", key="security_wrong_passphrase", placeholder="Passphrase for the separate test key")
        if st.button("Run wrong-key test", key="security_wrong_key_button", use_container_width=True, disabled=security_package is None or wrong_private is None or not wrong_passphrase):
            try:
                wrong_key_obj = serialization.load_pem_private_key(wrong_private.getvalue(), password=wrong_passphrase.encode("utf-8"))
                if not hasattr(wrong_key_obj, "decrypt"):
                    raise ValueError("The test key is not an RSA private key.")
            except Exception:
                st.session_state["last_wrong_key_status"] = "invalid_test_key"
                st.error("The test key could not be unlocked. Verify that the uploaded file and its passphrase match.")
            else:
                try:
                    decrypt_secure_package(security_package.getvalue(), wrong_private.getvalue(), wrong_passphrase)
                except Exception:
                    st.session_state["last_wrong_key_status"] = "passed"
                    st.success("Passed: the different private key could not recover the AES key.")
                else:
                    st.session_state["last_wrong_key_status"] = "failed"
                    st.error("Failed: a different key unexpectedly decrypted the package.")

    tamper_ok = st.session_state.get("last_tamper_status") == "passed"
    wrong_key_ok = st.session_state.get("last_wrong_key_status") == "passed"
    if tamper_ok and wrong_key_ok:
        st.markdown('<div class="result-card"><div class="result-title">Security validation complete</div><div class="result-copy">Both negative tests passed: altered ciphertext was rejected and a different private key could not recover the file. Save screenshots of these results for your report, with all passphrase fields empty or masked.</div></div>', unsafe_allow_html=True)



# Persistent previous/next controls turn the separate workspaces into a guided wizard.
render_step_navigation(page)

st.markdown(
    '<div class="footer">CipherShare <span style="color:#3f556f">/</span> Academic prototype for Cryptography & Network Security <span style="color:#3f556f">/</span> Local processing only</div>',
    unsafe_allow_html=True,
)
