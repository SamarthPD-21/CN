# CN Practice Quiz — Sessions 1–8 (40 conceptual MCQs, 5 per session)

Style: "what property / why" questions with plausible-but-wrong reasons as distractors. Pick ONE. Answer key + explanations at the bottom.

---

## Session 1 — Sockets & protocol design

**1.** A server calls `socket()`, `bind()` and `listen()` but never `accept()`. A client connects. What does the client see?
- A) `connect()` fails immediately with "Connection refused"
- B) `connect()` succeeds because the kernel completes the handshake, but the client then hangs waiting for the server
- C) The kernel sends a RST as soon as the backlog fills
- D) The server process is killed by SIGPIPE

**2.** Why does a TCP client never need to call `bind()`?
- A) Binding is only allowed for root, and clients are unprivileged
- B) `connect()` binds to the server's port automatically
- C) The kernel picks a free ephemeral port at `connect()`; only servers need a well-known port that clients can find
- D) Clients use UDP, which has no ports

**3.** A process writes to a socket whose peer has already reset the connection and dies silently with no error message. Why?
- A) The default action of SIGPIPE terminates the process
- B) `write()` returns -1 and the C runtime aborts
- C) The kernel's OOM killer reclaims the socket's memory
- D) The RST itself is delivered as SIGKILL

**4.** Why do JWTs, Basic auth and email attachments use base64 even though it makes data ~33% bigger?
- A) It compresses binary data into fewer characters
- B) It encrypts the data so intermediaries can't read it
- C) It is faster to parse than hex
- D) It maps arbitrary bytes onto a small alphabet that every text-only layer can carry without corruption

**5.** "SSL/TLS secures TCP, not HTTP." What does that mean in practice?
- A) TLS only works with HTTP on port 443
- B) TLS sits below the application protocol, so the same machinery can protect any protocol running on a socket (SMTP, databases, etc.)
- C) TLS replaces TCP's reliability mechanisms
- D) HTTP must be rewritten to be TLS-aware

---

## Session 2 — OSI, SS7, TCP, text protocols

**6.** Why does Wi-Fi use collision *avoidance* (CSMA/CA) instead of the collision *detection* used by wired Ethernet?
- A) A radio cannot listen while it is transmitting, so it can't detect a collision as it happens
- B) Wi-Fi frames are too short for detection to work
- C) Wi-Fi has no MAC addresses to detect collisions with
- D) Radio waves never collide

**7.** SYN cookies let a server survive a SYN flood. What do they cost?
- A) They require the client to be modified
- B) They make the handshake 4 segments instead of 3
- C) Because state is squeezed into the 32-bit ISN, most TCP options (window scale, SACK, timestamps) are lost, so they're enabled only under pressure
- D) They disable `listen()` backlog entirely, forever

**8.** Why does closing a TCP connection take 4 segments when opening takes 3?
- A) FIN segments are retransmitted once by design
- B) The kernel needs an extra segment to start TIME_WAIT
- C) Closing needs a second RST to confirm
- D) The server's SYN and ACK can be combined, but FIN and ACK can't — the other side may still have data to send, so each direction closes separately

**9.** What was the key idea of SS7 that ended "blue box" phone phreaking?
- A) Encrypting voice with 64-bit keys
- B) Moving signalling out of the voice channel into a separate network, so users can't control call setup by making sounds
- C) Replacing analogue lines with fibre
- D) Using IP packets for voice

**10.** In SMTP, an email can display `From: ceo@company.com` while `MAIL FROM:<anyone@evil.com>` was used. Why is that possible?
- A) SMTP servers always rewrite the From header
- B) The DATA section is encrypted, so servers can't check it
- C) The envelope (MAIL FROM / RCPT TO) and the headers inside DATA are independent, and base SMTP has no authentication or cross-check (hence SPF/DKIM/DMARC)
- D) MIME overrides the envelope

---

## Session 3 — Scaling servers

**11.** Raising `ulimit -n` to 100000 does not let a `select()` server handle more than 1024 sockets. Why?
- A) `select()` ignores file descriptors above 1000 for performance
- B) The kernel caps TCP sockets at 1024 per process
- C) `select()` only works with files, not sockets
- D) `fd_set` is a fixed-width bitmap (FD_SETSIZE = 1024) baked in at compile time

