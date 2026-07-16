# Product name and licensing considerations

This document records release gates, not legal advice.

## Temporary repository license

The current `LICENSE` is a conservative all-rights-reserved notice. Source
visibility alone does not make the project open source and does not authorize
copying, modification, redistribution, hardware production, or sale. Before wider
collaboration or any distribution, the owners need qualified advice and a written
decision covering at least:

- desktop application source and binaries;
- firmware source and compiled images;
- documentation, examples, icons, screenshots, and other assets;
- schematic, PCB, enclosure, CAD, and manufacturing files if added;
- inbound contributor terms and the owners of existing contributions;
- notices and license obligations for every bundled dependency.

Software, documentation, hardware designs, trademarks, and patents may need
different licenses. Choosing an OSI software license does not automatically grant
rights to a logo, product name, circuit, or patent.

## Product name

“Stream Deck” is associated with third-party products and may be protected as a
trademark. The repository's current “StreamDeck Control” name can imply origin,
compatibility, or endorsement. Before public marketing, packaging, installer
signing, domain registration, store submission, crowdfunding, or sale:

1. commission a trademark/domain/store search in each intended market;
2. select and clear a distinctive original product name;
3. define accurate compatibility wording and attribution;
4. replace package names, credential-service names, executable metadata, USB
   descriptors, screenshots, and documentation consistently;
5. obtain review of third-party brand and OBS trademark usage.

Until then, every public-facing page must keep the non-affiliation disclaimer and
avoid third-party logos or trade dress. A repository rename needs redirect and
configuration migration plans; it must not silently orphan stored credentials or
user data.

## Commercial hardware

Source-code readiness is not product certification. Selling a physical device may
require electrical safety, EMC/ESD, radio (if later added), materials/environmental,
consumer, accessibility, labeling, warranty, recycling, import, and data-protection
work depending on jurisdiction and channel. Keep design controls, risk analysis,
supplier records, production tests, traceability, firmware provenance, incident
response, support, and recall capability.

No release workflow or README statement should claim certification, open-source
status, warranty coverage, or commercial readiness until the responsible owner has
documented evidence and approval.
