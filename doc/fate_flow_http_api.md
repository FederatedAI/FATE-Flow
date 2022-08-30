# REST API

## 1. Description

### 2. Error codes

`400 Bad Request` request body has both json and form

`401 Unauthorized` Missing one or more header(s)

`400 Invalid TIMESTAMP` `TIMESTAMP` could not be parsed

`425 TIMESTAMP is more than 60 seconds away from the server time` The `TIMESTAMP` in the header is more than 60 seconds away from the server time

`401 Unknown APP_KEY` header in `APP_KEY` does not match `http_app_key` in the Flow configuration file

`403 Forbidden` Signature verification failed
