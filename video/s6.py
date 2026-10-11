import math

from common import *


class S6(VScene):
    def construct(self):
        self.session_title(
            6, "(Ab)using CDNs", "Someone else's computers, closer to your users, and everything they can do while the traffic passes through",
            "Session six. Abusing CDNs. Someone else's computers, closer to your users, and everything they can do while the traffic is passing through.")
        self.ch_physics()
        self.ch_distance()
        self.ch_edge_buys()
        self.ch_what_is_cdn()
        self.ch_consistent_hash()
        self.ch_players()
        self.ch_anycast()
        self.ch_cache_defaults()
        self.ch_cache_status()
        self.ch_uncacheable()
        self.ch_esi()
        self.ch_delta()
        self.ch_cache_attacks()
        self.ch_bbr()
        self.ch_pool()
        self.ch_shield()
        self.ch_security()
        self.ch_waf()
        self.ch_rate()
        self.ch_ddos()
        self.ch_gateway()
        self.ch_handson()
        self.ch_workers()
        self.ch_bill()
        self.ch_ideas()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_physics(self):
        self.new_slide("Physics: the one number you can't optimise", "First, why the edge exists. Physics. The speed of light is the one number you cannot optimise.", C_BLUE)
        a = VGroup(T("Light in vacuum", 26, C_YELLOW), T("299,792 km/s", 34, WHITE)).arrange(DOWN, buff=0.15).move_to(LEFT * 3.5 + UP * 1.5)
        b = VGroup(T("Light in fibre", 26, C_ORANGE), T("~204,218 km/s  (about 2/3 c; index 1.468)", 28, WHITE), T("= 4.90 ms per 1000 km, one way", 28, C_GREEN)).arrange(DOWN, buff=0.15).move_to(RIGHT * 3.0 + UP * 1.5)
        with self.vo("Light in a vacuum travels at two ninety-nine thousand seven ninety-two kilometres a second. In fibre, about two thirds of that: two hundred four thousand kilometres a second, a refractive index of one point four six eight. That is four point nine milliseconds per thousand kilometres, one way."):
            self.play(FadeIn(a), FadeIn(b), run_time=1.5)
        tbl = self.table([["Route", "Round trip floor", "Measured / note"],
                          ["Mumbai - Chennai - back", "~10 ms", "ping 23 ms"],
                          ["Mumbai - Ashburn (us-east-1) - back", "126 ms", "can never go below"],
                          ["TLS 1.3 to Virginia: 3 RTTs to first byte", "~380 ms", "of nothing - no CPU helps"]],
                         [5.8, 3.2, 3.8], size=22, y=-0.9, row_h=0.8)
        self.reveal_rows(tbl, ["Mumbai to Chennai and back: about ten milliseconds as a floor. A measured ping is twenty-three.",
                               "Mumbai to Ashburn, Virginia, and back: one hundred twenty-six milliseconds as a floor. You can never go below that.",
                               "And TLS one point three needs three round trips to the first byte. That is about three hundred eighty milliseconds of nothing to Virginia. No CPU helps."])
        t = T("Hollow-core fibre would be 47% faster (Azure deploying, Sep 2025) - not on your path today.", 22, C_GREY, maxw=12.4).to_edge(DOWN, buff=0.4)
        with self.vo("Hollow core fibre would be forty-seven percent faster. Microsoft Azure started deploying it in September twenty twenty-five. It is not on your path today."):
            self.play(FadeIn(t))

    def ch_distance(self):
        self.new_slide("Distance charges you twice: latency AND loss", "Distance charges you twice: in latency, and in loss. This is Akamai data from twenty ten.", C_RED)
        tbl = self.table([["Distance", "RTT", "Loss", "Throughput", "4 GB download"],
                          ["Local < 100 mi", "1.6 ms", "0.6%", "44 Mbps", "12 min"],
                          ["Regional 500-1000 mi", "16 ms", "0.7%", "4 Mbps", "2.2 hrs"],
                          ["Cross-continent ~3000 mi", "48 ms", "1.0%", "1 Mbps", "8.2 hrs"],
                          ["Multi-continent ~6000 mi", "96 ms", "1.4%", "0.4 Mbps", "20 hrs"]],
                         [4.2, 1.6, 1.4, 2.4, 2.8], size=23, y=1.0, row_h=0.85)
        self.reveal_rows(tbl, ["Local, under a hundred miles: one point six milliseconds, point six percent loss, forty-four megabits, and a four gigabyte download in twelve minutes.",
                               "Regional: sixteen milliseconds, four megabits, two point two hours.", "Cross-continent: forty-eight milliseconds, one megabit, eight point two hours.",
                               "Multi-continent: ninety-six milliseconds, one point four percent loss, point four megabits, and twenty hours."])
        eq = VGroup(T("Mathis formula (1997)", 26, C_YELLOW), T("Throughput  ≈  MSS / ( RTT × √loss )", 36, WHITE)).arrange(DOWN, buff=0.2).shift(DOWN * 2.1)
        with self.vo("The Mathis formula, from nineteen ninety-seven: throughput is roughly the maximum segment size, divided by the round trip time times the square root of the loss. "
                     "A single TCP flow's ceiling falls with both the round trip time and the square root of loss. So the far edge is a hundred and ten times slower, not sixty times. HTTP two multiplexing and BBR exist to claw some of this back."):
            self.play(FadeIn(eq))

    def ch_edge_buys(self):
        self.new_slide("What the edge buys back", "What does an edge actually buy back? You are ten milliseconds from a Mumbai edge, which is one hundred ninety-four milliseconds from a Washington origin, with TLS one point three on every hop.", C_GREEN)
        self.bars([("direct, new connection", 621, C_RED), ("direct, kept alive", 208, C_ORANGE), ("edge, NO origin pool", 625, C_RED), ("edge, warm pool, new conn", 233, C_YELLOW),
                   ("edge, warm pool, kept alive", 209, C_ORANGE), ("edge cache HIT", 34, C_GREEN), ("edge HIT, kept alive", 11, C_GREEN)],
                  650, y0=1.9, gap=0.62, left=-2.4, width=6.4, label_w=4.4, size=20, unit=" ms",
                  narrs=["Direct to the origin on a new connection: six hundred twenty-one milliseconds. Three round trips.", "Direct, kept alive: two hundred eight. One round trip.",
                         "An edge with no origin pool, just a longer proxy: six twenty-five. No better.", "An edge with a warm origin pool: two thirty-three.", "Warm pool and kept alive: two oh nine, about the same as direct.",
                         "An edge cache hit: thirty-four milliseconds.", "And a hit on a kept alive connection: eleven."])
        t = T(wrap("A cache MISS through the edge is no faster than direct. The edge earns its place two ways: warm connections to origin (saves handshakes) and cache HITs (deletes the origin round trip: 194 ms -> 0).", 100), 20, C_YELLOW, maxw=12.4, line_spacing=0.9).to_edge(DOWN, buff=0.3)
        with self.vo("A cache miss through the edge is no faster than going direct, and sometimes slower. The edge earns its place in two ways: warm connections to the origin, which save handshakes, and cache hits, which delete the origin round trip. One hundred ninety-four milliseconds become zero."):
            self.play(FadeIn(t))

    def ch_what_is_cdn(self):
        self.new_slide("What a CDN is: a reverse proxy, rented in 300+ cities", "So what is a CDN? Session four's reverse proxy, rented in three hundred plus cities.", C_PURPLE)
        fl, _ = self.flow(["you", "edge PoP\ncache · TLS · WAF", "shield /\ntiered cache", "your origin"], [C_BLUE, C_ORANGE, C_PURPLE, C_GREEN], y=1.0, w=2.8, h=1.3, size=22, gap=0.5,
                          narrations=["You,", "ten milliseconds from an edge point of presence, with cache, TLS and a WAF,", "which talks to a shield, or tiered cache,", "which talks to your origin, over one long, controlled leg."])
        rows = [("Reverse proxy", "nginx (Session 4)"), ("Caching", "proxy_cache (Session 4)"), ("Connection pool", "upstream keepalive (Session 3)"), ("Anycast", "one IP in every city (Session 2 addressing)")]
        tbl = self.table([["Nothing new...", "...it's Sessions 2-4, rented"]] + [[a, b] for a, b in rows], [4.4, 6.4], size=23, y=-1.4, row_h=0.6)
        self.reveal_rows(tbl, ["Nothing here is new. The reverse proxy is nginx from session four.", "The caching is proxy_cache.", "The pool is upstream keepalive, from session three.", "And anycast puts one IP address in every city. Squid, by the way, did reverse proxy caching in nineteen ninety-six."])
        with self.vo("What geography adds: cheap handshakes near the user. The CDN owns both ends of the long leg, so it controls transport and pooling. A shield layer means many edges share one origin fetch. And one anycast address announced from every city."):
            pass

    def ch_consistent_hash(self):
        self.new_slide("Consistent hashing: the founding algorithm", "The founding algorithm of CDNs is consistent hashing. Karger and colleagues, STOC nineteen ninety-seven. Akamai was founded on it.", C_YELLOW)
        with self.vo("The problem: a hundred thousand URLs spread over ten caches. Now add an eleventh."):
            pass
        tbl = self.table([["Scheme", "URLs that move", "Busiest vs mean"],
                          ["hash(url) % N", "90.9%", "1.02x"],
                          ["consistent hash, 1 point per server", "3.3%", "2.93x (uneven)"],
                          ["consistent hash, 160 points per server", "8.2%  (~ 1/11)", "1.14x"]],
                         [6.6, 3.0, 3.2], size=24, y=1.1, row_h=0.9)
        self.reveal_rows(tbl, ["With hash of the URL modulo N, adding a server moves ninety point nine percent of the URLs. That is a near-total cache flush, and an origin stampede.",
                               "With consistent hashing and one point per server, only three point three percent move, but the load is uneven: the busiest server gets nearly three times the mean.",
                               "With a hundred sixty virtual points per server, about one eleventh move, exactly the new server's fair share, and the load is even: one point one four times the mean."])
        self.new_slide("Consistent hashing: the ring", "Let me show it on a ring.", C_YELLOW)
        center = LEFT * 3.2 + DOWN * 0.1
        R = 2.4
        ring = Circle(radius=R, color=C_DIM, stroke_width=3).move_to(center)
        self.play(Create(ring))
        node_ang = {"A": 20, "B": 110, "C": 200, "D": 290}
        cols = {"A": C_BLUE, "B": C_GREEN, "C": C_ORANGE, "D": C_PURPLE, "E": C_RED}
        keys = [12, 35, 52, 70, 88, 100, 125, 140, 150, 165, 178, 195, 215, 235, 255, 280, 300, 320, 340, 355]

        def pos(a, r=R):
            return center + np.array([r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 0])

        def owner(a, nodes):
            cands = sorted(nodes.items(), key=lambda kv: kv[1])
            for n, ang in cands:
                if ang >= a:
                    return n
            return cands[0][0]
        node_m = {}
        for n, a in node_ang.items():
            d = Dot(pos(a), radius=0.2, color=cols[n])
            lab = T(n, 22, WHITE).move_to(pos(a, R + 0.5))
            node_m[n] = VGroup(d, lab)
        key_m = [Dot(pos(a, R), radius=0.09, color=cols[owner(a, node_ang)]) for a in keys]
        with self.vo("Imagine a ring. Four cache servers sit at hashed positions on it. Each URL is also hashed to a point on the ring, and belongs to the first server it meets going around. The dots are colored by owner."):
            self.play(*[FadeIn(m) for m in node_m.values()], run_time=1.2)
            self.play(LaggedStart(*[FadeIn(k) for k in key_m], lag_ratio=0.05), run_time=2)
        new_ang = dict(node_ang)
        new_ang["E"] = 160
        e = VGroup(Dot(pos(160), radius=0.2, color=cols["E"]), T("E", 22, WHITE).move_to(pos(160, R + 0.5)))
        changed = [i for i, a in enumerate(keys) if owner(a, new_ang) != owner(a, node_ang)]
        with self.vo("Now add a fifth server, E. Only the keys between its predecessor and its own position change owner. Everyone else stays put. That is the whole trick."):
            self.play(FadeIn(e), run_time=0.8)
            self.play(*[key_m[i].animate.set_color(cols["E"]).scale(1.8) for i in changed], run_time=1.5)
        pts = VGroup(T("Modulo is a trap: adding a server", 24, C_RED), T("moves ~90% of URLs", 24, C_RED), T("Consistent hashing moves only the", 24, C_GREEN), T("new server's fair share ~ 1/(N+1)", 24, C_GREEN),
                     T("Virtual points even out the load", 24, WHITE), T("nginx:  hash $request_uri consistent;", 21, C_YELLOW, font=MONO, maxw=5.8),
                     T("(160 points / server, ketama-compatible)", 20, C_GREY, maxw=5.8)).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(RIGHT * 3.6 + DOWN * 0.1)
        with self.vo("Modulo is a trap. Consistent hashing moves only the new server's fair share, about one over N plus one. Virtual points, many per server, even out the load. "
                     "nginx offers this as hash, request URI, consistent, with a hundred sixty points per server, compatible with ketama. The same idea powers DHTs and sharded caches: choosing an owner without a central registry."):
            self.play(FadeIn(pts, lag_ratio=0.2), run_time=3)

    def ch_players(self):
        self.new_slide("The players", "Who are the players?", C_BLUE)
        tbl = self.table([["CDN", "Born", "Runs on / notable"],
                          ["Akamai", "1998", "own 'ghost' edge servers; ESI (2001); FastTCP -> BBR; consistent hashing"],
                          ["CloudFront", "2008", "AWS edge; BBR to viewers since 2019 (+22%)"],
                          ["Fastly", "2011", "heavily-modified Varnish + H2O; instant purge"],
                          ["Google Media CDN", "2022", "YouTube's edge opened up; QUIC / BBR everywhere"],
                          ["Broadpeak", "-", "born of video; operator / telco CDN; on GKE"],
                          ["Cloudflare", "2010", "nginx + LuaJIT (FL1) -> Rust (FL2, Oct 2025: -10 ms, +25%); origin proxy Pingora (2022)"]],
                         [3.0, 1.0, 8.8], size=20, y=0.4, row_h=0.8)
        self.reveal_rows(tbl, ["Akamai, nineteen ninety-eight. Its own ghost edge servers. It gave us ESI in two thousand one, moved from FastTCP to BBR, and was founded on consistent hashing.",
                               "Amazon CloudFront, two thousand eight, on the AWS edge. It has used BBR to viewers since twenty nineteen, for up to twenty-two percent more.",
                               "Fastly, two thousand eleven, a heavily modified Varnish, with instant purge.",
                               "Google's Media CDN, twenty twenty-two: YouTube's edge, opened up.", "Broadpeak, born of video: an operator or telco CDN for streaming. We will meet it in session eight.",
                               "Cloudflare, two thousand ten, was nginx plus LuaJIT, then Rust. Its second generation, F L two, shipped in October twenty twenty-five, ten milliseconds faster and twenty-five percent better. The origin facing proxy is Pingora, from twenty twenty-two."])

    def ch_anycast(self):
        self.new_slide("Anycast demo", "Anycast, which you can see for yourself.", C_TEAL)
        code = self.code_block(["$ curl -s https://www.cloudflare.com/cdn-cgi/trace", "colo=BOM   tls=TLSv1.3   kex=X25519MLKEM768",
                                "$ dig +short CHAOS TXT id.server @1.1.1.1", "\"BOM\"", "cf-ray: 8c1a...-BOM"], size=22, pos=UP * 1.2, hl={"BOM": C_YELLOW})
        with self.vo("Curl the trace endpoint, and it prints colo equals BOM. Colo is an I A T A airport code: BOM is Mumbai, DEL is Delhi, MAA Chennai, SIN, LHR, IAD for Ashburn. It also shows TLS one point three, and the key exchange X twenty-five five nineteen M L KEM, which is post-quantum."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=4))
        pts = [("dig CHAOS TXT id.server shows which resolver answered", "A dig for CHAOS TXT id dot server shows which resolver answered."),
               ("cf-ray ends with the colo: every response carries the PoP that served it", "And every response carries a cf-ray header whose suffix is the colo."),
               ("The PoP is chosen by BGP anycast, not by you: classroom Wi-Fi vs mobile data -> different colo, same IP", "The PoP is chosen by BGP anycast, not by you. Classroom Wi-Fi and mobile data give a different colo for the same IP.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 1.9)

    def ch_cache_defaults(self):
        self.new_slide("Caching defaults (Cloudflare)", "Now caching. First, the defaults.", C_GREEN)
        pts = [("Caches by file extension: 68 static extensions (css, js, png, jpg, webp, woff, mp4, pdf, zip...)", "Cloudflare caches by file extension: sixty-eight static extensions, like css, js, png, jpg, webp, woff, mp4, pdf and zip."),
               ("NOT cached by default: HTML, JSON, anything with Set-Cookie, or Cache-Control private / no-store / no-cache / max-age=0", "Not cached by default: HTML, JSON, anything with a Set-Cookie, or with Cache-Control private, no-store, no-cache or max-age zero."),
               ("Default edge TTL if the origin is silent: 200 / 301 -> 2 hours · 404 -> 3 minutes · others not cached", "If the origin is silent, the default edge TTL is two hours for two hundreds and three oh ones, three minutes for four oh fours, and the rest are not cached."),
               ("Default cache key = scheme + host + path + query. Cookies and most headers are NOT in the key", "The default cache key is scheme, host, path and query. Cookies and most headers are not in the key."),
               ("-> two users with different cookies share one object: fine for app.css, catastrophic for /account. Vary or a custom key says 'these differ'", "So two users with different cookies share one object. Fine for app dot css, catastrophic for slash account. Vary, or a custom key, is how you say these differ.")]
        self.bullets(pts, size=22, gap=0.4)

    def ch_cache_status(self):
        self.new_slide("cf-cache-status: eight states", "The cf-cache-status header has eight states.", C_GREEN)
        tbl = self.table([["Status", "Meaning", "Origin hit?"],
                          ["MISS", "eligible, not in cache, fetched", "yes"],
                          ["HIT", "served from cache, fresh", "no"],
                          ["EXPIRED", "was cached, TTL passed, re-fetched", "yes"],
                          ["REVALIDATED", "TTL passed, origin said 304 -> reused (ETag)", "cheap 304"],
                          ["UPDATING", "stale served now, refresh in background", "async"],
                          ["STALE", "origin down: serve stale anyway", "failed"],
                          ["DYNAMIC", "not eligible: never looked in cache (HTML default)", "yes"],
                          ["BYPASS", "eligible, but origin said no-store (or bypass rule)", "yes"]],
                         [2.6, 7.4, 2.4], size=20, y=0.2, row_h=0.62)
        self.reveal_rows(tbl, ["MISS: eligible, not in the cache, so it was fetched from the origin.", "HIT: served from cache, fresh. No origin hit.",
                               "EXPIRED: it was cached, the TTL passed, so it was re-fetched.", "REVALIDATED: the TTL passed, but the origin answered three oh four, so the cached copy was reused. A cheap hit.",
                               "UPDATING: stale content is served now, and refreshed in the background. Like proxy_cache_use_stale updating.", "STALE: the origin is down, so serve stale anyway. More in session seven.",
                               "DYNAMIC: not eligible, so it never looked in the cache. The default for HTML.", "BYPASS: eligible, but the origin said no-store, or a bypass rule matched."])

    def ch_uncacheable(self):
        self.new_slide("Caching the uncacheable: move personalisation outward", "How do you cache the uncacheable? Move the personalisation outward.", C_ORANGE)
        fl, _ = self.flow(["SSI\n1994\nthe server", "ESI\n2001\nthe edge", "Ajax\n~2005\nthe browser", "Railgun\n2013-2024\nthe delta"], [C_BLUE, C_ORANGE, C_GREEN, C_PURPLE], y=1.2, w=2.9, h=1.5, size=22, gap=0.45,
                          narrations=["SSI, Server-Side Includes, from NCSA HTTPd one point zero a one, in nineteen ninety-four. It predates CGI, and nginx still ships it. Holes in the HTML are filled by the server before sending.",
                                      "ESI, Edge-Side Includes, from Akamai and Oracle, a W three C note in two thousand one. The same holes, filled at the edge. Cache the shared shell everywhere, and assemble per user at the point of presence.",
                                      "Ajax, around two thousand five. Holes pushed to the browser. Cache the body on the CDN, and fetch the personal bits asynchronously.",
                                      "And Railgun, from Cloudflare, twenty thirteen to twenty twenty-four. Give up on caching the page, and send only the bytes that changed, a delta."])
        t = T("Arc: server -> edge -> browser. Only the small personal part is recomputed.", 26, C_YELLOW, maxw=12.4).shift(DOWN * 1.4)
        with self.vo("The arc is: server, edge, browser. Only the small personal part is recomputed."):
            self.play(FadeIn(t))

    def ch_esi(self):
        self.new_slide("ESI in numbers", "ESI, in numbers.", C_ORANGE)
        code = self.code_block(["<esi:include src=\"/fragment/user\"/>   <esi:include src=\"/fragment/cart\"/>", "Cache-Control: s-maxage=300     Surrogate-Control: content=\"ESI/1.0\""], size=19, pos=UP * 2.0,
                               hl={"esi:include": C_YELLOW, "s-maxage": C_GREEN})
        with self.vo("The origin sends one shell, with ESI include tags for the user fragment and the cart fragment, and Cache-Control s-maxage three hundred, plus a Surrogate-Control header marking it as ESI."):
            self.play(FadeIn(code))
        tbl = self.table([["100 logged-in users, 39,676 B page", "Origin requests", "Origin -> edge bytes", "Edge cache"],
                          ["Origin assembles", "100", "3,984,200", "DYNAMIC x100"],
                          ["ESI, edge assembles", "201", "83,454  (-98%)", "HIT x99, MISS x1"]],
                         [4.4, 2.4, 3.2, 2.9], size=21, y=0.1, row_h=0.9)
        self.reveal_rows(tbl, ["With a hundred logged-in users and a page of about forty thousand bytes, if the origin assembles every page: a hundred requests, nearly four million bytes from origin to edge, all dynamic.",
                               "With ESI: two hundred one requests, because each fragment is its own fetch, but only eighty-three thousand bytes. Ninety-eight percent less. And ninety-nine hits, one miss."])
        t = T("Origin bytes -98% · user download unchanged · origin requests UP. Load moves from origin rendering to edge assembly.", 22, C_YELLOW, maxw=12.4).shift(DOWN * 1.8)
        with self.vo("The trade: origin bytes drop ninety-eight percent, the user's download is unchanged, and origin requests go up. The load moves from origin rendering to edge assembly."):
            self.play(FadeIn(t))

    def ch_delta(self):
        self.new_slide("Delta / dictionary compression", "Delta compression, from Railgun to R F C ninety-eight forty-two. A twenty-four kilobyte news page, regenerated every minute.", C_PURPLE)
        self.bars([("gzip -6, no dictionary", 4276, C_RED), ("deflate, dict = page 1 min ago", 598, C_ORANGE), ("zstd, dict = page 1 min ago", 436, C_GREEN), ("zstd, dict = page 1 hour ago", 1277, C_YELLOW)], 4400,
                  y0=1.8, gap=0.8, left=-3.0, width=6.5, label_w=4.2, size=21, unit=" B",
                  narrs=["Gzip, with no dictionary: four thousand two hundred seventy-six bytes, seventeen point seven percent.", "Deflate, with the page from a minute ago as dictionary: five ninety-eight bytes, two point five percent.",
                         "Zstd with the same dictionary: four hundred thirty-six bytes. One point eight percent.", "Zstd with a dictionary from an hour ago: twelve seventy-seven. Five point three percent."])
        pts = [("Railgun: a daemon at the origin + a sender at the edge keep the last version of each page and send only the delta. Retired Jan 2024 - the network got fast, and a standard arrived", "Railgun kept the last version of each page at both ends and sent only the delta. It was retired in January twenty twenty-four, because the network got fast and a standard arrived."),
               ("RFC 9842, Compression Dictionary Transport (Sep 2025): the previous version is the dictionary. Available-Dictionary: <sha-256>; Content-Encoding: dcb / dcz. Same-origin, HTTPS-only, hashed", "That standard is R F C ninety-eight forty-two, Compression Dictionary Transport, from September twenty twenty-five. The browser's previous version is the dictionary. Headers: Available-Dictionary with a sha two fifty-six hash, and Content-Encoding dcb or dcz, for dictionary compressed brotli or zstd. It is same-origin and HTTPS only, because dictionaries leak, as with CRIME."),
               ("About 10x better than gzip - catch: the dictionary must be recent and identical on both ends", "About ten times better than gzip. The catch: the dictionary must be recent, and identical on both ends.")]
        self.bullets(pts, size=19, gap=0.3, shift=DOWN * 2.0)

    def ch_cache_attacks(self):
        self.new_slide("Two classic cache attacks", "Two classic cache attacks. A shared cache is a shared weapon.", C_RED)
        L = VGroup(T("Cache POISONING", 28, C_RED), T("James Kettle, 2018", 20, C_GREY), T(wrap("Origin reflects an UNKEYED header (X-Forwarded-Host: evil.example) into the page. One attacker request caches <script src=evil.example/app.js>. Every visitor gets it (HIT).", 34), 20, WHITE, maxw=6.0, line_spacing=0.9),
                   T(wrap("Fix: drop the unkeyed header at the edge, add it to the key, or Vary on it.", 34), 20, C_GREEN, maxw=6.0, line_spacing=0.9)).arrange(DOWN, buff=0.25).move_to(LEFT * 3.4 + UP * 0.3)
        R = VGroup(T("Cache DECEPTION", 28, C_ORANGE), T("Omer Gil, Black Hat 2017", 20, C_GREY), T(wrap("Trick the victim into loading /account/settings/fake.css. The edge sees '.css' and caches the victim's PRIVATE page. The attacker fetches the same URL from the cache.", 34), 20, WHITE, maxw=6.0, line_spacing=0.9),
                   T(wrap("Fix: don't cache by extension alone; honour the origin's content-type and no-store.", 34), 20, C_GREEN, maxw=6.0, line_spacing=0.9)).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.4 + UP * 0.3)
        with self.vo("Cache poisoning, by James Kettle, twenty eighteen. The origin reflects an unkeyed header, like X-Forwarded-Host, into the page. One attacker request caches a script tag pointing at the attacker's domain, and every visitor gets it, as a hit. "
                     "The fix: drop the unkeyed header at the edge, add it to the key, or Vary on it."):
            self.play(FadeIn(L), run_time=2)
        with self.vo("Cache deception, by Omer Gil, Black Hat twenty seventeen. Trick a victim into loading slash account slash settings slash fake dot css. The edge sees dot css and caches the victim's private page. The attacker fetches the same URL from the cache. "
                     "The fix: do not cache by extension alone. Honour the origin's content type and no-store."):
            self.play(FadeIn(R), run_time=2)
        t = T("Both = the cache key disagreeing with reality.", 28, C_YELLOW).to_edge(DOWN, buff=0.5)
        with self.vo("Both are the cache key disagreeing with reality."):
            self.play(FadeIn(t))

    def ch_bbr(self):
        self.new_slide("BBR on the CDN", "Moving bytes faster. BBR, again, now at CDN scale. Bottleneck Bandwidth and Round-trip propagation time, by Cardwell and colleagues at Google, twenty sixteen.", C_PURPLE)
        L = VGroup(T("CUBIC (loss-based)", 26, C_RED), T("fill the pipe until a drop, then halve", 22), T("on long lossy CDN paths it", 22), T("mistakes distance for congestion", 22, C_RED)).arrange(DOWN, buff=0.18).move_to(LEFT * 3.5 + UP * 1.3)
        R = VGroup(T("BBR", 26, C_GREEN), T("measures bottleneck bandwidth + min RTT", 22), T("and paces to that", 22), T("loss is not a congestion signal", 22, C_GREEN)).arrange(DOWN, buff=0.18).move_to(RIGHT * 3.5 + UP * 1.3)
        with self.vo("Loss-based CUBIC fills the pipe until a drop, then halves. On long, lossy CDN paths it mistakes distance for congestion."):
            self.play(FadeIn(L))
        with self.vo("BBR measures the bottleneck bandwidth and the minimum round trip time, and paces to that. Loss is not a congestion signal."):
            self.play(FadeIn(R))
        tbl = self.table([["Deployed", "Where", "Result"],
                          ["Google B4 + YouTube, 2016", "the paper", "2-25x CUBIC throughput; median RTT -53%"],
                          ["Amazon CloudFront, 2019", "edge -> viewer", "up to +22%; some US mobile +100%"],
                          ["Akamai, Nov 2019", "media", "BBR on >80% of end-user connections"],
                          ["Web census 2023", "top-10k sites", "BBR the most-deployed CCA; CUBIC ~7%"]],
                         [4.0, 2.6, 6.0], size=20, y=-1.5, row_h=0.62)
        self.reveal_rows(tbl, ["Google's B4 and YouTube, in twenty sixteen: two to twenty-five times CUBIC's throughput, and median round trip time down fifty-three percent.", "Amazon CloudFront in twenty nineteen: up to twenty-two percent, and some US mobile networks doubled.",
                               "Akamai, November twenty nineteen: BBR on more than eighty percent of end-user connections.", "And a twenty twenty-three web census: BBR is now the most deployed congestion control algorithm among the top ten thousand sites. CUBIC is about seven percent."])
        t = T("Only the SENDER changes: no new protocol, client or router. A CDN owns the sender on both legs, so it can just switch it on.", 21, C_YELLOW, maxw=12.4).to_edge(DOWN, buff=0.3)
        with self.vo("The key point: only the sender changes. No new protocol, no new client, no new router. A CDN owns the sender on both legs, so it can just switch it on."):
            self.play(FadeIn(t))

    def ch_pool(self):
        self.new_slide("Connection pooling to the origin", "Connection pooling to the origin. Three hundred visitors, fifty milliseconds between edge and origin, TLS one point three, and the origin closes idle connections after one second.", C_GREEN)
        self.bars([("no pool", 160, C_RED), ("32 worker pools", 112, C_ORANGE), ("8 worker pools", 74, C_YELLOW), ("1 shared pool", 57, C_GREEN)], 170, y0=1.6, gap=0.8, left=-3.0, width=6.0, label_w=3.4, size=22, unit=" ms",
                  narrs=["No pool: three hundred new connections, no reuse, a mean time to first byte of one hundred sixty milliseconds.", "Thirty-two worker pools: one sixty-four new connections, forty-five percent reuse, one twelve.",
                         "Eight worker pools: fifty-two new connections, eighty-three percent reuse, seventy-four.", "One shared pool: just four new connections, ninety-eight point seven percent reuse, fifty-seven milliseconds."])
        pts = [("A connection opened by one worker can only be reused by that worker (nginx's per-worker pools), so split pools stay cold", "A pooled connection opened by one worker can only be reused by that worker. That is nginx's per-worker pools. Split pools stay cold."),
               ("Cloudflare Pingora (shared pool, Sep 2022): one big customer's reuse went 87.1% -> 99.92% = 160x fewer new origin connections - '434 years of handshake time saved every day'", "Cloudflare's Pingora, with a shared pool, September twenty twenty-two: one big customer's reuse went from eighty-seven point one percent to ninety-nine point nine two. That is a hundred sixty times fewer new origin connections, and four hundred thirty-four years of handshake time saved every day."),
               ("Amortise the setup, across a continent - the setup is a 2-RTT TLS handshake", "Amortise the setup, across a continent. The setup is a two round trip TLS handshake.")]
        self.bullets(pts, size=19, gap=0.28, shift=DOWN * 2.0)

    def ch_shield(self):
        self.new_slide("Multiplexing, shielding, collapsing", "Multiplexing and shielding.", C_PURPLE)
        pts = [("CDNs use HTTP/2 on both legs in principle, but most CDN -> origin hops are still HTTP/1.1; cloudflared's http2Origin defaults to false. Pooling is what actually saves you today", "CDNs use HTTP two on both legs in principle, but most CDN to origin hops are still HTTP one point one. cloudflared's http2Origin setting defaults to false. Pooling is what actually saves you today."),
               ("Tiered cache / origin shield: without it, 300 edges MISS -> 300 origin requests for the same object (a built-in thundering herd). With it, edges fetch from a regional parent, which fetches once", "A tiered cache, or origin shield: without it, three hundred edges miss, and send three hundred origin requests for the same object. A built-in thundering herd. With it, edges fetch from a regional parent, which fetches once."),
               ("Request collapsing at one edge: 50 users, cold cache, 1 object -> 50 origin fetches without, 1 with (49 wait, then HIT). nginx's version = proxy_cache_lock", "Request collapsing at one edge: fifty users, a cold cache, one object. Without collapsing, fifty origin fetches. With it, one, and the other forty-nine wait, then hit. nginx's version is proxy_cache_lock."),
               ("Collapsing (one PoP) + tiered cache (across PoPs) = never fetch the same object twice at once: the CDN protects the origin during a spike instead of amplifying it", "Collapsing within one point of presence, plus tiered caching across them, means never fetching the same object twice at once. The CDN protects the origin during a spike, instead of amplifying it.")]
        self.bullets(pts, size=21, gap=0.4)

    def ch_security(self):
        self.new_slide("Not speed: the edge becomes the security perimeter", "Now, everything that is not speed. All requests are coming to the CDN anyway.", C_RED)
        chips = VGroup(chip("WAF: SQLi, XSS, traversal", C_RED, 24), chip("rate limiting", C_ORANGE, 24), chip("DDoS absorption", C_PURPLE, 24), chip("API gateway: auth, headers, route, fallback", C_BLUE, 24)).arrange(DOWN, buff=0.3).shift(UP * 0.5)
        with self.vo("So the CDN grows a WAF, that blocks SQL injection, cross-site scripting and path traversal. Rate limiting. DDoS absorption. And an API gateway: authentication, adding and stripping headers, routing, and fallback."):
            self.play(FadeIn(chips, lag_ratio=0.3), run_time=2.5)
        t = T("Speed got you to adopt it; control is why you can't leave.", 30, C_YELLOW).shift(DOWN * 2.4)
        with self.vo("Speed got you to adopt it. Control is why you cannot leave."):
            self.play(FadeIn(t))

    def ch_waf(self):
        self.new_slide("WAF: a denylist of spellings", "A WAF is a denylist of spellings. The bug still lives in your origin.", C_RED)
        tbl = self.table([["Payload", "Result"],
                          ["' OR 1=1 --", "blocked by rule sqli-tautology"],
                          ["'/**/OR/**/1=1--  (comments instead of spaces)", "5 rows LEAK"],
                          ["same, with normalisation (strip comments)", "blocked"],
                          ["' --   (no OR / UNION / digits)", "leaks again"]],
                         [7.0, 5.0], size=22, y=0.9, row_h=0.85)
        self.reveal_rows(tbl, ["The classic tautology, quote OR one equals one, is blocked by the rule.", "Replace the spaces with SQL comments, and five rows leak.",
                               "Add normalisation, stripping the comments, and it is blocked again.", "But a quote and a comment, with no OR, UNION or digits, leaks again."])
        pts = [("The arms race is normalisation (raw -> URL-decode -> strip comments -> ...) vs the number of spellings. It is never won outright", "The arms race is normalisation, against the number of spellings. It is never won outright."),
               ("A WAF buys time and blocks mass-scanned known payloads (Log4Shell, OWASP top). The real fix: bind parameters in the origin", "A WAF buys time, and blocks mass-scanned known payloads, like Log4Shell and the OWASP top ten. The real fix is to bind parameters, using parameterised queries, in the origin."),
               ("Cloudflare: Free Managed Ruleset on all plans; the OWASP Core ruleset needs Pro", "Cloudflare gives the Free Managed Ruleset on all plans. The OWASP core set needs Pro.")]
        self.bullets(pts, size=20, gap=0.3, shift=DOWN * 1.9)

    def ch_rate(self):
        self.new_slide("Rate limiting: '100 per 10 seconds' has five meanings", "Rate limiting. A hundred per ten seconds has five different meanings.", C_ORANGE)
        tbl = self.table([["Algorithm", "Burst at window edge", "Normal page load"],
                          ["Fixed window", "200 in one second", "all pass"],
                          ["Sliding log (exact)", "100", "all pass"],
                          ["Sliding window (estimate)", "104", "all pass"],
                          ["Token bucket", "109", "all pass"],
                          ["Leaky bucket, burst = 0", "10", "97% REFUSED"]],
                         [4.4, 4.2, 4.0], size=23, y=0.9, row_h=0.8)
        self.reveal_rows(tbl, ["Fixed window: a hundred requests at nine point nine nine nine seconds, and a hundred more at ten point oh oh one. Two hundred in one second.",
                               "A sliding log, which is exact, allows a hundred.", "A sliding window estimate allows about a hundred and four.", "A token bucket allows a hundred and nine.",
                               "A leaky bucket with no burst allows ten, but refuses ninety-seven percent of a normal page load, because a browser opens thirty requests at once."])
        pts = [("Cloudflare's answer (2017): the sliding-window ESTIMATE - weight the previous window by how much still overlaps; two counters per client; across 400M requests only 0.003% wrongly allowed or blocked", "Cloudflare's answer, in twenty seventeen, is the sliding window estimate. Weight the previous window by how much of it still overlaps. Two counters per client. Across four hundred million requests, only zero point zero zero three percent were wrongly allowed or blocked."),
               ("The free plan offers only the 10 s fixed window. nginx limit_req has a burst parameter for exactly this reason. Counts are per data centre, not global: a botnet across 330 cities gets 330 budgets", "The free plan offers only the ten second fixed window. nginx's limit_req has a burst parameter for exactly this reason. And counts are per data centre, not global. A botnet across three hundred thirty cities gets three hundred thirty budgets.")]
        self.bullets(pts, size=19, gap=0.3, shift=DOWN * 2.1)

    def ch_ddos(self):
        self.new_slide("DDoS: the one thing you can't do yourself", "DDoS. The one thing you genuinely cannot do yourself.", C_RED)
        big = VGroup(T("31.4 Tbps", 64, C_RED), T("largest DDoS on record - Cloudflare, Dec 2025", 24), T("Aisuru botnet, 1-4 million devices · lasted 35 s · mitigated automatically", 21, C_GREY, maxw=12)).arrange(DOWN, buff=0.2).shift(UP * 1.5)
        with self.vo("Thirty-one point four terabits per second. The largest DDoS on record, mitigated by Cloudflare in December twenty twenty-five. The Aisuru botnet, one to four million devices. It lasted thirty-five seconds, and was mitigated automatically."):
            self.play(FadeIn(big, lag_ratio=0.3), run_time=2)
        pts = [("Cloudflare's capacity: ~500 Tbps across 330+ cities. Volumetric floods are won with more capacity, and anycast splits the flood across locations. Your origin has one pipe", "Cloudflare's capacity is about five hundred terabits across more than three hundred thirty cities. Volumetric floods are won with more capacity, and anycast splits the flood across locations. Your origin has one pipe."),
               ("The catch: one network absorbing everyone's attacks is everyone's single point of failure. Fastly, 8 June 2021: one customer's config change -> 85% of the network returning errors -> Reddit, Spotify, gov.uk down; 49 minutes to recover", "The catch: one network absorbing everyone's attacks is everyone's single point of failure. Fastly, the eighth of June twenty twenty-one: one customer's config change sent eighty-five percent of the network into errors. Reddit, Spotify and gov dot uk went down. Forty-nine minutes to recover.")]
        self.bullets(pts, size=21, gap=0.4, shift=DOWN * 1.5)

    def ch_gateway(self):
        self.new_slide("API gateway at the edge (JWT)", "The edge as an API gateway, using JWTs.", C_BLUE)
        tbl = self.table([["Request", "Edge response"],
                          ["no token", "401"],
                          ["valid JWT", "edge sets X-User; origin returns data"],
                          ["expired JWT", "401"],
                          ["alg: none forgery", "refused - 'never let the token pick the algorithm'"],
                          ["client-sent X-User: admin", "ignored / overwritten"]],
                         [4.4, 8.0], size=22, y=1.1, row_h=0.8)
        self.reveal_rows(tbl, ["No token: four oh one.", "A valid JWT: the edge sets an X-User header, and the origin returns data.", "An expired token: four oh one.",
                               "A forged token with algorithm none: refused. Never let the token pick the algorithm.", "A client that sends its own X-User admin header: ignored, or overwritten."])
        pts = [("But: an attacker who hits the origin IP directly leaks everything. The gateway is only real if the origin can't be reached directly", "But an attacker who hits the origin IP directly gets everything. The gateway is only real if the origin cannot be reached directly."),
               ("Fix: mutual TLS (authenticated origin pulls) or a Tunnel - the origin only answers clients with the edge's certificate. And strip headers like X-Powered-By: PHP/5.4.45", "The fix: mutual TLS, called authenticated origin pulls, or a tunnel, so that the origin only answers clients that hold the edge's certificate. And practise header hygiene: strip X-Powered-By.")]
        self.bullets(pts, size=21, gap=0.35, shift=DOWN * 2.0)

    def ch_handson(self):
        self.new_slide("Cloudflare hands-on", "Cloudflare hands-on. Some demos need no account.", C_ORANGE)
        pts = [("trace for colo / TLS / kex · dig CHAOS TXT id.server · curl -sI for cf-ray, cf-cache-status, age, alt-svc", "No account needed: the trace endpoint, dig CHAOS, and curl dash capital I for cf-ray, cf-cache-status, age and alt-svc."),
               ("TLS time Mumbai vs Virginia (curl -w '%{time_appconnect}' to DynamoDB regional endpoints)", "Compare TLS time from Mumbai and from Virginia, using curl with time_appconnect against regional endpoints."),
               ("cloudflared tunnel --url http://localhost:8000 -> https://<rand>.trycloudflare.com. Quick Tunnel: no account, no DNS; 200 in-flight limit, no SSE, testing only. The echo server shows CF-Connecting-IP, CF-Ray, CDN-Loop - and few TCP connections: the pool", "And a Quick Tunnel: cloudflared tunnel dash dash url, pointing at localhost. You get a trycloudflare dot com address. No account, no DNS. Limits: two hundred in-flight, no server-sent events, testing only. The echo server prints CF-Connecting-IP, CF-Ray and CDN-Loop, and shows very few TCP connections. That is the pool.")]
        self.bullets(pts, size=21, gap=0.4, shift=UP * 1.0)
        tbl = self.table([["Dashboard action (free plan)", "Point", "Limit"],
                          ["Orange vs grey cloud", "origin IP vanishes behind anycast", "-"],
                          ["Cache an HTML page", "MISS > HIT > purge > MISS; Age climbs", "10 rules"],
                          ["WAF custom rule", "the same bypasses", "5 rules, no regex"],
                          ["Rate-limit /api/*", "~20 pass, then 429; per colo", "1 rule, 10 s only"],
                          ["Transform Rules", "strip X-Powered-By", "unlimited"],
                          ["Deploy a Worker", "code at the edge", "100k req/day"]],
                         [4.3, 5.2, 3.2], size=19, y=-1.9, row_h=0.5)
        with self.vo("On the dashboard, free plan: the orange cloud versus the grey cloud, which hides your origin IP behind anycast. Cache an HTML page, and watch miss, hit, purge, miss, with the Age header climbing. A WAF custom rule. A rate limit that passes about twenty requests and then returns four twenty-nine, per colo. "
                     "A transform rule to strip X-Powered-By. And a Worker, deployed with wrangler, up to a hundred thousand requests a day."):
            self.reveal_rows(tbl, with_lines=False)

    def ch_workers(self):
        self.new_slide("Workers: Session 3's question, answered again", "Workers. Session three's question, answered again.", C_PURPLE)
        fl, _ = self.flow(["CGI\nforked per request", "FastCGI\nkept warm", "nginx\nevent loop", "Workers\nruntime resident\nin every PoP"], [C_RED, C_ORANGE, C_BLUE, C_GREEN], y=1.0, w=2.9, h=1.5, size=21, gap=0.4,
                          narrations=["CGI forked a process per request.", "FastCGI kept it warm.", "The nginx event loop removed the worker.", "Workers: the runtime is already resident in every point of presence, and your code just runs in it. Amortise the setup, at the edge."])
        pts = [("A Worker is a V8 isolate, not a process: starts in ~5 ms with ~3 MB, vs a container's 35 MB plus cold start", "A Worker is a V eight isolate, not a process. It starts in about five milliseconds, using about three megabytes, against a container's thirty-five megabytes plus a cold start."),
               ("Example: rate limit by IP, verify a JWT (WebCrypto), set X-User, fetch(origin) with primary -> backup failover. Tested locally in workerd. The ESI worker has a framing bug - 'where does this element end?' - which is why HTMLRewriter exists", "An example worker rate limits by IP, verifies a JWT with WebCrypto, sets X-User, and fetches the origin with failover from primary to backup. It is tested locally in workerd. The ESI worker had a framing bug: where does this element end? That is why HTMLRewriter exists.")]
        self.bullets(pts, size=21, gap=0.4, shift=DOWN * 1.7)

    def ch_bill(self):
        self.new_slide("The bill: what you hand over", "The bill. What you hand over.", C_RED)
        tbl = self.table([["You hand over", "Detail"],
                          ["Your TLS private keys", "the edge terminates HTTPS, so it can read every byte"],
                          ["A single point of failure", "Fastly, 8 Jun 2021: 85% of the network errored, 49 minutes"],
                          ["Power to see and shape traffic", "domain fronting - banned by AWS & Google (2018), Azure (2022), Fastly (Feb 2024)"],
                          ["Lock-in by architecture", "WAF, rate limits, auth, Workers at the edge: a security perimeter, not a swappable cache"]],
                         [4.3, 8.4], size=21, y=0.8, row_h=1.0)
        self.reveal_rows(tbl, ["Your TLS private keys. The edge terminates HTTPS, so it can read every byte.", "A single point of failure. Fastly, June twenty twenty-one.",
                               "The power to see and shape traffic. Domain fronting, which hid censored traffic behind innocent domains, was banned by AWS and Google in twenty eighteen, Azure in twenty twenty-two, and Fastly in February twenty twenty-four.",
                               "And lock-in by architecture. WAF, rate limits, auth and Workers at the edge make it your security perimeter, not a swappable cache."])

    def ch_ideas(self):
        self.new_slide("Four ideas from Session 6", "Four ideas from this session.", C_GREEN)
        pts = [("1. Move the work, or move the data - content closer (cache), or personalisation outward (SSI > ESI > Ajax)", "One. Move the work, or move the data. Content closer, with a cache. Or personalisation outward: SSI, ESI, Ajax."),
               ("2. The edge is wherever all the traffic converges - firewall, rate limiter, DDoS scrubber, auth and code followed the traffic", "Two. The edge is wherever all the traffic converges. The firewall, the rate limiter, the DDoS scrubber, auth and code all followed the traffic."),
               ("3. It's all Sessions 2-5, rented by the city - reverse proxy, pooling, ETag revalidation, BBR, multiplexing, consistent hashing", "Three. It is all sessions two to five, rented by the city. Reverse proxy, pooling, ETag revalidation, BBR, multiplexing, consistent hashing."),
               ("4. Concentration cuts both ways - it absorbs 31 Tbps; one config bug takes 85% down", "Four. Concentration cuts both ways. It absorbs thirty-one terabits, and one config bug takes eighty-five percent of the network down.")]
        self.bullets(pts, size=24, gap=0.5)

    def quiz(self):
        self.quiz_recap(6, [
            "Fibre ~ 2/3 c, ~204,000 km/s, 4.9 ms per 1000 km one way. Mumbai-Ashburn RTT floor 126 ms; Mumbai-Chennai ~10 ms.",
            "Mathis: throughput ~ MSS / (RTT x sqrt(loss)). The edge saves handshakes (warm pool) and, on a HIT, the whole origin round trip. A MISS is no faster than direct.",
            "CDN = reverse proxy + cache + pool + anycast in 300+ cities. colo = IATA code; the cf-ray suffix = colo.",
            "Consistent hashing (Karger 1997, Akamai): modulo moves ~90%; consistent ~1/(N+1); 160 virtual nodes; nginx 'hash ... consistent' (ketama).",
            "Akamai 1998 (ESI); CloudFront 2008; Cloudflare 2010 (nginx+LuaJIT -> Rust FL2; Pingora); Fastly 2011 (Varnish); Google Media CDN 2022; Broadpeak (video).",
            "Default: cache by extension (68); HTML / JSON not cached; key = scheme+host+path+query; TTL 200/301 = 2 h, 404 = 3 min.",
            "cf-cache-status: MISS, HIT, EXPIRED, REVALIDATED, UPDATING, STALE, DYNAMIC, BYPASS.",
            "SSI 1994 (server) > ESI 2001 (edge) > Ajax 2005 (browser) > Railgun 2013-2024 (delta). RFC 9842: Available-Dictionary, dcb / dcz.",
            "Poisoning (Kettle 2018, unkeyed header) vs deception (Gil 2017, fake .css path). BBR: Google 2016, sender-only change, now the most-deployed CCA.",
            "Shared pool beats per-worker pools (Pingora 87.1% > 99.92%). Tiered cache, request collapsing, proxy_cache_lock.",
            "WAF = a denylist of spellings; fix with parameterised queries. Rate limiting: fixed window allows 2x bursts; leaky bucket with no burst refuses real browsers; Cloudflare = sliding-window estimate; counts are per colo.",
            "DDoS record 31.4 Tbps (Dec 2025, Aisuru, 35 s). Fastly outage 8 Jun 2021, 85%, 49 min. Gateway: refuse alg:none; lock the origin (mTLS / tunnel). Workers = V8 isolates (~5 ms, ~3 MB). Domain fronting banned.",
        ], "Here is what the quiz is most likely to ask from session six.", size=23, per_page=4)
        self.say("That is session six. Next up, session seven: building for failures.")
