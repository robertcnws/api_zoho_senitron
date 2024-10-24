import {
  ApolloClient,
  InMemoryCache,
  ApolloProvider,
  HttpLink,
  split,
} from '@apollo/client';
import { CONFIG } from '../config-global';



const client = new ApolloClient({
  uri: `${CONFIG.apiUrl}/api_zoho/graphql/`, 
  cache: new InMemoryCache(),
});

export default client;
