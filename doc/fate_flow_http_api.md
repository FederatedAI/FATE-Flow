# REST API

## 1. Description

## 2. Interface Authentication

Flow HTTP API added signature authentication in 1.7.0. If `http_app_key` and `http_secret_key` are set in the configuration file, all requests sent to Flow will need to add the following header

`TIMESTAMP`: Unix timestamp in milliseconds, e.g. `1634890066095` means `2021-10-22 16:07:46 GMT+0800`, note that the difference between this time and the current time of the server cannot exceed 60 seconds

`NONCE`: random string, can use UUID, such as `782d733e-330f-11ec-8be9-a0369fa972af`

`APP_KEY`: must be consistent with `http_app_key` in the Flow configuration file

`SIGNATURE`: signature generated based on `http_secret_key` and the request parameters in the Flow configuration file

### 2.1 Signature generation method

- Combine the following elements in order

`TIMESTAMP`

`NONCE`

`APP_KEY`

request path + query parameters, if there are no query parameters then the final `? `, such as `/v1/job/submit` or `/v1/data/upload?table_name=dvisits_hetero_guest&namespace=experiment`

If `Content-Type` is `application/json`, then it is the original JSON, i.e. the request body; if not, this item is filled with the empty string

If `Content-Type` is `application/x-www-form-urlencoded` or `multipart/form-data`, all parameters need to be sorted alphabetically and `urlencode`, refer to RFC 3986 (i.e. except `a-zA-Z0-9- . _~`), note that the file does not participate in the signature; if not, this item is filled with the empty string

- Concatenate all parameters with the newline character `\n` and encode them in `ASCII`.

- Use the `HMAC-SHA1` algorithm to calculate the binary digest using the `http_secret_key` key in the Flow configuration file

- Encode the binary digest using base64

### 2.2. Example

You can refer to the signature method of [Fate SDK](https://github.com/FederatedAI/FATE/blob/develop-1.7/python/fate_client/flow_sdk/client/base.py#L63) or the proofreading method of [Fate Flow](https://github.com/FederatedAI/FATE/blob/develop-1.7/python/fate_client/flow_sdk/client/base.py#L63) (https://github.com/FederatedAI/FATE-Flow/blob/develop-1.7.0/python/fate_flow/apps/__init__.py#L104) for the checksum method

### 2.3. Error codes

`400 Bad Request` request body has both json and form

`401 Unauthorized` Missing one or more header(s)

`400 Invalid TIMESTAMP` `TIMESTAMP` could not be parsed

`425 TIMESTAMP is more than 60 seconds away from the server time` The `TIMESTAMP` in the header is more than 60 seconds away from the server time

`401 Unknown APP_KEY` header in `APP_KEY` does not match `http_app_key` in the Flow configuration file

`403 Forbidden` Signature verification failed
