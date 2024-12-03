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
    const checkAndTogglePolling = () => {
      const now = new Date();
      const currentHour = now.getHours();
      
      if (currentHour >= 7 && currentHour < 17) {
        startPolling(900000); // 15 minutos
      } else {
        stopPolling();
      }
    };

    checkAndTogglePolling();

    const intervalId = setInterval(checkAndTogglePolling, 60000); // Cada minuto

    return () => {
      clearInterval(intervalId);
      stopPolling();
    };
  }, [startPolling, stopPolling]);
  
  return { loading, error, data: data?.allTimelineItems };
};
