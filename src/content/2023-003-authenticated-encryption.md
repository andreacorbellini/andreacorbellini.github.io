Title: Authenticated encryption: why you need it and how it works
Date: 2023-03-09 18:35
Author: andreacorbellini
Category: cryptography
Slug: authenticated-encryption
Image: images/lack-of-diffusion.webp
Status: published

In this article I want to explore a common problem of modern cryptographic
ciphers: malleability. I will explain that problem with some hands-on examples,
and then look in detail at how that problem is solved through the use of
authenticated encryption. I will describe in particular two algorithms that
provide authenticated encryption: ChaCha20-Poly1305 and AES-GCM, and briefly
mention some of their variants.

# The problem

If we want to encrypt some data, a very common approach is to use a symmetric
cipher. When we use a symmetric cipher, we hold a **secret key**, which is
generally a sequence of bits chosen at random of some fixed length (nowadays
ranging from 128 to 256 bits). The symmetric cipher takes two inputs: the
secret key, and the message that we want to encrypt, and produces a single
output: a ciphertext. Decryption is the inverse process: it takes the secret
key and the ciphertext as the input and yields back the original message as an
output. With symmetric ciphers, we use the same secret key both to encrypt and
decrypt messages, and this is why they are called symmetric (this is in
contrast with public key cryptography, or asymmetric cryptography, where
encryption and decryption are performed using two different keys: a public key
and a private key).

Generally speaking, symmetric ciphers can be divided into two big families:

* **stream ciphers**, which can encrypt data bit-by-bit;
* **block ciphers**, which can encrypt data block-by-block, where a block has a
  fixed size (usually 128 bits).

As we will discover soon, both these two families exhibit the same fundamental
problem, although they slightly differ in the way this problem manifests
itself. To understand this problem, let's take a close look at how these two
families of algorithms work and how we can manipulate the ciphertexts they
produce.

## Stream ciphers

A good way to think of a stream cipher is as a deterministic random number
generator that yields a sequence of random bits. The **secret key** can be
thought of as the *seed* for the random number generator. Every time we
initialize the random number generator with the same secret key, we will get
exactly the same sequence of random bits out of it.

The bits coming out of the random number generator can then be XOR-ed together
with the data that we want to encrypt: <code><span
style="color:#204a87">ciphertext</span> = <span style="color:#a40000">random
sequence</span> XOR <span style="color:#4e9a06">message</span></code>, like in
the following example:

<pre>
<span style="color:#a40000">random sequence: 3bAWC5ThFSPXX1W8P94q3XV35TG6CRVTNAPW27Q69F</span>
                                     ⊕
        <span style="color:#4e9a06">message: I would really like an ice cream right now</span>
                                     =
     <span style="color:#204a87">ciphertext: zB686Y0H46144HwT9RQQR6vZV1gU1779n390ZCqXV1</span>
</pre>

The XOR operator acts as a toggle that can either flip bits or keep them
unchanged. Let me explain with an example:

* `a XOR 0 = a`
* `a XOR 1 = NOT a`

If we XOR "something" with a 0 bit, we get "something" out; if we XOR
"something" with a 1 bit, we get the opposite of "something". And if we use the
same toggle twice, we return to the initial state:

* `a XOR b XOR b = a`

This works for any `a` and any `b` and it's due to the fact that `b XOR b` is
always equal to 0. In more technical terms, each input is its own self-inverse
under the XOR operator.

The self-inverse property gives us a way to decrypt the message that we
encrypted above: all we have to do is to replay the random sequence and XOR it
together with the ciphertext:

<pre>
<span style="color:#a40000">random sequence: 3bAWC5ThFSPXX1W8P94q3XV35TG6CRVTNAPW27Q69F</span>
                                     ⊕
     <span style="color:#204a87">ciphertext: zB686Y0H46144HwT9RQQR6vZV1gU1779n390ZCqXV1</span>
                                     =
        <span style="color:#4e9a06">message: I would really like an ice cream right now</span>
</pre>

This works because <code><span style="color:#204a87">ciphertext</span> = <span
style="color:#a40000">random sequence</span> XOR <span
style="color:#4e9a06">message</span></code>, therefore <code><span
style="color:#a40000">random sequence</span> XOR <span
style="color:#204a87">ciphertext</span> = <span style="color:#a40000">random
sequence</span> XOR <span style="color:#a40000">random sequence</span> XOR
<span style="color:#4e9a06">message</span></code>. The two <code><span
style="color:#a40000">random sequence</span></code> are the same, so they
cancel each other (self-inverse), leaving only <code><span
style="color:#4e9a06">message</span></code>:

<pre>
<span style="color:#a40000">random sequence: 3bAWC5ThFSPXX1W8P94q3XV35TG6CRVTNAPW27Q69F</span>
                                     ⊕
<span style="color:#a40000">random sequence: 3bAWC5ThFSPXX1W8P94q3XV35TG6CRVTNAPW27Q69F</span>
                                     ⊕
        <span style="color:#4e9a06">message: I would really like an ice cream right now</span>
                                     =
        <span style="color:#4e9a06">message: I would really like an ice cream right now</span>
</pre>

Only the owner of the secret key will be able to generate the random sequence,
therefore only the owner of the secret key should, in theory, be able to
recover the message using this method.

### Playing with stream ciphers

The self-inverse property not only allows us to recover the message from the
random sequence and the ciphertext, but it also allows us to recover the random
sequence if can correctly guess the message:

<pre>
        <span style="color:#4e9a06">message: I would really like an ice cream right now</span>
                                     ⊕
     <span style="color:#204a87">ciphertext: zB686Y0H46144HwT9RQQR6vZV1gU1779n390ZCqXV1</span>
                                     =
<span style="color:#a40000">random sequence: 3bAWC5ThFSPXX1W8P94q3XV35TG6CRVTNAPW27Q69F</span>
</pre>

This "feature" opens the door to at least two serious problems. If we are able
to correctly guess the message or a portion of it, then we can:

1. **decrypt** other ciphertexts produced by the same secret key (or at least
   portions of them, depending on what portions of the random sequence we were
   able to recover);
1. **modify** ciphertexts.

And we can do all of this without any knowledge of the secret key.

The first problem implies that key reuse is forbidden with stream ciphers.
Every time we want to encrypt something with a stream cipher, we need a new
key. This problem is easily solved by the use of a *nonce* (also known as
*initialization vector*, *IV*, or *starting variable*, *SV*): a random value
that is generated before every encryption, and that is combined in some way
with the secret key to produce a new value to initialize the random number
generator. If the nonce is unique per encryption, then we can be sufficiently
confident that the random sequence generated will also be unique. The nonce
value does not necessarily need to be kept secret, and needs to be known at
decryption time. Nonces are usually generated at random at encryption time and
stored alongside the ciphertext.

The second problem is a bit more subtle: if we have a ciphertext and we can
correctly guess the original message that produced it, we can modify it using
the XOR operator to "cancel" the original message and "insert" a new message,
like in this example:

<pre>
         <span style="color:#3465a4">ciphertext: zB686Y0H46144HwT9RQQ<strong style="color:#204a87">R6vZV1gU1779</strong>n390ZCqXV1</span>
                                         ⊕
            <span style="color:#73d216">message: I would really like <strong style="color:#4e9a06">an ice cream</strong> right now</span>
                                         ⊕
    <span style="color:#73d216">altered message: I would really like <strong style="color:#4e9a06">to go to bed</strong> right now</span>
                                         =
<span style="color:#3465a4">tampered ciphertext: zB686Y0H46144HwT9RQQ<strong style="color:#204a87">G7vTZt3Yc030</strong>n390ZCqXV1</span>
</pre>

This message, when correctly decrypted with the secret key, will return the
tampered ciphertext *without detection!*

Note that I do not need to know the full message to carry out this technique,
in fact, the following example (where unknown parts have been replaced by
hyphens) produces the same result as the above one:

<pre>
         <span style="color:#3465a4">ciphertext: zB686Y0H46144HwT9RQQ<strong style="color:#204a87">R6vZV1gU1779</strong>n390ZCqXV1</span>
                                         ⊕
            <span style="color:#73d216">message: --------------------<strong style="color:#4e9a06">an ice cream</strong>----------</span>
                                         ⊕
    <span style="color:#73d216">altered message: --------------------<strong style="color:#4e9a06">to go to bed</strong>----------</span>
                                         =
<span style="color:#3465a4">tampered ciphertext: zB686Y0H46144HwT9RQQ<strong style="color:#204a87">G7vTZt3Yc030</strong>n390ZCqXV1</span>
</pre>

