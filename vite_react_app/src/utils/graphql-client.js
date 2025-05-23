import {
  ApolloClient,
  InMemoryCache,
} from '@apollo/client';

import { CONFIG } from '../config-global';


const client = new ApolloClient({
  uri: `${CONFIG.apiUrl}/query/graphql/`, 
  cache: new InMemoryCache(),
});

export default client;
