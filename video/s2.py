from common import *


class S2(VScene):
    def construct(self):
        self.session_title(
            2, "The Eagle-Eye View", "OSI · SS7 · TCP / UDP / QUIC · text protocols",
            "Session two. The eagle-eye view. Seven system calls make a server. Seven layers of nesting carry eleven bytes. "
            "The idea that ties the whole session together is this: one layer's headers are another layer's body.")
        self.ch_recap()
        self.ch_osi()
        self.ch_wifi()
        self.ch_starlink()
        self.ch_packet()
        self.ch_ss7_idea()
        self.ch_ss7_stack()
        self.ch_sms_encaps()
        self.ch_sms_140()
        self.ch_sms_flow()
        self.ch_isup()
        self.ch_sip()
        self.ch_ss7_vs_tcp()
        self.ch_bbr()
        self.ch_handshake()
        self.ch_syn_flood()
        self.ch_close()
        self.ch_rtt()
        self.ch_udp_quic()
        self.ch_smtp()
        self.ch_mime()
        self.ch_pop_imap()
        self.ch_framing()
        self.ch_ftp()
        self.quiz()

    # ------------------------------------------------------------------
    def ch_recap(self):
        self.new_slide("Sockets recap", "A quick recap of session one, with one new detail about closing.", C_BLUE)
        pts = [("Server: socket, bind, listen, accept, read, write, close",
                "The server makes seven calls. The one in listen is the accept queue depth, not the connection limit."),
               ("Client: no bind, no listen. connect() triggers the handshake",
                "The client skips bind and listen. The kernel picks an ephemeral source port, and connect triggers the handshake."),
               ("close() sends FIN, then the socket sits in TIME_WAIT for 2 x MSL",
                "A normal close sends a FIN, the polite way to say I am done sending. The socket then sits in TIME underscore WAIT for two times MSL, the Maximum Segment Lifetime."),
               ("SO_LINGER {1,0} sends RST: immediate, no TIME_WAIT",
                "SO underscore LINGER with one and zero sends an R S T instead. Immediate teardown, unsent data discarded, no TIME underscore WAIT.")]
        self.bullets(pts, size=28, gap=0.5)

    def ch_osi(self):
        self.new_slide("OSI: a 1984 committee model", "The OSI model is a nineteen eighty-four committee model that outlived almost everything built on it.", C_YELLOW)
        rows = [("L7", "Application", "HTTP · FTP · DNS · SMTP", C_ORANGE),
                ("L6", "Presentation", "encryption · compression · encoding", C_PURPLE),
                ("L5", "Session", "session management · authentication", C_PURPLE),
                ("L4", "Transport", "TCP · UDP", C_GREEN),
                ("L3", "Network", "IP · ICMP · routing", C_BLUE),
                ("L2", "Data link", "Ethernet · MAC · ARP · switches", C_TEAL),
                ("L1", "Physical", "cables · signals · hardware", C_GREY)]
        nars = ["Layer seven, application: HTTP, FTP, DNS, SMTP.",
                "Layer six, presentation: encryption, compression, encoding.",
                "Layer five, session: session management and authentication.",
                "Layer four, transport: TCP and UDP.",
                "Layer three, network: IP, ICMP, and routing.",
                "Layer two, data link: Ethernet, MAC addresses, ARP, switches.",
                "Layer one, physical: cables, signals, hardware."]
        g = VGroup()
        for n, name, ex, c in rows:
            g.add(VGroup(box(f"{n}  {name}", c, w=3.4, h=0.62, size=22), T(ex, 22, WHITE)).arrange(RIGHT, buff=0.5))
        g.arrange(DOWN, buff=0.1, aligned_edge=LEFT).shift(DOWN * 0.3 + RIGHT * 0.5)
        for r, n in zip(g, nars):
            with self.vo(n):
                self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.5)
        self.new_slide("TCP vs UDP", "Both live at layer four, but they make opposite promises.", C_GREEN)
        tbl = self.table([["", "TCP", "UDP"],
                          ["Connection", "connection-oriented", "connectionless"],
                          ["Delivery", "reliable, ordered", "no guarantee, no ordering"],
                          ["Control", "flow + congestion control, recovery", "fast, low overhead"],
                          ["Latency", "higher", "low"],
                          ["Used by", "HTTP, FTP, SMTP, SSH", "DNS, VoIP, video calls, gaming"]],
                         [2.4, 5.2, 5.2], size=25, y=0.3, row_h=0.8)
        self.reveal_rows(tbl, ["TCP is connection-oriented. UDP is connectionless.",
                               "TCP gives reliable, ordered delivery. UDP gives no guarantee and no ordering.",
                               "TCP adds flow control, congestion control and error recovery. UDP is fast, with low overhead.",
                               "So TCP has higher latency, and UDP has low latency.",
                               "HTTP, FTP, SMTP and SSH use TCP. DNS, voice calls, video calls and games use UDP."])

    def ch_wifi(self):
        self.new_slide("Wire vs radio: CSMA/CD vs CSMA/CA", "Layers one and two differ a lot between a wire and radio.", C_TEAL)
        L = VGroup(T("Ethernet (wire)", 30, C_BLUE), T("CSMA / CD", 40, C_YELLOW), T("detects collisions", 26)).arrange(DOWN, buff=0.25).move_to(LEFT * 3.4 + UP * 1.0)
        R = VGroup(T("Wi-Fi 802.11 (radio)", 30, C_GREEN), T("CSMA / CA", 40, C_YELLOW), T("can only avoid them", 26)).arrange(DOWN, buff=0.25).move_to(RIGHT * 3.4 + UP * 1.0)
        with self.vo("Ethernet, over a wire, detects collisions. That is CSMA slash C D. Wi-Fi, over radio, can only avoid them. That is CSMA slash C A."):
            self.play(FadeIn(L), FadeIn(R), run_time=1.2)
        why = T("Why? A radio cannot listen while it transmits.\nIts own signal drowns everything.", 26, C_ORANGE).shift(DOWN * 0.2)
        with self.vo("Why not detect on radio? Because a radio cannot listen while it transmits. Its own signal drowns everything else out."):
            self.play(FadeIn(why))
        self.flow(["listen\n(carrier sense)", "busy?\ndefer", "random backoff\n(contention window)", "transmit", "wait for ACK"],
                  [C_BLUE, C_RED, C_ORANGE, C_GREEN, C_YELLOW], y=-1.8, w=2.3, h=1.0, size=19, gap=0.35,
                  narrations=["So CSMA slash C A works in steps. First, listen to the channel. This is carrier sense.",
                              "If it is busy, defer.",
                              "Then wait a random backoff, called the contention window.",
                              "Then transmit.",
                              "And wait for an explicit acknowledgement for every frame. No ACK means back off and retransmit."])
        with self.vo("All of this costs about two milliseconds of contention delay before a frame leaves. And every Wi-Fi frame is acknowledged at layer two, long before TCP at layer four knows anything happened."):
            self.wait(0.5)

    def ch_starlink(self):
        self.new_slide("Starlink: layering in action", "Your packet can go to space and back, and nothing above layer two notices.", C_PURPLE)
        fl, _ = self.flow(["laptop", "Wi-Fi /\nEthernet", "Starlink\ndish", "LEO satellite\n~550 km\n~20 ms", "ground\ngateway", "internet"],
                          [C_BLUE, C_TEAL, C_ORANGE, C_PURPLE, C_ORANGE, C_GREEN], y=0.6, w=1.95, h=1.3, size=21, gap=0.3,
                          narrations=["A laptop.", "Over Wi-Fi or Ethernet.", "To a Starlink phased-array dish.", "An R F uplink in the Ku or Ka band to a low earth orbit satellite, about five hundred fifty kilometres up, around twenty milliseconds, optionally hopping across laser links between satellites.",
                                      "Down to a ground gateway.", "And onto the internet."])
        with self.vo("Nine physical hops. The I P header arrives unchanged, except for the time to live, the checksum, and any NAT rewrite. That is the whole argument for layering."):
            self.wait(0.3)

    def ch_packet(self):
        self.new_slide("Encapsulation, byte by byte", "Now what a packet actually looks like. Each layer wraps the one above.", C_ORANGE)
        l7 = box("GET / HTTP/1.1  Host: example.com", C_ORANGE, w=5.4, h=1.2, size=22)
        l4 = box("TCP  20 B", C_GREEN, w=1.8, h=1.2, size=22)
        l3 = box("IP  20 B", C_BLUE, w=1.6, h=1.2, size=22)
        l2h = box("Eth 14 B", C_TEAL, w=1.7, h=1.2, size=22)
        fcs = box("FCS 4 B", C_TEAL, w=1.4, h=1.2, size=22)
        frame = VGroup(l2h, l3, l4, l7, fcs).arrange(RIGHT, buff=0.0).move_to(DOWN * 0.4)
        with self.vo("Start at the top. Layer seven is the HTTP request, an opaque byte stream that TCP does not care about."):
            self.play(FadeIn(l7.move_to(frame[3])))
        with self.vo("TCP wraps it in a twenty byte header. Source port two bytes, destination port two bytes, sequence number four bytes, acknowledgement number four bytes, then flags and window."):
            self.play(FadeIn(l4.move_to(frame[2])))
        with self.vo("IP wraps that in another twenty byte header. It carries a time to live of one byte, a protocol field where six means TCP, a checksum, and four bytes each for the source and destination address."):
            self.play(FadeIn(l3.move_to(frame[1])))
        with self.vo("Ethernet adds a fourteen byte header in front. Destination MAC six bytes, source MAC six bytes, and a two byte EtherType, where zero x zero eight zero zero means IPv4."):
            self.play(FadeIn(l2h.move_to(frame[0])))
        with self.vo("And a four byte frame check sequence at the end, a CRC thirty-two."):
            self.play(FadeIn(fcs.move_to(frame[4])))
        eq = VGroup(T("MTU 1500  −  IP 20  −  TCP 20  =", 28), T("MSS 1460 B", 34, C_YELLOW)).arrange(RIGHT, buff=0.3).shift(DOWN * 1.9)
        eq2 = T("+ 14 B Ethernet header + 4 B FCS  →  1518 B on the wire", 26, C_GREY).next_to(eq, DOWN, buff=0.3)
        with self.vo("The byte budget. The MTU is fifteen hundred. Subtract twenty for IP and twenty for TCP, and you get a maximum segment size of fourteen sixty. "
                     "Add the fourteen byte Ethernet header and four byte trailer, and the frame on the wire is fifteen eighteen bytes."):
            self.play(FadeIn(eq))
            self.play(FadeIn(eq2))

    def ch_ss7_idea(self):
        self.new_slide("SS7: a second internet, older than TCP/IP", "Now a very different network. SS7, from nineteen seventy-five. It is a second internet, older than TCP IP.", C_RED)
        with self.vo("Its one big idea: get signalling out of the voice channel."):
            pass
        L = VGroup(T("Before: in-band signalling", 30, C_RED),
                   T("voice and control share the channel", 24),
                   T("2600 Hz tone = 'trunk is idle'", 24, C_YELLOW),
                   T("digits dialled as MF tones", 24),
                   T("anyone who can make the sound", 24), T("can make the decision", 24),
                   T("→ blue boxes, phone phreaking", 24, C_RED)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.4 + DOWN * 0.1)
        with self.vo("Before: in-band signalling. Voice and control shared one channel. A twenty-six hundred hertz tone meant this trunk is idle, and digits were dialled as multi-frequency tones. "
                     "Anyone who could make the sound could make the decision. These were the blue boxes of phone phreaking."):
            self.play(FadeIn(L, lag_ratio=0.2), run_time=3)
        R = VGroup(T("After: out-of-band", 30, C_GREEN),
                   T("voice bearer: 64 kbps DS0", 24), T("(the conversation only)", 24, C_GREY),
                   T("+ a separate packet-switched", 24), T("signalling network", 24),
                   T("MTP · SCCP · TCAP · MAP · ISUP", 24, C_YELLOW),
                   T("= control plane vs data plane", 24, C_GREEN)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.4 + DOWN * 0.1)
        with self.vo("After: out-of-band. The voice bearer is a sixty-four kilobit D S zero carrying only the conversation. A separate packet-switched signalling network carries the control. "
                     "That is the control plane versus data plane separation, decades before anyone used those words."):
            self.play(FadeIn(R, lag_ratio=0.2), run_time=3)

    def ch_ss7_stack(self):
        self.new_slide("SS7 stack vs TCP/IP stack", "Compare the SS7 stack with TCP IP, stack to stack, not protocol to protocol.", C_RED)
        tbl = self.table([["OSI", "SS7", "TCP/IP"],
                          ["L7", "MAP · INAP · CAP · ISUP", "HTTP · DNS · SMTP · SIP"],
                          ["L5-6", "TCAP (dialogues, ASN.1 BER)", "TLS / app framing"],
                          ["L4", "SCCP (Global Title Translation)", "TCP / UDP"],
                          ["L3", "MTP3 (point-code routing)", "IP (best effort, TTL)"],
                          ["L2", "MTP2 (signal units, CRC-16)", "Ethernet / PPP (MAC, FCS)"],
                          ["L1", "MTP1 (64 kbps DS0 on E1/T1)", "copper, fibre, radio"]],
                         [1.5, 5.6, 5.0], size=23, y=0.2, row_h=0.75)
        self.reveal_rows(tbl, [
            "At layer seven, SS7 has MAP, INAP, CAP and ISUP: call setup, roaming and SMS. TCP IP has HTTP, DNS, SMTP and SIP.",
            "At layers five and six, SS7 has TCAP, which handles dialogues using ASN dot one B E R. TCP IP has no distinct layer here.",
            "At layer four, SCCP, which does Global Title Translation, mapping a phone number to a destination. TCP IP has TCP and UDP.",
            "At layer three, MTP three routes by point code. IP is best effort with a time to live.",
            "At layer two, MTP two handles signal units, sequence numbers and a CRC sixteen with retransmission. Ethernet does framing and an F C S.",
            "And at layer one, MTP one is a sixty-four kilobit D S zero on an E one or T one line.",
        ])

    def ch_sms_encaps(self):
        self.new_slide("An SMS 'Hello World!' on the wire", "Let us encapsulate a real text message: Hello World, sent as a MO ForwardSM.", C_RED)
        layers = [("MTP2 MSU", "SIF cap 273 octets", C_GREY),
                  ("MTP3", "SIO 0x83 · DPC 2065 · OPC 2050 · SLS 5", C_TEAL),
                  ("SCCP UDT", "class 1 · Called/Calling Global Titles = phone numbers", C_BLUE),
                  ("TCAP BEGIN", "Invoke · opCode 46 = mo-ForwardSM", C_PURPLE),
                  ("MAP MO-ForwardSM-Arg", "", C_ORANGE),
                  ("SMS-SUBMIT TPDU", "TP-DCS 0x00 = GSM-7 · TP-UDL 0x0C = 12", C_GREEN),
                  ("TP-UD", "C8 32 9B FD 06 5D DF 72 36 39 04  =  'Hello World!'", C_YELLOW)]
        nars = ["The outermost layer is the MTP two message signal unit. Its payload field is capped at two hundred seventy-three octets.",
                "Inside it, MTP three: service indicator zero x eight three, destination point code two thousand sixty-five, origin point code two thousand fifty, link selector five.",
                "Inside that, an SCCP unitdata message, class one, whose called and calling Global Titles are the phone numbers.",
                "Inside that, a TCAP BEGIN carrying an Invoke with operation code forty-six, which is mo underscore ForwardSM.",
                "Then the MAP MO ForwardSM argument.",
                "Then the SMS-SUBMIT T P D U, with data coding scheme zero meaning GSM seven bit, and a user data length of twelve.",
                "And finally the user data: eleven octets, C eight, thirty-two, nine B, F D, zero six, five D, D F, seventy-two, thirty-six, thirty-nine, zero four. That spells Hello World."]
        for i, ((nm, det, c), n) in enumerate(zip(layers, nars)):
            top = 2.55 - 0.55 * i
            bot = -3.3 + 0.2 * i
            wd = 12.4 - 0.5 * i
            r = RoundedRectangle(corner_radius=0.08, width=wd, height=top - bot, color=c, stroke_width=3)
            r.set_fill(c, 0.06)
            r.move_to([0, (top + bot) / 2, 0])
            lab = T(f"{nm}   {det}", 19, c)
            if lab.width > wd - 0.4:
                lab.scale((wd - 0.4) / lab.width)
            lab.move_to([0, top - 0.27, 0])
            with self.vo(n):
                self.play(FadeIn(r), FadeIn(lab), run_time=0.8)
        with self.vo("Same picture as Ethernet around IP around TCP around HTTP. A different network, the same idea."):
            self.wait(0.3)

    def ch_sms_140(self):
        self.new_slide("Why is an SMS 140 bytes?", "Why is an SMS one hundred forty bytes? Three stacked limits, and the smallest wins.", C_RED)
        bars = [("272 octets", "SIF: MTP2's hard ceiling (one MSU)", 9.0, C_BLUE),
                ("~200 octets", "MAP sm-RP-UI field", 6.6, C_PURPLE),
                ("140 octets", "TP-UD: the SMS itself", 4.6, C_GREEN)]
        nars = ["Two hundred seventy-two octets: the signal information field, the hard ceiling of one MTP two message signal unit.",
                "About two hundred octets: the MAP sm RP UI field that carries the message.",
                "And one hundred forty octets: the TP user data, the SMS itself. It was chosen so the whole MAP operation always fits in one message signal unit."]
        y = 1.5
        for nm, d, wd, c in bars:
            r = Rectangle(width=wd, height=0.7, color=c, fill_opacity=0.3, stroke_width=3).move_to([-6.4 + wd / 2, y, 0])
            t = T(f"{nm}  -  {d}", 22).move_to(r)
            if t.width > wd - 0.2:
                t.scale((wd - 0.2) / t.width)
            with self.vo(nars[bars.index((nm, d, wd, c))]):
                self.play(GrowFromEdge(r, LEFT), FadeIn(t), run_time=1.0)
            y -= 1.0
        with self.vo("So there is no segmentation and no reassembly. One text is one signalling packet. That is why SMS ran on nineteen eighties hardware, and still works when mobile data is down."):
            self.wait(0.3)
        self.new_slide("160 characters in 140 bytes", "How do you fit one hundred sixty characters into one hundred forty bytes? Pack seven bits per character.", C_RED)
        eq = T("140 octets × 8 = 1120 bits  ÷  7 bits per char  =  160 chars", 30, C_YELLOW).shift(UP * 1.6)
        with self.vo("One hundred forty octets times eight is eleven hundred twenty bits. Divide by seven bits per character, and you get exactly one hundred sixty characters. This is GSM seven bit packing: septets in a continuous bit stream."):
            self.play(Write(eq))
        eq2 = T("'Hello World!' = 12 chars × 7 = 84 bits → 11 octets (+4 bits padding)", 27, C_GREEN).shift(UP * 0.3)
        with self.vo("Twelve characters times seven bits is eighty-four bits, which rounds up to eleven octets, with four bits of zero padding."):
            self.play(FadeIn(eq2))
        eq3 = T("UCS-2 (emoji / non-Latin): 140 ÷ 2 = 70 characters", 30, C_RED).shift(DOWN * 1.2)
        eq4 = T("one emoji can more than halve your message and silently cost a second SMS", 25, C_GREY).next_to(eq3, DOWN, buff=0.3)
        with self.vo("Switch to UCS two for emoji or non-Latin scripts, and it is two bytes per character: one hundred forty divided by two is seventy characters. "
                     "One emoji can more than halve your message, and silently cost you a second SMS."):
            self.play(FadeIn(eq3), FadeIn(eq4))

    def ch_sms_flow(self):
        self.new_slide("Sending an SMS = a database lookup in a queue", "Sending an SMS is really a database lookup wrapped in a queue.", C_RED)
        fl, bx = self.flow(["Phone A", "VMSC / VLR", "SMSC\nstore & fwd", "HLR", "MSC B", "Phone B"],
                           [C_BLUE, C_TEAL, C_ORANGE, C_PURPLE, C_TEAL, C_GREEN], y=0.8, w=1.9, h=1.1, size=20, gap=0.45,
                           narrations=["Phone A submits an SMS-SUBMIT.", "It reaches the visited MSC and VLR, which sends a MAP mo-ForwardSM.",
                                       "To the SMS centre, which stores it. It replies TCAP END immediately: accepted. Delivery is now the SMSC's problem.",
                                       "The SMSC asks the HLR, the subscriber database: send routing info for SM, with the phone number.",
                                       "The HLR returns the IMSI and the address of the serving MSC. The SMSC then sends a MAP mt-ForwardSM, an SMS-DELIVER, to that MSC.",
                                       "Which pushes it to Phone B."])
        with self.vo("Delivery acknowledgement flows back. An SMS status report is generated only if the sender requested it."):
            self.wait(0.3)

    def ch_isup(self):
        self.new_slide("A phone call = ISUP signalling + separate voice", "A phone call works the same way: signalling on one path, voice on another.", C_RED)
        ll = self.lifelines("MSC A", "MSC B", x=3.2)
        self.msg(ll, "r", "IAM", C_YELLOW, dy=0.7, note="Initial Address Message", narration="Phone A goes off-hook and dials. MSC A sends an I A M, the Initial Address Message.")
        self.msg(ll, "l", "ACM", C_GREEN, dy=0.7, note="B is ringing", narration="MSC B rings phone B and replies A C M, Address Complete. The caller hears ringback.")
        self.msg(ll, "l", "ANM", C_GREEN, dy=0.7, note="B answered", narration="B answers: A N M, the Answer Message. The voice path is cut through.")
        v = Line([-3.2, ll["y"] - 0.45, 0], [3.2, ll["y"] - 0.45, 0], color=C_ORANGE, stroke_width=10)
        vt = T("conversation: 64 kbps bearer circuit - no SS7 involved", 22, C_ORANGE).next_to(v, UP, buff=0.12)
        with self.vo("Now the conversation travels on the sixty-four kilobit bearer circuit. SS7 is not involved at all while you talk."):
            self.play(Create(v), FadeIn(vt))
        ll["y"] = ll["y"] - 0.9
        self.msg(ll, "r", "REL", C_RED, dy=0.7, note="on-hook: Release", narration="When someone hangs up, a REL, Release, is sent.")
        self.msg(ll, "l", "RLC", C_RED, dy=0.7, note="Release Complete", narration="Answered by R L C, Release Complete. Four messages set up a call, and signalling is idle during the talk.")

    def ch_sip(self):
        self.new_slide("5G / IMS: SIP", "On 5G and IMS, the same call is made with SIP: text shaped like HTTP, over IP.", C_RED)
        ll = self.lifelines("Alice", "Bob (via proxy / SBC)", x=3.2)
        self.msg(ll, "r", "INVITE + SDP offer", C_YELLOW, dy=0.62, size=20, narration="Alice sends INVITE with an SDP offer, through the proxy.")
        self.msg(ll, "l", "100 Trying", C_GREY, dy=0.62, size=20, narration="Back comes one hundred Trying,")
        self.msg(ll, "l", "180 Ringing", C_GREEN, dy=0.62, size=20, narration="one eighty Ringing,")
        self.msg(ll, "l", "200 OK + SDP answer", C_GREEN, dy=0.62, size=20, narration="and two hundred OK with an SDP answer. SIP borrowed HTTP's status codes.")
        self.msg(ll, "r", "ACK", C_YELLOW, dy=0.62, size=20, narration="Alice confirms with ACK, end to end.")
        v = Line([-3.2, ll["y"] - 0.45, 0], [3.2, ll["y"] - 0.45, 0], color=C_ORANGE, stroke_width=10)
        vt = T("RTP / SRTP media over UDP, directly between endpoints", 21, C_ORANGE).next_to(v, UP, buff=0.12)
        with self.vo("Now the media flows as RTP or SRTP over UDP, directly between the endpoints. The proxy never touches it. Control and data, on separate paths."):
            self.play(Create(v), FadeIn(vt))
        ll["y"] = ll["y"] - 0.9
        self.msg(ll, "r", "BYE", C_RED, dy=0.62, size=20, narration="Then BYE, and a two hundred OK.")

    def ch_ss7_vs_tcp(self):
        self.new_slide("SS7 vs TCP", "SS7 makes every hop reliable. TCP makes only the endpoints reliable.", C_RED)
        tbl = self.table([["Function", "SS7", "TCP"],
                          ["Sequencing", "FSN, 7 bits, wraps at 128", "32-bit seq number, per byte"],
                          ["Ack", "BSN + BIB, piggybacked", "cumulative ACK (+SACK)"],
                          ["Retransmit", "BIB toggle; PCR on satellite", "RTO; fast retransmit, 3 dup-ACKs"],
                          ["Flow control", "SIB: blunt stop/go", "sliding window"],
                          ["Error check", "CRC-16 per signal unit", "16-bit checksum"],
                          ["Addressing", "point code + SSN + Global Title", "IP + port"],
                          ["Congestion", "hop-by-hop (MTP3)", "end-to-end (Reno, CUBIC, BBR)"],
                          ["Reliability", "per hop", "end to end"],
                          ["Max payload", "272 octets", "~1460 B (64 KB w/ scaling)"]],
                         [2.4, 5.2, 5.4], size=22, y=-0.1, row_h=0.56)
        self.reveal_rows(tbl, ["Sequencing. SS7 uses a seven bit forward sequence number that wraps at one twenty-eight. TCP uses a thirty-two bit sequence number, counted per byte.",
                               "Acks. SS7 piggybacks a backward sequence number. TCP uses a cumulative ack number, plus SACK.",
                               "Retransmission. SS7 toggles a bit. TCP uses retransmission timers, and fast retransmit on three duplicate acks.",
                               "Flow control. SS7 is blunt stop or go. TCP has the sliding window advertised in every segment.",
                               "Error detection. SS7 uses a CRC sixteen on every signal unit. TCP uses a sixteen bit checksum.",
                               "Addressing. SS7 uses point codes, subsystem numbers and Global Titles. TCP uses IP and port.",
                               "Congestion control. SS7 is hop by hop. TCP is end to end.",
                               "So the scope of reliability: SS7 per hop, TCP end to end.",
                               "And the maximum payload: two hundred seventy-two octets, versus about fourteen sixty bytes, or sixty-four kilobytes with window scaling."])

    def ch_bbr(self):
        self.new_slide("BBR congestion control", "Next, congestion control, and Google's BBR from twenty sixteen.", C_PURPLE)
        ax = Axes(x_range=[0, 10, 1], y_range=[0, 5, 1], x_length=5.6, y_length=3.0, axis_config={"color": C_GREY, "include_ticks": False}).shift(LEFT * 3.4 + DOWN * 0.6)
        saw = VGroup()
        pts = []
        t, v = 0, 1.0
        while t < 10:
            pts.append(ax.c2p(t, v))
            t += 0.01
            v += 0.0045 * 1.0 + 0.003
            if v > 4.3:
                v = 2.15
        # simple sawtooth polyline
        xs = [0, 2.5, 2.5, 5, 5, 7.5, 7.5, 10]
        ys = [1.0, 4.2, 2.1, 4.2, 2.1, 4.2, 2.1, 4.2]
        line = VMobject(color=C_RED, stroke_width=4).set_points_as_corners([ax.c2p(x, y) for x, y in zip(xs, ys)])
        lab = T("Reno / CUBIC: loss-based sawtooth", 24, C_RED).next_to(ax, UP, buff=0.3)
        with self.vo("Loss-based TCP, like Reno and CUBIC, grows until a packet drops, then halves. That makes a sawtooth. "
                     "It needs loss to make progress, so on lossy, wireless or long fat links they crawl. And they fill buffers, which causes bufferbloat."):
            self.play(Create(ax), run_time=0.6)
            self.play(Create(line), FadeIn(lab), run_time=3)
        ax2 = Axes(x_range=[0, 10, 1], y_range=[0, 5, 1], x_length=5.6, y_length=3.0, axis_config={"color": C_GREY, "include_ticks": False}).shift(RIGHT * 3.4 + DOWN * 0.6)
        line2 = VMobject(color=C_GREEN, stroke_width=4).set_points_as_corners([ax2.c2p(x, y) for x, y in [(0, 1), (2, 3.6), (3, 3.9), (10, 3.9)]])
        lab2 = T("BBR: bandwidth × RTT", 24, C_GREEN).next_to(ax2, UP, buff=0.3)
        with self.vo("BBR measures the bottleneck bandwidth and the round-trip propagation time, and sends at what the path can carry, keeping the queue near empty. "
                     "Google reported up to two thousand times the throughput on some benchmarks, and much lower latency."):
            self.play(Create(ax2), run_time=0.6)
            self.play(Create(line2), FadeIn(lab2), run_time=2.5)

    def ch_handshake(self):
        self.new_slide("TCP handshake: 3 segments", "The TCP handshake. Each direction needs its own sequence number confirmed.", C_BLUE)
        ll = self.lifelines("Client  (CLOSED)", "Server  (LISTEN)", x=3.4)
        self.msg(ll, "r", "SYN  seq=1000", C_YELLOW, dy=1.0, note="options: MSS 1460, SACK, wscale 7",
                 narration="The app calls connect. The client sends a SYN with sequence number one thousand, and options: maximum segment size, SACK permitted, window scale.")
        self.msg(ll, "l", "SYN-ACK  seq=5000 ack=1001", C_GREEN, dy=1.0, note="server: SYN RECEIVED (half-open entry in backlog)",
                 narration="The server replies SYN ACK with its own sequence number, five thousand, and ack one thousand one. It now holds a half-open entry in the backlog.")
        self.msg(ll, "r", "ACK  seq=1001 ack=5001", C_YELLOW, dy=1.0, note="both ESTABLISHED; accept() returns",
                 narration="The client sends ACK. No payload is needed. Both sides are established, and the server's accept returns.")
        pts = [("The server's own SYN is what forces the third leg", "The server's own SYN is what forces the third leg."),
               ("SYN and FIN each consume a sequence number: ack=1001 answers seq=1000", "A SYN and a FIN each consume one sequence number. That is why ack one thousand one answers sequence one thousand, even though the SYN carried no data."),
               ("Random ISN (RFC 6528) - predictable ISNs enabled the Mitnick attack", "And the initial sequence number must be random. Early stacks were predictable, so an attacker could inject forged segments blind. That was the Mitnick attack. R F C sixty-five twenty-eight fixes it with a keyed hash of the four tuple plus a timer.")]
        self.new_slide("Handshake details", None, C_BLUE)
        self.bullets(pts, size=26, gap=0.5)

    def ch_syn_flood(self):
        self.new_slide("SYN flood and SYN cookies (1996)", "An attack on that handshake: the SYN flood.", C_RED)
        ll = self.lifelines("Attacker (spoofed IPs)", "Server", x=3.4)
        self.msg(ll, "r", "SYN SYN SYN SYN ...", C_RED, dy=0.9, narration="The attacker sends spoofed SYNs and never completes the handshake.")
        self.msg(ll, "l", "SYN-ACK → nowhere", C_GREY, dy=0.9, narration="Each one costs the attacker one packet, and costs the server a half-open backlog entry until it times out. Fill the backlog, and legitimate connections are refused. Remember listen with a backlog of one.")
        self.new_slide("Defence: keep no state", "The defence is to keep no state at all.", C_GREEN)
        fl, _ = self.flow(["4-tuple\n+ time\n+ MSS", "keyed\nhash", "server\nISN", "client ACK\n= ISN + 1", "validate,\nrebuild"],
                          [C_BLUE, C_PURPLE, C_ORANGE, C_YELLOW, C_GREEN], y=0.8, w=2.2, h=1.4, size=22, gap=0.4,
                          narrations=["Encode the connection parameters from the four tuple, a coarse timestamp and the MSS,", "run them through a keyed hash,",
                                      "and use the result as the server's initial sequence number.", "The client's ACK returns it plus one.",
                                      "The server recomputes, validates, and reconstructs the connection. No memory was spent in between."])
        pts = [("Cost: only 32 bits of ISN - window scale, SACK, timestamps mostly lost", "The cost: only thirty-two bits of ISN, so most TCP options, like window scale, SACK and timestamps, are mostly lost. That is why cookies switch on only under pressure."),
               ("Same trick everywhere: push state into a token the client returns", "The same trick shows up everywhere: push the state into a token that the client hands back. HTTP cookies, JWTs, signed URLs.")]
        self.bullets(pts, size=25, gap=0.4, below=fl)

    def ch_close(self):
        self.new_slide("Close: 4 segments, not 3", "Closing a connection takes four segments, not three.", C_ORANGE)
        ll = self.lifelines("Client", "Server", x=3.4)
        self.msg(ll, "r", "FIN", C_YELLOW, dy=0.85, note="client: FIN_WAIT_1", narration="The client sends a FIN.")
        self.msg(ll, "l", "ACK", C_GREEN, dy=0.85, note="server: CLOSE_WAIT · client: FIN_WAIT_2 (half-closed)",
                 narration="The server acknowledges. The server is now in CLOSE underscore WAIT, and the client in FIN underscore WAIT two. This is half closed: the client can still receive.")
        self.msg(ll, "l", "FIN", C_YELLOW, dy=0.85, note="after the server's remaining data", narration="The server sends any remaining data, and then its own FIN.")
        self.msg(ll, "r", "ACK", C_GREEN, dy=0.85, note="client: TIME_WAIT 2 x MSL, then CLOSED", narration="The client acknowledges, and waits in TIME underscore WAIT for two M S L before it is finally closed.")
        self.new_slide("Close: three things to remember", None, C_ORANGE)
        pts = [("SYN+ACK can combine; FIN+ACK cannot - the other side may still have data", "SYN and ACK can be combined into one segment. FIN and ACK cannot, because the other side may still have data to send."),
               ("Sockets stuck in CLOSE_WAIT = your app forgot close()", "Sockets stuck in CLOSE underscore WAIT are almost always an application that forgot to call close. It is not a network problem. Look at your code."),
               ("TIME_WAIT is why restart says 'address already in use' -> SO_REUSEADDR", "And TIME underscore WAIT is why restarting a server says address already in use, which SO underscore REUSEADDR fixes.")]
        self.bullets(pts, size=27, gap=0.55)

    def ch_rtt(self):
        self.new_slide("The round-trip tax", "The round trip tax. How many round trips before the first application byte?", C_YELLOW)
        tbl = self.table([["Setup", "RTTs before first app byte"],
                          ["TCP", "1"],
                          ["TCP + TLS 1.2", "3"],
                          ["TCP + TLS 1.3", "2"],
                          ["TCP Fast Open", "data in the SYN (returning clients)"],
                          ["QUIC / HTTP/3", "1 (transport + crypto folded together)"]],
                         [3.8, 7.4], size=26, y=0.4, row_h=0.8)
        self.reveal_rows(tbl, ["Plain TCP: one.", "TCP plus TLS one point two: three. The TCP handshake, then ClientHello and ServerHello, then key exchange.",
                               "TLS one point three saves one round trip of crypto: two in total.",
                               "TCP Fast Open puts data in the SYN for returning clients.", "And QUIC folds transport and crypto together: one."])
        t = T("Bandwidth you can buy. Round trips you cannot.  Mumbai → Virginia ≈ 190 ms", 26, C_ORANGE).shift(DOWN * 2.6)
        with self.vo("Bandwidth you can buy. Round trips you cannot. Mumbai to Virginia is about one hundred ninety milliseconds, every round trip."):
            self.play(FadeIn(t))

    def ch_udp_quic(self):
        self.new_slide("UDP: TCP with every promise removed", "UDP is TCP with every promise removed.", C_GREEN)
        hdr = VGroup(box("Src port\n2 B", C_BLUE, w=2.6, h=1.0, size=22), box("Dst port\n2 B", C_BLUE, w=2.6, h=1.0, size=22),
                     box("Length\n2 B", C_GREEN, w=2.6, h=1.0, size=22), box("Checksum\n2 B", C_ORANGE, w=2.6, h=1.0, size=22)).arrange(RIGHT, buff=0.05).shift(UP * 1.4)
        with self.vo("The UDP header is eight bytes in total. Source port, two bytes. Destination port, two bytes. Length, two bytes. Checksum, two bytes. The payload goes up to sixty-five thousand five hundred seven bytes."):
            self.play(FadeIn(hdr, lag_ratio=0.3), run_time=2)
        pts = [("TCP header: 20 B minimum (seq, ack, flags, window, options 0-40 B)", "Compare TCP: at least twenty bytes, with sequence, ack, flags, window, and up to forty bytes of options."),
               ("Used by Zoom, WebRTC, games, DNS, real-time streaming", "Zoom, WebRTC, game servers, DNS and real-time streaming use UDP. A retransmitted audio frame arrives too late to play, so dropping it is correct.")]
        self.bullets(pts, size=26, gap=0.5, below=hdr)
        self.new_slide("QUIC / HTTP/3: TCP rebuilt inside UDP", "QUIC rebuilds TCP inside UDP, in userspace.", C_PURPLE)
        L = VGroup(T("HTTP/1.1 and HTTP/2 over TCP", 27, C_RED), T("TLS: separate handshake", 23), T("one ordered byte stream", 23),
                   T("one lost packet stalls", 23, C_RED), T("every stream  (HOL blocking)", 23, C_RED)).arrange(DOWN, buff=0.2).move_to(LEFT * 3.4 + UP * 0.6)
        R = VGroup(T("HTTP/3 over QUIC", 27, C_GREEN), T("each stream has its own sequence space", 23), T("TLS 1.3 inside one handshake", 23),
                   T("lose a packet: only that", 23, C_GREEN), T("stream waits", 23, C_GREEN)).arrange(DOWN, buff=0.2).move_to(RIGHT * 3.4 + UP * 0.6)
        with self.vo("With HTTP one and two over TCP, TLS is a separate handshake, and TCP is one ordered byte stream. One lost packet stalls every stream. That is head-of-line blocking."):
            self.play(FadeIn(L))
        with self.vo("HTTP three over QUIC gives each stream its own sequence space, and folds TLS one point three into the same handshake. Lose a packet, and only that stream waits. UDP's eight bytes are left alone by kernels and middleboxes."):
            self.play(FadeIn(R))
        pts = [("Why userspace: TCP is in the kernel -> an OS update for the planet", "Why userspace matters: TCP lives in the kernel, so changing it means an operating system update for the whole planet, and hoping middleboxes do not object."),
               ("QUIC ships in the browser: congestion-control change 'on Tuesday'", "QUIC ships in the browser, so Google can deploy a congestion control change on a Tuesday.")]
        self.bullets(pts, size=24, gap=0.4, shift=DOWN * 2.0)

    def ch_smtp(self):
        self.new_slide("SMTP: the S is Simple", "Now text protocols you can speak by hand. First SMTP. The S stands for Simple. It has never stood for Secure.", C_BLUE)
        tbl = self.table([["Port", "Use"], ["25", "SMTP relay, server to server, plaintext"], ["587", "submission, client to server, STARTTLS (use this)"],
                          ["465", "SMTPS - implicit TLS from the first byte"], ["110 / 143", "POP3 / IMAP retrieval"]],
                         [2.4, 9.0], size=28, y=0.5, row_h=0.85)
        self.reveal_rows(tbl, ["Port twenty-five is relay, server to server, in plaintext.", "Port five eighty-seven is submission, client to server, upgraded with STARTTLS. Use this one.",
                               "Port four sixty-five is SMTPS: TLS from the very first byte.", "And one-ten and one-forty-three are for retrieving mail: POP three and IMAP."])
        self.new_slide("An SMTP session by hand", "Here is a session by hand over telnet.", C_BLUE)
        code = self.code_block(["EHLO scaler-demo", "MAIL FROM:<jeet@scaler.com>", "RCPT TO:<kshitij@scaler.com>", "DATA",
                                "From: jeet   To: kshitij", "Subject: hi", "", "hello body", ".", "QUIT"], size=21, pos=LEFT * 3.7 + DOWN * 0.3,
                               hl={"EHLO": C_GREEN, "MAIL": C_BLUE, "RCPT": C_BLUE, "DATA": C_ORANGE, "QUIT": C_RED})
        with self.vo("EHLO, then MAIL FROM, RCPT TO, DATA, the headers, a blank line, the body, a single dot on a line by itself, and QUIT."):
            self.play(FadeIn(code[0]), Write(code[1], run_time=3.5))
        notes = [("Envelope: MAIL FROM / RCPT TO = routing", C_BLUE,
                  "Envelope versus letter. MAIL FROM and RCPT TO are the envelope, used for routing."),
                 ("Letter: From: / To: in DATA = just text. Nothing checks they match", C_YELLOW,
                  "From and To inside DATA are just text printed on the letter. They do not have to match, and nothing checks. There is no authentication in base SMTP."),
                 ("A lone '.' ends the message -> dot-stuffing", C_ORANGE,
                  "A lone dot ends the message, so a body line that starts with a dot gets an extra dot. That is dot-stuffing."),
                 ("Miss the blank line -> Subject becomes body", C_RED, "Miss the blank line, and the subject becomes the body.")]
        ng = VGroup(*[T(wrap(x[0], 30), 22, x[1], maxw=6.4, line_spacing=0.9) for x in notes]).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(RIGHT * 3.4 + DOWN * 0.2)
        for n, (txt, c, nar) in zip(ng, notes):
            with self.vo(nar):
                self.play(FadeIn(n, shift=LEFT * 0.2), run_time=0.7)
        with self.vo("STARTTLS, SPF, DKIM and DMARC are all later patches, answering the question: is this sender allowed to say that?"):
            self.wait(0.3)

    def ch_mime(self):
        self.new_slide("MIME and base64: images travel as text", "How do images travel over a text protocol? MIME and base sixty-four.", C_BLUE)
        cx = -3.6
        top = VGroup(*[box(b, C_BLUE, w=1.9, h=0.7, size=22) for b in ["0x4D  M", "0x61  a", "0x6E  n"]]).arrange(RIGHT, buff=0.1).move_to([cx, 1.7, 0])
        bits = M("01001101 01100001 01101110", 22, C_YELLOW, maxw=6.2).move_to([cx, 0.6, 0])
        six = M("010011 010110 000101 101110", 22, C_GREEN, maxw=6.2).move_to([cx, -0.4, 0])
        out = VGroup(*[box(c, C_GREEN, w=1.1, h=0.8, size=28) for c in "TWFu"]).arrange(RIGHT, buff=0.1).move_to([cx, -1.6, 0])
        with self.vo("Three bytes, twenty-four bits, are regrouped as four six-bit values. Each maps to one of sixty-four safe printable characters. The word Man becomes T W F u."):
            self.play(FadeIn(top))
            self.play(FadeIn(bits))
            self.play(FadeIn(six))
            self.play(FadeIn(out, lag_ratio=0.2))
        rows = [("alphabet: A-Z a-z 0-9 + /  and = padding", WHITE), ("size x 4/3  =  +33%", C_YELLOW), ("76 characters per line (RFC 2045)", WHITE),
                ("Content-Type: multipart/mixed;", C_ORANGE), ("   boundary=\"=_a7f3c91\"", C_ORANGE), ("parts start  --=_a7f3c91", C_ORANGE),
                ("last part ends  --=_a7f3c91--", C_ORANGE), ("Content-Transfer-Encoding: base64", C_BLUE)]
        pts = VGroup(*[T(a, 22, b, maxw=6.4) for a, b in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(RIGHT * 3.4 + DOWN * 0.1)
        with self.vo("The alphabet is upper and lower case letters, digits, plus and slash, with equals for padding. The size grows by four thirds, about thirty-three percent, wrapped at seventy-six characters per line. "
                     "Parts are separated by a boundary declared in the Content-Type header. Each part starts with dash dash and the boundary, and the last ends with a trailing dash dash. Each part declares Content-Transfer-Encoding base sixty-four."):
            self.play(FadeIn(pts, lag_ratio=0.2), run_time=3)

    def ch_pop_imap(self):
        self.new_slide("POP3 and IMAP", "Reading mail. POP three has four verbs, on port one-ten, or nine ninety-five with TLS.", C_TEAL)
        ll = self.lifelines("Client", "POP3 server", x=3.2)
        self.msg(ll, "r", "USER bob / PASS secret", C_YELLOW, dy=0.7, size=20, note="plaintext! → POP3S 995", narration="Log in with USER and PASS, in plaintext, which is why POP3S on port nine ninety-five exists.")
        self.msg(ll, "r", "STAT", C_BLUE, dy=0.7, size=20, note="count + bytes", narration="STAT returns the count and total bytes.")
        self.msg(ll, "r", "LIST", C_BLUE, dy=0.7, size=20, note="number + size per message", narration="LIST returns a number and size for each message.")
        self.msg(ll, "r", "RETR n", C_GREEN, dy=0.7, size=20, note="the whole message n", narration="RETR n fetches the whole message.")
        self.msg(ll, "r", "DELE n  ... QUIT", C_RED, dy=0.7, size=20, note="marked, applied at QUIT", narration="DELE n marks it for deletion, and the deletion is applied at QUIT.")
        self.new_slide("POP3 vs IMAP", "POP puts the state on your machine. IMAP puts it on the server.", C_TEAL)
        tbl = self.table([["", "POP3 (110)", "IMAP (143)"],
                          ["Mail lives", "on your device", "on the server"],
                          ["Second device", "sees nothing", "same mailbox, same state"],
                          ["Read / unread", "local only", "server flags \\Seen \\Flagged"],
                          ["Folders", "just the inbox", "arbitrary hierarchy"],
                          ["Search", "download all, search locally", "SEARCH on server; IDLE push"],
                          ["Partial fetch", "no - RETR = whole message", "FETCH BODY[1] - one MIME part"]],
                         [2.6, 4.8, 5.4], size=24, y=0.1, row_h=0.8)
        self.reveal_rows(tbl, ["With POP the mail lives on your device and the server is a spool to empty. With IMAP it lives on the server and the client holds a cache.",
                               "A second device sees nothing under POP. Under IMAP it sees the same mailbox with the same state.",
                               "Read and unread is local only under POP. IMAP keeps server-side flags: Seen, Answered, Flagged.",
                               "POP has just the inbox. IMAP has an arbitrary folder hierarchy over the wire.",
                               "POP downloads everything and searches locally. IMAP searches on the server, and IDLE pushes new mail.",
                               "And POP can only fetch the whole message. IMAP can fetch just one MIME part."])

    def ch_framing(self):
        self.new_slide("Framing: length or delimiter (or both)", "A recurring theme: framing. Every protocol picks a delimiter, a length, or both.", C_ORANGE)
        tbl = self.table([["Delimiter", "Length", "Both"],
                          ["SMTP lone '.'", "SMS TP-UDL = 12 septets", "IMAP literal {310} + 310 bytes"],
                          ["HTTP headers CRLF CRLF", "HTTP Content-Length", "HTTP/1.1 headers + Content-Length"],
                          ["MIME --boundary--", "MTP2 LI, SIF <= 273", "POP3 +OK line, dotted body"],
                          ["Redis CRLF", "protobuf varint prefix", "HTTP/2 binary frames"]],
                         [4.4, 4.0, 4.6], size=24, y=0.5, row_h=0.9)
        self.reveal_rows(tbl, ["Delimiters: SMTP's lone dot, HTTP's blank line, MIME boundaries, Redis CRLF.",
                               "Lengths: an SMS user data length, HTTP content length, the MTP two length indicator, protobuf's varint prefix.",
                               "Both: IMAP literals say how many bytes follow. POP three has a plus OK line and then a dotted body. HTTP two uses binary frames.",
                               "And Redis uses CRLF between parts."][:3])
        self.new_slide("Framing: the trade-offs", None, C_ORANGE)
        pts = [("Delimiter: cheap, readable, streamable - but you must escape it (dot-stuffing)", "A delimiter is cheap and readable, and you can stream without knowing the size, but you must escape the delimiter. Dot-stuffing."),
               ("Length: content can never be confused with protocol - but the size must be known first (chunked encoding)", "A length means content can never be confused with protocol, but you must know the size before sending. That is why chunked transfer encoding exists."),
               ("Both: readable control + safe binary payload - but two parsers: request smuggling lives in the gap", "Using both gives readable control and a safe binary payload, but you now have two parsers, and request smuggling lives in the gap between them.")]
        self.bullets(pts, size=28, gap=0.6)

    def ch_ftp(self):
        self.new_slide("FTP: refuses to mix commands and data", "Finally, FTP, which refuses to mix commands and data.", C_PURPLE)
        ctrl = Line([-4.6, 1.5, 0], [4.6, 1.5, 0], color=C_BLUE, stroke_width=6)
        ct = T("control connection · port 21 · USER PASS LIST RETR PWD PASV", 22, C_BLUE, maxw=9).next_to(ctrl, UP, buff=0.15)
        cl = box("Client", C_BLUE, w=1.6, h=0.7, size=22).move_to([-5.5, 1.5, 0])
        sv = box("Server", C_GREEN, w=1.6, h=0.7, size=22).move_to([5.5, 1.5, 0])
        with self.vo("FTP uses a control connection on port twenty-one, for commands like USER, PASS, LIST, RETR, PWD and PASV. And a brand new data connection for every file or listing."):
            self.play(FadeIn(cl), FadeIn(sv), Create(ctrl), FadeIn(ct))
        a = Arrow([4.6, 0.2, 0], [-4.6, 0.2, 0], color=C_RED, stroke_width=5)
        at = T("Active (1971): server connects FROM port 20 back INTO the client\n-> blocked by every NAT / firewall", 22, C_RED, maxw=11).next_to(a, UP, buff=0.12)
        with self.vo("Active mode, from nineteen seventy-one: the server connects from port twenty back into the client. Every NAT and firewall now blocks this."):
            self.play(GrowArrow(a), FadeIn(at))
        b = Arrow([-4.6, -1.5, 0], [4.6, -1.5, 0], color=C_GREEN, stroke_width=5)
        bt = T("Passive (PASV): the client opens BOTH connections\n-> the only shape NAT allows", 22, C_GREEN, maxw=11).next_to(b, UP, buff=0.12)
        with self.vo("Passive mode, PASV: the server replies with an address and port, and the client opens both connections. That is the only shape NAT allows, so it is effectively mandatory now."):
            self.play(GrowArrow(b), FadeIn(bt))
        self.new_slide("Decoding the 227 reply", None, C_PURPLE)
        dec = VGroup(M("227 Entering Passive Mode (127,0,0,1,117,48)", 26, C_YELLOW),
                     T("IP = 127.0.0.1", 28), T("port = p1 x 256 + p2 = 117 x 256 + 48 = 30000", 30, C_GREEN)).arrange(DOWN, buff=0.4).shift(UP * 0.3)
        with self.vo("To decode the two twenty-seven reply: the first four numbers are the IP address. The port is p one times two fifty-six plus p two. One seventeen times two fifty-six plus forty-eight is thirty thousand. "
                     "A big-endian pair, htons spelled out in ASCII."):
            self.play(FadeIn(dec, lag_ratio=0.3), run_time=2)
        pts = [("Encapsulation: Ethernet > IP > TCP > HTTP  =  MTP2 > MTP3 > SCCP > TCAP > MAP > TPDU", "To keep from this session. Encapsulation: the same picture in both stacks."),
               ("Framing: SMS chose length, SMTP chose a dot, IMAP chose both", "Framing: SMS chose a length, SMTP chose a dot, IMAP chose both."),
               ("Reliability has an address: SS7 per hop at L2, TCP end to end at L4, QUIC in userspace", "Reliability has an address: SS7 at layer two per hop, TCP at layer four end to end, QUIC in userspace."),
               ("Separate control from data: SS7, SIP, FTP", "And separate control from data: SS7 killed blue boxes, SIP keeps media off the proxy, FTP opens a second socket.")]
        self.new_slide("What to keep from Session 2", None, C_GREEN)
        self.bullets(pts, size=28, gap=0.55)

    def quiz(self):
        self.quiz_recap(2, [
            "OSI 7 layers + examples. TCP vs UDP properties and users.",
            "Ethernet = CSMA/CD; Wi-Fi = CSMA/CA (L2 ACK every frame, ~2 ms contention).",
            "MAC 6 B, EtherType 2 B (0x0800 IPv4), FCS 4 B, MTU 1500, IP 20, TCP 20, UDP 8, MSS 1460, wire frame 1518. IP proto 6 = TCP.",
            "SS7: 1975, out-of-band, 64 kbps DS0, 2600 Hz blue box. MTP1/2/3, SCCP, TCAP, MAP/ISUP.",
            "SMS: 140 octets, 160 GSM-7 / 70 UCS-2 chars; SIF 272; store & forward; HLR lookup; mo-ForwardSM = opCode 46.",
            "ISUP: IAM, ACM, ANM, REL, RLC. SIP: INVITE, 100, 180, 200, ACK, BYE; media = RTP over UDP.",
            "SS7 reliability per hop; TCP end to end. BBR = bandwidth x RTT, not loss.",
            "SYN & FIN consume a seq number; random ISN (RFC 6528, Mitnick). SYN cookies: state in ISN, lose wscale/SACK/timestamps.",
            "Close = 4 segments; CLOSE_WAIT = app forgot close(); TIME_WAIT = 2 MSL.",
            "RTTs: TCP 1, +TLS1.2 3, +TLS1.3 2, QUIC 1. QUIC: UDP + userspace + per-stream sequence.",
            "SMTP 25 / 587 / 465; envelope vs header; lone dot; SPF/DKIM/DMARC. POP3 110/995; IMAP 143.",
            "FTP: 21 control, 20 active data; PASV 227 port = p1 x 256 + p2.",
        ], "Here is what the quiz is most likely to ask from session two.", size=25, per_page=6)
        self.say("That is session two. Next up, session three: scaling servers, from one process to many clients.")
