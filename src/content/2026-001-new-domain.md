Title: This blog has moved to a new domain
Date: 2026-10-20 08:10 UTC
Author: andreacorbellini
Category: blog
Slug: new-domain
Image: images/librewolf-server-not-found.png
Status: published

**TL;DR:** This blog has moved from
[https://andrea.corbellini**.name**](https://andrea.corbellini.name) to
[https://andrea.corbellini**.blog**](https://andrea.corbellini.blog). Please
update all URLs pointing to this blog, and sorry for the inconvenience.

# Me and .name

Back in 2014 (12 years ago), I wanted to claim my small slice of the internet,
and so I purchased my first personal domain name, where I would have hosted my
blog: `andrea.corbellini.name`. To be honest with you, I would have liked a
more creative domain name, but I'm notoriously not good at giving names to
things, and so I couldn't come up with anything better than `first.last.name`.

For those who are not familiar with the matter, `.name` domains have always
been special and different from other domains: when they launched (back in
2002, according to Wikipedia), they only allowed third-level domain
registrations, meaning that you _could_ register the third-level domain
`first.last.name`, but _could not_ register the second-level domain
`last.name`. Second-level domains would be somewhat shared between the folks
sharing the same last name. A few years later (in 2009, still according to
Wikipedia), this restriction was lifted, and the ability to register
second-level domains was offered.

So when I went to register my domain name I had two options: register
`corbellini.name` or `andrea.corbellini.name`. I wanted to be kind to other
people and so I decided to register the third-level domain, leaving
`corbellini.name` subdomains available to other people as well. I don't think
my last name is very common, and in fact I would bet that my domain is the only
one under `corbellini.name` even today, so perhaps we could say that my
kindness was totally unnecessary. What's sure is that my kindness did not get
rewarded.

Recently, Verisign, the operator of `.name` domains, decided to discontinue
third-level domains like mine. This means that sometime in the future,
`andrea.corbellini.name` will disappear from the internet. It will cease to
exist. Any attempt to resolve that domain name and to reach my blog will fail.
Visitors will get a generic error from their browser, without any hints about
what happened, why, and where my blog can be found. No redirect, no "click here
to visit the new site", nothing. The void.

<figure>
  <img src="{static}/images/librewolf-server-not-found.png" alt="Server Not Found error from LibreWolf">
</figure>

# A new home: .blog

I recently registered a new domain at `andrea.corbellini.blog` and moved my
blog there. Needless to say, this time I own the whole `corbellini.blog`
domain (also because there's no other choice with `.blog`).

Right now, my `.name` domain redirects to my new `.blog`, but this won't last
forever.

I haven't published a ton of stuff on this blog (not nearly as much as I
wished), but some of the articles I published have become quite popular in
their niche ecosystem, in particular my articles about Elliptic Curve
Cryptography and Authenticated Encryption. I see a ton of visits from people
who found links to my articles from other sites. All those links will be broken
once my `.name` domain will be terminated, which is a shame. It's still not
very clear to me when this will happen, but it will happen at some point, so I
need to ask everyone who has links pointing to my blog: please change all the
URLs to my articles from `.name` to `.blog`.

# The perks of .blog

I must say, while it's certainly disappointing to have a domain name (that has
served me and others for so many years) disappear in a blip without any control
from me, or any concrete possibility to appeal, owning a second-level domain
comes with its own perks.

One of them is that now I can enable DNSSEC, which is something I could never
do with my third-level `.name` domain, as I had no control over the second-level
domain (who knows, maybe there was a way, but I never figured it out). And in
fact I'm happy to say that I did enable DNSSEC on `andrea.corbellini.blog`.

Another perk is that I can now use services that were not previously available
to me, like Cloudflare. Services like Cloudflare in fact do not understand
third-level domains and did not allow me to register with them because they
wanted proof of ownership of the second-level domain. Now this is no longer an
obstacle.

Reaching my blog also becomes a bit easier: https://corbellini.blog in fact
redirects to https://andrea.corbellini.blog.

Perhaps an amusing fact about `.blog` specifically is that it's owned and
operated by a company called "Knock Knock WhoIS There, LLC", and I find that
name quite funny. Having said that, I don't know anything about this company or
their reputation.

# Final remarks

I know there are a few active attempts at keeping third-level `.name` domains
alive. A very prominent reconsideration request was recently sent by [Neil
Fraser](https://neil.fraser.name/news/2026/10/04/). I will very likely join
these attempts, although honestly I've witnessed so much enshittification in
the past few years that I've lost hope in most (if not all) corporations, and I
seriously doubt that things will change in this time frame. What is happening
to `.name` domains in my opinion is a small symptom of something much bigger:
the fast decay of modern corporate culture, focused on profits above anything
else, to the point that screwing customers over and over has become standard
practice. I doubt Verisign is going to sacrifice revenue, keep on the costs of
maintaining third-level `.name` domains, and reverse their course of action.

And to those who are going to point out that it's ICANN who has the power of
reversing this decision, and ICANN is a non-profit organization, not one of the
corporations I'm complaining about: sure, you may have a point. I don't want to
either defend nor attack ICANN's role in this matter. The thing is that I don't
see a world where ICANN forces Verisign to do something they don't want to do
anymore, regardless of what ICANN's intentions are.

I'm happy to be proven wrong. I _truly_ hope this decision gets reversed and I
get to keep my `.name` domain. But at this point I lost all hope.
