import streamlit as st
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="Smart Email Assistant", page_icon="📧", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: #07090f;
    --card: #0e1120;
    --card2: #131726;
    --accent: #5b8dee;
    --accent2: #7c3aed;
    --text: #dde2f0;
    --muted: #6b7a9e;
    --border: rgba(91,141,238,0.15);
}

html, body, .stApp {
    background-color: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text) !important;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 70% 50% at 15% 10%, rgba(91,141,238,0.09) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 85% 85%, rgba(124,58,237,0.09) 0%, transparent 55%),
        radial-gradient(ellipse 50% 40% at 55% 25%, rgba(6,214,160,0.05) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: "";
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(91,141,238,0.07) 1px, transparent 1px);
    background-size: 30px 30px;
    pointer-events: none;
    z-index: 0;
}

section.main > div { position: relative; z-index: 1; }
.block-container { padding-top: 2rem !important; max-width: 1100px !important; }

[data-testid="stSidebar"] { background: #060810 !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text) !important; }

h1,h2,h3 { color: var(--text) !important; }

.stTextArea textarea, .stTextInput input {
    background-color: var(--card2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: 14px !important;
}

label, p, li, span, div { color: var(--text) !important; }

.stSelectbox > div > div {
    background-color: var(--card2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 0.55rem 1.4rem !important;
    width: 100%;
    transition: transform .15s !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; }

.stDownloadButton > button {
    background: var(--card2) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    width: auto !important;
}

[data-baseweb="tab-list"] {
    background: var(--card) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border-bottom: none !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: var(--accent) !important;
    color: #fff !important;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
    color: var(--text) !important;
    line-height: 1.8;
    font-size: 14px;
    white-space: pre-wrap;
}

.stSuccess, .stInfo, .stWarning {
    background: var(--card2) !important;
    border-radius: 10px !important;
}

.stCode pre, code {
    background: #060810 !important;
    color: #7ee8a2 !important;
    border-radius: 8px !important;
}

[data-testid="stMetric"] { background: var(--card) !important; border-radius: 12px !important; padding: 12px !important; }
[data-testid="stMetricValue"] { color: var(--accent) !important; font-weight: 700 !important; }
[data-testid="stFileUploader"] {
    background: var(--card2) !important;
    border: 1.5px dashed var(--accent) !important;
    border-radius: 12px !important;
}
.stDataFrame { background: var(--card) !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DETECT EMAIL TYPE
# ─────────────────────────────────────────────

def detect_type(email: str) -> str:
    e = email.lower()
    if any(w in e for w in ["meeting", "schedule", "calendar", "appointment", "call"]):
        return "Meeting"
    elif any(w in e for w in ["complaint", "issue", "problem", "delay", "refund", "sorry", "escalate", "disappointed", "frustrated"]):
        return "Complaint"
    elif any(w in e for w in ["request", "please send", "could you", "kindly", "need", "require", "asking", "wanted to ask"]):
        return "Request"
    elif any(w in e for w in ["offer", "proposal", "partnership", "collaborate", "opportunity", "pitch", "interested in"]):
        return "Proposal"
    elif any(w in e for w in ["follow up", "following up", "update", "status", "any news", "check in", "just checking"]):
        return "Follow-Up"
    elif any(w in e for w in ["invoice", "payment", "billing", "due", "overdue", "receipt", "transaction"]):
        return "Invoice/Payment"
    elif any(w in e for w in ["interview", "job", "position", "application", "resume", "cv", "hire", "candidate"]):
        return "Job/Interview"
    else:
        return "General"


# ─────────────────────────────────────────────
# EXTRACT KEY DETAILS FROM EMAIL
# ─────────────────────────────────────────────

def extract_key_details(email: str) -> dict:
    details = {}
    name_match = re.search(r"(?:hi|hello|dear|hey)\s+([A-Z][a-z]+)", email, re.IGNORECASE)
    details["sender_name"] = name_match.group(1) if name_match else None
    date_match = re.search(
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+\w+|\w+\s+\d{1,2}(?:st|nd|rd|th)?|monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|today)\b",
        email, re.IGNORECASE
    )
    details["date_ref"] = date_match.group(0) if date_match else None
    topic_match = re.search(
        r"(?:about|regarding|re:|concerning|related to)\s+(?:the\s+)?([a-zA-Z\s]{3,30}?)(?:\.|,|\n|$)",
        email, re.IGNORECASE
    )
    details["topic"] = topic_match.group(1).strip() if topic_match else None
    number_match = re.search(r"(?:₹|rs\.?|inr|usd|\$|€|£)?\s*[\d,]+(?:\.\d+)?", email, re.IGNORECASE)
    details["amount"] = number_match.group(0).strip() if number_match else None
    return details


# ─────────────────────────────────────────────
# REPLY TEMPLATES
# ─────────────────────────────────────────────

REPLY_TEMPLATES = {
    "Meeting": [{
        "Formal": [
            "Dear {name},\n\nThank you for reaching out regarding {topic}. I have reviewed your message and would like to confirm my availability for the proposed {date}.\n\nPlease find my calendar details attached, and do let me know if the timing requires any adjustment. I look forward to a productive discussion.\n\nYours sincerely,",
            "Dear {name},\n\nI appreciate you taking the time to write. With reference to the meeting you proposed{date_str}, I am pleased to confirm my participation.\n\nKindly share the agenda in advance so I may prepare accordingly. I trust we will make the most of our time together.\n\nRespectfully,",
            "Dear {name},\n\nThank you for the meeting invitation. I have noted the details and will ensure all relevant stakeholders are briefed prior to our scheduled discussion{date_str}.\n\nShould there be any preparatory material you wish to share, please do not hesitate to forward it.\n\nWith regards,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for reaching out about {topic}. I've reviewed the details and can confirm my availability{date_str}.\n\nCould you share a calendar invite along with any agenda items? Looking forward to connecting.\n\nBest regards,",
            "Hi {name},\n\nAppreciate you getting in touch. The meeting{date_str} works well for me — I'll block my calendar accordingly.\n\nPlease do share any pre-read material if available.\n\nKind regards,",
            "Hello {name},\n\nThanks for the heads-up on {topic}. I'm available{date_str} and will come prepared with the relevant updates.\n\nFeel free to send over an agenda. See you then.\n\nBest,",
        ],
        "Friendly": [
            "Hey {name}!\n\nSounds good — {topic} is definitely worth discussing! I'm free{date_str}, so let's make it happen.\n\nJust drop a calendar invite and we're all set!\n\nCheers,",
            "Hi {name}!\n\nAbsolutely, let's meet{date_str}! I've been looking forward to chatting about {topic} anyway.\n\nSend over a meeting link and I'll be there!\n\nTalk soon,",
            "Hey {name}!\n\nPerfect timing — I'm totally free{date_str}. Shoot me a calendar invite and let's get this sorted!\n\nCheers,",
        ],
    }],
    "Complaint": [{
        "Formal": [
            "Dear {name},\n\nI sincerely regret the inconvenience this matter has caused you. Please be assured that your concern regarding {topic} has been escalated to the appropriate team and is being treated with the utmost priority.\n\nWe aim to resolve this within 24 to 48 business hours and will keep you informed of all developments.\n\nYours faithfully,",
            "Dear {name},\n\nThank you for bringing this matter to our attention. I unreservedly apologise for the experience you have encountered{date_str}. Such lapses fall far below the standards we hold ourselves to.\n\nA dedicated case has been raised and our team will contact you directly with a resolution.\n\nRespectfully,",
            "Dear {name},\n\nWe have received your complaint concerning {topic} and I want to personally assure you that this is being investigated as a matter of urgency.\n\nYou will receive a comprehensive response within two business days.\n\nWith sincere apologies,",
        ],
        "Professional": [
            "Hello {name},\n\nThank you for flagging this — I'm sorry to hear about the issue with {topic}. This isn't the experience we want for you.\n\nI've escalated this to the relevant team and we'll have an update within 48 hours.\n\nBest regards,",
            "Hi {name},\n\nI appreciate you reaching out and I apologise for the trouble caused{date_str}. Your concern has been noted and is being reviewed.\n\nWe'll be in touch shortly with a resolution.\n\nKind regards,",
            "Hello {name},\n\nSorry for the inconvenience around {topic}. I've logged your concern and our team is already looking into it.\n\nExpect a follow-up within 24 hours.\n\nBest,",
        ],
        "Friendly": [
            "Hey {name},\n\nOh no — I'm really sorry to hear that! That definitely shouldn't have happened and I completely understand your frustration.\n\nI'm on it right now and will get back to you with a fix as soon as possible!\n\nSorry again,",
            "Hi {name},\n\nI'm so sorry about {topic}! That's totally on us and not okay at all.\n\nLet me sort this out for you right away. I'll come back to you very soon!\n\nApologies,",
            "Hey {name}!\n\nFirst — I'm so sorry! I want to fix this for you immediately and I'm jumping on it right now.\n\nThanks for being so understanding!\n\nSorry!",
        ],
    }],
    "Request": [{
        "Formal": [
            "Dear {name},\n\nThank you for submitting your request regarding {topic}. I have reviewed the details and will begin compiling the necessary information forthwith.\n\nYou may expect a comprehensive response{date_str}. Should you require any clarification in the interim, please do not hesitate to contact me.\n\nYours sincerely,",
            "Dear {name},\n\nI acknowledge receipt of your request and wish to confirm that it is receiving my immediate attention. The information pertaining to {topic} will be collated and forwarded to you at the earliest opportunity.\n\nRespectfully,",
            "Dear {name},\n\nYour request has been duly noted and I am pleased to assist you with {topic}. I will coordinate with the relevant parties to ensure accuracy and completeness.\n\nKindly allow me until{date_str} to revert with the required details.\n\nWith regards,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for your request — happy to help with {topic}. I'll gather what you need and get back to you{date_str}.\n\nLet me know if there's anything specific to prioritise.\n\nBest regards,",
            "Hi {name},\n\nReceived your request regarding {topic} — noted and in progress. I'll have everything ready shortly.\n\nKind regards,",
            "Hello {name},\n\nAppreciate you reaching out about {topic}. I'm on it and will send the details as soon as they're ready{date_str}.\n\nBest,",
        ],
        "Friendly": [
            "Hey {name}!\n\nOf course — happy to help with {topic}! I'll get that sorted and send it over{date_str}.\n\nJust holler if you need anything else!\n\nCheers,",
            "Hi {name}!\n\nOn it! I'll pull everything together for {topic} and have it with you very soon!\n\nTalk soon,",
            "Hey {name}!\n\nAbsolutely, no problem! {topic} — consider it done. I'll send it across{date_str}!\n\nCheers,",
        ],
    }],
    "Proposal": [{
        "Formal": [
            "Dear {name},\n\nThank you for presenting this proposal regarding {topic}. I have reviewed the submission with considerable interest and believe there is merit in exploring this further.\n\nI would welcome the opportunity to schedule a formal discussion{date_str} to evaluate the specifics.\n\nYours sincerely,",
            "Dear {name},\n\nI am grateful for the detailed proposal you have shared concerning {topic}. After an initial review, I find the proposition promising and worth deliberating upon.\n\nI suggest we convene{date_str} to discuss the finer details and chart a path forward.\n\nRespectfully,",
            "Dear {name},\n\nThank you for the well-considered proposal on {topic}. The outlined scope aligns with several of our current strategic priorities.\n\nKindly confirm your availability for a detailed discussion at the earliest mutual convenience.\n\nWith regards,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for sharing this proposal on {topic} — I've had a look and see real potential here.\n\nCould we set up a call{date_str} to discuss next steps?\n\nBest regards,",
            "Hi {name},\n\nAppreciate you putting this together regarding {topic}. There are some compelling elements here that align with what we're working on.\n\nLet's schedule some time — are you free{date_str}?\n\nKind regards,",
            "Hello {name},\n\nThanks for the proposal — {topic} looks promising. Can we connect{date_str} for a more in-depth discussion?\n\nBest,",
        ],
        "Friendly": [
            "Hey {name}!\n\nWow, this is exciting! I've read through your proposal on {topic} and I'm genuinely impressed.\n\nLet's definitely chat{date_str} — I'd love to explore what we could do together!\n\nCheers,",
            "Hi {name}!\n\nThis is really cool! The {topic} proposal is super interesting.\n\nLet's grab a call{date_str} and dig into the details!\n\nTalk soon,",
            "Hey {name}!\n\nLove this idea around {topic}! I'm definitely interested — let's set something up{date_str}!\n\nCheers,",
        ],
    }],
    "Follow-Up": [{
        "Formal": [
            "Dear {name},\n\nThank you for your follow-up on {topic}. I apologise for any delay in my response and appreciate your continued patience.\n\nThe matter is currently being addressed and you will receive a comprehensive update{date_str}.\n\nYours sincerely,",
            "Dear {name},\n\nI acknowledge your follow-up and sincerely regret any inconvenience caused by the delay. The status of {topic} is being reviewed and I will revert at the earliest.\n\nRespectfully,",
            "Dear {name},\n\nThank you for following up regarding {topic}. I wish to assure you that this is being handled with priority and a detailed update will be shared{date_str}.\n\nWith regards,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for following up on {topic} — apologies for the delay. You'll have a full update{date_str}.\n\nBest regards,",
            "Hi {name},\n\nGood to hear from you. The {topic} matter is progressing and I'll send a proper update very shortly.\n\nKind regards,",
            "Hello {name},\n\nThanks for checking in on {topic}. I have an update almost ready and will share it{date_str}.\n\nBest,",
        ],
        "Friendly": [
            "Hey {name}!\n\nThanks for the nudge on {topic} — my bad for keeping you waiting! Update coming very soon!\n\nCheers,",
            "Hi {name}!\n\nSorry for the silence on {topic}! I haven't forgotten — update coming your way{date_str}!\n\nTalk soon,",
            "Hey {name}!\n\nOops — sorry for the delay! I'm on it now and you'll hear from me very soon!\n\nCheers,",
        ],
    }],
    "Invoice/Payment": [{
        "Formal": [
            "Dear {name},\n\nThank you for your message regarding the payment of {amount}. I confirm that the relevant details have been noted and the transaction will be processed within the stipulated timeframe.\n\nYours sincerely,",
            "Dear {name},\n\nI acknowledge receipt of your invoice communication. The amount of {amount} has been duly noted and will be processed in accordance with our standard payment terms.\n\nRespectfully,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for reaching out about the payment of {amount}. I've noted the details and will ensure it's processed promptly.\n\nBest regards,",
            "Hi {name},\n\nAcknowledged — the invoice for {amount} is being reviewed and will be actioned shortly.\n\nKind regards,",
        ],
        "Friendly": [
            "Hey {name}!\n\nGot it — the {amount} payment is on my radar and I'll get it sorted very soon!\n\nCheers,",
            "Hi {name}!\n\nThanks for flagging the {amount} payment! I'm on it!\n\nTalk soon,",
        ],
    }],
    "Job/Interview": [{
        "Formal": [
            "Dear {name},\n\nThank you for your interest in the position and for reaching out regarding {topic}. I have reviewed your message and would like to proceed with the next steps of our selection process.\n\nWe will be in touch{date_str} to schedule a formal interview.\n\nYours sincerely,",
            "Dear {name},\n\nI am grateful for your application. After reviewing your profile, I am pleased to invite you to discuss {topic} further{date_str}.\n\nPlease confirm your availability at the earliest.\n\nRespectfully,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for reaching out about the {topic} opportunity. We've reviewed your details and would love to schedule a conversation{date_str}.\n\nBest regards,",
            "Hi {name},\n\nAppreciate your interest in {topic}. We'd like to set up an interview{date_str} — please share your availability.\n\nKind regards,",
        ],
        "Friendly": [
            "Hey {name}!\n\nSo glad you reached out about {topic}! Your background looks really exciting.\n\nLet's set up a chat{date_str}!\n\nCheers,",
            "Hi {name}!\n\nThanks for applying for {topic}! We're very interested and would love to talk{date_str}!\n\nTalk soon,",
        ],
    }],
    "General": [{
        "Formal": [
            "Dear {name},\n\nThank you for your correspondence. I have carefully read your message and will ensure a thorough and timely response.\n\nPlease be assured that your query is being given due consideration.\n\nYours sincerely,",
            "Dear {name},\n\nI acknowledge receipt of your message and wish to express my appreciation for reaching out. The matter you have raised is being reviewed and I will respond in full{date_str}.\n\nRespectfully,",
            "Dear {name},\n\nThank you for getting in touch. I have noted the contents of your message and will provide a comprehensive reply upon reviewing the relevant details.\n\nWith regards,",
        ],
        "Professional": [
            "Hello {name},\n\nThanks for reaching out. I've read through your message and will get back to you{date_str}.\n\nBest regards,",
            "Hi {name},\n\nGot your message — thanks for writing in. I'll look into this and come back to you shortly.\n\nKind regards,",
            "Hello {name},\n\nThanks for your email. I'll review the details and respond properly{date_str}.\n\nBest,",
        ],
        "Friendly": [
            "Hey {name}!\n\nThanks so much for reaching out! I'll get back to you very soon with everything you need.\n\nCheers,",
            "Hi {name}!\n\nSo glad you wrote in! I'll send you a proper reply shortly. Stay tuned!\n\nTalk soon,",
            "Hey {name}!\n\nGot your message — I'll sort this out and get back to you in no time!\n\nCheers,",
        ],
    }],
}


# ─────────────────────────────────────────────
# BUILD REPLY
# ─────────────────────────────────────────────

def build_reply(email: str, tone: str, length: str, variant: int) -> str:
    email_type     = detect_type(email)
    details        = extract_key_details(email)
    name           = details.get("sender_name") or "there"
    topic          = details.get("topic") or "this matter"
    amount         = details.get("amount") or "the amount"
    date_ref       = details.get("date_ref")
    date_str       = f" on {date_ref}" if date_ref else ""
    templates      = REPLY_TEMPLATES.get(email_type, REPLY_TEMPLATES["General"])
    tone_templates = templates[0].get(tone, templates[0]["Professional"])
    idx            = variant % len(tone_templates)
    body           = tone_templates[idx]

    body = body.replace("{name}", name)
    body = body.replace("{topic}", topic)
    body = body.replace("{amount}", amount)
    body = body.replace("{date_str}", date_str)
    body = body.replace("{date}", date_ref or "the proposed time")

    if length == "Medium":
        extras = {
            "Meeting":         "\n\nPlease also let me know if there is any documentation or agenda you would like me to review before we connect.",
            "Complaint":       "\n\nI want to personally assure you that steps are being taken to prevent a recurrence of this issue.",
            "Request":         "\n\nIf there is any additional context that would help me address your request more precisely, do feel free to share it.",
            "Proposal":        "\n\nI would also appreciate receiving any supporting data or case studies that might help us evaluate the proposal thoroughly.",
            "Follow-Up":       "\n\nI apologise once more for any inconvenience the delay may have caused and appreciate your continued understanding.",
            "Invoice/Payment": "\n\nPlease ensure the bank details on file are current, and do reach out if any discrepancy arises.",
            "Job/Interview":   "\n\nPlease bring any portfolio materials or references that would support our conversation.",
            "General":         "\n\nDo not hesitate to reach out should you require any further assistance in the meantime.",
        }
        body += extras.get(email_type, "")

    elif length == "Long":
        body += (
            "\n\nI want to take this opportunity to assure you that your communication is valued and that we are committed to delivering the highest quality of service in every interaction. "
            "Our team is fully dedicated to ensuring that all matters are handled with care, diligence, and a genuine commitment to your satisfaction."
            "\n\nShould you have any further questions, concerns, or additional requirements, please do not hesitate to contact me directly. "
            "I remain at your disposal and look forward to a continued and productive relationship."
        )

    return body


# ─────────────────────────────────────────────
# IMPROVE DRAFT — full rewrite, no API needed
# ─────────────────────────────────────────────

def improve_draft(text: str) -> str:
    original = text.strip()
    cleaned  = original

    # ── Step 1: fix contractions ──
    contraction_fixes = {
        r"\bi\b": "I", r"\bdont\b": "don't", r"\bcant\b": "can't",
        r"\bwont\b": "won't", r"\bisnt\b": "isn't", r"\barent\b": "aren't",
        r"\bwasnt\b": "wasn't", r"\bwerent\b": "weren't", r"\bim\b": "I'm",
        r"\bive\b": "I've", r"\bill\b": "I'll", r"\bhasnt\b": "hasn't",
        r"\bhadnt\b": "hadn't", r"\bwouldnt\b": "wouldn't",
        r"\bcouldnt\b": "couldn't", r"\bshouldnt\b": "shouldn't",
        r"\bthats\b": "that's", r"\bwhats\b": "what's",
        r"\bweve\b": "we've", r"\btheyre\b": "they're", r"\btheyll\b": "they'll",
        r"\byoure\b": "you're", r"\byoull\b": "you'll", r"\byouve\b": "you've",
        r"\bhes\b": "he's", r"\bshes\b": "she's", r"\bwere\b": "we're",
    }
    for pat, rep in contraction_fixes.items():
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    # ── Step 2: upgrade weak / casual vocabulary ──
    word_upgrades = [
        (r"\bwanted to ask\b",         "I am writing to enquire"),
        (r"\bwanted to\b",             "I would like to"),
        (r"\bjust wanted\b",           "I wanted to"),
        (r"\bgot your\b",              "received your"),
        (r"\bgot\b",                   "received"),
        (r"\bsorry for\b",             "I apologise for"),
        (r"\bsorry about\b",           "I apologise for"),
        (r"\bso sorry\b",              "sincerely apologise"),
        (r"\bthanks a lot\b",          "thank you very much"),
        (r"\bthanks\b",                "thank you"),
        (r"\bstuff\b",                 "matters"),
        (r"\bthings\b",                "matters"),
        (r"\bget back to you\b",       "revert to you"),
        (r"\bget back\b",              "respond"),
        (r"\bASAP\b",                  "at the earliest convenience"),
        (r"\bas soon as possible\b",   "at the earliest convenience"),
        (r"\bcheck\b",                 "review"),
        (r"\blook into\b",             "investigate"),
        (r"\bfind out\b",              "ascertain"),
        (r"\btell me\b",               "kindly inform me"),
        (r"\blet me know\b",           "please do inform me"),
        (r"\bsend me\b",               "kindly forward"),
        (r"\bsend over\b",             "kindly share"),
        (r"\bneed\b",                  "require"),
        (r"\buse\b",                   "utilise"),
        (r"\bshow\b",                  "demonstrate"),
        (r"\bstart\b",                 "commence"),
        (r"\bend\b",                   "conclude"),
        (r"\bhelp\b",                  "assist"),
        (r"\bfix\b",                   "resolve"),
        (r"\bbusy\b",                  "occupied with other commitments"),
        (r"\bproblem\b",               "concern"),
        (r"\bissue\b",                 "matter"),
        (r"\bstill waiting\b",         "yet to receive a response"),
        (r"\bno reply\b",              "not received a response"),
        (r"\bnobody replied\b",        "no response has been received"),
        (r"\bno one replied\b",        "no response has been received"),
        (r"\bpls\b",                   "please"),
        (r"\bplz\b",                   "please"),
        (r"\bu\b",                     "you"),
        (r"\br\b",                     "are"),
        (r"\bbtw\b",                   "by the way"),
        (r"\bfyi\b",                   "for your information"),
        (r"\basap\b",                  "at the earliest convenience"),
        (r"\bkindly do the needful\b", "kindly take the necessary action"),
        (r"\bdo the needful\b",        "take the necessary action"),
        (r"\brevert back\b",           "revert"),
        (r"\bfrustrated\b",            "concerned"),
        (r"\bannoyed\b",               "concerned"),
        (r"\bupset\b",                 "concerned"),
        (r"\bwaiting\b",               "awaiting a response"),
        (r"\b2 weeks\b",               "two weeks"),
        (r"\b2 days\b",                "two days"),
        (r"\b3 days\b",                "three days"),
    ]
    for pat, rep in word_upgrades:
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    # ── Step 3: clean up sentences ──
    sentences = re.split(r'(?<=[.!?])\s+', cleaned.strip())
    polished  = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        if s[-1] not in ".!?":
            s += "."
        polished.append(s)
    middle = " ".join(polished)

    # ── Step 4: detect intent and pick opening + closing ──
    intent   = detect_type(original)
    openings = {
        "Meeting":         "I am writing with reference to the meeting we discussed.",
        "Complaint":       "I am writing to bring an important concern to your attention.",
        "Request":         "I am writing to formally request your assistance with the following matter.",
        "Proposal":        "I am pleased to present the following for your kind consideration.",
        "Follow-Up":       "I am writing to follow up on my previous communication.",
        "Invoice/Payment": "I am writing regarding the pending payment matter.",
        "Job/Interview":   "I am writing in connection with the position we discussed.",
        "General":         "I am writing to bring the following matter to your attention.",
    }
    closings = {
        "Meeting":         "I look forward to a productive discussion and will ensure I am well prepared for our meeting.",
        "Complaint":       "I trust this matter will be addressed promptly and look forward to your earliest response.",
        "Request":         "I would appreciate your prompt attention to this matter and await your response at your convenience.",
        "Proposal":        "I look forward to exploring this opportunity further and remain available for any discussion.",
        "Follow-Up":       "I would appreciate an update at your earliest convenience and thank you for your continued attention.",
        "Invoice/Payment": "Please do not hesitate to reach out should any clarification or documentation be required.",
        "Job/Interview":   "I look forward to hearing from you and remain available at your convenience.",
        "General":         "Please do not hesitate to contact me should you require any further information or clarification.",
    }

    opening = openings.get(intent, openings["General"])
    closing = closings.get(intent, closings["General"])

    if middle.lower().startswith("i am writing"):
        body = middle
    else:
        body = f"{opening}\n\n{middle}"

    closing_triggers = ["look forward", "await your", "do not hesitate", "feel free", "remain available"]
    if not any(t in middle.lower() for t in closing_triggers):
        body += f"\n\n{closing}"

    result = f"Dear Sir/Madam,\n\n{body}\n\nYours sincerely,"
    result = re.sub(r' {2,}', ' ', result)
    return result


# ─────────────────────────────────────────────
# FILE UPLOAD HELPER
# ─────────────────────────────────────────────

def extract_text_from_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    elif name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return df.to_string()
    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("## 📧 Smart Email Assistant")
st.caption("Smart replies · Text improvement · Document upload · History log")


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    tone   = st.selectbox("Tone",   ["Formal", "Friendly", "Professional"])
    length = st.selectbox("Length", ["Short", "Medium", "Long"])
    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    total = len(st.session_state.history)
    st.metric("Replies Generated", total)
    if total:
        types_df = pd.DataFrame(st.session_state.history)
        st.bar_chart(types_df["email_type"].value_counts(), height=160)
    st.markdown("---")
    st.caption("Built with Streamlit · Python · No API needed")


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✉️ Email Generator", "✏️ Text Improver", "📜 History"])


# ════════════════════════════════════════════
# TAB 1 — EMAIL GENERATOR
# ════════════════════════════════════════════
with tab1:
    st.markdown("### Compose or Upload an Email")
    input_method = st.radio("Input method", ["Type / Paste", "Upload File (.txt / .csv)"], horizontal=True)

    email_input = ""
    if input_method == "Type / Paste":
        email_input = st.text_area(
            "Paste the email you received:", height=200,
            placeholder="Hi, I wanted to follow up on the project proposal we discussed last week..."
        )
    else:
        uploaded = st.file_uploader("Upload a .txt or .csv file", type=["txt", "csv"])
        if uploaded:
            email_input = extract_text_from_file(uploaded)
            st.text_area("Extracted content:", value=email_input, height=180)

    detected_type = detect_type(email_input) if email_input.strip() else "—"
    st.info(f"🔍 Detected email type: **{detected_type}**")
    num_replies = st.slider("Number of reply variants", 1, 5, 3)

    if st.button("🚀 Generate Replies"):
        if email_input.strip():
            st.markdown("#### ✨ Generated Replies")
            approach_labels = ["Variant A", "Variant B", "Variant C", "Variant D", "Variant E"]
            for i in range(num_replies):
                reply = build_reply(email_input, tone, length, variant=i)
                st.session_state.history.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "email_type": detected_type,
                    "tone": tone,
                    "reply": reply,
                })
                with st.expander(f"Option {i+1} — {tone} · {length} · {approach_labels[i]}", expanded=(i == 0)):
                    st.markdown(
                        f"<div class='card'>{reply.replace(chr(10), '<br>')}</div>",
                        unsafe_allow_html=True
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        st.code(reply, language="")
                    with c2:
                        st.download_button(
                            f"📥 Download Option {i+1}",
                            data=reply,
                            file_name=f"reply_option_{i+1}.txt",
                            mime="text/plain",
                            key=f"dl_{i}_{datetime.now().microsecond}"
                        )
        else:
            st.warning("⚠️ Please enter or upload an email first.")


# ════════════════════════════════════════════
# TAB 2 — TEXT IMPROVER
# ════════════════════════════════════════════
with tab2:
    st.markdown("### ✏️ Improve Your Draft")
    st.caption("Type your rough draft below — it will be rewritten into a polished, professional email.")

    user_text = st.text_area(
        "Enter your rough draft:", height=180,
        placeholder="i wanted to ask about the refund because its been 2 weeks and nobody replied yet and im getting frustrated"
    )

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("✨ Improve Text"):
            if user_text.strip():
                improved = improve_draft(user_text)
                st.markdown("#### ✅ Improved Version")
                st.markdown(
                    f"<div class='card'>{improved.replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True
                )
                st.code(improved, language="")
                st.download_button(
                    "📥 Download Improved Text",
                    data=improved,
                    file_name="improved_text.txt",
                    mime="text/plain"
                )
            else:
                st.warning("⚠️ Enter some text first.")

    with col_b:
        st.markdown("#### 💡 Tips for Better Emails")
        tips = [
            "Start with a clear subject line.",
            "Keep paragraphs short — 3 sentences max.",
            "State your request in the first paragraph.",
            "Always capitalise 'I' — never write 'i'.",
            "End with a clear call-to-action.",
            "Avoid vague words like 'stuff' or 'things'.",
            "Re-read once before sending.",
        ]
        for tip in tips:
            st.markdown(
                f"<div class='card' style='padding:12px 16px;margin-bottom:8px'>💬 {tip}</div>",
                unsafe_allow_html=True
            )


# ════════════════════════════════════════════
# TAB 3 — HISTORY LOG
# ════════════════════════════════════════════
with tab3:
    st.markdown("### 📜 Reply History (this session)")
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)[["time", "email_type", "tone", "reply"]]
        df.columns = ["Time", "Email Type", "Tone", "Reply Preview"]
        df["Reply Preview"] = df["Reply Preview"].str[:80] + "..."
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export History as CSV",
            data=csv,
            file_name="email_reply_history.csv",
            mime="text/csv"
        )
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info("No replies generated yet. Head to the Email Generator tab to get started.")