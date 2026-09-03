# Legal position and contributor rules

**This is not legal advice.** It is the operating policy of this project, so
that everyone contributing knows where the lines are. If you need advice for
your own situation, talk to a lawyer.

## What this project is

Console Companion is an **interoperability project**. Its purpose is to let
people keep using Monogram Creative Console and Palette Gear hardware they
lawfully own, after the vendor stopped supporting it.

It is not a crack, a clone, or a rival product. Specifically, it does not:

- circumvent any technical protection measure, DRM, or licence check
- redistribute the vendor's software, installers, binaries, or firmware
- copy the vendor's source code, artwork, icons, or branding
- require anyone to obtain the vendor's software unlawfully

Everything here is either original work or information derived from observing
how hardware the contributor owns behaves on a USB bus.

## The hard lines

These are not negotiable. A contribution that crosses one will be rejected,
and if it has already been merged it will be reverted.

**Never contribute:**

| Do not bring in | Why |
|---|---|
| Vendor source code, in any form | Copyright infringement, plainly |
| Decompiled or disassembled vendor output | Derivative of their code |
| Extracted icons, artwork, sounds, or UI assets | Copyright in the assets themselves |
| Firmware images or firmware-derived code | Copyright, and possibly TPM issues |
| The vendor's installers or binaries | Redistribution |
| Vendor trademarks or logos in our branding | Trademark |
| Configuration files containing vendor-copyrighted content | Derivative work |

**Do contribute:**

- Original code you wrote
- Protocol observations from watching USB traffic on hardware you own
- Documentation in your own words
- Test recordings from your own device

## Clean-room policy for protocol work

Observing what a device sends on a bus is not copying a program. It is the
safest possible footing, and it is how the protocol work here should be done.

**Preferred method — black-box observation.** Plug in hardware you own, watch
what it sends, write down what you see. `probe/monoprobe.py` is built for
exactly this. Nothing is reproduced, so no copyright question arises.

**Discouraged — decompiling the vendor app.** It can be faster, and in some
jurisdictions it is lawful for interoperability, but the protection is
narrower and varies by country. Do not do it on behalf of this project.

**If you have already seen the vendor's source or decompiled output**, for any
reason, please do not contribute to the protocol decoder. Contribute
documentation, UI, packaging, or testing instead. This keeps the decoder's
provenance clean and defensible.

## Provenance for protocol contributions

When contributing protocol findings, state in the pull request:

1. That the hardware is yours.
2. That the findings came from observing bus traffic, not from vendor code.
3. What tool you used and roughly what you did.

A sentence is enough. It exists so the project's history shows a clean chain
if anyone ever asks.

## Naming and trademarks

The project is **Console Companion**. Monogram and Palette Gear are other
people's trademarks and we do not use them as ours.

**Acceptable** — factual, descriptive references that tell users what the
software works with:

- "Console Companion works with Monogram Creative Console hardware"
- "compatible with Palette Gear modules"

That is nominative fair use: naming a product to describe compatibility is
allowed, because there is no other way to say it.

**Not acceptable:**

- Naming a release "Monogram Creator" or anything confusingly similar
- Using their logo, wordmark, or visual identity
- Implying endorsement, affiliation, or that this is an official continuation
- Copying their app's visual design closely enough to be mistaken for it

We copy the *interaction model* — the idea that you drag a module onto a
layout and assign it a function. Ideas are free. The specific visual
expression is not, so ours is our own.

## Jurisdictional notes

Interoperability reverse engineering is protected in the major jurisdictions,
though the scope differs:

- **Australia** — [Copyright Act 1968 s47D](https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/cth/consol_act/ca1968133/s47d.html)
  permits reproduction to obtain information needed for an independently
  created interoperable program, where that information is not otherwise
  available and only to the extent reasonably necessary. Note that the
  [ALRC has described this exception as too narrow and out of date](https://www.alrc.gov.au/publication/copyright-and-the-digital-economy-alrc-report-122/17-computer-programs-and-back-ups/exceptions-for-computer-programs/),
  so it is a weaker shield than its US or EU counterparts. This is the main
  reason the project prefers black-box observation.
- **European Union** — the Software Directive permits decompilation for
  interoperability, subject to conditions.
- **United States** — *Sega v. Accolade* and *Sony v. Connectix* established
  that intermediate copying for interoperability can be fair use.

Observing bus traffic, which is what this project actually does, sits
comfortably inside all of them.

## A note on the vendor's status

The company has gone dark: servers shut down, no releases since 5.10.1, no
support. That is documented. What is **not** established is any formal
insolvency or transfer of assets.

This matters. A company being unreachable does not put its intellectual
property into the public domain. Someone still owns those copyrights,
trademarks, and any patents, and in an actual insolvency such assets are
usually sold rather than extinguished. Treat the IP as live and owned by
someone, even though nobody is answering the phone.

In practice, enforcement against a free, non-commercial compatibility tool is
rare. That risk rises if the project ever becomes commercial, which is a good
reason to keep it free.

## If someone objects

If a rights holder contacts the project with a specific, credible complaint,
the response is to take it seriously and engage rather than posture: review
the claim, remove anything that genuinely crosses a line above, and document
what changed. Nothing here is worth a fight, and the project's value is in
keeping hardware working, not in winning an argument.

## Contributor agreement

By contributing you confirm that:

- your contribution is your own original work, or you have the right to submit it
- it contains no vendor code, assets, or firmware
- you licence it under this project's [MIT licence](LICENSE)
