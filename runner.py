from strawberry.aiohttp.views import GraphQLView
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from aiohttp import web

from api import schema
 
 
view = GraphQLView(schema, subscription_protocols=[
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL
])

app = web.Application()
app.router.add_route("*", "/graphql", view)

if __name__ == '__main__':
    web.run_app(app)