This problem is known as
[**malleability**](https://en.wikipedia.org/wiki/Malleability_(cryptography)),
and it's a serious issue in the real world because most of the messages that we
exchange are in practice relatively easy to guess.

Suppose for example that I have control over a WiFi network, and I can inspect
and alter the internet traffic that passes through it. Suppose that I know that
a person connected to my WiFi network is visiting an e-commerce website and
that they're interested in a particular item. The traffic that your browser
exchanges with the e-commerce website may be encrypted, and therefore I won't
be able to decrypt its contents, but I might be able to guess certain parts of
it, like the HTTP headers sent by the website, or some parts of the HTML that
are common to all pages on that website, or even the name and the price of the
item you want to buy. If I can guess that information (which is public
information, not a secret, and it's generally easy to guess), then I might be
able to alter some parts of the web page, showing you false information, and
altering the price that you see in an attempt to trick you into buying that
item.

<details markdown="block">
<summary>An example of malleability using ChaCha20 with OpenSSL</summary>

Here's a practical example of how we can take the output of a stream cipher,
and alter it as we wish without knowledge of the secret key. I'm going to use
the OpenSSL command line interface to encrypt a message with a stream cipher:
[ChaCha20](https://en.wikipedia.org/wiki/ChaCha20). This is a modern, fast,
stream cipher with a good reputation:

```sh
openssl enc -chacha20 \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 0123456789abcdef0123456789abcdef \
    -in <(echo 'I would really like an ice cream right now') \
    -out ciphertext.bin
```

The `-K` option specifies the key in hexadecimal format (256 bits, or 32 bytes,
or 64 hex characters), the `-iv` is the nonce, also known as *initialization
vector* (128 bits, or 16 bytes, or 32 hex characters).

This trivial Python script can tamper with the ciphertext:

```python
with open('ciphertext.bin', 'rb') as file:
    ciphertext = file.read()

guessed_message     = b'--------------------an ice cream----------\n'
replacement_message = b'--------------------to go to bed----------\n'

tampered_ciphertext = bytes(x ^ y ^ z for (x, y, z) in
                            zip(ciphertext, guessed_message, replacement_message))

with open('tampered-ciphertext.bin', 'wb') as file:
    file.write(tampered_ciphertext)
```

This script is using partial knowledge of the message. It knows (thanks to an
educated guess) that the original message contained the words "an ice cream" at
a specific offset, and uses that knowledge to replace those words with new ones
("to go to bed") which add up to the same length. Note that this technique
cannot be used to remove or add parts from the message, only to modify them
without changing their length.

Now if we run this script and we decrypt the `tampered-ciphertext.bin` file
with the same key and nonce as before, we get "to go to bed" instead of "an ice
cream", without any error indicating that tampering occurred:

```sh
openssl enc -d -chacha20 \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 0123456789abcdef0123456789abcdef \
    -in tampered-ciphertext.bin
```
</details>

## Block ciphers

We have seen that stream ciphers alone have a serious problem (malleability)
that allows anyone to modify arbitrary portions of ciphertexts without
detection. Let's take a look at the alternative: block ciphers. Will they have
the same problem?

While a stream cipher can encrypt variable amounts of data, a block cipher can
only take as input a block of data of a fixed size, and produce as output
another block of data. A good block cipher produces an output that is
indistinguishable from random.

The block size is generally small, usually 128 bits (16 bytes), so if we want
to encrypt larger amounts of data, we have to split the data into multiple
blocks, and encrypt each block individually. If the data is too short to fit in
a block, the data will also need to be padded.

<pre>
   message: <span style="color:#4e9a06">The cat is on th</span> <span style="color:#204a87">e table.........</span>
            |______________| |______________|
                <span style="color:#4e9a06">block #1</span>         <span style="color:#204a87">block #2</span>
                                 <span style="color:#204a87">(padded)</span>

ciphertext: <span style="color:#73d216">c2TNPW3r09hZ6f1P</span> <span style="color:#3465a4">Vc32VX41XSy579Y9</span>
</pre>

This approach however has a problem: if we encrypt multiple blocks with the
same secret key, then portions of messages that are the repeated will produce
the same output. This gives the ability to analyze a ciphertext and find
patterns in it without knowledge of the secret key. This problem is famously
evident when encrypting pictures:

<figure>
  <img src="{static}/images/lack-of-diffusion.webp" alt="Ubuntu logo before and after encryption with a block cipher">
  <figcaption>Example of applying a block cipher to an uncompressed image. The original colors are lost, but the overall layout of the image is still understandable. That's because multiple blocks of the image (containing the RGB values of each pixel), for example from the white background, are repeated multiple times, yielding the same exact encrypted blocks. The inspiration for making this image came from <a href="https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation">Wikipedia</a>.</figcaption>
</figure>

<details markdown="block">
<summary>How this image was generated</summary>

Before jumping into how I encrypted the image, let me spend a few words on how
I did NOT encrypt the image: I did not use a modern image format. Modern image
formats are very sophisticated, they're not a simple sequence of RGB values.
Instead, they have some control structures mixed in the image, they implement
compression to reduce the image size, etc. This complexity means that if I
simply take an image in any format and encrypt it, the result won't be
visualizable by an image viewer: the image viewer would just throw an error
because it would find invalid data structures.

Note that this does not imply that encrypting modern image formats is more
secure: people can still analyze patterns in them, but it simply means that a
modern image format, once encrypted, would not produce the sensational
visualization that I showed above.

In order to produce this visualization I had to find an uncompressed image
format without too much metadata in it. Thankfully the Wikipedia article on
[image file formats](https://en.wikipedia.org/wiki/Image_file_format) provided
a list, which included the [Netpbm](https://en.wikipedia.org/wiki/Netpbm)
family of formats (something I never heard of before). Among the formats in
this family, I chose PPM, because it's the one that supports colors.

The PPM file format is very simple: it has 3 lines of metadata, followed by the
RGB values for each pixel. No compression. Definitely the right format for this
kind of experiment!

So here's what I did: first of all I downloaded an image (the Ubuntu "Circle of
Friends" logo, obtained from Wikipedia) and converted it to PPM with
[ImageMagick](https://imagemagick.org/script/convert.php):

```sh
convert UbuntuCoF.png img.ppm
```

I separated the header from the RGB values:

```sh
head -n3 img.ppm > ppm-header
tail -n+4 img.ppm > ppm-image
```

The reason why I separated the header from RGB values is that I won't encrypt
the header. If I did, then the image won't be visualizable by an image viewer,
just like if I used a modern image format.  In a real-world scenario, a person
would be able to easily guess the header if it was encrypted.

I encrypted the RGB values with
[AES-256](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard), a
modern, strong block cipher with a good reputation:

```
openssl enc -aes-256-ecb \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -in ppm-image \
    -out ppm-image-encrypted
```

Then I joined the header and the encrypted RGB values in a PPM file:

```
cat ppm-header ppm-image-encrypted > img-encrypted.ppm
```

This results in a randomized image that can be viewed without problems on an
image viewer. It's interesting to see that, if you change the encryption key,
you will get a different randomized image!
</details>

The problem we have just seen is known as **lack of diffusion**. This is kinda
analogous to the first problem we identified with stream ciphers: at the root
of both problems there is key reuse. We solved this problem for stream ciphers
by combining a key with a random nonce. We could use the same strategy here,
but it would be an expensive approach, as initializing a block cipher with a
new key is a relatively expensive operation. It's much cheaper to initialize
the block cipher once, and reuse it for every block encryption. We need a way
to "link" blocks to each other, so that if two linked blocks contain the same
plaintext, their encryption will give different results.

There are various strategies do that. These strategies are known as [*mode of
operation*](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation) of
block ciphers. Let's take a look at two of them: **Cipher Block Chaining
(CBC)** and **Counter Mode (CTR)**.

### Cipher Block Chaining (CBC)

This mode of operation, as the name suggests, 'chains' each block to the next
one. The way it works is by using the XOR operator in the following way:

*   First of all, a random nonce is generated. The purpose of the nonce is the
    same as before (with stream ciphers): ensuring that using the same secret
    key to perform multiple encryptions yields different results each time, so
    that secret information or patterns are not revealed.

    The nonce does not need to be kept secret and is normally stored alongside
    the ciphertext so that it can be easily used during decryption. It is
    however important that the nonce is unique.

*   The first block of message `m[0]` is XOR-ed with the nonce, and then
    encrypted the block cipher, producing the first block of ciphertext `c[0] =
    block_encrypt(m[0] XOR nonce)`

*   The second block of message `m[1]` is XOR-ed with `c[0]`, and then
    encrypted with the block cipher: `c[1] = block_encrypt(m2 XOR c[0])`

*   ...

*   The last block of message `m[n]` is XOR-ed together with `c[n-1]`, and then
    encrypted with the block cipher: `c[n] = block_encrypt(m[n] XOR c[n-1])`

<figure>
  <img src="{static}/images/cipher-block-chaining.svg" alt="Visualization of the Cipher Block Chaining (CBC) mode of operation">
</figure>

The XOR operator is back! With stream ciphers, the XOR operator was allowing us
to tamper with ciphertexts. Can we do the same thing here? Yes of course! The
approach is slightly different though: instead of acting directly on the block
that we want to change, we will act on the block that precedes it.

For example, if we want to change the sentence "I came home in the afternoon
and the cat was on the table" so that it reads 'dog' instead of 'cat', we would
need to change the block right before the one that contains the word 'cat'. If
we want to change the very first block, for example to change the word 'came'
to 'left', we would need to change the nonce instead.

<pre>
                             <span style="color:#75507b">nonce</span>+<span style="color:#3465a4">ciphertext</span>: <span style="color:#75507b">yz<strong style="color:#5c3566">URZR</strong>bP6X1w3ZRL</span> <span style="color:#3465a4">XRDnPbEkx3JUP2Fv C2ZWt<strong style="color:#204a87">19E</strong>dAXDi76H pkbk8qTgaSdzerbF 8CWYqscBqE6cSLmx</span>
                                                                ⊕
        <span style="color:#73d216">message</span> (shifted 1 block to the left): <span style="color:#73d216">I <strong style="color:#4e9a06">came</strong> home in t he afternoon and  the <strong>cat</strong> was on  the table.......</span>
                                                                ⊕
<span style="color:#73d216">altered message</span> (shifted 1 block to the left): <span style="color:#73d216">I <strong style="color:#4e9a06">left</strong> home in t he afternoon and  the <strong>dog</strong> was on  the table.......</span>
                                                                =
                    tampered <span style="color:#75507b">nonce</span>+<span style="color:#3465a4">ciphertext</span>: <span style="color:#75507b">yz<strong style="color:#5c3566">ZVQC</strong>bP6X1w3ZRL</span> <span style="color:#3465a4">XRDnPbEkx3JUP2Fv C2ZWt<strong style="color:#204a87">67V</strong>dAXDi76H pkbk8qTgaSdzerbF 8CWYqscBqE6cSLmx</span>
</pre>

If we do the above, and then decrypt the tampered ciphertext, we will get
something like this:

```
I left home in t���������������the dog was on the table
```

<details markdown="block">
<summary>How to get this result using AES-CBC with OpenSSL</summary>

Here's a step-by-step guide on how to tamper with a ciphertext encrypted with
AES-256 in CBC mode.

First, generate a valid ciphertext:

```sh
openssl enc -aes-256-cbc \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 0123456789abcdef0123456789abcdef \
    -in <(echo 'I came home in the afternoon and the cat was on the table') \
    -out ciphertext.bin
```

Like in the stream cipher example, `-K` is the key in hexadecimal format (256
bits), while `-iv` is the nonce (128 bits).

We can perform the tampering with this Python script:

```python
with open('ciphertext.bin', 'rb') as file:
    ciphertext = file.read()

guessed_message     = b'---------------------cat----------------------------------------'
replacement_message = b'---------------------dog----------------------------------------'

tampered_ciphertext = bytes(x ^ y ^ z for (x, y, z) in
                            zip(ciphertext, guessed_message, replacement_message))

with open('tampered-ciphertext.bin', 'wb') as file:
    file.write(tampered_ciphertext)
```

Note that OpenSSL does not store the nonce along with the ciphertext, but
instead expects it to be passed as a command line argument. We need to modify
it separately, so here's another Python script just for the nonce:

```python
nonce = bytes.fromhex('0123456789abcdef0123456789abcdef')

guessed_message     = b'--came----------'
replacement_message = b'--left----------'

tampered_nonce = bytes(x ^ y ^ z for (x, y, z) in
                       zip(nonce, guessed_message, replacement_message))

print(tampered_nonce.hex())
```

If we run that script, we get: `01234a6382bacdef0123456789abcdef`.

Now to decrypt the tampered ciphertext with the tampered nonce:

```sh
openssl enc -d -aes-256-cbc \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 01234a6382bacdef0123456789abcdef \
    -in tampered-ciphertext.bin
```
</details>

It's interesting to see that we were successful in changing the word 'cat' to
'dog' but in doing so we had to sacrifice a block, which, when decrypted,
resulted in random bytes.

In a real world scenario, seeing some random bytes could raise some suspicion,
and maybe generate some errors in applications, however that's not always the
case (how many times have we seen garbled text on our monitors, and we never
worried that somebody was tampering with our communications). Also, when
dealing with formats like HTML, one could conceal tampering attempts using
comment blocks, or using JavaScript. One example of what I'm describing is the
[EFAIL vulnerability](https://efail.de/): discovered in 2017, it affected some
popular email clients including Gmail, it targeted the use of AES in CBC mode
(as well as another mode very similar to it: Cipher Feedback, CFB), and allowed
the injection of malicious content in HTML emails.

We can conclude that block ciphers in CBC mode, just like stream ciphers, are
also malleable.

### Counter Mode (CTR)

Are other modes of operation all malleable like CBC, or will they be different?
Let's take a look at another, very common, mode of operation: Counter Mode
(CTR), so that we can get a better sense of how the problem of malleability can
affect the world of block ciphers.

The mechanism behind Counter Mode is very simple:

1.  A random nonce is generated. The purpose of the nonce is the usual one:
    make sure that repeated encryptions using the same key produce different
    results.

1.  A counter (usually an integer) is initialized to 1 (or any other starting
    value of your choice).

1.  The nonce is concatenated with the counter, and encrypted using the block
    cipher: `r[0] = block_encrypt(nonce || counter)`.

    Because the block cipher can only accept as input a block of a fixed size,
    it follows that the length of the nonce plus the length of the counter must
    be equal to the block size. For example, for a 128-bit block cipher, a
    common choice is to have a 96-bit nonce and a 32-bit counter.

1.  The counter is incremented: `counter = counter + 1` (the increment does not
    necessarily need to be by 1, but that's a common choice). The nonce and the
    new counter are concatenated again, and encrypted using the block cipher:
    `r[1] = block_encrypt(nonce || counter)`.

1.  The counter is incremented again (`counter = counter + 1`), and a new block
    is encrypted, just like before: `r[2] = block_encrypt(nonce || counter)`.

1.  ...

This mechanism produces a sequence of blocks `r[0]`, `r[1]`, `r[2]`, ... which
are indistinguishable from random. This sequence of random blocks can be XOR-ed
with the message to produce the ciphertext.

It's important that the values for the counter never repeat. If, for example,
we're using a 32-bit counter, the counter will "reset" (go back to the starting
value) after 2<sup>32</sup> iterations, and will start repeating the same
sequence of random blocks as it did at the beginning. This introduces the
problem of lack of diffusion that we have seen before, just at a larger scale.
If we're using a 32-bit counter with a 128-bit block cipher, we cannot encrypt
more than 128·2<sup>32</sup> bits = 64 GiB of data at once. This is a very
important detail: exceeding these limits may allow the decryption of portions
of ciphertext without knowledge of the secret key.

<figure>
  <img src="{static}/images/counter-mode.svg" alt="Visualization of the Counter Mode (CTR) mode of operation">
</figure>

What Counter Mode is doing is effectively **turning a block cipher into a
stream cipher**. As such, a block cipher in Counter Mode has the exact same
malleability problems of stream ciphers that we have seen before.

<details markdown="block">
<summary>An example of malleability using AES-CTR with OpenSSL</summary>

This example is going to be very similar (almost identical) to the example with
ChaCha20 that I showed in the stream cipher section, just that this time I'm
going to use AES-256 in CTR mode.

Let's produce a valid ciphertext:

```sh
openssl enc -aes-256-ctr \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 0123456789abcdef0123456700000001 \
    -in <(echo 'Can you give me a ride to the party?') \
    -in <(echo 'Do not  give me a ride to the party!') \
    -out ciphertext.bin
```

Tamper it with Python:

```python
with open('ciphertext.bin', 'rb') as file:
    ciphertext = file.read()

guessed_message     = b'--------------------an ice cream----------\n'
replacement_message = b'--------------------to go to bed----------\n'

tampered_ciphertext = bytes(x ^ y ^ z for (x, y, z) in
                            zip(ciphertext, guessed_message, replacement_message))

with open('tampered-ciphertext.bin', 'wb') as file:
    file.write(tampered_ciphertext)
```

And now we can decrypt it:

```sh
openssl enc -d -aes-256-ctr \
    -K 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -iv 0123456789abcdef0123456700000001 \
    -in tampered-ciphertext.bin
```
</details>

# The solution: Authenticated Encryption (AE)

We have seen that stream ciphers and block ciphers (in their mode of operation)
both exhibit the same problem (in different flavors): malleability. I've shown
some examples of how this problem can be exploited with modern ciphers like
ChaCha20 and AES. These ciphers, alone, **cannot guarantee the integrity or
authenticity of encrypted data**.

In this context, [*integrity*](https://en.wikipedia.org/wiki/Data_integrity) is
the assurance that data is not corrupted or modified in any way.
[*Authenticity*](https://en.wikipedia.org/wiki/Message_authentication) can be
thought of as a stronger version of integrity, and it's the assurance that a
given ciphertext was produced only with knowledge of the secret key.

Does this mean that modern ciphers, like ChaCha20 and AES, should be considered
insecure and avoided? Absolutely not! The correct answer is that those ciphers
cannot be used alone. You should think of them as basic building blocks, and
you need some additional building blocks in order to construct a complete and
secure cryptosystem. One of these additional building blocks, that we are going
to explore in this article, is an algorithm that provides integrity and
authentication: welcome **Authenticated Encryption (AE)**.

When using authenticated encryption, an adversary may be able to modify a
ciphertext using the techniques described above, but such modification would be
detected by the authentication algorithm, and decryption will fail with an
error. The decrypted message at that point should be discarded, preventing the
use of tampered data.

There are many different methods to implement authenticated encryption. The
most common approach is to use an authentication algorithm to authenticate the
ciphertext produced by a cipher. Here I will describe two very popular
authentication algorithms:

- **Poly1305**, which is often used in conjunction with the stream cipher
  ChaCha20 to form **ChaCha20-Poly1305**;
- **Galois/Counter Mode (GCM)**, which is often used with the block cipher AES
  to form **AES-GCM**.

These authentication algorithms work by computing a hash of the ciphertext,
which is then stored alongside the ciphertext. This hash is not a regular hash,
but it's a **keyed hash**. A regular hash is a function that takes as input
some data and returns a fixed-size bit string:

$$\operatorname{hash}: data \rightarrow bits$$

A keyed hash instead takes two inputs: a secret key and some data, and produces
a fixed-size bit string:

$$\operatorname{keyed-hash}: (key, data) \rightarrow bits$$

The output of the keyed hash is more often called *Message Authentication Code
(MAC)*, or *authentication tag*, or even just *tag*.

During decryption, the same authentication algorithm is run again on the
ciphertext, and a new tag is produced. If the new tag matches the original tag
(that was stored alongside the ciphertext), then decryption succeeds. Else, if
the tags don't match, it means that the ciphertext was modified (or the stored
tag was modified), and decryption fails. This gives us a way to detect
tampering and gives us the opportunity to reject ciphertexts that were not
produced by the secret key.

The secret key passed to the keyed hash function is not necessarily the same
secret key used for the encryption. In fact, both ChaCha20-Poly1305 and AES-GCM
operate on a **subkey** derived from the key used for encryption.

## Poly1305

Poly1305 is a keyed hash function proposed by [Daniel J.
Bernstein](https://en.wikipedia.org/wiki/Daniel_J._Bernstein) in 2004, who is
also the author of ChaCha20. It works by using **polynomials evaluated modulo
the prime 2<sup>130</sup> - 5**, hence the name.

The key to Poly1305 is a 256-bit string, and it's split into two halves:

- the first half (128 bits) is called $r$;
- the second half (128 bits) is called $s$.

We'll see later how this key is generated when Poly1305 is used to implement
authenticated encryption. For now, let's assume that the key is a random
(unpredictable) bit string provided as an input.

The first half $r$ is also *clamped* by setting some of its bits to 0. This is
a performance-related optimization that some Poly1305 implementations can take
advantage of when doing multiplication using 64-bit registers. Clamping is
performed by applying the following hexadecimal bitmask:

```
0ffffffc0ffffffc0ffffffc0fffffff
```

The message to authenticate is split into chunks of 128 bits each: $m_1$,
$m_2$, $m_3$, ... $m_n$. If the length of the message is not a multiple of 128
bits, then the last block may be shorter. The authentication tag is then
calculated as follows:

*   Interpret $r$ and $s$ as two 128-bit little-endian integers.

*   Initialize the Poly1305 state $a_0$ to the integer 0. As we shall see
    later, this state will need to hold at most 131 bits.

*   For each block $m_i$:

    *   Interpret the block $m_i$ as a little-endian integer.

    *   Compute $\overline{m}_i$ by appending a 1-bit to the end of the block
        $m_i$.  If $m_i$ is 128 bits long, then this is equivalent to computing
        $\overline{m}_i = 2^{128} + m_i$. In general, if the length of the
        block $m_i$ in bits is $\operatorname{len}(m_i)$, then this is
        equivalent to $\overline{m}_i = 2^{\operatorname{len}(m_i)} + m_i$.

        This step ensures that the resulting block $\overline{m}_i$ is always
        non-zero, even if the original block $\overline{m}_i$ is zero. This is
        important for the security of the algorithm, as explained later.

    *   Compute the new state $a\_i = (a\_{i-1} + \overline{m}\_i) \cdot r
        \pmod{2^{130} - 5}$. Note that, because the operation is modulo
        $2^{130} - 5$, the result will always fit in 130 bits.

*   Once each block has been processed, compute the final state
    $a_{n+1} = a_n + s$. Note that the state $a_n$ is at most 130 bits long,
    and $s$ is at most 128 bits long, hence the result will be at most 131 bits
    long.

*   Truncate the final state $a_{n+1}$ to 128 bits by removing the most
    significant bits.

*   Return the truncated final state $a_{n+1}$ as a little-endian byte string.

What this method is doing is computing the following polynomial in $r$ and $s$:

$$\begin{align\*}
  tag
  & = ((((((\overline{m}_1 \cdot r) + \overline{m}_2) \cdot r) + \cdots + \overline{m}_n) \cdot r) \bmod{(2^{130} - 5)}) + s \\\\
  & = (\overline{m}_1 r^n + \overline{m}_2 r^{n-1} + \cdots + \overline{m}_n r) \bmod{(2^{130} - 5)} + s
\end{align\*}$$

$r$ and $s$ are secrets, and they come from the Poly1305 key. Note that if we
didn't add $s$ at the end, then the resulting polynomial would be a polynomial
in $r$, and one could use polynomial root-finding methods to figure out $r$
from the authentication tag, without knowledge of the key. Therefore it's
important that $s$ is non-zero.

In Python, this is what a Poly1305 implementation could look like (disclaimer:
this is for learning purposes, and not necessarily secure or optimized for
performance):

```python
def iter_blocks(message: bytes):
    """
    Splits a message in blocks of 16 bytes (128 bits) each, except for the last
    block, which may be shorter.
    """
    start = 0
    while start < len(message):
        yield message[start:start+16]
        start += 16

def poly1305(key: bytes, message: bytes):
    assert len(key) == 32  # 256 bits

    # Prime for the evaluation of the polynomial
    p = (1 << 130) - 5

    # Split the key into two parts r and s
    r = int.from_bytes(key[:16], 'little')  # 128 bits
    s = int.from_bytes(key[16:], 'little')  # 128 bits
    # Clamp r
    r = r & 0x0ffffffc0ffffffc0ffffffc0fffffff

    # Initialize the state
    a = 0

    # Update the state with every block
    for block in iter_blocks(message):
        # Append a 1-bit to the end of each block
        block = block + b'\1'
        # Convert the block to an integer
        c = int.from_bytes(block, 'little')
        # Update the state
        a = ((a + c) * r) % p

    # Add s to the state and truncate it to 128 bits, removing the most
    # significant bits and keeping only the least significant 128 bits
    a = (a + s) & ((1 << 128) - 1)

    # Convert the state from an integer to a 16-byte string (128 bits)
    return a.to_bytes(16, 'little')
```

And here is an example of how that code could be used:

```
key = bytes.fromhex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
msg = b'I had a very nice day today at the beach'
print(poly1305(key, msg).hex())
```

This returns `b0c4cb74b3089e9a982e3baa90c1bb5f`, which is the same result that
we would get using OpenSSL:

```sh
openssl mac \
    -macopt hexkey:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
    -in <(echo -n 'I had a very nice day today at the beach') \
    poly1305
```

A few things to note:

*   The same key cannot be reused to construct two distinct tags. In fact,
    suppose that we use the same hash key to compute `tag1 = Poly1305(key,
    msg1)` and `tag2 = Poly1305(key, msg2)`. Then, because $s$ is the same for
    both, we could subtract the two tags (`tag1 - tag2`) to remove the $s$ part
    and obtain a polynomial in $r$. From there, we could use algebraic methods
    to figure out $r$. Once we have $r$, we can use either one of the tags and
    compute $s$, therefore recovering the full secret key.

    Similarly, if the keys were generated using a predictable algorithm (for
    example, incrementally: `key[i+1] = key[i] + 1`), it would still be
    possible to use a similar approach to figure out the secret key.

    For this reason, **Poly1305 keys must be unique and unpredictable**.
    Generating Poly1305 keys randomly or pseudo-randomly is an acceptable
    approach. Authentication functions like Poly1305 are called **one-time
    authenticators** because they can be used only one time with the same key.

*   If we didn't add the 1-bits at the end of each block (in other words, if we
    used the $m_i$ blocks instead of $\overline{m}_i$), then encrypting a
    message full of zero bits would be the equivalent of encrypting an empty
    message.  Adding the 1-bits is a way to ensure that the length of the
    message always has an effect on the output.

### Use of Poly1305 with ChaCha20 (ChaCha20-Poly1305)

Let's see how we can combine ChaCha20 and Poly1305 to construct an authenticated cipher. To recap:

* ChaCha20 is a stream cipher;
* Poly1305 is a one-time authenticator;
* ChaCha20, like most ciphers, requires the use of a unique nonce to allow key
  reuse.

Putting the two together gives birth to ChaCha20-Poly1305. Here I'm going to
describe how to implement it as standardized in [RFC
8439](https://www.rfc-editor.org/rfc/rfc8439).

The **inputs to the ChaCha20-Poly1305 encryption function** are:

* a 256-bit secret key;
* a 96-bit nonce;
* a variable-length plaintext message.

The **outputs from the ChaCha20-Poly1305 encryption function** are:

* a variable-length ciphertext (same length as the input plaintext);
* a 128-bit authentication tag.

The **ChaCha20-Poly1305 decryption function** will accept the same secret key,
nonce, ciphertext, and authentication tag as the input, and produce either the
plaintext or an error as the output. The error is returned in case the
authentication fails.

<figure>
  <img src="{static}/images/chacha20-poly1305-encryption.svg" alt="Diagram of data flow during encryption with ChaCha20-Poly1305">
  <figcaption>Data flow during a ChaCha20-Poly1305 encryption. This shows the inputs in <span style="color:#3465a4;font-weight:bold">blue</span>, the outputs in <span style="color:#73d216;font-weight:bold">green</span>, and the intermediate objects in <span style="color:#cc0000;font-weight:bold">red</span>.</figcaption>
</figure>

ChaCha20-Poly1305 works in the following way:

1.  The **ChaCha20** stream cipher is **initialized** with the 256-bit secret key and
    the 96-bit nonce.

1.  The stream cipher is used to encrypt a 256-bit string of all zeros. The
    result is the **Poly1305 subkey**.

    If you recall how a stream cipher works, you should know that encrypting
    using a stream cipher is equivalent to performing the XOR of a random bit
    stream with the plaintext. Here the plaintext is all zeros, so the process
    of generating the Poly1305 subkey is equivalent to grabbing the first 256
    bits from the ChaCha20 bit stream.

    We previously saw that the Poly1305 subkey must be unpredictable and unique
    in order for Poly1305 to be secure. The use of ChaCha20 with a unique nonce
    ensures that: because ChaCha20 is a stream cipher, its output will be
    random and unpredictable. Therefore, with this construction, the subkey
    will be unpredictable even if the nonce is predictable.

1.  The stream cipher is used to encrypt another 256-bit string. The result is
    discarded. This is equivalent to advancing the stream cipher state by 256
    bits.

    This step may seem weird, and in fact is not needed for security purposes,
    but it's a mere implementation detail. This step is here because ChaCha20
    has an internal state of 512 bits. In the previous step we obtained the
    first 256 bits of the state, and this next step is to discard the rest of
    the state to start with a fresh state. There is no particular reason for
    requiring a fresh state. The reason why RFC 8439 does that is because...
    spoiler alert: ChaCha20 is a block cipher under the hood. Its block size is
    512 bits. If you read the RFC, you'll see that it asks to call the ChaCha20
    block encryption function once, grab the first 256 bits, and discard the
    rest. Here I'm treating ChaCha20 as a stream cipher, so I have to include
    this extra step to discard the bits.

1.  The **plaintext** is **encrypted** using the stream cipher.

    Note that this is done without resetting the state of the cipher. We are
    continuing to use the same stream cipher instance that was used to generate
    the Poly1305 subkey.

1.  The **ciphertext** is **padded** with zeros to make its length a multiple
    of 16 bytes (128 bits) and is **authenticated using Poly1305**, via the
    subkey generated in step 2.

    This step may be done in parallel to the previous one, that is: every time
    we generate a chunk of ciphertext, we feed it to the Poly1305
    authentication function.

    Why pad the ciphertext before passing it to Poly1305? After all, ChaCha20
    is a stream cipher, and Poly1305 can accept arbitrary-sized messages.
    Again, this is an detail of RFC 8439 and padding does not serve any
    specific purpose.

1.  The **length** of the **ciphertext** (in bytes) is fed into the **Poly1305
    authenticator**. This length is represented as a 64-bit little-endian
    integer padded with 64 zero bits.

    The reason why the length is represented as 64 bits and padded (instead of
    representing it as 128 bits) will be clearer later: what I have given you
    so far is a simplified view of ChaCha20-Poly1305 and authenticated
    encryption in general. I will give you the full picture when talking about
    [associated data](#authenticated-encryption-with-associated-data-aead)
    later on, and at that point this step will be slightly modified.

1.  The ciphertext from ChaCha20 and the authentication tag from Poly1305 are
    returned.

The decryption algorithm works in a very similar way: ChaCha20 is initialized
in the same way, the subkey is generated in the same way, the Poly1305
authentication tag is calculated from the ciphertext in the same way. The only
difference is that ChaCha20 is used to decrypt the ciphertext (instead of
encrypting the plaintext) and that the input authentication tag is compared to
the calculated authentication tag before returning.

Here is a Python implementation of ChaCha20-Poly1305, based on the
implementations of ChaCha20 and Poly1305 from
[pycryptodome](https://pypi.org/project/pycryptodome/) (usual disclaimer: this
code is for educational purposes, and is not necessarily secure or optimized
for performance):

```python
from Crypto.Cipher import ChaCha20
from Crypto.Hash import Poly1305

def chacha20poly1305_encrypt(key, nonce, message):
    assert len(key) == 32  # 256 bits
    assert len(nonce) == 12  # 96 bits

    # Initialize the ChaCha20 cipher with the key and nonce
    cipher = ChaCha20.new(key=key, nonce=nonce)

    # Derive the Poly1305 subkey using the ChaCha20 cipher
    subkey = cipher.encrypt(b'\0' * 32)  # 256 bits
    subkey_r = subkey[:16]
    subkey_s = subkey[16:]

    # Initialize the Poly1305 authenticator with the subkey
    authenticator = Poly1305.Poly1305_MAC(r=subkey_r, s=subkey_s, data=None)

    # Discard the rest of the internal ChaCha20 state
    cipher.encrypt(b'\0' * 32)  # 256 bits

    # Encrypt the message
    ciphertext = cipher.encrypt(message)

    # Authenticate the ciphertext
    authenticator.update(ciphertext)
    # Pad the ciphertext with zeros (to make it a multiple of 16 bytes)
    if len(ciphertext) % 16 != 0:
        authenticator.update(b'\0' * (16 - len(ciphertext) % 16))
    # Authenticate the length of the associated data (0 for simplicity)
    authenticator.update((0).to_bytes(8, 'little'))  # 64 bits
    # Authenticate the length of the ciphertext
    authenticator.update(len(ciphertext).to_bytes(8, 'little'))  # 64 bits
    # Generate the authentication tag
    tag = authenticator.digest()

    return (ciphertext, tag)

def chacha20poly1305_decrypt(key, nonce, ciphertext, tag):
    assert len(key) == 32  # 256 bits
    assert len(nonce) == 12  # 96 bits
    assert len(tag) == 16  # 128 bits

    # Initialize the ChaCha20 cipher and the Poly1305 authenticator, in the
    # same exact way as it was done during encryption
    cipher = ChaCha20.new(key=key, nonce=nonce)

    subkey = cipher.encrypt(b'\0' * 32)
    subkey_r = subkey[:16]
    subkey_s = subkey[16:]
    authenticator = Poly1305.Poly1305_MAC(r=subkey_r, s=subkey_s, data=None)

    cipher.encrypt(b'\0' * 32)

    # Generate the authentication tag, like during encryption
    authenticator.update(ciphertext)
    if len(ciphertext) % 16:
        authenticator.update(b'\0' * (16 - len(ciphertext) % 16))
    authenticator.update((0).to_bytes(8, 'little'))
    authenticator.update(len(ciphertext).to_bytes(8, 'little'))
    expected_tag = authenticator.digest()

    # Compare the input tag with the generated tag. If they're different, the
    # plaintext must not be returned to the caller
    if tag != expected_tag:
        raise ValueError('authentication failed')

    # The two tags match; decrypt the plaintext and return it to the caller
    # Note that, because ChaCha20 is a symmetric cipher, there is no difference
    # between the encrypt and decrypt method: here we are reusing the same
    # exact code used during decryption
    message = cipher.encrypt(ciphertext)

    return message
```

And here is how it can be used:

```python
key = bytes.fromhex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
nonce = bytes.fromhex('0123456789abcdef01234567')
message = b'I wanted to go to the beach, but now I changed my mind'

ciphertext, tag = chacha20poly1305_encrypt(key, nonce, message)
decrypted_message = chacha20poly1305_decrypt(key, nonce, ciphertext, tag)
assert message == decrypted_message

print(f'ciphertext: {ciphertext.hex()}')
print(f'       tag: {tag.hex()}')
print(f' plaintext: {decrypted_message}')
```

Running it produces the following output:

```
ciphertext: 5d9b09cc5d90ca9ddff2d3470cfd6b563c5158e952bfae6acf1ebf9a3b968a488a41969567ef5ccfe05dcf9e548567028ff374a754af
       tag: dac3c05d261920e278ceb22e2800aa95
 plaintext: b'I wanted to go to the beach, but now I changed my mind'
```

This is the same output we would obtain by using the ChaCha20-Poly1305
implementation from pycryptodome directly:

```python
from Crypto.Cipher import ChaCha20_Poly1305

key = bytes.fromhex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
nonce = bytes.fromhex('0123456789abcdef01234567')
message = b'I wanted to go to the beach, but now I changed my mind'

cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
ciphertext, tag = cipher.encrypt_and_digest(message)

print(f'ciphertext: {ciphertext.hex()}')
print(f'       tag: {tag.hex()}')
```

As already stated, it is extremely important that the nonce passed to
ChaCha20-Poly1305 is unique. It may be predictable, but it must be unique. If
the same nonce is reused twice or more, we can:

*   Decrypt arbitrary messages without using the secret key, if we can guess at
    least one message from its ciphertext.

    This can be done using the techniques described at the beginning of this
    article: by recovering the random bit string from the XOR of the ciphertext
    with the guessed message.

*   Recover the Poly1305 subkey, and, at that point, tamper with ciphertexts
    and forge new, valid authentication tags.

    This can be done by using algebraic methods on the polynomial of the
    authentication tag.

There is also a variant of ChaCha20-Poly1305, called XChaCha20-Poly1305, that
features an extended 192-bit nonce (the X stands for 'extended'). This is
described in an [RFC
draft](https://datatracker.ietf.org/doc/html/draft-irtf-cfrg-xchacha) but so
far it hasn't been accepted as a standard yet. I won't cover XChaCha20 in
detail here, because it's slightly more complex and does not add much to the
topic of this article, but XChaCha20-Poly1305 has better security properties
than ChaCha20-Poly1305, so you should prefer it in your applications if you can
use it. The reason why XChaCha20-Poly1305 has better properties than
ChaCha20-Poly1305 is that, having a longer nonce, the probability of generating
two random nonces with the same value are much lower.

## Galois/Counter Mode (GCM)

Let's now take a look at Galois/Counter Mode (GCM). This is commonly used with
the Advanced Encryption Standard (AES), to construct the authenticated cipher
AES-GCM. One main difference between Poly1305 and GCM is that Poly1305 can work
with any stream or block cipher, while GCM is designed to work with block
ciphers with a block size of 128 bits.

GCM was proposed by David McGrew and John Viega in 2004 and is standardized in
[NIST Special Publication
800-38D](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-38d.pdf)
as well as [RFC 5288](https://www.rfc-editor.org/rfc/rfc5288). It takes its
name from Galois fields, also known as [finite
fields](https://en.wikipedia.org/wiki/Finite_field), which in turn get their
name from the French mathematician [Évariste
Galois](https://en.wikipedia.org/wiki/%C3%89variste_Galois), who introduced the
concept of finite fields as we know them today.

As we did before with Poly1305, we are going to first see how the keyed hash
function used by GCM works, and then we will see how to use it to construct an
authenticated cipher like AES-GCM on top of it. Before we can do that though,
we need to understand what finite fields are, and what specific types of finite
fields are used in GCM.

### Finite Fields (Galois Fields)

What is a field? A field is a mathematical structure that contains a bunch of
elements, and those elements can interact with each other using addition and
multiplication. For both these operations there's an identity element and an
inverse element. Addition and multiplication in a field must obey the usual
properties that we're used to: commutativity, associativity, and
distributivity.

A well-known example of a field is the field of fractions.  Here is why
fractions form a field:

* the **elements** of the field are the fractions;
* **addition** is well-defined: if we add two fractions, we get a fraction out
  (example: $5/3 + 3/2 = 19/6$);
* **multiplication** is also well-defined: if we multiply two fractions, we get
  a fraction out (example: $1/2 \cdot 8/3 = 4/3$);
* the **additive identity element** is 0: if we add 0 to any fraction, we get
  the same fraction back;
* the **additive inverse element** is the negated fraction (example: $5/1$ is
  the additive inverse of $-5/1$ because $5/1 + (-5/1) = 0$);
* the **multiplicative identity element** is 1: multiplying any fraction by 1
  yields the same fraction back;
* the **multiplicative inverse element** is what we get if we swap the
  numerator with the denominator (example: $3/2$ is the multiplicative inverse
  of $2/3$ because $3/2 \cdot 2/3 = 1$)—except for 0, which does not have a
  multiplicative inverse.
* and so on...

On top of addition, multiplication, and inverse elements, we can define derived
operations like subtraction and division. Subtracting $a$ from $b$ is
equivalent to adding $a$ to the additive inverse of $b$: $a - b = a + (-b)$.
Similarly, division can be defined in terms of multiplication with
multiplicative inverses ($a / b = a b^{-1}$).

Fields are a generalization of structures where addition, multiplication,
subtraction, and division behave according to the rules that we're used to.
Field elements do not necessarily need to be numbers.

An example of something that is *not* a field is the integers. That's because
integers don't have multiplicative inverses (for example, there's no integer
that multiplied by 5 makes the result equal to 1). However, there is a way to
turn the integers into a field: if we take the integers and a prime number *p*,
then we can construct the **field of integers modulo _p_**.

When we work with the integers modulo a prime *p*, whenever we see *p* appear
in any of our expressions, we can replace it with 0. In other words, in such a
field, *p* and 0 are two different ways to write the same element--they are two
different *representations* of the same element.

Here is an example: in the field of integers modulo 7, the expression 5 + 3
equals 1, because:

- 5 + 3 evaluates to 8;
- 8, by definition, is 7 + 1;
- if 7 and 0 are the same element, then 7 + 1 is equal to 0 + 1
- 0 + 1 evaluates to 1

What we have just seen is that 8 is just a different representation of 1, just
like 7 is a different representation of 0. Different symbols, same object.
Just like, in programming languages, we can have multiple variables pointing to
the same memory location: here the numbers are like variables, and what they
point to is what really matters.

In the field of integers modulo 7, the additive inverse for 5 is 2, because 5
+ 2 = 7 = 0. If we manipulate the equation, we get that 5 = −2. In other words,
5 and −2 are two different representations for the same element, and similarly
2 and −5 are also two different representations of the same element. A similar
story holds for multiplication: the multiplicative inverse for 5 is 3 because:
5 · 3 = 15 = 7 + 7 + 1 = 1, so we can write 5 = 3<sup>−1</sup> as well as 3 =
5<sup>−1</sup>.

What we have just seen is an example of a **finite field**. It's different from
a general field because it contains a finite number of elements (unlike
fractions, which do not have a limit). In the case of the integers modulo 7,
the number of elements is 7, and the list of elements is: {0, 1, 2, 3, 4, 5,
6}, or {−3, −2, −1, 0, 1, 2, 3}, or {0, 1, 2, 3, 2<sup>−1</sup>,
3<sup>−1</sup>, 6}, depending on what representation we like the most.

<details markdown="block">
<summary>A few words about terminology, notation, and equivalences of finite fields</summary>

There can be many ways to construct a finite field (or even a general field). I
have given an example using numbers, but a field does not necessarily need to
be formed from numbers. We can also use vectors, matrices, polynomials, and
anything you would like. As long as addition, multiplication, identity
elements, and inverse elements are well-defined, you can get a field. Using
programming terms, you can think of a field as an interface or a trait that can
have arbitrary implementations.

An important result in algebra is that finite fields with the same number of
elements are "unique up to isomorphism". This means that if two finite fields
have the same number of elements, then there is an equivalence relation between
the two. The number of elements of a field is therefore enough to define a
field. It's not enough to tell us what the elements of the field look like, or
how they can be represented, but it's enough to know how it behaves. To denote
a field with $n$ elements, there are two major notations: $GF(n)$ and
$\mathbb{F}_{n}$.

Another important result in algebra is that $n$ may be either a prime number,
or a power of a prime. For example, we can have finite fields with 2 elements,
or with 9 (= 3<sup>2</sup>) elements, but we cannot have a field with 6 (= 2·3)
elements. For this reason, you will often find finite fields denoted as
$GF(p^k)$ or $\mathbb{F}\_{p^k}$, where $p$ is a prime and $k$ is an integer
greater than 0. The prime $p$ is called *characteristic* of the field, while $n
= p^k$ is called *order* of the field.

Some common fields also have their own notation: in particular, the field of
integers modulo a prime $p$ is denoted as $Z/pZ$. This notation encodes the
"building instructions" to construct the field, in fact:

* $Z$ denotes the integers: $Z = \\{\dots, -2, -1, 0, 1, 2, \dots\\}$;
* $pZ$ denotes the integers multiplied by $p$: $pZ = \\{\dots, -2p, -p, 0, p,
  2p\\}$ (example: $2Z = \\{\dots, -4, -2, 0, 2, 4, \dots\\}$);
* $A/B$ is a _quotient_. This is a way to define an equivalence relation
  between elements, and its meaning is: within $A/B$, all the elements of $B$
  are equivalent to 0. In the case of $Z/pZ$, all the multiples of $p$ are
  equivalent to 0, which is indeed what happens with the integers modulo $p$.
  The way I described this equivalence relation earlier is by saying that
  multiples of $p$ are different representations for 0.

Note that the integers modulo a power of a prime ($Z/p^kZ$, with $k$ greater
than 1) do not form a field. The problem is that elements in $Z/p^kZ$ sometimes
do not have a multiplicative inverse. For example, in $Z/4Z$, the number 2 does
not have a multiplicative inverse (there is no element that multiplied by 2
gives 1). A field $GF(p^k)$ with $k$ greater than 1 needs to be constructed in
a different way. One such way is to use polynomials, as described in the next
section.
</details>

#### Polynomial fields

Let's now move our attention from integers to polynomials, like this one:

$$x^7 + 5x^3 - 9x^2 + 2x + 1$$

Polynomials are a sum of coefficients multiplied by a variable (usually denoted
by the letter *x*) raised to an integral power.

Let's restrict our view to polynomials that have integer coefficients, like the
one shown above. Something that is _not_ a polynomial with integer coefficients
is $1/2 x^2 + x$, because it has a fraction in it.

Integers and polynomials with integer coefficients are somewhat similar to each
other. They kinda behave the same in many aspects. One important property of
integers is the [unique factorization
theorem](https://en.wikipedia.org/wiki/Fundamental_theorem_of_arithmetic): if
we have an integer, there's a way to write it as a multiplication of some
primary factors. For example, the integer 350 can be factored as the
multiplication of 2, 5, 5, and 7.

$$350 = 7 \cdot 5 \cdot 5 \cdot 2$$

This factorization is *unique*: we can change the order of the factors, but
it's not possible to obtain a different set of factors (there's no way to make
the number 3 appear in the factorization of 350, or to make the number 7
disappear).

Polynomials with integer coefficients also have a unique factorization. In the
case of integers, We call the unique factors "prime numbers"; in the case of
polynomials we have "irreducible polynomials". And just like we can have a
field of integers modulo a prime, we can have a **field of polynomials modulo
an irreducible polynomial**.

| Integers                                       | Polynomials (with integer coefficients)                       |
| ---------------------------------------------- | ------------------------------------------------------------- |
| Unique factorization: $42 = 7 \cdot 3 \cdot 2$ | Unique factorization: $x^3 - 1 = (x^2 + x + 1)(x - 1)$        |
| Prime numbers: 2, 3, 5, 7, 11, …               | Irreducible polynomials: $x + 1$, $x^2 - 2$, $x^2 + x + 1$, … |
| Integers modulo a prime number                 | Polynomials modulo an irreducible polynomial                  |

Let's take a look at how arithmetic in polynomial fields works. Let's take, for
example, the field of polynomials with integer coefficients modulo $x^3 + x +
1$, and try to compute the result of $(x^2 + 1)(x^2 + 2)$. If we expand the
expression, we get:

$$(x^2 + 1)(x^2 + 2) = x^4 + 3x^2 + 2$$

This expression can be *reduced*. Reducing a polynomial expression is the
equivalent of what we were doing with the integers modulo a prime, when we were
saying that 8 = 7 + 1 = 1 (mod 7). That "conversion" from 8 to 1 is the
equivalent of the reduction that we're talking about here.

To reduce $x^4 + 3x^2 + 2$, first note that $x^4 = x \cdot x^3$. Also note that
$x^3 = x^3 + x + 1 - x - 1$. Here we have just added and removed the term $x +
1$: the result hasn't changed, but now the irreducible polynomial $x^3 + x + 1$
appears in the expression, and so we can substitute it with 0. Putting
everything together, we get:

$$\begin{align\*}
(x^2 + 1)(x^2 + 2) & = x^4 + 3x^2 + 2 \\\\
                   & = x \cdot x^3 + 3x^2 + 2 \\\\
                   & = x \cdot (x^3 + x + 1 - x - 1) + 3x^2 + 2 \\\\
                   & = x \cdot (0 - x - 1) + 3x^2 + 2 \\\\
                   & = -x^2 - x + 3x^2 + 2 \\\\
                   & = 2x^2 - x + 2
\end{align\*}$$

It's interesting to note that, if the polynomial field is formed by an
irreducible polynomial with degree $n$, then all the polynomials in that field
will all have degree less than $n$. That's because if any $x^n$ (or higher)
appears in a polynomial expression, then we can use the substitution trick I
just showed to reduce its degree.

#### Binary fields

Let's now look at polynomials where **coefficients are from the field of
integers modulo 2**, meaning that they can be either 0 or 1. This is an example
of such a polynomial:

$$x^7 + x^4 + x^2 + 1$$

or, in a more explicit form, where we can clearly see all the coefficients:

$$1 x^7 + 0 x^6 + 0 x^5 + 1 x^4 + 0 x^3 + 1 x^2 + 0 x^1 + 1 x^0$$

These are called **binary polynomials**. It's interesting to note that if we
ignore the variables and the powers, and keep only the coefficients, then what
we get is a **bit string**:

$$(1 0 0 1 0 1 0 1)$$

This suggests that there's an interesting duality between binary polynomials
and bit strings. This means, in particular, that binary polynomials can be
represented in a very compact and natural way on computers.

The duality between binary polynomials and bit strings also suggests that
perhaps we can use bitwise operations to perform arithmetic on binary
polynomials. And this turns out to be true, in fact:

* binary polynomial addition can be computed using the XOR operator on the two
  corresponding bit strings;
* binary polynomial multiplication can be computed using XOR, AND and
  bit-shifting.

Computers are pretty fast at performing these bitwise operations, and this
makes binary polynomials quite attractive for use in computer algorithms and
cryptography.

<details markdown="block">
<summary>Arithmetic with binary polynomials</summary>

The arithmetic of such polynomials is quite interesting: in fact, because $1 +
1 = 0$ (modulo 2), then also $x^k + x^k = 0$, in fact:

$$1 \cdot x^k + 1 \cdot x^k = (1 + 1) x^k = 0 \cdot x^k = 0$$

It's easy to see that addition modulo 2 is equivalent to the XOR binary
operator. And addition of two binary polynomials is equivalent to the bitwise
XOR of their corresponding bit strings:

$$\begin{array}{ccccc}
(x^3 + x^2 + 1) & +      & (x^2 + x)    & = & x^3 + x + 1 \\\\
\updownarrow    &        & \updownarrow &   & \updownarrow \\\\
(1101)          & \oplus & (0110)       & = & (1011)
\end{array}$$

Multiplication of binary polynomials can also be implemented as a bitwise
operation on bit strings. First, note that multiplying a polynomial by a
monomial is equivalent to bit-shifting:

$$\begin{array}{ccccc}
(x^3 + x + 1) & \cdot  & x^2          & = & x^5 + x^3 + x^2 \\\\
\updownarrow  &        & \updownarrow &   & \updownarrow \\\\
(1011)        & \ll    & 2            & = & (101100)
\end{array}$$

Then note that multiplication of two polynomials can be expressed as the sum of
multiplications by monomials:

$$(x^3 + 1)(x^2 + x + 1) = (x^3 + 1) \cdot x^2 + (x^3 + 1) \cdot x^1 + (x^3 + 1) \cdot x^0$$

Putting everything together, we have multiplications by monomials (equivalent
to bit-shifts) and sums (equivalent to bitwise XOR). This suggests that
multiplication can be implemented on top of bitwise XOR and bit-shifting.

Here is some Python code to implement binary polynomial multiplication, where
each polynomial is represented compactly as an `int`:

```python
def multiply(a, b):
    """
    Compute a*b, where a and b are two integers representing binary
    polynomials.

    a and b are expected to have their most significant bit set to
    the monomial with the highest power. For example, the polynomial
    x^8 is represented as the integer 0b10000.
    """
    assert a >= 0
    assert b >= 0

    result = 0
    while b:
        result ^= a * (b & 1)
        a <<= 1
        b >>= 1
    return result
```

Other than XOR and bit-shifting, this code also uses AND to "query" whether a
certain monomial is present or not.

Here is an example of how to use the code:

```python
a = 0b0101_0111              # x^6 + x^4 + x^2 + x + 1
b = 0b0001_1010              # x^4 + x^3 + x
c = multiply(a, b)
assert c == 0b0111_0110_0110 # x^10 + x^9 + x^8 + x^6 + x^5 + x^2 + x
```
</details>

Now that we have introduced binary polynomials, we can of course form **binary
polynomials modulo a binary irreducible polynomial**. These form a finite
field, which is more concisely called: **binary field**.

Note that in a binary field where the modulo is an irreducible polynomial of
degree $n$, all polynomials in the field can be represented as $n$-bit strings,
and all $n$-bit strings have a corresponding binary polynomial in the field.

<details markdown="block">
<summary>Arithmetic in binary fields</summary>

If we have three integers $a$, $b$, and $p$, we can compute $(a + b) \bmod{p}$
or $a \cdot b \bmod{p}$ by performing the binary operation (addition or
multiplication) and then taking the remainder of the division by $p$. This is a
method that returns the results of addition or multiplication using a
representation with the lowest number of digits possible.

What if instead of having 3 integers we have three binary polynomials $A$, $B$,
and $P$ and we want to compute $(A + B) \bmod{P}$ or $A \cdot B \bmod{P}$? It
turns out that these operations can be implemented with code that is even
easier than the integer counterpart: no division needs to be involved!

Let's start with addition: we have already seen that addition with binary
polynomials can be implemented with a simple XOR operation. This means that if
the degree of $A$ and $B$ is lower than the degree of $P$, then the result of
$A + B$ is also going to have degree less than $P$, hence no reduction is
needed. We can use the result as-is, without any transformation: **adding two
binary field elements can be implemented with a single XOR operation**.

With multiplication the story is different: the product $A \cdot B$ may have
degree equal to or higher than $P$. For example, if $A = B = x$ and $P = x^2 +
1$, the product $A \cdot B$ is equal to $x^2$, which has the same degree as
$P$. We need to find a way to efficiently reduce the higher-degree terms of
this product. To see one way to do that, note that we can write $P$ like this:

$$P = x^n + Q$$

where $n$ is the degree of $P$ (the maximum power of $P$) and $Q$ is another
binary polynomial, with degree strictly lower than $n$. Rearranging the
equation, we get:

$$x^n = P + Q$$

Note that subtraction and addition are the same operations in a binary field.
Because $P$ equals 0, we can write:

$$x^n = Q$$

This equivalence gives us a way to eliminate higher-level terms that appear
during multiplication: whenever we see an $x^n$ appearing in the result, we can
remove that term and add $Q$ instead. One way to do that, using binary strings,
is to discard the highest bit (the one corresponding to $x^n$) and XOR with
the binary string corresponding to $Q$.

Another way to do it is to just add $P$ (XOR by the binary string corresponding
to $P$). This is equivalent to adding 0, results in the more compact
representation that we're interested in.

We could use similar tricks to eliminate terms like $x^{n+1}$, but these tricks
are not necessary if we eliminate $x^n$ terms as soon as they appear in an
iterative way.

Here is some Python code for multiplication in binary fields that uses the "add
$P$" trick just described:

```python
def multiply(a, b, p):
    """
    Compute a*b modulo p, where a, b and c are three integers representing
    binary polynomials.

    a, b and p are expected to have their most significant bit set to the
    highest power monomial. For example, the polynomial x^8 is represented as
    0b10000.
    """
    bit_length = p.bit_length() - 1
    assert a >= 0 and a < (1 << bit_length)
    assert b >= 0 and b < (1 << bit_length)

    result = 0
    for i in range(bit_length):
        result ^= a * (b & 1)
        a <<= 1
        a ^= p * ((a >> bit_length) & 1)
        b >>= 1
    return result
```

This code is essentially the same as the binary polynomial multiplication code we had before, except for this line in the `for` loop:

```python
a ^= p * ((a >> bit_length) & 1)
```

This line is what "adds $P$" whenever adding the shifted $A$ would result in a
$x^n$ term to appear.

Again, we achieved implementing **multiplication using only XOR, AND and
bit-shifting**.

Note that the binary polynomial $P$ here does not necessarily need to be an
irreducible polynomial for this algorithm to work. However, the resulting
algebraic structure won't be a field unless $P$ is irreducible. A similar story
holds for integers: we can have integers modulo a non-prime number, but that's
not a field.
</details>

### The GHASH keyed hash function

GCM uses a binary field. The irreducible binary polynomial that defines the
binary field used by GCM is:

$$P = x^{128} + x^7 + x^2 + x + 1$$

We will call this field the *GCM field*. Note that this polynomial has degree
128, hence the GCM field elements can be represented as 128-bit strings, and
each 128-bit string has a corresponding element in the GCM field.

The keyed hash function used by GCM is called GHASH and takes as input a
128-bit key. We will call this key $H$. This key is interpreted as an element
of the GCM field.

The message to authenticate is split into blocks of 128 bits each: $M_1$,
$M_2$, $M_3$, ... $M_n$. If the length of the message is not a multiple of 128
bits, then the last block is padded with zeros. Each block of message is also
interpreted as an element of the GCM field.

Here is how the authentication tag is computed from $H$ and the padded message
blocks $M_1$, ..., $M_n$:

* The initial state (a GCM field element) is initialized to 0: $A_0 = 0$.
* For every block of message $M_i$, the next state $A_i$ is computed as $A_i =
  (A_{i-1} + M_i) \cdot H \bmod{P}$.
* The final state $A_n$ is returned as a 128-bit string.

What this function is doing is computing the following polynomial in $H$:

$$\begin{align\*}
  Tag
  & = (((M_1 \cdot H + M_2) \cdot H + \cdots M_n) \cdot H) \bmod{P} \\\\
  & = (M_1 H^n + M_2 H^{n-1} + \cdots M_n H) \bmod{P}
\end{align\*}$$

This construction is somewhat similar to the one from Poly1305, although there
are important differences:

- In Poly1305, the elements of the tag polynomial are integers modulo a prime,
  in GHASH they are elements of a binary field.
- GHASH does not perform any step to encode the length of the message, hence
  the tag for an empty message will be the same as the tag for a sequence of
  zero blocks. We will see later that GCM fixes this problem by appending the
  length of the message to the end of the input passed to GHASH.
- Most importantly, the final $Tag$ polynomial is a polynomial in one unknown,
  and as such $H$ may be easily recoverable using algebraic methods. For this
  reason, **GHASH is not suitable as a secure one-time authenticator**. We will
  see that GCM fixes this problem by encrypting the output of GHASH.

### Use of GCM with AES (AES-GCM)

GCM is the combination of a block cipher, Counter Mode (CTR), and the GHASH
function that we have just seen. The block cipher is often AES. When we combine
AES with GCM, the what we get is AES-GCM, which is described below. However the
block cipher does not necessarily need to be AES: what is important is that the
block size of the cipher is 128 bits, and that's because GHASH only works on
128-bit blocks.

The **inputs to the AES-GCM encryption function** are:

* a secret key (the length of the key depends on the variant of AES used: if
  AES-128, this will be 128 bits);
* a 96-bit nonce;
* a variable-length plaintext message.

The **outputs of the AES-GCM encryption function** are:

* a variable-length ciphertext (same length as the input plaintext);
* a 128-bit authentication tag.

The **AES-GCM decryption function** will accept the same secret key, nonce,
ciphertext, and authentication tag as the input, and produce either the
plaintext or an error as the output. The error is returned in case the
authentication fails.

<figure>
  <img src="{static}/images/aes-gcm-encryption.svg" alt="Diagram of data flow during encryption with AES-GCM">
  <figcaption>Data flow during an AES-GCM encryption. This shows the inputs in <span style="color:#3465a4;font-weight:bold">blue</span>, the outputs in <span style="color:#73d216;font-weight:bold">green</span>, and the intermediate objects in <span style="color:#cc0000;font-weight:bold">red</span>.</figcaption>
</figure>

AES-GCM works in the following way:

1.  The **GHASH subkey** $H$ is generated by encrypting a zero-block: $H =
    \operatorname{Encrypt}(key, \underbrace{000\dots0}_\text{128 bits})$.

1.  The block cipher **AES** is **initialized** in Counter Mode (AES-CTR) with
    the key, the nonce, and a 32-bit, big-endian counter starting at **2**.

1.  The **plaintext** is **encrypted** using the instance of AES-CTR just
    created.

1.  The **GHASH** function is run with the following inputs:

    - the subkey $H$, computed in step 1;
    - the ciphertext padded with zeros to make its length a multiple of 16
      bytes (128 bits), concatenated to the length (in bits) of the ciphertext
      represented as a 128-bit big-endian integer.

    The result is a 128-bit block $S = \operatorname{GHASH}(H, ciphertext || padding || length)$.

1.  The AES-CTR **counter** is set to **1**.

1.  The block $S$ is then **encrypted** using AES-CTR. The result of the
    encryption is the **authentication tag**.

    Note that, because $S$ matches the block size of the cipher, this
    encryption won't cause the counter value 2 to be reused.

1.  The ciphertext and authentication tag are returned.

Here is how AES-GCM and GHASH can be implemented in Python, using the AES
implementation from [pycryptodome](https://pypi.org/project/pycryptodome/)
(usual disclaimer: this code is for educational purposes, and it's not
necessarily secure or optimized for performance):

```python
from Crypto.Cipher import AES

def multiply(a: int, b: int) -> int:
    """
    Compute a*b in the GCM field, where a and b are two integers representing
    elements of the GCM field.

    a and b are expected to have their least significant bit set to the highest
    power monomial. For example, the polynomial x^125 is represented as 0b100.
    """
    bit_length = 128
    q = 0xe1000000000000000000000000000000
    assert a >= 0 and a < (1 << bit_length)
    assert b >= 0 and b < (1 << bit_length)

    result = 0
    for i in range(bit_length):
        result ^= a * ((b >> 127) & 1)
        a = (a >> 1) ^ (q * (a & 1))
        b <<= 1
    return result

def pad_block(data: bytes) -> bytes:
    """
    Pad data with zero bytes so that the resulting length is a multiple of 16
    bytes (128 bits).
    """
    if len(data) % 16 != 0:
        data += b'\0' * (16 - len(data) % 16)
    return data

def iter_blocks_padded(data: bytes):
    """
    Split the given data into blocks of 16 bytes (128 bits) each, padding the
    last block with zeros if necessary.
    """
    start = 0
    while start < len(data):
        yield pad_block(data[start:start+16])
        start += 16

def ghash(subkey: bytes, message: bytes) -> bytes:
    subkey = int.from_bytes(subkey, 'big')
    assert subkey < (1 << 128)

    state = 0
    for block in iter_blocks_padded(message):
        block = int.from_bytes(block, 'big')
        state = multiply(state ^ block, subkey)

    return state.to_bytes(16, 'big')

def aes_gcm_encrypt(key: bytes, nonce: bytes, message: bytes):
    assert len(key) in (16, 24, 32)
    assert len(nonce) == 12

    # Initialize a raw AES instance and encrypt a 16-byte block of all zeros to
    # derive the GHASH subkey H
    cipher = AES.new(mode=AES.MODE_ECB, key=key)
    h = cipher.encrypt(b'\0' * 16)

    # Encrypt the message with AES in CTR mode, with the counter composed by
    # the concatenation of the 12 byte (96 bits) nonce and a 4 byte (32 bits)
    # integer, starting from 2
    cipher = AES.new(mode=AES.MODE_CTR, key=key, nonce=nonce, initial_value=2)
    ciphertext = cipher.encrypt(message)

    # Compute the GHASH of the ciphertext plus the ciphertext length in bits
    s = ghash(h, pad_block(ciphertext) + (len(ciphertext) * 8).to_bytes(16, 'big'))
    # Encrypt the GHASH value using AES in CTR mode, with the counter composed
    # by the concatenation of the 12 byte (96 bits) nonce and a 4 byte (32
    # bits) integer set at 1. The GHASH value fits in one block, so the counter
    # won't be increased during this round of encryption
    cipher = AES.new(mode=AES.MODE_CTR, key=key, nonce=nonce, initial_value=1)
    tag = cipher.encrypt(s)

    return (ciphertext, tag)

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes):
    assert len(key) in (16, 24, 32)
    assert len(nonce) == 12
    assert len(tag) == 16

    # Compute the GHASH subkey, the GHASH value, and the authentication tag, in
    # the same exact way as it was done during encryption
    cipher = AES.new(mode=AES.MODE_ECB, key=key)
    h = cipher.encrypt(b'\0' * 16)

    s = ghash(h, pad_block(ciphertext) + (len(ciphertext) * 8).to_bytes(16, 'big'))
    cipher = AES.new(mode=AES.MODE_CTR, key=key, nonce=nonce, initial_value=1)
    expected_tag = cipher.encrypt(s)

    # Compare the input tag with the generated tag. If they're different, the
    # plaintext must not be returned to the caller
    if tag != expected_tag:
        raise ValueError('authentication failed')

    # The two tags match; decrypt the plaintext and return it to the caller.
    # Note that, because AES-CTR is a symmetric cipher, there is no difference
    # between the encrypt and decrypt method: here we are reusing the same
    # exact code used during decryption
    cipher = AES.new(mode=AES.MODE_CTR, key=key, nonce=nonce, initial_value=2)
    message = cipher.encrypt(ciphertext)

    return message
```

And here is how the code can be used:

```python
key = bytes.fromhex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')
nonce = bytes.fromhex('0123456789abcdef01234567')
message = b'I went to the zoo yesterday but not today'

ciphertext, tag = aes_gcm_encrypt(key, nonce, message)
print(f'ciphertext: {ciphertext.hex()}')
print(f'       tag: {tag.hex()}')
decrypted_message = aes_gcm_decrypt(key, nonce, ciphertext, tag)
print(f' plaintext: {decrypted_message}')
assert message == decrypted_message
```

This snippet produces the following output:

```
ciphertext: e0c32db2962f9b729c69028d9a1fdfb2c93839fc1188f314c58ee97fd6a242404953bb208df609a33c
       tag: 9fa6fe2f77a0c98282868924ace0e4ec
 plaintext: b'I went to the zoo yesterday but not today'
```

This is the same output we would obtain by using the AES-GCM implementation
from pycryptodome directly:

```python
from Crypto.Cipher import AES

cipher = AES.new(mode=AES.MODE_GCM, key=key, nonce=nonce)
ciphertext, tag = cipher.encrypt_and_digest(message)
print(f'ciphertext: {ciphertext.hex()}')
print(f'       tag: {tag.hex()}')
```

Nonce reuse is catastrophic for AES-GCM in two ways:

* Because the ciphertext produced by AES-GCM is just a variant of AES-CTR,
  nonce reuse with GCM can have the same consequences as nonce reuse with
  AES-CTR, or any other stream cipher: if someone is able to guess the
  plaintext, they can recover the random stream, and use that to decrypt other
  messages (or portions of them).

* If the same nonce is used twice or more, the GHASH subkey $H$ will always be
  the same. Even if the output of GHASH is encrypted in step 7, we can use the
  XOR of two authentication tags to "cancel" the encryption and obtain a
  polynomial in $H$. From there, we can use algebraic methods to recover $H$.
  This gives us the ability to forge new, valid authentication tags.

It's worth mentioning that there's a variant of AES-GCM, called AES-GCM-SIV,
(Synthetic Initialization Vector) specified in [RFC
8452](https://www.rfc-editor.org/rfc/rfc8452). This differs from AES-GCM in
that it uses a little-endian version of GHASH called POLYVAL (which is faster
on modern CPUs), and in that it allows nonce reuse without the two catastrophic
consequences that I mentioned above.

(Nonce reuse with AES-GCM-SIV however still presents a problem, just not as
serious as the two ones above: specifically, it breaks [ciphertext
indistinguishability](https://en.wikipedia.org/wiki/Ciphertext_indistinguishability).)

# Authenticated Encryption with Associated Data (AEAD) {#authenticated-encryption-with-associated-data-aead}

The way I have described authenticated encryption, and in particular the
constructions ChaCha20-Poly1305 and AES-GCM, is accurate, but incomplete. What
I have told you is that when you use an authenticated encryption cipher, the
ciphertext is checked for integrity and authenticity. But we can use the same
technique to authenticate *anything*, not just ciphertexts: we can, for example,
authenticate some plaintext data, or authenticate a piece of plaintext data and
a piece of ciphertext altogether.

When we use a method to authenticate a plaintext message only, what we get is a
Message Authentication Code (MAC). We don't use the word "encryption" in this
context, because the confidentiality of the message is not ensured (only its
authenticity).

When we use a method to authenticate both a ciphertext and a plaintext message,
what we get is **Authenticated Encryption with Associated Data (AEAD)**. In
this construction, there are two messages involved: one to be encrypted
(resulting in a ciphertext), and one to be kept in plaintext. The plaintext
message is called "associated data" (AD) or "additional authenticated data"
(AAD). Both the ciphertext and the associated data are authenticated at
encryption time, so their integrity and authenticity will be enforced.

The **inputs to the encryption function** of an AEAD cipher are, generally
speaking:

* a key;
* a nonce;
* the additional data;
* the message to encrypt.

The **outputs of the encryption** are:

* the ciphertext;
* the authentication tag.

Note that there's only one authentication tag that covers both the additional
data and the ciphertext.

The **inputs to the decryption** function are:

* the key used for encryption;
* the nonce used for encryption;
* the additional data used for encryption;
* the ciphertext.

And the **output of the decryption** is either an error or the decrypted
message.

It's important to note that the associated data must be both at encryption time
and decryption time. Changing a single bit of it will make the entire
decryption operation fail.

Both ChaCha20-Poly1305 and AES-GCM (and their variants, XChaCha20-Poly1305 and
AES-GCM-SIV) are AEAD ciphers. Here's how they implement AEAD:

* When the Poly1305 or GHASH authenticator is first initialized, they are fed
  the additional data, padded with zeros to make its size a multiple of 16
  bytes (128 bits).
* Then the padded ciphertext is fed into the authenticator.
* The length of the additional data and the length of the ciphertext are
  represented as two 64-bit integers, concatenated, and fed into the
  authenticator.

<figure>
  <img src="{static}/images/chacha20-poly1305-aead-encryption.svg" alt="Diagram of data flow during encryption with ChaCha20-Poly1305, including the Associated Data (AE)">
  <figcaption>Updated data flow during a ChaCha20-Poly1305 encryption which shows where the Associated Data (AE) is placed.</figcaption>
</figure>

<figure>
  <img src="{static}/images/aes-gcm-aead-encryption.svg" alt="Diagram of data flow during encryption with AES-GCM, including the Associated Data (AE)">
  <figcaption>Updated data flow during an AES-GCM encryption which shows where the Associated Data (AE) is placed.</figcaption>
</figure>

If the additional data is empty, then what you get are exactly the
constructions that I described earlier in this article.

Authenticated Encryption with Associated Data is useful in situations where you
want to encode some metadata along with your encrypted data. For example: an
identifier for the resource that is encrypted, or the type of data encrypted
(text, image, video, ...), or some information that indicates what key and
algorithm was used to encrypt the resource, or maybe the expiration of the
data. The associated data is in plaintext so systems that do not have access to
the secret key can gather some properties about the encrypted resource. It must
however be understood that the associated data cannot be trusted until it's
verified using the secret key. Systems that analyze the associated data must be
designed in such a way that, if the associated data is tampered, nothing bad
will happen, and such tampering attempt will be detected sooner or later.

# A word of caution

Something very important to understand is that when using authenticated
encryption ciphers like ChaCha20-Poly1305 or AES-GCM, **decryption can in
theory succeed even if the verification of the authentication tag fails**.

For example, we can decrypt a ciphertext encrypted with ChaCha20-Poly1305 by
using ChaCha20 and ignoring the authentication tag. Similarly, we can decrypt a
ciphertext encrypted with AES-GCM by using AES-CTR and, again, ignoring the
authentication tag. This possibility opens the doors to all the nasty scenarios
that we have seen at the beginning of this article, removing all the benefits
of authenticated encryption.

Perhaps the most important thing to remember when using authenticated
encryption is: **never use decrypted data until you have verified its
authenticity**.

Why am I emphasizing this? Because some AE or AEAD implementations do return
plaintext bytes *before* verifying their authenticity.

The code samples that I have provided do the following: they first calculate
the authentication tag, compare it to the input tag, and only if the comparison
succeeds they perform the decryption. This is a simple approach, but it may be
expensive when encrypting large amounts of data (for example: several
gigabytes). The reason why this approach is expensive is that, if the
ciphertext is too large, it may not fit all in memory, and the ciphertext would
have to be read from the storage device twice: once for calculating the tag,
and once for decrypting the ciphertext.  Also, chances are that by the time the
application has computed the tag, the underlying ciphertext may have changed
without detection.

What some authenticated encryption implementations do when dealing with large
amounts of data is that they calculate the tag *and* perform the decryption in
parallel. They read the ciphertext chunk-by-chunk, and pass each chunk to both
the authenticator and the decryption function, returning a chunk of decrypted
bytes to the caller at each iteration. Only at the end, when the full
ciphertext has been read, the authenticity is checked, and the application may
return an error only at that point. With such implementations, it is imperative
that the exit status of the application is checked before using any of the
decrypted bytes.

An implementation that works like that (returning decrypted bytes before
authentication is complete) is GPG. Here is an example of the output that GPG
produces when decrypting a tampered message:

```
gpg: AES256.CFB encrypted data
gpg: encrypted with 1 passphrase
This is a very long message.
gpg: WARNING: encrypted message has been manipulated!
```

The decrypted message ("This is a very long message") got printed, together
with a warning, and the exit status is 2, indicating that an error occurred. It
is important in this case that the decrypted message is not used in any way.

Other implementations avoid this problem by simply not encrypting large amounts
of data. If given a large file to encrypt, the file is first split into
multiple chunks of a few KiB, then each chunk is encrypted independently, with
its own nonce and authentication tag. Because each chunk is small,
authentication and decryption can happen in memory, one before the other. If a
chunk was tampered, decryption would stop, returning truncated output, but
never tampered output. It's still important to check the exit status of such an
implementation, but the consequences are less catastrophic than before. The
drawback of this approach is that the total size of the ciphertext increases,
because each chunk requires a nonce, an authentication tag, and some
information about the position of the chunk (to prevent the chunks from being
reordered). Storing the nonces or the positions can be avoided by using an
algorithm to generate them on the fly, but storing the tag cannot be avoided.

The method of splitting that I have just described (of splitting long messages
into chunks that are individually encrypted and authenticated) is used for
example in [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security), as
well as the command line tool [AGE](https://github.com/FiloSottile/age).

# Summary and final considerations

At the beginning of this article we have seen some risks of using bare
encryption ciphers: one of them in particular was malleability, that is: the
property that ciphertexts may be modified without detection.

This problem was addressed by using Authenticated Encryption (AE) or
Authenticated Encryption with Associated Data (AEAD), which are methods to
provide integrity and authenticity in addition to confidentiality when
encrypting data.

We have seen the details of the two most popular authenticated encryption
ciphers and briefly mentioned some of their variants. Their features are
summarized here:

| Cipher             | Cipher Type  | Key Size           | Nonce Size | Nonce Reuse  | Tag Size |
| ------------------ | ------------ | ------------------ | ---------- | ------------ | -------- |
| ChaCha20-Poly1305  | Stream, AEAD | 256 bits           | 96 bits    | Catastrophic | 128 bits |
| XChaCha20-Poly1305 | Stream, AEAD | 256 bits           | 192 bits   | Catastrophic | 128 bits |
| AES-GCM            | Stream, AEAD | 128, 192, 256 bits | 96 bits    | Catastrophic | 128 bits |
| AES-GCM-SIV        | Stream, AEAD | 128 or 256 bits    | 96 bits    | Reduced risk | 128 bits |

Authenticated encryption is used in most of our modern protocols, including
TLS, S/MIME, PGP/GPG, and many more. Failure to implement authenticated
encryption correctly has lead to some serious issues in the past.

Whenever you're using encryption, ask yourself: how is integrity and
authentication verified? And remember: it's essential to verify the
authenticity of data *before* using it.

I hope you enjoyed this article! As usual, if you have any suggestions or
spotted some mistakes, let me know in the comments or by contacting me!
