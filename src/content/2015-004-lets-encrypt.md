Title: Let's Encrypt: the road towards a better web?
Date: 2015-04-12 16:07
Author: andreacorbellini
Category: information-technology
Tags: security, tls, web, let's encrypt
Slug: lets-encrypt-the-road-towards-a-better-web
Status: published

I've always dreamed of a encrypted web, where HTTPS is the standard and plain HTTP is no more. A web where eavesdropping or manipulating information is not possible, or at least much harder than today.

I remember that I got excited when I first heard of **[CAcert](http://www.cacert.org/): "a community-driven Certificate Authority that issues certificates to the public at large for free"**. Unfortunately, CAcert's root certificate never made it into the major web browsers and operating systems. Whatever the reasons, the result is that visiting a HTTPS website with a certificate released by CAcert produces nothing but a [scary warning with a call to leave the site](https://cacert.org/), making CAcert unsuitable for most.

[StarCom](https://www.startssl.com/), on the other hand, has made it into the major browsers. But despite its certificates are released for free, it has never become much widespread. Also, StarCom [has](https://news.ycombinator.com/item?id=7557764) [been](https://www.techdirt.com/articles/20140409/11442426859/shameful-security-startcom-charges-people-to-revoke-ssl-certs-vulnerable-to-heartbleed.shtml) [heavily](https://twitter.com/startssl/status/453631038883758080) [criticized](https://bugzilla.mozilla.org/show_bug.cgi?id=994033) for how the Heartbleed vulnerability was handled, and AFAIK this has led many customers away.

# Let's Encrypt

Recently, I learned about **[Let's Encrypt](https://letsencrypt.org/): a "free, automated, and open" Certificate Authority** arriving in mid-2015. There are many important facts that make Let's Encrypt different and better from all the other Certificate Authorities out there. I'll let you discover all of them. Probably, the most important fact is that Let's Encrypt has **[important sponsors](https://letsencrypt.org/sponsors/), including Mozilla**. And this is what matters today, because it gives Let's Encrypt a chance to be included in at least one major browser.

<figure>
  <a href="https://letsencrypt.org/"><img src="{static}/images/letsencrypt-logo-horizontal.png" alt="Let&#039;s Encrypt" width="519" height="124"></a>
  <figcaption>Let's Encrypt logo.</figcaption>
</figure>

Another interesting fact about Let's Encrypt is that its **certificates are released in [a way that is both secure and automated](https://letsencrypt.org/howitworks/technology/) at the same time**. This gives the opportunity for other (potential) Certificate Authorities to adopt the same automated system.

If Let's Encrypt wins, then everyone will have an easy way to obtain a free HTTPS certificate for their website. The next big step would be making Let's Encrypt increase in adoption and the final step would be deprecating plain HTTP. There are however a few open questions:

* What will be the answer from Google, Apple, Microsoft and other major browser/operating systems makers?
* What will be the reaction of Verisign and Comodo? (That together hold [more than 50%](http://w3techs.com/technologies/overview/ssl_certificate/all) of all the certificates currently used on the web.)
* Will they declare war to Let's Encrypt or will they consolidate their efforts on customer services and Extended Validation?
* Will the technology behind Let's Encrypt allow the creation of a new model for certificate management? Will we see web servers and providers with built-in support for it?

I do not have an answer to these questions, time will tell. However I really hope my dream to become a reality soon. If you, like me, want Let's Encrypt to be a success, then please **share and discuss** about it. Perhaps, one day, we will find ourselves teaching juniors that HTTPS has not always been the standard... :)
