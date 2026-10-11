"""Shared toolkit for the CN video course: theme, Piper narration, reusable diagram helpers."""
import hashlib
import warnings
import wave
from contextlib import contextmanager
from pathlib import Path

warnings.filterwarnings("ignore")
from manim import *  # noqa: E402,F401,F403

ROOT = Path(__file__).parent
VOICE_PATH = ROOT / "voices" / "en_US-lessac-medium.onnx"
AUDIO_DIR = ROOT / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

# ---- theme (3Blue1Brown-ish) -------------------------------------------------
BG = "#0d0f14"
C_BLUE = "#58C4DD"
C_YELLOW = "#FFD866"
C_GREEN = "#83C167"
C_RED = "#FC6255"
C_ORANGE = "#FF9F43"
C_PURPLE = "#B392F0"
C_TEAL = "#5CD0B3"
C_GREY = "#8B93A1"
C_DIM = "#3a4150"
SANS = "Adwaita Sans"
SERIF = "Liberation Serif"
MONO = "Liberation Mono"

config.background_color = BG

FS = 1.2  # global font scale: manim's frame is only 8 units tall
_Text = Text


def Text(*a, **kw):  # noqa: F811
    if "font_size" in kw:
        kw["font_size"] = kw["font_size"] * FS
    return _Text(*a, **kw)


_voice = None

# ---- speech + caption text processing ----------------------------------------------
import re as _re

_SPELL = {
    "TCP": "T C P", "UDP": "U D P", "IP": "I P", "HTTP": "H T T P", "HTTPS": "H T T P S", "DNS": "D N S", "TLS": "T L S", "SSL": "S S L",
    "SMTP": "S M T P", "FTP": "F T P", "POP3": "pop three", "POP3S": "pop three S", "IMAP": "eye map", "SMS": "S M S", "SS7": "S S seven",
    "MTP": "M T P", "MTP1": "M T P one", "MTP2": "M T P two", "MTP3": "M T P three", "SCCP": "S C C P", "TCAP": "tee cap", "ISUP": "eye sup",
    "SIP": "sip", "RTP": "R T P", "SRTP": "S R T P", "SDP": "S D P", "MSC": "M S C", "SMSC": "S M S C", "HLR": "H L R", "VLR": "V L R",
    "VMSC": "V M S C", "ISN": "I S N", "MSS": "M S S", "MTU": "M T U", "MSL": "M S L", "RST": "R S T", "ACK": "ack", "SYN": "sin",
    "FIN": "fin", "SACK": "sack", "FCS": "F C S", "CRC": "C R C", "TTL": "T T L", "NAT": "nat", "OSI": "O S I", "MAC": "mack",
    "ASCII": "ass key", "TLV": "T L V", "RPC": "R P C", "gRPC": "g R P C", "BBR": "B B R", "QUIC": "quick", "CRLF": "C R L F",
    "RFC": "R F C", "CDN": "C D N", "WAF": "waff", "DDoS": "D Dos", "SIF": "S I F", "FSN": "F S N", "BSN": "B S N", "MIME": "mime",
    "ASN": "A S N", "BER": "B E R", "GSM": "G S M", "UCS": "U C S", "JSON": "jason", "URL": "U R L", "URI": "U R I", "HTML": "H T M L",
    "CSMA": "C S M A", "CD": "C D", "CA": "C A", "RTT": "R T T", "RTTs": "R T Ts", "TTLs": "T T Ls", "IMS": "I M S", "SBC": "S B C",
    "IAM": "I A M", "ACM": "A C M", "ANM": "A N M", "REL": "R E L", "RLC": "R L C", "MO": "M O", "MT": "M T", "TPDU": "T P D U",
    "SSN": "S S N", "DS0": "D S zero", "LEO": "L E O", "ISO": "I S O", "SIO": "S I O", "DPC": "D P C", "OPC": "O P C", "SLS": "S L S",
    "EHLO": "E hello", "STARTTLS": "start T L S", "SPF": "S P F", "DKIM": "D K I M", "DMARC": "dee mark", "PASV": "pass've",
    "HOL": "H O L", "LAN": "lan", "RF": "R F", "FD": "F D", "EOF": "E O F", "SIGPIPE": "sig pipe", "SIGINT": "sig int", "SIGKILL": "sig kill",
    "SIGTERM": "sig term", "EPIPE": "E pipe", "SOCK": "sock", "SETSIZE": "set size", "REUSEADDR": "reuse addr", "NOSIGNAL": "no signal",
    "epoll": "e poll", "kqueue": "k queue", "IOCP": "I O C P", "io_uring": "I O u ring", "nginx": "engine X", "HAProxy": "H A proxy",
    "sendfile": "send file", "FastCGI": "fast C G I", "CGI": "C G I", "FCGI": "F C G I", "PHP": "P H P", "JVM": "J V M", "DPDK": "D P D K",
    "mTCP": "m T C P", "REUSEPORT": "reuse port", "stdin": "standard in", "stdout": "standard out", "stderr": "standard error",
    "envp": "env p", "ulimit": "u limit", "NIC": "N I C", "VCL": "V C L", "MPM": "M P M", "C10K": "C ten K", "C10M": "C ten M",
    "RESP": "R E S P", "MQTT": "M Q T T", "IoT": "I O T", "API": "A P I", "RPS": "R P S", "MySQL": "my S Q L", "Kafka": "kafka",
    "fd": "F D", "fds": "F Ds", "fpm": "F P M", "Apache": "a patchy", "Squid": "squid", "SIGPIPE": "sig pipe", "TTFB": "T T F B",
    "CPU": "C P U", "RAM": "ram", "GB": "gigabytes", "MB": "megabytes", "KB": "kilobytes", "ms": "milliseconds", "kbps": "kilobits per second",
    "Mbps": "megabits per second", "Gbps": "gigabits per second", "TB": "terabytes", "AWS": "A W S", "CPUs": "C P Us", "I/O": "I O",
    "INADDR": "in addr", "ANY": "any", "NOSIGNAL": "no signal", "UTF": "U T F", "SACKs": "sacks", "CUBIC": "cubic", "ID": "I D",
}


