# CN Practice Quiz — HARD set (Sessions 1–8, 40 MCQs, 5 per session)

Tougher than the first set: scenarios, multi-step calculations, config puzzles, and "which is wrong". Pick ONE. Answer key with working at the bottom.

---

## Session 1

**1.** A load-test client must hold 250,000 simultaneous connections to a single `server_ip:8080`. Linux ephemeral range is 32768–60999. Minimum number of client source IPs needed?
- A) 5
- B) 7
- C) 9
- D) 12

**2.** You kill your server and restart it immediately. It fails with "address already in use", though `ps` shows no server process. Which fix addresses the actual cause?
- A) Raise `net.core.somaxconn`
- B) Set `SO_REUSEADDR` before `bind()` — the old connection's socket is still in TIME_WAIT on that port
- C) Set `SO_LINGER {1,0}` on the new listening socket
- D) Ignore SIGPIPE

**3.** You must stream output of unknown total size, containing arbitrary binary bytes, and the receiver must know where it ends. Which framing works?
- A) A newline delimiter between messages
- B) A `Content-Length` header up front
- C) Length-prefixed chunks, ended by a zero-length chunk
- D) Fixed-length records of 4096 bytes

**4.** Which of these is NOT a problem with `gethostbyname()`?
- A) IPv4 only
- B) Not thread-safe
- C) Blocks with no timeout you control
- D) It ignores `/etc/hosts` and always queries DNS

**5.** You encode the decimal number 1234567 as BCD. How many bytes, and what is the final byte?
- A) 4 bytes: `12 34 56 7F`
- B) 4 bytes: `12 34 56 07`
- C) 7 bytes: one per digit
- D) 3 bytes: `12 34 56`

---

## Session 2

**6.** A UDP datagram with a 1000-byte payload travels in an IPv4 packet inside an Ethernet II frame (no VLAN, no options). Bytes on the wire, counting Ethernet header and FCS but not the preamble?
- A) 1028
- B) 1042
- C) 1046
- D) 1066

**7.** A 100-character SMS made only of GSM-7 characters fits in one SMS. You add one emoji. What happens?
- A) Still one SMS; the emoji is one extra character
- B) Two SMS — the whole message switches to UCS-2, where 140 bytes hold only 70 characters
- C) The first 160 characters go as GSM-7 and the emoji goes alone as a second SMS
- D) The emoji is dropped

**8.** On Wi-Fi a data frame is corrupted by interference. Which statement is correct?
- A) TCP notices a missing ACK and retransmits first
- B) The access point forwards the corrupted frame, and TCP's checksum catches it
- C) The SMSC re-sends it
- D) The L2 ACK never arrives, so the sender retransmits the frame at L2 (after backoff) — TCP above may never notice

**9.** A server calls `close()` first on 10,000 short connections. Where do TIME_WAIT sockets accumulate?
- A) On the server — the side that sends the first FIN holds the 4-tuple for 2 MSL
- B) On the clients, since they called `connect()`
- C) Equally on both sides
- D) Nowhere; TIME_WAIT only follows an RST

**10.** In an ISUP call, after the called party picks up, which message is sent and what carries the conversation?
- A) ACM; voice is carried inside ISUP messages
- B) ANM; voice is carried inside TCAP
- C) IAM; voice goes over SCCP
- D) ANM; voice is cut through on the separate 64 kbps bearer circuit while SS7 stays idle until REL

---

## Session 3

**11.** Your `select()` server has the listening socket fd 4 and clients on fds 3, 5, 9. What should the first argument to `select()` be?
- A) 4
- B) 9
- C) 10
- D) 1024

**12.** A service handles 2,000 req/s. 90% of requests take 50 ms; 10% take 2 s. Roughly how many requests are in flight on average?
- A) 100
- B) 490
- C) 4,000
- D) 4,100

