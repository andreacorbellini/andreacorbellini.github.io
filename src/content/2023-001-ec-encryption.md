Title: Can we encrypt data using Elliptic Curves?
Date: 2023-01-02 06:30
Author: andreacorbellini
Category: cryptography
Tags: ecc, encryption, elgamal
Slug: ec-encryption
Status: published

From time to time, I hear people saying that Elliptic Curve Cryptography (ECC)
cannot be used to directly encrypt data, and you can only do key agreement and
digital signatures with it. This is a common misconception, but it's not
actually true: you can indeed use elliptic curve keys to encrypt arbitrary
data. And I'm not talking about hybrid-encryption schemes (like
[ECIES](https://en.wikipedia.org/wiki/Integrated_Encryption_Scheme) or
[HPKE](https://datatracker.ietf.org/doc/rfc9180/)): I'm talking about pure
elliptic curve encryption, and I'm going to show an example of it in this
article.  It's true however that pure elliptic curve encryption is not widely
used or standardized because, as I will explain at the end of the article, key
agreement is more convenient for most applications.

# Quick recap on Elliptic Curve Cryptography

I wrote an [in-depth article about elliptic curve
cryptography]({filename}/2015-005-ecc-part-1.md) in the past on this blog, and
here is a quick recap: points on an elliptic curve from an interesting
algebraic structure: a _cyclic group_. This group lets us do some algebra with
the points of the elliptic curve: if we have two points $A$ and $B$, we can
**add** them ($A + B$) or **subtract** them ($A - B$). We can also **multiply**
a point by an integer, which is the same as doing repeated addition ($n A$ = $A
+ A + \cdots + A$, $n$ times).

We know some efficient algorithms for doing multiplication, but the reverse of
multiplication is believed to be a "hard" problem for certain elliptic curves,
in the sense that we know efficient methods for computing $B = n A$ given $n$
and $A$, but we do not know very efficient methods to figure out $n$ given $A$
and $B$.  This problem of reversing a multiplication is known as Elliptic
Curve Discrete Logarithm Problem (ECDLP).

Elliptic Curve Cryptography is based on multiplication of elliptic curve points
by integers and its security is given mainly by the difficulty of solving the
ECDLP.

In order to use Elliptic Curve Cryptography, we first have to generate a
**private-public key pair**:

- the **private key** is a random integer $s$;
- the **public key** is the result of multiplying the integer $s$ with the
  generator $G$ of the elliptic curve group: $P = s G$.

Let's now see a method to use Elliptic Curve Cryptography to encrypt arbitrary
data, so that we can demystify the common belief that elliptic curves cannot be
used to encrypt.

# Elliptic Curve ElGamal

One method to encrypt data with elliptic curve keys is
**[ElGamal](https://en.wikipedia.org/wiki/ElGamal_encryption)**. This is not
the only method, of course, but it's the one that I chose because it's well
known and simple enough. ElGamal is a cryptosystem that takes the name from
[its author](https://en.wikipedia.org/wiki/Taher_Elgamal) and works on any
cyclic group, not just elliptic curve groups.

If we want to **encrypt** a message using the public key $P$ via ElGamal, we
can do the following:

1. map the message to a point $M$ on the elliptic curve
1. generate a random integer $t$
1. compute $C_1 = t G$
1. compute $C_2 = t P + M$
1. return the tuple $(C_1, C_2)$

To **decrypt** an encrypted tuple $(C_1, C_2)$ using the private key $s$, we
can do the following:

1. compute $M = C_2 - s C_1$
1. map the point $M$ back to a message

The scheme works because:
$$\begin{align\*}
    s C_1 & = s (t G) \\\\
          & = t (s G) \\\\
          & = t P
\end{align\*}$$
therefore:
$$\begin{align\*}
    C_2 - s C_1 & = (t P + M) - (t P) \\\\
                & = M
\end{align\*}$$

There's however a big problem with this scheme: how do we map a message to a
point, and vice versa? How can we perform step 1 of the encryption algorithm,
or step 2 of the decryption algorithm?

# Mapping a message to a point

A message can be an arbitrary byte string. An elliptic curve point is,
generally speaking, a pair of integers $(x, y)$ belonging to the elliptic curve
field.  How can we transform a byte string into a pair of field integers?

Well, as far as computers are concerned, both byte strings and integers have
the same nature: they are just sequences of bits, so there's a natural map
between the two. We could take the message, split it into two parts, and
interpret the first part as an integer $x$ and the second part as an integer
$y$. This would work for obtaining two arbitrary integers, but there's a
problem: the coordinates $x$ and $y$ of an elliptic curve point are related by
a mathematical equation (the curve equation), so we cannot choose two arbitrary
$x$ and $y$ and expect them to identify a valid point on the curve. In fact,
for curves in Weierstrass form, given $x$ there are at most two possible
choices for $y$, so it's _very_ unlikely that this splitting method will yield
a valid point.

Let's change our strategy a little bit: instead of transforming the message to
a pair $(x, y)$, we transform it to $x$ and then we compute a valid $y$ from
the curve equation. This is a much better method, but there's still a problem:
generally speaking, not every $x$ will have a corresponding $y$. Not every $x$
can satisfy the curve equation.

Luckily, most of the popular elliptic curves used in cryptography have an
interesting property: about half of the possible field integers are valid
$x$-coordinates. To see this, let's take a look at an example: the curve
`secp384r1`. This is a Weierstrass curve that has the following order:
```
0xffffffffffffffffffffffffffffffffffffffffffffffffc7634d81f4372ddf581a0db248b0a77aecec196accc52973
```
I remind you that the order is the number of valid points that belong to the
elliptic curve group. Because this is a Weierstrass curve, for each $x$ there
are 2 possible points, so the number of valid $x$-coordinates is `order / 2`.
Given an arbitrary 384-bit integer, what are the chances that this is a valid
$x$-coordinate? The answer is `(order / 2) / (2 ** 384)` which is approximately
0.5 or 50%.

OK, but how does this help with our goal: mapping an arbitrary message to a
valid $x$-coordinate? It's simple: we can _append_ a random byte (or multiple
bytes) to the message. We call this extra byte (or bytes): **padding**. If the
resulting padded message does not translate to a valid $x$-coordinate, we
choose another random padding and try again, until we find one that works.
Given that there's 50% chance of finding a valid $x$ coordinate, this method
will find a valid $x$-coordinate very quickly: on average, this will happen on
the first or the second try.

<figure>
  <img src="{static}/images/ec-elgamal-padding.svg" alt="Padding a message to obtain a valid elliptic curve point" width="500" height="120">
  <figcaption>Example of how to use padding to obtain a valid elliptic curve point from an arbitrary message.</figcaption>
</figure>

This operation can be easily **reversed**: if you have a point $(x, y)$, in
order to recover the message that generated it, just take the $x$ coordinate
and remove the padding. That's it!

It's worth noting that there are some standard curves where all the possible
byte strings (of the proper size) can be translated to elliptic curve points,
without any random padding needed. For example, with
[Curve25519](https://en.wikipedia.org/wiki/Curve25519), every 32-byte string is
a valid elliptic curve point. Another curve like that is
[Curve448](https://en.wikipedia.org/wiki/Curve448).

It's also important to note that the padding does not need to be truly random.
In the image above I show a padding that is simply a constantly increasing
sequence of numbers: 1, 2, 3, ... That's enough to find a valid point.

# Putting everything together

We have seen how to map a message to a point and how ElGamal works, so now we
have all the elements to write some working code. I'm choosing
[Python](https://www.python.org/) and the
[ECPy](https://github.com/cslashm/ECPy) package to work with elliptic curves,
which you can install with `pip install ecpy`.

```python
import random
from ecpy.curves import Curve, Point


def message_to_point(curve: Curve, message: bytes) -> Point:
    # Number of bytes to represent a coordinate of a point
    coordinate_size = curve.size // 8
    # Minimum number of bytes for the padding. We need at least 1 byte so that
    # we can try different values and find a valid point. We also add an extra
    # byte as a delimiter between the message and the padding (see below)
    min_padding_size = 2
    # Maximum number of bytes that we can encode
    max_message_size = coordinate_size - min_padding_size

    if len(message) > max_message_size:
        raise ValueError('Message too long')

    # Add a padding long enough to ensure that the resulting padded message has
    # the same size as a point coordinate. Initially the padding is all 0
    padding_size = coordinate_size - len(message)
    padded_message = bytearray(message) + b'\0' * padding_size

    # Put a delimiter between the message and the padding, so that we can
    # properly remove the padding at decrypt time
    padded_message[len(message)] = 0xff

    while True:
        # Convert the padded message to an integer, which may or may not be a
        # valid x-coordinate
        x = int.from_bytes(padded_message, 'little')
        # Calculate the corresponding y-coordinate (if it exists)
        y = curve.y_recover(x)
        if y is None:
            # x was not a valid coordinate; increment the padding and try again
            padded_message[-1] += 1
        else:
            # x was a valid coordinate; return the point (x, y)
            return Point(x, y, curve)


def encrypt(public_key: Point, message: bytes) -> bytes:
    curve = public_key.curve
    # Map the message to an elliptic curve point
    message_point = message_to_point(curve, message)
    # Generate a randon number
    seed = random.randrange(0, curve.field)
    # Calculate c1 and c2 according to the ElGamal algorithm
    c1 = seed * curve.generator
    c2 = seed * public_key + message_point
    # Encode c1 and c2 and return them
    return bytes(curve.encode_point(c1) + curve.encode_point(c2))


def point_to_message(point: Point) -> bytes:
    # Number of bytes to represent a coordinate of a point
    coordinate_size = curve.size // 8
    # Convert the x-coordinate of the point to a byte string
    padded_message = point.x.to_bytes(coordinate_size, 'little')
    # Find the padding delimiter
    message_size = padded_message.rfind(0xff)
    # Remove the padding and return the resulting message
    message = padded_message[:message_size]
    return message


def decrypt(curve: Curve, secret_key: int, ciphertext: bytes) -> bytes:
    # Decode c1 and c2 and convert them to elliptic curve points
    c1_bytes = ciphertext[:len(ciphertext) // 2]
    c2_bytes = ciphertext[len(ciphertext) // 2:]
    c1 = curve.decode_point(c1_bytes)
    c2 = curve.decode_point(c2_bytes)

    # Calculate the message point according to the ElGamal algorithm
    message_point = c2 - secret_key * c1
    # Convert the message point to a message and return it
    return point_to_message(message_point)
```

And here is an usage example:

```python
curve = Curve.get_curve('secp384r1')

secret_key = 0x123456789abcdef
public_key = secret_key * curve.generator

message = 'hello'
print('  Message:', message)

encrypted = encrypt(public_key, message.encode('utf-8'))
print('Encrypted:', encrypted.hex())

decrypted = decrypt(curve, secret_key, encrypted).decode('utf-8')
print('Decrypted:', decrypted)
```

Which produces the following output:

```
  Message: hello
Encrypted: 04fa333c6a03994c5bce4627de4447c5cdd358415f8db2745b67836932a0d5e81f19...
Decrypted: hello
```

# Some considerations on padding and security

It's important to note that padding is a very delicate problem in cryptography.
There exist many [padding
schemes](https://en.wikipedia.org/wiki/Padding_(cryptography)), and **not all
of them are secure**. The padding scheme that I wrote in this article was just
for demonstration purposes and may not be the most secure, so don't use it in
production systems. Take a look at
[OAEP](https://en.wikipedia.org/wiki/Optimal_asymmetric_encryption_padding) if
you're looking for a modern and secure padding scheme.

Another thing to note is that the decryption method that I wrote does not check
if the decryption was successful. If you try to decrypt an invalid ciphertext,
or use the wrong key, you won't get an error but instead a random result, which
is not desiderable. A good padding scheme like OAEP will instead throw an error
if decryption was unsuccessful.

(Receiving an error when decryption is not successful is very important due to
the fact that schemes like ElGamal are
[malleable](https://en.wikipedia.org/wiki/Malleability_(cryptography)). Check
out my post about [authenticated
encryption]({filename}/2023-003-authenticated-encryption.md) for examples and
details about why this is important.)

# Cost of elliptic curve encryption

With Elliptic Curve ElGamal, if we are using an _n_-bit elliptic curve, we can
encrypt messages that are at most _n_-bit long (actually less than that,
if we're using padding), and the output is at least _2n_-bit long (if the
resulting points $C_1$ and $C_2$ are encoded using point compression). This
means that encryption using Elliptic Curve ElGamal doubles the size of the data
that we want to encrypt. It also requires a fair amount of compute resources,
because it involves a random number generation and 2 point multiplications.

In short, Elliptic Curve ElGamal is expensive both in terms of space and in
terms of time and compute power, and this makes it unattractive in applications
like [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security) or general
purpose encryption.

So what can we use Elliptic Curve ElGamal for? We can use it to encrypt
_symmetric keys_, such as
[AES](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) keys or
[ChaCha20](https://en.wikipedia.org/wiki/ChaCha20) keys, and then use these
symmetric keys to encrypt our arbitrary data. Symmetric keys are relatively
short (ranging from 128 to 256 bits nowadays), so they can be encrypted with
one round of Elliptic Curve ElGamal with most curves. It's worth noting that
this is the same approach that we use with
[RSA](https://en.wikipedia.org/wiki/RSA_(cryptosystem)) encryption: for most
applications, we don't use RSA to encrypt data directly, but rather we use RSA
to encrypt symmetric keys which are later used for encrypting data.

These are the reason why schemes like Elliptic Curve ElGamal, or other methods of
encryption with elliptic curves, are not used in practice:

- elliptic curve encryption is more expensive than hybrid encryption;
- hybrid encryption scales better and is more performant;
- elliptic curve key exchange is simpler and has fewer pitfalls than
  encryption.

In conclusion, there are no practical benefits from elliptic curve encryption
compared to hybrid encryption with key agreement, and that's why we don't use
it. However, the idea that elliptic curves cannot be used for encryption is a
myth, and I hope this article will help clarify that confusion.
