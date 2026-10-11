# Computer Networks @ Scaler — Master Study Notes (Sessions 1–8)

> Built from the lecture PDFs and the Session 7 PNG in this folder. Read top to bottom; every session ends with a "Quiz points" box. The last part is a full revision cheat sheet + practice questions.

## Course roadmap

| Session | Topic (lecture title) | One-line idea |
| --- | --- | --- |
| 1 | Network programming, from the socket up | A TCP server is 7 syscalls; everything else is a wrapper |
| 2 | Eagle-eye view: OSI · SS7 · TCP/UDP/QUIC · text protocols | One layer's headers are another layer's body |
| 3 | One process, many clients — scaling servers | The event loop is the architecture; concurrency = throughput × latency |
| 4 | nginx and the code that explains it | Apache made the worker cheaper; nginx deleted it |
| 5 | HTTP, 1996 → now (1.0, 1.1, 2, QUIC/3) | Same semantics, three wire formats; every fix is the next problem |
| 6 | (Ab)using CDNs | A reverse proxy rented in 300+ cities; it became your security perimeter |
| 7 | Building for failures: failures & retries | Every step of a request fails differently; react per step |
| 8 | Streaming video at large scale | Every live stream is a scorecard with bigger bytes |

Syllabus note: the early slides list W7 "Economics of cloud tech" and W8 "Building for failures". From Session 5 on, the slides list **W7 Building for failures** and **W8 Streaming video at large scale**. These notes follow the later version.

### Threads that run through the whole course
1. **Encapsulation** — Ethernet ⊃ IP ⊃ TCP ⊃ HTTP is the same picture as MTP2 ⊃ MTP3 ⊃ SCCP ⊃ TCAP ⊃ MAP ⊃ TPDU.
2. **Framing** — a receiver knows a message ended by **fixed length**, a **delimiter**, or a **length prefix** (or delimiter + length). "There is no third option" (fixed length is the trivial case).
3. **Amortise the setup** — pre-fork, pre-thread, FastCGI, connection pools, keep-alive, TLS resumption: pay expensive setup once, not per request.
4. **Round trips are the tax** — bandwidth can be bought, latency (speed of light) cannot.
5. **Separate control from data** — SS7 vs in-band tones, FTP control vs data connection, SIP signalling vs RTP media.

---

# SESSION 1 — Network Programming, From the Socket Up

**Core claim:** A TCP server is **seven system calls**: `socket → bind → listen → accept → read → write → close`. Express, Flask, Go's net/http are all wrappers around this sequence.

- Four calls only a **server** makes: `bind`, `listen`, `accept` (plus `socket`, shared). A **client** does `socket → connect → read/write → close`.
- The course "port" is **2026**.

## 1.1 The echo server (≈20 lines of C)

```c
int server_fd = socket(AF_INET, SOCK_STREAM, 0);   // IPv4, TCP
struct sockaddr_in addr = {0};
addr.sin_family = AF_INET;
addr.sin_addr.s_addr = INADDR_ANY;                 // listen on every interface
addr.sin_port = htons(2026);                       // host→network byte order
bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
listen(server_fd, 1);                              // 1 = accept-queue (backlog) depth
while (1) {
    int client_fd = accept(server_fd, NULL, NULL); // blocks until a connection is queued
    char buf[4096];
    int n = read(client_fd, buf, sizeof(buf));
    write(client_fd, buf, n);                      // echo it back ONCE
    close(client_fd);
}
```

- `AF_INET` = IPv4 address family; `SOCK_STREAM` = TCP (byte stream). (`SOCK_DGRAM` would be UDP.)
- Demo: `gcc -o echo_server echo_server.c` then `nc localhost 2026`.
- **Persistent version:** "One read() is not a conversation." Wrap read/write in `while ((n = read(...)) > 0) write(...)` so the server keeps echoing until the client closes (read returns 0 = EOF).

## 1.2 Ports — "Everything below 1024 belongs to root"

| Range | Who can bind | Examples |
| --- | --- | --- |
| < 1024 (privileged / well-known) | root only | 80 HTTP, 443 HTTPS, 25 SMTP, 21 FTP, 110 POP |
| ≥ 1024 | anyone | 3000 node, 8080 alt-http, 6379 redis, 2026 (ours) |

- Why it matters: binding 80 means running as root → a bug in your request parser = **root compromise**.
- Real deployments: app binds **8080 as an unprivileged user**; a **front proxy** (which does almost nothing) owns 80/443.

## 1.3 Thought experiment — what breaks if you skip a call?

| Mistake | What the client sees | Why |
| --- | --- | --- |
| **No `bind()`** (nothing on the port) | **Connection refused** — fast, loud | Kernel answers the SYN with an **RST** immediately; nobody owns the port |
| **`bind()`+`listen()` but no `accept()`** | **It just hangs** | Kernel **completes the 3-way handshake on your behalf**; connection sits in the accept queue; process never picks it up → client waits until TCP times out. Looks exactly like an overloaded server |

## 1.4 `listen(fd, backlog)` — the accept queue

1. The kernel finishes the handshake without you; by the time `accept()` returns, the connection has been established for a while.
2. **Full-queue behaviour is not portable** — "connection refused" on some systems, indefinite "Trying..." on others. Don't build logic on it.
3. We passed 1; real servers pass hundreds. Linux **caps it at `net.core.somaxconn`**, so the number in code may not be the number in effect.
4. The backlog is the **accept-queue depth, not a connection limit** (comes back in SYN floods, Session 2).

## 1.5 Signals — SIGPIPE is the one that will kill you

| Signal | Number | Meaning |
| --- | --- | --- |
| SIGINT | 2 | Ctrl-C |
| SIGKILL | 9 | Cannot be caught |
| **SIGPIPE** | **13** | **Write to a socket the peer already closed → process dies by default, no error, no exception** |
| SIGTERM | 15 | The polite kill |
| SIGHUP | — | SSH disconnect |
| SIGSTOP / SIGTSTP | — | Ctrl-Z |

- Demo: server reads, `sleep(1)`, client force-closes with RST; first `write()` triggers SIGPIPE; second write never runs.
- **`SO_LINGER {1, 0}`** (linger on, timeout 0) = **abortive close: sends RST instead of FIN**. Connection torn down immediately, unsent data discarded, **no TIME_WAIT**. Fast but lossy — for demos, not production.
- (Real fix in servers: ignore SIGPIPE / use `MSG_NOSIGNAL` and handle the EPIPE error.)

## 1.6 You already have a client

- **telnet** — if a protocol is text, your keyboard is an implementation of it: `telnet google.com 80`, `telnet localhost 2026`, `telnet mail.example.com 25`.
  - Typing `GET / HTTP/1.1` + `Host: google.com` + blank line → Google answers `HTTP/1.1 301 Moved Permanently`, `Location: http://www.google.com/`, `Cache-Control: public, max-age=2592000` (30 days), `Server: gws`, `Content-Length: 219`.
- **openssl s_client** — for anything encrypted (telnet is useless once TLS is in the way): `openssl s_client -connect www.hotstar.com:443`.
- **netcat (nc)** — everything else: `nc localhost 2026` (client), `nc -l 9000` (listen = tiny server).

## 1.7 Writing the client

```c
struct hostent *he = gethostbyname("localhost");   // DNS hidden in a function call
int fd = socket(AF_INET, SOCK_STREAM, 0);
memcpy(&addr.sin_addr, he->h_addr_list[0], he->h_length);
addr.sin_port = htons(8080);
connect(fd, ...);           // triggers the 3-way handshake
write(fd, "hello", 5);
close(fd);
```

**Notice what's missing: no bind, no listen.**

### Ephemeral ports
- **Clients never bind; the kernel picks a random high port** at `connect()` time from the ephemeral range — **typically 32768–60999 on Linux**.
- Server must bind a known port (clients need a fixed address — the reason well-known ports exist).
- Ephemeral ports are finite and **TIME_WAIT holds each for ~60 s after close** → busy clients **do run out**.

### Byte order — `htons()`
- **htons = host to network, short (2 bytes)**; `htonl` = 4 bytes; `ntohs`/`ntohl` on the way back.
- Port 2026 = **0x07EA**. Little-endian (x86/ARM laptop) stores `EA 07`; **network byte order is big-endian**: `07 EA`.

### `gethostbyname()` — one function call is a whole protocol (DNS)
1. **/etc/hosts first**, before any network traffic (why editing hosts overrides everything, and a stale entry is hard to debug).
2. **UDP query to your resolver** (from `/etc/resolv.conf`); it recurses on your behalf: **root → TLD → authoritative**.
3. **Cached for the TTL, and it blocks** — fast when warm, seconds when cold, no timeout you control.
- Use **`getaddrinfo()`** in real code: `gethostbyname` is **IPv4-only and not thread-safe**.

## 1.8 Where we are on the OSI stack

| Layer | Name | What we touched |
| --- | --- | --- |
| 7 | Application | our echo protocol, HTTP |
| 4 | Transport | TCP, ports, `htons(2026)` |
| 3 | Network | IP, `INADDR_ANY`, 127.0.0.1 |
| 2 | Data link | Ethernet, Wi-Fi, MAC addresses |
| 1 | Physical | copper, fibre, radio |

"We have been writing layer 7 this whole time." Ports are L4, IP addresses are L3.

## 1.9 HTTP & curl
- An HTTP client is just client.c with a string in it: connect to 80, write `GET / HTTP/1.1\r\nHost: google.com\r\n\r\n`, read until close.
- **CRLF line endings, and the blank line is mandatory** (it ends the headers).
- curl as a teaching tool: `curl google.com`, `curl -i google.com` (show response headers), `curl -vv https://google.com 2>&1 | less` (verbose: TLS handshake, headers).

## 1.10 Many clients at once

| One process per connection: `fork()` | One process, many sockets: `select`/`epoll` |
| --- | --- |
| Dead simple; OS does scheduling; each child has own memory → crash contained | Ask kernel which sockets are ready, handle only those; no context switching, no per-client memory |
| A process per client. Fine for hundreds, hopeless at 10,000 | Harder to write; one slow handler blocks everything. **What nginx and Node do** |

### `fork()` returns twice
| Return value | Meaning |
| --- | --- |
| `0` | You are the **child** — handle this client, then exit |
| `> 0` | You are the **parent** — value is the child's PID; close your copy of the fd, go back to `accept()` |
| `-1` | fork **failed** (out of processes/memory) — almost nobody checks |

### select vs epoll
| select | epoll |
| --- | --- |
| Portable, **O(n)** | Linux, **O(ready)** |
| Rebuild the fd set every call; kernel walks all of them | Register interest once; kernel returns only fds that changed |
| **FD_SETSIZE caps ~1024 descriptors** | Equivalents: **kqueue** (BSD/macOS), **IOCP** (Windows). nginx & Node are built on it |

### Client-side limits
- **6** — Chrome's old per-host connection cap; requests 7–10 just queue.
- **`ulimit -n`** — hard ceiling on open file descriptors; sockets count; often **1024**.
- **Connection pool** — open once, reuse many times; skip TCP + TLS handshake after the first.

### Socket options
- **INADDR_ANY** — listen on every interface. Convenient in dev; in prod bind a specific address when you mean one.
- **Promiscuous mode** — see traffic that isn't yours (on a hub every frame reaches every port) → how sniffers work, why plaintext protocols died.
- **SO_REUSEADDR** — the one you'll actually use: without it, restarting fails with **"address already in use"** while the old socket sits in **TIME_WAIT**.

### See the bytes: tcpdump / Wireshark / strace
```
sudo tcpdump -ni any port 2026 -w 1.pcap   # capture to file
tcpdump -r local_capture.pcap -A            # read as ASCII
tcpdump -r local_capture.pcap -X            # hex + ASCII
```

## 1.11 SSL / TLS — "SSL secures TCP, not HTTP"
TLS sits under the application protocol → same machinery protects SSH-like, SMTP, DB connections, anything on a socket.
1. **Exchange keys & certificates** — **asymmetric crypto to agree on a shared secret, then symmetric crypto for the data** (symmetric is dramatically faster).
2. **The certificate binds a key to an identity**; the **CA chain** is why you believe it. Certificates **expire** (the 3 a.m. outage).
3. **Certificate pinning** removes the CA from the trust equation — common in mobile apps: trust *this exact* cert.

## 1.12 Protocol design

**Text vs binary**: Text won (HTTP — you can telnet it, tcpdump it, read logs) but is verbose, ambiguous at edges, slower to parse. Binary is compact, unambiguous, cheap to parse but needs tooling. **HTTP/2 is binary.**

