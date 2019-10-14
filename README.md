# kongcli - cli for kong admin api

*Note:* usable but still alpha quality - I will remove the alpha flag as soon as the coverage is above 90%.

This is a command line interface (cli) to configure the awesome [kong](https://konghq.com/), espacially using the [kong admin api](https://docs.konghq.com/1.3.x/admin-api/). There are alternatives like

- [konga](https://pantsel.github.io/konga/): Web GUI.
- [kong-cli](https://github.com/passos/kong-cli): CLI to Kong 0.10.x. (Last commit Jul 2017, as of this writing)
- [kongctl](https://github.com/kepkin/kongctl): CLI to Kong. I was not aware of this, when I started the project.

At work we use(d) a kong 0.13.x, hence the CLI's were either outdated or not ready. As with the GUI... it was to much overhead for my case. Then I collected some `*.http` files for the [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client), but was never really satisfied with the 'UI'.

I started this project for *my most used endpoints*, i.e. there is a lot of not-implemented endpoints - if you need them, consider the [`raw`](#raw) command or provide a PR ;) . I plan to make it compatible with **kong >= 0.13.x** - currently, CI tests with latest docker images for 0.13, 0.14, 0.15, 1.0, 1.1, 1.2 and 1.3.

## installation

> TBD - not yet published

```sh
$ pip install kongcli
```

## usage

`kongcli` support `-h` / `--help` and documentation for the individual commands (along with documentation on [Kong Admin API](https://docs.konghq.com/1.3.x/admin-api/) for your kong version) should be sufficient to get most common operations done with ease:

```sh
$ kongcli -h
Usage: kongcli [OPTIONS] COMMAND [ARGS]...

  Interact with your kong admin api.

  Some options can also be configured via environment variables:

  --url KONG_BASE            base url to the kong admin api
  --apikey KONG_APIKEY       api key for the kong admin api
  --basic KONG_BASIC_USER    basic auth username for kong admin api
  --passwd KONG_BASIC_PASSWD basic auth password for the kong admin api

Options:
  --url TEXT       Base url to kong.  [required]
  --apikey TEXT    API key for key-auth to kong.
  --basic TEXT     Basic auth username for kong.
  --passwd TEXT    Basic auth password for kong. Is also prompted, if left
                   out.
  --tablefmt TEXT  Format for the output tables. Supported formats:
                   fancy_grid, github, grid, html, jira, latex,
                   latex_booktabs, latex_raw, mediawiki, moinmoin, orgtbl,
                   pipe, plain, presto, psql, rst, simple, textile, tsv,
                   youtrack  [default: fancy_grid]
  --font TEXT      Font for the table headers. See
                   http://www.figlet.org/examples.html for examples.
                   [default: banner]
  -v, --verbose    Add more verbose output.  [default: 0]
  -h, --help       Show this message and exit.

Commands:
  consumers  Manage Consumers Objects.
  info       Show information on the kong instance.
  list       List various resources (chainable).
  plugins    Manage Plugin Objects.
  raw        Perform raw http requests to kong.
  routes     Manage Routes Objects.
  services   Manage Service Objects.
  version    Show version of kongcli.
```

### raw

If the endpoint / plugin / ... you need to configure is not implemented, you can always use curl or other means to submit a request to the kong admin api. The `raw` command should make it a bit easier:

```sh
$ Usage: kongcli raw [OPTIONS] METHOD URL

  Perform raw http requests to kong.

  You can provide headers using the --header / -H option:

  - to get the header 'Accept: application/json' use
      -H Accept application/json
  - to get the header 'Content-Type: application/json; charset=utf-8' use
      -H Content-Type "application/json; charset=utf-8"

  You can provide a json body using the --data / -d option
    -d foo bar          # => {"foo": "bar"}
    -d foo true         # => {"foo": true}
    -d foo '"true"'     # => {"foo": "true"}
    -d foo.bar.baz 2.3  # => {"foo": {"bar": {"baz": 2.3}}}
    -d name bar -d config.methods '["GET", "POST"]'
    # => {"name": "bar", "config": {"methods": ["GET", "POST"]}}

  The first argument to `--data / -d` is the key. It is split by dots and
  sub-dictionaries are created. The second argument is assumed to be valid
  JSON; if it cannot be parsed, we assume it is a string. Multiple usages of
  `--data / -d` will merge the dictionary.

Options:
  -H, --header <TEXT TEXT>...  Add headers.
  -d, --data <TEXT TEXT>...    Add key-value data points to the payload.
  -h, --help                   Show this message and exit.
```

If you provide the base url and authentication via environment variables, requests to kong admin api via `raw` are like:

```sh
$ kongcli raw GET /
> GET http://localhost:8001/
> User-Agent: python-requests/2.22.0
> Accept-Encoding: gzip, deflate
> Accept: */*
> Connection: keep-alive
>
< http/11 200 OK
< Date: Mon, 14 Oct 2019 15:59:41 GMT
< Content-Type: application/json; charset=utf-8
< Transfer-Encoding: chunked
< Connection: keep-alive
< Access-Control-Allow-Origin: *
< Server: kong/0.13.1

{"plugins":{"enabled_in_cluster":[],"available_on_server":{"response-transformer":true,"correlation-id":true,"statsd":true,"jwt":true,"cors":true,"basic-auth":true,"key-auth":true,"ldap-auth":true,"http-log":true,"oauth2":true,"hmac-auth":true,"acl":true,"datadog":true,"tcp-log":true,"ip-restriction":true,"request-transformer":true,"file-log":true,"bot-detection":true,"loggly":true, ...}
```

## CRUD for consumers, services, routes, (some) plugins

The objects consumers, services, routes, plugins all have a 'similar' create, read, update, delete (CRUD) interface. For consumers the commands are as follows, but the others are similar:

```sh
$ kongcli consumers -h
Usage: kongcli consumers [OPTIONS] COMMAND [ARGS]...

  Manage Consumers Objects.

  The Consumer object represents a consumer - or a user - of a Service. You
  can either rely on Kong as the primary datastore, or you can map the
  consumer list with your database to keep consistency between Kong and your
  existing primary datastore.

Options:
  -h, --help  Show this message and exit.

Commands:
  add-groups     Add the given groups to the consumer.
  basic-auth     Manage basic auths of Consumer Objects.
  create         Create a user / consumer of your services / routes.
  delete         Delete a consumer with all associated plugins / acls etc.
  delete-groups  Delete the given groups from the consumer.
  key-auth       Manage key auths of Consumer Objects.
  list           List all consumers along with relevant information.
  retrieve       Retrieve a specific consumer.
  update         Update a consumer.
```

## UI

- Tables are printed using [`tabulate`](https://github.com/astanin/python-tabulate) - other formats can be selected via the `--tablefmt TEXT` option from `kongcli`.
- Headers are printed using [`pyfiglet`](https://github.com/pwaller/pyfiglet) - other fonts can be selected via the `--font TEXT` option from `kongcli` (see [http://www.figlet.org/examples.html](http://www.figlet.org/examples.html) for examples).
- logs can be shown using the `-v` / `--verbose` option from `kongcli`:
    - zero `-v` will show ERROR only
    - `-v` will show WARNING logs and above
    - `-vv` will show INFO and above
    - `-vvv` will show DEBUG and above

## examples

CRUD on a consumer:

```sh
$ kongcli consumers create --username foobar                                                                                                                                                                                                        
╒═══════════════════════════╤══════════════════════════════════════╤════════════╕                                                                                                                                                                                           
│ created_at                │ id                                   │ username   │                                                                                                                                                                                           
╞═══════════════════════════╪══════════════════════════════════════╪════════════╡                                                                                                                                                                                           
│ 2019-10-14 16:54:53+00:00 │ f4203001-c3de-4ab9-ad26-6f4ca0306ea8 │ foobar     │                                                                                                                                                                                           
╘═══════════════════════════╧══════════════════════════════════════╧════════════╛                                                                                                                                                                                            

$ kongcli consumers list  # to get all consumers
 #####                                                                                                                                                                                                                                                                       
#     #  ####  #    #  ####  #    # #    # ###### #####   ####                                                                                                                                                                                                               
#       #    # ##   # #      #    # ##  ## #      #    # #                                                                                                                                                                                                                   
#       #    # # #  #  ####  #    # # ## # #####  #    #  ####                                                                                                                                                                                                              
#       #    # #  # #      # #    # #    # #      #####       #                                                                                                                                                                                                             
#     # #    # #   ## #    # #    # #    # #      #   #  #    #                                                                                                                                                                                                                
 #####   ####  #    #  ####   ####  #    # ###### #    #  ####                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
╒══════════════════════════════════════╤═════════════╤════════════╤══════════════╤═══════════╤══════════════╤════════════╕                                                                                                                                                  
│ id                                   │ custom_id   │ username   │ acl_groups   │ plugins   │ basic_auth   │ key_auth   │
╞══════════════════════════════════════╪═════════════╪════════════╪══════════════╪═══════════╪══════════════╪════════════╡
│ f4203001-c3de-4ab9-ad26-6f4ca0306ea8 │             │ foobar     │              │           │              │            │                                                                                                                                                  
╘══════════════════════════════════════╧═════════════╧════════════╧══════════════╧═══════════╧══════════════╧════════════╛ 

$ kongcli consumers retrieve foobar  # to get a specific consumer
╒═══════════════════════════╤══════════════════════════════════════╤════════════╕                                                                                                                                                                                           
│ created_at                │ id                                   │ username   │                                                                                                                                                                                           
╞═══════════════════════════╪══════════════════════════════════════╪════════════╡                                                                                                                                                                                           
│ 2019-10-14 16:54:53+00:00 │ f4203001-c3de-4ab9-ad26-6f4ca0306ea8 │ foobar     │                                                                                                                                                                                           
╘═══════════════════════════╧══════════════════════════════════════╧════════════╛      

$ kongcli consumers update foobar --custom_id 1234
╒═══════════════╤═════════════╤══════════════════════════════════════╤════════════╕                                                                                                                                                                                         
│    created_at │   custom_id │ id                                   │ username   │                                                                                                                                                                                         
╞═══════════════╪═════════════╪══════════════════════════════════════╪════════════╡                                                                                                                                                                                         
│ 1571072093000 │        1234 │ f4203001-c3de-4ab9-ad26-6f4ca0306ea8 │ foobar     │                                                                                                                                                                                         
╘═══════════════╧═════════════╧══════════════════════════════════════╧════════════╛ 

$ kongcli consumers delete foobar
Deleted consumer `foobar`! 
```

## contribute

The project still needs some love. If you want to contribute, please consider the following things:

- We cannot know, which version of kong somebody is stuck with - please make your contributions compatible with 0.13+. If there is a new feature not supported downwards, please do not attempt to contribute it. Also, do not contribute depricated API, e.g. [API Objects](https://docs.konghq.com/0.13.x/admin-api/#api-object) etc. .
- make sure CI will most likely pass, e.g.:
    - static tests: `make statics`
    - pytests: `make tests`
    - try at least one or two different kong versions locally
- if you want to contribute new endpoints, please only provide endpoints you are actually using a lot - the more specific endpoints we support, the more maintenance work has to be done.
- i really would like it, if you just use the cli, report your bugs here, brag about how great it is on twitter, facebook, hackernews, reddit, ...


### start local development kong

The provided `docker-compose.yml` is able to start and setup different kong versions for local development (one at a time). In `.testenv`, change the `KONG_VERSION_TAG` and `KONG_MIGRATION_CMD` (`< 0.15` use `up`, `>= 0.15` use `bootstrap`). Then source the file, e.g. `export $(cat .testenv | xargs)`. Start the docker-compose with:

```sh
$ docker-compose down -v
$ docker-compose --project-name tests up -d
```