**12.** An API's latency rises from 100 ms to 1 s at the same request rate. By Little's Law, what happens to concurrent connections?
- A) They stay the same, since the rate is unchanged
- B) They grow about 10×, since concurrency = throughput × latency
- C) They fall 10×
- D) They grow only if CPU is saturated

**13.** What problem did FastCGI solve compared with plain CGI?
- A) It avoids creating a new process per request by keeping long-lived workers and talking to them over a socket
- B) It encrypts requests between the web server and the script
- C) It replaced HTTP headers with environment variables
- D) It removed the need for a web server

**14.** Why is a segfault in `mod_php` more dangerous than one in a PHP-FPM worker?
- A) PHP-FPM catches segfaults automatically
- B) `mod_php` uses more memory
- C) `mod_php` runs inside the web server's own process, so one crash takes the server down; FPM workers are separate processes
- D) `mod_php` cannot be restarted

**15.** Why does `epoll` scale to many *idle* connections while `select` doesn't?
- A) epoll compresses idle connections
- B) The watch list lives in the kernel and `epoll_wait` returns only the descriptors that are ready, so cost tracks activity, not the number watched
- C) epoll closes idle connections automatically
- D) epoll uses multiple threads internally

---

## Session 4 — nginx

**16.** What question did nginx ask that Apache's prefork → worker → event evolution never asked?
- A) How can the worker use less memory?
- B) How can workers be pre-created at startup?
- C) Why should there be a worker per connection at all? A connection only needs a few hundred bytes of state until it has something to say
- D) How can the kernel schedule threads faster?

**17.** nginx config has `location ^~ /images/ { }` and `location ~ \.php$ { }`. A request for `/images/a.php` goes to:
- A) The regex location, because regexes are always checked first
- B) Whichever location appears first in the file
- C) The longer of the two patterns
- D) The `^~ /images/` location, because `^~` stops nginx from searching regexes once it has the longest prefix match

**18.** In `proxy_cache_path`, what's the difference between `inactive=60s` and `proxy_cache_valid 200 10s`?
- A) `inactive` evicts entries nobody has *read* for 60 s regardless of freshness; `proxy_cache_valid` sets how long a response is *fresh*
- B) They're the same setting with different names
- C) `inactive` sets freshness; `proxy_cache_valid` sets disk size
- D) `inactive` applies to errors; `proxy_cache_valid` applies to successes

**19.** `sendfile on` makes static serving cheaper. Why does it conflict with `gzip on`?
- A) Both use the same system call
- B) gzip has to read and transform the bytes in user space, but sendfile moves data from kernel to socket without it ever entering the process
- C) sendfile only works on files under 1 MB
- D) gzip disables epoll

**20.** Why must nginx's HTTP request parser be a resumable state machine?
- A) Regular expressions are too slow
- B) It must support HTTP/2
- C) With non-blocking I/O the request line can arrive split across several TCP segments, so the parser has to stop between any two bytes and resume later
- D) It lets nginx skip the kernel

---

## Session 5 — HTTP evolution

**21.** What is the root cause of head-of-line blocking in HTTP/1.1 pipelining?
- A) Text encoding is slower than binary
- B) There is no request identifier on the wire — responses must return in request order, so one slow response delays the rest
- C) TCP slow start
- D) Headers are too large

**22.** Why did HTTP/1.1 make the `Host` header mandatory?
- A) To authenticate the client
- B) To enable compression
- C) To let proxies cache responses
- D) Virtual hosting: many sites share one IP and port, so the request must carry the name of the site

**23.** Why is HPACK safe from CRIME-style attacks while gzipping headers is not?
- A) HPACK uses a fixed Huffman table and an exact-match index (no adaptive substring matching), so guesses next to a secret don't change the compressed size in a leaky way
- B) HPACK encrypts headers
- C) HPACK only compresses the first request
- D) HPACK has no dynamic table

**24.** HTTP/2 multiplexes streams on one TCP connection, yet one lost packet still stalls all of them. Why?
- A) HTTP/2 streams share one sequence number
- B) The server is single-threaded
- C) TCP delivers one ordered byte stream and can't see HTTP/2's streams, so bytes behind the gap wait even if they belong to other streams
- D) HPACK blocks on lost packets

