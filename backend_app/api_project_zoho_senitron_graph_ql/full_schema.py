import graphene
from api_zoho.schema import Query as QueryApiZoho
from api_senitron.schema import Query as QueryApiSenitron

class Query(QueryApiZoho, QueryApiSenitron, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
