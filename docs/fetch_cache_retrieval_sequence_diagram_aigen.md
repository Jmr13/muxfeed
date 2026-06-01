sequenceDiagram
    autonumber
    participant U as User
    participant F as URLFetcher
    participant C as Cache
    participant M as Memory Cache
    participant D as Disk Cache
    participant S as requests.Session
    participant R as HTTP Server

    U->>F: fetch(url, force_refresh=false)

    alt Cache enabled & not force refresh
        F->>C: get(url, allow_stale=true)
        C->>M: lookup cache key

        alt Cache hit in memory
            M-->>C: CachedResponse
        else Cache miss in memory
            C->>D: load persistent cache file
            D-->>C: CachedResponse or None
            alt Found on disk
                C->>M: populate memory cache
            end
        end

        C-->>F: CachedResponse or None
    end

    alt Cached response exists
        F->>F: prepare headers (If-None-Match / If-Modified-Since)
    else No cache
        F->>F: use default headers
    end

    F->>S: GET request(url, headers, timeout)
    S->>R: HTTP request
    R-->>S: HTTP response
    S-->>F: response

    alt HTTP 304 Not Modified AND cached exists
        F->>C: set(updated cached_at)
        C->>M: update memory cache
        F-->>U: FetchResult(from_cache=true, cached content)
    else HTTP 200 OK
        F->>F: build CachedResponse
        F->>C: set(new_cached)
        C->>M: store in memory
        C->>D: persist to disk (optional)
        F-->>U: FetchResult(from_cache=false, content)
    else HTTP error / exception
        F-->>U: FetchResult(ok=false, error)
    end