def speak_text(text: str) -> str:
    t = text
    t = t.replace("ASN dot one", "A S N one").replace("ASN.1", "A S N one")
    t = _re.sub(r"\bdash dash\b", " ", t)
    t = _re.sub(r"\b(underscore)\b", " ", t)
    t = _re.sub(r"\bslash\b", " ", t)
    t = _re.sub(r"\bdash\b", " ", t)
    for k in sorted(_SPELL, key=len, reverse=True):
        t = _re.sub(rf"(?<![A-Za-z0-9]){_re.escape(k)}(?![A-Za-z0-9])", _SPELL[k], t)
    t = _re.sub(r"0x([0-9A-Fa-f]+)", lambda m: "hex " + " ".join(m.group(1)), t)
    for a, b in [("→", ", "), ("->", ", then "), ("=>", ", "), ("≈", " about "), ("×", " times "), ("÷", " divided by "), ("·", ", "),
                 ("—", ", "), ("–", ", "), ("…", "."), ("&", " and "), ("%", " percent"), ("+", " plus "), ("=", " equals "),
                 ("~", " about "), ("#", " number "), ("<=", " at most "), (">=", " at least "), ("<", " less than "), (">", " greater than ")]:
        t = t.replace(a, b)
    t = _re.sub(r"[\"“”`*_\\|^{}\[\]()]", " ", t)
    t = _re.sub(r"\s+-\s+", ", ", t)
    t = _re.sub(r"(?<=\w)-(?=\w)", " ", t)
    t = _re.sub(r"/", " ", t)
    t = _re.sub(r"\s+", " ", t).strip()
    t = _re.sub(r"\s+([,.;:?!])", r"\1", t)
    return t


def caption_text(text: str) -> str:
    t = text
    t = _re.sub(r"(\w+) underscore (\w+)", r"\1_\2", t)
    t = _re.sub(r"(\w+) underscore (\w+)", r"\1_\2", t)
    t = t.replace("ASN dot one", "ASN.1").replace(" dot com", ".com")
    t = _re.sub(r"\b((?:[A-Z] )+[A-Z])\b", lambda m: m.group(1).replace(" ", ""), t)
    t = t.replace(" slash ", "/").replace(" dash dash ", " --").replace(" dash ", " -")
    return t


