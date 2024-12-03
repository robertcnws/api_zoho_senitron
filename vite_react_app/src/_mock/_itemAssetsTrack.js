import { useEffect } from 'react';
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
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_ZOHO_ITEM_ASSETS_TRACK, {
    variables: { listIds },
  });

  useEffect(() => {
    const checkAndTogglePolling = () => {
      const now = new Date();
      const currentHour = now.getHours();
      
      if (currentHour >= 7 && currentHour < 17) {
        startPolling(900000); 
      } else {
        stopPolling();
      }
    };

    checkAndTogglePolling();

    const intervalId = setInterval(checkAndTogglePolling, 60000); 

    return () => {
      clearInterval(intervalId);
      stopPolling();
    };
  }, [startPolling, stopPolling]);
  
  return { loading, error, data: data?.allZohoItemAssetsTrack };
};
