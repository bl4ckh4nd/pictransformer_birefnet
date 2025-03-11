Web endpoints
Modal gives you a few ways to expose functions as web endpoints. You can turn any Modal function into a web endpoint with a single line of code, or you can serve a full app using frameworks like FastAPI, Django, or Flask.

Note that if you wish to invoke a Modal function from another Python application, you can deploy and invoke the function directly with our client library.

Simple endpoints
The easiest way to create a web endpoint from an existing function is to use the @modal.fastapi_endpoint decorator.

import modal

image = modal.Image.debian_slim().pip_install("fastapi[standard]")
app = modal.App(name="has-simple-web-endpoint", image=image)


@app.function()
@modal.fastapi_endpoint()
def f():
    return "Hello world!"

Copy
This decorator wraps the Modal function in a FastAPI application.

Note: Prior to v0.73.82, this function was named @modal.web_endpoint.

Developing with modal serve
You can run this code as an ephemeral app, by running the command

modal serve server_script.py

Copy
Where server_script.py is the file name of your code. This will create an ephemeral app for the duration of your script (until you hit Ctrl-C to stop it). It creates a temporary URL that you can use like any other REST endpoint. This URL is on the public internet.

The modal serve command will live-update an app when any of its supporting files change.

Live updating is particularly useful when working with apps containing web endpoints, as any changes made to web endpoint handlers will show up almost immediately, without requiring a manual restart of the app.

Deploying with modal deploy
You can also deploy your app and create a persistent web endpoint in the cloud by running modal deploy:

Passing arguments to an endpoint
When using @modal.fastapi_endpoint, you can add query parameters which will be passed to your function as arguments. For instance

import modal

image = modal.Image.debian_slim().pip_install("fastapi[standard]")
app = modal.App(image=image)


@app.function()
@modal.fastapi_endpoint()
def square(x: int):
    return {"square": x**2}

Copy
If you hit this with an urlencoded query string with the “x” param present, it will send that to the function:

$ curl https://modal-labs--web-endpoint-square-dev.modal.run?x=42
{"square":1764}

Copy
If you want to use a POST request, you can use the method argument to @modal.fastapi_endpoint to set the HTTP verb. To accept any valid JSON object, use dict as your type annotation and FastAPI will handle the rest.

import modal

image = modal.Image.debian_slim().pip_install("fastapi[standard]")
app = modal.App(image=image)


@app.function()
@modal.fastapi_endpoint(method="POST")
def square(item: dict):
    return {"square": item['x']**2}

Copy
This now creates an endpoint that takes a JSON body:

$ curl -X POST -H 'Content-Type: application/json' --data-binary '{"x": 42}' https://modal-labs--web-endpoint-square-dev.modal.run
{"square":1764}

Copy
This is often the easiest way to get started, but note that FastAPI recommends that you use typed Pydantic models in order to get automatic validation and documentation. FastAPI also lets you pass data to web endpoints in other ways, for instance as form data and file uploads.

How do web endpoints run in the cloud?
Note that web endpoints, like everything else on Modal, only run when they need to. When you hit the web endpoint the first time, it will boot up the container, which might take a few seconds. Modal keeps the container alive for a short period in case there are subsequent requests. If there are a lot of requests, Modal might create more containers running in parallel.

For the shortcut @modal.fastapi_endpoint decorator, Modal wraps your function in a FastAPI application. This means that the Image your Function uses must have FastAPI installed, and the Functions that you write need to follow its request and response semantics. Web endpoint Functions can use all of FastAPI’s powerful features, such as Pydantic models for automatic validation, typed query and path parameters, and response types.

Here’s everything together, combining Modal’s abilities to run functions in user-defined containers with the expressivity of FastAPI:

from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import modal

image = modal.Image.debian_slim().pip_install("fastapi[standard]", "boto3")
app = modal.App(image=image)


class Item(BaseModel):
    name: str
    qty: int = 42


@app.function()
@modal.fastapi_endpoint(method="POST")
def f(item: Item):
    import boto3
    # do things with boto3...
    return HTMLResponse(f"<html>Hello, {item.name}!</html>")

Copy
This endpoint definition would be called like so:

curl -d '{"name": "Erik", "qty": 10}' \
    -H "Content-Type: application/json" \
    -X POST https://ecorp--web-demo-f-dev.modal.run

Copy
Or in Python with the requests library:

import requests

data = {"name": "Erik", "qty": 10}
requests.post("https://ecorp--web-demo-f-dev.modal.run", j