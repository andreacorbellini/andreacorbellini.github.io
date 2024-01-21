Title: My journey from Disqus to Remark42
Date: 2023-09-05 08:30
Author: andreacorbellini
Category: blog
Slug: disqus-to-remark42
Status: published

Readers of this blog might have noticed a few changes recently. For example,
I've been working on improving the look of the blog (maybe with questionable
results), as well as improving the experience on mobile. But one of the biggest
changes that perhaps some have noticed is that all of the comments on all of my
articles have suddenly disappeared since February 2023. Now, almost 7 months
later, all comments have finally been restored.

The reason for this 7 months blackout of comments is that I decided to change
the platform that hosts comments: I got rid of [Disqus](https://disqus.com/),
and eventually replaced it with [Remark42](https://remark42.com/). Here I will
describe why I did it. There will be another (more technical) blog post about
my new setup.

# Premise

My blog is a static website that has been using Disqus as a commenting platform
for a long time: since at least 2015 (8 years ago), or maybe even more (back
when my blog was on WordPress). Disqus at that time was gaining a lot of
popularity, it was free, and it was very attractive to me because easy to set
up. I might be wrong, but at that time, Disqus did not look to me like the
data-savvy, privacy-invading, revenue-oriented company that it is today. Maybe
I just naive, but so I kept using Disqus all these years without paying too
much attention to it: after all, it worked, so why would I spend any time
thinking about it?

# Advertisements on my blog!?

Fast-forward to February 2023: one day, a person very close to me, with the
utmost kindness that characterizes her, came to me and said: "the ads on your
blog suck! They're the worst kind of ads!"

At the beginning I had no idea what she was talking about. I have never
intentionally run any sort of advertisements on my blog. I hate advertisements!

Then I realized what was going on: precisely because I hate advertisements, I
run ad-blockers on all my devices. Maybe *there were* ads on my blog, but I
never noticed because I block those ads. The only third-party service that I
used to run on my blog was Disqus, so I immediately turned my attention to it.
I disabled my ad-blockers, refreshed my blog, scrolled down to the comments
section, and... the sad truth was revealed: Disqus was showing ads to my
readers. And yes, those ads were some of the worst kind of ads.

And I knew that, together with those ads, there was massive tracking,
collection of data, and maybe even data sharing with third-parties. People who
know me, know that I deeply care about privacy, and having Disqus on my blog
tracking my readers was the complete opposite of what I wanted.

I was extremely disappointed.

# Leaving Disqus

I did some quick research and I discovered that (1) I could not disable Disqus
ads without paying, and (2) Disqus was no longer that nice commenting platform
that I met in 2015. It had mutated into something obsessed about revenue, and
it was clear that their business model was completely based on ads. My fears
about tracking were [quickly
confirmed](https://techcrunch.com/2021/05/05/disqus-facing-3m-fine-in-norway-for-tracking-users-without-consent/).
Let's just say that Disqus turned out to something that does not really align
with my values.

I made the difficult decision to completely [remove
Disqus](https://github.com/andreacorbellini/andreacorbellini.github.io/commit/4f0e450d31441cab387a0e70f884fb65f19693fd)
from my blog on the same day. But I firmly believe that **[a blog without
comments is not a
blog](https://blog.codinghorror.com/a-blog-without-comments-is-not-a-blog/)**,
and so I *had* to find an alternative.

# Looking for a new platform

I quickly started to look for new commenting platforms that could replace
Disqus. The basic criteria that this new platform had to meet were (in no
particular order):

* be free of charge
* display only comments, no ads
* respect the privacy of users
* allow users to comment anonymously (at least to some extent)

The last time that I searched for a commenting platform was in 2015. Back in
those days, there were not many solutions, and that's one reason why I ended up
with Disqus. I thought: 8 years have passed since then, surely the space must
have improved, and alternatives must be proliferating, right? Well, no, not
really. I struggled to find a managed platform that met those criteria.

I did find some solutions that were using Mastodon or GitHub as a backend to
store comments, but I did not like at all the idea of forcing my readers to
have a Mastodon or GitHub account to comment on my blog.

# Trying Cactus Comments

One platform that came up multiple times during my search was [Cactus
Comments](https://cactus.chat/). Quoting the homepage of the project:

> Cactus Comments is a federated comment system built on Matrix. It respects
> your privacy, and puts you in control. The entire thing is completely free
> and open source.

That sounded interesting, although I did not really know what
[Matrix](https://matrix.org/) was to begin with (if you, like me earlier this
year, do not know what Matrix is: it is a team communication platform, somewhat
similar to [Slack](https://slack.com/)). I thought that I could give Cactus a
try. So, a few days after removing Disqus, I onboarded on Cactus Comments.

Onboarding was not hard, but it was not trivial either, mostly because I was
not familiar with Matrix. The frontend shown to readers was a bit
disappointing: even though Matrix supports threads, Cactus Comments does not.
Overall, the number of features that commenters could use was scarce: people
could only post a comment, and not much else; they had no ability to edit their
comments, or delete them. But it did allow people to post even without creating
a Matrix account, and that was great for me.

The "administrative interface" (if we can call it this way) was also
disappointing. All the administration and moderation had to be done through
Matrix, sometimes by communicating with a bot, and could not be done by
clicking buttons on my blog. Every blog post had to have its own Matrix channel
and I (the author) had to manually join each channel in order to get some sort
of notification for new comments.

I needed a Matrix client to spot new comments, and to perform moderation
actions, and I chose [Element](https://element.io/) for that purpose. Sadly,
Element was totally unreadable on small displays like my phone. And apparently
there's no web-based Matrix client that works well on mobile. I could have
installed an app for my phone, but I *hate* installing apps, especially for
activities that can in theory be done through a web browser.

Cactus Comments also did not support importing comments from Disqus, so moving
to this platform meant that all the conversations that happened over the years
on my blog were lost. But because Cactus Comments is free & open source
software, I thought that I could add support for importing comments from Disqus
if I decided to settle with Cactus Comments, so this was not a deal breaker.

Overall my experience with Cactus Comments was not great, but I was willing to
accept that in exchange for a platform that was free, managed by someone else,
and respecting the privacy of my readers.

There was however one big problem that eventually led me to remove Cactus
Comments from my blog: Cactus did not support sending email notifications. This
meant that if you left a comment on this blog, I would not get notified. And if
I responded to your comment, you would not get notified. In order to spot new
comments, I had to check the Matrix channels periodically, and readers and to
check my blog periodically. Maybe if I installed a Matrix app I could have
received push notifications on my phone, but that's not what I wanted, and this
wouldn't have solved the problem for my commenters anyway.

I was pretty bad at checking for new comments on Cactus. What happened multiple
times is that people would leave comments or questions on my blog, but I
wouldn't notice until 2 weeks later. At that point, it was pointless for me to
respond because so much time had passed that those commenters surely wouldn't
be checking my blog for a response...

I would say that with Cactus I had a blog that allowed *comments*, but did not
allow *conversations*. Not allowing conversations made the comments pointless
in my opinion. I might as well have had no comments at all: at least people
would stop leaving questions there that were destined to be unanswered, and
instead they would have emailed me directly.

# Meet Remark42

Between August and September 2023, I decided that I had to restart my quest for
a commenting platform. This time I knew that I had to look for a solution that
I had to install and manage myself. I was not super-excited about it, but from
my first search for a Disqus alternative, I couldn't find any managed solution
that I really liked.

Initially I thought about writing my own commenting platform in Rust with a
key-value store, but then I figured that if I looked for a software to install
instead of a managed platform, maybe I could find something I liked.

After some research, I decided to go with [Remark42](https://remark42.com/).
There were a few contenders, but Remark42 won because it looked like it had
all of the features I needed, and more:

* it supports sending of email notifications, both to me, and to my readers;
* it supports various authentication mechanisms, including: email, GitHub,
  Google, Facebook, etc (it's nice to give commenters a choice);
* it supports leaving comments anonymously, without logging in or leaving an
  email address;
* commenters can edit and delete comments;
* it supports importing comments from Disqus;
* in fact, it supports importing comments from any platform: the format it uses
  for restoring backups is JSON-based and very easy to replicate (in theory I
  could import the comments from Cactus, even though I have not done that yet);
* it's privacy-focused, and it looks like it's implemented with security in
  mind.

I decided to host it on [Fly.io](https://fly.io/), which offers some compute
and storage capacity for free. I was introduced to Fly.io on Mastodon, but I
had never used it before.

For sending emails, I chose [Elastic Email](https://elasticemail.com/), which
also offers the features I needed for free. I also had never used this service
before, and did not know much about it: it showed up while searching for a free
SMTP provider. Elastic Email describes itself as a marketing service, which
does not sound great from the point of view of privacy, but I figured that all
the emails being sent here contain only public information (all comments are
public after all), so there's not much to protect besides email addresses.  And
people are free to use temporary email providers like
[Mailinator](https://www.mailinator.com/) if they don't want to leave their
real email, or even leave no email address at all. (Should I be concerned about
Elastic Email, like I should have been concerned about Disqus? Let me know...
in the [comments](#comments) below.)

Setting up Remark42 on Fly.io was relatively easy, but it took me way longer
than I had expected, mostly because the Fly.io documentation was quite
inconsistent and confusing, and also the Remark42 documentation was not fully
clear. In the end I managed to make everything work and I'm pretty happy with
the setup I ended up with. I'm going to publish details about my setup in a
future blog post, in case you're interested (update: said blog post is now
[published]({filename}/2023-006-running-remark42-on-flyio.md)).

# Conclusion

That's all I have to say for now! Remark42 has been running on my blog for a
few days, so it's too early for me to say whether I'll stick with it or I will
look for a new solution, but so far it looks very promising, and I'm very happy
with it. I hope this is the beginning of a long journey!
