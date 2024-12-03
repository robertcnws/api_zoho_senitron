import { useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';

const GET_TIMELINES_ITEMS = gql`
  {
    allTimelineItems {
      id
      itemNumber
      previousStockOnHand
      datePreviousStockOnHand
      actualStockOnHand
      dateActualStockOnHand
      previousStatusZoho
      datePreviousStatusZoho
      actualStatusZoho
      dateActualStatusZoho
      previousQuantity
      datePreviousQuantity
      actualQuantity
      dateActualQuantity
      previousStatusSenitron {
        id
        senitronId
        name
      }
      datePreviousStatusSenitron
      actualStatusSenitron {
        id
        senitronId
        name
      }
      dateActualStatusSenitron
      senitronItem {
        itemNumber
        qty
        tagsCount
      }
      zohoItem {
        itemId
        name
        sku
        stockOnHand
      }
      text
    }
  }
`;

export const useTimelineItemsQuery = () => {
  const { loading, error, data, startPolling, stopPolling } = useQuery(GET_TIMELINES_ITEMS);

  useEffect(() => {
    startPolling(900000); 
    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling]);
  
  return { loading, error, data: data?.allTimelineItems };
};