**13.** A FastCGI client sends BEGIN_REQUEST, the PARAMS records, and STDIN, but forgets the empty (length-0) PARAMS record. What happens?
- A) The responder keeps waiting for more params; the request never starts
- B) The responder assumes params ended after 8 bytes
- C) nginx replies 400
- D) The STDIN data is parsed as params

**14.** About how much stack memory do 100,000 goroutines need at their initial size?
- A) 20 MB
- B) 2 GB
- C) 200 MB
- D) 80 GB

**15.** Why was early HAProxy (2001) built on `select()` and not `epoll`?
- A) select is faster at HAProxy's scale
- B) The author wanted single-threaded simplicity
- C) epoll was patented until 2005
- D) epoll didn't exist yet — it arrived in Linux 2.5.44 in late 2002

---

## Session 4

**16.** A worker has 8,000 connection slots. nginx's `ngx_accept_disabled = connection_n/8 − free_connection_n`. It stops competing for new connections when free slots drop below:
- A) 800
- B) 1,000
- C) 4,000
- D) 7,000

**17.** Config: `location = /api {A}`, `location /api/ {B}`, `location ~ /api/.*\.json$ {C}`, `location / {D}`. Which handles `/api/data.json`?
- A) A
- B) B
- C) C — longest prefix is remembered, then the regex matches and wins
- D) D

**18.** `proxy_cache_valid 200 10s; inactive=60s`. An object is fetched at t=0 and next requested at t=70 s. What does nginx do?
- A) MISS — the entry was evicted at 60 s for being unread, so it fetches the full object (not a revalidation)
- B) HIT, serving the stale copy
- C) EXPIRED, revalidating with a conditional request
- D) UPDATING, serving stale while refreshing

**19.** A benchmark shows `sendfile()` taking about the same wall-clock time as `read()+write()` over loopback. What's the correct reading?
- A) sendfile doesn't actually avoid copies
- B) The benchmark proves sendfile is useless
- C) mmap is always faster
- D) Loopback has no NIC/DMA, so it's memory-bound; sendfile's real wins are 2048 syscalls → 1 and CPU headroom under concurrency

**20.** Smooth weighted round robin with weights a=5, b=1, c=1. The order of the 7 picks is:
- A) a a a a a b c
- B) a a b a c a a
- C) a b a c a a a
- D) a a a b a c a

---

## Session 5

**21.** 24 objects, RTT 200 ms, HTTP/1.1 keep-alive on a single connection, sequential requests, no TLS, ignoring transfer time. Total time?
- A) 4.8 s
- B) 9.6 s
- C) 0.4 s
- D) 5.0 s (1 handshake RTT + 24 request/response RTTs)

**22.** A browser POSTs a form and gets `302 Found`. What does it do, and how would a server force the method to be kept?
- A) Browsers typically re-request with GET; send 307 to preserve the method
- B) Browsers re-POST as the RFC says; send 303 to preserve it
- C) It stops and shows an error; send 301
- D) It re-sends the POST only if the server also sends `Connection: keep-alive`

**23.** The file is 202,000 bytes. `Range: bytes=-50` gets a `206` with which `Content-Range`?
- A) `bytes 0-49/202000`
- B) `bytes 201950-201999/202000`
- C) `bytes 201950-202000/202000`
- D) `bytes */202000` with a 416

**24.** Why does domain sharding hurt under HTTP/2?
- A) HTTP/2 forbids multiple hostnames
- B) TLS sessions can't be resumed across hosts
- C) Each extra connection has its own cold HPACK table and congestion window, and you lose multiplexing on one connection
- D) Browsers cap h2 at 6 connections

**25.** Cold connection at 100 ms RTT, first response byte received. Which triple is right for TCP+TLS1.3+HTTP/2, QUIC 1-RTT, and QUIC 0-RTT?
- A) ~300 ms / ~200 ms / ~100 ms
- B) ~450 ms / ~300 ms / ~150 ms
- C) ~300 ms / ~300 ms / ~100 ms
- D) ~200 ms / ~200 ms / ~100 ms

