# CloudFront in mocksy

mocksy serves each CloudFront distribution on its gateway and forwards requests
to the distribution's origins. Moto stores the CloudFront resources.

## Domain

The `DomainName` of a distribution is
`<id>.cloudfront.localhost.localstack.cloud` (the `LOCALSTACK_HOST` host). Send
requests to that host on mocksy's gateway, port 4566, with HTTP or HTTPS:

```sh
curl https://e1abc2def3.cloudfront.localhost.localstack.cloud:4566/index.html
```

`*.localhost.localstack.cloud` resolves to 127.0.0.1.

## Request handling

1. **Cache behaviour:** the first `CacheBehaviors` item whose `PathPattern`
   matches the path (`*` matches any characters, `?` one), else
   `DefaultCacheBehavior`.
2. **ViewerProtocolPolicy:** `redirect-to-https` answers HTTP with 301,
   `https-only` answers HTTP with 403.
3. **AllowedMethods:** other methods get 403.
4. **Cache:** GET and HEAD responses are served from the cache while they are
   fresh (`X-Cache: Hit from cloudfront`).
5. **Origin:**
   - S3 origin (`<bucket>.s3.<region>.amazonaws.com`): the object is read from
     mocksy's S3. `/` returns `DefaultRootObject`.
   - Custom origin: the request goes to `<DomainName>:<port><OriginPath><path>`
     with the scheme from `OriginProtocolPolicy`, the origin's `CustomHeaders`,
     `Host` set to the origin domain, and `X-Forwarded-For` and `Via`. TLS
     certificates of origins are not checked.
   - The query string goes to the origin when `ForwardedValues.QueryString` is
     true, or when the behaviour uses a cache policy.
6. **CustomErrorResponses:** an origin error with a configured `ErrorCode`
   is replaced by `ResponsePagePath` (fetched from the same origin) with
   `ResponseCode`. Use this for single-page apps (404 to `/index.html`, 200).

Responses carry `X-Cache`, `Via`, `X-Amz-Cf-Id` and `X-Amz-Cf-Pop: MOCKSY`.

## Cache time

| Response | Time in the cache |
|---|---|
| 2xx, 3xx | Origin `Cache-Control` `s-maxage`, else `max-age`, kept between `MinTTL` and `MaxTTL`; without them `DefaultTTL` |
| `no-store`, `no-cache`, `private` | `MinTTL` |
| 4xx | 10 s, or `ErrorCachingMinTTL` of a matching custom error response |
| 5xx | not cached |

Legacy cache settings (`ForwardedValues`) without TTLs use the AWS defaults:
`DefaultTTL` 86400 and `MaxTTL` 31536000. The managed cache policy
`CachingDisabled` turns the cache off. Other cache policies use the defaults.

CreateInvalidation removes matching paths from the cache (`/images/*` matches
every path that starts with `/images/`). UpdateDistribution and
DeleteDistribution clear the distribution's cache.

## Not supported yet

- Requests to `Aliases` (CNAMEs): use the distribution domain.
- CloudFront Functions and Lambda@Edge.
- Origin groups (failover), origin access control checks, signed URLs and
  cookies, geo restrictions, WAF, compression.
- Cache policy and origin request policy details (headers, cookies and query
  strings in the cache key).
- The cache is in memory and is lost when mocksy stops.
