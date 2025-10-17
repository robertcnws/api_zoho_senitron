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
  const { loading, error, data, refetch } = useQuery(GET_TIMELINES_ITEMS);

  return { loading, error, data: data?.allTimelineItems || [], refetch};
};