---

## Session 6

**26.** Mathis: throughput ≈ MSS / (RTT × √loss). RTT doubles and loss rate quadruples. Throughput becomes:
- A) ½
- B) ¼
- C) ⅛
- D) 1/16

**27.** Origin RTT floor is 126 ms. A fresh connection needs TCP + TLS 1.3 + the request (3 RTT). Lowest possible time-to-first-byte?
- A) 126 ms
- B) 252 ms
- C) 504 ms
- D) 378 ms

**28.** With default settings, which does Cloudflare cache?
- A) `/index.html` returning 200 with no cache headers
- B) `/data.json` returning 200
- C) `/app.css` returning 200, no `Set-Cookie`, no `no-store`
- D) `/app.css` returning 200 with a `Set-Cookie` header

**29.** A leaky bucket limit of "100 per 10 s" with burst = 0 refused ~97% of a normal page load. Why?
- A) A browser opens ~30 requests at once, but the bucket releases one per 100 ms with no burst allowance, so most are refused
- B) Leaky bucket counts bytes, not requests
- C) The limit is per data centre
- D) Browsers send HEAD first

**30.** ESI cut origin→edge bytes by 98%, yet origin requests rose from 100 to 201. What explains it?
- A) User download size also fell 98%, so fewer requests
- B) The shell is not cached at the edge
- C) The shell is fetched once and cached, but each personalised fragment (2 per user) is its own origin fetch; user download size is unchanged
- D) Railgun retries each fragment

---

## Session 7

**31.** `socket()` fails with EMFILE during a traffic spike. Best reaction?
- A) Retry the DNS lookup
- B) Switch to UDP
- C) Treat it as a 4xx and never retry
- D) Retry after a delay — descriptors free up as sockets close — and fix fd limits / use connection pooling

**32.** Which set contains only errors worth retrying (with backoff and jitter, for idempotent calls)?
- A) 400, 404, 502
- B) 429 (after `Retry-After`), 503, 504
- C) 401, 403, 503
- D) 413, 429, 501

**33.** An app pins a specific server cert. The server rotates to a new, perfectly valid CA-signed cert. What fails?
- A) Nothing; the new cert is valid
- B) A TLS version mismatch
- C) The pinning check — the app trusts only the old cert/key and refuses the new one
- D) A wrong-clock error

**34.** A long-poll holds responses for 90 s behind nginx with the default `proxy_read_timeout` (60 s). What does the client get?
- A) 504 Gateway Timeout from the proxy
- B) 502 Bad Gateway
- C) 429 Too Many Requests
- D) A normal 200

**35.** 50M clients normally generate 1.67M req/s. After an S3 `503 Slow Down`, each client immediately retries up to 3 times with no backoff. Worst-case load?
- A) 1.67M req/s
- B) 3.3M req/s
- C) 5M req/s
- D) 6.7M req/s

---

## Session 8

**36.** 50M phones poll the scorecard every 20 s. Peak request rate?
- A) 1.67M req/s
- B) 2.5M req/s
- C) 3.33M req/s
- D) 5M req/s

**37.** CloudFront India: $1.20 per million HTTPS requests; $0.109 per GB. Roughly at what object size do request fees equal byte fees?
- A) 1 KB
- B) 110 B
- C) 11 KB
- D) 1 MB

**38.** HLS `#EXT-X-TARGETDURATION:6`. You reloaded the media playlist and it was unchanged. When should you retry, per RFC 8216?
- A) After 1.5 s
- B) After 3 s (half a target duration)
- C) After 6 s
- D) After 12 s

**39.** Latency budget: encode 2 s + segment fill + CDN 2 s + player hold-back of 3 × target duration. With 6 s segments, glass-to-glass is about:
- A) 20 s
- B) 24 s
- C) 28 s
- D) 34 s

**40.** Segments are 6 s each, and the playlist lists 10 segments. For how long must a segment remain available after it leaves the playlist (RFC 8216)?
- A) 66 s (its duration + the playlist's duration)
- B) 6 s
- C) 60 s
- D) 120 s

