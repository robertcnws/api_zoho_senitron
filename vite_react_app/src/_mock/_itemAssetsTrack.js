import { gql, useQuery } from '@apollo/client';


const GET_ZOHO_ITEM_ASSETS_TRACK = gql`
  query GetZohoItemAssetsTrack($listIds: [String!]) {
    allZohoItemAssetsTrack(listIds: $listIds) {
      itemId
      sku
    	createdTime
      differences {
        news
        losts
      }
      historialDifferences {
        date
        differences {
          news
          losts
        }
      }  
    }
  }
`;

export const useItemAssetsTrackQuery = (listIds) => {
  const { loading, error, data, refetch } = useQuery(GET_ZOHO_ITEM_ASSETS_TRACK, {
    variables: { listIds },
    skip: !listIds || listIds.length === 0,
  });
  
  return { loading, error, data: data?.allZohoItemAssetsTrack || [], refetch };
};
