# CN Quiz Cheat Sheet (Sessions 1–8) — compressed for MCQs

Format: facts you can be asked, plus **⚠ traps** (the wrong option MCQs love). Source: CN_Master_Notes.md.

---

## S1 — Sockets
- **Server:** socket → bind → listen → accept → read → write → close. **Client:** socket → connect → read/write → close (**no bind, no listen**).
- `listen(fd, N)`: N = **accept-queue depth, NOT a connection limit**; Linux caps at `net.core.somaxconn`.
- No listener → kernel sends **RST** → "Connection refused" (fast). Listening but never `accept()` → **handshake completes in kernel, client hangs**.
- Ports **<1024 need root**. Ephemeral range **32768–60999** (28,232 ports), kernel picks at `connect()`. TIME_WAIT ≈ **60 s** (2 MSL).
- `AF_INET` = IPv4, `SOCK_STREAM` = TCP, `SOCK_DGRAM` = UDP. `INADDR_ANY` = all interfaces.
- **SIGPIPE = 13** (write to closed peer kills process). SIGINT 2, SIGKILL 9 (uncatchable), SIGTERM 15.
- `SO_LINGER {1,0}` → close sends **RST**, no TIME_WAIT, data discarded. `SO_REUSEADDR` → fixes "address already in use" (TIME_WAIT).
- `htons`: host→network short. 2026 = **0x07EA**, wire `07 EA` (**big-endian**).
- `gethostbyname`: /etc/hosts first → UDP to resolver → root→TLD→authoritative; cached by TTL; **IPv4-only, not thread-safe** → use `getaddrinfo`.
- `fork()` returns **0 child, >0 parent (child PID), −1 failure**.
- **select**: O(n), FD_SETSIZE **1024**. **epoll**: O(ready). kqueue = BSD/macOS, IOCP = Windows, io_uring = modern Linux.
- Tools: telnet (text protocols), `openssl s_client` (TLS), `nc` (anything), tcpdump/Wireshark.
- **TLS secures TCP, not HTTP.** Asymmetric → agree on key; symmetric → bulk data. Pinning bypasses CA trust.
- **Framing (3 ways):** fixed length · delimiter · length prefix. TCP is a **byte stream**, not messages.
- **BCD** = 4 bits/digit. **ASN.1** (1984): schema → generated codec (X.509, LDAP, SNMP, telecom). **TLV**: skip unknown types via length → forward-compatible (TLS ext, protobuf, ISO 8583). **base64 = +33%** (3 B → 4 chars).
- **gRPC** = RPC + protobuf over **HTTP/2**; can't curl it. "The network is not a function call."
- Text protocols: debuggable, verbose. Binary: compact, needs tools.