### Message framing — "TCP gives you a byte stream, not messages"
The single most important decision in your protocol; three answers:
1. **Fixed length** — every message exactly N bytes. Trivial to parse; pay in padding; can never change N.
2. **Delimited** — read until a sentinel (HTTP's blank line). Simple until the delimiter appears in your data → **escaping**.
3. **Length prefix** — send size, then bytes (`Content-Length: 219`). Robust, binary-safe; what most modern protocols do.

### Binary encodings
- **BCD (Binary Coded Decimal)** — 4 bits (a nibble) per decimal digit. 98765 → `1001 1000 0111 0110 0101` → hex `98 76 5F` (F pads the odd nibble). Digits "just show up" in hex. Half the size of ASCII, no conversion, exact decimal arithmetic. **Still used in SIM cards, SMS, card transactions.**
- **ASN.1 (1984)** — write the grammar (schema) once, **codec (encoder/decoder) is generated**. Still under **X.509 (certificates), LDAP, SNMP, the telecom stack**.
  ```
  Item ::= SEQUENCE { itemCode INTEGER (1..99999), color VisibleString ("Black"|"Blue"|"Brown"), isTaxable BOOLEAN }
  ```
- **TLV (Type-Length-Value)** — "ASN.1 you can write on a napkin". **Self-describing**: a parser that doesn't know a type can **skip it using the length** → **forward compatible**. Used by **TLS extensions, ISO 8583, protobuf**.
- **Hex vs base64**: hex is for *reading* (2 chars/byte; `tcpdump -X`). base64 is for *transport* over text-only channels (Basic auth, JWTs, email attachments, data URIs); **costs 33% more — 3 bytes become 4 characters**. "A wrapper, not a design."

### RPC & gRPC
- **RPC = framing + a function name.** Marshal (objects → bytes: function name + args) → frame & send → **"the network is not a function call"**: calls fail halfway, time out with work possibly done, get retried.
- **gRPC = RPC with protobuf underneath.** `.proto` schema first → generate client/server code in any language; **TLV on the wire** so new fields don't break old clients; runs on **HTTP/2** (binary, multiplexed — many streams over one connection). Cost: **can't read it with curl** — speed bought with debuggability. Faster than JSON, easier than ASN.1.

### Homework (Session 1)
Wireshark Redis traffic (RESP is text + length-prefixed) · write server/client in your language · go beyond echo (pick framing) · write base64 from scratch · TLV both directions with nested/optional fields · write a curl imitation (redirects, headers, chunked encoding).

> **Quiz points — Session 1**
> - 7 calls: socket, bind, listen, accept, read, write, close. Client: socket, connect, read/write, close (no bind/listen).
> - No listener → RST → "Connection refused". Listening but no accept → handshake completes, client hangs.
> - backlog = accept-queue depth, capped by `net.core.somaxconn`.
> - Ports <1024 need root. Ephemeral range 32768–60999. TIME_WAIT ~60 s.
> - SIGPIPE (13) kills you on write to closed peer. SO_LINGER{1,0} → RST, no TIME_WAIT. SO_REUSEADDR fixes "address already in use".
> - htons: 2026 = 0x07EA → wire `07 EA` (big-endian).
> - gethostbyname: /etc/hosts → UDP to resolver → root→TLD→authoritative; cached for TTL; use getaddrinfo.
> - select O(n), FD_SETSIZE 1024; epoll O(ready); kqueue/IOCP.
> - fork returns 0 (child), >0 (parent, child PID), -1 (fail).
> - TLS: asymmetric for key agreement, symmetric for data. Pinning bypasses CA.
> - Framing: fixed, delimiter, length-prefix. TLV skippable → forward compatible. base64 = +33%. BCD = 4 bits/digit.

---

# SESSION 2 — Eagle-Eye View: OSI · SS7 · TCP/UDP/QUIC · Text Protocols

**Theme:** "Seven syscalls make a server. Seven layers of nesting carry eleven bytes." **One layer's headers are another layer's body.**
Agenda: Sockets → OSI → SS7 → TCP·UDP·QUIC (and BBR) → text protocols (SMTP, POP, IMAP, FTP).

## 2.1 Sockets recap
- Server: socket → bind → listen → accept → read → write → close. `listen(fd, 1)`: the 1 is **accept-queue depth, not the connection limit**. `htons`: the wire is big-endian.
- Client: no bind, no listen; kernel picks an ephemeral source port; **`connect()` triggers the handshake**.
- Normal `close()` sends **FIN** (polite "I'm done sending"); socket then sits in **TIME_WAIT for 2 MSL** (MSL = Maximum Segment Lifetime). `SO_LINGER {1,0}` sends **RST**: immediate teardown, unsent data discarded, no TIME_WAIT.

## 2.2 OSI — "a 1984 committee model that outlived almost everything built on it"

| Layer | Name | Examples / job |
| --- | --- | --- |
| L7 | Application | HTTP, FTP, DNS, SMTP |
| L6 | Presentation | Encryption, compression, encoding |
| L5 | Session | Session management, authentication |
| L4 | Transport | TCP, UDP |
| L3 | Network | IP, ICMP, routing |
| L2 | Data link | Ethernet, MAC, ARP, switches |
| L1 | Physical | Cables, signals, hardware |

**TCP vs UDP (both L4)**

| TCP | UDP |
| --- | --- |
| Connection-oriented | Connectionless |
| Reliable, ordered delivery | No delivery guarantee, no ordering |
| Flow + congestion control, error recovery | Fast, low overhead |
| Higher latency | Low latency |
| HTTP, FTP, SMTP, SSH | DNS, VoIP, video calls, gaming |

### L1/L2: wire vs radio — CSMA/CD vs CSMA/CA
- **Ethernet (wire) detects collisions — CSMA/CD.** **Wi-Fi (802.11, radio) can only avoid them — CSMA/CA.**
- Why not CD on radio: a radio **cannot listen while it transmits** (its own signal drowns everything).
- CSMA/CA steps: listen to channel (carrier sense) → if busy, defer → **random backoff (contention window)** → transmit → **wait for explicit ACK for every frame**; no ACK → back off and retransmit.
- **≈2 ms of contention delay** before a frame leaves. Every Wi-Fi frame is ACKed **at L2**, long before TCP (L4) knows anything happened.

### Starlink — "Your packet can go to space and back and nothing above L2 notices"
Laptop → Wi-Fi/Ethernet → Starlink phased-array dish → RF uplink (Ku/Ka band) → **LEO satellite ~550 km, ~20 ms** → optional laser crosslink (sat-to-sat) → ground gateway → internet. Nine physical hops; the IP header arrives unchanged **except TTL, checksum and any NAT rewrite**. That is the whole argument for layering.

## 2.3 Packet shape — encapsulation byte by byte

| Layer | Header fields (sizes) |
| --- | --- |
| **L2 Ethernet II frame** | Dst MAC **6 B**, Src MAC **6 B**, EtherType **2 B (0x0800 = IPv4)**, payload **46–1500 B (MTU)**, FCS **4 B (CRC-32)** |
| **L3 IPv4 packet (20 B header)** | Ver/IHL, Total Len (2 B), **TTL (1 B)**, **Proto (6 = TCP)**, Checksum (2 B), Src IP 4 B, Dst IP 4 B |
| **L4 TCP segment (20 B header)** | Src port 2 B, Dst port 2 B, **Seq 4 B**, **Ack 4 B**, Flags (SYN/ACK/FIN), Window 2 B; payload ≤ MSS (typically 1460 B) |
| **L7** | `GET / HTTP/1.1 · Host: example.com` — opaque byte stream TCP doesn't care about |

**Byte budget:** 1500 MTU − 20 IP − 20 TCP = **1460 B MSS**. Add 14 B Ethernet header + 4 B FCS → wire frame **1518 B**.

## 2.4 SS7 — "a second internet, older than TCP/IP"

**SS7 (1975)'s one big idea: get signalling out of the voice channel.**
- Before: **in-band signalling** — voice and control on the same channel; a **2600 Hz tone** meant "trunk is idle"; digits dialled as MF tones. Anyone who could make the sound could make the decision (**blue boxes / phone phreaking**).
- After: **out-of-band** — voice bearer = **64 kbps DS0** (conversation only) + separate packet-switched **signalling network** (MTP/SCCP/TCAP/MAP/ISUP). = **control plane vs data plane** separation.

### SS7 stack vs TCP/IP stack

| OSI | SS7 | TCP/IP |
| --- | --- | --- |
| L7 | MAP · INAP · CAP · ISUP (call setup, roaming, SMS) | HTTP · DNS · SMTP · SIP |
| L5–L6 | **TCAP** (dialogues, components, ASN.1 BER) | No distinct layer (TLS / app framing) |
| L4 | **SCCP** (classes 0–3; subsystem numbers; **Global Title Translation**) | TCP / UDP (ports, sequencing, windowing) |
| L3 | **MTP3** (point-code routing, SLS load sharing) | IP (best-effort, fragmentation, TTL) |
| L2 | **MTP2** (signal units, FSN/BSN, **CRC-16**, retransmission) | Ethernet/PPP/HDLC (framing, MAC, FCS) |
| L1 | **MTP1** (64 kbps DS0 on E1/T1) | copper, fibre, radio |

"SS7 is a whole stack; TCP is one protocol at L4. Compare stack to stack."

### Encapsulation of an SMS "Hello World!" (MO-ForwardSM)
MTP2 MSU (SIF cap 273 octets) ⊃ MTP3 (SIO 0x83, DPC 2065, OPC 2050, SLS 5) ⊃ SCCP UDT (class 1, Called/Calling Global Titles = phone numbers) ⊃ TCAP BEGIN ⊃ Invoke (**opCode 46 = mo-ForwardSM**) ⊃ MAP MO-ForwardSM-Arg ⊃ SMS-SUBMIT TPDU (TP-DCS 0x00 = GSM-7, TP-UDL 0x0C = 12) ⊃ TP-UD `C8 32 9B FD 06 5D DF 72 36 39 04` = "Hello World!" (12 chars, 84 bits, **11 octets**).

### Why an SMS is 140 bytes
Three stacked limits — the smallest wins:
- **272 octets** — SIF, MTP2's hard ceiling (one Message Signal Unit)
- **~200 octets** — MAP's sm-RP-UI field
- **140 octets** — TP-UD, the SMS itself — chosen so the whole MAP operation always fits in one MSU.
**No segmentation, no reassembly** → one text = one signalling packet. Why SMS ran on 1980s hardware and still works when data is down.

### 160 characters in 140 bytes — GSM-7 packing
140 octets × 8 = 1120 bits ÷ **7 bits per char = 160 chars**. Septets packed into a continuous bit stream. 12 chars × 7 = 84 bits → 11 octets (4 bits zero padding).
**Switch to UCS-2 (emoji / non-Latin): 140 ÷ 2 = 70 characters.** One emoji can more than halve your message and silently cost a second SMS.

### Sending an SMS = a database lookup wrapped in a queue
Phone A → **SMS-SUBMIT** → VMSC/VLR → **MAP mo-ForwardSM** → **SMSC (store & forward)** → TCAP END (accepted; delivery is now SMSC's problem) → SMSC asks **HLR** (subscriber DB) `sendRoutingInfoForSM(MSISDN)` → HLR returns **IMSI + serving MSC address** → **MAP mt-ForwardSM (SMS-DELIVER)** → MSC B → Phone B → delivery ack → (SMS-STATUS-REPORT only if requested).

### A phone call = ISUP signalling + separate voice
Phone A off-hook + digits → MSC A sends **IAM (Initial Address Message)** → MSC B rings B → **ACM (Address Complete)** → caller hears ringback → B answers → **ANM (Answer Message)** → voice path cut through → conversation on **64 kbps bearer circuit, no SS7 involvement** → on-hook → **REL (Release)** → **RLC (Release Complete)**. Four messages set up a call; signalling idle during the talk.

### 5G / IMS — SIP: same call, HTTP-shaped text over IP
Alice → `INVITE sip:bob@... (SDP offer)` → proxy/SBC (IMS core) → Bob; **100 Trying · 180 Ringing · 200 OK (SDP answer)** → **ACK** end to end → **RTP/SRTP media flows directly between endpoints over UDP** → BYE → 200 OK. SIP borrowed HTTP's status codes. Signalling text, media RTP/UDP — control and data on separate paths. (Try: Asterisk/FreeSWITCH + Linphone/Zoiper + Wireshark.)

### SS7 vs TCP — "SS7 makes every hop reliable. TCP makes only the endpoints reliable."

| Function | SS7 | TCP |
| --- | --- | --- |
| Sequencing | FSN — 7 bits per signal unit, wraps at 128 | 32-bit sequence number, **per byte** |
| Ack | BSN + BIB, piggybacked | ACK number, cumulative (+SACK) |
| Retransmission | BIB toggle; PCR on long/satellite links | RTO timers, **fast retransmit on 3 dup-ACKs** |
| Flow control | SIB in LSSU — blunt stop/go | **Sliding window** advertised every segment |
| Error detection | **CRC-16** per signal unit | 16-bit ones-complement checksum |
| Addressing | Point Code (OPC/DPC) + SSN + Global Title | IP address + port |
| Connection setup | Connectionless; SCCP class 2/3 if needed | 3-way handshake |
| Congestion control | **Hop-by-hop** via MTP3 | **End-to-end** (Reno, CUBIC, BBR) |
| Scope of reliability | **Per hop** | **End to end** |
| Max payload | 272 octets | ~1460 B typical; 64 KB with window scaling |
| Security | None — trust by point code | None natively; TLS above |

## 2.5 BBR congestion control (Google, 2016)
- **Loss-based TCP (Reno, CUBIC)** grows until a packet drops, then halves → **sawtooth**; needs loss to make progress; on links that drop for non-congestion reasons (lossy/wireless/long fat links) they crawl. Also fills buffers → **bufferbloat** (2011).
- **BBR measures bottleneck bandwidth × round-trip propagation time** and sends at what the path can carry, **keeping the queue near empty**. Google reports up to **2,000×** throughput on some benchmarks and much lower latency.

## 2.6 TCP handshake, SYN cookies, teardown

### Open: 3 segments — "each direction needs its own sequence number confirmed"
1. Client → `SYN seq=1000` (options: MSS 1460, SACK permitted, wscale 7). Client CLOSED → app called `connect()`.
2. Server → `SYN-ACK seq=5000 ack=1001`. Server state **SYN RECEIVED** — a **half-open entry in the backlog**.
3. Client → `ACK seq=1001 ack=5001` (no payload needed). Both **ESTABLISHED**; server's `accept()` returns.
- The server's own SYN is what forces the third leg.
- **SYN and FIN each consume a sequence number** → ack=1001 answers seq=1000 though the SYN had no payload.
- **Random ISN**: early stacks used predictable ISNs → attacker could inject forged segments blind (**Mitnick attack**). **RFC 6528**: ISN = keyed hash of the 4-tuple + timer.

### SYN flood & SYN cookies (1996)
- **Attack:** spoofed SYNs, never complete handshake; each costs attacker 1 packet and the server a half-open backlog entry until timeout. Fill backlog → legit connections refused. (Remember `listen(fd, 1)`.)
- **Defence: keep no state.** Encode connection params into the **server's ISN** = keyed hash of the 4-tuple + coarse timestamp + MSS. Client's ACK returns it +1; server recomputes, validates, reconstructs the connection.
- **Cost:** only 32 bits of ISN → most TCP options (**window scale, SACK, timestamps**) mostly lost → cookies switch on **only under pressure**.
- Same trick elsewhere: push state into a token the client hands back (HTTP cookies, JWTs, signed URLs…).

### Close: 4 segments, not 3
Client `FIN` → server `ACK` (server in **CLOSE_WAIT**, client in **FIN_WAIT_2** — **half-closed**, still receiving) → server sends remaining data → server `FIN` → client `ACK` → client in **TIME_WAIT for 2 MSL**, then CLOSED.
- **SYN+ACK can be combined; FIN+ACK cannot** (the other side may still have data).
- **Sockets stuck in CLOSE_WAIT = almost always an application that forgot to call `close()`.** Not a network problem — look at your code.
- **TIME_WAIT is why "address already in use" on restart → SO_REUSEADDR.**

## 2.7 The round-trip tax

| Setup | RTTs before first app byte |
| --- | --- |
| TCP | 1 |
| TCP + TLS 1.2 | 3 (handshake, ClientHello/ServerHello, key exchange) |
| TCP + TLS 1.3 | 2 (one round trip of crypto instead of two) |
| TCP Fast Open | data in the SYN for returning clients |
| QUIC / HTTP/3 | 1 (transport + crypto folded together) |

"Bandwidth you can buy. Round trips you cannot — **Mumbai to Virginia is ~190 ms**."

## 2.8 UDP — "TCP with every promise removed"
- **TCP header: 20 B minimum** (src port, dst port, seq, ack, flags, window, checksum, urgent, options 0–40 B).
- **UDP header: 8 B total** — **Src port (2) · Dst port (2) · Length (2) · Checksum (2)**; payload up to **65,507 B**.
- Users: Zoom, WebRTC, game servers, DNS, real-time streaming — a retransmitted audio frame arrives too late to play, so dropping is correct.
- Broadcast for LAN discovery: nice idea, in practice people hard-coded IPs.

## 2.9 QUIC / HTTP/3 — "QUIC rebuilds TCP inside UDP, in userspace"
- HTTP/1.1 & HTTP/2 over TCP: TLS separate handshake; TCP = one ordered byte stream → **one lost packet stalls every stream (head-of-line blocking)**.
- HTTP/3 over QUIC: QUIC gives **each stream its own sequence space** + TLS 1.3 in one handshake → lose a packet, only that stream waits. UDP's 8 bytes are left alone by kernels & middleboxes.
- **Why userspace matters:** TCP lives in the kernel → changing it means an OS update for the planet + hoping middleboxes don't object. QUIC ships in the browser → Google can deploy a congestion-control change "on Tuesday".
- Adoption: still adopting HTTP/2; HTTP/3 not QUIC-everywhere yet. Lecturer's prediction: media over QUIC widespread in 2–5 years.

## 2.10 Text protocols you can speak by hand

### SMTP — "the S is Simple; it has never stood for Secure"

| Port | Use |
| --- | --- |
| **25** | SMTP relay, server-to-server, plaintext |
| **587** | Submission, client-to-server, **STARTTLS** — use this one |
| **465** | SMTPS, **implicit TLS** from the first byte |
| 110 / 143 | POP3 / IMAP retrieval |

- Stayed text: every relay must read/rewrite/add headers; extensible (unknown header = nothing breaks). STARTTLS, **SPF, DKIM, DMARC** are all later patches answering "is this sender allowed to say that?"
- **No authentication in base SMTP** — `MAIL FROM` is whatever you type.
- Session by hand (`telnet localhost 3025`): `EHLO scaler-demo` → `MAIL FROM:<jeet@scaler.com>` → `RCPT TO:<kshitij@scaler.com>` → `DATA` → headers (From/To/Subject) → **blank line** → body → **`.` alone on a line** → `QUIT`.
- **Envelope vs letter:** MAIL FROM / RCPT TO = envelope (routing). From:/To: inside DATA = text printed on the letter; **they don't have to match; nothing checks**.
- **Lone dot** ends the message → a body line starting with "." gets an extra dot (**dot-stuffing**). Miss the blank line → subject becomes body.
- Demo containers: **mailpit** (SMTP 1025, web UI 8025), **greenmail** (SMTP 3025, POP3 3110, user bob/secret).

### MIME & base64 — images travel as text, +33%
- 3 bytes (24 bits) regrouped as **4 × 6-bit** values → 64 safe printable chars: **A–Z a–z 0–9 + /** and **= padding**. "Man" (0x4D 0x61 0x6E) → "TWFu".
- Size **4/3 ≈ +33%**, **76 characters per line** (RFC 2045).
- Parts separated by a boundary: `Content-Type: multipart/mixed; boundary="=_a7f3c91"`, parts start `--=_a7f3c91`, end `--=_a7f3c91--`; `Content-Transfer-Encoding: base64`.

### POP3 — four verbs (port 110; POP3S 995)
`USER bob` / `PASS secret` (plaintext! → POP3S on 995) then **STAT** (count + bytes), **LIST** (number + size per message), **RETR n** (whole message n), **DELE n** (mark for deletion, applied at **QUIT**).

### POP3 vs IMAP

| | POP3 (110) | IMAP (143) |
| --- | --- | --- |
| Where mail lives | On your device; server = spool to empty | On the server; client holds a cache |
| Second device | Sees nothing | Same mailbox, same state |
| Read/unread | Local only | Server-side flags `\Seen \Answered \Flagged` |
| Folders | Just the inbox | Arbitrary hierarchy over the wire |
| Search | Download all, search locally | `SEARCH` on server; `IDLE` pushes new mail |
| Partial fetch | No — RETR = whole message | `FETCH BODY[1]` — one MIME part |

"POP puts the state on your machine, IMAP puts it on the server."

### Framing — length or delimiter (or both)

| Delimiter | Length | Both |
| --- | --- | --- |
| SMTP lone "." | SMS TP-UDL = 12 septets | IMAP literals `{310}` then 310 bytes |
| HTTP/1.1 headers CRLF CRLF | HTTP `Content-Length: 4096` | HTTP/1.1 CRLF headers + Content-Length |
| MIME `--=_boundary--` | SS7 MTP2 LI, SIF ≤ 273 | HTTP/2 binary framing over a stream |
| Redis CRLF between parts | Protobuf varint length prefix | POP3 +OK line then a dotted body |
| **+** cheap, readable, can stream without knowing size. **−** must escape delimiter (dot-stuffing) | **+** content can never be confused with protocol. **−** must know size before sending (why **chunked transfer encoding** exists) | **+** readable control, safe binary payload. **−** two parsers → **request smuggling** lives in the gap |

### FTP — "refuses to mix commands and data"
- **Control connection on port 21** (USER, PASS, LIST, RETR, PWD, PASV). **A brand-new data connection for every file/listing.**
- **Active mode (1971):** server connects **from port 20 back INTO the client** → every NAT/firewall now blocks this.
- **Passive mode (PASV):** server replies `227 Entering Passive Mode (h,h,h,h,p1,p2)`; **client opens both connections** — the only shape NAT allows. Now effectively mandatory.
- **Decode 227:** `(127,0,0,1,117,48)` → IP 127.0.0.1, **port = p1 × 256 + p2 = 117 × 256 + 48 = 30000** (big-endian pair = htons spelled out in ASCII; 1971 clients shouldn't parse numbers >255).
- Demo: pyftpdlib in podman, port 2121, passive range 30000–30009, `--nat-address` (container doesn't know its reachable address).

### What to keep (Session 2)
- **Encapsulation:** Ethernet⊃IP⊃TCP⊃HTTP = MTP2⊃MTP3⊃SCCP⊃TCAP⊃MAP⊃TPDU.
- **Framing:** SMS chose length, SMTP chose a dot, IMAP chose both.
- **Reliability has an address:** SS7 at L2 per hop; TCP at L4 end-to-end; QUIC in userspace.
- **Separate control & data:** SS7 killed blue boxes; SIP keeps media off the proxy; FTP opens a second socket.

Homework: draw UDP header from memory & diff with capture · TCP SYN cookies (1996) vs HTTP cookies — which first? · unpack "Hello World!" GSM-7 by hand · Asterisk SIP call + Wireshark RTP.

> **Quiz points — Session 2**
> - OSI 7 layers + examples. TCP vs UDP properties and users.
> - Ethernet = CSMA/CD (detect); Wi-Fi 802.11 = CSMA/CA (avoid; L2 ACK every frame; ~2 ms contention).
> - Sizes: MAC 6 B, EtherType 2 B (0x0800 IPv4), FCS 4 B CRC-32, MTU 1500, IP hdr 20, TCP hdr 20, UDP hdr 8, MSS 1460, wire frame 1518. IP proto 6 = TCP.
> - SS7 1975, out-of-band signalling, 64 kbps DS0, 2600 Hz blue box. Stack MTP1/2/3, SCCP, TCAP, MAP/ISUP.
> - SMS: 140 octets, 160 GSM-7 chars, 70 UCS-2 chars; SIF 272; SMSC store & forward; HLR lookup; mo-ForwardSM opcode 46.
> - ISUP: IAM, ACM, ANM, REL, RLC. SIP: INVITE, 100, 180, 200, ACK, BYE; media = RTP over UDP.
> - SS7 reliability per hop; TCP end to end.
> - BBR = bandwidth × RTT, not loss. Reno/CUBIC = loss-based sawtooth.
> - Handshake SYN/SYN-ACK/ACK; SYN & FIN consume a seq number; random ISN (RFC 6528, Mitnick).
> - SYN cookies: state in ISN; lose wscale/SACK/timestamps; enabled under pressure.
> - Close = 4 segments; CLOSE_WAIT = app forgot close(); TIME_WAIT = 2 MSL.
> - RTTs: TCP 1, +TLS1.2 3, +TLS1.3 2, QUIC 1. Mumbai–Virginia ~190 ms.
> - QUIC: UDP + userspace + per-stream sequence → no TCP HOL blocking.
> - SMTP ports 25/587/465; envelope vs header; lone dot; SPF/DKIM/DMARC. POP3 STAT/LIST/RETR/DELE (110/995); IMAP 143.
> - FTP 21 control, 20 active data; PASV 227 port = p1×256+p2.

---

# SESSION 3 — One Process, Many Clients: Scaling Servers

**One question: how does one box hold ten thousand clients at the same time?**
Blocks: (1) select/epoll, timeouts · (2) CGI/FastCGI · (3) Isn't everything a web server? · (4) Limits: ulimit & C10K, memory, context switches, queueing · (5) Apache, HAProxy, Varnish, nginx.

## 3.1 Multiplexing — three ways to serve many clients

| Fork per request | Thread per request | One loop, many sockets |
| --- | --- | --- |
| Whole process copied per client. Simple, isolated, most expensive per connection | Cheaper than fork; latency drops; but every thread still costs a stack before any work | select/epoll; one thread watches every socket, wakes only for ready ones. **The one that scales** |

**What actually ships:** pre-fork or pre-thread a **pool**, each worker runs its own select/epoll loop — **isolation from processes, concurrency from the loop**.

### fork() costs
A full process image per connection; page tables, fds, scheduler entry duplicated; paid while the user waits.

### The select() server — key details
- `listen(server_fd, 16)`; `int clients[FD_SETSIZE]`.
- Each iteration: `FD_ZERO`, `FD_SET(server_fd)`, `FD_SET` every client, track `maxfd` → `select(maxfd + 1, &readfds, NULL, NULL, NULL)`.
- If `FD_ISSET(server_fd)` → `accept` new client. For each client with `FD_ISSET`: read; if `n <= 0` close and **O(1) delete**: `clients[i] = clients[--nclients]; i--;` else echo.
- **The last NULL is the timeout** → NULL = block forever.

### select's ceiling: FD_SETSIZE = 1024
- `fd_set` is a **fixed-width bitmap — 1024 bits on glibc**; descriptor 1024 cannot be represented.
- **select = O(n) every call**: rebuild set each iteration; kernel scans every fd; 10,000 idle sockets cost the same as 10,000 busy ones.
- **epoll = O(ready)**: register each fd once with **`epoll_ctl`**; **`epoll_wait`** returns only what fired; idle connections cost nothing.
- Same idea elsewhere: **kqueue** (BSD/macOS), **IOCP** (Windows), **io_uring** (modern Linux).
- **The number to remember: 1024** — it's FD_SETSIZE, your default ulimit, and the K in C10K. "One wall, three names."

### In production you stack them
At startup fork/spawn a pool of workers (often **one per CPU core**) → each runs its own select/epoll loop → **SO_REUSEPORT** lets the kernel spread new connections across them → crash isolation + concurrency.
This is **Apache's event MPM, nginx's master-and-workers, and the Go runtime** (goroutines multiplexed onto OS threads by a scheduler on top of epoll).

### Timeouts — the client's half of the contract
select waits on three sets: **readfds** (new content arrived), **writefds** (socket allows writing), **exceptfds** (sockets being connected/closed/exceptions). Last arg = timeout. **NULL = block forever → one wedged client stops the whole loop.** Client side: set a deadline, then **retry with backoff**.

## 3.2 CGI / FastCGI — how the server runs your code

### CGI (Common Gateway Interface) — every request forks a new copy of your program
Apache → creates a CGI process with **envp** (env vars), **stdin pipe**, **stdout pipe**, **stderr → Apache error log**.
- Server side: set child's stdin/stdout/stderr to pipes it controls, then exec. Client request body → stdin; stdout → client; stderr → error log.
- Real code: **apache/httpd `modules/generators/mod_cgi.c` L576 `run_cgi_child()`** — creates child, attaches 3 pipes, **timeout on each** so a hung script can't hold the worker forever.
- **HTTP headers become environment variables**: `REQUEST_METHOD=GET/POST`, `QUERY_STRING=<after ?>`; header `User-Agent: curl` → **`HTTP_USER_AGENT=curl`** (upper-case, dashes→underscores, prefix `HTTP_`). Also GATEWAY_INTERFACE, SERVER_PROTOCOL. Code: `server/util_script.c` L409 **`ap_add_cgi_vars()`**; `ap_add_common_vars()` does the rest.
- **The CGI program just prints:** read REQUEST_METHOD; POST → read stdin; GET → parse QUERY_STRING; print `Content-Type: text/html`, **blank line** (the delimiter), body. Any language that reads env vars and prints can serve HTTP → early web in Perl and shell.
- **Cost:** whole program image created, run once, discarded — per hit.

### Fixes
1. **Compile the module into the server: mod_php, mod_perl** — no new process, but app shares address space with the web server → **one segfault takes both down**.
2. **FastCGI (the fix that won)** — keep a **long-lived process** (pool) and talk to it over a **Unix or TCP socket** with a reduced vocabulary.
- The move: **take setup cost off the request path, pay it once at startup** (same as pre-forking).

### FastCGI architecture
Clients (thousands, many slow) → **nginx/httpd** (user-facing: absorbs slow connections, TLS, buffering) → FastCGI → **php-fpm** (fixed pool of long-lived workers). You define an **upstream**.
- "A modified HTTP with less vocabulary" — same info (method, headers, query, body) but **binary, typed, multiplexed**.

### FastCGI record stream
Request: `FCGI_BEGIN_REQUEST` → `FCGI_PARAMS` (REQUEST_METHOD=POST, SCRIPT_FILENAME=/var/www/test.php, QUERY_STRING=x=10, CONTENT_TYPE, CONTENT_LENGTH=17, HTTP_HOST, HTTP_USER_AGENT) → **empty FCGI_PARAMS = params finished** → `FCGI_STDIN` (`name=alice&age=20` = 17 bytes) → **empty FCGI_STDIN = stdin finished**.
Response: `FCGI_STDOUT` (headers, blank line, body) → empty STDOUT → `FCGI_STDERR` (goes to log; separate record type so debug output can't corrupt the page) → `FCGI_END_REQUEST`.
**Framing: FastCGI uses BOTH** — every record header carries its **content length**, and an **empty (length-0) record is the delimiter** for "stream finished".

### Servlets — the same idea in a JVM
Jetty/Tomcat **are** the web server; JVM already running your code; **pre-threading** (thread pool at startup); isolation by **class loader and thread, not process** → cheaper than fork but a runaway servlet can hurt neighbours.
"CGI, FastCGI, servlets, and every modern framework answer one question: how do we run user code per request without creating the world each time?"

## 3.3 Isn't everything a web server?

| Speaks HTTP | Doesn't (own protocol) |
| --- | --- |
| Wi-Fi router admin page, agent runtimes/cloud tooling, most Node apps, Firestore, CouchDB (REST), Kafka with REST proxy | **Redis (RESP)**, **MySQL (binary wire protocol)**, **MQTT brokers (IoT)**, messenger backends (WhatsApp-like), **Kafka natively (binary)** |

- **HTTP is stateless** → any box can answer any request; you can close connections when you like; LB can send the next request anywhere → **horizontal scaling is "free-ish"**.
- **A database wants to stay connected** (TCP connect + handshake + auth + session setup is expensive) → the question becomes **how many persistent connections can one box hold**, not requests/sec.

## 3.4 Four walls (limits)
1. **File descriptors** — a connection is a descriptor; default **1024**.
2. **Memory** — a stack per thread, a buffer per connection, paid before work.
3. **Context switches** — every read/write/syscall crosses the kernel boundary.
4. **The queue** — latency and throughput aren't independent; being slow costs memory.

### C10K → C10M
- **1999 C10K** — **Dan Kegel**: can one box hold **10,000** simultaneous connections? Then: no.
- **2013 C10M** — **Robert Graham**: the kernel is the problem; bypass it → **10,000,000**.
- **Today** — **2–3 million** connections demonstrated on one server. Default `ulimit -n` still **1024**.

### Memory per thread
- **OS thread: 8 MB default stack** reserved up front → 10,000 threads ≈ **80 GB** of address space.
- **Goroutine: 2 KB initial stack**, grown on demand — **4000× smaller**. Go runtime multiplexes goroutines onto few OS threads via a **netpoller built on epoll** (you write blocking reads; runtime parks you on a poll).

### Kernel boundary tax
- User→kernel→user: save state, switch page tables, validate, copy, return — **hundreds of ns each**; **Spectre/Meltdown mitigations made it worse**.
- **Bypass the kernel:** user-space TCP — **DPDK, netmap, mTCP, Seastar** (lose all your tools, get the packets).
- **Make fewer calls:** **`sendfile()`** moves file → socket without a user-space copy; **`io_uring`** submits batches via a shared ring.

### Little's Law — concurrency = throughput × latency
**connections in flight = requests per second × seconds per request.**
At 10,000 req/s: 100 ms latency → **1,000** connections; 1 s → **10,000** — same traffic. **"Slowness is a memory bug"** → take high-latency work off the request path (async).

## 3.5 What our favourite software does

### Apache: prefork → worker → event (MPM = Multi-Processing Module)
| Prefork | Worker | Event |
| --- | --- | --- |
| Pool of processes, 1 connection each. Bulletproof; works with non-thread-safe modules; most expensive | Processes each running many threads; cheaper; but a thread is **pinned to a connection even while idle on keep-alive** | **Listener thread per process parks idle keep-alive sockets on epoll**, hands workers only sockets with work. **Default on Unix today** (arrived ~2012) |

### HAProxy (2001)
- Arrived **2001**; **epoll landed in Linux 2.5.44 in late 2002** → HAProxy was largely **select** at first; moved to epoll later; **multi-threaded only since 1.8 (2017)**.
- **Introduced the load balancer as a tier** — sits in front of app servers, chooses between them, switches between upstreams.
- Single event-driven process saturated a NIC.
- **Absorbs connection churn** — holds a pool of persistent connections to upstreams.

### Varnish (2006) — first popular caching reverse proxy
- **Squid** cached for the client (forward proxy, near users, way out). **Varnish put the cache in front of the origin** (way in) — same mechanism, opposite direction.
- Acceptor thread per listening point per pool; **worker thread per active connection**, pools default **min 100, max 5000**; idle descriptors handed to a **waiter (epoll on Linux, kqueue on BSD)** → threads for work, a loop for waiting.
- **Fastly's edge is built on Varnish & VCL** (VCL in 2026 = configuring a 2006 program).

### nginx (2004) — epoll + sendfile
- `read()`+`write()` = disk→kernel→your buffer→kernel→socket. **`sendfile(sock, file, NULL, n)` = kernel → socket; you never touch the bytes (zero-copy).**
- **One master + one worker process per CPU core**; each worker = single thread, one epoll loop over thousands of connections.
- First a reverse proxy, then "abused" for caching, load balancing, TLS termination, rate limiting → the default shape of an edge.
- **Thread pool since 1.7.11** for disk reads — a page fault on a cache miss would stall every connection on that worker.

### Side by side
| Server | Concurrency model | Born | Idea it popularised | In the wild |
| --- | --- | --- | --- | --- |
| Apache | prefork→worker→event (listener + epoll) | 1995 | Modules; CGI to run anyone's code | Everywhere; Akamai started here |
| HAProxy | select then epoll; MT since 1.8 | 2001 | Load balancer as its own tier | Default LB in front of everything |
| Varnish | thread per active conn + epoll waiter | 2006 | Caching reverse proxy / HTTP accelerator | Fastly's edge, VCL |
| nginx | master + worker per core, one epoll loop each | 2004 | sendfile: never copy bytes to user space; answer to C10K | Default edge; Broadpeak, most CDNs |

All four ended up with **an event loop + a small pool of workers**.

### Code to read
mod_cgi.c `run_cgi_child()`; util_script.c `ap_add_cgi_vars()`; nginx `ngx_epoll_module.c`, `ngx_linux_sendfile_chain.c`; haproxy `src/ev_epoll.c` (ev_select.c beside it); varnish `cache_waiter_epoll.c`; Go `runtime/netpoll_epoll.go`.

Homework: open 1,100 connections to the select server and see it die, rewrite with epoll for 100,000 · watch CGI processes spawn with ps/top · tcpdump nginx↔php-fpm for FCGI_BEGIN_REQUEST · measure Little's Law with `ss -s`.

### The four ideas
1. **Amortise the setup** (pre-fork, pre-thread, FastCGI, pools, servlets).
2. **Nothing is free per connection** (descriptor, stack, buffer, scheduler entry × 10,000).
3. **Framing is still length or delimiter** (FastCGI: length in record + empty record).
4. **Concurrency = throughput × latency** — only getting faster reduces what you hold.

> **Quiz points — Session 3**
> - fork vs thread vs event loop; production = pre-fork pool + loop per worker + SO_REUSEPORT.
> - FD_SETSIZE = 1024 bitmap; select O(n), epoll O(ready) (epoll_ctl / epoll_wait); kqueue, IOCP, io_uring.
> - select args: nfds = maxfd+1, readfds, writefds, exceptfds, timeout (NULL = forever).
> - CGI: fork+exec per request, env vars (REQUEST_METHOD, QUERY_STRING, HTTP_USER_AGENT), stdin/stdout/stderr pipes.
> - mod_php/mod_perl: in-process, a segfault kills the server. FastCGI: persistent pool (php-fpm) over socket; binary records; empty record = end of stream.
> - Servlets: Tomcat/Jetty, pre-threaded, class-loader isolation.
> - HTTP stateless → horizontal scaling; DBs (Redis RESP, MySQL, Kafka, MQTT) want persistent connections.
> - C10K Dan Kegel 1999; C10M Robert Graham 2013; 2–3M today.
> - Thread stack 8 MB vs goroutine 2 KB. 10k threads ≈ 80 GB.
> - Kernel bypass: DPDK, netmap, mTCP, Seastar. sendfile = zero copy. io_uring = batched syscalls.
> - Little's Law: in-flight = RPS × latency.
> - Apache prefork/worker/event; HAProxy 2001, select first, epoll in Linux 2.5.44 (2002), MT in 1.8 (2017); Varnish 2006, Fastly; nginx 2004, master + worker per core, sendfile, thread pool since 1.7.11.

---

# SESSION 4 — nginx and the Code That Explains It

Four parts: (1) History, compressed · (2) What nginx changed · (3) Features you configure · (4) Walkthrough of the source (nginx 1.31.5; companion repo *nginx-from-scratch*, tour file NGINX-TOUR.md).

"Remember the evolution, you can forget the dates." Every design was someone's answer to a constraint that may no longer exist — knowing which constraint tells a **law** from a **habit**.

## 4.1 History — the correction worth making
**Myth:** "Berners-Lee wrote the first server, called Mosaic; Mosaic became Apache."
**Reality:** three separate programs:
- **CERN httpd** — Berners-Lee, on a **NeXT**, **1990** — the first web server.
- **NCSA Mosaic (1993)** — a **browser** (Andreessen's), inline images, web goes mainstream.
- **NCSA HTTPd (1993)** — **Rob McCool**; a server — **invents CGI**.
- **1994** McCool leaves → development stalls → webmasters trade patches by mail.
- **1995 Apache** — that patch set continued as a project: **"a patchy server"**.
- **1996** Apache passes NCSA HTTPd → **#1 for twenty years**.
- 1996–99: IIS fights for single-digit share; lighttpd and friends arrive.

### Apache spent a decade trying to outrun fork()
| Apache 1.3 — **prefork** | Apache 2.0 — **worker MPM** | Apache 2.4 — **event MPM** |
| --- | --- | --- |
| Pool of processes forked **at startup** instead of per request; setup cost off request path; one process still parks on one connection | Processes running many threads; 8 MB shared + a stack each; 1999–2002 Linux pthreads new & buggy ("reentrant") | Listener thread parks idle keep-alives on epoll; hands a worker a connection only when it has work. **Default on Unix since 2.4** |

"Three architectures, one question: how do I make the per-connection worker cheaper? None of them was a different question."

### Java's answer: stop creating things
- **J2EE (1999)** — multi-layer app server: web tier, **EJB** tier, database.
- CGI 1993 per request: fork + exec + load interpreter + parse script + run + exit.
- **Servlet 1997**: at startup load class, instantiate once; per request `service(req, res)` = a method call. "The object outlives the request — that is the trick."
- **Connection pools** do the same for the DB handshake. Same move as prefork and FastCGI.

### 2002: the numbers
**10,000** concurrent connections (C10K, Dan Kegel 1999) · **8 MB** stack per thread → 10k threads = **80 GB** address space · **1024** = FD_SETSIZE, hard-coded; **ulimit doesn't move it**. "Everyone is optimising the worker. Somebody is about to delete it."

## 4.2 What nginx changed
- **Igor Sysoev, Rambler (2002)** — Rambler (big Russian portal) Apache servers falling over under **connection volume, not request volume**.
- Started nginx **2002** to solve C10K. **First public release 4 October 2004** (anniversary of **Sputnik**). **1.0.0 only in April 2011**.
- Goal: serve 10k **mostly-idle** connections from one process and let something else generate dynamic content → **that's why nginx is a reverse proxy, not an app server**.
- **Apache asked "how do I make the worker cheaper?" nginx asked "why is there a worker per connection at all?"** A connection needs a few hundred bytes of state and a place in a list until it has something to say.

### Process model — one process per core + a master that never touches a connection
- **master**: binds :80, reads config, forks, handles signals. Nothing else.
- **worker 0..N**: one event loop each.
- **cache manager** (evicts LRU) and **cache loader** (warms the index).
- `ps -o pid,ppid,args -C nginx` → master (ppid 1), workers, cache manager. **Count doesn't change under load** (vs fork server, where it grows).
- Code: `ngx_process_cycle.c` `ngx_master_process_cycle()`, `ngx_start_worker_processes()`; `ngx_process.c` `ngx_spawn_process()`.

### All of nginx in six lines — `ngx_process_events_and_timers()` (src/event/ngx_event.c)
```c
timer = ngx_event_find_timer();
ngx_process_events(cycle, timer, flags);      /* epoll_wait() — 99.9% of life asleep here */
ngx_event_process_posted(cycle, &ngx_posted_accept_events);
ngx_shmtx_unlock(&ngx_accept_mutex);
ngx_event_expire_timers();
ngx_event_process_posted(cycle, &ngx_posted_events);
```
- **The timer is an argument to the sleep** → nginx never polls for timeouts.
- Handlers don't run inside the poll; they're **posted** and drained after.

### Load balancing between workers — one line
```c
ngx_accept_disabled = ngx_cycle->connection_n / 8 - ngx_cycle->free_connection_n;
```
"Once I'm using more than **7/8** of my connection slots, stop competing for new connections; let siblings take them." No coordinator, no shared counter — each worker decides alone.
- **accept_mutex**: **default off since 1.11.3**. The **thundering herd** (all workers woken for one connection) was real in 2004; now **EPOLLEXCLUSIVE (Linux 4.5+)** and **SO_REUSEPORT** let the kernel fan out.

### select vs epoll — "O(watched) vs O(active)"
| | select() | epoll() |
| --- | --- | --- |
| Watch list lives | In your process, rebuilt every call | **In the kernel**, edited via `epoll_ctl()` |
| Cost per iteration | O(n) build + O(n) kernel + O(n) scan | O(ready events) |
| 10,000 idle, 10 active | **30,000** units of work to find 10 | **10** |
| Ceiling | FD_SETSIZE 1024 (compile-time) | `ulimit -n` |
| What `ulimit -n` does | **Nothing** (limit is a bitmap width) | Everything |
| Portable | Everywhere since 1983 | Linux only (kqueue on BSD) |
"Everything is downstream of one decision: who owns the watch list."

### The stale-event bug (every event-loop author writes it once)
- `epoll_wait` returns a **batch**. Handling event 1 may close the connection event 7 points at; a new client on the **recycled fd** gets event 7.
- nginx fix: structs are aligned so the **low bit of the pointer is always 0** → used as an **"instance" generation flag**, flipped on reuse. `if (c->fd == -1 || rev->instance != instance) continue;` Free bit, no memory, one branch. (Repo's epolld.c uses an explicit generation counter.)

### sendfile — four copies become two
- **read()+write(): 4 copies, 2 mode switches per chunk**: disk → page cache → your buffer → socket buffer → NIC.
- **sendfile(): 2 copies (both DMA), 0 mode switches per chunk**: disk → page cache → socket buffer → NIC. Data never enters your process.
- **Limit:** if you must **touch the bytes (gzip, TLS, templating)** they must come to user space → **`gzip on` and `sendfile on` fight**; this is why **kTLS** (kernel TLS) exists.
- **Honest benchmark** (64 MB over loopback): read 37.4 ms / 2048 syscalls; mmap 23.3 ms / 4; sendfile 33.2 ms / **1 syscall**. On loopback there's no NIC/DMA; memory-bandwidth bound → wall-clock roughly the same. **Real win = 2048 syscalls → 1 and headroom under concurrency** (CPU not spent copying serves someone else). "A benchmark that doesn't model the bottleneck measures the wrong thing."

### Why "reverse" proxy? Because "proxy" was taken
| Forward proxy (Squid, 1996) | Reverse proxy (nginx) |
| --- | --- |
| Sits next to the **clients**; caches for campus users; protects your uplink | Sits next to the **servers**; caching + route by path/host + distribute across upstreams (weights, least-conn) + fallback + **TLS termination** + hold 10k slow clients |
| client → [proxy] → internet | internet → [nginx] → app servers |
- Client doesn't configure (and usually can't see) a reverse proxy.
- **Killer feature nobody lists: it absorbs slow clients** — your app never talks to a phone on 2G.

## 4.3 Features you configure

### The cache — two structures, one on disk
```
proxy_cache_path temp/cache levels=1:2 keys_zone=demo:10m max_size=100m inactive=60s use_temp_path=off;
```
| Directive | Meaning |
| --- | --- |
| `keys_zone=demo:10m` | **10 MB shared memory** holding the **rbtree + LRU queue** — the **index, not the data**. **~8,000 keys per MB** |
| `levels=1:2` | Two directory levels on disk so no directory holds a million files |
| `max_size=100m` | Disk ceiling; **cache manager evicts from LRU tail** |
| `inactive=60s` | Evicted if **not READ** for 60 s **regardless of TTL** |
- **`proxy_cache_valid`** = how long a response is **fresh** (TTL). **`inactive`** = how long an unread item **stays on disk**. Class question: valid=10s, inactive=60s → content is fresh for 10 s (then revalidated/stale), but kept on disk up to 60 s since last access; if unread for 60 s it's deleted even if still "valid".

### The LRU eviction (ngx_http_file_cache_expire)
Take the tail (`ngx_queue_last`); if `fcn->expire - now > 0` (still fresh) stop; if **`fcn->count == 0`** (nobody streaming it) delete. `count == 0` is why an object being streamed can't be evicted from under a client. `src/core/ngx_queue.h` — ~50 lines of macros, **intrusive doubly-linked list**.

### Two lines that save you at 3 a.m.
- **`proxy_cache_lock on;`** — **anti-stampede (cache stampede / thundering herd)**: when a popular object expires, only **one** request goes to origin; others wait. **Off by default.**
- **`proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;`** — **serve stale rather than fail** when origin is down. `updating` = one request refreshes while everyone else gets stale instantly (stale-while-revalidate).
- Always add **`add_header X-Cache-Status $upstream_cache_status;`** → see MISS / HIT.

### location precedence — not file order

| # | Form | Rule | Example → winner |
| --- | --- | --- | --- |
| 1 | `location = /exact` | **Exact match; wins immediately**, search stops | /exact → 1 |
| 2 | `location ^~ /images/` | Longest prefix **and suppresses regex search** | /images/a.php → **2** (not the regex!) |
| 3 | `location ~ \.php$` | Regex — **FIRST match in file order, not longest** (`~*` = case-insensitive) | /other/a.php → 3 |
| 4 | `location /` | Longest prefix, used **only if no regex matched** | /anything → 4 |

- Algorithm: exact → longest prefix (remember it; if `^~` stop) → regexes in order (first match wins) → else the remembered longest prefix.
- Half the room gets /images/a.php wrong.
- **nginx has no .htaccess** — deliberately, so it doesn't `stat()` up the directory tree every request.
- **Why 500 prefixes are free and 500 regexes aren't:** prefixes are a **ternary search tree** built at config-parse time, walked per URI segment; regexes are a **plain array walked in order every request**. "The data structure is the documentation" → tree ⇒ longest wins; array ⇒ first wins.

### Smooth weighted round robin
```c
peer->current_weight += peer->effective_weight; total += peer->effective_weight;
if (peer->effective_weight < peer->weight) peer->effective_weight++;  /* passive health check recovery */
if (best == NULL || peer->current_weight > best->current_weight) best = peer;
best->current_weight -= total;
```
- Weights 3:1 — naive WRR: `a a a b` (bursts); **nginx smooth: `a b a a`** — same ratio, no bursts at origin.
- Measured: 24 requests → 6 to :8001, 18 to :8004 = exactly 3:1.
- Other algorithm mentioned: **least_conn** (homework: with a slow upstream, compare p99 of round robin vs least_conn).

### Fallbacks — try_files
```nginx
location / { try_files $uri $uri/ /index.html?$args; }
location /maybe/ { try_files $uri @app; }
location @app { proxy_pass http://app; }
```
- "Is this a real file? A real directory? No? Hand the URI to the app." **The last entry is never tested — it's the fallback, not a candidate.**
- **Named location (`@app`)**: reachable only from try_files or error_page, never from a URL.
- WordPress, Rails, Django, every SPA router = this directive + an app that reads REQUEST_URI.

## 4.4 Walkthrough of the source
- "Line numbers drift; function names don't." nginx puts the return type on its own line → **`grep -rn "^ngx_epoll_process_events" src/`** finds the definition only.

### The tree
| Dir | Contents |
| --- | --- |
| `src/core/` | nginx's own stdlib: string, array, list, hash, rbtree, queue, palloc, buf, conf, cycle, connection |
| `src/event/` | The loop; `modules/` = six ways to wait: **epoll, kqueue, select, poll, devpoll, eventport** (chosen at ./configure) |
| `src/http/` | HTTP state machine, phase engine, upstream framework; `modules/` = every directive |
| `src/os/unix/` | Syscall layer: sendfile per OS, spawning, shm, atomics |
| `src/stream/` | Same architecture for raw TCP/UDP — **nginx as L4 load balancer** |
| `src/mail/` | Again, for **IMAP, POP3, SMTP proxying** |

### Two files to read first
- **`ngx_queue.h`** — intrusive doubly-linked list (link pointers inside the node; no allocation; link→data by pointer subtraction). Used by cache LRU, posted-event queues.
- **`ngx_palloc.h`** — **memory pool**: allocate from a pool attached to the request, **destroy the whole pool at the end**. No refcounting, no leak class, no free() on the hot path.

### Ten stops
| What | File | Function |
| --- | --- | --- |
| Process model | os/unix/ngx_process_cycle.c | ngx_start_worker_processes |
| The loop | event/ngx_event.c | ngx_process_events_and_timers |
| Accept + herd | event/ngx_event_accept.c | ngx_event_accept |
| epoll + stale events | event/modules/ngx_epoll_module.c | ngx_epoll_process_events |
| Parser | http/ngx_http_parse.c | ngx_http_parse_request_line |
| Phases | http/ngx_http_core_module.c | ngx_http_core_run_phases |
| Routing | http/ngx_http_core_module.c | ngx_http_core_find_static_location |
| sendfile | os/unix/ngx_linux_sendfile_chain.c | ngx_linux_sendfile |
| Cache LRU | http/ngx_http_file_cache.c | ngx_http_file_cache_expire |
| FastCGI records | http/modules/ngx_http_fastcgi_module.c | ngx_http_fastcgi_process_record |

### The HTTP parser is a resumable state machine
- **27 states for the request line alone** (sw_start, sw_method, sw_spaces_before_uri, sw_schema, … sw_http_H, sw_http_HT…).
- No regex, no strtok, no allocation; **one byte at a time; can stop between any two bytes**; `state = r->state` resumes where it stopped (request line may arrive in 3 TCP segments).
- "This is what non-blocking costs you: every parser must be resumable."

### 11 phases — and `return` means "suspended"
**POST_READ → SERVER_REWRITE → FIND_CONFIG → REWRITE → POST_REWRITE → PREACCESS → ACCESS → POST_ACCESS → PRECONTENT → CONTENT → LOG**
```c
while (ph[r->phase_handler].checker) {
    rc = ph[r->phase_handler].checker(r, &ph[r->phase_handler]);
    if (rc == NGX_OK) return;   /* NOT done. SUSPENDED. */
}
```
A hand-rolled **coroutine** in C; request resumes at the phase it left when its event fires.
Which module runs when: **limit_req → PREACCESS · auth_basic → ACCESS · try_files → PRECONTENT · proxy_pass, fastcgi_pass, static → CONTENT.**

### FastCGI wire format
- **8-byte record header: version · type · requestId (2) · contentLength (2) · paddingLength · reserved** → contentData → padding.
- BEGIN_REQUEST header: `01 01 00 01 00 08 00 00` (version 1, type 1, request 1, length 8) — first 8 bytes of every FastCGI connection.
- Empty PARAMS: `01 04 00 01 00 00 00 00` (type 4, length 0) = end of params. **Empty record = delimiter**; forget it and the responder waits forever. Length + delimiter "at two levels".

### The ladder (companion repo, ~1,200 lines vs nginx's 200,000 — the difference is error paths)
| Dir | Model | Historical match | What you see |
| --- | --- | --- | --- |
| 01-fork | fork per client | Apache 1.3, 1995 | ps shows a process per request |
| 02-thread | pthread per client | Apache 2.0 worker, 1999 | prints its 8 MB stack |
| 03-select | one thread, select | …and the 1024 wall | dies at fd 1024; ulimit doesn't help |
| 04-epoll | one thread, epoll | nginx 2004 | 5,000 connections, nothing happens |
| 05-sendfile | read vs mmap vs sendfile | — | 2048 syscalls → 1 |
| 06-fastcgi | wire protocol both ends | CGI without the fork | nginx → your 200-line responder |
| 07-nginx | one nginx.conf, five demos | — | routing (:8081), cache & weights (:8082), fallbacks (:8084) |

### Four ideas to leave with
1. **Ask the other question** — Apache made the worker cheaper; nginx asked why there was one.
2. **Check whether the constraint still exists** — thread-per-connection died at 8 MB + context switch; **goroutines and virtual threads** brought it back.
3. **The data structure is the documentation** — prefixes = tree → longest wins; regexes = array → first wins.
4. **Amortise the setup** — prefork, pre-thread, servlets, connection pools, FastCGI, **upstream keepalive**: six names, one move.

Next: "Where did all the state go?" — sessions, sticky routing, TLS termination, shared caches.

> **Quiz points — Session 4**
> - First server CERN httpd (Berners-Lee, NeXT, 1990). Mosaic = browser (1993). NCSA HTTPd (Rob McCool, 1993) invented CGI. Apache 1995 "a patchy server", #1 from 1996.
> - Apache 1.3 prefork, 2.0 worker, 2.4 event (default). J2EE 1999, servlets 1997.
> - nginx: Igor Sysoev, Rambler, started 2002, released 4 Oct 2004 (Sputnik), 1.0 in April 2011.
> - Master (bind, config, fork, signals) + one worker per core + cache manager + cache loader.
> - accept_disabled = connections/8 − free (7/8 rule). accept_mutex off since 1.11.3; EPOLLEXCLUSIVE (Linux 4.5), SO_REUSEPORT.
> - Stale events fixed with pointer low-bit "instance" flag.
> - sendfile: 4 copies/2 mode switches → 2 DMA copies/0 switches; conflicts with gzip; kTLS.
> - Forward proxy (Squid, near clients) vs reverse proxy (near servers); absorbs slow clients.
> - keys_zone = index in shared mem (~8k keys/MB); inactive = unread eviction; proxy_cache_valid = freshness; proxy_cache_lock = anti-stampede (off by default); use_stale = serve stale on errors; X-Cache-Status.
> - location order: `=` exact → `^~` prefix → regex `~` first match → longest prefix. No .htaccess.
> - Smooth WRR 3:1 → a b a a.
> - try_files last arg is the fallback, never tested; `@named` locations.
> - Parser = resumable state machine (27 states). 11 phases; NGX_OK return = suspended. ngx_palloc memory pools.
> - FastCGI 8-byte header; empty record ends a stream.

---

# SESSION 5 — Evolution of HTTP: 1996 → Now

"Same words. Three completely different ways of writing them down." **The protocol did not drift — it was pushed.**

| Hour | Version | RFC | Ends on (its wall) |
| --- | --- | --- | --- |
| 1 | HTTP/1.0 | **RFC 1945 · May 1996** | One response per connection |
| 2 | Early HTTP/1.1 | **RFC 2068 · Jan 1997** | "At most 2 connections" |
| 3 | HTTP/1.1 now | **RFC 2616 (Jun 1999) → 7230–7235 (Jun 2014) → 9110–9112 (Jun 2022)** | Head-of-line blocking |
| 4 | HTTP/2 | **RFC 7540 (May 2015) → 9113 (Jun 2022)**; HPACK RFC 7541 | TCP head-of-line blocking |
| 5 | QUIC + HTTP/3 | **RFC 9000 (QUIC) · RFC 9114 (HTTP/3)**; RFC 9001 (QUIC-TLS); QPACK RFC 9204 | The 3–5% who block UDP |

**Assignment (due before Session 7):** a calculator HTTP/1.1 server on a raw socket that **stays on the line**: `GET /add?a=2&b=3 → 200 5`, `/div?a=1&b=0 → 400`, `a=x → 400`, `/pow → 404`, `POST /add → 405`, missing Host → 400. Marked with **one socket for all requests** ("If the socket dies before I'm done, you've written a 1996 server"). Hard part: **where does one request end and the next begin** → consume exactly Content-Length bytes; byte n+1 belongs to the next request. Stretch: Connection: close, idle timeout, chunked, pipelining.
**Course project:** design **HTTP in binary** (server `bserve` + client `bcurl`): fixed-size frame header (HTTP/2 chose **24/8/8/31**), number your ten common header names + length-prefix the rest (HPACK's first two mechanisms), and **a receiver meeting an unknown frame type MUST skip it** (room for v2). Deliver: 2-page spec, program, annotated hexdump.

## 5.1 HTTP/1.0 (RFC 1945, May 1996) — the whole protocol on one slide
- **Methods:** GET, HEAD, POST (+ PUT, DELETE, LINK, UNLINK in Appendix D "additional methods").
- **Status codes:** 200, 201, 202, 204, 300, 301, 302 (Moved Temporarily), 304, 400, 401, 403, 404, 500, 501, 502, 503. **Today 62 assigned (IANA, Sep 2025).**
- **16 headers:** Allow, Authorization, Content-Encoding, Content-Length, Content-Type, Date, Expires, From, If-Modified-Since, Last-Modified, Location, Pragma, Referer, Server, User-Agent, WWW-Authenticate.
- Hand-speak: `printf 'GET / HTTP/1.0\r\n\r\n' | nc localhost 8010` → response, blank line delimiter, body, **server closes (FIN)**. (curl adds 4 headers you didn't write and hides 2 the server sent.)

### HTTP/1.0 limitations
1. **One response, then the socket dies.** RFC 1945 §1.3: connection established by the client before each request and closed by the server after. Second request on same socket → `b''` (empty read, not an error).
   - **24-object page at 200 ms RTT: 24 handshakes (4.8 s) + 24 req/resp (4.8 s) = 9.6 s** — plus 24 congestion windows each starting from nothing (slow start).
2. **No Host header → one IP = one website.** `Host: site-b` ignored → serves site-a. Until Jan 1997 the ratio was 1:1; today ~1.1 B websites vs IPv4. The fix (Host) = "the highest-leverage line in the standard".
3. **Caching with a clock as the fingerprint:** `Last-Modified` + `If-Modified-Since` → **304 Not Modified** (202,000 → 0 bytes). Problems with timestamps: **no sub-second field** (two writes in one second look like one), **clock drift** between you/me/proxy, **mtime is not identity** (a rebuild changes every mtime but no bytes). Also `Expires`.
4. **Only 16 headers / 3 methods** — no OPTIONS (can't ask what a server supports).

| Limitation | Concretely | Fixed in |
| --- | --- | --- |
| Not persistent | One request per handshake | RFC 2068 §8.1 |
| 16 headers, 3 methods | No OPTIONS | RFC 2068 §9.2 |
| Thin caching | A clock, not a fingerprint | RFC 2068 §14.19 (ETag) |
| No Host | One IP per site | RFC 2068 §14.23 |

**Correction:** HTTP/1.0 doesn't really have *head-of-line blocking* — HOL needs a queue and 1.0 has no pipelining. It has a **serialisation cost** (one RTT per object). Real HOL arrives in HTTP/1.1 as a side-effect of the fix. "Every solution today is the cause of the next slide."

## 5.2 Early HTTP/1.1 (RFC 2068, Jan 1997)

### Persistence becomes the default
- 1.0: `Connection: keep-alive` was a non-standard extension (some honoured, some ignored, some crashed). **Default = hang up.**
- 1.1: "persistent connections are the default" — you opt out with **`Connection: close`**. **Default = stay.** Demo: 3 responses, one TCP handshake.

### Host header (§14.23) — one IP, a thousand sites (virtual hosting)
No Host in 1.1 → **400 Bad Request** (it's a MUST). Same IP/port/socket, different sites.
**The same move at four layers:**
| Layer | Problem | Fix |
| --- | --- | --- |
| HTTP/1.0 | 4-tuple was the address | `Host:` — put the name in the message |
| TLS | Host is encrypted; cert must be chosen first | **SNI** in the ClientHello, in the clear |
| HTTP/2 | Headers compressed & unordered | **`:authority`** pseudo-header |
| Elsewhere | Many destinations, one connection | Topic, routing key, ingress host rule |

### ETag (§14.19) — a fingerprint, not a clock
- `ETag: "55274ac22c651b90"` (e.g., sha256 of bytes, first 16 hex). `If-None-Match: "<etag>"` → **304 Not Modified** (202,000 → 0 bytes of body).
- **Weak validator `W/"…"`** = equivalent, not identical. **Range requests need a strong one.**
- **`If-Match`** = same idea for writes → **optimistic concurrency**, fix for **lost updates**.

### Accept-* and Vary
- `Accept-Encoding: identity` → 202,000 B; `gzip` → 5,763 B (**2.8%**); deflate 5,751 B.
- **"HTTP/1.1 is slow because it's text" is undercut: text compresses.** The body was never the problem — **headers were** (Content-Encoding compresses only the body).
- **`Vary` is a cache-key instruction**: "this URL has more than one answer; here's what it depends on". `Vary: Accept-Encoding` = correct; **`Vary: User-Agent` = millions of keys, hit rate → 0**; `Vary: *` = caching off.

### Range (§14.35) — "the header that runs your data lake"
- `Range: bytes=100-199` → **206 Partial Content**, `Content-Range: bytes 100-199/202000`, Content-Length 100.
- `Range: bytes=-50` → last 50 bytes (size not needed) → `bytes 201950-201999/202000`.
- `Range: bytes=999999-` → **416 Range Not Satisfiable**, `Content-Range: bytes */202000`. (416 added in RFC 2616, not 2068.)
- Used by: **video scrubbing**, **resumable downloads**, **Parquet/ZIP footers** (directory at the END — read last few KB, then only the needed columns).

### Chunked transfer encoding (§3.6.1) — body without knowing its length
```
Transfer-Encoding: chunked        (and NO Content-Length)

37                                 ← hex length: 0x37 = 55 bytes
body{font-family:monospace;...}
0                                  ← empty chunk ends the body
```
**Both length and delimiter, nested** — each chunk length-prefixed; sequence delimited by an empty chunk = **FastCGI's record structure**. Underpins streaming JSON, **server-sent events**, **gRPC trailers**.

### Everything else that arrived in 1.1
| Arrival | Purpose | Where you meet it |
| --- | --- | --- |
| **OPTIONS** | Ask what a server supports | **Every CORS preflight** |
| PUT · DELETE | Write / remove | REST APIs |
| **TRACE** | Echo request back incl. proxies | **Disabled everywhere — Cross-Site Tracing (XST), 2003** |
| **Via** | Each proxy appends itself | Debugging which box lies |
| **Expect: 100-continue** | Ask before uploading 4 GB | curl's 1-second pause on big PUTs |
| **Cache-Control** | Vocabulary instead of one timestamp | `max-age`, `s-maxage` (shared caches), `no-cache` ≠ `no-store` |
| ~40 status codes | 303, 405, 409, 410, 412, 413, 415, 504… | **504 already in RFC 2068** (whole 5xx family in 1997) |

**`no-cache` = revalidate before use. `no-store` = don't write it down at all.** "Everybody gets this wrong exactly once."

### "SHOULD NOT maintain more than 2 connections" (§8.1.4)
6 assets at 150 ms RTT:
| Mode | Round trips | TCP conns | Wall ms |
| --- | --- | --- | --- |
| close (HTTP/1.0) | 12 | 6 | 1369 |
| keepalive (1 conn) | 7 | 1 | 985 |
| parallel2 (RFC says) | 4 | 2 | 607 |
| parallel6 (browsers) | 2 | 6 | 608 |
| **pipelined (1 batch)** | 2 | 1 | **304** |
- Browsers shipped **6 connections per origin** by ~2008; **18 via domain sharding** (img1, img2, img3) — a hack on a violated rule. **RFC 7230 removed the sentence in 2014** ("the spec conceded").
- **Pipelining** was the best row — and **nobody shipped it**.

## 5.3 HTTP/1.1 today — RFC 2616 (June 1999): mostly tightening
New in 2616: **307 Temporary Redirect**, **416**, **417 Expectation Failed** + Expect, identity content-coding, TE + transfer-coding registry, **Host becomes a MUST (missing → MUST 400)**, ETag required on resource creation, charset wildcards, byte ranges without known length. **504 is NOT new** (in 2068).

**Why 307 exists — "a standard losing to deployed reality":** RFC 2068 said 302 keeps the method; every browser turned POST into GET anyway. 2616 renamed 302 to **"Found"**, documented reality, and added **307 for "keep the method"**. (Also 303 See Other = explicitly change to GET.) "Easier to add a number than fix a billion deployed clients."

### Postel's law loses: Content-Length + Transfer-Encoding
- **RFC 2616 §4.4 (1999):** if both TE and CL present, **CL MUST be ignored** — recover, don't reject ("be liberal in what you accept").
- **RFC 9112 §6.3 (2022):** server **MAY reject** such a request or process by TE alone; **regardless, MUST close the connection** after responding.
- "Be liberal in what you accept is a fine rule for two programs, catastrophic for a chain of five."

### HTTP request smuggling — one byte stream, two readings
```
POST /echo HTTP/1.1
Host: site-a.local
Content-Length: 6
Transfer-Encoding: chunked

0

GET /admin HTTP/1.1
Host: site-a.local
```
- Reader using **Content-Length: 6** → ONE request with body `0\r\n\r\nG`.
- Reader using **Transfer-Encoding** → TWO requests; second is **GET /admin**.
- CDN reads one way, origin the other → a request the CDN never saw + a spare response left in the connection for the next user. Demo server answered **2 responses (200 + 404 for "the request nobody sent")**.
- **HTTP/2 makes this unrepresentable**: length in the frame header, no second opinion.

### One document became six (RFC 7230–7235, June 2014) — "microservices for RFCs"
| RFC | Title | Who reads it |
| --- | --- | --- |
| 7230 | Message Syntax & Routing | Proxies, LBs, CDNs (https scheme lives here) |
| 7231 | Semantics & Content | Frameworks: methods, status codes |
| 7232 | Conditional Requests | Anything with ETag |
| 7233 | Range Requests | Video, downloads, Parquet |
| 7234 | Caching | Every CDN |
| 7235 | Authentication | WWW-Authenticate / Authorization |

### Why your JWT is base64
- HTTP `token` grammar (tchar) excludes `" ( ) , / : ; < = > ? @ [ \ ] { }` — rule actually from **RFC 2616 §2.2 (1999)**, written as a list in 7230 §3.2.6.
- A JWT must survive Authorization header, URL query, cookie, form field and JSON body; the signature is raw bytes. **base64url swaps `+ /` for `- _`** (URL-safe). "Every layer has an alphabet; the intersection is ~64 characters wide — why base64 exists" (same as MIME in Session 2).

### RFC 9110–9114 (June 2022) — semantics vs encoding
| RFC | What | Version-specific? |
| --- | --- | --- |
| **9110** | HTTP **Semantics** (methods, status, headers, ranges, auth) | **No — shared by 1.1, 2, 3** |
| **9111** | HTTP **Caching** | No — shared |
| **9112** | HTTP/1.1 | Wire format only |
| **9113** | HTTP/2 | Wire format only |
| **9114** | HTTP/3 | Wire format only |
"Three encodings, one language." **418 I'm a teapot**: April Fool's **RFC 2324 (1998)** — reserved forever ("Unused") because too many people shipped the joke.

## 5.4 What HTTP/1.1 cost

### Head-of-line blocking — 5 fast responses wait 2 s for a sixth
Pipelined on one connection: `/big.txt?delay=2.0` first → **every response ~2003 ms**. One connection each: big 2006 ms, others **3–7 ms**.
**Cause: there is no request id on the wire — "the order IS the identifier."** Responses must come in request order, so the slowest sets the pace.

**Multiplexing needs identity:**
| Protocol | Identifier |
| --- | --- |
| TCP | src/dst port |
| SS7/TCAP | transaction id |
| FastCGI | requestId in every record |
| HTTP/1.1 | **nothing** → strict ordering |
| HTTP/2, HTTP/3 | **stream identifier, 31 bits, every frame** |

### Header bloat — 97.5% of what you upload is a repeat
One request's headers = **805 B** (cookies, User-Agent, Accept-*, sec-fetch-*). × 80 requests = 64,320 B; new info (paths) = 1,600 B (**2.5%**); repeats = 62,720 B (**97.5%**). On 1 Mbit uplink = **0.51 s** before app data moves. Why not gzip? → CRIME (below).

### Nagle + delayed ACK — "when keep-alive made it slower"
- **Nagle (RFC 896, 1984):** don't send a small segment while an earlier one is unacknowledged.
- **Delayed ACK (RFC 1122):** wait **up to 40 ms** to piggyback the ACK.
- `write(head); write(body)` → head goes out; body held by Nagle; client delays ACK → **~40 ms per request** (every request but the 1st) — only on **persistent** connections (close() flushes). Total 174 ms vs **3.2 ms with one write + `TCP_NODELAY`**.
- nginx and Apache **coalesce writes and set TCP_NODELAY**.

### The bill for HTTP/1.1
| Wall | Measured | Fixed by |
| --- | --- | --- |
| Head-of-line blocking | 2003 ms vs 3 ms | Stream ids — HTTP/2 |
| Header bloat | 97.5% repeats | HPACK — HTTP/2 |
| Too many connections | 6/origin, 18 with sharding | One connection — HTTP/2 |
| Ambiguous framing | Request smuggling | Frame headers — HTTP/2 |
| TCP itself | 3 RTTs before first byte | QUIC — HTTP/3 |

"Text is slow" is not the finding (gzip 2.8%). **The problem was text without lengths and without identifiers. HTTP/2 is "HTTP with lengths and ids"; binary is the consequence.** Text framing is why HTTP won (anyone could implement & debug with telnet).

## 5.5 HTTP/2

### History — ship to a billion users, then standardise
| When | What |
| --- | --- |
| **Nov 2009** | **SPDY** announced (Belshe & Peon, Chromium blog) — "up to 55% faster" |
| 2010–2014 | Chrome, Firefox, nginx, Twitter, Facebook ship it |
| Feb 2015 | Google announces SPDY retirement |
| **May 2015** | **RFC 7540 (HTTP/2) + RFC 7541 (HPACK)** — "SPDY with the edges filed off" |
| May 2016 | SPDY removed in **Chrome 51** |
| **Jun 2022** | **RFC 9113** obsoletes 7540; **deprecates priorities and the h2c Upgrade** |
It's **"HTTP/2" not "HTTP/2.0"** — no minor versions; next version = new number + new wire format.

### Connection preface — 24 bytes
`PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n` (exactly **24 octets**). An HTTP/1.1 server sees method PRI, version 2.0 and fails cleanly with **501** instead of parsing binary as text. ("PRI…SM" = **PRISM**, 2013.)
- **Over TLS: ALPN (RFC 7301)** — client lists `h2`, `http/1.1` in ClientHello; server picks in ServerHello; **zero extra RTTs**.
- **Cleartext (h2c):** RFC 7540's `Upgrade: h2c` dance **deprecated in 9113**; only "prior knowledge" remains. **No browser ever shipped cleartext HTTP/2.**

### Frame header — 9 bytes
**Length (24 bits) · Type (8) · Flags (8) · R (1 reserved bit) · Stream Identifier (31 bits)** → payload.
- **Client-initiated streams are odd, server streams even** (no coordination). **Stream 0 = the connection** (SETTINGS, PING, GOAWAY).
- Example: `GET /` = 67 B of text → **15 B HPACK**.

### The ten frame types
| Type | Name | Does | Replaced |
| --- | --- | --- | --- |
| 0x0 | DATA | Body chunks ≤ MAX_FRAME_SIZE | Content-Length / chunked |
| 0x1 | HEADERS | Opens a stream; HPACK block | Request line + headers |
| 0x2 | PRIORITY | **Deprecated** (RFC 9218 PRIORITY_UPDATE) | — |
| 0x3 | RST_STREAM | **Cancel ONE stream** | Closing TCP (killing everything) |
| 0x4 | SETTINGS | Announce limits both directions | Nothing |
| 0x5 | PUSH_PROMISE | Server push | Nothing (didn't last) |
| 0x6 | PING | RTT; keep intermediaries awake | Nothing |
| 0x7 | GOAWAY | "Last stream id I'll process" — graceful drain | Connection: close mid-flight |
| 0x8 | WINDOW_UPDATE | Flow control **per stream AND per connection** | Only TCP's window |
| 0x9 | CONTINUATION | Header block bigger than a frame | Nothing — **a 2024 DoS class** |
Defaults: **HEADER_TABLE_SIZE 4096 · INITIAL_WINDOW_SIZE 65535 · MAX_FRAME_SIZE 16384 · MAX_CONCURRENT_STREAMS unlimited ("no smaller than 100" recommended)**.

### HPACK (RFC 7541) — 174 bytes → 79 → 6
1. **Static table — 61 entries**, identical everywhere; index 2 = `:method: GET` (name AND value) → GET costs one byte **0x82**. "Not compressed. Indexed."
2. **Dynamic table — from index 62**: anything sent before **on this connection** gets an index; 300-byte cookie costs 300 B once then 1–2 B forever.
3. **Huffman (Appendix B)** — fixed canonical code from real header text ("e" = 5 bits, "X" = 8); used per string only when it shrinks.
- Same header set: **HTTP/1.1 text 174 B → HPACK first time 79 B (55% saved) → second time 6 B (97%)** — six one-byte indices.
- **Dynamic table is per connection → HTTP/2 wants ONE connection; domain sharding is now harmful.**

### Why not just gzip headers? CRIME (2012)
Attacker can't decrypt but watches **compressed size**: inject guesses next to a secret cookie; when the guess matches, gzip finds a repeat and the length drops by 1 byte → "correct". HPACK's defence is structural: **Huffman table is fixed** (not adaptive), **dynamic table is an exact-match index, not a substring matcher**; RFC 7541 §7.1 lets you mark fields **"never indexed"**. Warning: gzipping JSON with a user search term + an API key = rebuilt CRIME (BREACH-style).

### Multiplexing — same six requests, one connection, ~400× faster
HTTP/2: /style.css 4.9 ms, logo 5.7, icon 6.9, app.js 6.9, hero 7.8, big.txt 2005.9 — **out of order on purpose**, because each frame says which stream it belongs to. Dynamic table warming: 84 B → 30 B, 76 → 12, 73 → 11…

### "A protocol can only give you permission" — the bug shipped first
Handling requests inline in the read loop → exactly HTTP/1.1's numbers (all ~2005 ms). Fix: a thread per stream + lock on the connection. **The transport is fine; you serialised the work yourself** (same shape: worker pool sharing one DB connection, blocking call inside a coroutine, gRPC handler with a global mutex).

### Server push — nobody deprecated it, everybody removed it
- Still in RFC 9113 §8.4 and RFC 9114 §4.6. Only PRIORITY and h2c Upgrade were deprecated.
- **Chrome 106 (27 Sep 2022)** removed it: used by **1.25%** of HTTP/2 sites (later 0.7%); "no clear net performance gain and in many cases regressions".
- Problem: **the server doesn't know what's in your cache** → pushes files you already have, competing for bandwidth/cwnd.
- Replacement: **103 Early Hints (RFC 8297)** — "you're going to want style.css"; client checks its cache and decides. **"The server keeps the knowledge; the client keeps the decision. Inform — do not act."**

### What HTTP/2 could not fix — TCP head-of-line blocking
RFC 9114 §1.1: a lost/reordered packet stalls **all** streams because TCP's loss recovery can't see HTTP/2's streams. Demo: 300 ms stall at byte 3000 → everything behind the hole waits ~306 ms though the bytes had arrived (kernel can't hand them over out of order); **which streams get caught changes every run**.
Google SPDY data: **11.81% speedup at 0% loss, 47.7% at 2% loss** — multiplexing helps most exactly where TCP hurts most.

## 5.6 QUIC

### Why UDP — "the internet stopped accepting new protocols"
- IP protocol numbers: **TCP = 6, UDP = 17, SCTP = 132**. Why not a new number (e.g. 253)? Every NAT, firewall, CGNAT, corporate proxy and hotel router **drops what it doesn't recognise** → **SCTP (standardised 2000) can't be used across the public internet**. UDP is "a hole that already exists".
- **Ossification:** "Anything a middlebox CAN read, it will eventually depend on" (RFC 8999 §7) — how TCP options became unusable. **QUIC encrypts packet numbers and most of the header** — not only for privacy but to stay changeable.
- **Userspace:** a TCP change = kernel upgrade on a billion machines and a decade; a QUIC change ships with your app.

### Round trips — one handshake, not two
| Cold connection | RTTs | Measured @150 ms |
| --- | --- | --- |
| TCP + TLS 1.3 + HTTP/2 | **3** (TLS 1.2 → 4) | 456.6 ms |
| QUIC + HTTP/3 (1-RTT) | **2** | 319.8 ms |
| QUIC 0-RTT (resumed) | **1** (request in first flight) | 161.7 ms |
- RFC 9001 §2.1: no separate transport and crypto handshakes — **TLS ClientHello rides in a QUIC CRYPTO frame**; ALPN rides there too. **TLS is mandatory — there is no unencrypted QUIC.**
- Cold: QUIC saves 137 ms. Resumed 0-RTT saves 295 ms.
- "Every layer boundary is a place you may pay a round trip."

### 0-RTT and replay
- RFC 9001 §9.2: early data is exposed to **replay attacks**; protections (single-use ticket cache) are imperfect because a server farm has many servers — attacker replays to a different one.
- **Rule: idempotent requests only** (GET fine; POST that charges a card, not). **Cloudflare allows only GET and HEAD** in 0-RTT and sets an **`Early-Data`** header so origin can reply **425 Too Early**.
- "0-RTT is a cache of a negotiation; every cache of a negotiation trades a round trip for the possibility of a replay."

### Head-of-line blocking, gone
QUIC **STREAM frames carry a stream id and an offset — ordered within a stream, unordered between streams**. With 18 datagrams deleted (5%), only /big.txt (78 ms) waited; others 4–11 ms. On TCP the blast radius is "whoever had bytes behind the gap"; on QUIC it's exactly one stream.

### Connection IDs — connection survives changing networks
- **TCP: the connection IS the 4-tuple** (src IP, src port, dst IP, dst port). Wi-Fi → LTE changes IP → every TCP connection dies (video buffers, downloads restart, websockets reconnect). Same with **NAT rebinding** after idle.
- **QUIC: identity ≠ addressing** — **connection ID**; new address, same CID, path validated → **connection migration**.
- Privacy: a stable CID is a tracking id → CIDs "MUST NOT contain information an observer can correlate"; endpoints **issue a pool and rotate**.
- "Identity belongs at the layer that owns the semantics."

### QPACK (RFC 9204) — HPACK had its own HOL blocking
- HPACK's dynamic table is shared mutable state requiring **total ordering** (free on TCP); QUIC removed that → a header block on stream 12 could reference an entry inserted on stream 8 that hasn't arrived → stall.
- Fix: move table updates to dedicated **unidirectional streams**: **encoder stream (type 0x02)** (insertions) and **decoder stream (type 0x03)** ("I've seen these" acks). Encoder only references entries known safe.
- Defaults **QPACK_BLOCKED_STREAMS = 0, QPACK_MAX_TABLE_CAPACITY = 0**.
- Static table: **HPACK 61 entries from index 1; QPACK 99 entries from index 0** (includes sec-fetch headers).
- "Relax an ordering guarantee, then go find what was relying on it."

### Discovery & fallback
| Mechanism | RFC · date | How | Cost |
| --- | --- | --- | --- |
| **ALPN** | RFC 7301 · Jul 2014 | Protocol chosen in TLS handshake ("h2", "h3") | Needs a handshake first |
| **Alt-Svc** | RFC 7838 · Apr 2016 | Response header `Alt-Svc: h3=":443"`; browser remembers | One full TCP+TLS connection per cold cache |
| **HTTPS DNS RR** | RFC 9460 · Nov 2023 | **DNS record type 65** carries ALPN list | Nothing — lookup happens anyway |
- **3–5% of networks block all UDP** (RFC 9308). **95.3%** of Google's clients could use QUIC; 4.4% blocked or packet-size problems.
- Fallback to TCP/TLS = **downgrade attack** by construction (drop UDP, wait for fallback).

### Adoption (2024–2026)
- HTTP Archive / Web Almanac 2024 by request: **HTTP/1.1 ≈15%, HTTP/2+ ≈85%**. By homepage: h1 21–22%, h2 70–71%, **h3 7–9%**. Alt-Svc advertising h3 ≈26–28%; HTTPS DNS RR ≈9–10%.
- W3Techs (Sep 2026) HTTP/2 34.6%, HTTP/3 40.3% — "treat with suspicion".
- 15% of requests still HTTP/1.1 eleven years later — no cutover, a long tail.

### Four ideas
1. **Multiplexing needs identity** — no request id → order is the identifier. 31 bits fixed it (TCP ports, SS7 transaction ids, FastCGI requestId, QUIC stream ids).
2. **Every fix is the next problem** — persistence → pipelining → HOL; HTTP/2 fixed HOL above TCP, exposed it inside TCP; QUIC fixed that and broke HPACK → QPACK.
3. **Semantics and encoding differ** — RFC 9110 = meaning; 9112/9113/9114 = three ways to write it. GET unchanged since 1996.
4. **Deployed reality beats specification** — 302→307; 2 connections → 6; Postel's law lost to smuggling; 418 reserved; push dead without deprecation; QUIC on UDP because middleboxes have a veto.

Homework: plot wall time vs N connections (find the knee; cwnd via `ss -ti`) · ETag from mtime + two writes in one second (weak vs strong) · decode HPACK by hand (RFC 7541 §6) · QPACK_BLOCKED_STREAMS 0 vs 16 · block UDP 4433 with iptables and time the fallback.

> **Quiz points — Session 5**
> - RFC map: 1945 (1.0, 1996), 2068 (1.1, 1997), 2616 (1999), 7230–7235 (2014), 9110 semantics / 9111 caching / 9112 h1 / 9113 h2 / 9114 h3 (2022), 7540+7541 (h2 + HPACK, 2015), 9000 QUIC, 9001 QUIC-TLS, 9204 QPACK, 7301 ALPN, 7838 Alt-Svc, 9460 HTTPS RR, 8297 103 Early Hints, 2324 teapot, 896 Nagle, 1122 delayed ACK.
> - 1.0: close after each response, no Host, Last-Modified/If-Modified-Since/Expires caching.
> - 1.1: persistent by default (Connection: close to opt out), Host required (else 400), ETag/If-None-Match → 304, weak W/ validators, If-Match = optimistic concurrency, Range → 206/416, chunked (hex length, 0 terminator), OPTIONS (CORS preflight), TRACE (XST), Via, Expect: 100-continue, Cache-Control (no-cache = revalidate, no-store = don't store), Vary.
> - 2 connections rule → browsers 6 per origin; removed in RFC 7230. Pipelining never shipped.
> - 302 "Found" vs 307 (keeps method) vs 303.
> - Smuggling = CL vs TE disagreement; RFC 9112 says close the connection; HTTP/2 makes it unrepresentable.
> - HOL root cause: no request id. Headers 97.5% repeats. Nagle + delayed ACK 40 ms → TCP_NODELAY.
> - SPDY 2009 → RFC 7540 2015 → SPDY removed Chrome 51 (2016) → RFC 9113 2022.
> - Preface "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n" 24 bytes; ALPN "h2"; h2c deprecated.
> - Frame header 9 bytes: length 24, type 8, flags 8, R 1, stream id 31. Client odd, server even, stream 0 = connection. 10 frame types.
> - HPACK: 61 static entries (0x82 = :method GET), dynamic table from 62, Huffman; 174→79→6 B. CRIME = compression-size leak.
> - Server push removed in Chrome 106 (2022); replacement 103 Early Hints.
> - HTTP/2 still suffers TCP HOL. QUIC = UDP (proto 17) + userspace + encrypted headers; streams with id + offset.
> - Handshakes: TCP+TLS1.3+h2 = 3 RTT, QUIC = 2 RTT incl. request (1-RTT handshake), 0-RTT = replayable → idempotent only, 425 Too Early.
> - Connection IDs → migration; rotated for privacy. QPACK encoder/decoder streams; 99 static entries.
> - 3–5% networks block UDP; fallback = downgrade attack.

---

# SESSION 6 — (Ab)using CDNs

"Someone else's computers, closer to your users — and everything they can do while the traffic is passing through."
Players & keywords: Akamai · CloudFront · Fastly · Google · Broadpeak · Cloudflare · SSI · ESI · Railgun · BBR · anycast.
Weeks 1–5 made one origin fast; Week 6 puts a network in front of it; Week 7 = what fails; Week 8 = video through all of it.

Six questions: (1) Why the edge exists (physics) · (2) What a CDN is · (3) Caching, incl. the uncacheable, poisoning & deception · (4) Moving bytes faster (BBR, pooling, multiplexing, shielding) · (5) Everything that isn't speed (WAF, rate limit, DDoS, API gateway) · (6) Cloudflare hands-on.

## 6.1 Physics — the speed of light is the one number you can't optimise
- Light in vacuum **299,792 km/s**; in fibre **~204,218 km/s** (~2/3 c; refractive/group index **1.468**) → **4.90 ms per 1000 km one way** (~5 µs/km).
- **Mumbai → Chennai → back: ~10 ms** floor (measured ping 23 ms). **Mumbai → Ashburn (us-east-1) → back: 126 ms** floor — can never go below.
- Hollow-core fibre would be **47% faster** (Microsoft Azure deploying, Sep 2025) — not on your path today.
- TLS 1.3 needs **3 RTTs** to first byte (TCP + TLS + request) → **~380 ms of nothing** to Virginia; no CPU helps.

### Distance charges you twice: latency AND loss (Akamai 2010)
| Distance | RTT | Loss | Throughput | 4 GB download |
| --- | --- | --- | --- | --- |
| Local < 100 mi | 1.6 ms | 0.6% | 44 Mbps | 12 min |
| Regional 500–1000 mi | 16 ms | 0.7% | 4 Mbps | 2.2 hrs |
| Cross-continent ~3000 mi | 48 ms | 1.0% | 1 Mbps | 8.2 hrs |
| Multi-continent ~6000 mi | 96 ms | 1.4% | 0.4 Mbps | 20 hrs |

**Mathis formula (1997): Throughput ≈ MSS / (RTT × √loss).** A single TCP flow's ceiling falls with RTT and √loss → far edge is **110× slower**, not 60×. HTTP/2 multiplexing and BBR exist to claw this back.

### What the edge buys back (you —10 ms— Mumbai edge —194 ms— Washington origin, TLS 1.3 every hop)
| Path | Content | TTFB | vs direct |
| --- | --- | --- | --- |
| Direct to origin, new connection | dynamic | 621 ms | 3.0 RTT |
| Direct, kept alive | dynamic | 208 ms | 1.0 RTT |
| Edge with **no origin pool** (just a longer proxy) | dynamic | 625 ms | 3.1 RTT |
| Edge, **warm origin pool**, new user connection | dynamic | 233 ms | 1.1 RTT |
| Edge, warm pool, kept alive | dynamic | 209 ms | ≈ direct |
| **Edge cache HIT** | static | **34 ms** | 0.2 RTT |
| Edge cache HIT, kept alive | static | **11 ms** | 0.1 RTT |
**A cache miss through the edge is no faster than direct (sometimes slower).** The edge earns its place two ways: **warm connections to origin (saves handshakes)** and **cache hits (deletes the origin round trip: 194 ms → 0)**.

## 6.2 What a CDN is — "Session 4's reverse proxy, rented in 300+ cities"
you → **edge PoP** (cache · TLS · WAF), ~10 ms → **shield / tiered cache** → your origin (one long, controlled leg).
- Nothing new: reverse proxy = nginx (S4); caching = proxy_cache (S4); pool = upstream keepalive (S3); **anycast** puts one IP in every city (S2 addressing). Squid did reverse-proxy caching in 1996.
- Geography adds: cheap handshakes near the user; CDN owns both ends of the long leg (own transport & pooling); shield layer means many edges share one origin fetch; **one anycast address announced from every city**.

### Consistent hashing — the founding algorithm (Karger et al., STOC 1997 — Akamai founded on it)
100,000 URLs on 10 caches, add an 11th:
| Scheme | URLs that move | Busiest vs mean |
| --- | --- | --- |
| `hash(url) % N` | **90.9%** | 1.02× |
| Consistent hash, 1 point/server | 3.3% | 2.93× (uneven) |
| Consistent hash, **160 points/server** (virtual nodes) | 8.2% (~1/11) | 1.14× |
- **Modulo is a trap**: adding a server moves ~90% of URLs → near-total cache flush + origin stampede.
- Consistent hashing moves only the new server's fair share (~1/(N+1)); **virtual points** even out load.
- nginx: **`hash $request_uri consistent;`** (160 points/server, **ketama**-compatible). Same idea: DHTs, sharded caches — choosing an owner without a central registry.

### The players
| CDN | Born | Runs on / notable | Course link |
| --- | --- | --- | --- |
| **Akamai** | 1998 | own "ghost" edge servers; **ESI (2001)**; FastTCP → BBR | consistent hashing |
| **Amazon CloudFront** | 2008 | AWS edge; **BBR to viewers since 2019 (+22%)** | S2 congestion |
| **Fastly** | 2011 | **heavily-modified Varnish** + H2O; instant purge | S3/S4 Varnish |
| **Google (Media CDN)** | 2022 | YouTube's edge opened up; QUIC/BBR everywhere | S5 |
| **Broadpeak** | — | born of video; operator/telco CDN for streaming; on GKE | S8 |
| **Cloudflare** | 2010 | was **nginx + LuaJIT (FL1) → Rust/Oxy (FL2, Oct 2025: −10 ms, +25%)**; origin-facing proxy → **Pingora (2022)** | S4 nginx |

### Anycast demo
- `curl -s https://www.cloudflare.com/cdn-cgi/trace` → `colo=BOM` (**colo = IATA airport code**: BOM Mumbai, DEL Delhi, MAA Chennai, SIN, LHR, IAD Ashburn). Also shows `tls=TLSv1.3`, `kex=X25519MLKEM768` (post-quantum).
- `dig +short CHAOS TXT id.server @1.1.1.1` → "BOM" (which resolver answered).
- **`cf-ray: 8c1a…-BOM`** — the suffix is the colo; every response carries the PoP that served it.
- PoP chosen by **BGP anycast**, not by you; classroom Wi-Fi vs mobile data → different colo, same IP.

## 6.3 Caching

### Defaults (Cloudflare)
- **Caches by file extension**: **68 static extensions** (css, js, png, jpg, webp, woff, mp4, pdf, zip…). **NOT cached by default: HTML, JSON**, anything with **Set-Cookie**, or `Cache-Control: private / no-store / no-cache / max-age=0`.
- Default edge TTL if origin is silent: **200/301 → 2 hrs · 404 → 3 min · others not cached**.
- **Default cache key = scheme + host + path + query.** Cookies and most headers **not in the key** → two users with different cookies share one object: fine for app.css, catastrophic for /account. `Vary` or a custom key says "these differ".
- `x-cache: MISS` (first visitor pays) → `HIT`; HTML → `DYNAMIC`.

### cf-cache-status — eight states
| Status | Meaning | Origin hit? |
| --- | --- | --- |
| **MISS** | Eligible, not in cache, fetched | yes |
| **HIT** | Served from cache, fresh | no |
| **EXPIRED** | Was cached, TTL passed, re-fetched | yes |
| **REVALIDATED** | TTL passed, origin said **304** → reused (ETag/If-None-Match) | cheap 304 |
| **UPDATING** | Stale served now, refresh in background (= proxy_cache_use_stale updating) | async |
| **STALE** | Origin down — serve stale anyway (Session 7) | failed |
| **DYNAMIC** | Not eligible — never looked in cache (default for HTML) | yes |
| **BYPASS** | Eligible but origin said no-store (or bypass rule) | yes |

### Caching the uncacheable — move personalisation outward
| Technique | When / who | Idea |
| --- | --- | --- |
| **SSI** Server-Side Includes | **NCSA HTTPd 1.0a1, 1994** (predates CGI; nginx still ships it) | Holes in HTML filled by **the server** before sending |
| **ESI** Edge-Side Includes | **Akamai + Oracle, W3C Note 2001** | Same holes filled **at the edge**; cache the shared shell everywhere, assemble per user at the PoP |
| **Ajax** | Web 2.0, ~2005 | Holes pushed to **the browser**; cache body on CDN, fetch personal bits async |
| **Railgun** | Cloudflare 2013–2024 | Give up caching the page; send only the **bytes that changed** (delta) |
Arc: **server → edge → browser**; only the small personal part is recomputed.

### ESI in numbers
Origin sends one shell: `<esi:include src="/fragment/user"/> <esi:include src="/fragment/cart"/>` with `Cache-Control: s-maxage=300` and `Surrogate-Control: content="ESI/1.0"`. 100 logged-in users (page 39,676 B each):
| | Origin requests | Origin→edge bytes | Bytes to users | Edge cache |
| --- | --- | --- | --- | --- |
| Origin assembles | 100 | 3,984,200 | 3,992,400 | DYNAMIC ×100 |
| ESI, edge assembles | **201** | **83,454 (−98%)** | ~same | HIT ×99, MISS ×1 |
Trade: **origin bytes −98%**, **user download unchanged**, **origin requests UP** (each fragment is its own fetch). Load moves from origin rendering to edge assembly.

### Delta / dictionary compression (Railgun → RFC 9842)
~24 KB news page regenerated every minute:
| Method | Bytes | % of raw |
| --- | --- | --- |
| gzip -6, no dictionary | 4,276 | 17.7% |
| deflate, dict = page 1 min ago | 598 | 2.5% |
| **zstd, dict = page 1 min ago (dcz)** | **436** | **1.8%** |
| zstd, dict = page 1 hour ago | 1,277 | 5.3% |
- **Railgun** — daemon in origin + sender at edge keep the last version of each page; send only the delta ("caching down to individual bytes"). **Retired Jan 2024** (network got fast; a standard arrived).
- **RFC 9842 Compression Dictionary Transport (Sep 2025)** — browser↔server: previous version = dictionary. Headers **`Available-Dictionary: <sha-256>`**, **`Content-Encoding: dcb / dcz`** (dictionary-compressed brotli / zstd). Same-origin, HTTPS-only, hashed (dictionaries leak, cf. CRIME). RFC 9841 = shared brotli.
- ~10× better than gzip; catch: dictionary must be recent and identical on both ends.

### Two classic cache attacks — "a shared cache is a shared weapon"
| Cache **poisoning** (James Kettle, 2018) | Cache **deception** (Omer Gil, Black Hat 2017) |
| --- | --- |
| Origin reflects an **unkeyed header** (e.g. `X-Forwarded-Host: evil.example`) into the page → one attacker request caches `<script src="https://evil.example/app.js">` → **every visitor** gets it (HIT) | Trick victim into loading **/account/settings/fake.css**; edge sees ".css", **caches the victim's private page**; attacker fetches same URL from cache |
| Fix: **drop the unkeyed header at the edge, add it to the key, or Vary on it** | Fix: **don't cache by extension alone**; honour origin's content-type and no-store |
Both = **the cache key disagreeing with reality**.

## 6.4 Faster bytes

### BBR (Bottleneck Bandwidth and Round-trip propagation time — Cardwell et al., Google, 2016)
- Loss-based **CUBIC**: fill pipe until drop, halve → sawtooth; on long lossy CDN paths it **mistakes distance for congestion**.
- **BBR measures bottleneck bandwidth + min RTT, paces to that. Loss ≠ congestion signal.**
| Deployed | Where | Result |
| --- | --- | --- |
| Google B4 + YouTube, 2016 | the paper | **2–25× CUBIC throughput; median RTT −53%** |
| Amazon CloudFront, 2019 | edge → viewer | up to **+22%**; some US mobile +100% |
| Akamai, Nov 2019 | media | BBR on >80% of end-user connections |
| Web census 2023 | top-10k sites | **BBR now most-deployed CCA**; CUBIC ~7% |
**Only the sender changes** — no new protocol/client/router → a CDN can just switch it on (it owns the sender on both legs).

### Connection pooling to origin (300 visitors, edge↔origin 50 ms, TLS 1.3, origin idle-close 1 s)
| Edge config | New conns | Reuse | Mean TTFB |
| --- | --- | --- | --- |
| No pool | 300 | 0% | 160 ms |
| 32 worker pools | 164 | 45.3% | 112 ms |
| 8 worker pools | 52 | 82.7% | 74 ms |
| **1 shared pool** | **4** | **98.7%** | **57 ms** |
- A pooled connection opened by one worker can only be reused by that worker (nginx's **per-worker pools**); split pools stay cold.
- **Cloudflare Pingora** (shared pool, Sep 2022): one big customer's reuse **87.1% → 99.92%** → **160× fewer new origin connections**, **"434 years of handshake time saved every day"**.
- "Amortise the setup" across a continent — the setup is a 2-RTT TLS handshake.

### Multiplexing & shielding
- CDNs use HTTP/2 on both legs in principle, but **most CDN→origin hops are still HTTP/1.1**; cloudflared's **`http2Origin` defaults to false**. Pooling is what actually saves you today.
- **Tiered cache / origin shield**: without it, 300 edges MISS → **300 origin requests** for the same object (a built-in **thundering herd**). With it, edges fetch from a regional parent which fetches once. Cloudflare **Tiered Cache / Argo**.
- **Request collapsing** at one edge: 50 users, cold cache, 1 object → **50 origin fetches without, 1 with** (49 wait then HIT). nginx's single-flight version = **`proxy_cache_lock`**.
- Collapsing (one PoP) + tiered cache (across PoPs) = "never fetch the same object twice at once" → CDN **protects** origin during a spike instead of amplifying it.

## 6.5 Not speed — the edge becomes the security perimeter
"All requests are coming to the CDN anyway" → **WAF** (SQLi, XSS, path traversal), **rate limiting**, **DDoS absorption**, **API gateway** (auth, add/strip headers, route, fallback). "Speed got you to adopt it; control is why you can't leave."

### WAF — "a denylist of spellings; the bug still lives in your origin"
- `' OR 1=1 --` → blocked by rule sqli-tautology. `'/**/OR/**/1=1--` (comments instead of spaces) → **5 rows leak**. With normalisation (strip comments) → blocked. `' --` (no OR/UNION/digits) → leaks again.
- **The arms race is normalisation** (raw → URL-decode → strip comments → …) vs the number of spellings; never won outright.
- WAF is for **buying time + blocking mass-scanned known payloads (Log4Shell, OWASP top)**. **Real fix: bind parameters (parameterised queries) in the origin.**
- Cloudflare Free Managed Ruleset on all plans; OWASP Core needs Pro.

### Rate limiting — "100 per 10 seconds" has five meanings
| Algorithm | Burst at window edge | Normal page load |
| --- | --- | --- |
| **Fixed window** | **200 in one second** (100 at 9.999 s + 100 at 10.001 s) | all pass |
| Sliding log (exact) | 100 | all pass |
| **Sliding window (estimate)** | 104 | all pass |
| Token bucket | 109 | all pass |
| **Leaky bucket, burst=0** | 10 | **97% refused** (browser opens 30 requests at once) |
- **Cloudflare's answer (2017): sliding-window estimate** — weight the previous window by how much still overlaps; **two counters per client**; across 400M requests only **0.003%** wrongly allowed/blocked.
- Cloudflare free plan offers only the **10 s fixed window**. nginx **`limit_req` has a `burst`** parameter for this reason (leaky bucket with burst).
- **Counts are per data centre, not global** — a botnet across 330 cities gets 330 budgets.

### DDoS — the one thing you genuinely can't do yourself
- **31.4 Tbps** — largest DDoS on record (Cloudflare, **Dec 2025**; **Aisuru** botnet, 1–4M devices; **lasted 35 s**); **mitigated automatically**.
- Cloudflare capacity **~500 Tbps across 330+ cities**. Volumetric floods are won with more capacity spread so **anycast splits the flood** across locations. Your origin has one pipe.
- Catch: one network absorbing everyone's attacks = **everyone's single point of failure** — **Fastly, 8 June 2021**: one customer's config change → **85% of network returning errors** → Reddit, Spotify, gov.uk down; **49 min** to recover.

### API gateway at the edge (JWT)
- No token → **401**; valid JWT → edge sets `X-User`, origin returns data; expired → 401; **`alg: none` forgery → refused ("never let the token pick the algorithm")**; client-sent `X-User: admin` → **ignored/overwritten**.
- **Attacker hits origin IP directly → everything leaks** → "the gateway is only real if the origin can't be reached directly". Fix: **mutual TLS (authenticated origin pulls)** or a **Tunnel** (origin only answers clients with the edge's certificate).
- Header hygiene: strip `X-Powered-By: PHP/5.4.45`.

## 6.6 Cloudflare hands-on
**No-account demos:** (1) `/cdn-cgi/trace` colo/tls/kex; (2) `dig CHAOS TXT id.server @1.1.1.1`; (3) `curl -sI` for `cf-ray`, `cf-cache-status`, `age`, `alt-svc`; (4) TLS time Mumbai vs Virginia via DynamoDB regional endpoints (`curl -w '%{time_appconnect}'`); (5) **`cloudflared tunnel --url http://localhost:8000` → `https://<rand>.trycloudflare.com`** (Quick Tunnel: no account, no DNS; limits **200 in-flight, no SSE, testing only**); echo server prints **CF-Connecting-IP**, **CF-Ray**, **CDN-Loop** and shows few TCP connections (the pool). Also radar.cloudflare.com, speed.cloudflare.com.

**Dashboard (free plan):**
| Action | Point | Free limit |
| --- | --- | --- |
| **Orange vs grey cloud** (DNS proxy toggle) | origin IP vanishes behind anycast | — |
| Cache an HTML page (Cache Rules) | MISS→HIT→purge→MISS; `Age` climbs | 10 rules |
| WAF custom rule | same bypasses | 5 rules, no regex |
| Rate-limit /api/* | ~20 pass then **429**; per-colo | 1 rule, 10 s only |
| Transform Rules — strip X-Powered-By | header hygiene | unlimited |
| Deploy a Worker (`wrangler deploy`) | code at the edge | **100k req/day** |

### Workers — Session 3's question answered again
- A Worker is a **V8 isolate, not a process** — starts in **~5 ms, ~3 MB**, vs a container's 35 MB + cold start.
- CGI forked per request → FastCGI kept warm → nginx event loop → **Workers: runtime already resident in every PoP; your code just runs in it** ("amortise the setup" at the edge).
- Example worker: rate limit by IP (`env.LIMITER.limit`), verify JWT (WebCrypto), set X-User, `fetch(origin)` with primary→backup failover. Tested locally in **workerd** (via Miniflare). ESI worker has a framing bug ("where does this element end?" — why HTMLRewriter).

## 6.7 The bill — what you hand over
| You hand over | Detail |
| --- | --- |
| **Your TLS private keys** | Edge terminates HTTPS → can read every byte |
| **A single point of failure** | Fastly 8 Jun 2021: 85% of network errors, 49 min |
| **Power to see and shape traffic** | **Domain fronting** (hide censored traffic behind innocent domains) — banned by **AWS & Google (2018)**, Azure (2022), **Fastly (Feb 2024)** |
| **Lock-in by architecture** | WAF, rate limits, auth, Workers at the edge → it's your security perimeter, not a swappable cache |

### Four ideas
1. **Move the work, or move the data** — content closer (cache) or personalisation outward (SSI→ESI→Ajax).
2. **The edge is wherever all the traffic converges** — firewall, rate limiter, DDoS scrubber, auth, code followed the traffic.
3. **It's all Sessions 2–5, rented by the city** — reverse proxy, pooling, ETag revalidation, BBR, multiplexing, consistent hashing.
4. **Concentration cuts both ways** — absorbs 31 Tbps; one config bug takes 85% down.

Lab repo *cdn-lab*: origin.py (naive: trusts X-User, f-string SQL, leaks headers), edge.py (~450 lines: cache, pool, WAF, rate limit, JWT, ESI), laggy.py (adds distance, never drops). Assignment: origin behind Cloudflare; show MISS→HIT and DYNAMIC; one cache-key hazard and fix; TTFB table cold/warm/HIT; one edge feature (WAF/rate limit/Worker).

**Quiz schedule (from slides):** Quiz 1 — 21 Sep (Mon); Quiz 2 — 25 Sep (Fri); assignment submission — 25 Sep (Fri, class time).

> **Quiz points — Session 6**
> - Fibre ≈ 2/3 c, ~204,000 km/s, 4.9 ms/1000 km one way. Mumbai–Ashburn RTT floor 126 ms; Mumbai–Chennai ~10 ms.
> - Mathis: throughput ≈ MSS / (RTT × √loss).
> - Edge saves handshakes (warm pool) and, on a HIT, the whole origin round trip. A MISS is no faster than direct.
> - CDN = reverse proxy + cache + pool + anycast, in 300+ cities. colo = IATA code; cf-ray suffix = colo.
> - Consistent hashing (Karger 1997, Akamai): modulo moves ~90%; consistent moves ~1/(N+1); 160 virtual nodes; nginx `hash … consistent` (ketama).
> - Players: Akamai 1998 (ESI), CloudFront 2008, Cloudflare 2010 (nginx+LuaJIT → Rust FL2; Pingora), Fastly 2011 (Varnish), Google Media CDN 2022, Broadpeak (video).
> - Default: cache by extension (68), HTML/JSON not cached; key = scheme+host+path+query; TTL 200/301 2 h, 404 3 min.
> - cf-cache-status: MISS, HIT, EXPIRED, REVALIDATED, UPDATING, STALE, DYNAMIC, BYPASS.
> - SSI 1994 (server) → ESI 2001 (edge) → Ajax 2005 (browser) → Railgun 2013–2024 (delta). RFC 9842 dictionary transport, dcb/dcz, Available-Dictionary.
> - Poisoning (Kettle 2018, unkeyed header) vs deception (Gil 2017, fake .css path).
> - BBR: Google 2016, measures bandwidth + min RTT; now the most-deployed CCA; sender-only change.
> - Shared pool beats per-worker pools; Pingora 87.1% → 99.92% reuse.
> - Tiered cache / origin shield, request collapsing, proxy_cache_lock.
> - WAF = denylist of spellings; fix with parameterised queries. Rate limiting: fixed window allows 2× bursts; leaky bucket without burst refuses real browsers; Cloudflare uses a sliding-window estimate; counts are per colo.
> - DDoS record 31.4 Tbps (Dec 2025, Aisuru, 35 s). Fastly outage 8 Jun 2021, 85%, 49 min.
> - Gateway: refuse alg:none; origin must be locked down (mTLS / tunnel).
> - Workers = V8 isolates (~5 ms, ~3 MB).
> - Domain fronting banned (AWS/Google 2018, Fastly 2024).

---

# SESSION 7 — Building for Failures: Failures & Retries

> **Source:** the Session 7 material in this folder is one mind map ("Failures & Retries"). Every branch below is from that map. The *Explanation* column and the "retry toolkit" are added from the Session 6 teaser, Session 8's "Week 7" call-backs, and the earlier lectures, so you can answer "why" questions.

**Core idea:** a network request is a chain of steps (socket → DNS → connect → write → read → TLS → HTTP → CDN tiers). **Each step fails in its own way**, and the right reaction (retry? fall back? give up? serve stale?) depends on **which** step failed.

## 7.1 The failure map, step by step

### 1. Client — `socket()` system call
| Failure | Reaction (from map) | Explanation |
| --- | --- | --- |
| Can't create a socket (out of file descriptors / resources) | **Retry — after some time a socket can get free** | `socket()` fails with EMFILE/ENFILE when `ulimit -n` (default 1024, S3) is exhausted. Sockets in TIME_WAIT or being closed free up later |

### 2. DNS lookup
| Failure | Explanation |
| --- | --- |
| **DNS mapping not available** | No record (NXDOMAIN) — name doesn't exist or record deleted |
| **Network issue → DNS timeout** | The UDP query to the resolver (S1) is lost; gethostbyname blocks with no timeout you control |
| **DNS resolved but misconfigured** | Wrong IP returned (bad record, stale /etc/hosts entry, wrong resolver) |

### 3. Client — `connect()` system call
| Failure | Explanation |
| --- | --- |
| **Host unreachable → network blockers** | No route (EHOSTUNREACH / ENETUNREACH); firewalls, security groups, NAT block the path |
| **Port 8080 is not listening** | Nothing bound → kernel answers SYN with **RST** → "Connection refused" (ECONNREFUSED) — fast, loud (S1) |
| **Number of connections exceeded (client)** | Client out of fds or **ephemeral ports** (32768–60999 = 28,232 per destination; TIME_WAIT holds them ~60 s) |
| **Number of connections exceeded (server)** | Server's **accept queue/backlog full** (somaxconn), fd limit, or SYN backlog full (SYN flood) — behaviour not portable: refused or hang |
| **TCP timer for packet → No response to SYN** → **No server · Slow network / packet drops · Handshake failure · Connect or dial timeout** | SYN retransmitted with exponential backoff until the connect/dial timeout (ETIMEDOUT). Silent and slow; looks like an overloaded server |
| **Stale DNS IP entry** | Cached IP (TTL, /etc/hosts, client cache) points at a box that no longer serves |

### 4. Client — `write()` system call
| Failure | Explanation |
| --- | --- |
| **Network issue → packet drop → write timeout** | Send buffer fills because peer isn't ACKing; write blocks / times out |
| **Physical machine shutdown** | Peer gone; writes eventually fail (EPIPE/ECONNRESET); **SIGPIPE kills the process** if not handled (S1) |
| **Some network node in the path shuts down** (laptop network, Wi-Fi access point, or the server machine) | Path breaks mid-stream; TCP's connection = 4-tuple, so a network change kills it (QUIC connection IDs fix this, S5) |
| **Rate limit → server business logic → Close / Stop reading** | Server deliberately closes, or stops reading so your writes block (TCP flow control/backpressure) |
| **Rate limit → You submitted a very large content** | Body too large (e.g. 413 Payload Too Large; `Expect: 100-continue` asks first, S5) |

### 5. Client — `read()` system call
| Failure | Explanation |
| --- | --- |
| **Server business logic → Access denied** | Server reads request and refuses (401/403) |
| **Network issue → Read timeout** | Nothing arrives within the deadline; the work may or may not have been done |
| **Rate limit** | 429 Too Many Requests (often with Retry-After) |
| **Server-side errors** | 5xx |
| **Server dropping connection silently** | Read returns 0 (EOF) / ECONNRESET; idle-timeout on LB/NAT dropped the connection |

### 6. CDN
| Failure | Explanation |
| --- | --- |
| **DNS anycast** | Wrong/unhealthy PoP chosen by BGP; routing changes mid-connection |
| **Bad server — configuration / overwhelmed** | e.g. **Fastly 8 Jun 2021: one config change → 85% of the network errors, 49 min** (S6) |
| **Stale information → bug / configuration** | Cache serving wrong/old content (poisoning, bad TTLs, stale playlists in S8) |
| **All the other TCP errors discussed above** | Every connect/read/write failure applies to the CDN's own hops |
| **Same errors between edge and tiers** | Edge → shield/mid-tier leg can fail |
| **Same errors between mid-tier and origin** | Mid-tier → origin leg can fail |

### 7. SSL / TLS
| Failure | Explanation |
| --- | --- |
| **Invalid certificate** | Expired (the 3 a.m. outage, S1), wrong hostname, untrusted CA chain |
| **Protocol mismatch → TLS 1.1 / TLS 1.2 — TLS 1.3** | Client and server support no common version |
| **Protocol mismatch → Cipher mismatch** | No common cipher suite |
| **SSL pinning mismatch** | App pinned a specific cert/key; server rotated it → app refuses (S1) |
| **Incorrect date/time on server/client** | Cert appears not-yet-valid or expired |
| **Underlying TCP timeout** | TLS runs on TCP; any TCP failure surfaces here |

### 8. HTTP
| Failure | Explanation |
| --- | --- |
| **HTTP protocol version error** | e.g. 505, h2 preface sent to an h1 server → 501 (S5), ALPN mismatch |
| **Business logic → incorrect / missing headers** | App-level validation (e.g. missing auth header, wrong content-type) |
| **Protocol requirements → incorrect / missing headers** | e.g. HTTP/1.1 without Host → **400** (S5) |
| **Error code → Auth failure → 401 / 407** | 401 Unauthorized (server), **407 Proxy Authentication Required** (proxy); or an error page response |
| **Error code → 4xx → 403 denied, 404 not found, 400** | Client errors — retrying the same request won't help |
| **Error code → 5xx → 502, 503, 504** | **502 Bad Gateway** (proxy got a bad response from upstream), **503 Service Unavailable** (overloaded/maintenance; may carry Retry-After), **504 Gateway Timeout** (upstream didn't answer in time) |
| **Error code → OPTIONS / preflight request fail → CORS** | Browser's **CORS preflight** (OPTIONS, S5) rejected → request never sent |
| **Read timeout (server / CDN)** | Proxy's upstream timeout (e.g. nginx `proxy_read_timeout`, ALB idle timeout both default **60 s**) |

## 7.2 The retry toolkit (concepts the course refers back to as "Week 7")

| Concept | What it means | Where it shows up in the course |
| --- | --- | --- |
| **Timeouts / deadlines** | Never wait forever; set connect, read, write timeouts | select's NULL timeout blocks forever (S3); "set a deadline, then retry with backoff" |
| **Retry with exponential backoff** | Wait longer after each failure (e.g. 1 s, 2 s, 4 s…) | S3; SYN retransmits; Wi-Fi CSMA/CA random backoff (S2) |
| **Jitter (full jitter)** | Randomise the wait so clients don't retry in sync | S8 poller uses ±20% jitter so 50M phones don't poll on the same second |
| **Retry storm** | Many clients retrying immediately amplify the outage | S8: 50M clients retrying S3 503 "Slow Down" without backoff |
| **Retry-After / 503 / 429** | Server tells you when to come back | S8 (S3 503 Slow Down) |
| **Idempotency** | Only safely retry operations that can repeat without harm | "The network is not a function call" — calls time out with work possibly done (S1 RPC); QUIC 0-RTT only for GET/HEAD (S5); MQTT QoS 1 duplicates → apply by version number (S8) |
| **Which errors to retry** | Retry transient ones (timeouts, refused, 502/503/504, 429 after Retry-After); **don't retry 400/401/403/404** | Mind map's 4xx vs 5xx split |
| **Fallback ≠ retry** | Try something *different* (another codec, CDN, rendition) | S8: "a codec fallback is not a retry" |
| **Circuit breaker** | After repeated failures stop calling a dependency for a while; fail fast; probe later | S6 teaser; S8 client failover between CDNs |
| **Failover** | Primary → backup (origin, CDN, region) | S6 Worker primary→backup; S8 multi-CDN, Content Steering |
| **Serve stale / stale-if-error** | When origin fails, the cache is the last thing standing | S4 `proxy_cache_use_stale`; S6 cf-cache-status STALE; S8 RFC 5861 |
| **Negative caching** | Cache errors briefly to shield a struggling origin | S8: 5xx for 1–2 s; 404 almost never |
| **Graceful degradation / "who decides worse"** | Give something worse than ideal instead of nothing | S8 ABR: a stall is worse than a lower rendition |
| **Thundering herd on recovery** | Everything reconnects/refills at once | S4 proxy_cache_lock, S6 collapsing/tiered cache, S8 reconnect storms |
| **Feature flags** | Turn features off at runtime to shed load | S6 teaser |

> **Quiz points — Session 7**
> - Know the 8 branches in order: socket → DNS → connect → write → read → CDN → SSL/TLS → HTTP.
> - socket(): out of descriptors → retry later. DNS: no mapping, timeout, misconfigured.
> - connect(): host unreachable, port not listening (RST/refused), client or server connection limits, no response to SYN (no server / drops / handshake failure / dial timeout), stale DNS IP.
> - write(): packet drop → write timeout, machine shutdown, path node down, rate limit (server closes/stops reading, content too large).
> - read(): access denied, read timeout, rate limit, server errors, silent drop.
> - CDN: anycast, bad/overwhelmed server, stale info (bug/config), and every TCP error on edge→tier and mid-tier→origin legs.
> - TLS: invalid cert, version/cipher mismatch, pinning mismatch, wrong clock, TCP timeout.
> - HTTP: version error, missing headers, 401/407, 400/403/404, 502/503/504, CORS preflight failure, read timeout.
> - Retry transient errors with exponential backoff + jitter; only idempotent operations; circuit breakers and failover; serve stale.

---

# SESSION 8 — Streaming Video at Large Scale

"It starts with a live cricket scorecard." **Every live stream is a scorecard with bigger bytes.**
```
GET /match/412/score.json        200 · 1,088 bytes   · every 15 s
GET /stream_1/index.m3u8         200 · 228 bytes     · every 4 s
GET /stream_1/seg_000008.ts      200 · 823,440 bytes · once
```
All 8 weeks show up in one system: one live match on fifty million phones.

## 8.1 The brief
- **25–45 s** between balls; an over every 4–5 minutes.
- **50 M** peak concurrent viewers; **20 M average** over a 4-hour match.
- Scorecard **4–5 KB JSON, ~1 KB gzipped**.
- **100 events a year**.

### Two families of delivery
| Non-persistent — *the client asks* | Persistent — *the server tells* |
| --- | --- |
| **Polling**: GET same URL every few seconds | **Long poll**: GET answered only when there's news |
| **Conditional GET**: 304 when nothing changed | **Server-Sent Events**: one response that never ends |
| **Caches**: nginx, then a CDN | **WebSockets**: HTTP upgrades into a two-way framed pipe |
| Any server, no memory of who asked | **Pub/Sub (MQTT)**: topics, broker, fan-out |
| | Plain binary socket (your own protocol) |
| Ordinary GETs → **stateless servers, cacheable, CDN can front it** | Every viewer holds a connection all match → **stateful servers, nothing a CDN can cache** |

### Polling
```js
let etag = null; const EVERY = 15_000;
async function poll() {
  const res = await fetch("/match/412/score.json", { headers: etag ? { "If-None-Match": etag } : {} });
  if (res.status === 200) { etag = res.headers.get("ETag"); render(await res.json()); } // 304 → keep
  const jitter = 0.8 + Math.random() * 0.4;   // ±20%
  setTimeout(poll, EVERY * jitter);
}
```
- ETag + If-None-Match → 304 with empty body (the request still happens).
- **Jitter ±20%** so 50M phones don't poll in the same second.
- Freshness at worst = **one poll interval + every cache TTL on the path**.

### Long polling
- `GET /match/412/score?after=1841` → server holds until ball 1842 or **25 s** → returns `{"version":1842,...}` → client asks again at once.
- A held request is a held socket: **W is 25 s, not 30 ms** (Little's Law).
- **Answer before idle timeouts**: nginx `proxy_read_timeout` and ALB idle timeout both default **60 s**.
- **Synchronises the herd**: a wicket completes 20M responses in one second → 20M new requests next second.
- Came back standardised: **LL-HLS blocking playlist reload = long polling**.

### Server-Sent Events (SSE)
```
GET /match/412/events   Accept: text/event-stream   Last-Event-ID: 1841
HTTP/1.1 200 OK   Content-Type: text/event-stream
retry: 5000

id: 1842
event: ball
data: {"over":"15.4","runs":4,"total":"146/4"}

```
- **Framing by delimiter** — an event ends at a **blank line** (SMTP's lone dot in another costume).
- **Resume**: on reconnect browser sends **Last-Event-ID**; server replays only what was missed. `retry:` sets reconnect delay.
- **~6 per browser over HTTP/1.1** (each tab its own connection); HTTP/2 multiplexes them on one.
- **One way only** (server → client).

### WebSockets
```
GET /live HTTP/1.1
Upgrade: websocket   Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==   Sec-WebSocket-Version: 13

HTTP/1.1 101 Switching Protocols
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```
- **Accept = base64(SHA-1(key + a fixed GUID))**.
- Frame: byte 1 **FIN · RSV · opcode** (text, binary, ping, pong, close); byte 2 **MASK · length** (0–125 = length; **126 → 16-bit extended length, 127 → 64-bit**); extended length 0/2/8 bytes; **masking key 4 bytes on every client→server frame**; payload.
- **Length-prefixed, not delimited** (the other framing answer).
- **Client frames are masked** so stray bytes can never look like a request to a caching proxy (cache poisoning defence).

### MQTT — publish once, fan out
- `CONNECT client=phone-8812 keepalive=60` → CONNACK → `SUBSCRIBE match/412/score qos=1` → SUBACK → `PUBLISH match/412/score retain=1 {...}` → `PINGREQ C0 00` / `PINGRESP D0 00` (two bytes each keepalive).
- **Retained message**: broker keeps the last score and gives it to every new subscriber immediately — a cache inside the broker.
- **QoS 1 = at-least-once** → duplicates happen; apply updates by **version number** so duplicates are harmless.
- **Remaining Length is a varint**: 7 bits per byte, top bit = "more" (TLV).
- Keepalives wake the phone's radio and keep the **NAT mapping** alive.
- **Hotstar chose MQTT with the EMQX broker**.

### How Hotstar held 50 million sockets (Hotstar Engineering blog, 6 June 2019)
1. **One node**: EMQX on one **c5.4xlarge → 250k connections**.
2. **A cluster**: publisher split from subscribers → **2M**; **Mnesia** wants < 10 nodes.
3. **The ELB wall**: drops at ~500k without **pre-warming**; **4M per pre-warmed Classic ELB**.
4. **Five clusters**: 5 × 8 subscribe nodes, bridged → past 10M.
5. **Reverse bridge**: a Go service on each subscriber pulls from the publisher → **200 nodes: 50M**.
"Caching at any level is also not possible" — their **social feed** was tied to live moments, so it had to be pushed. A scorecard is the opposite: one file, identical for everyone.

## 8.2 What it costs

### A held socket's cost
- **Machines**: stateful — each phone lives on one box for hours; **100k–200k connections per box** (Hotstar 250k); new boxes sit empty until reconnects → rebalancing = disconnecting people.
- **Memory**: kernel socket buffers, TLS state, broker per-client process — **250k phones on 32 GiB ≈ 137 KB each**; soft `ulimit -n` still 1024.
- **Network**: keepalives with nothing to say — 60 s keepalive × 20M idle phones = **333k pings/s** before the first ball.
- **Load balancers**: one address, even spread — but the LB holds every socket too (4M per Classic ELB).
- **Testing**: one client IP has **28,232 ephemeral ports (32768–60999)** per destination → 250k test sockets need **≥ 9 source IPs**.

### Little's Law, twice (L = λ × W)
| Polling through a CDN | Push over held sockets |
| --- | --- |
| 1.67M req/s × ~0.03 s at the edge = **50,000 in flight** | W = whole match (4 h) → **50,000,000 sockets held** |
**1000× the concurrency** for the same audience, because W went from ms to hours.

### Where the scorecard lives
Own servers (ELB → nginx × N in memory ← NFS/NAS ← writer) · Object store with no cache (every poll is a bucket GET) · **Through a CDN (edge + mid-tier absorb polls; bucket sees a few per TTL)**.

### The arithmetic before the architecture (poll every 30 s)
- requests/match = 20M × 14,400 s ÷ 30 s = **9.6 B**
- peak rate = 50M ÷ 30 s = **1.67M req/s**
- bytes/match = 9.6 B × 1 KB = **9.6 TB**
- poll every 15 s → 19.2 B requests, 3.33M req/s, 19.2 TB
- push each ball → ~9.6 B messages (one every ~30 s per phone)
- × 100 events → 960 B requests, 960 TB a year

### Four ways to pay for one match (AWS list prices, Sep 2026)
| Design | Per match | × 100 events | Mostly paying for | Breaks first |
| --- | --- | --- | --- | --- |
| S3 straight to phones | $4.7K | $470K | GET fees ($3,840) | **5,500 GET/s per prefix** |
| nginx fleet + ALB | $1.2–1.8K | $120–180K | egress ($864) + LB units | 20–50M idle keep-alive sockets at the LB |
| CDN (CloudFront India) | **$12.5K** | $1.25M | **request fees: 92%** | nothing — it's just the bill |
| Push: 200 × c5.4xlarge | **$0.9–1.6K** | $90–160K | peak-sized fleet + egress | reconnect storms, rebalancing |
At list price **push is cheapest per match, CDN dearest**.

### S3 runs out of requests before money
S3 promises **≥ 5,500 GETs/s per prefix**; 50M phones polling every 30 s ask **1.67M/s** → **303× over**. "You may see some **503 (Slow Down)** errors" → 50M clients retrying without backoff = Session 7's **retry storm** at your own bucket.

### Billed per request vs per byte
CloudFront India: **HTTPS $0.0120 per 10,000 requests** ($1.20/million); **$0.109/GB** (after 1 free TB; $0.072/GB past 5 PB).
- Scorecard 1 KB: $1.20 request fee vs $0.11 bytes per million → **92% of the scorecard's CDN bill is request fees**.
- 480p segment 823 KB: $1.20 vs $59–90 → bytes dominate.
- **Break-even ≈ 11 KB**: below it you pay per request (scorecard, playlist 228 B); above it per byte (segments 459 KB–1.6 MB).

### Why the lecturer prefers polling here
**Cacheable** (one file identical for 50M) · **Stateless** (any server/edge/CDN answers) · **Already paid for** (scorecard = **0.28%** of the match's video bill). "I prefer polling because I want to tell you how it's used for video too."

## 8.3 Making polling survive

### Conditional GET → 304
`If-None-Match: "v1841"` → `304 Not Modified`, `ETag: "v1841"`, `Cache-Control: public, max-age=10`.
- **Saves:** the 1 KB body, JSON parse, re-render. **Doesn't save:** the request fee, round trip, headers.
- Make the **ETag = the scorecard's version number** (fingerprint, not clock). If-Modified-Since only to the second.
- **Pays most between CDN tiers** (edge→mid-tier→origin: 304s instead of copies).

### TTLs add up
- Every layer 30 s (mid-tier 30 + edge 30 + client poll 30) → **up to 90 s stale** (2–3 balls behind).
- CDN TTLs 5 s + 5 s + poll 15 s → **up to 25 s** (inside one ball).
- **Worst-case staleness = poll interval + every cache TTL on the path.** Keep each CDN TTL ≤ **½ the promised freshness**; refresh before expiry — **prefetch at ~25 s of a 30 s TTL (Akamai "prefresh")**.

### The thundering herd at expiry — four fixes
1. **Request collapsing** — one fetch per edge per object; others queue (`proxy_cache_lock on`).
2. **Serve stale while updating** — RFC 5861 (stale-while-revalidate / stale-if-error) (`proxy_cache_use_stale updating …`, `proxy_cache_background_update on`).
3. **Prefetch before expiry** — refresh at ~25 s of 30 s.
4. **Jitter from the client**.
```nginx
proxy_cache_lock on;
proxy_cache_use_stale updating error timeout http_500 http_502 http_503 http_504;
proxy_cache_background_update on;
proxy_cache_valid 200 10s;
```

### Collapsing needs a shareable answer
20,000 phones ask one edge in the same 50 ms → edge sends 1 upstream; origin sees 1.
- **The first response decides**: `Cache-Control: public` releases every waiter at once; a **private answer or stray Set-Cookie dequeues them one by one**, and **Fastly then skips collapsing for that object for 2 minutes**.
- **Early hints**: HTTP **103** for pages; in LL-HLS a **preload hint** names the next piece; requests queue at the edge; one arrival releases all.
- Check defaults: **Cloudflare doesn't cache .json** out of the box → `DYNAMIC`, every poll reaches you.

### Negative caching
- **5xx — cache it briefly**: 1–2 s of a cached 503 shields a struggling origin from 50M retries (one probe per TTL per edge).
- **404 — almost never**: a 404 for a file about to exist (next match, newest live segment) keeps being served; **Cloudflare default 404 TTL = 3 min**.
```nginx
proxy_cache_valid 200 10s;
proxy_cache_valid 404 1s;
proxy_cache_valid 500 502 503 504 2s;
```
**Rule: a negative TTL must be far shorter than the time the missing thing takes to appear.**

### Send diffs, not the whole card
Full JSON **4,117 B** → gzipped **1,088 B** → one ball as gzipped **JSON Patch 183 B**.
- **Push**: SSE/MQTT carry the 183-byte patch; a phone that sees a **version gap** fetches the full card once.
- **Pull**: `?since=1841` gives every client its own URL → **hit rate collapses**. Instead publish **one file with the version + the last few changes**.

### A versioned scorecard IS a playlist
| score.json (polled 15 s) | index.m3u8 (polled 4 s) |
| --- | --- |
| `version` | `#EXT-X-MEDIA-SEQUENCE` |
| `recent` changes | the last N segments |
| poll interval | `#EXT-X-TARGETDURATION` |
"A small index everyone polls, pointing at numbered pieces that never change. That design has a name: **HTTP Live Streaming (HLS)**."

## 8.4 Same loop, bigger bytes — HLS
Scorecard 1 KB/15 s · playlist 228 B/4 s · one 4 s 480p segment 823 KB, fetched once. Demo: Big Buck Bunny / Tears of Steel on videojs.org with DevTools; throttle → rendition changes.

### HLS in one picture (control vs data)
1. **master.m3u8** — once (CONTROL): the menu of renditions (bandwidth, resolution, codecs).
2. **stream_1/index.m3u8** — every target duration, 4 s (CONTROL): last 10 segments; changes every 4 s.
3. **stream_1/seg_000011.ts** — each new one (DATA): 4 s of audio+video, 823 KB, **never changes**.
4. Player plays from the buffer; **switches rendition when throughput changes**.

### Master playlist
```
#EXTM3U
#EXT-X-VERSION:6
#EXT-X-STREAM-INF:BANDWIDTH=3440800,RESOLUTION=1280x720,CODECS="avc1.4d401f,mp4a.40.2"
stream_0/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1755600,RESOLUTION=854x480,CODECS="avc1.4d401f,mp4a.40.2"
stream_1/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=950400,RESOLUTION=640x360,CODECS="avc1.4d401e,mp4a.40.2"
stream_2/index.m3u8
```
- **BANDWIDTH = (video + audio) × 1.1** → (3000k + 128k) × 1.1 = 3,440,800.
- Doesn't change during the match → fetch once, cache for minutes. **Some players re-poll it to switch CDNs** → standardised as **Content Steering**.
- **CODECS** lets the player skip what it can't decode (e.g. HEVC → H.264): **a fallback, not a retry**. (avc1 = H.264, mp4a.40.2 = AAC-LC.)

### Media playlist, polled (RFC 8216 §6.3.4)
Reload at t=47.0 s: MEDIA-SEQUENCE 1, seg_000001…seg_000010; at t=51.5 s: MEDIA-SEQUENCE 2, seg_000002…seg_000011. Each segment has `#EXTINF:4.000000,` and `#EXT-X-PROGRAM-DATE-TIME` (wall clock).
- **Changed?** wait **at least one target duration** before reloading.
- **Unchanged?** wait **half a target duration**, then retry.
- **Same number, different URI?** "It SHOULD halt playback."

### VOD = a playlist that stopped changing
`#EXT-X-TARGETDURATION:10`, 63 × 10 s + 5 s segments, ends with **`#EXT-X-ENDLIST`** → read once, stop polling. 10 s segments = old advice; **Apple now says 6 s**. Query `?pubId=…&videoId=…` is the same for everyone so it caches; a **per-viewer token would not** (query is in the cache key).

### A segment is 188-byte packets (MPEG-TS)
- **4-byte header** (**sync byte 0x47**, **13-bit PID**, continuity counter) + **184-byte payload** (video, audio, or PAT/PMT tables).
- **Fixed length + sync byte = both framing answers at once.** **188 chosen for ATM.**
- PID says whose packet it is — audio, video, tables share one byte stream (multiplexing).
| Rendition | Segment | 188-B packets | Overhead |
| --- | --- | --- | --- |
| 720p | 1,613,416 B | 8,582 | 3.3% |
| 480p | 823,440 B | 4,380 | 4.1% |
| 360p | 452,328 B | 2,406 | 5.6% |
- **fMP4 / CMAF** segments are **boxes** (size, type, payload) = TLV again.

### How long should a segment be? (50M viewers)
| Segment | Peak segment requests | Latency floor (3×) |
| --- | --- | --- |
| 2 s | 25 M/s | 6 s |
| 3 s | 16.7 M/s | 9 s |
| **4 s** | 12.5 M/s | 12 s (our ffmpeg run) |
| **6 s** | 8.3 M/s | 18 s (**Apple's advice**) |
| 30 s | 1.7 M/s | 90 s ("too late!") |
- Shorter: more requests, more keyframes, more round trips. Longer: more latency, slower bandwidth reaction.
- **Adaptive/hybrid**: 1–2 s segments at start-up for fast first frame: `-hls_init_time 1 -hls_time 4`.

### Playlist traffic is harder than segment traffic
| | Media playlist | Segment |
| --- | --- | --- |
| Size | ~230 B gzipped | 450–1,600 KB |
| Changes | every 4 s | never |
| Cache TTL | ≤ ½ target duration | minutes to forever |
| Stale copy | **stalls, or points at deleted files** | harmless |
| Billed by | requests | bytes |
Polling every 1 s = 50M req/s at peak; at one target duration (RFC) = 12.5M.

## 8.5 Buffers and latency

### The buffer — "the buffer is the stale cache"
- **Large buffer**: survives a bad minute on a train; costs latency and memory on low-end phones/TV sticks.
- **One-segment buffer**: lowest latency; one slow segment → stall.
- More bandwidth → smaller buffer suffices. When the playlist stops moving, the buffer keeps the picture going.

### Latency is a budget
encode **~2 s** + segment fills **4 s** + to CDN **~2 s** + **player hold-back = 3 × target duration = 12 s** → **~20 s behind the stadium** with 4 s segments.
**Low-Latency HLS (LL-HLS)** — four ideas from earlier weeks:
| Idea | What |
| --- | --- |
| **Parts** | ~1 s pieces of a segment (Apple: ≥ 3× the P95 round trip) |
| **Blocking playlist reload** | `?_HLS_msn=…` held until that segment exists = **long polling** |
| **Preload hints** | Name the next part early — **replaced HTTP/2 push (Jan 2020)** |
| **Delta updates** | **`EXT-X-SKIP`** drops old entries — diffs for playlists |
With 1 s parts, 12 s hold-back → **~3 s** (Apple: **PART-HOLD-BACK ≥ 3 parts**).

### The spoiler problem
Wicket at 0 s → scorecard shows "W" at **~10 s** → video shows it at **~20 s** → **10 s spoiler window**.
Fix: **stamp each update with the ball's wall-clock time** (`"at": "2026-09-27T03:16:44.1Z"`); the player knows each segment's `#EXT-X-PROGRAM-DATE-TIME` → reveal the update only when playback passes it.

### ABR (Adaptive Bitrate) — the player picks the next rendition
"Who decides 'worse'?" → **the player, at every segment, under a policy the product sets**.
- **Throughput-based**: measure how fast recent segments arrived; pick highest rendition that fits — "congestion control, one layer up".
- **Buffer-based**: buffer nearly empty → step down; full → step up. **Netflix A/B tests: 10–20% fewer rebuffers** at similar video rate (Huang et al., SIGCOMM 2014).
- Policy: **a stall is worse than a lower rendition**. Apple suggests starting **cellular at 730 kbps**, **Wi-Fi at 2 Mbps**.

## 8.6 Many origins, many CDNs
Android app → CDN A (primary) edge → CDN A mid-tier → Origin 1 (packager A); fallback CDN B → mid-tier → Origin 2 (packager B); same segment names.
| Mechanism | How | Trade |
| --- | --- | --- |
| **DNS** | Hand out a CDN per region/ISP | Slow to change — resolvers cache |
| **Listed twice** | Master lists each rendition once per CDN | Stream failover |
| **Content Steering** | JSON file polled every TTL names the preferred CDN | Standardised re-polling |
| **Client failover** | Errors on one CDN **trip a circuit breaker**; next segment tries the other | Session 7 |

### Stale playlists and deleted segments (stale-if-error, with a catch)
1. ffmpeg's `delete_segments` keeps only one unreferenced segment — seg_000000 vanished 4 s after leaving the playlist.
2. **RFC 8216: a removed segment MUST stay available for its duration + the playlist's duration** → 4 + 40 = **44 s**.
3. During an origin blip the CDN serves a **stale playlist** listing a segment the origin already deleted.
4. → **404, negatively cached → player stalls**. "Serve stale may cause player issues."
**Fixes:** `-hls_delete_threshold 12`; playlist TTL ≤ ½ target duration, serve stale for **one target duration at most**; segments never change → serve stale freely; Apple: treat a playlist as **invalid when Last-Modified is > 3 target durations behind Date**.

### Caching rules for a live stream
| Object | TTL | Serve stale | 404 TTL |
| --- | --- | --- | --- |
| master.m3u8 | minutes | yes | 1 s |
| media playlist | ≤ ½ target duration | one target duration max | 1 s or none |
| segment .ts | long (never changes) | yes | ≤ 1 s at live edge |
| score.json | ≤ ½ your promise | while updating | 1 s (5xx 2 s) |
```nginx
location ~ \.m3u8$ { proxy_cache_valid 200 2s; proxy_cache_lock on; proxy_cache_use_stale updating; }
location ~ \.ts$   { proxy_cache_valid 200 10m; proxy_cache_valid 404 1s; }
gzip_types application/vnd.apple.mpegurl application/json;
```
Also: **gzip every playlist (Apple: MUST)**; **keep per-viewer tokens out of the cache key**.

## 8.7 Making the stream (ffmpeg)

### One-liner from an mp4
```
ffmpeg -re -i input.mp4 -codec: copy -hls_time 4 -hls_list_size 5 -hls_playlist_type event -f hls index.m3u8
```
| Flag | Meaning |
| --- | --- |
| `-re` | Read at native speed — a file pretending to be a camera |
| `-codec: copy` | No re-encode → can only cut at existing keyframes |
| `-hls_time 4` | Target segment length — **not a promise** |
| `-hls_list_size 5` | 5-segment window, unless… |
| `-hls_playlist_type event` | …playlist is **append-only** (window ignored) |
What running it showed: **8.33 s segments, not 4** — x264's default keyframe interval is **250 frames = 8.33 s at 30 fps**; EVENT playlist only grew (11 segments listed).
Real pipeline: **camera → RTMP or SRT → transcoder → packager → origin → CDN**.

### The ABR ladder
- `split=3`: **decode once, encode three times** (1280×720, 854×480, 640×360); `asplit=3` for audio.
- `-c:v libx264 -preset veryfast -profile:v main -sc_threshold 0 -g 120 -keyint_min 120` → **keyframe every 120 frames = 4 s at 30 fps only** (a 24 fps source gave **5 s** segments). `-sc_threshold 0` disables scene-cut keyframes.
- Bitrates: 720p **3000k** (maxrate 3210k, bufsize 4500k, audio 128k) · 480p **1500k** (96k audio) · 360p **800k** (64k audio). AAC stereo 48 kHz.
- `-hls_time 4 -hls_list_size 10 -hls_flags independent_segments+delete_segments+omit_endlist+program_date_time` → **a 40 s window that never ends, stamped with wall-clock time**.
- `-hls_segment_filename "out/stream_%v/seg_%06d.ts" -master_pl_name master.m3u8 -var_stream_map "v:0,a:0 v:1,a:1 v:2,a:2"`.
- Homework: prove 24 fps → 5 s segments; switch to time-based keyframes (`force_key_frames`) → 4 s.

## 8.8 The whole course in one cricket match
| Week | Shows up as |
| --- | --- |
| 1 Sockets | 16-bit ports → 28k test sockets per client IP; base64 in the WebSocket handshake |
| 2 Wire | Framing: SSE blank line, WebSocket lengths, 188-byte packets; playlists = control, segments = data |
| 3 Scale | 50M held sockets, Little's Law, nothing free per connection |
| 4 nginx | proxy_cache_lock, use_stale, one location per file type |
| 5 HTTP | ETag & 304, keep-alive, 101 Upgrade, push's death shaping LL-HLS |
| 6 CDNs | Tiers, collapsing, negative caching, paying per request vs per byte |
| 7 Failures | Jitter, the live-edge 404, stale-if-error, failover, who decides "worse" |
| 8 Video | HLS: a playlist polled like a scorecard, pointing at bytes that never change |

### Four ideas to keep
1. **Pull scales through caches; push scales through machines.** Same answer for everyone → CDN. Different answer per person → you're buying sockets.
2. **Number the pieces, then cache them forever.** Small changing index + immutable numbered pieces (versioned scorecard = HLS playlist).
3. **Latency is a budget you spend on safety.** Poll intervals, TTLs, segment length, hold-back all add up.
4. **Know which bill you're on.** Below ~11 KB you pay per request (scorecards, playlists); above it per byte (segments).

Assignment: nginx origin + nginx mid-tier cache + 1,000 simulated viewers → (1) origin RPS with proxy_cache_lock off/on; (2) staleness per ball at 30 s vs 5 s TTL; (3) break it with `hls_delete_threshold 1`, catch the 404s, fix; (4) spoiler — hold updates until PROGRAM-DATE-TIME passes.

> **Quiz points — Session 8**
> - 50M peak, 20M avg, 4-hour match; scorecard ~1 KB gzipped; 100 events/year.
> - Polling (stateless, cacheable) vs persistent (long poll, SSE, WebSocket, MQTT, raw socket — stateful, not cacheable).
> - Jitter ±20%. Staleness = poll interval + sum of TTLs; CDN TTL ≤ ½ promise; prefresh.
> - Long poll ~25 s; beat 60 s idle timeouts; LL-HLS blocking reload = long poll.
> - SSE: text/event-stream, blank-line delimiter, Last-Event-ID, retry:, ~6/browser on h1.
> - WebSocket: 101 Switching Protocols, Accept = base64(SHA-1(key + GUID)), length 126/127 extended, client frames masked.
> - MQTT: retained message, QoS 1 at-least-once, PINGREQ C0 00, varint length; Hotstar + EMQX, 250k/node, ELB 4M, 50M on 200 nodes (2019).
> - Little's Law: polling 50k in flight vs push 50M sockets.
> - 9.6 B requests/match, 1.67M req/s peak, 9.6 TB. S3 5,500 GET/s per prefix → 503 Slow Down.
> - CDN cost: 92% request fees for 1 KB; break-even ~11 KB. Push cheapest, CDN dearest at list price.
> - Negative caching: 5xx 1–2 s; 404 ~never (1 s); Cloudflare 404 default 3 min.
> - JSON Patch diff 183 B vs 1,088 B gzipped.
> - HLS: master (once) → media playlist (every target duration) → segments (once). EXT-X-TARGETDURATION, MEDIA-SEQUENCE, EXTINF, PROGRAM-DATE-TIME, ENDLIST (VOD), STREAM-INF BANDWIDTH = (v+a)×1.1.
> - Reload: changed → ≥ 1 target duration; unchanged → ½.
> - MPEG-TS: 188-byte packets, sync 0x47, 13-bit PID, 4-byte header; chosen for ATM. fMP4/CMAF = boxes.
> - Segment length trade-off; Apple 6 s; latency floor 3× segment.
> - Latency ≈ 20 s with 4 s segments; LL-HLS parts, blocking reload, preload hints, EXT-X-SKIP → ~3 s.
> - Spoiler fix: wall-clock stamp + PROGRAM-DATE-TIME.
> - ABR: throughput-based vs buffer-based (Netflix 10–20% fewer rebuffers); stall worse than lower quality.
> - Multi-CDN: DNS, listed twice, Content Steering, client failover with circuit breaker.
> - Removed segment must remain duration + playlist duration (44 s). Apple: playlist invalid if Last-Modified > 3 target durations old.
> - ffmpeg: -re, -codec copy cuts at keyframes; x264 default GOP 250 → 8.33 s; -g 120 = 4 s @30 fps; split=3 decode once encode thrice.

---

# FINAL REVISION — Cheat Sheet, Numbers, Traps, Practice Questions

## A. Numbers to memorise
| Number | What |
| --- | --- |
| 7 | syscalls for a TCP server (socket, bind, listen, accept, read, write, close) |
| 1024 | privileged-port boundary; FD_SETSIZE; default `ulimit -n`; the "K" in C10K |
| 32768–60999 | Linux ephemeral port range (28,232 ports) |
| ~60 s | TIME_WAIT (2 MSL) |
| 13 / 9 / 15 / 2 | SIGPIPE / SIGKILL / SIGTERM / SIGINT |
| 0x07EA | 2026 in hex; wire order `07 EA` |
| 1500 / 1460 / 1518 | MTU / MSS / full Ethernet frame |
| 20 / 20 / 8 | IPv4 header / TCP header / UDP header (bytes) |
| 6 / 17 / 132 | IP protocol numbers TCP / UDP / SCTP |
| 0x0800 | EtherType IPv4 |
| 140 / 160 / 70 / 272 | SMS octets / GSM-7 chars / UCS-2 chars / SS7 SIF limit |
| 64 kbps | DS0 voice channel |
| 2600 Hz | blue-box in-band tone |
| ~2 ms | Wi-Fi contention delay; ~20 ms / 550 km to Starlink LEO |
| 1 / 3 / 2 / 1 / 0 RTT | TCP / +TLS1.2 / +TLS1.3 / QUIC / QUIC 0-RTT before data |
| ~190 ms | Mumbai–Virginia RTT (lecture 2); 126 ms theoretical floor (lecture 6) |
| 33% | base64 overhead (3 bytes → 4 chars); 76 chars/line MIME |
| 8 MB vs 2 KB | thread stack vs goroutine stack |
| 80 GB | 10,000 threads' stacks |
| 10k / 10M / 2–3M | C10K (Kegel 1999) / C10M (Graham 2013) / today |
| 7/8 | nginx accept_disabled threshold |
| ~8,000 | cache keys per MB of keys_zone |
| 11 | nginx HTTP phases; 27 request-line parser states |
| 8 | FastCGI record header bytes |
| 24 | bytes in the HTTP/2 connection preface |
| 9 | HTTP/2 frame header bytes (24/8/8/1+31 bits) |
| 10 | HTTP/2 frame types |
| 61 / 99 | HPACK / QPACK static table entries |
| 4096 / 65535 / 16384 | HTTP/2 default header table / initial window / max frame size |
| 174 → 79 → 6 | HPACK bytes: text / first / repeat |
| 97.5% | repeated header bytes in HTTP/1.1 |
| 2.8% | gzip size of the demo text file |
| 40 ms | delayed-ACK wait |
| 6 / 18 | browser connections per origin / with domain sharding |
| 62 | IANA-assigned status codes (Sep 2025) |
| 3–5% | networks that block UDP |
| ~85% / ~15% | requests on HTTP/2+ / HTTP/1.1 |
| ~204,000 km/s, 4.9 ms/1000 km | light in fibre |
| 90.9% vs ~1/11 | URLs moved: modulo vs consistent hashing (adding 11th cache) |
| 160 | virtual points per server (nginx consistent hash) |
| 68 | Cloudflare default-cached extensions |
| 2 h / 3 min | Cloudflare default TTL for 200/301 / 404 |
| 87.1% → 99.92% | Pingora connection reuse |
| 31.4 Tbps | largest DDoS (Dec 2025) |
| 85%, 49 min | Fastly outage, 8 Jun 2021 |
| ~5 ms, ~3 MB | Cloudflare Worker isolate start / memory |
| 50M / 250k / 4M | Hotstar peak / per EMQX node / per Classic ELB |
| 1.67M req/s, 9.6 B, 9.6 TB | scorecard peak rate / requests / bytes per match |
| 5,500 | S3 GET/s per prefix |
| ~11 KB | CDN per-request vs per-byte break-even |
| 188 / 0x47 / 13 bits | MPEG-TS packet / sync byte / PID |
| 3× target duration | HLS hold-back; ~20 s latency with 4 s segments |
| 44 s | removed segment availability (4 + 40) |
| 250 frames | x264 default GOP (8.33 s @ 30 fps) |

## B. Timeline
| Year | Event |
| --- | --- |
| 1971 | FTP (active mode) |
| 1975 | SS7 (out-of-band signalling) |
| 1983 | select() |
| 1984 | OSI model, ASN.1, Nagle (RFC 896) |
| 1990 | CERN httpd (Berners-Lee, NeXT) |
| 1993 | NCSA Mosaic (browser), NCSA HTTPd (Rob McCool, CGI) |
| 1994 | SSI (NCSA HTTPd 1.0a1) |
| 1995 | Apache |
| 1996 | HTTP/1.0 (RFC 1945); SYN cookies; Squid; Apache becomes #1 |
| 1997 | HTTP/1.1 (RFC 2068); consistent hashing (Karger); Mathis formula; Servlets |
| 1998 | Akamai; RFC 2324 (418 teapot) |
| 1999 | RFC 2616; C10K (Dan Kegel); J2EE |
| 2001 | HAProxy; ESI |
| 2002 | epoll (Linux 2.5.44); Sysoev starts nginx |
| 2003 | Cross-Site Tracing |
| 2004 | nginx public release (4 Oct) |
| 2005 | Ajax |
| 2006 | Varnish |
| 2008 | CloudFront; browsers at 6 connections/origin |
| 2009 | SPDY |
| 2010 | Cloudflare |
| 2011 | Fastly; nginx 1.0; bufferbloat |
| 2012 | CRIME; Apache event MPM |
| 2013 | C10M (Robert Graham); Railgun |
| 2014 | RFC 7230–7235; ALPN (RFC 7301) |
| 2015 | HTTP/2 (RFC 7540) + HPACK (RFC 7541) |
| 2016 | BBR; SPDY removed (Chrome 51); Alt-Svc (RFC 7838) |
| 2017 | HAProxy multi-threaded (1.8); cache deception (Gil); Cloudflare sliding-window rate limit |
| 2018 | cache poisoning (Kettle); domain fronting banned (AWS, Google); Workers |
| 2019 | Hotstar 50M MQTT; CloudFront & Akamai adopt BBR |
| 2020 | LL-HLS preload hints replace push (Jan) |
| 2021 | Fastly outage (8 Jun) |
| 2022 | RFC 9110–9114; Chrome 106 drops push; Pingora; Google Media CDN |
| 2023 | HTTPS DNS RR (RFC 9460) |
| 2024 | Railgun retired; Fastly bans domain fronting |
| 2025 | RFC 9842 dictionary transport; Cloudflare FL2 (Rust); 31.4 Tbps DDoS |

## C. Classic traps
1. **`listen(fd, N)`'s N is the accept-queue depth, not a connection limit.**
2. **No listener → "refused" (RST). Listening but never `accept()` → hang** (the kernel already completed the handshake).
3. **Clients don't call bind()**; the kernel picks an ephemeral port at connect().
4. **`ulimit -n 65536` does not fix select()**: FD_SETSIZE is a compiled bitmap width.
5. **SSL/TLS secures TCP, not HTTP.** It works for any protocol on a socket.
6. **SYN+ACK can be combined; FIN+ACK cannot.** That is why opening takes 3 segments and closing takes 4.
7. **CLOSE_WAIT piling up = your app forgot close()**, not a network problem.
8. **Wi-Fi = CSMA/CA (avoid). Ethernet = CSMA/CD (detect).**
9. **SS7 is reliable per hop; TCP is reliable end to end.**
10. **Mosaic was a browser, not a server.** CGI came from NCSA HTTPd.
11. **nginx `location` precedence ignores file order** except among regexes (first match wins). `^~` beats regex. `=` beats all.
12. **`inactive` ≠ `proxy_cache_valid`.** One evicts unread entries; the other sets freshness.
13. **`proxy_cache_lock` is off by default.**
14. **`sendfile` and `gzip` conflict**, because gzip has to touch the bytes.
15. **HTTP/1.0 has no true head-of-line blocking**, only a serialisation cost. HOL blocking came with HTTP/1.1 pipelining.
16. **`no-cache` = revalidate before use; `no-store` = never store.**
17. **302 vs 307:** browsers turn POST into GET on 302. 307 keeps the method.
18. **The RFC never deprecated server push.** Only PRIORITY and h2c Upgrade were deprecated. Chrome removed push anyway.
19. **HTTP/2 fixes HTTP-level HOL blocking but not TCP-level HOL blocking.** QUIC fixes TCP's.
20. **QUIC runs over UDP because middleboxes drop unknown protocols**, not because UDP is a good base.
21. **0-RTT data can be replayed.** Use it for idempotent requests only.
22. **A CDN cache MISS is no faster than going direct.** The wins are warm pools and HITs.
23. **CDNs don't cache HTML/JSON by default.** The default cache key ignores cookies.
24. **A WAF does not fix SQL injection.** Parameterised queries do.
25. **Fixed-window rate limits allow 2× bursts at the boundary.**
26. **Rate-limit counts are per colo**, not global.
27. **An edge gateway is useless if the origin IP is reachable.**
28. **304 saves bytes, not the request fee or the round trip.**
29. **Negative-cache 5xx briefly. Almost never cache 404s at the live edge.**
30. **`-hls_time` is a target, not a promise.** Segments are cut at keyframes.
31. **With push, the CDN can't help.** Every viewer holds a socket.
32. **Retry only transient errors**, with backoff and jitter. Don't retry 4xx. A fallback is not a retry.

## D. Comparison tables (one line each)
- **fork vs thread vs event loop:** isolation vs cheaper vs scalable.
- **select vs poll vs epoll vs kqueue vs IOCP vs io_uring:** portable O(n) · no 1024 cap but O(n) · Linux O(ready) · BSD/macOS · Windows · batched ring.
- **CGI vs mod_php vs FastCGI vs Servlets vs Workers:** process per request · in-process (shared crash) · persistent pool over socket · JVM thread pool · V8 isolates at the edge.
- **Forward vs reverse proxy:** near clients (Squid) vs near servers (nginx, Varnish, CDN).
- **POP3 vs IMAP:** state on client vs state on server.
- **FTP active vs passive:** server dials the client (port 20) vs client opens both connections (PASV 227).
- **SSI vs ESI vs Ajax vs Railgun:** server vs edge vs browser assembly vs deltas.
- **Poisoning vs deception:** unkeyed header vs fake static extension.
- **Polling vs long poll vs SSE vs WebSocket vs MQTT:** client asks · held GET · one endless response · bidirectional framed · broker fan-out.
- **Throughput-based vs buffer-based ABR.**
- **TCP vs QUIC identity:** the 4-tuple vs a connection ID.

## E. Practice questions (answers below)
1. Which system calls does a TCP server make that a client never does?
2. A client gets "Connection refused" instantly. What happened at the TCP level?
3. Why does writing to a socket whose peer reset the connection kill the process, and what socket option sends an RST on close?
4. Convert port 30000 into the FTP PASV p1,p2 pair.
5. What is the MSS on a standard Ethernet link with IPv4 + TCP and no options?
6. Why can an SMS carry 160 characters in 140 bytes? How many with an emoji?
7. Name the ISUP messages to set up and tear down a call.
8. What does BBR measure instead of loss?
9. How do SYN cookies avoid storing state, and what do they cost?
10. Why does select() fail at descriptor 1024 even after raising ulimit?
11. State Little's Law. At 5,000 req/s and 200 ms latency, how many connections are in flight?
12. How does FastCGI mark the end of the PARAMS stream?
13. In nginx, which location handles `/images/a.php` given `^~ /images/` and `~ \.php$`?
14. With weights 3:1, what order does nginx's smooth WRR produce?
15. What does `proxy_cache_use_stale updating` do?
16. What two HTTP/1.0 problems did the Host header and persistent connections fix?
17. What's the difference between a weak and a strong ETag, and which do Range requests need?
18. Explain request smuggling in one sentence.
19. Why can HTTP/2 multiplex when HTTP/1.1 couldn't?
20. Why is HPACK safe from CRIME when gzip isn't?
21. What replaced HTTP/2 server push?
22. Why is QUIC built on UDP and encrypted almost entirely?
23. What lets a QUIC connection survive a Wi-Fi → LTE switch?
24. Why did HTTP/3 need QPACK instead of HPACK?
25. Give the formula for single-flow TCP throughput.
26. Why does modulo hashing hurt a CDN when you add a cache?
27. What are cf-cache-status REVALIDATED and DYNAMIC?
28. What does ESI improve, and what does it make worse?
29. Why did a single shared pool beat 32 per-worker pools?
30. Which rate-limit algorithm does Cloudflare use, and why not a fixed window?
31. Why must the origin be locked down when the edge does authentication?
32. List the failure branches of the Session 7 map in order.
33. Which HTTP errors are worth retrying, and how?
34. Why did Hotstar use push for its social feed, while the lecture prefers polling for the scorecard?
35. What is the worst-case staleness for a 15 s poll behind two 5 s CDN TTLs?
36. What HLS tag plays the role of the scorecard's version number?
37. Why are MPEG-TS packets 188 bytes, and what does the PID do?
38. Why did ffmpeg produce 8.33 s segments when asked for 4 s?
39. How does LL-HLS reach ~3 s latency?
40. How do you stop the scorecard from spoiling the video?

### Answers
1. bind, listen, accept.
2. Nothing was listening on the port, so the kernel answered the SYN with an RST.
3. The default action of SIGPIPE (signal 13) terminates the process. `SO_LINGER {1, 0}` makes close() send an RST.
4. 30000 = 117 × 256 + 48, so the pair is (117, 48).
5. 1500 − 20 − 20 = 1460 bytes.
6. GSM-7 uses 7-bit characters: 1120 bits ÷ 7 = 160. With UCS-2 it is 70.
7. Setup: IAM, ACM, ANM. Teardown: REL, RLC.
8. Bottleneck bandwidth and minimum round-trip propagation time.
9. It encodes the connection state in the server's ISN as a keyed hash of the 4-tuple, a timestamp and the MSS. The cost is losing most TCP options (window scaling, SACK, timestamps).
10. fd_set is a fixed 1024-bit bitmap (FD_SETSIZE), set at compile time.
11. L = λ × W, so 5,000 × 0.2 = 1,000 connections.
12. With an empty (length-0) PARAMS record.
13. The `^~ /images/` block. It suppresses the regex search.
14. a, b, a, a.
15. It serves the stale cached copy while one request refreshes it in the background.
16. One IP could only host one site, and every request needed its own TCP handshake.
17. Weak (`W/`) means equivalent; strong means byte-identical. Range requests need a strong one.
18. Two servers in a chain frame the same bytes differently (Content-Length vs Transfer-Encoding), so a hidden second request slips through.
19. Every frame carries a 31-bit stream ID. HTTP/1.1 had no request ID, so response order was the only identifier.
20. HPACK uses a fixed Huffman table and an exact-match index, not adaptive substring matching. Sensitive fields can also be marked "never indexed".
21. 103 Early Hints (RFC 8297), and preload hints in LL-HLS.
22. Middleboxes drop unknown IP protocols. Anything they can read, they end up depending on (ossification). Encryption keeps QUIC changeable.
23. Connection IDs, which identify the connection independently of the IP/port 4-tuple.
24. HPACK assumes all frames arrive in one total order. QUIC streams arrive out of order, so QPACK moves table updates to separate encoder and decoder streams.
25. Throughput ≈ MSS / (RTT × √loss).
26. About 90% of URLs move to a different cache. That is close to a full cache flush and a stampede on the origin.
27. REVALIDATED: the TTL expired and the origin answered 304. DYNAMIC: the object wasn't eligible, so the cache was never checked.
28. Bytes from the origin drop about 98%. Origin request count goes up, and the user's download size stays the same.
29. A pooled connection can only be reused by the worker that opened it, so split pools go cold before reuse.
30. A sliding-window estimate with two counters per client. A fixed window lets 2× the limit through at the window boundary.
31. Otherwise an attacker can skip the edge and call the origin IP directly. Use mTLS or a tunnel.
32. socket → DNS → connect → write → read → CDN → SSL/TLS → HTTP.
33. Transient ones: timeouts, connection refused, 502/503/504, and 429 after Retry-After. Use exponential backoff with jitter, and only for idempotent operations.
34. The social feed was different for each user and tied to live moments, so nothing could be cached. The scorecard is one file, the same for everyone, so it can sit in a CDN.
35. 15 + 5 + 5 = 25 seconds.
36. `#EXT-X-MEDIA-SEQUENCE`.
37. The size was chosen for ATM. The 13-bit PID says which stream a packet belongs to (audio, video or tables).
38. With `-codec copy` it can only cut at existing keyframes, and x264's default GOP is 250 frames (8.33 s at 30 fps).
39. Parts of about 1 s, blocking playlist reloads, preload hints and delta updates (EXT-X-SKIP). PART-HOLD-BACK is at least 3 parts.
40. Stamp each update with wall-clock time. Reveal it only once playback passes that `#EXT-X-PROGRAM-DATE-TIME`.

---
*Good luck in the quiz!*
