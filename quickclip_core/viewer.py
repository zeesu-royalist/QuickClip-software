from quickclip_core.config import SAVE_DIR
from quickclip_core.storage import load_clips, load_shots

def is_code(text: str) -> bool:
    indicators = ["def ", "import ", "class ", "const ", "let ", "function",
                  "<html>", "css", "void ", "#include", "public class", "fn ", "impl "]
    if any(ind in text for ind in indicators):
        return True
    if len(text.splitlines()) > 3 and any(c in text for c in ['{', '}', ';', '=', ':', '(', ')']):
        return True
    return False

def generate_viewer():
    """Regenerate the HTML dashboard with current clips and screenshots."""
    clips = load_clips()
    shots = load_shots()

    # ── Text clip cards ────────────────────────────────────────────────────────
    clip_rows = ""
    for c in clips:
        text = c["text"]
        preview = text[:600].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        code_class = " clip-code" if is_code(text) else ""
        escaped = (text.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))
        clip_rows += f"""<div class="clip-card" onclick="copyClip(this)" data-text="{escaped}">
          <div class="clip-content{code_class}">{preview}</div>
          <div class="clip-footer">
            <div class="clip-time"><span>🕒</span><span>{c['time']}</span></div>
            <div class="clip-action-hint">Click to Copy ✨</div>
          </div>
        </div>\n"""

    empty_clips = """<div class="empty-state">
      <div class="empty-icon">📭</div>
      <div class="empty-title">Abhi koi clip nahi hai</div>
      <p class="empty-desc">Koi text copy karo ya <strong>Ctrl+Alt+Q</strong> dabao.</p>
    </div>"""

    # ── Screenshot cards ───────────────────────────────────────────────────────
    shot_rows = ""
    for s in shots:
        thumb = s.get("thumb_b64", "")
        fname = s.get("filename", "screenshot")
        # Full image path relative to viewer.html (both in SAVE_DIR)
        full_path = f"screenshots/{fname}"
        img_tag = (f'<img src="{thumb}" class="shot-thumb" alt="{fname}" '
                   f'onclick="openShot(\'{full_path}\')">'
                   if thumb else
                   f'<div class="shot-placeholder">🖼️</div>')
        shot_rows += f"""<div class="shot-card">
          {img_tag}
          <div class="shot-footer">
            <div class="clip-time"><span>📸</span><span>{s['time']}</span></div>
            <div class="shot-name">{fname[:30]}</div>
          </div>
        </div>\n"""

    empty_shots = """<div class="empty-state">
      <div class="empty-icon">🖼️</div>
      <div class="empty-title">Koi screenshot nahi</div>
      <p class="empty-desc">Screenshot lo — ye page pe apne aap aa jayega!</p>
    </div>"""

    # ── Full HTML ──────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>QuickClip Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-gradient: linear-gradient(135deg, #090d16 0%, #111827 100%);
      --panel-bg: rgba(17, 24, 39, 0.75);
      --card-bg: rgba(31, 41, 55, 0.45);
      --card-hover: rgba(55, 65, 81, 0.6);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-hover: rgba(99, 102, 241, 0.45);
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
      --accent-color: #6366f1;
      --accent-light: #c084fc;
      --success: #10b981;
      --radius-lg: 16px;
      --radius-md: 12px;
      --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: var(--bg-gradient);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* ── Header ── */
    header {{
      width: 100%;
      background: rgba(10,15,30,0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 10;
      padding: 14px 24px;
    }}
    .header-inner {{
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .logo-container {{ display: flex; align-items: center; gap: 10px; }}
    .logo-icon {{ font-size: 26px; filter: drop-shadow(0 2px 8px rgba(99,102,241,.3)); }}
    h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      font-weight: 700;
      background: var(--accent-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .badges {{ display: flex; gap: 10px; }}
    .badge {{
      background: var(--accent-gradient);
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 20px;
    }}
    .badge.green {{ background: linear-gradient(135deg,#10b981,#059669); }}

    /* ── Two-panel layout ── */
    .panels {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0;
      flex: 1;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 0;
    }}
    @media (max-width: 900px) {{
      .panels {{ grid-template-columns: 1fr; }}
    }}

    .panel {{
      padding: 20px 20px 60px;
      border-right: 1px solid var(--border-color);
      overflow-y: auto;
      max-height: calc(100vh - 56px);
    }}
    .panel:last-child {{ border-right: none; }}

    .panel-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 16px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: .08em;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* ── Search ── */
    .search-wrapper {{
      position: relative;
      margin-bottom: 16px;
    }}
    .search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 14px;
      pointer-events: none;
    }}
    .search-input {{
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      padding: 10px 14px 10px 38px;
      outline: none;
      transition: var(--transition);
    }}
    .search-input:focus {{
      border-color: var(--accent-color);
      background: rgba(99,102,241,.08);
    }}

    /* ── Clip cards ── */
    .clip-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 14px 16px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: var(--transition);
    }}
    .clip-card:hover {{ background: var(--card-hover); border-color: var(--border-hover); transform: translateY(-1px); }}
    .clip-card.copied {{ border-color: var(--success); background: rgba(16,185,129,.1); }}
    .clip-content {{
      font-size: 13.5px;
      line-height: 1.65;
      color: var(--text-main);
      word-break: break-word;
      white-space: pre-wrap;
      max-height: 160px;
      overflow: hidden;
    }}
    .clip-code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      background: rgba(0,0,0,.25);
      border-radius: 8px;
      padding: 10px;
    }}
    .clip-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 10px;
    }}
    .clip-time {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      color: var(--text-muted);
    }}
    .clip-action-hint {{
      font-size: 11px;
      color: var(--accent-light);
      opacity: 0;
      transform: translateX(6px);
      transition: var(--transition);
    }}
    .clip-card:hover .clip-action-hint {{ opacity: 1; transform: translateX(0); }}

    /* ── Screenshot cards ── */
    .shots-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 12px;
    }}
    .shot-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
      transition: var(--transition);
    }}
    .shot-card:hover {{ border-color: var(--border-hover); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,.3); }}
    .shot-thumb {{
      width: 100%;
      aspect-ratio: 16/9;
      object-fit: cover;
      display: block;
      cursor: zoom-in;
      background: rgba(0,0,0,.3);
    }}
    .shot-placeholder {{
      width: 100%;
      aspect-ratio: 16/9;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 36px;
      background: rgba(0,0,0,.2);
    }}
    .shot-footer {{
      padding: 8px 10px;
    }}
    .shot-name {{
      font-size: 10px;
      color: var(--text-muted);
      margin-top: 3px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    /* ── Lightbox ── */
    #lightbox {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,.88);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      cursor: zoom-out;
    }}
    #lightbox.open {{ display: flex; }}
    #lightbox img {{
      max-width: 92vw;
      max-height: 90vh;
      border-radius: 10px;
      box-shadow: 0 24px 60px rgba(0,0,0,.6);
    }}
    #lightbox-close {{
      position: fixed;
      top: 20px;
      right: 28px;
      color: #fff;
      font-size: 30px;
      cursor: pointer;
      z-index: 1001;
      opacity: .7;
      transition: opacity .2s;
    }}
    #lightbox-close:hover {{ opacity: 1; }}

    /* ── Toast ── */
    .toast {{
      position: fixed;
      bottom: 28px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: var(--accent-gradient);
      color: #fff;
      font-weight: 600;
      font-size: 14px;
      padding: 12px 24px;
      border-radius: 30px;
      box-shadow: 0 10px 25px rgba(99,102,241,.35);
      opacity: 0;
      transition: var(--transition);
      z-index: 100;
      pointer-events: none;
    }}
    .toast.show {{ opacity: 1; transform: translateX(-50%) translateY(0); }}

    /* ── Empty state ── */
    .empty-state {{
      text-align: center;
      padding: 60px 16px;
      color: var(--text-muted);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }}
    .empty-icon {{ font-size: 52px; animation: float 3s ease-in-out infinite; }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
    .empty-title {{ font-family:'Outfit',sans-serif; font-size:18px; color:var(--text-main); font-weight:600; }}
    .empty-desc {{ font-size:13px; max-width:280px; line-height:1.6; }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <div class="logo-container">
      <span class="logo-icon">📋</span>
      <h1>QuickClip</h1>
    </div>
    <div class="badges">
      <span class="badge" id="clip-count">{len(clips)} clips</span>
      <span class="badge green" id="shot-count">{len(shots)} screenshots</span>
    </div>
  </div>
</header>

<div class="panels">

  <!-- LEFT PANEL: Text clips -->
  <div class="panel" id="clips-panel">
    <div class="panel-title">📝 Copied Text</div>
    <div class="search-wrapper">
      <span class="search-icon">🔍</span>
      <input type="text" id="search" class="search-input"
             placeholder="Search clips..." oninput="filterClips()">
    </div>
    <div id="clips-list">
      {clip_rows if clips else empty_clips}
    </div>
  </div>

  <!-- RIGHT PANEL: Screenshots -->
  <div class="panel" id="shots-panel">
    <div class="panel-title">📸 Screenshots</div>
    <div class="shots-grid" id="shots-grid">
      {shot_rows if shots else empty_shots}
    </div>
  </div>

</div>

<!-- Lightbox for full-size screenshot -->
<div id="lightbox" onclick="closeLightbox()">
  <span id="lightbox-close" onclick="closeLightbox()">✕</span>
  <img id="lightbox-img" src="" alt="Screenshot">
</div>

<div class="toast" id="toast">✅ Copied to Clipboard!</div>

<script>
  // ── Copy clip to clipboard ─────────────────────────────────────────────────
  function copyClip(el) {{
    const text = el.getAttribute('data-text')
      .replace(/&quot;/g,'"').replace(/&#39;/g,"'")
      .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    navigator.clipboard.writeText(text).then(() => {{
      el.classList.add('copied');
      showToast('✅ Copied!');
      setTimeout(() => el.classList.remove('copied'), 1600);
    }}).catch(console.error);
  }}

  function showToast(msg) {{
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 1800);
  }}

  // ── Search / filter text clips ─────────────────────────────────────────────
  function filterClips() {{
    const q = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.clip-card').forEach(c => {{
      c.style.display = c.getAttribute('data-text').toLowerCase().includes(q) ? '' : 'none';
    }});
  }}

  // ── Lightbox for screenshots ───────────────────────────────────────────────
  function openShot(src) {{
    document.getElementById('lightbox-img').src = src;
    document.getElementById('lightbox').classList.add('open');
  }}
  function closeLightbox() {{
    document.getElementById('lightbox').classList.remove('open');
    document.getElementById('lightbox-img').src = '';
  }}
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeLightbox(); }});

  // ── Persist scroll & search across reloads ─────────────────────────────────
  window.addEventListener('beforeunload', () => {{
    localStorage.setItem('clipScroll', document.getElementById('clips-panel').scrollTop);
    localStorage.setItem('shotScroll', document.getElementById('shots-panel').scrollTop);
    localStorage.setItem('searchQ', document.getElementById('search').value);
  }});
  window.addEventListener('DOMContentLoaded', () => {{
    const q = localStorage.getItem('searchQ');
    if (q) {{ document.getElementById('search').value = q; filterClips(); }}
    const cs = localStorage.getItem('clipScroll');
    const ss = localStorage.getItem('shotScroll');
    if (cs) document.getElementById('clips-panel').scrollTop = parseInt(cs);
    if (ss) document.getElementById('shots-panel').scrollTop = parseInt(ss);
  }});

</script>
</body>
</html>"""

    p = SAVE_DIR / "viewer.html"
    p.write_text(html, encoding="utf-8")
    return str(p)