## S2 — OSI / SS7 / TCP / text protocols
- **OSI:** L7 App (HTTP, FTP, DNS, SMTP) · L6 Presentation (encrypt/compress) · L5 Session · L4 Transport (TCP/UDP) · L3 Network (IP, ICMP) · L2 Data link (Ethernet, MAC, ARP, switch) · L1 Physical.
- **Ethernet = CSMA/CD (detect)**; **Wi-Fi = CSMA/CA (avoid)** — radio can't listen while sending; random backoff; **L2 ACK on every frame**; ~2 ms contention.
- Sizes: MAC 6 B, EtherType 2 B (**0x0800 = IPv4**), payload/MTU **1500**, FCS 4 B (CRC-32), frame **1518**. IP hdr **20**, TCP hdr **20**, UDP hdr **8**. **MSS = 1500−20−20 = 1460**. IP proto **6 TCP / 17 UDP / 132 SCTP**.
- Starlink: LEO ~550 km, ~20 ms; IP header unchanged except TTL/checksum/NAT — layering argument.
- **UDP header:** src port, dst port, length, checksum (2 B each = 8 B).
- **SS7 (1975):** out-of-band signalling; killed **blue boxes (2600 Hz in-band tone)**. Voice = **64 kbps DS0**. Stack: MTP1/2/3, SCCP, TCAP, MAP/ISUP. MTP2 uses CRC-16.
- **SMS:** 140 octets (TP-UD) ≤ MAP ~200 ≤ MTP2 SIF 272. **160 chars GSM-7 (7 bit)**, **70 UCS-2** (emoji). `mo-ForwardSM` opCode **46**. **SMSC = store & forward**; **HLR** = subscriber DB (`sendRoutingInfoForSM` → IMSI + serving MSC). No segmentation needed.
- **ISUP call:** IAM → ACM → ANM → (voice on separate bearer) → REL → RLC.
- **SIP:** INVITE → 100 Trying → 180 Ringing → 200 OK → ACK → RTP/SRTP over UDP → BYE. (HTTP-shaped, text.)
- **SS7 reliability = per hop; TCP = end-to-end.** SS7 congestion hop-by-hop; TCP end-to-end. FSN 7-bit (wraps 128); TCP seq 32-bit per byte.
- **Loss-based CC (Reno/CUBIC):** sawtooth, bufferbloat. **BBR (Google 2016):** bottleneck bandwidth × min RTT, ignores loss.
- **Handshake:** SYN → SYN-ACK → ACK. **SYN and FIN each consume 1 seq number.** Random ISN (RFC 6528; **Mitnick** attack on predictable ISN).
- **SYN flood** fills half-open backlog. **SYN cookies (1996):** state encoded in server ISN (keyed hash of 4-tuple+time+MSS); **cost: lose window-scale/SACK/timestamps**; only under pressure.
- **Close = 4 segments** (FIN+ACK can't merge; half-close). **CLOSE_WAIT piling up = app forgot `close()`**. TIME_WAIT = 2 MSL on the side that closes first.
- **RTTs before first byte:** TCP 1 · +TLS1.2 **3** · +TLS1.3 **2** · QUIC **1** · 0-RTT 0 extra. Mumbai–Virginia ~190 ms.
- **QUIC:** over UDP, userspace, per-stream sequence → no TCP HOL; TLS 1.3 built in.
- **SMTP ports:** **25** relay · **587** submission + STARTTLS · **465** implicit TLS. POP3 **110**/995 · IMAP **143**. No auth in base SMTP; **SPF/DKIM/DMARC** patch. **Envelope (MAIL FROM/RCPT TO) ≠ headers (From/To)**. DATA ends with lone **"."** (dot-stuffing). Blank line separates headers/body.
- SMTP session: EHLO → MAIL FROM → RCPT TO → DATA → … → `.` → QUIT. Demo tools: mailpit (1025/8025), greenmail (3025/3110).
- **MIME/base64:** 4×6-bit chars, **76 chars/line**, +33%, `=` padding, "Man" → "TWFu". Multipart boundary `--x`, end `--x--`.
- **POP3:** USER, PASS, **STAT, LIST, RETR, DELE** (applied on QUIT); state on client. **IMAP:** state on server, folders, SEARCH, IDLE, partial FETCH, flags `\Seen`.
- **FTP:** control **21**, data new connection each time. **Active:** server connects from **port 20** into client (NAT blocks). **Passive (PASV, 227):** client opens both. Port = **p1×256+p2** (117,48 → 30000).
- **Framing examples:** SMTP dot (delimiter), SMS TP-UDL (length), IMAP `{310}` (both), HTTP/1.1 (both), FastCGI (both).

## S3 — Scaling servers
- Fork per conn (isolated, costly) / thread per conn (cheaper) / **event loop (select/epoll) scales**. Production = **pre-forked workers each running epoll + SO_REUSEPORT**.
- select args: `nfds=maxfd+1, readfds, writefds, exceptfds, timeout`. **NULL timeout = block forever.**
- **`ulimit -n` does NOT fix select** (FD_SETSIZE = compiled bitmap, 1024). epoll: `epoll_ctl` (register) / `epoll_wait`.
- **CGI:** fork+exec per request; headers → env vars (`REQUEST_METHOD`, `QUERY_STRING`, `HTTP_USER_AGENT`); stdin = body, stdout = response, stderr = error log. Output: headers, blank line, body.
- **mod_php/mod_perl:** in-process, **a segfault kills the server**. **FastCGI:** persistent pool (php-fpm) over socket; binary records; **empty record ends a stream**; stderr separate record type. **Servlets:** Tomcat/Jetty, thread pool in JVM, class-loader isolation.
- **HTTP stateless → horizontal scaling**. DBs (Redis RESP, MySQL, Kafka, MQTT) use own protocols + persistent connections.
- **Four walls:** file descriptors · memory · context switches/kernel tax · queueing.
- **C10K:** Dan Kegel **1999**. **C10M:** Robert Graham **2013**. Today 2–3 M conns/box.
- **Thread stack 8 MB** (10k threads ≈ 80 GB) vs **goroutine 2 KB** (4000× smaller; netpoller on epoll).
- Kernel bypass: **DPDK, netmap, mTCP, Seastar**. Fewer syscalls: **sendfile**, **io_uring**.
- **Little's Law: concurrency = throughput × latency.** (10k rps × 100 ms = 1000; × 1 s = 10,000.) "Slowness is a memory bug."
- **Apache MPMs:** prefork (process/conn) → worker (threads) → **event** (listener thread parks idle keep-alive on epoll; default since 2.4).
- **HAProxy 2001:** LB as a tier; select first; epoll Linux 2.5.44 (2002); multi-thread **1.8 (2017)**.
- **Varnish 2006:** caching reverse proxy in front of origin (Squid = forward, near clients); **Fastly built on Varnish/VCL**.
- **nginx 2004:** master + one worker/core, epoll, **sendfile** (zero-copy); thread pool since **1.7.11**.

## S4 — nginx
- **CERN httpd (Berners-Lee, NeXT, 1990)** = first server. **Mosaic = browser (1993)**. **NCSA HTTPd (Rob McCool 1993) → CGI.** Apache 1995 ("a patchy server"), #1 from 1996. ⚠ Mosaic did NOT become Apache.
- Apache 1.3 prefork → 2.0 worker → 2.4 event. Servlet 1997, J2EE 1999.
- **nginx:** Igor Sysoev, Rambler; started **2002**; public **4 Oct 2004** (Sputnik anniv.); **1.0 in Apr 2011**. Apache asked "cheaper worker?"; nginx asked "why a worker per connection?" → reverse proxy, not app server.
- **Master** = bind, config, fork, signals (never touches connections). **Workers** = one event loop each. + **cache manager** (LRU evict) + **cache loader**.
- Loop (`ngx_process_events_and_timers`): find timer → `epoll_wait(timer)` → posted accept → unlock → expire timers → posted events. Timer = arg to sleep.
- `ngx_accept_disabled = connection_n/8 − free_connection_n` → **7/8 rule**. `accept_mutex` **off by default since 1.11.3**; EPOLLEXCLUSIVE (Linux 4.5), SO_REUSEPORT.
- **Stale event bug:** batch from epoll_wait, fd closed/recycled → nginx uses **low bit of pointer as "instance" flag**.
- **select:** watch list in your process, O(n) ×3; ceiling 1024; `ulimit` irrelevant. **epoll:** watch list in kernel, O(ready). (10,000 idle/10 active: 30,000 vs 10 units.)
- **sendfile:** read+write = 4 copies, 2 mode switches → sendfile = **2 DMA copies, 0 switches**. ⚠ **gzip/TLS/templating need bytes in user space → conflict with sendfile** (kTLS exists). Loopback benchmark: roughly equal time, but 2048 syscalls → 1.
- **Forward proxy** (Squid 1996; near clients) vs **reverse proxy** (near servers; TLS termination; **absorbs slow clients**).
- **Cache directives:** `keys_zone=demo:10m` = shared-mem **index** (rbtree + LRU; **~8,000 keys/MB**), not data. `levels=1:2` dir fanout. `max_size` disk cap. **`inactive`** = evict if unread (regardless of TTL). **`proxy_cache_valid`** = freshness TTL. ⚠ different things.
- **`proxy_cache_lock on`** = anti-stampede, **OFF by default**. **`proxy_cache_use_stale updating error timeout http_5xx`** = serve stale. `X-Cache-Status $upstream_cache_status`.
- LRU eviction: take tail; skip if `count != 0` (being streamed).
- **location precedence:** `=` exact (stop) → longest prefix (if **`^~`** → stop, skips regex) → **regex `~` first match in file order** → else longest prefix. ⚠ `/images/a.php` with `^~ /images/` + `~ \.php$` → **the `^~` block**. Prefixes = ternary search tree (longest wins); regexes = array (first wins). **No .htaccess** (avoids stat per dir).
- **Smooth WRR 3:1 → a b a a** (not a a a b).
- **`try_files`**: last arg = fallback, **never tested**. `@name` = named location (only from try_files/error_page).
- **Parser:** resumable state machine, **27 states** for request line, no regex/alloc. **11 phases:** POST_READ, SERVER_REWRITE, FIND_CONFIG, REWRITE, POST_REWRITE, PREACCESS, ACCESS, POST_ACCESS, PRECONTENT, CONTENT, LOG. `NGX_OK` = suspended. Modules: limit_req→PREACCESS; auth_basic→ACCESS; try_files→PRECONTENT; proxy_pass/fastcgi/static→CONTENT.
- **Memory pools (`ngx_palloc`):** destroy pool at request end. `ngx_queue.h` = intrusive doubly-linked list.
- src dirs: core, event (epoll/kqueue/select/poll/devpoll/eventport), http, os/unix, **stream (L4 TCP/UDP LB)**, **mail (IMAP/POP3/SMTP proxy)**.
- **FastCGI header = 8 bytes** (version, type, requestId[2], contentLength[2], padding, reserved). BEGIN_REQUEST `01 01 00 01 00 08 00 00`. Empty PARAMS (type 4, len 0) = end.
- Four ideas: ask the other question · check if constraint still exists (goroutines/virtual threads revive thread-per-conn) · data structure is documentation · amortise setup (**upstream keepalive**).

## S5 — HTTP evolution
**RFC map:** 1945 = HTTP/1.0 (May 1996) · 2068 = 1.1 (Jan 1997) · 2616 (Jun 1999) · 7230–7235 (2014, six docs) · **9110 semantics / 9111 caching / 9112 h1.1 / 9113 h2 / 9114 h3** (2022) · 7540 (h2) + 7541 (HPACK) 2015 · 9000 QUIC · 9001 QUIC-TLS · 9204 QPACK · 7301 ALPN · 7838 Alt-Svc · 9460 HTTPS RR · 8297 Early Hints · 2324 teapot (418) · 896 Nagle · 1122 delayed ACK.

**HTTP/1.0:** GET/HEAD/POST; 16 headers; **one request per connection** (close after each); **no Host** (1 IP = 1 site); caching by `Last-Modified`/`If-Modified-Since`/`Expires` (timestamp: no sub-second, clock drift, mtime ≠ identity). 24 objects @200 ms = 9.6 s. ⚠ 1.0 has a *serialisation cost*, not true HOL (HOL needs pipelining).

**HTTP/1.1 (1997):**
- **Persistent by default**; opt out with `Connection: close`.
- **Host is MUST** → missing = **400**. SNI = TLS equivalent; `:authority` = h2.
- **ETag** = fingerprint; `If-None-Match` → **304**. **Weak `W/"…"`** = equivalent; **Range needs strong**. **`If-Match`** = optimistic concurrency (lost updates).
- `Vary`: cache-key instruction. `Vary: Accept-Encoding` ok; **`Vary: User-Agent`** kills hit rate; `Vary: *` = no cache.
- **Range → 206** + `Content-Range`; `bytes=-50` = last 50; beyond end → **416** (416 came in 2616). Used by video seek, resume, Parquet.
- **Chunked:** hex length + data, **`0` chunk ends**; no Content-Length. Both length + delimiter.
- **OPTIONS** (CORS preflight), **TRACE** (XST attack 2003, disabled), **Via**, **Expect: 100-continue**, **Cache-Control**. ⚠ **`no-cache` = revalidate; `no-store` = never store.** `s-maxage` = shared caches.
- gzip: 202,000 → 5,763 B (**2.8%**) → "text is slow" is false; **headers** are the problem (Content-Encoding only compresses body).
- **"SHOULD NOT >2 connections"** → browsers used **6** (~2008), **18** with domain sharding; removed in RFC 7230. **Pipelining was best but nobody shipped it.**
- **RFC 2616:** **307** added, 416, 417, Host MUST. **302 renamed "Found"** (browsers turned POST→GET); **307 keeps method; 303 → GET**. 504 was already in 2068.
- **Smuggling:** Content-Length vs Transfer-Encoding disagree. 2616: CL ignored; **9112: may reject, MUST close connection**. h2 makes it unrepresentable. "Postel's law loses."
- JWT = **base64url** (`+ /` → `- _`) because of HTTP token alphabet.
- **418** = April Fool's RFC 2324, reserved. **62** status codes assigned (IANA Sep 2025).

**HTTP/1.1 costs:** **HOL blocking** — no request ID ("order IS the identifier"); 2003 ms vs 3 ms. **Header bloat** — 805 B × 80 = **97.5% repeats**. **Nagle (RFC 896) + delayed ACK (40 ms)** → ~40 ms/request on persistent conns → fix: single write + **`TCP_NODELAY`**. Multiplexing needs identity: TCP ports, TCAP transaction id, FastCGI requestId, **h2 31-bit stream id**.

**HTTP/2:**
- **SPDY** (Nov 2009, Belshe & Peon; "55% faster") → RFC 7540 (May 2015) → SPDY removed **Chrome 51** (2016) → RFC 9113 (2022; deprecated **priorities + h2c Upgrade**). "HTTP/2", not 2.0.
- **Preface:** `PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n` = **24 bytes** (PRISM). h1 server replies 501. **ALPN** (`h2`) in TLS ClientHello = 0 extra RTT. No browser shipped cleartext h2.
- **Frame header 9 B:** Length **24** · Type **8** · Flags **8** · R **1** · Stream ID **31**. **Client streams odd, server even, stream 0 = connection.**
- **10 types:** DATA 0, HEADERS 1, PRIORITY 2 (deprecated), **RST_STREAM 3** (cancel one stream), SETTINGS 4, PUSH_PROMISE 5, PING 6, **GOAWAY 7**, **WINDOW_UPDATE 8** (per stream AND connection), CONTINUATION 9 (2024 DoS class).
- Defaults: header table **4096**, init window **65535**, max frame **16384**.
- **HPACK:** static table **61** entries (index 2 = `:method GET` → **0x82**), dynamic from **62**, Huffman. **174 B → 79 B → 6 B.** Per connection → use ONE connection (sharding harmful).
- **CRIME (2012):** compression-size leak; HPACK safe (fixed Huffman, exact-match index, "never indexed").
- **Server push:** not deprecated in RFC, but **Chrome 106 removed (Sep 2022)** (server doesn't know client cache). Replacement **103 Early Hints**: "server informs, client decides."
- h2 still has **TCP-level HOL** (one loss stalls all streams). SPDY: +11.8% at 0% loss, +47.7% at 2%.

**QUIC / HTTP/3:**
- Over **UDP** (proto 17) because **middleboxes drop unknown protocols** (SCTP 132 failed) — ossification: "anything a middlebox can read, it will depend on." Encrypts most headers to stay changeable. Userspace.
- Cold RTT: TCP+TLS1.3+h2 **3**, QUIC **2**, **0-RTT 1** (@150 ms: 457/320/162 ms). **TLS 1.3 mandatory**; ClientHello in CRYPTO frame.
- **0-RTT replayable → idempotent only**; Cloudflare allows GET/HEAD; `Early-Data` header; **425 Too Early**.
- STREAM frames: stream id + offset → ordered within stream only.
- **TCP identity = 4-tuple** (Wi-Fi→LTE kills it). **QUIC = connection ID** → migration; CIDs rotated for privacy.
- **QPACK** (RFC 9204): HPACK needs total order; QUIC has none → **encoder stream (0x02) / decoder stream (0x03)**; **99** static entries from index 0 (HPACK 61 from 1).
- Discovery: **ALPN**, **Alt-Svc** (`h3=":443"`), **HTTPS DNS RR** (type **65**). **3–5% networks block UDP**; fallback = downgrade attack.
- Adoption: ~85% requests h2+, ~15% h1.1.
- Four ideas: multiplexing needs identity · every fix is next problem · semantics ≠ encoding · deployed reality beats spec.
- Assignment: calculator server must keep **one socket** for all requests; consume exactly Content-Length.

## S6 — CDNs
- Light in fibre **~204,000 km/s (~2/3 c)** → **4.9 ms / 1000 km** one way. Mumbai–Ashburn RTT floor **126 ms**; Mumbai–Chennai ~10 ms.
- **Mathis (1997): throughput ≈ MSS / (RTT × √loss).** Akamai 2010: far edge 110× slower.
- **Edge wins:** warm origin pool (saves handshakes) + **cache HIT** (34 ms vs 621 ms). ⚠ **A MISS is no faster than direct.**
- CDN = reverse proxy + cache + pool + anycast in 300+ cities. **colo = IATA airport code** (BOM, DEL, IAD); `cf-ray` suffix = colo; `/cdn-cgi/trace`. PoP chosen by **BGP anycast**.
- **Consistent hashing (Karger 1997; Akamai):** add 11th cache → **modulo moves 90.9%** of URLs; consistent ≈ **1/(N+1)**; **160 virtual points/server**; nginx `hash $request_uri consistent` (ketama).
- **Players:** Akamai 1998 (ESI) · CloudFront 2008 (BBR 2019, +22%) · Cloudflare 2010 (nginx+LuaJIT FL1 → Rust FL2; **Pingora 2022**) · Fastly 2011 (**Varnish**) · Google Media CDN 2022 · Broadpeak (video/telco).
- **Cloudflare defaults:** caches by extension (**68**); **HTML/JSON NOT cached**; Set-Cookie/private/no-store not cached. TTL **200/301 = 2 h, 404 = 3 min**. **Cache key = scheme+host+path+query** (no cookies!).
- **cf-cache-status (8):** MISS · HIT · EXPIRED (re-fetched) · **REVALIDATED (304)** · UPDATING (stale + bg refresh) · STALE (origin down) · **DYNAMIC (not eligible)** · BYPASS (origin said no-store).
- **Uncacheable content:** **SSI 1994** (server, NCSA HTTPd) → **ESI 2001** (edge; Akamai+Oracle) → **Ajax ~2005** (browser) → **Railgun 2013–2024** (delta). ESI: origin bytes **−98%**, user bytes same, **origin requests go UP**. Headers `Surrogate-Control: content="ESI/1.0"`.
- **RFC 9842 Compression Dictionary Transport (2025):** `Available-Dictionary`, `Content-Encoding: dcb/dcz`; zstd w/ 1-min-old dict = 1.8% of raw.
- **Poisoning (Kettle 2018):** unkeyed header (X-Forwarded-Host) cached for all. **Deception (Omer Gil 2017):** `/account/fake.css` → private page cached. Both = cache key ≠ reality.
- **BBR** (Cardwell, Google 2016): bandwidth + min RTT; **sender-only change**; B4/YouTube 2–25×; CloudFront +22%; now most-deployed CCA.
- **Pooling:** per-worker pools stay cold; **1 shared pool: 98.7% reuse, 57 ms** (vs 160 ms none). **Pingora 87.1% → 99.92%.** Most CDN→origin still HTTP/1.1.
- **Tiered cache / origin shield** (300 edges → 1 origin fetch); **request collapsing** (= `proxy_cache_lock`).
- **WAF** = denylist of spellings (bypass `'/**/OR/**/1=1`); real fix = **parameterised queries**.
- **Rate limits:** fixed window allows **2× burst** at boundary; sliding log exact; **Cloudflare = sliding-window estimate (2 counters, 0.003% error)**; leaky bucket burst=0 refuses real browsers; nginx `limit_req burst`; **counts per data centre**.
- **DDoS:** **31.4 Tbps** (Dec 2025, **Aisuru**, 35 s); Cloudflare ~500 Tbps/330+ cities. **Fastly 8 Jun 2021: one config → 85% errors, 49 min.**
- **API gateway:** no token → 401; refuse **`alg:none`**; overwrite client `X-User`; **origin must be unreachable directly → mTLS (authenticated origin pulls) or Tunnel**.
- **Workers = V8 isolates** (~5 ms, ~3 MB) not processes. Quick Tunnel: `cloudflared tunnel --url`, 200 in-flight, no SSE. Free: 100k Worker req/day.
- **Domain fronting** banned: AWS & Google 2018, Azure 2022, Fastly Feb 2024.
- You hand over: TLS keys · SPOF · visibility · lock-in.

## S7 — Failures & retries
- **Request chain (order):** socket() → DNS → connect() → write() → read() → CDN → SSL/TLS → HTTP.
- **socket():** out of fds → retry later.
- **DNS:** no mapping (NXDOMAIN) · timeout · misconfigured.
- **connect():** host unreachable · port not listening (**RST/ECONNREFUSED**) · client conn limit (fds/ephemeral ports) · server limit (backlog/fd/SYN flood) · **no SYN response → timeout (backoff)** · stale DNS IP.
- **write():** packet drop → write timeout · machine/path node down (SIGPIPE) · rate limit (server closes / stops reading) · body too large (**413**).
- **read():** access denied (401/403) · read timeout · **429** · 5xx · silent drop (EOF/RST).
- **CDN:** anycast wrong PoP · bad/overwhelmed server (Fastly 2021) · stale info · same TCP errors on edge↔tier and mid-tier↔origin.
- **TLS:** invalid cert (expired/hostname/CA) · version mismatch (1.1/1.2/1.3) · cipher mismatch · **pinning mismatch** · wrong clock · TCP timeout.
- **HTTP:** version error (505/501) · missing headers (no Host → 400) · **401 / 407 (proxy auth)** · 4xx · **502 (bad upstream) / 503 (overloaded) / 504 (upstream timeout)** · **CORS preflight (OPTIONS) failure** · read timeout (nginx `proxy_read_timeout` & ALB idle = **60 s**).
- **Retry toolkit:** timeouts · **exponential backoff + jitter** · retry storm · Retry-After · **idempotency** · retry only transient (timeouts, refused, 502/503/504, 429) — **never 400/401/403/404** · **fallback ≠ retry** · circuit breaker · failover · serve stale / stale-if-error · negative caching · graceful degradation · thundering herd on recovery · feature flags.

## S8 — Video streaming at scale
- Brief: **50 M peak**, 20 M avg, 4 h match, scorecard ~4–5 KB (**~1 KB gz**), 100 events/yr.
- **Pull (non-persistent):** polling, conditional GET, caches → stateless, **CDN-able**. **Push (persistent):** long poll, SSE, WebSocket, MQTT, raw socket → stateful, **not cacheable**. "Pull scales via caches; push scales via machines."
- **Polling:** ETag/If-None-Match → 304; **jitter ±20%**. **Staleness = poll interval + Σ cache TTLs** (15 + 5 + 5 = 25 s). Keep CDN TTL ≤ ½ promise; prefresh at ~25 of 30 s.
- **Long poll:** ~25 s hold; answer before **60 s** idle timeouts; synchronises herd; **LL-HLS blocking reload = long poll**.
- **SSE:** `text/event-stream`; **blank-line delimiter**; `Last-Event-ID` resume; `retry:`; one-way; ~6/browser on h1.
- **WebSocket:** `101 Switching Protocols`; `Sec-WebSocket-Accept = base64(SHA-1(key + GUID))`; length 0–125 / **126 → 16-bit** / **127 → 64-bit**; **client frames masked (4-B key)** to stop cache poisoning; length-prefixed.
- **MQTT:** CONNECT/CONNACK/SUBSCRIBE/PUBLISH; **retained message** (broker cache); **QoS 1 = at-least-once** → dedupe by version; PINGREQ `C0 00`, PINGRESP `D0 00`; Remaining Length = varint; keepalive holds NAT.
- **Hotstar 2019:** MQTT + **EMQX**; 250k/node (c5.4xlarge) → cluster 2M (Mnesia <10 nodes) → ELB **4M** pre-warmed (drops at ~500k otherwise) → 5 clusters >10M → **reverse bridge, 200 nodes = 50M**. Used push for **social feed** (personalised, can't cache).
- **Held socket costs:** memory (~137 KB/phone), keepalives (60 s × 20 M = **333k pings/s**), LB; test needs **≥9 client IPs** (28,232 ports each).
- **Little's Law twice:** polling via CDN 1.67 M rps × 0.03 s = **50,000** in flight vs push 50 M sockets (**1000×**).
- **Poll math (30 s):** 20 M × 14,400 / 30 = **9.6 B requests**, **1.67 M rps**, **9.6 TB**. At 15 s: 19.2 B, 3.33 M rps.
- **Costs/match:** S3 $4.7K (GETs) · nginx+ALB $1.2–1.8K · **CDN $12.5K (92% request fees)** · **push $0.9–1.6K (cheapest)**. S3 **5,500 GET/s/prefix** → 1.67 M = 303× over → **503 Slow Down** → retry storm.
- **CloudFront India:** $0.012/10k HTTPS req; $0.109/GB. **Break-even ≈ 11 KB**: below pay per request (scorecard, playlist), above per byte (segments).
- Why polling for scorecard: cacheable, stateless, already paid (0.28% of video bill).
- **Thundering-herd fixes:** request collapsing (`proxy_cache_lock`), serve stale while updating (**RFC 5861**), prefetch, client jitter. Collapsing needs a **shareable answer** (`public`; Set-Cookie/private breaks it; Fastly skips collapsing 2 min). **Cloudflare doesn't cache .json** by default.
- **Negative caching:** **5xx 1–2 s (cache it)**; **404 ≈ never** (1 s) at live edge; Cloudflare default 404 = 3 min. Negative TTL ≪ time for the thing to appear.
- **Diffs:** 4,117 B → 1,088 gz → **183 B JSON Patch**. Push the patch; version gap → full fetch. Pull: don't use per-client `?since=` (hit rate collapses).
- **Versioned scorecard = HLS playlist** (`version` = `#EXT-X-MEDIA-SEQUENCE`, poll interval = `#EXT-X-TARGETDURATION`).
- **HLS flow:** master.m3u8 (once, control) → media playlist (every target duration, control) → segments (once, data, immutable). Player switches rendition by throughput.
- **Master:** `#EXT-X-STREAM-INF` BANDWIDTH = (video+audio)×**1.1** (3000k+128k → 3,440,800); CODECS = skip undecodable (**fallback, not retry**); **Content Steering** = CDN switching.
- **Playlist reload (RFC 8216):** changed → wait **≥ 1 target duration**; unchanged → **½ target duration**; same seq, diff URI → SHOULD halt.
- Tags: `#EXTINF`, `#EXT-X-PROGRAM-DATE-TIME` (wall clock), **`#EXT-X-ENDLIST` = VOD / stopped changing**. Apple recommends **6 s** segments. Per-viewer token in query = cache-key bust.
- **MPEG-TS:** **188-B packets** = 4-B header (**sync 0x47**, **13-bit PID**, continuity counter) + 184 payload; **188 chosen for ATM**; fixed length + sync = both framing answers. Overhead 3.3–5.6%. **fMP4/CMAF** = boxes (TLV).
- **Segment length:** 2 s → 25 M rps; 4 s → 12.5 M; 6 s → 8.3 M; **latency floor = 3× segment** (4 s → 12 s). Playlist traffic is **harder** than segments (changes every 4 s; stale = stall/404).
- **Latency budget:** encode ~2 + segment 4 + CDN ~2 + hold-back 12 ≈ **20 s**. **LL-HLS:** **parts** (~1 s), **blocking reload** (`_HLS_msn`), **preload hints** (replaced h2 push Jan 2020), **delta `EXT-X-SKIP`** → ~**3 s**; PART-HOLD-BACK ≥ 3 parts.
- **Spoiler fix:** stamp updates with wall-clock; reveal when playback passes `PROGRAM-DATE-TIME`.
- **ABR:** throughput-based vs buffer-based (**Netflix: 10–20% fewer rebuffers**); **stall worse than lower quality**; Apple start 730 kbps cellular / 2 Mbps Wi-Fi.
- **Multi-CDN:** DNS · listed twice · Content Steering · client failover w/ **circuit breaker**.
- **Deleted segments:** removed segment must stay **duration + playlist duration (4 + 40 = 44 s)**; stale playlist + deleted segment → 404 → stall. Fix `-hls_delete_threshold`; Apple: playlist invalid if Last-Modified > **3 target durations** old.
- **Caching rules:** master mins/yes/1 s · media playlist ≤ ½ target, stale ≤ 1 target · segment long/yes/≤1 s · score.json ≤ ½ promise. **gzip playlists (MUST)**.
- **ffmpeg:** `-re` native speed; **`-codec copy` can only cut at keyframes**; `-hls_time` is a **target not a promise**; **x264 default GOP 250 → 8.33 s @30 fps**; `-g 120` = 4 s @30 fps (24 fps → 5 s); `-sc_threshold 0`; `split=3` = decode once, encode thrice; ladder 720p 3000k / 480p 1500k / 360p 800k; `-hls_list_size 5` ignored with `-hls_playlist_type event` (append-only). Real pipeline: camera → RTMP/SRT → transcoder → packager → origin → CDN.

---

## Confusable pairs (high MCQ yield)
| A | B |
| --- | --- |
| `listen` backlog = queue depth | connection limit ✗ |
| Connection refused (RST, no listener) | Hang (listening, no accept) |
| CSMA/CD Ethernet | CSMA/CA Wi-Fi |
| SS7 reliable per hop | TCP end-to-end |
| SYN+ACK combine (3 seg open) | FIN+ACK can't (4 seg close) |
| CLOSE_WAIT = app bug | TIME_WAIT = normal 2 MSL |
| select 1024 (bitmap, ulimit useless) | epoll (ulimit matters) |
| `inactive` (unread eviction) | `proxy_cache_valid` (freshness) |
| `^~` stops regex | regex first match in file order |
| sendfile zero-copy | breaks with gzip/TLS |
| `no-cache` revalidate | `no-store` never store |
| 302 (POST→GET in practice) | 307 keeps method; 303 → GET |
| Weak ETag (equivalent) | Strong ETag (needed for Range) |
| Mosaic = browser | NCSA HTTPd = server/CGI |
| HPACK 61 static from 1 | QPACK 99 static from 0 |
| h2 fixes HTTP HOL | QUIC fixes TCP HOL |
| h2 push removed (Chrome) | not deprecated in RFC; → 103 Early Hints |
| TCP identity = 4-tuple | QUIC = connection ID |
| Cache poisoning = unkeyed header | Cache deception = fake extension |
| ESI/SSI/Ajax/Railgun = edge/server/browser/delta | |
| REVALIDATED = 304 | DYNAMIC = never eligible |
| Fixed window = 2× burst | Sliding window estimate (Cloudflare) |
| Fallback (different codec/CDN) | Retry (same thing again) |
| Polling = cacheable, stateless | Push = stateful, un-cacheable |
| 5xx negative-cache 1–2 s | 404 almost never |
| Playlist: polled, changes | Segment: once, immutable |
| Pay per request < 11 KB | Pay per byte > 11 KB |

## Numbers (one-glance)
7 syscalls · 1024 (priv ports / FD_SETSIZE / ulimit / C10K) · 32768–60999 · 60 s TIME_WAIT · SIGPIPE 13 · 0x07EA · 1500/1460/1518 · 20/20/8 · proto 6/17/132 · 140/160/70/272 · 64 kbps · 2600 Hz · RTT 1/3/2/1 · +33% base64 · 8 MB vs 2 KB · 80 GB · 7/8 · ~8000 keys/MB · 11 phases · 27 states · 8-B FastCGI · 24-B preface · 9-B frame · 10 frame types · 61/99 static · 4096/65535/16384 · 174→79→6 · 97.5% · 40 ms · 6/18 conns · 62 codes · 3–5% UDP blocked · 90.9% vs 1/11 · 160 vnodes · 68 extensions · 2 h/3 min · 87.1→99.92% · 31.4 Tbps · 85%/49 min · 5 ms/3 MB · 50M/250k/4M · 1.67M rps/9.6B/9.6TB · 5,500 GET/s · 11 KB · 188/0x47/13-bit · 3× · 44 s · 250 frames.

## Timeline
1971 FTP · 1975 SS7 · 1984 OSI/ASN.1/Nagle · 1990 CERN httpd · 1993 Mosaic + NCSA HTTPd (CGI) · 1994 SSI · 1995 Apache · 1996 HTTP/1.0, SYN cookies, Squid · 1997 HTTP/1.1, consistent hashing, Servlets · 1998 Akamai · 1999 RFC 2616, C10K, J2EE · 2001 HAProxy, ESI · 2002 epoll, nginx started · 2003 XST · 2004 nginx release · 2005 Ajax · 2006 Varnish · 2008 CloudFront · 2009 SPDY · 2010 Cloudflare · 2011 Fastly, nginx 1.0, bufferbloat · 2012 CRIME, Apache event · 2013 C10M, Railgun · 2014 RFC 7230–5, ALPN · 2015 HTTP/2 + HPACK · 2016 BBR, SPDY gone, Alt-Svc · 2017 HAProxy 1.8, cache deception · 2018 cache poisoning, fronting banned, Workers · 2019 Hotstar 50M, BBR on CDNs · 2020 LL-HLS preload hints · 2021 Fastly outage · 2022 RFC 9110–9114, Pingora, Chrome 106 drops push, Media CDN · 2023 HTTPS RR · 2024 Railgun retired, Fastly bans fronting · 2025 RFC 9842, FL2, 31.4 Tbps.
