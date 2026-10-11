from common import *


class S5(VScene):
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

    def construct(self):
        self.session_title(
            5, "HTTP, 1996 to Now", "HTTP/1.0 → 1.1 → 2 → QUIC and HTTP/3",
            "Session five. The evolution of HTTP. Same words, three completely different ways of writing them down. The protocol did not drift. It was pushed.")
        self.ch_map()
        # 1.0
        self.ch_h10()
        self.ch_h10_limits()
        # 1.1 early
        self.ch_persist_host()
        self.ch_etag()
        self.ch_encoding_vary()
        self.ch_range()
        self.ch_chunked()
        self.ch_other_11()
        self.ch_two_conn()
        # 2616+
        self.ch_307()
        self.ch_smuggling()
        self.ch_rfcs()
        # cost
        self.ch_hol()
        self.ch_bloat_nagle()
        self.ch_bill()
        # h2
        self.ch_h2_history()
        self.ch_h2_frames()
        self.ch_hpack()
        self.ch_push()
        # quic
        self.ch_why_udp()
        self.ch_rtts()
        self.ch_quic_features()
        self.ch_qpack_discovery()
        self.ch_ideas()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_map(self):
        self.new_slide("Five hours, five walls", "The course runs in five parts. Each version ends on its own wall.", C_YELLOW)
        tbl = self.table([["Version", "RFC", "Ends on its wall"],
                          ["HTTP/1.0", "RFC 1945 · May 1996", "one response per connection"],
                          ["Early HTTP/1.1", "RFC 2068 · Jan 1997", "'at most 2 connections'"],
                          ["HTTP/1.1 now", "2616 (1999) > 7230-7235 (2014) > 9110-9112 (2022)", "head-of-line blocking"],
                          ["HTTP/2", "7540 (2015) > 9113 (2022); HPACK 7541", "TCP head-of-line blocking"],
                          ["QUIC + HTTP/3", "9000 QUIC, 9114 HTTP/3, 9001, QPACK 9204", "the 3-5% who block UDP"]],
                         [2.9, 6.1, 3.8], size=21, y=0.5, row_h=0.85)
        self.reveal_rows(tbl, ["HTTP one point zero, R F C nineteen forty-five, May nineteen ninety-six. It ends on one response per connection.",
                               "Early HTTP one point one, R F C twenty sixty-eight, January nineteen ninety-seven. It ends on the rule: at most two connections.",
                               "HTTP one point one today. R F C twenty six sixteen in nineteen ninety-nine, then seventy-two thirty to seventy-two thirty-five in twenty fourteen, then ninety-one ten to ninety-one twelve in twenty twenty-two. It ends on head-of-line blocking.",
                               "HTTP two. R F C seventy-five forty, May twenty fifteen, replaced by ninety-one thirteen in twenty twenty-two, with HPACK in R F C seventy-five forty-one. It ends on TCP head-of-line blocking.",
                               "And QUIC with HTTP three. R F C ninety-thousand for QUIC, ninety-one fourteen for HTTP three, ninety-oh-oh-one for QUIC TLS, and ninety-two-oh-four for QPACK. It ends on the three to five percent of networks that block UDP."])

    def ch_h10(self):
        self.new_slide("HTTP/1.0 (RFC 1945, May 1996)", "HTTP one point zero, the whole protocol, on one slide.", C_BLUE)
        L = VGroup(T("Methods", 28, C_BLUE), T("GET · HEAD · POST", 24), T("(+ PUT DELETE LINK UNLINK in an appendix)", 19, C_GREY)).arrange(DOWN, buff=0.15).move_to(LEFT * 3.8 + UP * 1.5)
        R = VGroup(T("Status codes", 28, C_GREEN), T("200 201 202 204 · 300 301 302 304", 22), T("400 401 403 404 · 500 501 502 503", 22), T("Today: 62 assigned (IANA, Sep 2025)", 20, C_GREY)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.5 + UP * 1.5)
        with self.vo("Three methods: GET, HEAD and POST. PUT, DELETE, LINK and UNLINK appear in an appendix of additional methods."):
            self.play(FadeIn(L))
        with self.vo("Sixteen status codes, from two hundred through five oh three. Today, sixty-two are assigned."):
            self.play(FadeIn(R))
        hd = T("16 headers: Allow · Authorization · Content-Encoding · Content-Length · Content-Type · Date · Expires · From · If-Modified-Since · Last-Modified · Location · Pragma · Referer · Server · User-Agent · WWW-Authenticate",
               20, C_ORANGE, maxw=12.4)
        hd = T(wrap("16 headers: Allow, Authorization, Content-Encoding, Content-Length, Content-Type, Date, Expires, From, If-Modified-Since, Last-Modified, Location, Pragma, Referer, Server, User-Agent, WWW-Authenticate", 90), 20, C_ORANGE, maxw=12.4, line_spacing=0.9).shift(DOWN * 0.3)
        with self.vo("And just sixteen headers. Allow, Authorization, Content-Encoding, Content-Length, Content-Type, Date, Expires, From, If-Modified-Since, Last-Modified, Location, Pragma, Referer, Server, User-Agent, and WWW-Authenticate."):
            self.play(FadeIn(hd))
        code = self.code_block(["$ printf 'GET / HTTP/1.0\\r\\n\\r\\n' | nc localhost 8010",
                                "response ... blank line ... body ... server closes (FIN)"], size=20, pos=DOWN * 2.2)
        with self.vo("You can speak it by hand with netcat. The response, a blank line as delimiter, the body, and then the server closes with a FIN. curl, by the way, adds four headers you did not write, and hides two the server sent."):
            self.play(FadeIn(code))

    def ch_h10_limits(self):
        self.new_slide("HTTP/1.0 limitation 1: one response, then the socket dies", "Four limitations. One: the socket dies after one response.", C_RED)
        ll = self.lifelines("Client", "Server", x=3.0, y_top=1.7)
        self.msg(ll, "r", "SYN ... handshake", C_GREY, dy=0.7, narration="RFC nineteen forty-five says the connection is established by the client before each request, and closed by the server after.")
        self.msg(ll, "r", "GET /a", C_YELLOW, dy=0.7, narration="One request.")
        self.msg(ll, "l", "200 + body, then FIN", C_GREEN, dy=0.7, narration="One response, and then the server hangs up.")
        self.msg(ll, "r", "GET /b  (same socket)", C_YELLOW, dy=0.7, narration="A second request on the same socket gets back an empty read, bytes b-empty. Not an error. Just nothing.")
        eq = T("24-object page @ 200 ms RTT:  24 handshakes (4.8 s) + 24 req/resp (4.8 s) = 9.6 s", 24, C_RED, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("The arithmetic: a twenty-four object page at two hundred milliseconds round trip. Twenty-four handshakes cost four point eight seconds. Twenty-four request and response pairs cost another four point eight. Nine point six seconds, plus twenty-four congestion windows, each starting from nothing in slow start."):
            self.play(FadeIn(eq))
        self.new_slide("HTTP/1.0 limitations 2, 3 and 4", "Limitations two, three and four.", C_RED)
        pts = [("2. No Host header: one IP = one website. Until Jan 1997 the ratio was 1:1; today ~1.1 billion sites. Host is 'the highest-leverage line in the standard'", "Two. No Host header, so one IP address means one website. Until January nineteen ninety-seven the ratio was one to one. Today there are about one point one billion websites. The fix, the Host header, is the highest leverage line in the standard."),
               ("3. Caching with a clock as the fingerprint: Last-Modified + If-Modified-Since -> 304 Not Modified (202,000 -> 0 bytes). But: no sub-second field, clock drift, and mtime is not identity", "Three. Caching, with a clock as the fingerprint. Last-Modified and If-Modified-Since give you a three oh four Not Modified, and two hundred two thousand bytes become zero. But timestamps have no sub-second field, clocks drift between you, me and the proxy, and a modification time is not identity: a rebuild changes every mtime but no bytes."),
               ("4. Only 16 headers and 3 methods: no OPTIONS - you can't ask a server what it supports", "Four. Only sixteen headers and three methods. There is no OPTIONS, so you cannot ask a server what it supports.")]
        self.bullets(pts, size=22, gap=0.4)
        self.new_slide("Fixed in RFC 2068", "Every one of these is fixed in R F C twenty sixty-eight.", C_GREEN)
        tbl = self.table([["Limitation", "Concretely", "Fixed in"],
                          ["Not persistent", "one request per handshake", "RFC 2068 §8.1"],
                          ["16 headers, 3 methods", "no OPTIONS", "RFC 2068 §9.2"],
                          ["Thin caching", "a clock, not a fingerprint", "RFC 2068 §14.19 (ETag)"],
                          ["No Host", "one IP per site", "RFC 2068 §14.23"]],
                         [3.6, 4.4, 4.0], size=24, y=0.8, row_h=0.85)
        self.reveal_rows(tbl, ["Persistence, in section eight point one.", "More headers and methods, including OPTIONS, in section nine point two.",
                               "ETag, in section fourteen point nineteen.", "And Host, in section fourteen point twenty-three."])
        t = T("Correction: 1.0 has no head-of-line blocking (no pipelining, no queue) - it has a serialisation cost. Real HOL arrives with 1.1.", 21, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("One correction. HTTP one point zero does not really have head-of-line blocking. HOL needs a queue, and one point zero has no pipelining. It has a serialisation cost: one round trip per object. Real head-of-line blocking arrives in one point one, as a side effect of the fix. Every solution here is the cause of the next slide."):
            self.play(FadeIn(t))

    def ch_persist_host(self):
        self.new_slide("Early HTTP/1.1 (RFC 2068, Jan 1997): persistence", "Early HTTP one point one. First, persistence becomes the default.", C_BLUE)
        L = VGroup(T("HTTP/1.0", 30, C_RED), T("Connection: keep-alive", 22), T("a non-standard extension:", 22), T("some honoured it, some ignored it,", 22), T("some crashed", 22), T("default = hang up", 24, C_RED)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.5 + UP * 0.6)
        R = VGroup(T("HTTP/1.1", 30, C_GREEN), T("persistent connections are the default", 22), T("opt out with  Connection: close", 22), T("default = stay", 24, C_GREEN), T("3 responses, one TCP handshake", 22)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.5 + UP * 0.6)
        with self.vo("In one point zero, Connection keep-alive was a non-standard extension. Some servers honoured it, some ignored it, and some crashed. The default was to hang up."):
            self.play(FadeIn(L))
        with self.vo("In one point one, persistent connections are the default. You opt out with Connection close. The default is to stay. Three responses, one TCP handshake."):
            self.play(FadeIn(R))
        self.new_slide("Host: one IP, a thousand sites", "The Host header, from section fourteen point twenty-three. One IP address, a thousand sites. This is virtual hosting.", C_BLUE)
        with self.vo("In one point one, a request with no Host header gets a four hundred Bad Request. It is a MUST. Same IP, same port, same socket, different sites."):
            pass
        tbl = self.table([["Layer", "Problem", "Fix"],
                          ["HTTP/1.0", "the 4-tuple was the address", "Host: - put the name in the message"],
                          ["TLS", "Host is encrypted; cert must be chosen first", "SNI in the ClientHello, in the clear"],
                          ["HTTP/2", "headers compressed and unordered", ":authority pseudo-header"],
                          ["Elsewhere", "many destinations, one connection", "topic, routing key, ingress host rule"]],
                         [2.3, 5.2, 5.3], size=22, y=0.2, row_h=0.9)
        self.reveal_rows(tbl, ["It is the same move at four layers. In HTTP one point zero, the four-tuple was the address, so the fix was Host: put the name in the message.",
                               "In TLS, the Host header is encrypted, but the certificate must be chosen first. So the name goes in the ClientHello, in the clear, as S N I.",
                               "In HTTP two, headers are compressed and unordered, so there is a pseudo-header called authority.",
                               "And elsewhere, many destinations over one connection: a topic, a routing key, an ingress host rule."])

    def ch_etag(self):
        self.new_slide("ETag: a fingerprint, not a clock", "ETag. A fingerprint, not a clock.", C_PURPLE)
        ll = self.lifelines("Client", "Server", x=3.0, y_top=1.7)
        self.msg(ll, "l", 'ETag: "55274ac22c651b90"', C_GREEN, dy=0.8, size=19, note="e.g. first 16 hex of sha256 of the bytes", narration="The server returns an ETag, for example the first sixteen hex characters of a sha two fifty-six of the bytes.")
        self.msg(ll, "r", 'If-None-Match: "55274a..."', C_YELLOW, dy=0.8, size=19, narration="The client sends it back in If-None-Match.")
        self.msg(ll, "l", "304 Not Modified", C_GREEN, dy=0.8, size=19, note="202,000 bytes -> 0", narration="And if it still matches, a three oh four. Two hundred two thousand bytes of body become zero.")
        pts = [("Weak validator W/\"...\" = equivalent, not identical. Range requests need a strong one", "A weak validator, written W slash and a quoted string, means equivalent, not byte-identical. Range requests need a strong one."),
               ("If-Match = the same idea for writes: optimistic concurrency, the fix for lost updates", "If-Match is the same idea for writes. It gives you optimistic concurrency, the fix for lost updates.")]
        self.bullets(pts, size=22, gap=0.3, shift=DOWN * 2.45)

    def ch_encoding_vary(self):
        self.new_slide("Accept-Encoding and Vary", "Accept-Encoding, and Vary.", C_ORANGE)
        self.bars([("identity", 202000, C_RED), ("gzip", 5763, C_GREEN), ("deflate", 5751, C_GREEN)], 202000, y0=1.6, left=-3.0, size=24, unit=" B",
                  narrs=["Asking for identity encoding, the body is two hundred two thousand bytes.", "With gzip, five thousand seven hundred sixty-three bytes. That is two point eight percent.", "Deflate is about the same."])
        pts = [("'HTTP/1.1 is slow because it's text' is undercut: text compresses. The body was never the problem - headers were (Content-Encoding only compresses the body)", "So the claim that HTTP one point one is slow because it is text is undercut: text compresses. The body was never the problem. The headers were, because Content-Encoding compresses only the body."),
               ("Vary is a cache-key instruction. Vary: Accept-Encoding is correct. Vary: User-Agent = millions of keys, hit rate -> 0. Vary: * = caching off", "And Vary is a cache key instruction: this URL has more than one answer, and here is what it depends on. Vary Accept-Encoding is correct. Vary User-Agent creates millions of keys and sends the hit rate to zero. Vary star turns caching off.")]
        self.bullets(pts, size=21, gap=0.35, shift=DOWN * 1.2)

    def ch_range(self):
        self.new_slide("Range: the header that runs your data lake", "Range. The header that runs your data lake.", C_TEAL)
        tbl = self.table([["Request", "Response"],
                          ["Range: bytes=100-199", "206 Partial Content  ·  Content-Range: bytes 100-199/202000"],
                          ["Range: bytes=-50", "last 50 bytes  ·  bytes 201950-201999/202000"],
                          ["Range: bytes=999999-", "416 Range Not Satisfiable  ·  bytes */202000"]],
                         [4.2, 8.4], size=22, y=1.0, row_h=0.9)
        self.reveal_rows(tbl, ["Bytes one hundred to one ninety-nine returns two oh six Partial Content, with a Content-Range header giving the slice and the total size.",
                               "Bytes minus fifty means the last fifty bytes, and you do not even need to know the size.",
                               "Asking beyond the end returns four sixteen, Range Not Satisfiable. That code was added in R F C twenty six sixteen, not twenty sixty-eight."])
        pts = [("Used by: video scrubbing, resumable downloads, and Parquet / ZIP footers - the directory is at the END, so read the last few KB, then only the columns you need", "Who uses it: video scrubbing, resumable downloads, and Parquet and ZIP footers. The directory is at the end of the file, so you read the last few kilobytes, then fetch only the columns you need.")]
        self.bullets(pts, size=24, shift=DOWN * 1.5)

    def ch_chunked(self):
        self.new_slide("Chunked transfer encoding", "Chunked transfer encoding: a body without knowing its length.", C_GREEN)
        code = self.code_block(["Transfer-Encoding: chunked          (and NO Content-Length)", "", "37                                    <- hex length: 0x37 = 55 bytes",
                                "body{font-family:monospace;...}", "0                                     <- empty chunk ends the body"], size=20, pos=UP * 1.0, hl={"37": C_YELLOW, "0": C_RED})
        with self.vo("The header says Transfer-Encoding chunked, and there is no Content-Length. Each chunk starts with its length in hex: thirty-seven hex is fifty-five bytes. Then the data. And an empty chunk, zero, ends the body."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=3))
        pts = [("Both length AND delimiter, nested: each chunk is length-prefixed; the sequence is delimited by an empty chunk - FastCGI's record structure", "That is both length and delimiter, nested. Each chunk is length-prefixed, and the sequence is delimited by an empty chunk. It is the same structure as FastCGI records."),
               ("Underpins streaming JSON, server-sent events, gRPC trailers", "It underpins streaming JSON, server-sent events, and gRPC trailers.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 1.7)

    def ch_other_11(self):
        self.new_slide("Everything else that arrived in 1.1", "Everything else that arrived in one point one.", C_YELLOW)
        tbl = self.table([["Arrival", "Purpose", "Where you meet it"],
                          ["OPTIONS", "ask what a server supports", "every CORS preflight"],
                          ["PUT / DELETE", "write / remove", "REST APIs"],
                          ["TRACE", "echo the request back, incl. proxies", "disabled everywhere (XST, 2003)"],
                          ["Via", "each proxy appends itself", "debugging which box lies"],
                          ["Expect: 100-continue", "ask before uploading 4 GB", "curl's 1 s pause on big PUTs"],
                          ["Cache-Control", "vocabulary, not one timestamp", "max-age, s-maxage, no-cache != no-store"],
                          ["~40 status codes", "303 405 409 410 412 413 415 504 ...", "504 already in RFC 2068"]],
                         [3.0, 4.6, 5.2], size=20, y=0.4, row_h=0.72)
        self.reveal_rows(tbl, ["OPTIONS asks what a server supports. You meet it in every CORS preflight.", "PUT and DELETE: write and remove. REST APIs.",
                               "TRACE echoes the request back, including proxies. It is disabled everywhere, because of Cross-Site Tracing in two thousand three.",
                               "Via: each proxy appends itself. Useful for debugging which box is lying.", "Expect 100-continue lets you ask before uploading four gigabytes. It is why curl pauses for a second on big PUTs.",
                               "Cache-Control replaced one timestamp with a vocabulary: max-age, s-maxage for shared caches, no-cache, no-store.",
                               "And about forty status codes. Five oh four was already in R F C twenty sixty-eight, so the whole five hundred family existed in nineteen ninety-seven."])
        t = T("no-cache = revalidate before use.   no-store = don't write it down at all.   Everybody gets this wrong exactly once.", 22, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.4)
        with self.vo("No-cache means revalidate before use. No-store means do not write it down at all. Everybody gets this wrong exactly once."):
            self.play(FadeIn(t))

    def ch_two_conn(self):
        self.new_slide("'SHOULD NOT maintain more than 2 connections'", "Section eight point one point four said a client should not maintain more than two connections. Here is six assets, at one hundred fifty milliseconds round trip.", C_ORANGE)
        self.bars([("close (HTTP/1.0)", 1369, C_RED), ("keepalive, 1 conn", 985, C_ORANGE), ("parallel 2 (RFC)", 607, C_YELLOW), ("parallel 6 (browsers)", 608, C_YELLOW), ("pipelined, 1 batch", 304, C_GREEN)],
                  1400, y0=1.7, left=-2.8, width=6.5, label_w=3.6, size=22, unit=" ms",
                  narrs=["Closing after each: twelve round trips, six connections, thirteen hundred sixty-nine milliseconds.", "Keep-alive on one connection: seven round trips, nine hundred eighty-five.",
                         "Two parallel connections, as the RFC says: four round trips, six hundred seven.", "Six parallel connections, as browsers did: two round trips, six hundred eight. The same wall time as two, with more connections.",
                         "And pipelined in one batch: two round trips, one connection, three hundred four milliseconds. The best row."])
        pts = [("Browsers shipped 6 connections per origin by ~2008; 18 via domain sharding (img1, img2, img3). RFC 7230 removed the sentence in 2014: the spec conceded", "Browsers shipped six connections per origin by around two thousand eight, and eighteen with domain sharding: img one, img two, img three. R F C seventy-two thirty removed the sentence in twenty fourteen. The spec conceded."),
               ("Pipelining was the best row - and nobody shipped it", "Pipelining was the best row, and nobody shipped it.")]
        self.bullets(pts, size=21, gap=0.3, shift=DOWN * 2.4)

    def ch_307(self):
        self.new_slide("RFC 2616 (June 1999): mostly tightening", "R F C twenty six sixteen, June nineteen ninety-nine, was mostly tightening. It added three oh seven, four sixteen, four seventeen with Expect, identity content-coding, and made Host a MUST. Five oh four is not new.", C_BLUE)
        pts = [("Why 307 exists - 'a standard losing to deployed reality': RFC 2068 said 302 keeps the method; every browser turned POST into GET anyway", "Why does 307 exist? It is a standard losing to deployed reality. R F C twenty sixty-eight said a three oh two keeps the method, but every browser turned POST into GET anyway."),
               ("2616 renamed 302 to 'Found', documented reality, and added 307 for 'keep the method'. 303 See Other = explicitly change to GET", "So twenty six sixteen renamed three oh two to Found, documented the reality, and added three oh seven for keep the method. Three oh three, See Other, explicitly means change to GET."),
               ("Easier to add a number than fix a billion deployed clients", "It is easier to add a number than to fix a billion deployed clients.")]
        self.bullets(pts, size=24, gap=0.5)
        self.new_slide("Postel's law loses: Content-Length + Transfer-Encoding", "Postel's law loses.", C_RED)
        L = VGroup(T("RFC 2616 §4.4 (1999)", 26, C_BLUE), T("both TE and CL present:", 22), T("CL MUST be ignored", 24, C_YELLOW), T("recover, don't reject", 22, C_GREY)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.5 + UP * 1.1)
        R = VGroup(T("RFC 9112 §6.3 (2022)", 26, C_GREEN), T("server MAY reject, or use TE alone", 22), T("regardless: MUST close the", 24, C_YELLOW), T("connection after responding", 24, C_YELLOW)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.5 + UP * 1.1)
        with self.vo("R F C twenty six sixteen, in nineteen ninety-nine: if both Transfer-Encoding and Content-Length are present, Content-Length must be ignored. Recover, don't reject. Be liberal in what you accept."):
            self.play(FadeIn(L))
        with self.vo("R F C ninety-one twelve, in twenty twenty-two: the server may reject such a request, or process it by Transfer-Encoding alone, but regardless it must close the connection after responding."):
            self.play(FadeIn(R))
        t = T("Be liberal in what you accept is a fine rule for two programs, catastrophic for a chain of five.", 25, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.7)
        with self.vo("Be liberal in what you accept is a fine rule for two programs. It is catastrophic for a chain of five."):
            self.play(FadeIn(t))

    def ch_smuggling(self):
        self.new_slide("HTTP request smuggling: one byte stream, two readings", "Which brings us to request smuggling. One byte stream, two readings.", C_RED)
        code = self.code_block(["POST /echo HTTP/1.1", "Host: site-a.local", "Content-Length: 6", "Transfer-Encoding: chunked", "", "0", "", "GET /admin HTTP/1.1", "Host: site-a.local"],
                               size=20, pos=LEFT * 4.3 + DOWN * 0.2, hl={"Content-Length": C_BLUE, "Transfer-Encoding": C_ORANGE, "GET /admin": C_RED})
        with self.vo("Here is a request with both headers: Content-Length six, and Transfer-Encoding chunked. Then a chunk of zero, which ends the body. And then bytes that look like a second request: GET slash admin."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=4))
        a = VGroup(T("Reader using Content-Length: 6", 23, C_BLUE), T("ONE request", 26, C_BLUE), T("body = 0 CR LF CR LF G", 21, WHITE)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.3 + UP * 1.5)
        b = VGroup(T("Reader using Transfer-Encoding", 23, C_ORANGE), T("TWO requests", 26, C_RED), T("the second is GET /admin", 21, WHITE)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.3 + DOWN * 0.6)
        with self.vo("A reader that trusts Content-Length sees one request, with a body of zero, carriage return, line feed, carriage return, line feed, and the letter G."):
            self.play(FadeIn(a))
        with self.vo("A reader that trusts Transfer-Encoding sees two requests. And the second one is GET slash admin."):
            self.play(FadeIn(b))
        t = T("CDN reads one way, origin the other -> a request the CDN never saw + a spare response in the connection for the next user.  HTTP/2 makes this unrepresentable.", 21, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.4)
        t = T(wrap("CDN reads one way, origin the other: a request the CDN never saw, and a spare response left in the connection for the next user. HTTP/2 makes this unrepresentable.", 90), 21, C_ORANGE, maxw=12.4, line_spacing=0.9).to_edge(DOWN, buff=0.35)
        with self.vo("Now put a CDN in front, which reads one way, and an origin behind it, which reads the other. The origin sees a request the CDN never saw, and a spare response is left in the connection for the next user. "
                     "The demo server answered two responses: a two hundred, and a four oh four for the request nobody sent. HTTP two makes this unrepresentable: the length is in the frame header, with no second opinion."):
            self.play(FadeIn(t))

    def ch_rfcs(self):
        self.new_slide("One document became six (June 2014)", "In June twenty fourteen, one document became six. Microservices for RFCs.", C_PURPLE)
        tbl = self.table([["RFC", "Title", "Who reads it"],
                          ["7230", "Message Syntax & Routing", "proxies, LBs, CDNs"],
                          ["7231", "Semantics & Content", "frameworks: methods, status codes"],
                          ["7232", "Conditional Requests", "anything with ETag"],
                          ["7233", "Range Requests", "video, downloads, Parquet"],
                          ["7234", "Caching", "every CDN"],
                          ["7235", "Authentication", "WWW-Authenticate / Authorization"]],
                         [1.5, 5.4, 5.7], size=22, y=0.5, row_h=0.72)
        self.reveal_rows(tbl, ["Seventy-two thirty, message syntax and routing, for proxies, load balancers and CDNs.", "Seventy-two thirty-one, semantics and content, for frameworks.",
                               "Seventy-two thirty-two, conditional requests, for anything with an ETag.", "Seventy-two thirty-three, range requests, for video, downloads and Parquet.",
                               "Seventy-two thirty-four, caching, for every CDN.", "And seventy-two thirty-five, authentication."])
        self.new_slide("Why your JWT is base64", "Why is your JWT base sixty-four?", C_PURPLE)
        pts = [("The HTTP token grammar excludes  \" ( ) , / : ; < = > ? @ [ \\ ] { }  - a rule from RFC 2616 §2.2 (1999)", "The HTTP token grammar excludes a list of punctuation characters. That rule comes from R F C twenty six sixteen, section two point two, in nineteen ninety-nine."),
               ("A JWT must survive the Authorization header, URL query, cookie, form field and JSON body - and the signature is raw bytes", "A JWT must survive the Authorization header, a URL query, a cookie, a form field and a JSON body, and its signature is raw bytes."),
               ("base64url swaps + / for - _  (URL-safe). Every layer has an alphabet; the intersection is ~64 characters wide - why base64 exists", "So base sixty-four U R L swaps plus and slash for dash and underscore. Every layer has an alphabet, and the intersection is about sixty-four characters wide. That is why base sixty-four exists, same as MIME in session two.")]
        self.bullets(pts, size=23, gap=0.45)
        self.new_slide("RFC 9110-9114 (June 2022): semantics vs encoding", "In June twenty twenty-two, the standard was reorganised around one idea: semantics are separate from encoding.", C_PURPLE)
        tbl = self.table([["RFC", "What", "Version-specific?"],
                          ["9110", "HTTP Semantics (methods, status, headers, ranges, auth)", "No - shared by 1.1, 2, 3"],
                          ["9111", "HTTP Caching", "No - shared"],
                          ["9112", "HTTP/1.1", "wire format only"],
                          ["9113", "HTTP/2", "wire format only"],
                          ["9114", "HTTP/3", "wire format only"]],
                         [1.4, 7.0, 4.2], size=22, y=0.6, row_h=0.8)
        self.reveal_rows(tbl, ["Ninety-one ten is HTTP semantics: methods, status codes, headers, ranges, authentication. Not version specific. Shared by one point one, two and three.",
                               "Ninety-one eleven is caching, also shared.", "Ninety-one twelve is HTTP one point one. Wire format only.", "Ninety-one thirteen is HTTP two. Wire format only.", "And ninety-one fourteen is HTTP three. Wire format only."])
        t = T("Three encodings, one language.   418 I'm a teapot: April Fool's RFC 2324 (1998) - reserved forever.", 24, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.6)
        with self.vo("Three encodings, one language. And, a fun fact: four eighteen, I'm a teapot, comes from an April Fool's R F C, twenty three twenty-four, in nineteen ninety-eight. It is reserved forever, because too many people shipped the joke."):
            self.play(FadeIn(t))

    def ch_hol(self):
        self.new_slide("Head-of-line blocking", "Now, what HTTP one point one cost. First, head-of-line blocking.", C_RED)
        with self.vo("Pipeline six requests on one connection, where the first asks for a response that takes two seconds. Every response arrives at about two thousand three milliseconds. Five fast responses wait two seconds for a sixth."):
            pass
        self.bars([("pipelined: big.txt first", 2003, C_RED), ("pipelined: others", 2003, C_RED), ("one connection each: big", 2006, C_ORANGE), ("one connection each: others", 5, C_GREEN)], 2100,
                  y0=1.5, left=-2.6, width=6.0, label_w=4.0, size=21, unit=" ms",
                  narrs=[None, None, "With one connection each, the big one still takes two thousand six milliseconds,", "but the others take three to seven. Hardly anything."])
        t = T("Cause: there is no request id on the wire. The order IS the identifier.", 27, C_YELLOW, maxw=12.4).shift(DOWN * 1.6)
        with self.vo("The cause: there is no request identifier on the wire. The order is the identifier. Responses must come back in request order, so the slowest sets the pace."):
            self.play(FadeIn(t))
        tbl = self.table([["Protocol", "Identifier"], ["TCP", "src / dst port"], ["SS7 / TCAP", "transaction id"], ["FastCGI", "requestId in every record"], ["HTTP/1.1", "nothing -> strict ordering"], ["HTTP/2, HTTP/3", "stream identifier, 31 bits, every frame"]],
                         [3.2, 6.0], size=22, y=-2.0, row_h=0.5)
        self.new_slide("Multiplexing needs identity", "Multiplexing needs identity. Compare how every protocol does it.", C_RED)
        tbl = self.table([["Protocol", "Identifier"], ["TCP", "src / dst port"], ["SS7 / TCAP", "transaction id"], ["FastCGI", "requestId in every record"], ["HTTP/1.1", "NOTHING -> strict ordering"], ["HTTP/2, HTTP/3", "stream identifier, 31 bits, every frame"]],
                         [3.4, 6.4], size=24, y=0.5, row_h=0.8)
        self.reveal_rows(tbl, ["TCP uses source and destination ports.", "SS7 TCAP uses a transaction id.", "FastCGI puts a request id in every record.", "HTTP one point one has nothing, so it needs strict ordering.", "HTTP two and three put a thirty-one bit stream identifier in every frame."])

    def ch_bloat_nagle(self):
        self.new_slide("Header bloat: 97.5% of what you upload is a repeat", "Second cost: header bloat.", C_ORANGE)
        eq = VGroup(T("one request's headers = 805 B   (cookies, User-Agent, Accept-*, sec-fetch-*)", 23), T("x 80 requests = 64,320 B", 26, C_RED), T("new information (the paths) = 1,600 B  (2.5%)", 24, C_GREEN),
                    T("repeats = 62,720 B  (97.5%)", 28, C_RED), T("on a 1 Mbit uplink: 0.51 s before any app data moves", 24, C_ORANGE)).arrange(DOWN, buff=0.35).shift(UP * 0.2)
        with self.vo("One request's headers, with cookies, User-Agent, Accept and sec-fetch headers, come to eight hundred five bytes. Eighty requests make sixty-four thousand three hundred twenty bytes. "
                     "The new information, the paths, is sixteen hundred bytes: two point five percent. Ninety-seven point five percent of what you upload is a repeat. On a one megabit uplink, that is half a second before any application data moves."):
            self.play(FadeIn(eq, lag_ratio=0.3), run_time=4)
        t = T("Why not gzip the headers? -> CRIME (see HPACK)", 24, C_YELLOW).shift(DOWN * 2.6)
        with self.vo("Why not just gzip the headers? Because of CRIME. We will get to it."):
            self.play(FadeIn(t))
        self.new_slide("Nagle + delayed ACK", "Third cost: when keep-alive made things slower. Nagle plus delayed ACK.", C_ORANGE)
        L = VGroup(T("Nagle (RFC 896, 1984)", 26, C_BLUE), T("don't send a small segment while", 22), T("an earlier one is unacknowledged", 22)).arrange(DOWN, buff=0.15).move_to(LEFT * 3.6 + UP * 1.5)
        R = VGroup(T("Delayed ACK (RFC 1122)", 26, C_GREEN), T("wait up to 40 ms to", 22), T("piggyback the ACK", 22)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.6 + UP * 1.5)
        with self.vo("Nagle's algorithm, R F C eight ninety-six, from nineteen eighty-four: do not send a small segment while an earlier one is unacknowledged. And delayed ACK, R F C eleven twenty-two: wait up to forty milliseconds to piggyback the ACK."):
            self.play(FadeIn(L), FadeIn(R))
        code = self.code_block(["write(head);   write(body);"], size=24, pos=UP * 0.0)
        with self.vo("Now a server that does write head, then write body. The head goes out. The body is held by Nagle. The client delays its ACK. So each request pays about forty milliseconds, every request but the first, and only on persistent connections, since close flushes."):
            self.play(FadeIn(code))
        self.bars([("two writes, persistent", 174, C_RED), ("one write + TCP_NODELAY", 3.2, C_GREEN)], 180, y0=-1.3, left=-2.2, width=6.0, label_w=4.2, size=22, unit=" ms",
                  narrs=["Total: one hundred seventy-four milliseconds,", "versus three point two milliseconds with one write and TCP_NODELAY. nginx and Apache coalesce writes and set TCP_NODELAY."])

    def ch_bill(self):
        self.new_slide("The bill for HTTP/1.1", "The bill for HTTP one point one.", C_RED)
        tbl = self.table([["Wall", "Measured", "Fixed by"],
                          ["Head-of-line blocking", "2003 ms vs 3 ms", "stream ids - HTTP/2"],
                          ["Header bloat", "97.5% repeats", "HPACK - HTTP/2"],
                          ["Too many connections", "6 / origin, 18 with sharding", "one connection - HTTP/2"],
                          ["Ambiguous framing", "request smuggling", "frame headers - HTTP/2"],
                          ["TCP itself", "3 RTTs before first byte", "QUIC - HTTP/3"]],
                         [3.8, 4.4, 4.4], size=23, y=0.9, row_h=0.85)
        self.reveal_rows(tbl, ["Head-of-line blocking: two thousand three milliseconds against three. Fixed by stream ids.", "Header bloat: ninety-seven point five percent repeats. Fixed by HPACK.",
                               "Too many connections: six per origin, eighteen with sharding. Fixed by one connection.", "Ambiguous framing: request smuggling. Fixed by frame headers.", "And TCP itself: three round trips before the first byte. Fixed by QUIC."])
        t = T(wrap("'Text is slow' is not the finding (gzip: 2.8%). The problem was text without lengths and without identifiers. HTTP/2 is HTTP with lengths and ids; binary is the consequence.", 90), 23, C_YELLOW, maxw=12.4, line_spacing=0.9).shift(DOWN * 2.3)
        with self.vo("Text is slow is not the finding. Gzip proved that. The problem was text without lengths and without identifiers. HTTP two is HTTP with lengths and ids. Binary is the consequence. "
                     "And text framing is exactly why HTTP won: anyone could implement it and debug it with telnet."):
            self.play(FadeIn(t))

    def ch_h2_history(self):
        self.new_slide("HTTP/2: ship to a billion users, then standardise", "Now HTTP two. The history: ship it to a billion users, then standardise.", C_BLUE)
        rows = [("Nov 2009", "SPDY announced (Belshe & Peon, Chromium blog) - 'up to 55% faster'", C_BLUE, "November two thousand nine: SPDY is announced, by Belshe and Peon, claiming up to fifty-five percent faster."),
                ("2010-2014", "Chrome, Firefox, nginx, Twitter, Facebook ship it", C_GREEN, "Between twenty ten and twenty fourteen, Chrome, Firefox, nginx, Twitter and Facebook ship it."),
                ("Feb 2015", "Google announces SPDY retirement", C_ORANGE, "February twenty fifteen: Google announces SPDY's retirement."),
                ("May 2015", "RFC 7540 (HTTP/2) + RFC 7541 (HPACK): 'SPDY with the edges filed off'", C_YELLOW, "May twenty fifteen: R F C seventy-five forty, and seventy-five forty-one for HPACK. SPDY with the edges filed off."),
                ("May 2016", "SPDY removed in Chrome 51", C_GREY, "May twenty sixteen: SPDY is removed in Chrome fifty-one."),
                ("Jun 2022", "RFC 9113 obsoletes 7540; deprecates priorities and the h2c Upgrade", C_PURPLE, "June twenty twenty-two: R F C ninety-one thirteen obsoletes seventy-five forty, and deprecates priorities and the h2c Upgrade.")]
        y = 1.9
        for d, txt, c, nar in rows:
            g = VGroup(T(d, 24, c, maxw=2.2), T(txt, 20, WHITE, maxw=9.6)).arrange(RIGHT, buff=0.4)
            g.move_to([0, y, 0]); g.shift(RIGHT * (-6.4 - g.get_left()[0]))
            with self.vo(nar):
                self.play(FadeIn(g, shift=RIGHT * 0.3), run_time=0.7)
            y -= 0.8
        t = T("It's 'HTTP/2', not 'HTTP/2.0': no minor versions. The next version = a new number + a new wire format.", 22, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("And it is HTTP slash two, not two point zero. No minor versions. The next version is a new number and a new wire format."):
            self.play(FadeIn(t))

    def ch_h2_frames(self):
        self.new_slide("Connection preface and frame header", "Every HTTP two connection starts with a twenty-four byte preface.", C_BLUE)
        pre = M("PRI * HTTP/2.0\\r\\n\\r\\nSM\\r\\n\\r\\n", 32, C_YELLOW).shift(UP * 1.8)
        with self.vo("It is the text: PRI, star, HTTP slash two point zero, then two blank lines, SM, and two more blank lines. Exactly twenty-four octets. An HTTP one point one server sees method PRI, version two point zero, and fails cleanly with a five oh one, instead of parsing binary as text. PRI and SM spell PRISM, from twenty thirteen."):
            self.play(Write(pre))
        pts = [("Over TLS: ALPN (RFC 7301) - the client lists h2, http/1.1 in the ClientHello; the server picks in the ServerHello. Zero extra RTTs", "Over TLS, the protocol is negotiated with ALPN, R F C seventy-three oh one. The client lists h2 and http one point one in the ClientHello, the server picks in the ServerHello. Zero extra round trips."),
               ("Cleartext (h2c): the Upgrade dance is deprecated in 9113; only 'prior knowledge' remains. No browser ever shipped cleartext HTTP/2", "For cleartext, h2c, the Upgrade dance was deprecated in ninety-one thirteen. Only prior knowledge remains, and no browser ever shipped cleartext HTTP two.")]
        self.bullets(pts, size=22, gap=0.4, shift=DOWN * 0.4)
        self.new_slide("The frame header: 9 bytes", "Then the frame header. Nine bytes.", C_BLUE)
        hdr = VGroup(box("Length\n24 bits", C_BLUE, w=3.6, h=1.1, size=22), box("Type\n8", C_GREEN, w=1.8, h=1.1, size=22), box("Flags\n8", C_ORANGE, w=1.8, h=1.1, size=22),
                     box("R\n1", C_GREY, w=1.0, h=1.1, size=22), box("Stream Identifier\n31 bits", C_PURPLE, w=3.8, h=1.1, size=22)).arrange(RIGHT, buff=0.04).shift(UP * 1.5)
        with self.vo("Length, twenty-four bits. Type, eight. Flags, eight. One reserved bit. And a thirty-one bit stream identifier. Then the payload."):
            self.play(FadeIn(hdr, lag_ratio=0.2), run_time=2.5)
        pts = [("Client-initiated streams are odd; server-initiated are even - no coordination needed. Stream 0 = the connection itself (SETTINGS, PING, GOAWAY)", "Client-initiated streams are odd, server-initiated streams are even, so no coordination is needed. Stream zero is the connection itself: SETTINGS, PING and GOAWAY."),
               ("Example: GET / = 67 bytes of text -> 15 bytes with HPACK", "Example: a GET slash request is sixty-seven bytes of text, and fifteen bytes with HPACK.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 0.8)
        self.new_slide("The ten frame types", "There are ten frame types.", C_BLUE)
        tbl = self.table([["Type", "Name", "Does", "Replaced"],
                          ["0x0", "DATA", "body chunks <= MAX_FRAME_SIZE", "Content-Length / chunked"],
                          ["0x1", "HEADERS", "opens a stream; HPACK block", "request line + headers"],
                          ["0x2", "PRIORITY", "deprecated (RFC 9218)", "-"],
                          ["0x3", "RST_STREAM", "cancel ONE stream", "closing TCP (kills all)"],
                          ["0x4", "SETTINGS", "announce limits, both ways", "nothing"],
                          ["0x5", "PUSH_PROMISE", "server push", "nothing (didn't last)"],
                          ["0x6", "PING", "RTT; keep intermediaries awake", "nothing"],
                          ["0x7", "GOAWAY", "'last stream id I'll process'", "Connection: close mid-flight"],
                          ["0x8", "WINDOW_UPDATE", "flow control per stream AND connection", "only TCP's window"],
                          ["0x9", "CONTINUATION", "header block bigger than a frame", "nothing - a 2024 DoS class"]],
                         [1.0, 2.6, 5.0, 4.0], size=18, y=-0.2, row_h=0.52)
        self.reveal_rows(tbl, ["DATA carries body chunks, replacing Content-Length and chunked.", "HEADERS opens a stream, with an HPACK block.", "PRIORITY is deprecated, replaced by R F C ninety-two eighteen.",
                               "RST_STREAM cancels one stream, instead of closing TCP and killing everything.", "SETTINGS announces limits in both directions.", "PUSH_PROMISE is server push. It did not last.",
                               "PING measures round trip time and keeps intermediaries awake.", "GOAWAY says: this is the last stream id I will process. A graceful drain.",
                               "WINDOW_UPDATE gives flow control per stream and per connection.", "And CONTINUATION carries a header block bigger than one frame. It became a denial of service class in twenty twenty-four."])
        t = T("Defaults: HEADER_TABLE_SIZE 4096 · INITIAL_WINDOW_SIZE 65535 · MAX_FRAME_SIZE 16384 · MAX_CONCURRENT_STREAMS unlimited (>= 100 recommended)", 18, C_GREY, maxw=12.6).to_edge(DOWN, buff=0.3)
        with self.vo("Defaults to remember: header table size four thousand ninety-six, initial window size sixty-five thousand five hundred thirty-five, max frame size sixteen thousand three hundred eighty-four, and max concurrent streams unlimited, though no smaller than one hundred is recommended."):
            self.play(FadeIn(t))

    def ch_hpack(self):
        self.new_slide("HPACK (RFC 7541): 174 bytes -> 79 -> 6", "HPACK, R F C seventy-five forty-one. It uses three mechanisms.", C_GREEN)
        pts = [("1. Static table - 61 entries, identical everywhere. Index 2 = :method GET (name AND value), so GET costs one byte: 0x82. 'Not compressed. Indexed.'", "One. The static table, sixty-one entries, identical everywhere. Index two is method GET, name and value, so a GET costs one byte: zero x eighty-two. Not compressed. Indexed."),
               ("2. Dynamic table - from index 62. Anything sent before on this connection gets an index: a 300-byte cookie costs 300 B once, then 1-2 B forever", "Two. The dynamic table, from index sixty-two. Anything sent before on this connection gets an index. A three hundred byte cookie costs three hundred bytes once, then one or two bytes forever."),
               ("3. Huffman (Appendix B) - a fixed canonical code from real header text ('e' = 5 bits, 'X' = 8), used per string only when it shrinks", "Three. Huffman coding, from Appendix B: a fixed canonical code built from real header text. The letter e takes five bits, and X takes eight. It is used per string, only when it shrinks it.")]
        self.bullets(pts, size=21, gap=0.4, shift=UP * 0.8)
        self.bars([("HTTP/1.1 text", 174, C_RED), ("HPACK, first time", 79, C_ORANGE), ("HPACK, second time", 6, C_GREEN)], 180, y0=-1.5, left=-2.6, width=6.5, label_w=4.0, size=22, unit=" B",
                  narrs=["The same header set: one hundred seventy-four bytes as HTTP one point one text.", "Seventy-nine bytes the first time with HPACK. Fifty-five percent saved.", "And six bytes the second time. Six one-byte indices. Ninety-seven percent saved."])
        t = T("The dynamic table is per connection -> HTTP/2 wants ONE connection; domain sharding is now harmful.", 22, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.35)
        with self.vo("The dynamic table is per connection. So HTTP two wants one connection, and domain sharding is now harmful."):
            self.play(FadeIn(t))
        self.new_slide("Why not just gzip headers? CRIME (2012)", "So why not just gzip the headers? Because of CRIME, in twenty twelve.", C_RED)
        fl, _ = self.flow(["attacker injects\na guess next to\nthe secret cookie", "guess matches ->\ngzip finds a repeat", "compressed length\ndrops by 1 byte", "'correct!'\nrepeat per character"],
                          [C_RED, C_ORANGE, C_YELLOW, C_GREEN], y=0.9, w=2.9, h=1.4, size=20, gap=0.4,
                          narrations=["The attacker cannot decrypt anything, but can watch the compressed size. They inject a guess next to a secret cookie.", "When the guess matches, gzip finds a repeat,", "and the length drops by one byte.", "That means the guess was right. Repeat for each character."])
        pts = [("HPACK's defence is structural: the Huffman table is fixed (not adaptive); the dynamic table is an exact-match index, not a substring matcher; RFC 7541 §7.1 lets you mark fields 'never indexed'", "HPACK's defence is structural. The Huffman table is fixed, not adaptive. The dynamic table is an exact-match index, not a substring matcher. And section seven point one lets you mark fields as never indexed."),
               ("Warning: gzipping JSON that contains a user search term + an API key = a rebuilt CRIME (BREACH-style)", "A warning: gzipping a JSON response that contains a user's search term next to an API key rebuilds CRIME. That is the BREACH style of attack.")]
        self.bullets(pts, size=21, gap=0.35, shift=DOWN * 1.9)
        self.new_slide("Multiplexing: ~400x faster", "And now multiplexing. The same six requests, over one connection.", C_GREEN)
        self.bars([("/style.css", 4.9, C_GREEN), ("logo", 5.7, C_GREEN), ("icon", 6.9, C_GREEN), ("app.js", 6.9, C_GREEN), ("hero", 7.8, C_GREEN), ("big.txt", 2005.9, C_RED)], 2100, y0=1.6, left=-3.0, width=6.5, label_w=2.8, gap=0.7, size=22, unit=" ms",
                  narrs=["Style dot css in four point nine milliseconds.", "The logo in five point seven.", "The icon in six point nine.", "App dot js in six point nine.", "The hero image in seven point eight.", "And big dot txt in two thousand five milliseconds. Out of order, on purpose, because each frame says which stream it belongs to."])
        t = T("A protocol can only give you permission: handle requests inline in the read loop and you get exactly HTTP/1.1's numbers. Fix: a thread per stream.", 21, C_ORANGE, maxw=12.4).to_edge(DOWN, buff=0.4)
        with self.vo("One honest lesson from the demo: a protocol can only give you permission. The first version handled requests inline in the read loop, and got exactly HTTP one point one's numbers, all around two thousand five milliseconds. "
                     "The fix was a thread per stream and a lock on the connection. The transport was fine. We serialised the work ourselves. The same shape: a worker pool sharing one database connection, a blocking call inside a coroutine, a gRPC handler with a global mutex."):
            self.play(FadeIn(t))

    def ch_push(self):
        self.new_slide("Server push: nobody deprecated it, everybody removed it", "Server push. Nobody deprecated it. Everybody removed it.", C_RED)
        pts = [("Still in RFC 9113 §8.4 and RFC 9114 §4.6 - only PRIORITY and the h2c Upgrade were deprecated", "It is still in R F C ninety-one thirteen and ninety-one fourteen. Only PRIORITY and the h2c Upgrade were deprecated."),
               ("Chrome 106 (27 Sep 2022) removed it: used by 1.25% of HTTP/2 sites (later 0.7%); 'no clear net performance gain and in many cases regressions'", "Chrome one oh six, on the twenty-seventh of September twenty twenty-two, removed it. It was used by one point two five percent of HTTP two sites, later zero point seven. No clear net performance gain, and in many cases regressions."),
               ("The problem: the server doesn't know what's in your cache - it pushes files you already have, competing for bandwidth and cwnd", "The problem: the server does not know what is in your cache. It pushes files you already have, competing for bandwidth and congestion window.")]
        self.bullets(pts, size=22, gap=0.4, shift=UP * 0.6)
        t = VGroup(T("Replacement: 103 Early Hints (RFC 8297) - 'you're going to want style.css'; the client checks its cache and decides.", 22, C_GREEN, maxw=12.4),
                   T("The server keeps the knowledge; the client keeps the decision. Inform - do not act.", 25, C_YELLOW, maxw=12.4)).arrange(DOWN, buff=0.3).to_edge(DOWN, buff=0.5)
        with self.vo("The replacement is one oh three Early Hints, R F C eighty-two ninety-seven. The server says: you are going to want style dot css. The client checks its cache, and decides. The server keeps the knowledge, the client keeps the decision. Inform, do not act."):
            self.play(FadeIn(t, lag_ratio=0.3), run_time=1.5)
        self.new_slide("What HTTP/2 could not fix: TCP head-of-line blocking", "What HTTP two could not fix: TCP head-of-line blocking.", C_RED)
        pts = [("RFC 9114 §1.1: one lost or reordered packet stalls ALL streams, because TCP's loss recovery can't see HTTP/2's streams", "R F C ninety-one fourteen, section one point one: a lost or reordered packet stalls all streams, because TCP's loss recovery cannot see HTTP two's streams."),
               ("Demo: a 300 ms stall at byte 3000 - everything behind the hole waits ~306 ms though the bytes had arrived (the kernel can't hand them over out of order). Which streams get caught changes every run", "In the demo, a three hundred millisecond stall at byte three thousand makes everything behind the hole wait about three hundred six milliseconds, even though the bytes had already arrived. The kernel cannot hand them over out of order. Which streams get caught changes every run."),
               ("Google SPDY data: 11.81% speedup at 0% loss, 47.7% at 2% loss - multiplexing helps most exactly where TCP hurts most", "Google's SPDY data: an eleven point eight one percent speedup at zero loss, and forty-seven point seven percent at two percent loss. Multiplexing helps most exactly where TCP hurts most.")]
        self.bullets(pts, size=22, gap=0.4)

    def ch_why_udp(self):
        self.new_slide("QUIC: why UDP?", "Now QUIC. Why UDP? Because the internet stopped accepting new protocols.", C_PURPLE)
        nums = VGroup(box("TCP = 6", C_BLUE, w=2.6, h=0.8, size=26), box("UDP = 17", C_GREEN, w=2.6, h=0.8, size=26), box("SCTP = 132", C_RED, w=2.8, h=0.8, size=26)).arrange(RIGHT, buff=0.4).shift(UP * 1.7)
        with self.vo("IP protocol numbers: TCP is six, UDP is seventeen, SCTP is one thirty-two. Why not just pick a new number, like two fifty-three?"):
            self.play(FadeIn(nums, lag_ratio=0.3), run_time=1.5)
        pts = [("Every NAT, firewall, CGNAT, corporate proxy and hotel router drops what it doesn't recognise. SCTP (standardised 2000) can't be used across the public internet. UDP is 'a hole that already exists'", "Because every NAT, firewall, carrier grade NAT, corporate proxy and hotel router drops what it does not recognise. SCTP, standardised in two thousand, cannot be used across the public internet. UDP is a hole that already exists."),
               ("Ossification: 'Anything a middlebox CAN read, it will eventually depend on' (RFC 8999 §7) - how TCP options became unusable. QUIC encrypts packet numbers and most of the header, to stay changeable", "The second reason is ossification. Anything a middlebox can read, it will eventually depend on. That is R F C eighty-nine ninety-nine. It is how TCP options became unusable. QUIC encrypts packet numbers and most of its header, not only for privacy, but to stay changeable."),
               ("Userspace: a TCP change = a kernel upgrade on a billion machines and a decade; a QUIC change ships with your app", "And userspace: a TCP change needs a kernel upgrade on a billion machines and a decade. A QUIC change ships with your app.")]
        self.bullets(pts, size=21, gap=0.35, shift=DOWN * 0.8)

    def ch_rtts(self):
        self.new_slide("Round trips: one handshake, not two", "Round trips. One handshake, not two.", C_PURPLE)
        self.bars([("TCP + TLS 1.3 + HTTP/2", 456.6, C_RED), ("QUIC + HTTP/3 (1-RTT)", 319.8, C_ORANGE), ("QUIC 0-RTT (resumed)", 161.7, C_GREEN)], 480, y0=1.7, left=-2.6, width=6.5, label_w=4.2, gap=1.0, size=22, unit=" ms",
                  narrs=["A cold connection with TCP, TLS one point three and HTTP two takes three round trips. TLS one point two would be four. Measured at one hundred fifty milliseconds: four hundred fifty-six point six.",
                         "QUIC with HTTP three needs two round trips: the handshake, and the request. Three hundred nineteen point eight milliseconds.",
                         "And QUIC zero RTT, on a resumed connection, sends the request in the first flight. One round trip. One hundred sixty-one point seven."])
        pts = [("RFC 9001 §2.1: no separate transport and crypto handshakes - the TLS ClientHello rides in a QUIC CRYPTO frame; ALPN rides there too. TLS is mandatory: there is no unencrypted QUIC", "R F C ninety-oh-oh-one, section two point one: there are no separate transport and crypto handshakes. The TLS ClientHello rides in a QUIC CRYPTO frame, and ALPN rides there too. TLS is mandatory. There is no unencrypted QUIC."),
               ("Cold: QUIC saves 137 ms. Resumed 0-RTT saves 295 ms. Every layer boundary is a place you may pay a round trip", "Cold, QUIC saves one hundred thirty-seven milliseconds. Resumed with zero RTT, it saves two hundred ninety-five. Every layer boundary is a place you may pay a round trip.")]
        self.bullets(pts, size=21, gap=0.35, shift=DOWN * 2.2)
        self.new_slide("0-RTT and replay", "Zero RTT has a price: replay.", C_RED)
        pts = [("RFC 9001 §9.2: early data is exposed to replay attacks. Protections (a single-use ticket cache) are imperfect because a server farm has many servers - the attacker replays to a different one", "R F C ninety-oh-oh-one, section nine point two: early data is exposed to replay attacks. Protections like a single-use ticket cache are imperfect, because a server farm has many servers. The attacker replays to a different one."),
               ("Rule: idempotent requests only - GET is fine; a POST that charges a card is not", "So the rule is: idempotent requests only. A GET is fine. A POST that charges a card is not."),
               ("Cloudflare allows only GET and HEAD in 0-RTT and sets an Early-Data header so the origin can reply 425 Too Early", "Cloudflare allows only GET and HEAD in zero RTT, and sets an Early-Data header, so the origin can reply four twenty-five Too Early."),
               ("0-RTT is a cache of a negotiation; every cache of a negotiation trades a round trip for the possibility of a replay", "Zero RTT is a cache of a negotiation. And every cache of a negotiation trades a round trip for the possibility of a replay.")]
        self.bullets(pts, size=22, gap=0.4)

    def ch_quic_features(self):
        self.new_slide("Head-of-line blocking, gone", "Head-of-line blocking, gone.", C_GREEN)
        pts = [("QUIC STREAM frames carry a stream id AND an offset: ordered within a stream, unordered between streams", "QUIC STREAM frames carry a stream id and an offset. They are ordered within a stream, and unordered between streams.")]
        self.bullets(pts, size=24, shift=UP * 2.1)
        self.bars([("/big.txt (waited)", 78, C_ORANGE), ("others", 11, C_GREEN)], 90, y0=0.6, left=-2.6, width=6.5, label_w=3.2, size=22, unit=" ms",
                  narrs=["With eighteen datagrams deleted, five percent, only big dot txt waited: seventy-eight milliseconds.", "The others took four to eleven."])
        t = T("On TCP the blast radius is 'whoever had bytes behind the gap'. On QUIC it's exactly one stream.", 24, C_YELLOW, maxw=12.4).shift(DOWN * 1.7)
        with self.vo("On TCP, the blast radius is whoever had bytes behind the gap. On QUIC, it is exactly one stream."):
            self.play(FadeIn(t))
        self.new_slide("Connection IDs: surviving a network change", "Connection IDs. A connection that survives changing networks.", C_PURPLE)
        L = VGroup(T("TCP: the connection IS the 4-tuple", 26, C_RED), T("src IP, src port, dst IP, dst port", 22), T("Wi-Fi -> LTE changes the IP:", 22), T("every connection dies", 24, C_RED), T("(video buffers, downloads restart, websockets reconnect)", 18, C_GREY),
                   T("same with NAT rebinding after idle", 20)).arrange(DOWN, buff=0.18).move_to(LEFT * 3.5 + UP * 0.6)
        R = VGroup(T("QUIC: identity != addressing", 26, C_GREEN), T("a connection ID (CID)", 22), T("new address, same CID,", 22), T("path validated", 22), T("-> connection migration", 24, C_GREEN)).arrange(DOWN, buff=0.18).move_to(RIGHT * 3.5 + UP * 0.6)
        with self.vo("With TCP, the connection is the four-tuple: source IP, source port, destination IP, destination port. Switch from Wi-Fi to LTE, the IP changes, and every connection dies. Video buffers, downloads restart, websockets reconnect. NAT rebinding after idle does the same."):
            self.play(FadeIn(L))
        with self.vo("In QUIC, identity is not addressing. A connection I D identifies the connection. A new address, the same connection I D, the path is validated, and you have connection migration."):
            self.play(FadeIn(R))
        t = T(wrap("Privacy: a stable CID is a tracking id, so CIDs MUST NOT contain information an observer can correlate; endpoints issue a pool and rotate. Identity belongs at the layer that owns the semantics.", 90), 20, C_ORANGE, maxw=12.4, line_spacing=0.9).to_edge(DOWN, buff=0.4)
        with self.vo("There is a privacy catch. A stable connection I D is a tracking identifier. So connection I Ds must not contain information an observer can correlate, and endpoints issue a pool of them and rotate. Identity belongs at the layer that owns the semantics."):
            self.play(FadeIn(t))

    def ch_qpack_discovery(self):
        self.new_slide("QPACK (RFC 9204): HPACK had its own HOL blocking", "QPACK, R F C ninety-two oh four. HPACK had its own head-of-line blocking.", C_ORANGE)
        pts = [("HPACK's dynamic table is shared mutable state that needs total ordering - free on TCP. QUIC removed that: a header block on stream 12 could reference an entry inserted on stream 8 that hasn't arrived -> stall", "HPACK's dynamic table is shared mutable state that needs total ordering, which is free on TCP. QUIC removed that. So a header block on stream twelve could reference an entry inserted on stream eight that has not arrived yet, and stall."),
               ("Fix: move table updates to dedicated unidirectional streams - an encoder stream (type 0x02) for insertions, a decoder stream (type 0x03) for 'I've seen these' acks. The encoder only references entries known safe", "The fix: move table updates to dedicated one-way streams. An encoder stream, type two, carries insertions. A decoder stream, type three, carries acknowledgements: I have seen these. The encoder only references entries known to be safe."),
               ("Defaults: QPACK_BLOCKED_STREAMS = 0, QPACK_MAX_TABLE_CAPACITY = 0. Static table: HPACK 61 entries from index 1; QPACK 99 entries from index 0", "Defaults: blocked streams zero, and max table capacity zero. The static table: HPACK has sixty-one entries from index one. QPACK has ninety-nine entries from index zero."),
               ("Relax an ordering guarantee, then go find what was relying on it", "The lesson: relax an ordering guarantee, then go find what was relying on it.")]
        self.bullets(pts, size=20, gap=0.35)
        self.new_slide("Discovery and fallback", "How does a browser find out a server speaks HTTP three?", C_TEAL)
        tbl = self.table([["Mechanism", "RFC · date", "How", "Cost"],
                          ["ALPN", "7301 · Jul 2014", "protocol chosen in the TLS handshake ('h2', 'h3')", "needs a handshake first"],
                          ["Alt-Svc", "7838 · Apr 2016", "response header Alt-Svc: h3=\":443\"; browser remembers", "one full TCP+TLS connection per cold cache"],
                          ["HTTPS DNS RR", "9460 · Nov 2023", "DNS record type 65 carries the ALPN list", "nothing - the lookup happens anyway"]],
                         [2.3, 2.2, 4.8, 3.6], size=19, y=0.9, row_h=1.0)
        self.reveal_rows(tbl, ["ALPN, R F C seventy-three oh one, July twenty fourteen: the protocol is chosen in the TLS handshake. h2 or h3. But it needs a handshake first.",
                               "Alt-Svc, R F C seventy-eight thirty-eight, April twenty sixteen: a response header says h3 is available on port four forty-three, and the browser remembers. The cost: one full TCP and TLS connection per cold cache.",
                               "And the HTTPS DNS record, R F C ninety-four sixty, November twenty twenty-three. DNS record type sixty-five carries the ALPN list. It costs nothing, because the lookup happens anyway."])
        pts = [("3-5% of networks block all UDP (RFC 9308); 95.3% of Google's clients could use QUIC, 4.4% blocked or had packet-size problems", "Three to five percent of networks block all UDP, per R F C ninety-three oh eight. Of Google's clients, ninety-five point three percent could use QUIC, and four point four percent were blocked or had packet size problems."),
               ("Fallback to TCP/TLS is a downgrade attack by construction: drop UDP, wait for the fallback", "And fallback to TCP is a downgrade attack by construction: drop the UDP, and wait for the fallback.")]
        self.bullets(pts, size=22, gap=0.35, shift=DOWN * 2.1)
        self.new_slide("Adoption (2024-2026)", "Adoption, in twenty twenty-four to twenty twenty-six.", C_TEAL)
        pts = [("HTTP Archive / Web Almanac 2024, by request: HTTP/1.1 ~15%, HTTP/2+ ~85%", "By request, HTTP one point one is about fifteen percent, and HTTP two and up about eighty-five."),
               ("By homepage: h1 21-22%, h2 70-71%, h3 7-9%. Alt-Svc advertising h3 ~26-28%; HTTPS DNS RR ~9-10%", "By homepage: h1 is twenty-one to twenty-two percent, h2 seventy to seventy-one, and h3 seven to nine. Alt-Svc advertising h3 is twenty-six to twenty-eight percent, and the HTTPS DNS record nine to ten."),
               ("15% of requests are still HTTP/1.1, eleven years later: no cutover, a long tail", "Fifteen percent of requests are still HTTP one point one, eleven years later. There is no cutover, only a long tail.")]
        self.bullets(pts, size=24, gap=0.5)

    def ch_ideas(self):
        self.new_slide("Four ideas from Session 5", "Four ideas from this session.", C_GREEN)
        pts = [("1. Multiplexing needs identity - no request id means the order is the identifier. 31 bits fixed it (TCP ports, TCAP transaction ids, FastCGI requestId, QUIC stream ids)", "One. Multiplexing needs identity. With no request id, the order is the identifier. Thirty-one bits fixed it: like TCP ports, TCAP transaction ids, FastCGI request ids, and QUIC stream ids."),
               ("2. Every fix is the next problem - persistence > pipelining > HOL; HTTP/2 fixed HOL above TCP and exposed it inside TCP; QUIC fixed that and broke HPACK > QPACK", "Two. Every fix is the next problem. Persistence led to pipelining, which led to head-of-line blocking. HTTP two fixed it above TCP and exposed it inside TCP. QUIC fixed that, and broke HPACK, which led to QPACK."),
               ("3. Semantics and encoding differ - RFC 9110 = meaning; 9112/9113/9114 = three ways to write it. GET is unchanged since 1996", "Three. Semantics and encoding differ. R F C ninety-one ten is meaning. Ninety-one twelve, thirteen and fourteen are three ways to write it. GET is unchanged since nineteen ninety-six."),
               ("4. Deployed reality beats specification - 302 > 307; 2 connections > 6; Postel's law lost to smuggling; 418 reserved; push died without deprecation; QUIC on UDP because middleboxes have a veto", "Four. Deployed reality beats specification. Three oh two led to three oh seven. Two connections became six. Postel's law lost to smuggling. Four eighteen is reserved. Push died without deprecation. And QUIC runs on UDP because middleboxes have a veto.")]
        self.bullets(pts, size=21, gap=0.4)

    def quiz(self):
        self.quiz_recap(5, [
            "RFC map: 1945 (1.0), 2068 (1.1), 2616, 7230-7235, 9110-9114; 7540 + 7541 (h2 + HPACK); 9000 QUIC; 9001; 9204 QPACK; 7301 ALPN; 7838 Alt-Svc; 9460 HTTPS RR; 8297 Early Hints.",
            "1.0: close after each response, no Host, Last-Modified / If-Modified-Since / Expires caching, 16 headers, 3 methods.",
            "1.1: persistent by default (Connection: close to opt out); Host required (else 400); ETag / If-None-Match -> 304; weak W/ validators; If-Match = optimistic concurrency.",
            "1.1: Range -> 206 / 416; chunked (hex length, 0 terminator); OPTIONS (CORS); TRACE (XST); Via; Expect: 100-continue; no-cache = revalidate, no-store = don't store; Vary.",
            "2 connections rule -> browsers 6 per origin; removed in RFC 7230. Pipelining never shipped. 302 'Found' vs 307 (keeps method) vs 303.",
            "Smuggling = CL vs TE disagreement; RFC 9112 says close the connection; HTTP/2 makes it unrepresentable.",
            "HOL root cause: no request id. Headers are 97.5% repeats. Nagle + delayed ACK = 40 ms -> TCP_NODELAY.",
            "SPDY 2009 -> RFC 7540 (2015) -> SPDY removed Chrome 51 (2016) -> RFC 9113 (2022). Preface PRI * HTTP/2.0 (24 bytes); ALPN 'h2'; h2c deprecated.",
            "Frame header 9 bytes: length 24, type 8, flags 8, R 1, stream id 31. Client odd, server even, stream 0 = connection. 10 frame types.",
            "HPACK: 61 static entries (0x82 = :method GET), dynamic table from 62, Huffman; 174 -> 79 -> 6 B. CRIME = compression-size leak.",
            "Push removed in Chrome 106 (2022); replacement = 103 Early Hints. HTTP/2 still has TCP HOL blocking.",
            "QUIC = UDP (proto 17) + userspace + encrypted headers; streams with id + offset. TCP+TLS1.3+h2 = 3 RTT; QUIC = 2; 0-RTT = 1 (replayable: idempotent only; 425 Too Early).",
            "Connection IDs -> migration; rotated for privacy. QPACK: encoder / decoder streams; 99 static entries. 3-5% of networks block UDP; fallback = downgrade attack.",
        ], "Here is what the quiz is most likely to ask from session five.", size=24, per_page=4)
        self.say("That is session five. Next up, session six: abusing CDNs.")
