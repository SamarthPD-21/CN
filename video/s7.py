import random

from common import *


class S7(VScene):
    def construct(self):
        self.session_title(
            7, "Building for Failures", "Failures and retries: every step of a request fails differently",
            "Session seven. Building for failures. This session is built around one mind map, called Failures and Retries. "
            "The core idea: a network request is a chain of steps, each step fails in its own way, and the right reaction depends on which step failed.")
        self.ch_chain()
        self.ch_socket()
        self.ch_dns()
        self.ch_connect()
        self.ch_connect2()
        self.ch_write()
        self.ch_read()
        self.ch_cdn()
        self.ch_tls()
        self.ch_http()
        self.ch_http2()
        self.ch_which_retry()
        self.ch_backoff()
        self.ch_jitter()
        self.ch_breaker()
        self.ch_toolkit()
        self.ch_toolkit2()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_chain(self):
        self.new_slide("The failure map: a chain of steps", "Here is the chain.", C_YELLOW)
        labels = ["socket()", "DNS", "connect()", "write()", "read()", "CDN", "SSL / TLS", "HTTP"]
        cols = [C_BLUE, C_PURPLE, C_ORANGE, C_GREEN, C_GREEN, C_TEAL, C_RED, C_YELLOW]
        nars = ["First, the socket system call.", "Then a DNS lookup.", "Then connect.", "Then write.", "Then read.", "Then the CDN, with its tiers.", "Then SSL and TLS.", "And finally, HTTP itself."]
        g1 = VGroup(*[box(f"{i + 1}  {l}", c, w=3.0, h=0.9, size=24) for i, (l, c) in enumerate(zip(labels[:4], cols[:4]))]).arrange(RIGHT, buff=0.5).shift(UP * 1.2)
        g2 = VGroup(*[box(f"{i + 5}  {l}", c, w=3.0, h=0.9, size=24) for i, (l, c) in enumerate(zip(labels[4:], cols[4:]))]).arrange(RIGHT, buff=0.5).shift(DOWN * 0.4)
        for b, n in zip(list(g1) + list(g2), nars):
            with self.vo(n):
                self.play(FadeIn(b, shift=UP * 0.15), run_time=0.5)
        t = T("Each step fails in its own way. The right reaction - retry, fall back, give up, serve stale - depends on WHICH step failed.", 24, C_YELLOW, maxw=12.4).shift(DOWN * 2.3)
        with self.vo("Each step fails in its own way. And the right reaction, whether that is to retry, fall back, give up, or serve stale, depends on which step failed. We will go through the map branch by branch."):
            self.play(FadeIn(t))

    def stage(self, title, color, intro, rows, narrs, size=21, widths=(5.6, 7.2), y=0.8, row_h=0.9, header=("Failure", "Reaction / explanation")):
        self.new_slide(title, intro, color)
        tbl = self.table([list(header)] + [list(r) for r in rows], list(widths), size=size, y=y, row_h=row_h)
        self.reveal_rows(tbl, narrs)
        return tbl

    def ch_socket(self):
        self.stage("1 · Client: socket()", C_BLUE, "Step one: the socket system call.",
                   [["Can't create a socket (out of file descriptors / resources)", "RETRY - after some time a socket can get free. socket() fails with EMFILE / ENFILE when ulimit -n (default 1024) is exhausted; sockets in TIME_WAIT free up later"]],
                   ["The only failure: you cannot create a socket, because you are out of file descriptors or resources. The map's reaction: retry, because after some time a socket can get free. socket fails with EMFILE or ENFILE when the ulimit, one thousand twenty-four by default, is exhausted. Sockets in TIME_WAIT or being closed free up later."],
                   row_h=1.2)

    def ch_dns(self):
        self.stage("2 · DNS lookup", C_PURPLE, "Step two: the DNS lookup. Three ways it fails.",
                   [["DNS mapping not available", "no record (NXDOMAIN): the name doesn't exist, or the record was deleted"],
                    ["Network issue -> DNS timeout", "the UDP query to the resolver was lost; gethostbyname blocks with no timeout you control"],
                    ["DNS resolved but misconfigured", "wrong IP returned: a bad record, a stale /etc/hosts entry, the wrong resolver"]],
                   ["The mapping is not available. There is no record: NXDOMAIN. The name does not exist, or the record was deleted.",
                    "A network issue causes a DNS timeout. The UDP query to the resolver was lost, and gethostbyname blocks, with no timeout you control.",
                    "Or the DNS resolved, but was misconfigured: it returned the wrong IP. A bad record, a stale hosts entry, or the wrong resolver."], widths=(4.6, 8.0))

    def ch_connect(self):
        self.stage("3 · Client: connect()  (1/2)", C_ORANGE, "Step three: connect. This one has the most branches.",
                   [["Host unreachable - network blockers", "no route (EHOSTUNREACH / ENETUNREACH); firewalls, security groups, NAT block the path"],
                    ["Port 8080 is not listening", "nothing bound -> kernel answers SYN with RST -> 'Connection refused' (ECONNREFUSED): fast and loud"],
                    ["Connections exceeded (client)", "client out of fds or ephemeral ports (32768-60999 = 28,232 per destination; TIME_WAIT holds them ~60 s)"],
                    ["Connections exceeded (server)", "accept queue / backlog full (somaxconn), fd limit, or SYN backlog full (SYN flood); behaviour not portable: refused or hang"]],
                   ["Host unreachable, because of network blockers. There is no route, or a firewall, security group or NAT blocks the path.",
                    "The port is not listening. Nothing is bound, so the kernel answers the SYN with an RST. Connection refused. Fast, and loud.",
                    "The number of connections is exceeded on the client. It is out of file descriptors, or out of ephemeral ports: thirty-two thousand seven hundred sixty-eight to sixty thousand nine hundred ninety-nine is twenty-eight thousand two hundred thirty-two per destination, and TIME_WAIT holds them for sixty seconds.",
                    "Or the number of connections is exceeded on the server: the accept queue is full, or the fd limit is hit, or the SYN backlog is full, in a SYN flood. The behaviour is not portable: it is refused, or it hangs."],
                   size=19, widths=(4.6, 8.2), row_h=1.0)

    def ch_connect2(self):
        self.new_slide("3 · Client: connect()  (2/2)", C_ORANGE, "Two more connect failures. The first is the silent one.")
        top = box("TCP timer for packet: no response to SYN", C_RED, w=7.2, h=0.8, size=24).shift(UP * 1.9)
        kids = VGroup(*[box(t, C_ORANGE, w=2.8, h=0.9, size=19) for t in ["No server", "Slow network /\npacket drops", "Handshake\nfailure", "Connect / dial\ntimeout"]]).arrange(RIGHT, buff=0.25).shift(UP * 0.4)
        with self.vo("The first is a TCP timer: no response to the SYN. That can mean there is no server, or a slow network with packet drops, or a handshake failure, or simply a connect or dial timeout."):
            self.play(FadeIn(top))
            self.play(FadeIn(kids, lag_ratio=0.2), run_time=2)
        t = T("SYN is retransmitted with exponential backoff until the connect / dial timeout (ETIMEDOUT). Silent and slow - looks like an overloaded server.", 21, C_YELLOW, maxw=12.4).shift(DOWN * 1.0)
        with self.vo("The SYN is retransmitted with exponential backoff until the connect timeout, which gives ETIMEDOUT. It is silent and slow, and looks exactly like an overloaded server."):
            self.play(FadeIn(t))
        t2 = VGroup(box("Stale DNS IP entry", C_PURPLE, w=4.0, h=0.8, size=22), T("a cached IP (TTL, /etc/hosts, client cache) points at a box that no longer serves", 21, WHITE, maxw=8)).arrange(RIGHT, buff=0.4).shift(DOWN * 2.4)
        with self.vo("The second: a stale DNS IP entry. A cached address, from the TTL, the hosts file, or a client cache, points at a box that no longer serves."):
            self.play(FadeIn(t2))

    def ch_write(self):
        self.stage("4 · Client: write()", C_GREEN, "Step four: write.",
                   [["Network issue -> packet drop -> write timeout", "the send buffer fills because the peer isn't ACKing; write blocks or times out"],
                    ["Physical machine shutdown", "peer gone; writes eventually fail (EPIPE / ECONNRESET); SIGPIPE kills the process if not handled"],
                    ["A network node in the path shuts down", "laptop network, Wi-Fi AP, or the server machine. TCP's connection = 4-tuple, so a network change kills it (QUIC connection IDs fix this)"],
                    ["Rate limit -> server logic -> close / stop reading", "the server closes deliberately, or stops reading so your writes block (TCP flow control / backpressure)"],
                    ["Rate limit -> you submitted very large content", "body too large (413 Payload Too Large); Expect: 100-continue asks first"]],
                   ["A network issue causes packet drops, and then a write timeout. The send buffer fills, because the peer is not acknowledging.",
                    "A physical machine shutdown. The peer is gone, writes eventually fail with EPIPE or ECONNRESET, and SIGPIPE kills the process if you do not handle it.",
                    "Some network node in the path shuts down: your laptop's network, a Wi-Fi access point, or the server machine. A TCP connection is the four-tuple, so a network change kills it. QUIC connection I Ds fix that.",
                    "A rate limit, driven by server business logic: the server closes, or stops reading, so your writes block. That is TCP flow control, or backpressure.",
                    "Or a rate limit because you submitted very large content. Four thirteen, Payload Too Large. Expect 100-continue asks first."],
                   size=18, widths=(4.8, 8.0), row_h=0.95, y=0.4)

    def ch_read(self):
        self.stage("5 · Client: read()", C_GREEN, "Step five: read.",
                   [["Server business logic -> access denied", "the server read your request and refused (401 / 403)"],
                    ["Network issue -> read timeout", "nothing arrives within the deadline - the work may or may not have been done"],
                    ["Rate limit", "429 Too Many Requests (often with Retry-After)"],
                    ["Server-side errors", "5xx"],
                    ["Server dropping the connection silently", "read returns 0 (EOF) or ECONNRESET; an idle timeout on the LB / NAT dropped it"]],
                   ["Access denied by the server's business logic: it read the request, and refused. Four oh one or four oh three.",
                    "A read timeout from a network issue. Nothing arrives within the deadline. And note: the work may or may not have been done.",
                    "A rate limit: four twenty-nine Too Many Requests, often with a Retry-After header.", "Server-side errors: the five hundreds.",
                    "Or the server drops the connection silently. Read returns zero, end of file, or ECONNRESET, because an idle timeout on a load balancer or NAT dropped it."],
                   size=20, widths=(5.0, 7.8), row_h=0.9)

    def ch_cdn(self):
        self.stage("6 · CDN", C_TEAL, "Step six: the CDN, which adds its own failure modes.",
                   [["DNS anycast", "the wrong or unhealthy PoP is chosen by BGP; routing changes mid-connection"],
                    ["Bad server: configuration / overwhelmed", "e.g. Fastly, 8 Jun 2021: one config change -> 85% of the network errored, 49 min"],
                    ["Stale information: bug / configuration", "the cache serves wrong or old content (poisoning, bad TTLs, stale playlists)"],
                    ["All the other TCP errors above", "every connect / read / write failure applies to the CDN's own hops"],
                    ["Same errors: edge <-> tier, mid-tier <-> origin", "each leg of the chain can fail on its own"]],
                   ["DNS anycast: BGP chooses the wrong or an unhealthy point of presence, or routing changes mid-connection.",
                    "A bad server, from configuration or overload. For example Fastly on the eighth of June twenty twenty-one: one config change, eighty-five percent of the network in errors, forty-nine minutes.",
                    "Stale information, from a bug or a configuration: the cache serves wrong or old content. Poisoning, bad TTLs, stale playlists.",
                    "All the other TCP errors discussed above apply to the CDN's own hops.",
                    "And the same errors can occur between the edge and the tiers, and between the mid-tier and the origin."],
                   size=20, widths=(5.0, 7.8), row_h=0.9)

    def ch_tls(self):
        self.stage("7 · SSL / TLS", C_RED, "Step seven: SSL and TLS.",
                   [["Invalid certificate", "expired (the 3 a.m. outage), wrong hostname, untrusted CA chain"],
                    ["Protocol mismatch: TLS 1.1 / 1.2 / 1.3", "client and server support no common version"],
                    ["Protocol mismatch: cipher mismatch", "no common cipher suite"],
                    ["SSL pinning mismatch", "the app pinned a specific cert / key; the server rotated it -> the app refuses"],
                    ["Incorrect date / time (server or client)", "the cert appears not-yet-valid or expired"],
                    ["Underlying TCP timeout", "TLS runs on TCP; any TCP failure surfaces here"]],
                   ["An invalid certificate: expired, which is the three A M outage, or the wrong hostname, or an untrusted CA chain.",
                    "A protocol mismatch: TLS one point one, one point two or one point three. The client and server support no common version.",
                    "A cipher mismatch: no common cipher suite.", "A pinning mismatch: the app pinned a specific certificate or key, and the server rotated it. The app refuses.",
                    "An incorrect date or time, on the server or the client. The cert appears not yet valid, or expired.", "And an underlying TCP timeout, because TLS runs on TCP."],
                   size=20, widths=(4.8, 8.0), row_h=0.85, y=0.5)

    def ch_http(self):
        self.stage("8 · HTTP  (1/2)", C_YELLOW, "Step eight: HTTP.",
                   [["HTTP protocol version error", "e.g. 505; an h2 preface sent to an h1 server -> 501; ALPN mismatch"],
                    ["Business logic: incorrect / missing headers", "app-level validation (missing auth header, wrong content-type)"],
                    ["Protocol requirements: incorrect / missing headers", "e.g. HTTP/1.1 without Host -> 400"],
                    ["Error code -> auth failure", "401 Unauthorized (server) / 407 Proxy Authentication Required (proxy)"]],
                   ["An HTTP protocol version error: five oh five, or an h2 preface sent to an h1 server, which gets a five oh one, or an ALPN mismatch.",
                    "Business logic: incorrect or missing headers. App level validation, like a missing auth header or the wrong content type.",
                    "Protocol requirements: incorrect or missing headers, like HTTP one point one without a Host header, which gets a four hundred.",
                    "An auth failure: four oh one Unauthorized from a server, or four oh seven Proxy Authentication Required from a proxy."],
                   size=20, widths=(5.2, 7.6), row_h=1.0)

    def ch_http2(self):
        self.stage("8 · HTTP  (2/2)", C_YELLOW, "The rest of the HTTP branch.",
                   [["4xx: 403 denied, 404 not found, 400", "client errors - retrying the same request won't help"],
                    ["5xx: 502 / 503 / 504", "502 Bad Gateway (bad response from upstream); 503 Service Unavailable (overloaded; may carry Retry-After); 504 Gateway Timeout (upstream didn't answer in time)"],
                    ["OPTIONS / preflight fails -> CORS", "the browser's CORS preflight was rejected -> the request is never sent"],
                    ["Read timeout (server / CDN)", "a proxy's upstream timeout (nginx proxy_read_timeout, ALB idle timeout: both default 60 s)"]],
                   ["The four hundreds: denied, not found, bad request. These are client errors, and retrying the same request will not help.",
                    "The five hundreds. Five oh two Bad Gateway: the proxy got a bad response from upstream. Five oh three Service Unavailable: overloaded or in maintenance, and it may carry Retry-After. Five oh four Gateway Timeout: upstream did not answer in time.",
                    "An OPTIONS preflight that fails: CORS. The browser's preflight was rejected, so the request is never sent.",
                    "And a read timeout at the server or CDN: a proxy's upstream timeout. nginx's proxy_read_timeout and an A L B's idle timeout both default to sixty seconds."],
                   size=20, widths=(4.8, 8.0), row_h=1.05)

    def ch_which_retry(self):
        self.new_slide("Which errors do you retry?", "So which errors should you retry?", C_GREEN)
        L = VGroup(T("RETRY (transient)", 28, C_GREEN), T("timeouts", 24), T("connection refused (it may come back)", 24), T("502 / 503 / 504", 24), T("429 - after Retry-After", 24), T("socket(): out of fds", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(LEFT * 3.5 + UP * 0.5)
        R = VGroup(T("DON'T RETRY", 28, C_RED), T("400 bad request", 24), T("401 / 403 denied", 24), T("404 not found", 24), T("anything non-idempotent, unless", 24), T("you made it safe to repeat", 24)).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(RIGHT * 3.5 + UP * 0.5)
        with self.vo("Retry the transient errors: timeouts, connection refused, since it may come back, five oh two, five oh three, five oh four, a four twenty-nine after the Retry-After, and a socket call that ran out of descriptors."):
            self.play(FadeIn(L))
        with self.vo("Do not retry four hundred, four oh one, four oh three or four oh four. The same request will fail the same way. And do not retry anything that is not idempotent, unless you made it safe to repeat."):
            self.play(FadeIn(R))
        t = T("Remember: a read timeout means the work may or may not have been done. 'The network is not a function call.'", 22, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("Remember that a read timeout means the work may or may not have been done. The network is not a function call."):
            self.play(FadeIn(t))

    def ch_backoff(self):
        self.new_slide("Retry with exponential backoff", "Now the retry toolkit. These are the concepts the course refers back to as week seven. A note: the map gives the failures. The toolkit is assembled from what the other sessions say about retries.", C_BLUE)
        ax = Axes(x_range=[0, 16, 1], y_range=[0, 5, 1], x_length=9, y_length=3.0, axis_config={"color": C_GREY, "include_ticks": False}).shift(UP * 0.3 + LEFT * 0.5)
        self.play(Create(ax), run_time=0.6)
        waits = [1, 2, 4, 8]
        t = 0
        marks = VGroup()
        with self.vo("Exponential backoff: wait longer after each failure. One second, two seconds, four seconds, eight."):
            for i, w in enumerate(waits):
                t += w
                d = Dot(ax.c2p(t, 0), color=C_ORANGE, radius=0.1)
                lab = T(f"try {i + 2}", 18, C_ORANGE).next_to(d, UP, buff=0.15)
                br = BraceBetween if False else None
                self.play(FadeIn(d), FadeIn(lab), run_time=0.7)
                marks.add(d, lab)
        pts = [("Where it shows up: select's NULL timeout (S3); SYN retransmits; Wi-Fi CSMA/CA random backoff (S2)", "You have already seen it. SYN retransmits. Wi-Fi's random backoff in CSMA slash CA. And the advice from session three: set a deadline, then retry with backoff.")]
        self.bullets(pts, size=22, shift=DOWN * 2.3)

    def ch_jitter(self):
        self.new_slide("Jitter, and retry storms", "But backoff alone is not enough. If every client backs off the same amount, they all come back at the same instant. That is a retry storm.", C_RED)
        random.seed(3)
        lab1 = T("No jitter: every client retries together", 24, C_RED).move_to([-3.6, 2.0, 0])
        lab2 = T("Full jitter: retries spread out", 24, C_GREEN).move_to([3.4, 2.0, 0])
        l1 = Line([-6.4, -1.5, 0], [-0.8, -1.5, 0], color=C_GREY)
        l2 = Line([0.8, -1.5, 0], [6.4, -1.5, 0], color=C_GREY)
        self.play(FadeIn(lab1), FadeIn(lab2), Create(l1), Create(l2))
        d1 = VGroup(*[Dot([-4.6 + 0.02 * random.random(), -1.5 + 0.18 * k, 0], radius=0.07, color=C_RED) for k in range(14)] + [Dot([-2.0 + 0.02 * random.random(), -1.5 + 0.18 * k, 0], radius=0.07, color=C_RED) for k in range(14)])
        d2 = VGroup(*[Dot([0.9 + 5.4 * random.random(), -1.5 + 0.18 * random.randint(0, 3), 0], radius=0.07, color=C_GREEN) for _ in range(28)])
        with self.vo("Without jitter, thousands of clients hit the server at exactly the same moments, and amplify the outage. Fifty million phones retrying a three oh three Slow Down without backoff is exactly this."):
            self.play(FadeIn(d1, lag_ratio=0.03), run_time=2)
        with self.vo("With full jitter, you randomise the wait, so the retries spread out. The session eight poller uses plus or minus twenty percent jitter, so fifty million phones do not poll on the same second."):
            self.play(FadeIn(d2, lag_ratio=0.03), run_time=2)
        t = T("Retry-After / 503 / 429: the server can also TELL you when to come back.", 24, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.5)
        with self.vo("And the server can help: Retry-After with a five oh three or a four twenty-nine tells you exactly when to come back."):
            self.play(FadeIn(t))

    def ch_breaker(self):
        self.new_slide("Circuit breaker", "A circuit breaker stops you from hammering a dependency that is already down.", C_ORANGE)
        c = box("CLOSED\ncalls flow", C_GREEN, w=3.0, h=1.3, size=24).move_to(LEFT * 4.2 + UP * 0.9)
        o = box("OPEN\nfail fast", C_RED, w=3.0, h=1.3, size=24).move_to(RIGHT * 4.2 + UP * 0.9)
        h = box("HALF-OPEN\nprobe with 1 call", C_YELLOW, w=3.4, h=1.3, size=22).move_to(DOWN * 1.9)
        a1 = Arrow(c.get_right(), o.get_left(), color=C_RED, buff=0.1)
        l1 = T("repeated failures", 20, C_RED).next_to(a1, UP, buff=0.1)
        a2 = Arrow(o.get_bottom() + LEFT * 0.5, h.get_right(), color=C_YELLOW, buff=0.1)
        l2 = T("after a pause", 20, C_YELLOW).next_to(a2, RIGHT, buff=0.1).shift(UP * 0.4)
        a3 = Arrow(h.get_left(), c.get_bottom() + RIGHT * 0.5, color=C_GREEN, buff=0.1)
        l3 = T("probe succeeds", 20, C_GREEN).next_to(a3, LEFT, buff=0.1).shift(UP * 0.5)
        with self.vo("In the closed state, calls flow normally."):
            self.play(FadeIn(c))
        with self.vo("After repeated failures, the breaker opens. You stop calling the dependency for a while, and fail fast."):
            self.play(GrowArrow(a1), FadeIn(l1), FadeIn(o))
        with self.vo("After a pause, it goes half open, and probes with a single call."):
            self.play(GrowArrow(a2), FadeIn(l2), FadeIn(h))
        with self.vo("If the probe succeeds, the breaker closes again. If it fails, it opens again. Failover is the sibling idea: primary to backup, whether that is an origin, a CDN, or a region."):
            self.play(GrowArrow(a3), FadeIn(l3))

    def ch_toolkit(self):
        self.new_slide("The retry toolkit (1/2)", "The toolkit in one table. Part one.", C_BLUE)
        tbl = self.table([["Concept", "What it means", "Where in the course"],
                          ["Timeouts / deadlines", "never wait forever; set connect, read, write timeouts", "select's NULL timeout (S3)"],
                          ["Retry + exponential backoff", "wait longer after each failure: 1, 2, 4 s", "SYN retransmits; CSMA/CA"],
                          ["Jitter (full jitter)", "randomise the wait", "S8 poller +/-20%"],
                          ["Retry storm", "many clients retrying at once amplify the outage", "S8: 50M clients on S3 503"],
                          ["Retry-After / 503 / 429", "the server says when to come back", "S8"],
                          ["Idempotency", "only retry what is safe to repeat", "RPC (S1); QUIC 0-RTT GET/HEAD (S5); MQTT QoS 1 (S8)"]],
                         [3.4, 5.4, 4.2], size=19, y=0.4, row_h=0.8)
        self.reveal_rows(tbl, ["Timeouts and deadlines: never wait forever.", "Retry with exponential backoff.", "Jitter.", "A retry storm.", "Retry-After, with five oh three and four twenty-nine.",
                               "And idempotency: only retry what is safe to repeat. The network is not a function call. QUIC zero RTT is only for GET and HEAD. MQTT quality of service one can duplicate messages, so you apply them by version number."])

    def ch_toolkit2(self):
        self.new_slide("The retry toolkit (2/2)", "Part two.", C_BLUE)
        tbl = self.table([["Concept", "What it means", "Where in the course"],
                          ["Which errors to retry", "transient yes; 400/401/403/404 no", "the mind map's 4xx vs 5xx split"],
                          ["Fallback is not retry", "try something DIFFERENT (another codec, CDN, rendition)", "S8: 'a codec fallback is not a retry'"],
                          ["Circuit breaker", "stop calling a failing dependency; fail fast; probe later", "S8 failover between CDNs"],
                          ["Failover", "primary -> backup (origin, CDN, region)", "S6 Worker; S8 multi-CDN"],
                          ["Serve stale / stale-if-error", "when the origin fails, the cache is the last thing standing", "proxy_cache_use_stale (S4); STALE (S6); RFC 5861"],
                          ["Negative caching", "cache errors briefly to shield a struggling origin", "S8: 5xx 1-2 s; 404 almost never"],
                          ["Graceful degradation", "something worse beats nothing", "S8 ABR: a stall is worse than a lower rendition"],
                          ["Thundering herd on recovery", "everything reconnects or refills at once", "proxy_cache_lock (S4); collapsing (S6)"],
                          ["Feature flags", "turn features off at runtime to shed load", "S6"]],
                         [3.4, 5.4, 4.2], size=17, y=0.0, row_h=0.62)
        self.reveal_rows(tbl, ["Which errors to retry.", "A fallback is not a retry. It tries something different: another codec, CDN or rendition.", "A circuit breaker.", "Failover.",
                               "Serve stale, also called stale-if-error. When the origin fails, the cache is the last thing standing.", "Negative caching: cache errors briefly, one to two seconds for five hundreds, to shield a struggling origin. Almost never for four oh fours.",
                               "Graceful degradation, or who decides what is worse. A stall is worse than a lower rendition.", "The thundering herd on recovery: everything reconnects or refills at once.", "And feature flags: turn features off at runtime to shed load."])

    def quiz(self):
        self.quiz_recap(7, [
            "The 8 branches in order: socket > DNS > connect > write > read > CDN > SSL/TLS > HTTP.",
            "socket(): out of descriptors -> retry later. DNS: no mapping (NXDOMAIN), timeout, misconfigured / stale.",
            "connect(): host unreachable; port not listening (RST = refused); client or server connection limits; no response to SYN (no server / drops / handshake failure / dial timeout); stale DNS IP.",
            "write(): packet drop -> write timeout; machine shutdown (SIGPIPE); a path node down; rate limit (server closes / stops reading; content too large 413).",
            "read(): access denied; read timeout (work may be done); rate limit 429; server errors; silent drop (EOF / RST).",
            "CDN: anycast, a bad / overwhelmed server, stale information, and every TCP error on the edge-tier and mid-tier-origin legs.",
            "TLS: invalid certificate, version / cipher mismatch, pinning mismatch, wrong clock, TCP timeout.",
            "HTTP: version error; missing headers; 401 / 407; 400 / 403 / 404; 502 / 503 / 504; CORS preflight failure; read timeout (proxy_read_timeout 60 s).",
            "Retry only transient errors, with exponential backoff + jitter; only idempotent operations; circuit breakers and failover; serve stale; negative caching.",
        ], "Here is what the quiz is most likely to ask from session seven.", size=24, per_page=5)
        self.say("That is session seven. Last one: session eight, streaming video at large scale.")