def caption_chunks(text: str, dur: float, maxlen=84):
    """Split a narration into short caption lines with proportional timing -> [(start_off, end_off, text)]."""
    sents = _re.split(r"(?<=[.!?])\s+", caption_text(text).strip())
    chunks = []
    for sn in sents:
        words, cur = sn.split(), ""
        for w in words:
            if len(cur) + len(w) + 1 > maxlen and cur:
                chunks.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            chunks.append(cur)
    total = sum(len(c) for c in chunks) or 1
    out, t0 = [], 0.0
    for c in chunks:
        d = dur * len(c) / total
        out.append((t0, t0 + d, c))
        t0 += d
    return out


def _srt_time(x):
    h, r = divmod(x, 3600)
    m, sec = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int((sec - int(sec)) * 1000):03d}"



def synth(text: str):
    """Return (wav_path, duration_seconds); cached by text hash."""
    global _voice
    spoken = speak_text(text)
    h = hashlib.sha1(spoken.encode()).hexdigest()[:16]
    path = AUDIO_DIR / f"{h}.wav"
    if not path.exists():
        if _voice is None:
            from piper import PiperVoice, SynthesisConfig

            _voice = PiperVoice.load(str(VOICE_PATH))
        from piper import SynthesisConfig

        cfg = SynthesisConfig(length_scale=1.08, noise_scale=0.6, noise_w_scale=0.7)
        with wave.open(str(path), "wb") as wf:
            _voice.synthesize_wav(spoken, wf, syn_config=cfg)
    with wave.open(str(path), "rb") as wf:
        dur = wf.getnframes() / wf.getframerate()
    return str(path), dur


def T(s, size=30, color=WHITE, font=SANS, maxw=12.6, **kw):
    t = Text(s, font=font, font_size=size, color=color, **kw)
    if t.width > maxw:
        t.scale(maxw / t.width)
    return t


def M(s, size=24, color=WHITE, maxw=12.6, **kw):
    t = Text(s, font=MONO, font_size=size, color=color, **kw)
    if t.width > maxw:
        t.scale(maxw / t.width)
    return t


def wrap(s, n):
    import textwrap
    return textwrap.fill(s, n)


def box(label, color=C_BLUE, w=2.6, h=0.9, size=26, fill=0.12, font=SANS):
    t = Text(label, font=font, font_size=size, color=WHITE)
    if t.width > w - 0.3:
        t.scale((w - 0.3) / t.width)
    h = max(h, t.height + 0.3)
    r = RoundedRectangle(corner_radius=0.12, width=w, height=h, color=color, stroke_width=3)
    r.set_fill(color, opacity=fill)
    t.move_to(r)
    return VGroup(r, t)


def chip(label, color=C_BLUE, size=22):
    return box(label, color, w=Text(label, font=SANS, font_size=size).width + 0.5, h=0.6, size=size)


