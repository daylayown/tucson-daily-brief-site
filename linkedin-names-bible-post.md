I've been playing a lot of Fallout 3 on a DIY Steam machine I built recently, which got me reading about how the Fallout series has kept itself internally consistent across nearly thirty years of games. The franchise has a "Fallout Bible" — a running document of names, places, lore, and the rules of the world — so anyone writing for the series stays on the same page.

I'd been wrestling with a similar problem on a much smaller scale.

I run an AI pipeline for the Tucson Daily Brief that drafts news reports from government meeting recordings. Deepgram transcribes the audio, Claude writes the AP-style report, and I edit before publishing. The transcription is great — except for names. And Tucson has a lot of names that aren't in Deepgram's training data, especially Spanish ones.

Some real misreads from recent drafts:

• Supervisor Andrés Cano → "Conner"
• Dr. Theresa Cullen → "Cohen"
• Finance Director Art Cuaron → "Quaron"
• Augie Acuña Los Niños Park → "El Cunno Los Ninos Park"
• Supervisor Matt Heinz → "Hines"

Any one of these is small. Put a bunch of them in a local news story and readers stop trusting you fast. Wrong names are the thing people notice first.

So I built one of my own: a "names and places bible." A JSON file with the official name, title, and known mistranscriptions for every elected official and senior staffer across four Southern Arizona municipalities — plus regional landmarks Deepgram routinely mangles. The pipeline detects which jurisdiction a meeting belongs to, grabs the right roster, and pastes it into the prompt as a reference.

Now Claude writes "Supervisor Cano" the first time. Pronouns line up. Place names come out right. No more red ink on names during editorial review.

Cost: about 500 extra tokens per draft. Fractions of a cent. Roughly an hour to set up, most of which was looking up correct spellings on .gov sites. And it keeps growing — every editorial pass adds a few more misreads to the dictionary.

Funny that a trick from a decades-old video game franchise still ports cleanly to AI pipelines in 2026. The good ones learn the texture of your beat the same way Fallout's writers learned the texture of theirs.
