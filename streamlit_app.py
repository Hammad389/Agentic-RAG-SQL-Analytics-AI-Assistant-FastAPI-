"""
streamlit_app.py
Place this file in the project root (next to main.py) and run:
    streamlit run streamlit_app.py

Requirements:
    pip install streamlit requests
"""

import time
import textwrap
from pathlib import Path

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
API_BASE      = "http://localhost:8000"
CHAT_URL      = f"{API_BASE}/chat/"
HEALTH_URL    = f"{API_BASE}/health/"
INDEX_URL     = f"{API_BASE}/admin/index-knowledge/"
KNOWLEDGE_DIR = Path("knowledge_base")
SCHEMA_PATH   = Path("app/domain/sql_schema_registry.py")

st.set_page_config(
    page_title="Agentic Rag Assistant",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",   # always open on first load
)

# Force sidebar open — Streamlit sometimes collapses it despite the config
st.markdown("""
<script>
(function() {
  function expandSidebar() {
    var sb = window.parent.document.querySelector('[data-testid="stSidebar"]');
    if (sb && sb.getAttribute('aria-expanded') === 'false') {
      var btn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
      if (btn) btn.click();
    }
  }
  // try immediately and after a short delay
  expandSidebar();
  setTimeout(expandSidebar, 300);
})();
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300&display=swap');

:root {
  --bg0:#0d0d0f; --bg1:#111115; --bg2:#16161c; --bg3:#1c1c24;
  --line:#1f1f28; --line2:#252530;
  --t0:#eae6e0; --t1:#b8b4ae; --t2:#737080; --t3:#3e3c48;
  --ac:#d4875a; --ac-dim:#8a4f2a; --ac-bg:#1e1510;
  --gr:#5a9e78; --gr-bg:#0d1a12;
  --re:#9e5a5a; --re-bg:#1a0d0d;
  --bl:#5a78ae; --bl-bg:#0d1220;
  --r:10px; --rs:6px;
}

*,*::before,*::after{box-sizing:border-box;}
html,body{margin:0;padding:0;}

[data-testid="stApp"],[data-testid="stAppViewContainer"],.main{
  background:var(--bg0)!important;
}
[data-testid="stMain"]>div{background:var(--bg0)!important;}
.block-container{padding:0!important;max-width:100%!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"],
[data-testid="stSidebarNav"]{display:none!important;}

[data-testid="stSidebar"]{
  background:var(--bg1)!important;
  border-right:1px solid var(--line)!important;
  min-width:280px!important;
  max-width:320px!important;
}
[data-testid="stSidebar"][aria-expanded="false"]{
  min-width:0!important;
  max-width:0!important;
}
[data-testid="stSidebarContent"]{
  padding:0!important;
  background:var(--bg1)!important;
}
[data-testid="stSidebarUserContent"]{
  padding:0!important;
}
[data-testid="collapsedControl"]{
  background:var(--bg1)!important;
  border:1px solid var(--line2)!important;
}
[data-testid="stSidebarCollapseButton"] button{
  color:var(--t2)!important;
  background:transparent!important;
}

*{scrollbar-width:thin;scrollbar-color:var(--bg3) transparent;}
::-webkit-scrollbar{width:3px;height:3px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--bg3);border-radius:2px;}

body,.stMarkdown,p,div{
  font-family:'DM Mono',monospace!important;
  font-size:13px;color:var(--t1);
}

/* ── sidebar components ── */
.s-brand{padding:22px 20px 18px;border-bottom:1px solid var(--line);}
.s-brand-name{
  font-family:'Fraunces',serif!important;font-size:20px;font-weight:300;
  color:var(--t0);letter-spacing:-0.5px;
  display:flex;align-items:center;gap:9px;
}
.s-brand-name .mk{color:var(--ac);font-size:12px;font-style:italic;}
.s-brand-sub{margin-top:4px;font-size:9.5px;color:var(--t3);
  letter-spacing:.1em;text-transform:uppercase;}

.s-status{display:flex;align-items:center;gap:7px;
  padding:10px 20px;font-size:10.5px;color:var(--t3);}
.s-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;}
.s-dot.on {background:var(--gr);box-shadow:0 0 5px var(--gr);}
.s-dot.off{background:var(--re);box-shadow:0 0 5px var(--re);}

.s-lbl{padding:14px 20px 6px;font-size:9px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--t3);font-weight:500;}

.s-filetag{margin:4px 16px;padding:9px 12px;
  background:var(--bg2);border:1px solid var(--line2);
  border-radius:var(--rs);font-size:10.5px;color:var(--t2);line-height:1.5;}
.s-filetag strong{color:var(--t0);font-weight:400;}
.s-filetag .ext{display:inline-block;padding:1px 5px;background:var(--bg3);
  border-radius:3px;font-size:9px;color:var(--t3);margin-left:4px;
  vertical-align:middle;text-transform:uppercase;}

.s-toast{margin:5px 16px;padding:9px 12px;border-radius:var(--rs);
  font-size:10.5px;line-height:1.5;}
.s-toast.ok {background:var(--gr-bg);border:1px solid #1e3d28;color:var(--gr);}
.s-toast.err{background:var(--re-bg);border:1px solid #3d1e1e;color:var(--re);}
.s-toast.inf{background:var(--bl-bg);border:1px solid #1e2a3d;color:var(--bl);}
.s-toast.wrn{background:var(--ac-bg);border:1px solid #3d2a18;color:var(--ac);}

.s-pre{margin:5px 16px;padding:10px 12px;background:var(--bg0);
  border:1px solid var(--line);border-radius:var(--rs);
  font-size:9.5px;color:var(--t3);font-family:'DM Mono',monospace!important;
  line-height:1.65;max-height:130px;overflow-y:auto;
  white-space:pre-wrap;word-break:break-word;}

.s-doc{display:flex;align-items:center;gap:8px;
  padding:5px 20px;font-size:10px;color:var(--t3);}
.s-doc::before{content:'›';color:var(--ac-dim);}

.s-stat{margin:8px 16px;padding:8px 12px;background:var(--bg0);
  border:1px solid var(--line);border-radius:var(--rs);
  display:flex;align-items:baseline;gap:6px;}
.s-stat-n{font-family:'Fraunces',serif!important;font-size:22px;
  color:var(--t2);font-weight:300;line-height:1;}
.s-stat-l{font-size:9px;color:var(--t3);
  letter-spacing:.08em;text-transform:uppercase;}

.s-footer{padding:14px 20px;font-size:9.5px;color:var(--t3);
  line-height:1.7;border-top:1px solid var(--line);}

/* ── topbar ── */
.c-topbar{padding:14px 32px;border-bottom:1px solid var(--line);
  display:flex;align-items:center;justify-content:space-between;
  background:var(--bg0);}
.c-topbar-l{font-family:'Fraunces',serif!important;font-size:15px;
  font-weight:300;color:var(--t0);letter-spacing:-0.3px;
  display:flex;align-items:center;gap:10px;}
.c-topbar-l .mk{color:var(--ac);font-style:italic;font-size:11px;}
.c-topbar-r{font-size:9.5px;color:var(--t3);
  letter-spacing:.1em;text-transform:uppercase;}

/* ── empty state ── */
.c-empty{display:flex;flex-direction:column;align-items:center;
  justify-content:center;padding:80px 40px;gap:14px;text-align:center;}
.c-empty-glyph{font-family:'Fraunces',serif!important;font-size:48px;
  font-weight:300;font-style:italic;color:var(--t3);line-height:1;}
.c-empty-title{font-family:'Fraunces',serif!important;font-size:24px;
  font-weight:300;color:var(--t2);letter-spacing:-0.5px;}
.c-empty-sub{font-size:11px;color:var(--t3);max-width:340px;line-height:1.7;}
.c-pills{display:flex;flex-wrap:wrap;justify-content:center;gap:7px;margin-top:10px;}
.c-pill{background:var(--bg1);border:1px solid var(--line2);border-radius:100px;
  padding:6px 14px;font-size:10.5px;color:var(--t2);white-space:nowrap;}

/* ── messages ── */
.msg-wrap{padding:12px 32px;display:flex;gap:14px;align-items:flex-start;
  animation:fadeUp .18s ease;border-bottom:1px solid transparent;}
.msg-wrap.user{background:transparent;}
.msg-wrap.assistant{background:var(--bg1);border-bottom:1px solid var(--line);}

@keyframes fadeUp{
  from{opacity:0;transform:translateY(5px);}
  to  {opacity:1;transform:translateY(0);}
}

.msg-av{width:26px;height:26px;border-radius:5px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:500;margin-top:1px;}
.msg-av.user{background:var(--bg3);color:var(--t3);border:1px solid var(--line2);}
.msg-av.assistant{background:var(--ac-bg);color:var(--ac);
  border:1px solid var(--ac-dim);
  font-family:'Fraunces',serif!important;font-style:italic;}

.msg-body{flex:1;min-width:0;}
.msg-name{font-size:10px;font-weight:500;letter-spacing:.05em;
  margin-bottom:7px;text-transform:uppercase;}
.msg-name.user     {color:var(--t3);}
.msg-name.assistant{color:var(--ac-dim);}

.msg-txt{font-size:13.5px;line-height:1.75;color:var(--t0);
  white-space:pre-wrap;word-break:break-word;}
.msg-txt.user{color:var(--t1);}

.msg-err{background:var(--re-bg);border:1px solid #3d1e1e;
  border-radius:var(--rs);padding:9px 13px;
  font-size:11.5px;color:var(--re);margin-top:6px;}

/* chips */
.chip-row{display:flex;flex-wrap:wrap;gap:5px;margin-top:11px;}
.chip{font-size:9px;padding:2px 7px;border-radius:3px;
  letter-spacing:.06em;text-transform:uppercase;
  font-family:'DM Mono',monospace!important;}
.chip.intent{background:var(--bl-bg);color:var(--bl);border:1px solid #1e2d48;}
.chip.plan  {background:var(--gr-bg);color:var(--gr);border:1px solid #1e3a28;}
.chip.tokens{background:var(--bg2);color:var(--t3);border:1px solid var(--line2);}

/* sql table */
.sql-wrap{margin-top:13px;border:1px solid var(--line2);
  border-radius:var(--rs);overflow:hidden;font-size:11px;}
.sql-hdr{background:var(--bg2);padding:7px 13px;font-size:9px;
  color:var(--t3);letter-spacing:.1em;text-transform:uppercase;
  border-bottom:1px solid var(--line2);display:flex;align-items:center;gap:8px;}
.sql-hdr .cnt{background:var(--bg3);border-radius:3px;
  padding:1px 6px;color:var(--t2);}
.sql-tbl{width:100%;border-collapse:collapse;background:var(--bg1);}
.sql-tbl th{padding:7px 13px;text-align:left;font-size:9.5px;color:var(--t3);
  font-weight:500;letter-spacing:.07em;text-transform:uppercase;
  border-bottom:1px solid var(--line);}
.sql-tbl td{padding:7px 13px;font-size:11px;color:var(--t1);
  border-bottom:1px solid var(--line);}
.sql-tbl tr:last-child td{border-bottom:none;}
.sql-tbl tr:hover td{background:var(--bg2);}

/* input bar */
.input-bar{padding:16px 32px 22px;border-top:1px solid var(--line);
  background:var(--bg0);}

.stTextArea textarea{
  background:var(--bg1)!important;border:1px solid var(--line2)!important;
  border-radius:var(--r)!important;color:var(--t0)!important;
  font-family:'DM Mono',monospace!important;font-size:13px!important;
  line-height:1.65!important;padding:13px 15px!important;
  resize:none!important;caret-color:var(--ac)!important;
  transition:border-color .15s!important;
}
.stTextArea textarea:focus{
  border-color:var(--ac-dim)!important;
  box-shadow:0 0 0 3px rgba(212,135,90,.08)!important;outline:none!important;
}
.stTextArea textarea::placeholder{color:var(--t3)!important;}
.stTextArea label{display:none!important;}

.stButton>button{
  background:var(--bg2)!important;border:1px solid var(--line2)!important;
  color:var(--t1)!important;font-family:'DM Mono',monospace!important;
  font-size:11px!important;letter-spacing:.04em!important;
  padding:8px 14px!important;border-radius:var(--rs)!important;
  transition:all .15s!important;width:100%!important;
}
.stButton>button:hover{
  background:var(--bg3)!important;border-color:var(--ac-dim)!important;
  color:var(--t0)!important;
}
.stButton>button:active{
  background:var(--ac-bg)!important;border-color:var(--ac)!important;
  color:var(--ac)!important;
}

.send-btn>button{
  background:var(--ac-bg)!important;border-color:var(--ac-dim)!important;
  color:var(--ac)!important;height:52px!important;font-size:16px!important;
}
.send-btn>button:hover{
  background:#281a0e!important;border-color:var(--ac)!important;
}

.newchat-btn>button{
  background:transparent!important;border-color:var(--line)!important;
  color:var(--t3)!important;
}
.newchat-btn>button:hover{
  background:var(--bg2)!important;border-color:var(--line2)!important;
  color:var(--t1)!important;
}

[data-testid="stFileUploader"]{background:transparent!important;}
[data-testid="stFileUploaderDropzone"]{
  background:var(--bg1)!important;border:1px dashed var(--line2)!important;
  border-radius:var(--rs)!important;padding:12px 10px!important;
  transition:border-color .15s!important;
}
[data-testid="stFileUploaderDropzone"]:hover{
  border-color:var(--ac-dim)!important;background:var(--ac-bg)!important;
}
[data-testid="stFileUploaderDropzone"] p{
  font-size:10px!important;color:var(--t3)!important;
  font-family:'DM Mono',monospace!important;
}
[data-testid="stFileUploaderDropzone"] small{font-size:9px!important;color:var(--t3)!important;}
[data-testid="stFileUploaderDropzone"] svg{color:var(--t3)!important;}

hr{border:none!important;border-top:1px solid var(--line)!important;margin:6px 0!important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_defaults = dict(
    messages=[],
    api_online=False,
    indexed_docs=[],
    total_chunks=0,
    schema_active=False,
    schema_name=None,
    # upload flow state
    pending_doc=None,
    pending_schema=None,
    show_index_confirm=False,
    show_schema_confirm=False,
    index_status=None,   # ("ok"|"err"|"wrn", message)
    schema_status=None,  # ("ok"|"err", message)
)
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def api_health() -> bool:
    try:
        return requests.get(HEALTH_URL, timeout=2).status_code == 200
    except Exception:
        return False


def api_chat(message: str) -> dict:
    try:
        r = requests.post(CHAT_URL, json={"message": message}, timeout=90)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        return {"success": False, "error": "Cannot reach API. Is uvicorn running on port 8000?"}
    except requests.Timeout:
        return {"success": False, "error": "Request timed out (90s)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def api_index() -> dict:
    try:
        r = requests.post(INDEX_URL, timeout=180)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        return {"status": "error", "error": "Cannot reach API."}
    except requests.Timeout:
        return {"status": "error", "error": "Indexing timed out (180s)."}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# FILE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def save_knowledge_file(uploaded) -> tuple[bool, str]:
    try:
        KNOWLEDGE_DIR.mkdir(exist_ok=True)
        dest = KNOWLEDGE_DIR / uploaded.name
        uploaded.seek(0)
        dest.write_bytes(uploaded.read())
        return True, str(dest)
    except Exception as e:
        return False, str(e)


def write_schema(content: str) -> tuple[bool, str]:
    try:
        SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEMA_PATH.write_text(content, encoding="utf-8")
        return True, ""
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# RESPONSE PARSING
# ─────────────────────────────────────────────────────────────────────────────
def extract_reply(response: dict) -> str:
    """Pull the human-readable text from any response shape the backend returns."""
    if not response.get("success"):
        return ""
    data = response.get("data")
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        mode = data.get("mode")
        if mode in ("table", "simple", "empty"):
            return data.get("summary", "")
        return data.get("message", "")
    return str(data)


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE RENDERER
# ─────────────────────────────────────────────────────────────────────────────
def render_message(msg: dict):
    role    = msg["role"]
    content = msg["content"]
    meta    = msg.get("meta", {})
    is_err  = msg.get("is_error", False)

    avatar = "You" if role == "user" else "✦"
    name   = "You" if role == "user" else "Agentic Rag"

    if role == "user":
        body = f'<div class="msg-txt user">{content}</div>'
    elif is_err:
        body = f'<div class="msg-err">⚠ {content}</div>'
    else:
        body = f'<div class="msg-txt">{content}</div>'

        # SQL table
        data = meta.get("data") or {}
        if isinstance(data, dict) and data.get("mode") in ("table", "simple"):
            rows = data.get("rows", [])
            if rows:
                cols = list(rows[0].keys())
                th_html = "".join(f"<th>{c.replace('_',' ')}</th>" for c in cols)
                tr_html = ""
                for row in rows:
                    tds = "".join(f"<td>{row.get(c,'–')}</td>" for c in cols)
                    tr_html += f"<tr>{tds}</tr>"
                cnt = data.get("row_count", len(rows))
                body += f"""
                <div class="sql-wrap">
                  <div class="sql-hdr">
                    SQL Result
                    <span class="cnt">{cnt} row{"s" if cnt!=1 else ""}</span>
                  </div>
                  <table class="sql-tbl">
                    <thead><tr>{th_html}</tr></thead>
                    <tbody>{tr_html}</tbody>
                  </table>
                </div>"""

        # Chips
        chips = ""
        for i in (meta.get("intents") or []):
            chips += f'<span class="chip intent">{i}</span>'
        for p in (meta.get("execution_plan") or []):
            chips += f'<span class="chip plan">{p}</span>'
        tok = (meta.get("usage") or {}).get("total_tokens", 0)
        if tok:
            chips += f'<span class="chip tokens">{tok} tok</span>'
        if chips:
            body += f'<div class="chip-row">{chips}</div>'

    st.markdown(f"""
    <div class="msg-wrap {role}">
      <div class="msg-av {role}">{avatar}</div>
      <div class="msg-body">
        <div class="msg-name {role}">{name}</div>
        {body}
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────
st.session_state.api_online = api_health()


# ═════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # Brand
    st.markdown("""
    <div class="s-brand">
      <div class="s-brand-name"><span class="mk">✦</span> Agentic Rag</div>
      <div class="s-brand-sub">Agentic RAG · FastAPI</div>
    </div>
    """, unsafe_allow_html=True)

    # Status
    dot  = "on" if st.session_state.api_online else "off"
    stxt = "API online" if st.session_state.api_online else "API offline — start uvicorn"
    st.markdown(f'<div class="s-status"><div class="s-dot {dot}"></div><span>{stxt}</span></div>',
                unsafe_allow_html=True)

    # New chat
    st.markdown('<div class="newchat-btn">', unsafe_allow_html=True)
    if st.button("+ New conversation", key="new_chat"):
        for k in ("messages","pending_doc","pending_schema",
                  "show_index_confirm","show_schema_confirm",
                  "index_status","schema_status"):
            st.session_state[k] = [] if k == "messages" else None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────
    #  KNOWLEDGE BASE
    # ─────────────────────────────────────────────────
    st.markdown('<div class="s-lbl">Knowledge Base</div>', unsafe_allow_html=True)

    doc_file = st.file_uploader(
        "doc", type=["pdf","md","txt","json"],
        key="doc_uploader", label_visibility="collapsed",
    )

    # Detect new upload → read bytes immediately (Streamlit invalidates
    # the file object on the next rerun, so we must store bytes now)
    if doc_file is not None:
        cached = st.session_state.pending_doc
        if cached is None or cached.get("name") != doc_file.name:
            doc_file.seek(0)
            doc_bytes = doc_file.read()          # read now, before any rerun
            st.session_state.pending_doc = {
                "name":  doc_file.name,
                "size":  doc_file.size,
                "ext":   Path(doc_file.name).suffix.upper().lstrip("."),
                "bytes": doc_bytes,              # store bytes, not the object
            }
            st.session_state.show_index_confirm = True
            st.session_state.index_status = None

    # Confirm banner + buttons
    if st.session_state.show_index_confirm and st.session_state.pending_doc:
        pd = st.session_state.pending_doc
        kb = max(1, pd["size"] // 1024)
        st.markdown(f"""
        <div class="s-filetag">
          <strong>{pd['name']}</strong><span class="ext">{pd['ext']}</span><br>
          {kb} KB · Save to <code>knowledge_base/</code> and index?
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Index →", key="btn_idx"):
                # Write bytes directly — no live file object needed
                try:
                    KNOWLEDGE_DIR.mkdir(exist_ok=True)
                    dest = KNOWLEDGE_DIR / pd["name"]
                    dest.write_bytes(pd["bytes"])
                    ok, err_msg = True, ""
                except Exception as e:
                    ok, err_msg = False, str(e)

                if not ok:
                    st.session_state.index_status = ("err", f"Save failed: {err_msg}")
                else:
                    with st.spinner("Embedding chunks…"):
                        res = api_index()
                    if res.get("status") == "success":
                        n = res.get("indexed", 0)
                        st.session_state.total_chunks += n
                        if pd["name"] not in st.session_state.indexed_docs:
                            st.session_state.indexed_docs.append(pd["name"])
                        st.session_state.index_status = ("ok", f"✓ {n} chunks indexed")
                        st.session_state.show_index_confirm = False
                        st.session_state.pending_doc = None
                    elif res.get("status") == "no_documents_found":
                        st.session_state.index_status = ("wrn", "No documents found in knowledge_base/")
                    else:
                        e = res.get("error", res.get("status", "unknown"))
                        st.session_state.index_status = ("err", e)
                st.rerun()
        with c2:
            if st.button("Cancel", key="btn_idx_cancel"):
                st.session_state.show_index_confirm = False
                st.session_state.pending_doc = None
                st.session_state.index_status = None
                st.rerun()

    # Status toast (persists after confirm closes)
    if st.session_state.index_status:
        kind, msg = st.session_state.index_status
        st.markdown(f'<div class="s-toast {kind}">{msg}</div>', unsafe_allow_html=True)

    # Indexed list
    if st.session_state.indexed_docs:
        for d in st.session_state.indexed_docs[-6:]:
            label = d if len(d) <= 28 else d[:25]+"…"
            st.markdown(f'<div class="s-doc">{label}</div>', unsafe_allow_html=True)
        if st.session_state.total_chunks:
            st.markdown(f"""
            <div class="s-stat">
              <span class="s-stat-n">{st.session_state.total_chunks}</span>
              <span class="s-stat-l">chunks in vector DB</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="s-doc" style="font-style:italic;color:var(--t3)">No documents indexed</div>',
                    unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────
    #  SQL SCHEMA
    # ─────────────────────────────────────────────────
    st.markdown('<div class="s-lbl">SQL Schema</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 16px 8px;font-size:9.5px;color:var(--t3);line-height:1.6;">
      Upload a <code>sql_schema_registry.py</code> to replace the active
      schema. The SQL agent uses it for query generation.
    </div>""", unsafe_allow_html=True)

    schema_file = st.file_uploader(
        "schema", type=["py","txt","sql"],
        key="schema_uploader", label_visibility="collapsed",
    )

    if schema_file is not None:
        cached_s = st.session_state.pending_schema
        if cached_s is None or cached_s.get("name") != schema_file.name:
            schema_file.seek(0)
            raw = schema_file.read()
            st.session_state.pending_schema = {
                "name":    schema_file.name,
                "size":    schema_file.size,
                "content": raw.decode("utf-8", errors="replace"),
            }
            st.session_state.show_schema_confirm = True
            st.session_state.schema_status = None

    if st.session_state.show_schema_confirm and st.session_state.pending_schema:
        ps = st.session_state.pending_schema
        kb = max(1, ps["size"] // 1024)
        ext = Path(ps["name"]).suffix.upper().lstrip(".")
        preview = textwrap.shorten(ps["content"], width=360, placeholder="…")

        st.markdown(f"""
        <div class="s-filetag">
          <strong>{ps['name']}</strong><span class="ext">{ext}</span><br>
          {kb} KB · Will overwrite <code>app/domain/sql_schema_registry.py</code>
        </div>
        <div class="s-pre">{preview}</div>
        <div class="s-toast wrn" style="margin-top:5px;">
          ⚠ Restart uvicorn after applying for changes to take effect.
        </div>""", unsafe_allow_html=True)

        cs1, cs2 = st.columns(2)
        with cs1:
            if st.button("Apply →", key="btn_schema"):
                ok, err_msg = write_schema(ps["content"])
                if ok:
                    st.session_state.schema_active = True
                    st.session_state.schema_name   = ps["name"]
                    st.session_state.schema_status = ("ok", "✓ Schema written to disk")
                    st.session_state.show_schema_confirm = False
                    st.session_state.pending_schema = None
                else:
                    st.session_state.schema_status = ("err", f"Write failed: {err_msg}")
                st.rerun()
        with cs2:
            if st.button("Cancel", key="btn_schema_cancel"):
                st.session_state.show_schema_confirm = False
                st.session_state.pending_schema = None
                st.session_state.schema_status = None
                st.rerun()

    if st.session_state.schema_status:
        kind, msg = st.session_state.schema_status
        st.markdown(f'<div class="s-toast {kind}">{msg}</div>', unsafe_allow_html=True)

    if st.session_state.schema_active and st.session_state.schema_name:
        label = st.session_state.schema_name
        if len(label) > 26:
            label = label[:23]+"…"
        st.markdown(f'<div class="s-doc">Active: {label}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="s-doc" style="font-style:italic;color:var(--t3)">Default schema</div>',
                    unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div class="s-footer">
      Ask in plain English.<br>
      RAG → platform questions.<br>
      SQL → analytics queries.
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN CHAT
# ═════════════════════════════════════════════════════════════════════════════

# Topbar
turns = len([m for m in st.session_state.messages if m["role"] == "user"])
st.markdown(f"""
<div class="c-topbar">
  <div class="c-topbar-l"><span class="mk">✦</span>Agentic AI Assistant</div>
  <div class="c-topbar-r">
    {"ONLINE" if st.session_state.api_online else "OFFLINE"}
    &nbsp;·&nbsp;
    {turns} turn{"s" if turns!=1 else ""}
  </div>
</div>
""", unsafe_allow_html=True)

# Messages or empty state
if not st.session_state.messages:
    st.markdown("""
    <div class="c-empty">
      <div class="c-empty-glyph">✦</div>
      <div class="c-empty-title">How can I help?</div>
      <div class="c-empty-sub">
        Ask about the platform, navigate to any screen,
        or query your data in plain English.
      </div>
      <div class="c-pills">
        <div class="c-pill">How does task assignment work?</div>
        <div class="c-pill">How many tasks are overdue?</div>
        <div class="c-pill">Where is the notifications page?</div>
        <div class="c-pill">Show me project statistics</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        render_message(msg)

# Input bar
st.markdown('<div class="input-bar">', unsafe_allow_html=True)
col_txt, col_btn = st.columns([11, 1])

with col_txt:
    user_input = st.text_area(
        "msg", key="chat_input",
        placeholder="Message ",
        height=52, label_visibility="collapsed",
    )

with col_btn:
    st.markdown('<div class="send-btn">', unsafe_allow_html=True)
    send_clicked = st.button("↑", key="send_btn")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Handle send
if send_clicked and user_input and user_input.strip():
    text = user_input.strip()
    st.session_state.messages.append({"role": "user", "content": text, "meta": {}})

    if not st.session_state.api_online:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Cannot reach the API server. Make sure uvicorn is running on port 8000.",
            "meta": {}, "is_error": True,
        })
    else:
        with st.spinner(""):
            resp = api_chat(text)

        if resp.get("success"):
            reply = extract_reply(resp)
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply or "I couldn't generate a response for that.",
                "meta": {
                    "intents":        resp.get("intent"),
                    "execution_plan": resp.get("execution_plan"),
                    "usage":          resp.get("usage"),
                    "data":           resp.get("data"),
                },
            })
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": resp.get("error", "An unexpected error occurred."),
                "meta": {}, "is_error": True,
            })

    st.rerun()