class VScene(Scene):
    """Scene with narration (`with self.vo(text):`) and diagram helpers."""

    # ---- narration -----------------------------------------------------------
    @contextmanager
    def vo(self, text, pad=0.35):
        path, dur = synth(text)
        self.add_sound(path)
        t0 = self.renderer.time
        if not hasattr(self, "_cues"):
            self._cues = []
        for a, b, c in caption_chunks(text, dur):
            self._cues.append((t0 + a, t0 + b, c))
        yield
        spent = self.renderer.time - t0
        if spent < dur + pad:
            self.wait(dur + pad - spent)

    def tear_down(self):
        cues = getattr(self, "_cues", [])
        if cues:
            cap = ROOT / "captions"
            cap.mkdir(exist_ok=True)
            with open(cap / f"{type(self).__name__}.srt", "w") as f:
                for i, (a, b, c) in enumerate(cues, 1):
                    f.write(f"{i}\n{_srt_time(a)} --> {_srt_time(b)}\n{c}\n\n")
        super().tear_down()

    def say(self, text, pad=0.35):
        with self.vo(text, pad):
            pass

    # ---- chapter chrome ----------------------------------------------------------
    def clear(self, t=0.6):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=t)

    def session_title(self, num, title, tagline, narration):
        n = Text(f"SESSION {num}", font=SANS, font_size=28, color=C_BLUE, weight=BOLD)
        t = Text(title, font=SERIF, font_size=58, color=WHITE)
        if t.width > 12.5:
            t.scale(12.5 / t.width)
        tag = Text(tagline, font=SANS, font_size=26, color=C_GREY)
        if tag.width > 12.5:
            tag.scale(12.5 / tag.width)
        g = VGroup(n, t, tag).arrange(DOWN, buff=0.4)
        with self.vo(narration):
            self.play(FadeIn(n, shift=DOWN * 0.2), run_time=0.6)
            self.play(Write(t), run_time=1.6)
            self.play(FadeIn(tag), run_time=0.8)
        self.clear()

    def heading(self, text, color=C_YELLOW):
        h = Text(text, font=SERIF, font_size=42, color=color)
        if h.width > 12.8:
            h.scale(12.8 / h.width)
        h.to_edge(UP, buff=0.4)
        ul = Line(h.get_left(), h.get_right(), color=color, stroke_width=2).next_to(h, DOWN, buff=0.12)
        ul.set_opacity(0.5)
        return VGroup(h, ul)

    def new_slide(self, text, narration=None, color=C_YELLOW):
        """Clear screen and show a heading. Optionally narrate while it appears."""
        if narration and narration.startswith("#"):
            color, narration = narration, None
        self.clear()
        h = self.heading(text, color)
        if narration:
            with self.vo(narration):
                self.play(FadeIn(h, shift=DOWN * 0.2), run_time=0.6)
        else:
            self.play(FadeIn(h, shift=DOWN * 0.2), run_time=0.6)
        return h

    # ---- bullets ------------------------------------------------------------------
    def bullets(self, items, size=30, gap=0.5, colors=None, below=None, shift=ORIGIN, maxw=11.8, x=-6.2, chars=None):
        """items: list of (text, narration). Positions the whole block first, then reveals each line."""
        group = VGroup()
        chars = chars or int(1480 / (size * FS))
        lines = [Text(wrap(txt, chars), font=SANS, font_size=size, color=(colors[i] if colors else WHITE), line_spacing=0.9)
                 for i, (txt, _) in enumerate(items)]
        sc = min(1.0, min(maxw / l.width for l in lines))
        for line in lines:
            line.scale(sc)
            dot = Dot(radius=0.07, color=C_BLUE)
            row = VGroup(dot, line).arrange(RIGHT, buff=0.25, aligned_edge=UP)
            dot.shift(DOWN * 0.17)
            group.add(row)
        group.arrange(DOWN, aligned_edge=LEFT, buff=gap)
        if below is not None:
            group.next_to(below, DOWN, buff=0.5)
        else:
            group.move_to([0, -0.2, 0])
        group.shift(shift)
        group.shift(RIGHT * (x - group.get_left()[0]))
        for (txt, nar), row in zip(items, group):
            if nar:
                with self.vo(nar):
                    self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.6)
            else:
                self.play(FadeIn(row, shift=RIGHT * 0.3), run_time=0.6)
        return group

    # ---- code -------------------------------------------------------------------------
    def code_block(self, lines, size=24, hl=None, pos=ORIGIN):
        """lines: list[str]. hl: dict word->color for syntax tint."""
        hl = hl or {}
        rows = VGroup()
        for ln in lines:
            if ln.strip() == "":
                t = Text("I", font=MONO, font_size=size).set_opacity(0)
            else:
                t = Text(ln, font=MONO, font_size=size, t2c=hl)
            rows.add(t)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        bg = SurroundingRectangle(rows, color=C_DIM, buff=0.3, corner_radius=0.1)
        bg.set_fill("#151922", 1)
        g = VGroup(bg, rows).move_to(pos)
        return g

    # ---- sequence diagram ---------------------------------------------------------------
    def lifelines(self, left, right, y_top=1.9, y_bot=-3.7, lc=C_BLUE, rc=C_GREEN, x=3.6):
        a = box(left, lc, w=3.2, h=0.7, size=24).move_to([-x, y_top + 0.5, 0])
        b = box(right, rc, w=3.2, h=0.7, size=24).move_to([x, y_top + 0.5, 0])
        la = DashedLine(a.get_bottom(), [-x, y_bot, 0], color=C_DIM, dash_length=0.12)
        lb = DashedLine(b.get_bottom(), [x, y_bot, 0], color=C_DIM, dash_length=0.12)
        grp = VGroup(a, b, la, lb)
        self.play(FadeIn(grp), run_time=0.7)
        return {"a": a, "b": b, "x": x, "y": y_top - 0.2, "all": grp}

    def msg(self, ll, direction, label, color=C_YELLOW, dy=0.8, note=None, narration=None, size=22):
        """direction: 'r' = left->right, 'l' = right->left. Returns mobjects."""
        x = ll["x"]
        y = ll["y"]
        if note:
            dy = max(dy, 0.95)
        ll["y"] = y - dy
        s, e = ([-x, y, 0], [x, y - 0.2, 0]) if direction == "r" else ([x, y, 0], [-x, y - 0.2, 0])
        arr = Arrow(s, e, buff=0.08, color=color, stroke_width=5, max_tip_length_to_length_ratio=0.08)
        lab = Text(label, font=MONO, font_size=size, color=color)
        lab.move_to(arr.get_center()).shift(UP * 0.27)
        grp = VGroup(arr, lab)
        if note:
            nt = Text(note, font=SANS, font_size=20, color=C_GREY)
            if nt.width > 2 * x + 2.5:
                nt.scale((2 * x + 2.5) / nt.width)
            nt.move_to(arr.get_center()).shift(DOWN * 0.3)
            grp.add(nt)
        if narration:
            with self.vo(narration):
                self.play(GrowArrow(arr), FadeIn(lab), run_time=0.8)
                if note:
                    self.play(FadeIn(grp[2]), run_time=0.4)
        else:
            self.play(GrowArrow(arr), FadeIn(lab), run_time=0.8)
            if note:
                self.play(FadeIn(grp[2]), run_time=0.4)
        return grp

    # ---- flow of boxes --------------------------------------------------------------------
    def flow(self, labels, colors=None, y=0.0, w=2.2, h=0.9, size=22, gap=0.55, narrations=None, x_center=0.0):
        colors = colors or [C_BLUE] * len(labels)
        boxes = [box(l, c, w=w, h=h, size=size) for l, c in zip(labels, colors)]
        g = VGroup(*boxes).arrange(RIGHT, buff=gap).move_to([x_center, y, 0])
        if g.width > 13.0:
            g.scale(13.0 / g.width)
        arrows = [Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.05, color=C_GREY, stroke_width=3,
                        max_tip_length_to_length_ratio=0.25) for i in range(len(boxes) - 1)]
        for i, b in enumerate(boxes):
            nar = narrations[i] if narrations else None
            anims = [FadeIn(b, shift=UP * 0.15)]
            if i > 0:
                anims.append(GrowArrow(arrows[i - 1]))
            if nar:
                with self.vo(nar):
                    self.play(*anims, run_time=0.6)
            else:
                self.play(*anims, run_time=0.5)
        return VGroup(*boxes, *arrows), boxes

    # ---- table ----------------------------------------------------------------------------------
    def table(self, rows, col_w, size=22, header_color=C_YELLOW, y=0.2, row_h=0.62, hl_col0=C_BLUE):
        """rows: list of lists of str; first row is header. Uniformly scaled so every cell fits."""
        cells = []
        sc = 1.0
        for ri, row in enumerate(rows):
            rr = []
            for ci, cell in enumerate(row):
                col = header_color if ri == 0 else (hl_col0 if ci == 0 else WHITE)
                blank = not cell.strip()
                t = Text("-" if blank else cell, font=SANS if not (ri > 0 and ci == 0) else MONO, font_size=size, color=col,
                         weight=BOLD if ri == 0 else NORMAL)
                if blank:
                    t.set_opacity(0)
                sc = min(sc, (col_w[ci] - 0.25) / t.width)
                rr.append(t)
            cells.append(rr)
        total = sum(col_w)
        out = VGroup()
        for ri, rr in enumerate(cells):
            r = VGroup()
            x = -total / 2
            for ci, t in enumerate(rr):
                t.scale(sc)
                r.add(t)
            out.add(r)
        # vertical layout
        row_gap = row_h
        top = (len(rows) - 1) * row_gap / 2
        for ri, r in enumerate(out):
            x = -total / 2
            for ci, t in enumerate(r):
                t.move_to([x + 0.12 + t.width / 2, y + top - ri * row_gap, 0])
                x += col_w[ci]
        return out

    def reveal_rows(self, tbl, narrations=None, with_lines=True):
        # header rule
        if with_lines:
            rule = Line(tbl.get_left() + LEFT * 0.1, tbl.get_right() + RIGHT * 0.1, color=C_GREY, stroke_width=1.5)
            rule.next_to(tbl[0], DOWN, buff=0.12)
            rule.set_x(tbl.get_center()[0])
            self.play(FadeIn(tbl[0]), Create(rule), run_time=0.7)
        else:
            self.play(FadeIn(tbl[0]), run_time=0.5)
        for i, r in enumerate(tbl[1:]):
            nar = narrations[i] if narrations and i < len(narrations) else None
            if nar:
                with self.vo(nar):
                    self.play(FadeIn(r, shift=UP * 0.12), run_time=0.5)
            else:
                self.play(FadeIn(r, shift=UP * 0.12), run_time=0.4)

    # ---- helper: horizontal bar chart -----------------------------------------
    def bars(self, items, maxv, y0=1.6, gap=0.85, left=-3.0, width=7.0, label_w=3.4, size=22, unit="", narrs=None):
        grp = VGroup()
        for i, (name, val, col) in enumerate(items):
            y = y0 - i * gap
            lab = T(name, size, WHITE, maxw=label_w).move_to([left - label_w / 2 - 0.2, y, 0])
            lab.align_to([left - label_w - 0.1, 0, 0], LEFT)
            w = max(0.05, width * val / maxv)
            r = Rectangle(width=w, height=0.5, color=col, fill_opacity=0.7, stroke_width=2).move_to([left + w / 2, y, 0])
            v = T(f"{val:g}{unit}", size, col, maxw=2.5).next_to(r, RIGHT, buff=0.15)
            row = VGroup(lab, r, v)
            nar = narrs[i] if narrs else None
            if nar:
                with self.vo(nar):
                    self.play(FadeIn(lab), GrowFromEdge(r, LEFT), FadeIn(v), run_time=0.9)
            else:
                self.play(FadeIn(lab), GrowFromEdge(r, LEFT), FadeIn(v), run_time=0.7)
            grp.add(row)
        return grp

    # ---- quiz recap ----------------------------------------------------------------------------------------
    def quiz_recap(self, session, points, narration_intro, size=27, per_page=5):
        pages = [points[i:i + per_page] for i in range(0, len(points), per_page)]
        for pi, page in enumerate(pages):
            self.clear()
            title = f"Session {session} · What the quiz will ask" + (f"  ({pi + 1}/{len(pages)})" if len(pages) > 1 else "")
            h = self.heading(title, C_GREEN)
            if pi == 0:
                with self.vo(narration_intro):
                    self.play(FadeIn(h), run_time=0.6)
            else:
                self.play(FadeIn(h), run_time=0.6)
            lines = [Text(wrap(p, int(1500 / (size * FS))), font=SANS, font_size=size, line_spacing=0.9) for p in page]
            sc = min(1.0, min(12.0 / l.width for l in lines))
            rows = VGroup()
            for l in lines:
                l.scale(sc)
                d = Dot(radius=0.08, color=C_GREEN)
                row = VGroup(d, l).arrange(RIGHT, buff=0.22, aligned_edge=UP)
                d.shift(DOWN * 0.18)
                rows.add(row)
            rows.arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to([0, -0.3, 0])
            rows.shift(RIGHT * (-6.2 - rows.get_left()[0]))
            for r in rows:
                self.play(FadeIn(r, shift=RIGHT * 0.25), run_time=0.45)
                self.wait(1.2)
            self.wait(1.0)