---
---

# ANSWER KEY (with working)

| # | Ans | Working / why |
| --- | --- | --- |
| 1 | C | 250,000 ÷ 28,232 ports = 8.86 → **9** IPs |
| 2 | B | Old socket in TIME_WAIT; `SO_REUSEADDR` on the *new* socket fixes it (C affects the closing side and is wrong here) |
| 3 | C | Chunked-style: length-prefixed chunks + empty terminator handles unknown size + binary |
| 4 | D | It checks `/etc/hosts` first; A–C are real problems |
| 5 | A | 7 digits → 4 bytes: `12 34 56 7F` (F pads the odd nibble) |
| 6 | C | 14 + 20 + 8 + 1000 + 4 = **1046** |
| 7 | B | One emoji flips the whole message to UCS-2 → 70 chars/SMS → 2 messages |
| 8 | D | L2 ACK per frame; retransmit at L2 before TCP knows |
| 9 | A | Active closer (first FIN) gets TIME_WAIT |
| 10 | D | ANM, voice on a separate 64 kbps bearer, SS7 idle until REL/RLC |
| 11 | C | `nfds = maxfd + 1 = 10` |
| 12 | B | avg latency = 0.9×0.05 + 0.1×2 = 0.245 s; L = 2000 × 0.245 = **490** |
| 13 | A | Empty record is the delimiter; the responder waits forever |
| 14 | C | 100,000 × 2 KB = **200 MB** |
| 15 | D | epoll landed in Linux 2.5.44 (late 2002) |
| 16 | B | `connection_n/8 = 1000` → stops when free < 1000 (>7/8 used) |
| 17 | C | No exact match; longest prefix `/api/` remembered (no `^~`); regex matches → regex wins |
| 18 | A | `inactive=60s` evicts the unread entry, so it's a full MISS; freshness didn't matter |
| 19 | D | Loopback is memory-bound; real win = 2048 syscalls → 1 + CPU headroom |
| 20 | B | Smooth WRR for 5,1,1 → a a b a c a a |
| 21 | D | 1 + 24 = 25 RTT × 200 ms = 5.0 s (HTTP/1.0 = 24 × 2 RTT = 9.6 s) |
| 22 | A | Browsers turn POST into GET on 302; 307 keeps the method; 303 = explicit GET |
| 23 | B | Last 50 bytes of 202,000 → 201950–201999 |
| 24 | C | HPACK dynamic table and cwnd are per connection |
| 25 | A | 3 / 2 / 1 RTT × 100 ms |
| 26 | B | 1 / (2 × √4) = 1 / (2×2) = ¼ |
| 27 | D | 3 × 126 = **378 ms** |
| 28 | C | HTML/JSON aren't cached by default; Set-Cookie blocks caching |
| 29 | A | Browser opens ~30 requests at once; no burst allowance |
| 30 | C | Origin requests 1 shell + 200 fragments = 201; bytes to origin −98%; user bytes same |
| 31 | D | EMFILE is transient; retry later and fix limits/pooling |
| 32 | B | Transient errors only; never 400/401/403/404 |
| 33 | C | Pinning mismatch even though the cert is valid |
| 34 | A | Proxy gives up after 60 s → 504 |
| 35 | D | Original + 3 retries = 4 × 1.67M = **6.7M** |
| 36 | B | 50M ÷ 20 = **2.5M** req/s |
| 37 | C | 11 KB × 1M requests = 11 GB × $0.109 ≈ $1.20 |
| 38 | B | Unchanged → ½ target duration (changed → ≥ 1 target duration) |
| 39 | C | 2 + 6 + 2 + 18 = **28 s** |
| 40 | A | 6 + (10 × 6) = **66 s** |

**Scoring:** 36+ you're ready · 30–35 redo the ones you missed · <30 re-read the matching session in the cheat sheet.
