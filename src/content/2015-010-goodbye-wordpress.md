Title: Hello Pelican!
Date: 2015-08-02 18:55
Author: andreacorbellini
Category: misc
Tags: blog, pelican, wordpress
Slug: hello-pelican
Status: published

Today I switched from WordPress.com to [Pelican](http://getpelican.com/) and [GitHub Pages](https://pages.github.com/).

First off, let me say: almost all URLs that were previously working should still work. Only the feed URLs are broken, and this is not something I can fix. If you were following my blog via a feed reader, you should update to the new feed. Sorry for the inconvenience.

Having said that, I'd like to share with you the motivation that made me move and the details of the migration.

# The bad things of WordPress

Now, this doesn't want to be a rant, so I'll be pretty concise. WordPress, the content management system, is an excellent platform for blogging. Easy to start with, easy to maintain, easy to use. WordPress.com makes things even easier. It also comes with many useful features, like comments and social networks integration.

The problem is: you can't customize things or add features without paying. Of course, this is business, and I do not want to discuss business decisions made at WordPress.com. Not only that, but I could live fine with most of the major limitations. Also, I was perfectly conscious of this kind of problems with WordPress.com when I started (after all, this is not [the first blog I started]({filename}/2015-000-new-blog.md)).

I actually become upset of WordPress.com when writing the series of blog posts about [Elliptic Curve Cryptography]({filename}/2015-005-ecc-part-1.md). When writing these articles, I spent a lot of time employing workarounds to overcome WordPress.com limitations. Being used to Vim and its advanced features, I also found the editors (both the old and the new one) as a great obstacle for getting things done quickly. I do not want to enter the details of the problems I'm referring to, what matters is that, eventually, I gave up and I realized it was time to move on and seek for an alternative.

# Why Pelican

Pelican is a static site generator. I've always thought that a static site had too many limitations for me. But while seeking an alternative to WordPress.com, I realized that many of those limitations were not affecting me in any way. Actually, with a static site I can do everything I want: edit my articles with Vim, render my equations with MathJax, customize my theme, version control my content, write scripts to post process my content.

The only bad thing about Pelican is that it does not come with any theme I truly like. I decided to make my own. I'm not entirely satisfied with it, as I feel it is too "anonymous", but I believe it is fully responsive, fast, readable and offers all the features I want. Perhaps I'll tweak it a little more to make it more "personal".

Setting up Pelican and migrating everything required some time, but at least this time I worked on true solutions, not on ugly hacks and workarounds like I did with WordPress. This implies that when writing articles I will be able to focus more on content than other details.

# Why not other static site generators

In short: Pelican is written in Python and to my eyes it looked better than the other Python static site generators. I'll be honest and say that I did not truly evaluate all of the alternatives: I knew [list.org](...) switched to Pelican and that made me try Pelican before all other solutions.

# Conclusion

In the end I decided to leave WordPress for Pelican hosted on GitHub Pages. I'm pretty satisfied with the result I got. The nature of GitHub Pages prevents me from using HTTP redirects (and therefore the old feed links are broken), however in exchange I've got much more freedom, and this is what matters to me.