**25.** Why is QUIC 0-RTT data restricted to idempotent requests (e.g. GET)?
- A) 0-RTT can't carry a body
- B) Early data can be replayed by an attacker, so a repeated request must be harmless
- C) 0-RTT uses UDP checksums that fail on POST
- D) Servers don't parse 0-RTT headers

---

## Session 6 — CDNs

**26.** You add an 11th cache to a pool of 10. Why do CDNs prefer consistent hashing over `hash(url) % N`?
- A) Modulo hashing can't be computed quickly
- B) Consistent hashing guarantees perfectly even load
- C) Modulo can't use URLs as keys
- D) With modulo ~90% of URLs map to a different cache (a near-total cache flush); consistent hashing moves only ~1/(N+1)

**27.** Where does a CDN edge actually beat going directly to the origin?
- A) On cache HITs, and on MISSes where it reuses a warm connection to the origin; a cold MISS is no faster than going direct
- B) On every request, including cold MISSes
- C) Only for static files over 1 MB
- D) Only when the user is within the same city as the origin

**28.** What makes web cache *poisoning* (Kettle) different from cache *deception* (Gil)?
- A) Poisoning steals private pages; deception injects scripts
- B) Poisoning abuses an *unkeyed* input (e.g. a header) reflected into a page everyone then receives from cache; deception tricks the cache into storing a victim's private page under a fake static URL
- C) Poisoning targets DNS; deception targets TLS
- D) They are two names for the same attack

**29.** Why is a fixed-window rate limit ("100 per 10 s") considered weak?
- A) It uses too much memory
- B) It can't count per client
- C) A client can send 100 at the end of one window and 100 at the start of the next, getting about 2× the limit in a short burst
- D) It only works over HTTP/1.1

**30.** An edge gateway validates JWTs. Why is it still unsafe if the origin's IP is publicly reachable?
- A) JWTs expire too quickly
- B) The edge strips the user's cookies
- C) The CDN leaks the origin's TLS key
- D) An attacker can skip the edge and call the origin directly, bypassing all checks — so the origin must only accept the edge (mTLS or a tunnel)

---

## Session 7 — Failures & retries

**31.** A `connect()` returns "Connection refused" instantly in one case and hangs for tens of seconds in another. What best explains the difference?
- A) Refused = DNS failure; hang = TLS failure
- B) Refused = server overloaded; hang = server crashed
- C) Refused = host reachable but nothing listening, so the kernel sent RST; hang = SYNs getting no answer at all (dropped, no host, firewall), so TCP keeps retransmitting
- D) They are the same error with different timeouts

**32.** What distinguishes HTTP 502 from 504 at a reverse proxy?
- A) 502: the proxy got an invalid/bad response from upstream; 504: the upstream didn't respond in time
- B) 502: client error; 504: server error
- C) 502: authentication failed; 504: rate limit
- D) They are interchangeable

**33.** Why add random jitter on top of exponential backoff?
- A) To make waits longer
- B) So clients that failed together don't all retry at the same instant and cause a retry storm
- C) To bypass rate limits
- D) To avoid DNS caching

**34.** A client times out waiting for the response to `POST /charge`. Why is blindly retrying dangerous?
- A) POST can't be retried at all
- B) The server always rejects duplicates
- C) Retries are blocked by TCP
- D) A timeout doesn't mean the work didn't happen — the charge may have succeeded, so a retry needs idempotency (e.g. an idempotency key)

**35.** What does a circuit breaker do?
- A) Encrypts failing connections
- B) Retries faster after each failure
- C) After repeated failures it stops calling the dependency for a while (fail fast), then probes later, protecting both caller and callee
- D) Splits traffic evenly across servers

---

## Session 8 — Video streaming at scale

**36.** Why does polling a scorecard through a CDN scale to 50M viewers while pushing it over WebSockets/MQTT doesn't?
- A) Polling uses less bandwidth per message
- B) Everyone gets the same file, so caches answer for the origin and servers stay stateless; push means every viewer holds a socket all match, which a CDN can't cache
- C) WebSockets can't carry JSON
- D) CDNs block long-lived connections

