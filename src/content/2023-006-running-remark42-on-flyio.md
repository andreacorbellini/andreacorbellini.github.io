Title: How to run Remark42 on Fly.io
Date: 2023-09-19 02:12:00
Author: andreacorbellini
Category: blog
Slug: running-remark42-on-flyio
Image: images/remark42-setup.svg
Status: published

As I wrote on my [previous post]({filename}/2023-005-disqus-to-remark42.md), I
recently switched from [Disqus](https://disqus.com/) to
[Remark42](https://remark42.com/) for the comments on my blog. Here I will
explain how I set it up on [Fly.io](https://fly.io/).

# Overview

The setup that I ended up with looks like the following:

<figure>
  <img src="{static}/images/remark42-setup.svg" alt="Diagram of the components for the Remark42 setup">
</figure>

Something to note about this setup is that the "machine" (more on that later)
and the storage volume are both a single instance. This is not a distributed
setup. This is because Remark42 stores comments in a single file and does not
make use of a distributed database. This is listed as a "feature" on the
[Remark42 website](https://remark42.com/). How one is supposed to implement
replication? I have no idea. Thankfully Fly.io seems to be fast to provision
machines, and the Remark42 daemon also seems fast to start, so hopefully if a
problem occurs (or when updates are required), the downtime will be minimal.

It is imperative however to understand that, because of the
non-distributed/non-replicated nature of this setup, backups should be made
periodically to avoid the risk of losing your comments forever.

# Preliminaries

Before setting up Remark42, I had never used [Fly.io](https://fly.io/) before.
As Fly.io newbie, I would describe it as a cloud provider focused on Docker
containers. Fly.io uses some concepts (like "apps" and "machines") that make
sense after you practice a bit with them, but as a beginner they are not the
easiest to learn.  Most of the complexity I think comes from the fact that the
Fly.io documentation is poorly written. On top of that, it appears that Fly.io
is migrating their offering from "V1 apps" to "V2 apps", and today some
documentation applies only to "V1 apps", other pieces apply only to "V2 apps",
resulting in a big mess. The error messages you get are also far from clear.

But don't get too scared: once you get to know Fly.io, it can actually be fun
to use.

Creating resources on Fly.io requires installing their command line client:
`flyctl`. Because I do not like to run unknown software unconfined, I [packaged
it as a snap](https://snapcraft.io/andrea-flyctl) that you can install using:

```sh
snap install andrea-flyctl
```

Another source of confusion that I had the beginning was that, by reading the
documentation, it looked like a second command line tool named `fly` was needed
in addition to `flyctl`. It turns out that `fly` and `flyctl` are the same
thing, it's just that they're transitioning from a name to another. If you
installed the tool through the snap, you can set up these aliases so that you
can copy and paste commands without trouble:

```sh
alias fly=/snap/bin/andrea-flyctl.fly
alias flyctl=/snap/bin/andrea-flyctl.fly
```

According to the documentation (and assuming it's up-to-date), `flyctl` does
not support everything that Fly.io supports, so sometimes `curl` is used to
interact directly with the Fly.io API. In order to use that, you'll need to
download an authentication token from the Fly.io interface and store it in a
file (that I'll call `~/fly-token` from now on).

I'm going to skip over the steps to create and configure a Fly.io account,
obtaining an authentication token, as those were easy steps in my opinion.

# Creating a machine

A Fly.io "machine" is a virtual machine running a single Docker container with
a persistent volume attached to it. In order to create my Fly.io machine to run
Remark42 in it,  I loosely followed this page from the Fly.io documentation:
[Run User Code on Fly Machines
](https://fly.io/docs/machines/guides-examples/functions-with-machines/).
"Loosely" because it turned out that some pieces on that page are not fully
correct, but anyway...

Before creating a machine, you first need to create an "app". A Fly.io app is
basically an endpoint, which consists of a DNS name (in the form
`${app_name}.fly.dev`), and a set of IP addresses. Behind these IP addresses
there are Fly.io load balancers that will forward requests to the machines
inside the app.

You can do that through the API like this:

```sh
curl -X POST \
  -H "Authorization: Bearer $(<~/fly-token)" \
  -H 'Content-Type: application/json' \
  'https://api.machines.dev/v1/apps' \
  -d '{ "app_name": "${app_name}", "org_slug": "personal" }'
```

(Replace `${app_name}` with some identifier of your choice; I chose `remark42`
without knowing that this would have removed the possibility for other people
to register an app with the same name.)

IP addresses need to be manually allocated:

```sh
fly ips allocate-v4 --app=${app_name} --shared
fly ips allocate-v6 --app=${app_name}
```

The `--shared` option to `allocate-v4` tells Fly.io to allocate an IP address
that may be shared with other Fly.io apps, even outside of your
account/organization. Remove `--shared` if you want to use a dedicated IP, but
note that dedicated IPv4 addresses is a paid feature.

Allocating IPs is an important step: it can be done later, after creating the
machine, but it must be done, otherwise your machine will be unreachable and it
won't be obvious why.

You should now create a persistent volume for your machine:

```sh
fly volume create remark42_db_0 --app=${app_name} --size=1
```

This will display a warning about replication, but you can ignore it because,
sadly, Remark42 does not support replication.

Remark42 needs to be given a secret key (I guess for the purpose of signing
[JWT tokens](https://en.wikipedia.org/wiki/JSON_Web_Token)). Fly.io has a handy
feature to manage secrets, and make them available to machines, albeit poorly
documented. You can set the Remark42 secret like this:

```sh
fly secrets set --app=${app_name} SECRET='a very secret string'
```

(You can generate a random secret string with a command like `cat /dev/urandom
| tr -Cd 'a-zA-Z0-9' | head -c64`, which means: get some random bytes, keep
only alphanumeric characters, get the first 64 characters.)

You may be wondering: how is the container running inside the machine supposed
to access this secret? The Fly.io documentation doesn't say a word about it,
but after experimenting I was able to find that all the app secrets are passed
as environment variables, which is great, because this is exactly what Remark42
expects.

**Note: it's important to set `SECRET` before creating the machine, or Remark42
will refuse to start.**

Now you're ready to spin up the machine: create a configuration file for it...

```json
{
  "name": "remark42-0",
  "config": {
    "image": "umputun/remark42:latest",
    "env": {
      "SITE": "andrea.corbellini.name",
      "REMARK_URL": "https://${app_name}.fly.dev",
      "ALLOWED_HOSTS": "'self',https://andrea.corbellini.name",
      "AUTH_SAME_SITE": "none",
      "AUTH_ANON": "true",
      "AUTH_EMAIL_ENABLE": "true",
      "AUTH_EMAIL_FROM": "Andrea's Blog <hi@andrea.corbellini.name>",
      "AUTH_EMAIL_SUBJ": "Andrea's Blog - Email Confirmation",
      "NOTIFY_USERS": "email",
      "NOTIFY_ADMINS": "email",
      "NOTIFY_EMAIL_FROM": "Andrea's Blog <hi@andrea.corbellini.name>",
      "ADMIN_SHARED_EMAIL": "corbellini.andrea@gmail.com",
    },
    "mounts": [
      {
        "volume": "${volume_id}",
        "path": "/srv/var"
      }
    ],
    "services": [
      {
        "ports": [
          {
            "port": 443,
            "handlers": [
              "tls",
              "http"
            ]
          },
          {
            "port": 80,
            "handlers": [
              "http"
            ]
          }
        ],
        "protocol": "tcp",
        "internal_port": 8080
      }
    ],
    "checks": {
      "httpget": {
        "type": "http",
        "port": 8080,
        "method": "GET",
        "path": "/ping"
        "interval": "15s",
        "timeout": "10s",
      }
    },
    "metadata": {
      "fly_platform_version": "v2",
    }
  }
}
```

...and give it to Fly.io:

```sh
curl -X POST \
  -H "Authorization: Bearer $(<~/fly-token)" \
  -H 'Content-Type: application/json' \
  "https://api.machines.dev/v1/apps/${app_name}/machines"
  -d @config.json
```

There's a lot here, so let me break it down for you:

* `"image": "umputun/remark42:latest"`: this is the Docker image for Remark42.

* `"env": { ... }`: these are all the environment variables to pass to our
  container. They are briefly documented on the [Remark42
  website](https://remark42.com/docs/configuration/parameters/), and here's a
  bit more detailed explanation of some of them:

    * `"SITE": "andrea.corbellini.name"`: this is the internal identifier for the
      site, it can be an arbitrary string, it won't be visible, and you can omit
      it.

    * `"REMARK_URL": "https://${app_name}.fly.dev"`: this is the URL where
      Remark42 will be serving requests from. I set it to the Fly.io app
      endpoint. It's **important that you do not put a trailing slash**, or
      Remark42 will error out later on. It's also important that the protocol
      (http or https) matches your blog's protocol, or Remark42 will refuse to
      display comments (this makes local testing a bit annoying).

    * `"ALLOWED_HOSTS": "'self',https://andrea.corbellini.name"`: this is the
      list of sources that will be put into the [`Content-Security-Policy:
      frame-ancestors`
      header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors))
      of HTTP responses. Essentially, this defines where the Remark42 comments
      can be displayed.

    * `"AUTH_SAME_SITE": "none"`: this disable the ["same site" policy for
      cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#samesitesamesite-value).
      Disabling it is necessary because, in my setup, comments are served from
      one domain (`remark42.fly.dev`) to another domain
      (`andrea.corbellini.name`).

    * `"AUTH_ANON": "true"`: allows anonymous commenters. You may or may not
      want it.

    * `"AUTH_EMAIL_ENABLE": "true"` and friends: allows email-based
      authentication of commenters.

    * `"NOTIFY_USERS" "email"`: allows readers and commenters to be notified of
      new comments via email.

    * `"NOTIFY_ADMINS" "email"` and `"ADMIN_SHARED_EMAIL":
      "corbellini.andrea@gmail.com"`: makes Remark42 send me an email every
      time there's a new comment.

* `"mounts": [ ... ]`: this tells Fly.io to attach the volume that you created
  earlier to the container at the path `/srv/var`, which is what Remark42 uses
  to store its database as well as daily backups.

* `"services": [ ... ]`: this tells Fly.io what to expose through the load
  balancer. With the configuration that I provided, the Fly.io endpoint
  (`${app_name}.fly.dev`) will provide both HTTP and HTTPS to the internet.
  However, the load balancer will talk to the machine over plain HTTP on port
  8080 (meaning that TLS is terminated at the load balancer).

    I think in the future I will setup [certbot](https://certbot.eff.org/)
    inside the container so that I can do TLS termination on the machine, but
    not today.

* `"checks": { ... }`: this tells Fly.io to check if the Remark42 daemon is
  healthy by using its `/ping`endpoint.

* `"metadata": { "fly_platform_version": "v2" }`: this tells Fly.io to use a
  "V2 machine", or something like that. **Setting this metadata is very
  important, or certain things won't work later on.** The Fly.io documentation
  doesn't tell you to do it, but this is needed if you need to update the
  environment variables or the secrets inside the machine.

Note that all of this configuration can be changed at any time, so if you make
any mistakes or you just want to experiment, you don't have to overly worry.
You can even destroy your machine and recreate it from scratch if you want.

To view the configuration of an existing machine use the following:

```sh
curl \
  -H "Authorization: Bearer $(<~/fly-token)" \
  "https://api.machines.dev/v1/apps/${app_name}/machines/${machine_id}"
```

And to update it:

```sh
curl -X POST \
  -H "Authorization: Bearer $(<~/fly-token)" \
  -H 'Content-Type: application/json' \
  "https://api.machines.dev/v1/apps/${app_name}/machines/${machine_id}" \
  -d @new-config.json
```

I was also successful at changing configuration using `fly machines update`,
although it can't be used for everything (for example: it can be used to *add*
or *change* environment variables, but not to *remove* them).

# Testing the setup

If everything went well, you should be able to interact with Remark42 at
`https://${app_name}.fly.dev/web`. This should let you read and post new
comments.

# Configuring Remark42 to send emails

For sending emails, I chose to use <strike>Elastic Email</strike>
[Mailtrap](https://mailtrap.io/), which is an email-delivery service that
supports SMTP with STARTTLS. Creating a Mailtrap account, setting up
[DKIM](https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail) and
[SPF](https://en.wikipedia.org/wiki/Sender_Policy_Framework), and obtaining
SMTP credentials was extremely easy, so I won't cover it here.

> **UPDATE:** I initially chose to go with Elastic Email, but I found it to be
> garbage. They force the insertion of tracking URLs every one of your emails,
> and they refuse to disable tracking if you ask them to.

Setting up email delivery with Remark42 is pretty easy once you have the SMTP
credentials. Set the necessary (non-secret) configuration like this:

```sh
fly machines update ${machine_id} --app=${app_name} \
  -e SMTP_HOST=live.smtp.mailtrap.io \
  -e SMTP_PORT=587 \
  -e SMTP_STARTTLS=true \
  -e SMTP_USERNAME=...
```

And then set the SMTP password as a Fly.io secret:

```sh
fly secrets set --app=${app_name} SMTP_PASSWD='a very secret password'
```

Doing both `machines update` and `secrets set` will automatically restart the
machine so that Remark42 can pick up the new configuration. Pretty neat, heh?

# Configuring authentication providers for Remark42

Remark42 can let your users log in from a variety of providers, including:
GitHub, Google, Facebook, Telegram, and more. There are specific instructions
for each provider in the [Remark42
documentation](https://remark42.com/docs/configuration/authorization/). There's
really not much to add on top of what's already written there. Just remember:
set non-secret environment variables with `fly machines update`, and set
secrets with `fly secrets set`.

# Creating an administrator account

If you want to be able to moderate comments, you'll need an administrator
account. With Remark42, this is a 3 step process: first you create an account
(like any other user would do), then you copy the ID of the user you just
created, and lastly you add that user ID to the `ADMIN_SHARED_ID` environment
variable:

```sh
fly machines update ${machine_id} --app=${app_name} -e ADMIN_SHARED_ID=...
```

As step-by-step guide is on the [Remark42
documentation](https://remark42.com/docs/manuals/admin-interface/).

# Importing comments from Disqus (or any other platform)

In order to import comments into Remark42, first you need to temporarily set an
"admin password" for Remark42 (here the word "admin" has nothing to do with the
administrator account you just created; it's a totally separate concept):

```sh
fly secrets set --app=${app_name} ADMIN_PASSWD='this is super secret'
```

You can now copy your Disqus (or equivalent) backup on the machine and import
it. I could not find an easy way to do it through `flyctl` (but I also did not
spend too much time looking for an option), I did however find a way to open a
console on the machine, so what I did was simply copying and pasting the
base64-encoded backup:

```sh
# on my laptop
base64 < disqus-export.xml.gz  # copy the output

# attach to the machine
fly console --app=${app_name} --machine=${machine_id}

# on the machine
cd /srv/var
base64 -d > disqus-export.xml.gz  # paste the output from earlier
gunzip disqus-export.xml.gz
import --provider=disqus --file=/srv/var/disqus-export.xml --url=http://localhost:8080
rm disqus-export.xml
```

**Note: importing comments will clear the Remark42 database.** Any pre-existing
comment will be deleted. See also the [Remark42
documentation](https://remark42.com/docs/backup/migration/) for more
information.

Another note: for some reason, my Disqus export referenced my blog posts using
`http://` URLs instead of `https://`. Because of that, Remark42 did correctly
import all the Disqus comments in its database, but would not display them
under my blog posts. Remember: Remark42 is very picky when it comes to URL
schemes. To fix this, I simply [created a backup from
Remark42](https://remark42.com/docs/backup/backup/), modified the backup to
change all `http` entries to `https`, and then [restored the
backup](https://remark42.com/docs/backup/restore/). This was quite trivial
given that the format used by the backups is extremely intuitive.

# Final remarks

That was it!

Setting up Remark42 on Fly.io wasn't particularly difficult, but it took me way
more time than expected due to the poor documentation of both Remark42 and
Fly.io. I had to resort to trial-and-error multiple times to make things work.

One big drawback of Remark42 is that it does not allow replication. This means
that:

* if the machine running my instance of Remark42 goes down, or becomes
  unreachable for any reason, there will be downtime;
* some people who are "far away" from the Remark42 instance may experience
  higher latency than others;
* I need to periodically take backups of my Remark42 database and copy it
  somewhere, otherwise if my single storage volume is lost, I will lose all the
  comments.

Nonetheless I think both Remark42 and Fly.io are very interesting products. I
love Remark42's features, and Fly.io is easy enough to use once you get
familiar with it. I think I'm gonna stick with them for a long time.
