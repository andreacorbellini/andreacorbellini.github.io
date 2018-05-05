Title: Announcing Perfect Storm: bringing order to your cloud
Date: 2018-05-01 11:12
Author: andreacorbellini
Category: cloud-computing
Tags: cloud-computing, perfect-storm
Slug: perfect-storm
Status: draft

Today I want to announce the release of a personal project. Codenamed [Perfect Storm🗲](https://github.com/perfectstorm/perfectstorm), it's a tool to help you abstract your resources in the cloud (containers, virtual machines, networks, ...) and group them logically, like this:

<figure>
  <img src="{filename}/images/perfect-storm-2-tier-architecture.png" alt="Perfect Storm Visualization" width="500" height="293">
  <figcaption>A simple 2-tier architecture with a distributed frontend service and a replicated database.</figcaption>
</figure>

<figure>
  <img src="{filename}/images/perfect-storm-2-tier-architecture-zoom.png" alt="Perfect Storm Visualization (Zoom)" width="500" height="293">
  <figcaption>Below the abstraction layer: containers, virtual machines and everything that composes your application.</figcaption>
</figure>

Perfect Storm allows you to see your cloud services in the way you would describe them, and manage them easily. The concept was developed around a set of principles:

* **Resources are an implementation detail.** Do you like Docker containers? Do you prefer Rocket instead? Or maybe virtual machines scattered across Rackspace and AWS? No matter how you run your code, your application is still the same and must behave the same way. Containers and virtual machines are essential details, but it's what is running inside of them and how they interoperate that defines your application.
* **Ease of evolution.** Requirements change constantly, and your application and infrastructure do too. If today you want to start simple with a single-node PostgreSQL setup, chances are that tomorrow you will want to turn it into a distributed, replicated, master/slave setup. This is a big change in your platform and infrastructure, but overall the components that interact with your database should not change much, if at all.
* **Non-opinionated design.** You should be able to design your own workflow. We may provide built-in solutions, but those are optional and you should be able to come up with your own or use third-party ones if needed.


## Concepts

Perfect Storm orbits around three essential concepts: resources, groups and applications.

XXX Picture here?


### Resources

Those are your containers, your virtual machines and anything that is running on your cloud. When browsed through the command line client (stormctl), they look like this:

XXX Improve example showing multi-cluster

    :::console
    $ stormctl resource ls
    ID                               TYPE            NAMES                                                         STATUS    HEALTH
    res-4zvMHIP9a9qPW5TmBIEFzw       swarm-cluster   default, j7qt6ftt5nzsdfw0dtp7oquf7                            running   unknown
    ├─res-506x3OWzeGCLR920kQu1rI     swarm-node      swarm-agent-8, aft9keujn9i06c6jozou1sbi4                      running   unknown
    ├─res-509Z081DjwaLXgzt7t7XOW     swarm-node      swarm-agent-4, d2b5n2npk9i8yukyctozfxz4m                      running   unknown
    ├─res-50LLXbF4gtLoqh0a35fzxc     swarm-node      swarm-agent-3, dtr18tzk7nz0tiozict8sk94t                      running   unknown
    ├─res-50LLXcu79BVJA6YVeDbdGe     swarm-node      swarm-agent-2, fkoo9468a114dtn3mo1gwik2m                      running   unknown
    ├─res-50LLXeZ9bTenTW6RFLXGZg     swarm-node      swarm-manager, kwovvm8jf4n1qtydg9liqggpb                      running   healthy
    ├─res-50cMx7Ov8umFy1ib6FWHM4     swarm-node      swarm-agent-7, ms6ogd65glzvln7rexuj29muo                      running   unknown
    ├─res-4zvMHK4C2RztpV1hmQ9tIy     swarm-node      swarm-agent-5, n1yopuqrb7jd1az6xb8eu5rwr                      running   unknown
    ├─res-4zvMHLjEUk9O8uZdNY5Wc0     swarm-node      swarm-agent-6, nzbo034v8ggt3ggq4ch2z89ts                      running   unknown
    ├─res-50oqY8AMWvVMfJZkCez9Fk     swarm-node      swarm-agent-1, w1cyrvsglahp3njw94x9qeuh1                      running   unknown
    ╰─res-5KXdYazPSyVgznhiG03EQW     swarm-service   lucid_davinci, b4plskpusgoqxavtnb5ttvu42                      running   unknown
        ├─res-5KvMBQUvhzTV7KNe1UE8o0   swarm-task      lucid_davinci.nzbo034v8ggt3ggq4ch2z89ts, lucid_davinci.nzb…   running   healthy
        ├─res-5KdJVznUNPZYND7jWfY72q   swarm-task      lucid_davinci.ms6ogd65glzvln7rexuj29muo, lucid_davinci.ms6…   running   healthy
        ├─res-5KdJW1SWphj2gcff7nTkLs   swarm-task      lucid_davinci.n1yopuqrb7jd1az6xb8eu5rwr, lucid_davinci.n1y…   running   healthy
        ├─res-5KXdYceRvGfBJDFdr7yrjY   swarm-task      lucid_davinci.w1cyrvsglahp3njw94x9qeuh1, lucid_davinci.w1c…   running   healthy
        ├─res-5KXdYhdZI97eFRtQeVllee   swarm-task      lucid_davinci.fkoo9468a114dtn3mo1gwik2m, lucid_davinci.fko…   running   healthy
        ├─res-5KvMBOptFhK0nupiQMIVUy   swarm-task      lucid_davinci.d2b5n2npk9i8yukyctozfxz4m, lucid_davinci.d2b…   running   healthy
        ├─res-5KXdYeJUNYofccnZSFuV2a   swarm-task      lucid_davinci.dtr18tzk7nz0tiozict8sk94t, lucid_davinci.dtr…   running   healthy
        ├─res-5KXdYfyWpqy9w2LV3Nq8Lc   swarm-task      lucid_davinci.kwovvm8jf4n1qtydg9liqggpb, lucid_davinci.kwo…   running   healthy
        ╰─res-5KdJW37ZHzsX02DaivPNeu   swarm-task      lucid_davinci.aft9keujn9i06c6jozou1sbi4, lucid_davinci.aft…   running   healthy

Resources on Perfect Storm expose certain common attributes (names, status, health, node, ...). Those are unified across all clouds, so that if OpenStack and EC2 use different ways to express that a virtual machine is up and running, in Perfect Storm you can see them using the same terminology.

In addition to that, Perfect Storm keeps a 1:1 snapshot of all the metadata that is available on the cloud. For example, consider this Docker Swarm service:

    :::console
    $ stormctl resource get XXX
    XXX

The `snapshot` attribute contains all the information that the Docker Swarm API itself returned.


### Groups

As we have said, resources are an implementation detail. A key point that matters is how they are composed. Groups provide the functionality to, well, *group* related resources together. To define a group, often all you have to do is define a query that will match the resources you're interested in. For example, the following group shows all the resources that are running Redis:

    :::console
    $ stormctl group get redis
    name: redis
    query:
      image:
        $regex: 'redis:.*'

    $ stormctl group members redis
    XXX
    XXX
    XXX

That query will match all the resources with an `image` attribute matching the `redis:.*` regular expression (images are in the format `<name>:<version>`, the `.*` is there to match all versions of Redis).

Groups can be constructed from arbitrary queries and they can provide different views of the same resources. For example, if we were in the middle of an upgrade from Redis 3 to Redis 4, we might be interested in seeing the containers running the two distinct versions separately:

    :::console
    $ stormctl group get redis-3
    name: redis
    query:
      image:
        $regex: 'redis:3'

    $ stormctl group members redis-3
    XXX
    XXX
    XXX

    $ stormctl group get redis-4
    name: redis
    query:
      image:
        $regex: 'redis:4'

    $ stormctl group members redis-4
    XXX
    XXX
    XXX

Other than for viewing our regular resources, we can use groups to check for anomalies too. Suppose that we have a policy that no resources should use more than 1 GB of RAM. We could use this query to see all instances that are *not* meeting the policy:

    :::yaml
    name: excess-memory
    query:
      $or:
        - snapshot.Spec.Resources.Limits.MemoryBytes:
            $exits: false
        - snapshot.Spec.Resources.Limits.MemoryBytes:
            $gt: 1000000000

This query inspects the snapshot of our resources. It's made for Docker Swarm containers and matches all those containers either that don't have a memory limit set (`$exists: false`) or that have a limit which is too high (`$gt: 1000000000`).

Of course we can define more complex queries as well. The syntax used is the same for [MongoDB queries](https://docs.mongodb.com/manual/tutorial/query-documents/).

You can associate some metadata to groups too. At the moment, they support specifying a list of services they expose over the network:

    :::yaml
    name: consul
    query:
      image: { $regex: 'redis:.*' }
    services:
      - { name: rpc, port: 8300 }
      - { name: serf-lan, port: 8301 }
      - { name: serf-wan, port: 8302 }
      - { name: http, port: 8500 }
      - { name: dns, port: 8600 }

One nice thing to understand is that groups can be defined at any time. They are independent from how you started your resources and there are no constraints.


### Applications

Finally, applications define how our groups interact with each other

    :::yaml
    application:
      name: blog

      groups:
        - name: frontend
          query:
            image: { $regex: '^wordpress:' }
          services:
            - name: http
              port: 80

        - name: database
          query:
            image: { $regex: '^postgres:' }
          services:
            - name: postgres
              port: 5432

        - name: cache
          query:
            image: { $regex: '^redis:' }
          services:
            - name: redis
              port: 6379

      expose:
        - frontend[http]

      links:
        - frontend => database[postgres]
        - frontend => cache[redis]

Through `expose` we can list all groups (and their services) that are supposed to be reachable by end users. In the above example we are stating that the user will interact with `frontend` using the `http` protocol on port 80. The syntax is `<group-name>[<service-name>]`.

The `links` attribute specifies how components interact with each other. In the simple example above, `frontend` talks to both the database and the cache using their respective protocols.

This was an overview of the main concepts offered by Perfect Storm. Now how do we use them?


## Walkthrough

In order to explain Perfect Storm to people I usually show an example: we pick a simple 2-tier web application (frontend + database), we deploy it in a single-node setup and make it gradually evolve till reaching a fully distributed setup and see how Perfect Storm can help in this process.

For our walkthrough, our web frontend will be a [messaging service](https://hub.docker.com/r/andreacorbellini/messaging/) (nothing too fancy, just a custom-built web application to test that our setup is working correctly), our database backend will be MySQL and we will deploy our application on [Docker Swarm](XXX).


# Step 0: setup

XXX Move this section to the documentation and add a link to it

As I mentioned previously, we will be using Docker Swarm, so if you want to try yourself you can follow the [Swarm Mode tutorial](https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/) to set up a Swarm cluster. For this walkthrough, you will need at least 2 Docker machines, though I would say that if you want to fully enjoy the experience you should start 8 machines or more.

Once the Swarm is ready, we can run Perfect Storm on it. Technically, we could run Perfect Storm from anywhere, but for the purposes of this walkthrough it's simpler if we use the Swarm we just created. We need to start 3 services/containers:

1. **MongoDB.** It's used as storage backend for Perfect Storm:

        :::console
        $ docker service create --name mongodb --constraint node.role==manager -p 27017:27017 mongo

1. **stormd.** This is the Core API Server for Perfect Storm, which maintains the data model and provides you with relevant information:

        :::console
        $ docker service create --name stormd --constraint node.role==manager -p 28482:28482 perfectstorm/stormd --mongodb XXX:27017

1. **storm-swarm.** Perfect Storm is designed to support a range of different cloud orchestrator. The storm-swarm component takes care of discovering resources in Swarm and submitting them to stormd.

        :::console
        $ docker service create --name storm-swarm --constraint node.role==manager --mount type=bind,src=/var/run/docker.dock,dst=/var/run/docker.sock perfectstorm/storm-swarm -p

stormd comes with a web UI that you browse at `http://<swarm-manager-ip>:28482/`. If everything went well, you should be able to access that URL and check the status of your Swarm cloud.

Perfect Storm also has a command-line client, that we will use in this walkthrough: **stormctl**. It's written in Python: you can [download it](XXX) and run it as a standalone script, or you can install it using Pip:

    :::console
    $ pip install stormctl

In order to use it, set the `STORMD_HOST` variable to the address of your Swarm Manager:

    :::console
    $ export STORMD_HOST=<swarm-manager-ip>:28482

If everything worked, you should be able to run `stormctl status` successufully:

    :::console
    $ stormctl status
    XXX
    XXX
    XXX

Setup is complete, now we're ready to begin!

### Step 1: single node setup

For this first step, our aim is to run the most simple set up for our web application: one instance for the frontend, one instance for our database. For this setup, we are going to feed into Perfect Storm the following application specification:

    :::yaml
    application:
      name: messaging

      groups:
        - name: frontend
          query:
            type: { $in: ['swarm-service', 'swarm-task'] }
            image: { $regex: '^perfectstorm/messaging:' }
          services:
            - { name: http, port: 80 }

        - name: mysql
          query:
            type: { $in: ['swarm-service', 'swarm-task'] }
            image: { $regex: '^mysql:' }
          services:
            - { name: mysql, port: 3306 }

      expose:
        - frontend[http]

      links:
        - frontend => mysql[mysql]

      procedures:
        - name: frontend
          type: swarm
          content: |
            - service create --name frontend -p 80:80
                -e DB_HOST=172.17.0.1 -e DB_USER=messaging -e DB_PASSWORD=messaging -e DB_NAME=messaging
                andreacorbellini/messaging:latest

        - name: mysql
          type: swarm
          content: |
            - service create --name mysql -p 3306:3306
                -e MYSQL_DATABASE=messaging -e MYSQL_USER=messaging -e MYSQL_PASSWORD=messaging -e MYSQL_ROOT_PASSWORD=root
                mysql:{{ MYSQL_VERSION }} --server-id={{ SERVER_ID }} --log-bin=mysql-bin --sync-binlog=1 --gtid-mode=on --enforce-gtid-consistency=true
          params:
            MYSQL_VERSION: '5.7'
            SERVER_ID: '1'

We can save this specification into a YAML file named `frontend.yaml` and import it into Perfect Storm:

    :::console
    $ stormctl import -f frontend.yaml

Now let's take a close look at this specification to see what it does:

* At the beginning we have the name. Nothing special to say about it.

        :::yaml
        application:
          name: messaging

* Then we define two groups: one for the frontend and one for MySQL. We are matching both Swarm services and the Swarm tasks that are contained in those services so that we can have a full overview, but this is not strictly necessary (we could limit the groups to just the services or just the tasks).

        :::yaml
        groups:
          - name: frontend
            query:
              type: { $in: ['swarm-service', 'swarm-task'] }
              image: { $regex: '^perfectstorm/messaging:' }
            services:
              - { name: http, port: 80 }

          - name: mysql
            query:
              type: { $in: ['swarm-service', 'swarm-task'] }
              image: { $regex: '^mysql:' }
            services:
              - { name: mysql, port: 3306 }

* We define how our groups interact:

        :::yaml
        expose:
          - frontend[http]

        links:
          - frontend => mysql[mysql]

* And at the bottom we have something new, that I haven't introduced yet: **procedures**. Those are used to execute commands on Swarm. In this case they specify the `docker service create` commands to bring up our containers:

        :::yaml
        procedures:
          - name: frontend
            type: swarm
            content: |
              - service create --name frontend -p 80:80
                  -e DB_HOST=172.17.0.1 -e DB_USER=messaging -e DB_PASSWORD=messaging -e DB_NAME=messaging
                  perfectstorm/messaging:latest

        - name: mysql
          type: swarm
          content: |
            - service create --name mysql -p 3306:3306
                -e MYSQL_DATABASE=messaging -e MYSQL_USER=messaging -e MYSQL_PASSWORD=messaging -e MYSQL_ROOT_PASSWORD=root
                mysql:{{ MYSQL_VERSION }} --server-id={{ SERVER_ID }} --log-bin=mysql-bin --sync-binlog=1 --gtid-mode=on --enforce-gtid-consistency=true
          params:
            MYSQL_VERSION: '5.7'
            SERVER_ID: '1'

Strictly speaking, procedures are not needed: you could run the same commands on your terminal (or even use alternatives, like `docker-compose` or `docker stack deploy`) and groups will still catch the resources correctly. Procedures however provide two benefits:

1. You can document both how your components interact and how to bring them up at once, in the same file.
1. Procedures can "interact" with groups and resources discovered with Perfect Storm. We will see how powerful this is later.

To bring up our single-note setup, if you want to use the procedures defined above, you can run these two commands:

    :::console
    $ stormctl procedure exec frontend --target default
    $ stormctl procedure exec mysql --target default

As you can see, procedures require a `--target` argument: this is the name or ID of the Swarm Cluster where you want to run the commands (in case you have more than one Swarm cluster). When you create a Swarm, the predefined name is `default`, but if you set a different name then you need to update `--target` accordling. If unsure, check the output of `swarmctl resource ls | grep swarm-cluster`.

If we now visit `http://<docker-machine-ip>/` we should see our messaging application up and running. You should see the address of the database and you should be able to write and read messages without any problem.


### Step 2: frontend with replication

Suppose that our web service becomes popular: we have to scale it up. We can start by scaling the frontend service up: we start more than one container on more than one node. Here we encounter the first obstacle: given that our frontend instances will get different IP addresses, we need a load balancer in front of them. Luckly Swarm comes with built-in load balancing: when we expose a port in a service (e.g. `docker service create -p 80:80 ...`), no matter where our containers are running, all nodes will be able to accept connection on that port and redirect to the right container. We have another, similar, problem: the frontend instances need to connect to MySQL, which may or may not be running on the same node as them. But again, we can use Swarm bult-in load balancing system, so let's do it. Let's scale our frontend:

    :::console
    $ docker service update frontend --replica 5

Here we used `docker` instead of a procedure via `stormctl`. Perfect Storm will detect the changes and reflect them:

    :::console
    $ stormctl group members frontend
    XXX

This works and if we visit our website we should see that requests are directed to different instances. However, we must remember that Swarm load balancing works on the transport layer. In a real world scenario we might want to use a more sophisticated load balancer that offers more features, something like HAProxy.

Perfect Storm ships with a controller for HAProxy that automatically syncs the members of a group with the members of the load balancer. To start it, we can use this file:

    :::yaml
    application:
      name: frontend-lb

      groups:
        - name: load-balancer
          query:
            type: { $in: ['swarm-service', 'swarm-task'] }
            image: { $regex: '^perfectstorm/haproxy:' }
          services:
            - { name: http, port: 80 }

      expose:
        - load-balancer[http]

      links:
        - load-balancer => frontend[http]

      procedures:
        - name: load-balancer
          type: swarm
          content: |
            - service create --name load-balacer --network host
              perfectstorm/haproxy -H {{ STORMD_ADDRESS }} --group frontend


### Step 3: MySQL with master/slave replication

We set up Consul for discovery.

We set up multiple MySQL tasks and use procedures to start replication on them.


#### Step 4: global replication

We set up Consul on multiple datacenters.