**37.** By Little's Law (L = λ × W), why is push ~1000× more concurrent than polling for the same audience?
- A) Push messages are larger
- B) Push uses more threads per request
- C) Polling is spread across more servers
- D) W (time each connection is held) jumps from milliseconds per poll to hours per held socket

**38.** Why is caching a 404 for minutes dangerous at a live stream's edge?
- A) The player may request a segment just before it exists; a cached 404 keeps being served after the file appears, stalling playback
- B) 404s are never cacheable by spec
- C) It breaks TLS session resumption
- D) It increases the segment size

**39.** In an MPEG-TS segment, what does the 13-bit PID in each 188-byte packet do?
- A) It stores the packet's length
- B) It is a checksum
- C) It says which elementary stream the packet belongs to (video, audio, tables), so several streams can be multiplexed in one byte stream
- D) It numbers the segment in the playlist

**40.** `ffmpeg -codec: copy -hls_time 4` produced ~8.33 s segments. Why?
- A) `-re` slows the stream by half
- B) With `-codec copy` ffmpeg can only cut at existing keyframes, and x264's default GOP is 250 frames (8.33 s at 30 fps)
- C) `-hls_list_size 5` doubles segment duration
- D) HLS requires 8 s segments

---
---

# ANSWER KEY

| # | Ans | Why |
| --- | --- | --- |
| 1 | B | Kernel completes the handshake into the accept queue; nobody accepts → hang |
| 2 | C | Ephemeral port assigned at `connect()`; only servers need well-known ports |
| 3 | A | SIGPIPE (13) default action = terminate |
| 4 | D | base64 = safe alphabet for text-only channels; "a wrapper, not a design" |
| 5 | B | TLS sits under the app protocol |
| 6 | A | Radio can't listen while transmitting |
| 7 | C | Loses wscale/SACK/timestamps → only under pressure |
| 8 | D | SYN+ACK combine; FIN+ACK can't (half-close) |
| 9 | B | Out-of-band signalling |
| 10 | C | Envelope ≠ headers; no base auth |
| 11 | D | FD_SETSIZE bitmap is compile-time |
| 12 | B | L = λW → 10× |
| 13 | A | Long-lived workers over a socket; no fork+exec per request |
| 14 | C | In-process vs separate process |
| 15 | B | Kernel-held watch list, O(ready) |
| 16 | C | "Why a worker per connection at all?" |
| 17 | D | `^~` suppresses the regex search |
| 18 | A | `inactive` = unread eviction; `valid` = freshness |
| 19 | B | gzip needs user-space bytes; sendfile skips them |
| 20 | C | Non-blocking → request may arrive in pieces |
| 21 | B | No request ID: "the order IS the identifier" |
| 22 | D | Virtual hosting |
| 23 | A | Fixed Huffman + exact-match index; "never indexed" option |
| 24 | C | TCP HOL: loss recovery can't see streams |
| 25 | B | 0-RTT is replayable → idempotent only (425 Too Early) |
| 26 | D | Modulo ≈ 90.9% moved; consistent ≈ 1/(N+1) |
| 27 | A | Edge wins on HIT and warm pools; cold MISS no faster |
| 28 | B | Unkeyed input vs fake static extension |
| 29 | C | Boundary burst ≈ 2× |
| 30 | D | Lock origin to edge with mTLS/tunnel |
| 31 | C | RST = refused; no reply = timeout (SYN retries) |
| 32 | A | Bad Gateway vs Gateway Timeout |
| 33 | B | Avoid synchronised retry storms |
| 34 | D | Timeout ≠ not done; need idempotency |
| 35 | C | Fail fast, probe later |
| 36 | B | Cacheable + stateless vs stateful sockets |
| 37 | D | W goes from ms to hours |
| 38 | A | Live-edge 404 for a soon-to-exist file keeps being served |
| 39 | C | PID identifies the stream (multiplexing) |
| 40 | B | Keyframe-bound cuts + x264 GOP 250 |

**Scoring:** 37–40 great · 32–36 re-check the traps in the cheat sheet · <32 re-read the sessions you missed.
