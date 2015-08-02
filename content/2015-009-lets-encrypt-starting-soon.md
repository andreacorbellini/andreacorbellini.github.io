Title: Let's Encrypt is going to start soon
Date: 2015-06-16 18:20
Author: andreacorbellini
Category: cryptography
Tags: ecdsa, let's encrypt, rsa, security, tls
Slug: lets-encrypt-is-going-to-start-soon
Status: published

[Let's Encrypt](https://letsencrypt.org/) (the free, automated and open certificate authority) has just [announced its launch schedule](https://letsencrypt.org/2015/06/16/lets-encrypt-launch-schedule.html). According to it, certificates will be released to the public starting from the **week of September 14, 2015**.

Their intermediate certificates, which [were generated a few days ago](https://letsencrypt.org/2015/06/04/isrg-ca-certs.html), will be signed by [IdenTrust](https://www.identrustssl.com/). What this means is that if you browse a web page secured by Let's Encrypt, you won't get any scary message, but the usual green lock.

<figure>
  <img src="{filename}/images/green-lock.png" alt="Green lock" width="612" height="188">
  <figcaption><strong>You will see this...</strong></figcaption>
</figure>

<figure>
  <img src="{filename}/images/red-lock.png" alt="Red lock" width="612" height="300">
  <figcaption><strong>... not this.</strong></figcaption>
</figure>

In case you are curious: the root certificate is a 4096-bit RSA key, the two intermediate certificates are both 2048-bit RSA keys. But they are also [planning to generate ECDSA keys later this year](https://letsencrypt.org/certificates/) as well.

Technical aspects aside, this will be a great opportunity for the entire web. As I have [already written]({filename}/2015-004-lets-encrypt.md), I always dreamed of an encrypted web, and I truly believe that Let's Encrypt -- or at least its approach to the problem -- is the way to go.

So, will you get a Let's Encrypt certificate when the time comes? I will do. Not for this blog (I can't put a certificate without paying), but for other websites I manage.

Perhaps I'll also show a "Proudly secured by Let's Encrypt" badge.
